# PlantAgent: an AI engineer for any plant

PlantAgent opens a plant the way an engineer does: from its drawings, P&IDs, reports, bid documents and SCADA data.
It covers water and wastewater plants, chemical process units, petrochemical incidents, campus cooling, data centers and
pumping stations (open `web/home.html`). You ask a question ("Can this plant make 18 MGD?"), or click an issue and press **Fix**. Meta's **Muse**
models read the documents and the drawing, then run real simulators:

- **EPANET** for pumped systems
- a gravity hydraulic-profile solver
- **TSNet** transients
- extended-period SCADA calibration
- **DWSIM** for process plants
- **WaterTAP** for seawater reverse osmosis screening

The answer comes back as a **proposed change verified in the simulator**. The engineer accepts or rejects it, like a
code diff, and accepted changes are drawn on the real sheet and exported as **DWG**. Every number cites a page or a
simulator run.

> Draft engineering output for review by a licensed professional engineer. It is not a substitute for one.

## Process plants: from a smart P&ID to a verified fix

`web/plant.html?case=chem_c01` opens a chemical unit from its **DEXPI P&ID**, the vendor-neutral P&ID exchange standard.
The P&ID is the DEXPI e.V. reference example C01. Its operating data sheet (`cases/chem_c01/basis.md`) is
**illustrative**, written for this demo, and the page says so.

- **P&ID reader** (`plantagent/pid.py`, standard library only):
  - Turns the P&ID into equipment with design data, connections, valves and control loops.
  - Reads all 18 vendor exports in the DEXPI test set.
  - Flags design data that does not hang together. On C01 it flags a pump whose 60 kW shaft power implies 9 %
    efficiency, and a tank whose dimensions give 1,257 m3 against a stated 26 m3.
- **Muse builds the DWSIM model itself** from the P&ID and the data sheet:
  - It follows the P&ID topology: the tank recirculation loop through H1008 is closed with a recycle, and the
    reciprocating pump is modelled as positive displacement.
  - Where the site datasheets contradict the P&ID, it uses the site data and records the conflict as an assumption.
  - It reproduces all 14 measured values on the data sheet: temperatures, flows and pressure drops, e.g. 34.0 vs
    33.98 C and 23.6 vs 23.63 C.
  - A **coverage check** compares the model with the P&ID line by line. All 5 flow connections are modelled; the
    relief path through PSV 47125 is excluded because it carries no normal flow.
  - The build took 221 s and cost $0.0095.
- **Live load on the P&ID.** Each equipment item shows its load, and the throughput slider re-solves DWSIM in about
  0.3–0.5 s.
- **"Get me to target" (+20 %).** Three limits bind, and Muse proposes the cheapest fix for each:

  | Limit | Fix |
  |---|---|
  | H1007 cooler outlet | Cooling water 20 → 27 m3/h, which is 90 % of the branch supply. The exchanger pressure drop rises to 0.86 of the 1.0 bar available. |
  | Tank temperature, held by the H1008 recirculation | Chilled water 15 → 18 m3/h |
  | Quality-control hold time in the tank | Working level 80 → 85 %, the documented maximum |

- **Verified before acceptance.** DWSIM re-solves each proposal, and then all of them together: the unit reaches 120 %
  and the new maximum is 124 %. Accepting re-verifies on the server, and accepted changes become revisions that can be
  undone.

### Second opinion from Meta's open-weights model

Tick **+ open-model second opinion** in the workspace. **Muse Spark Open** (open weights, on Baseten) then answers the
same request independently, on the same calibrated model and tools.

- **How the answers are compared.** The comparison is deterministic; no third model picks a winner. It checks:
  - the limiting equipment
  - each proposed change (same path, values within 10 %)
  - which proposals verify in DWSIM
  - the target verdict
  - the stated annual energy saving
- **What the engineer sees.** "Both models agree", or the points where they differ, flagged for an engineer to look at.
- **Applying a fix.** Either model's proposals can be applied as a draft revision only if DWSIM verifies them. The
  audit entry records which model proposed the change and where the two models disagreed.

Results on the two process cases (`runs/ws/*/second_opinion_answer.json`):

| Case | Agree | Disagree |
|---|---|---|
| Chemical unit, +20 % | Cooling water to 27 m3/h and tank level to 22.1 m3; both reach 120 % | The open model missed the third limit, the tank temperature held by the H1008 chilled-water loop |
| Dairy refrigeration, N+1 and floating head | The new load fits with N+1; the condensers are the closest limit | Annual saving: 1,716 MWh from Muse Spark, 1,330 MWh from Muse Spark Open. A direct bin calculation on the same model gives 1,329 MWh, so the open model was right here. The open model also proposed a fixed 8.6 bar(a) head pressure. DWSIM first accepted it, because the condenser outlet was not tied to wet bulb. The condensers now carry a heat-sink limit (`min_T_out_C`: design wet bulb 21 C + 8 K approach, 1 K subcooled = 28 C), so that proposal no longer verifies. Floating head is evaluated with `annual_energy` over the wet-bulb bins. |

Neither model is always right. The value is in the disagreements the engineer is shown.

The open model sometimes writes a large tool call as text (`<x:invoke name=...>`) instead of a structured call. The
agent loop recovers these calls (`study.text_tool_calls`). Before this fix the open model could not finish an answer.

### Safety, records and data the engineer already has

- **Relief protection scan** (`pid.relief_scan`, deterministic, no LLM). For every side of every equipment item it
  checks whether the side reaches a relief device without passing a valve that could be closed. Relief direction
  counts: a relief valve protects its inlet, not the vessel it discharges into. It flags heated sides that could be
  blocked in, which is the Williams Geismar pattern.
  - On C01 it finds that both coolers' cooling- and chilled-water sides have no relief on the drawing. This is the
    API 521 blocked-in cooling-water case.
  - It also finds that H1008's product side reaches PSV 47125 only through a ball valve.
- **Audit trail** (`plantagent/audit.py`).
  - It is append-only and hash-chained, so editing an entry breaks the chain and `verify()` reports where. The chain is
    an internal consistency check, not an external signature: deleting the tail cannot be detected unless the last hash
    and entry count are published outside the writable run directory.
  - Each entry records user, time with time zone, action and reason.
  - Accepting a change requires a reason. Undo never deletes history: it adds a revert revision.
  - Revisions are kept on disk.
- **PDF schematics** (`plantagent/pidvision.py`). Most plants have only PDF or scanned P&IDs. Muse vision reads the
  sheet into the same structure as the DEXPI reader: loops with temperatures, equipment, connections and inline valves.
  Equipment positions come from the PDF's text layer, so the live badges sit on the real sheet. If the sheet has no
  text layer, the positions are Muse's estimates.
- **Data centre (IIT Kanpur tenders), an honest gap.** Muse reads the real PDF liquid-cooling schematic correctly:
  - the three loops with their temperatures (8/13, 15/20 and 30/38 C)
  - 2 x 750 kW plate exchangers, 14 rear-door exchangers and the dry coolers

  The engineer-confirm step was added after these failures. The read was checked against the tender and corrected 37
  times, mostly because the chiller plant, condenser loop and towers are not on this sheet. The fifth build, on the
  corrected read, had the right equipment. It was still not usable: loop flows scaled with load, pumps were over their
  rating at today's load, and the coverage check listed 6 missing connections.

  Four earlier attempts to have the agent build a DWSIM model of the plant did not give a model we would show either. They
  either missed the chillers, which are the N+1 question, or put the rear-door exchangers in series. No capacity answer
  is shown for this case.
- **Project documents.** The agent can search and read tenders and datasheets (`search_documents`,
  `read_document_page`) and cites their page numbers.
- **Historian / SCADA export.** `historian` returns the mean, p5, p95 and range per tag over a time window, for
  calibration against real operation.
- **Annual energy** (`annual_energy`, bin method). The tool solves the model once per bin (e.g. wet-bulb bins) and
  sums electric power x hours. A base case and an alternative can be compared over the same bins.
- **Water treatment ratings** (`standards.treatment_capacity`). It computes the rated capacity of flocculation,
  sedimentation and filters from their dimensions against Ten States Standards, including the case with the largest
  filter out, instead of quoting a documented rating. The workspace takes the lower of this rating and the hydraulic
  limit.

### What the DWSIM layer models

DWSIM (`plantagent/process.py`) runs headless through pythonnet as one long-lived worker.

- **Unit operations:** pumps (centrifugal or positive displacement), heat exchangers in rating mode, heaters and
  coolers (fixed or scaling heat loads), valves, tanks at vessel pressure, mixers, splitters (fixed recirculation) and
  compressors. This covers refrigeration cycles, e.g. ammonia with Peng-Robinson; the condenser outlet must be liquid.
- **Recycle loops.**
- **Limits checked:**
  - pump rated and minimum flow, motor power, NPSH margin, and discharge against 90 % of the relief set pressure
  - compressor motor power and discharge temperature
  - exchanger required area against installed area, with U and pressure drop that follow flow (films ~Q^0.8, dP ~Q^1.8)
  - frame limit and available pressure drop
  - hold time on net throughput
  - utilities at no more than 90 % of supply
- **Other tools:** a throughput capacity search, bubble-point pressure and fluid properties.
- **API 521 blocked-in (hydraulic expansion) check.** It reports both regimes: if the vessel was less than the
  critical liquid fill when isolated, the pressure stays at the vapour pressure; above that fill, hydraulic expansion
  governs. For Williams Geismar the critical fill is 70 %; the CSB found the reboiler was at least 65.5 % full. The same tools are available in blind studies
  (`"simulators": ["dwsim"]`).
- **Everyday liquid hydraulics:** rated control valves report required US Cv and travel for linear or equal-percentage
  characteristics. Pipe segments report Darcy-Weisbach/Colebrook pressure drop, velocity and Reynolds number, and take
  fittings and elevation into account.
- **Limits of the layer:** steady state only. Valve sizing is an incompressible-liquid screen without choking,
  cavitation, flashing, installed-characteristic or actuator-force calculations. Pipe calculations omit two-phase and
  compressible flow, heat transfer, water hammer, erosion and fouling. Exchanger U is scaled from one test point, not
  computed from exchanger geometry.

The first model of this unit put H1008 in series instead of in the recirculation loop. It is kept in
`runs/ws/chem_c01/model_v1_series.json`. An independent practitioner review caught it, which is why the coverage check now
exists.

## Try it in three minutes

Open `web/home.html` and press **Start the 3-minute demo**. It walks through the chemical unit in six steps:

1. the source P&ID and the model the agent built from it
2. the +20 % question
3. what limits it
4. the fixes, each re-solved in DWSIM
5. before and after
6. the evidence

What the workspace shows:

- **Basis of every input.** Each input is labelled as in a document, measured, computed or assumed.
- **Re-solved runs.** Every cited run is re-solved and must reproduce. A run that does not is shown as not reproduced.
- **Recorded vs. live solutions.** Recorded DWSIM solutions are labelled as such and are re-solved live once the model
  changes.
- **Draft revisions.** Applying a fix creates a draft model revision, not an engineering approval. It needs a reason
  and goes into the hash-chained audit trail.
- **Limits cannot be edited away.** A proposal that only edits a documented limit is refused as not verifiable. This
  applies to process limits, profile ratings, and a cited run that relaxes them.
- **Provisional answers.** When a deciding value is missing, the answer says it is provisional and lists field checks:
  what to measure, where, and which conclusion it would change.

## What it does

| | |
|---|---|
| **Engineering workspace** (`web/workspace.html`) | The real AutoCAD sheet with live water-surface gauges and capacity by unit. Each value is marked ● simulated or ○ documented. Also: water-surface and demand charts, plus Existing / Proposed views and a revision timeline. |
| **Ask / Fix / Get me to target** | Muse plans, reads, simulates and proposes. A proposal can be accepted only if the solver reproduces it, and the server re-checks before writing. |
| **Citation and solver check** | Deterministic, with no LLM involved. Cited runs must exist in the log, cited page values must appear on the page, and proposals must reproduce in the solver. This is separate from the QA/QC step of a blind study, where a second agent reviews the first agent's work. |
| **Drawing reading** | The sheet is read twice by Muse vision, as a full sheet and as zoomed tiles, and the two reads are reconciled. Roseburg: 35/35 elevations agree. An unseen sheet takes about 37 s. |
| **Field photo** | Muse reads a pump nameplate or gauge against a JSON schema. A specific-speed check and a letter-O/zero check catch misreads. The reading is matched to a model pump and applied as a logged revision. Writes are blocked when the reading is more than 2× off or overloads the motor. |
| **Voice** | Push-to-talk, transcribed by Muse Voice Transcribe. |
| **CAD round trip** | Exports an editable DXF/DWG (model parameters on layer `PA-PARAMS`). The engineer edits it in AutoCAD or LibreCAD and drops it back; changes become revisions and the model is re-solved. |
| **Deliverables** | Memo, calc sheets (xlsx), redlined DWG, a new hydraulic-profile sheet, pump data sheets, a field test plan, a cost estimate (published curves, ENR, full AACE band) and a Ten States Standards check. Each report ends with a scenario register, units/datum and a sign-off block. |

## Evidence: blind benchmark against real engineers

The separate [NETL design-reproduction check](evidence/designcheck/README.md) compares agent-built DWSIM outlet states with withheld published stream tables (deterministic thresholds, not an LLM judge):

| NETL 2022 Case 2 section | Supplied-inlet conservation | Inferred design outputs: Muse contributor | Inferred design outputs: Muse Spark Open |
|---|---:|---:|---:|
| Syngas cooler (streams 8→9) | 8/8 within ±10% | 0/2: T and duty missed | 0/2: T and duty missed |
| CO2 compression/drying (18+19→20) | 2/2 within ±10% | 3/5: water and aftercooler missed | 2/5: water, aftercooler and pressure-raising power missed |

The conservation column mainly proves that the submitted inlet flow and composition survive the model. The inferred
design-output columns are the harder reproduction result; the full raw metric table remains in
[`evidence/designcheck/README.md`](evidence/designcheck/README.md).

On each real project, the pages holding the engineers' conclusions are **withheld** from the agent. Recommendation
clauses are redacted, and a leak check runs against the answer key. The agent then does the study, and
**muse-wonder-1.0**, a different model from the agent, grades its findings against the engineers' conclusions.

- 13 cases and 6 task types: capacity, troubleshooting, energy audit, surge, failure investigation and force-main
  design. The cases span water and wastewater, canal pumping stations, campus cooling, a data center, a gas plant and an
  olefins plant.
- **Mean of the latest run per case: 65 %** of the engineers' conclusions.
- **Judge check:** every graded run was re-graded by a second model (muse-spark-1.3). It gave the same verdict on 88 %
  of 134 items, and the mean score moved from 66 % to 64 % (`evidence/judge_agreement.json`). That shows consistency
  between models; it is not a human check.
- **Gas and olefins plant incidents (CSB).** Pascagoula was first run with the water-network tools, which do not fit a
  cryogenic gas plant, and scored 67 %. Re-run with the DWSIM process tools (bubble point, fluid properties,
  blocked-in expansion) it scored 92 %. Williams Geismar scored 67 % in both runs. In the second run the agent
  computed the blocked-in expansion pressure: 6,260 psig, against the CSB's estimate of about 5,000 psig. All runs
  are kept.
- **Run-to-run variance (Roseburg, strict redaction, 4 independent runs):** 93%, 64%, 57% and 50% of the engineers'
  conclusions, mean 66%. The fourth run was made with the treatment-rating tool added. In it, one item contradicted the
  engineers: the agent held the clearwell to be limiting. The earlier Roseburg runs (57%, 71%, 79%) used a looser redaction that left hint sentences
  visible. They are kept for transparency but should not be compared with these.
- Results, per-run deliverables and grades are in [`evidence/`](evidence/README.md).
- **Contamination check:** with no documents, Muse says it does not know the Roseburg report's conclusions
  (`evidence/contamination_check.json`).
- The workspace never reads the withheld answer pages. The "Compare with the engineers" view shows an offline blind
  run, labelled with its run id.

**A negative result we report:** on 20 real factories from the US DOE Industrial Assessment Center database
(`plantagent/iac.py`), the agent was given only the plant profile and its utility bills.

- It named 47–53 % of the auditors' measures, by ARC family.
- A plain baseline did as well: the 10 measures most often recommended in the same industry named 54 %.
- Savings estimates were off by about 4×.

Predicting audit measures from bills alone mostly recovers base rates, so we do not claim it.

**Open weights: the same agent on Muse Spark Open.** Muse Spark Open (Meta's open-weights model, served on Baseten as
`meta-models/muse-spark-open-1026`) runs through the same client with the model id
`baseten:meta-models/muse-spark-open-1026`. Same tools, same blind setup, same judge:

| Test | Muse Spark (API, contributor) | Muse Spark Open (Baseten) |
|---|---|---|
| Williams Geismar blind incident study (CSB conclusions reached) | 67 % (3 runs) | 58 % (1 run) |
| 20 real factories (IAC), auditors' measures found, by ARC family | 53 % | 48 % |
| 20 real factories (IAC), savings estimate error (median factor) | 3.5x | 2.9x |

Muse Spark Open finished the full study loop on its own: 28 agent steps, 24 simulator runs including DWSIM, the QA/QC
review and the deliverables. On Williams it made the vapour pressure (about 490 psig) the main mechanism, where the
CSB concluded liquid thermal expansion.

Under a strict JSON schema it sometimes degenerates into whitespace. The client then asks again without the schema
(`plantagent/iac.py`).

## Honest limits

- Pump curves defined by a single rated point are flagged as screening only; firm capacity is solved N-1 in EPANET.
- Surge results are a **pre-screen**. TSNet here has no pump inertia, check-valve dynamics or column-separation model.
- The gravity profile models pipes, weirs, orifices and level controls. It has no open-channel step method.
- Costs are AACE Class 5 at a national-average location, with no contingency or engineering added.
- No InfoWater/WaterGEMS/GIS import yet. The data on the test systems comes from public PDFs, bid sets and benchmark datasets.

## Run it

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                            # then add keys; keep mode 0600
chmod 600 .env
.venv/bin/python -m plantagent.web --port 8765  # open http://127.0.0.1:8765/workspace.html?case=roseburg
.venv/bin/python -m plantagent.study --case roseburg   # a full blind study (about 20 min, about $0.20 on Spark contributor)
.venv/bin/python -m plantagent.grade                   # grade the latest runs against the engineers
```

**From a clean clone, with no API key and no DWSIM:**

- `home.html` and the blind-study replays (`index.html?case=...`) read the committed runs in `runs/`.
- `plant.html?case=chem_c01` shows the agent-built model and its committed answer. The throughput slider replays
  71 precomputed DWSIM solutions (80–150 %).
- Asking, building and accepting need the API key and DWSIM.
- The water workspace needs the public PDFs (URLs in `cases/*/case.json`; PDFs are not redistributed).

Optional tools:

- DWSIM 9 (Linux build) and .NET 8, for process plants (`~/opt/dwsim`, `~/opt/dotnet`)
- ODA File Converter (DWG)
- LibreCAD (CAD round trip)
- `.venv-surge` with `tsnet`, `numpy<2` and `wntr<1.2`, for transients

Muse spend is capped by `MUSE_BUDGET_USD` and logged in `runs/usage.jsonl`. The web UI disables
Muse-spending actions unless `WEB_ALLOW_RUNS=1`. The default server binds only to localhost. A non-local `--host`
requires `WEB_AUTH_TOKEN`; API/file requests then require `Authorization: Bearer <token>`, and POSTs remain disabled
until `WEB_ALLOW_WRITES=1`. Paid calls are serialized across local processes and reserve their worst-case token cost
before sending. Uploaded private projects default to non-contributor Muse Spark; contributor use requires the explicit
`ALLOW_PRIVATE_CONTRIBUTOR=1` override.

## Timeline

Built during the hackathon window. Kickoff was Oct 26, 2026 at 12:00 PM ET; the first source file was created on
Oct 27 at 01:44 Istanbul time (Oct 26, 6:44 PM ET). The first commit (Oct 27) bundles that first night's work, and the git
history shows the order of the work after it.

## Data and credits

The public documents are not redistributed; download them from the URLs in `cases/*/case.json`:

- City of Roseburg 2009 PDR
- St. Petersburg SWWRF 2014
- Battle Creek IFB 2023-040B
- Canal & River Trust / Green WIN audits
- GLWA, CSB, Stanislaus RWA and LBNL reports
- BattLeDIM 2020 (CC BY 4.0)
- CSB Williams Geismar case study (2016)
- DEXPI e.V. TrainingTestCases (reference P&ID C01)
- US DOE ITAC/IAC database (public)

Field photos are from Wikimedia Commons:

- De Laval pump label, by Loozrboy, CC BY-SA 2.0
- Standpipe gauge, by Mark Cross, CC BY 4.0
- others are listed in `case-data/raw/field_photos/SOURCE.txt`

Cost curves:

- TWDB 2024
- City of Phoenix 2024
- US EPA WBS
- EPA-600/2-79-162b

Design rules: Recommended Standards for Water Works (2022) and Wastewater Facilities (2014).
