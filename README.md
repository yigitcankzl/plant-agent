# PlantAgent: an AI engineer for any plant

**TL;DR**
- PlantAgent is an engineering workspace for existing plants: you open the plant's drawings and documents and ask an engineering question.
- Meta's **Muse** reads the P&ID and data sheets, builds the simulator model itself, and proposes physical changes.
- Deterministic engines (DWSIM, WaterTAP, EPANET, pandapower, ht/fluids, Cantera) re-solve every proposal before it can be applied; a change that only edits a limit is refused.
- Flagship: a vacuum-salt MVR crystalliser reaches **+20 %** with three verified changes (clean E-201, a parallel compressor K-202, a purge-steam trim). The discipline gates then flag what the process answer alone hides: **TX-1 overloaded (~131–133 %)** and **not robust when E-201 re-fouls**.
- Blind benchmark: on 13 real projects with the engineers' conclusions withheld, Muse reaches **64 %** of them on average (range 33–100 %).

| Muse does | The deterministic engines do |
|---|---|
| Reads P&IDs (DEXPI or PDF), data sheets, reports and photos | Solve the model: DWSIM (process), WaterTAP (RO), EPANET/WNTR and TSNet (water), a gravity profile solver |
| Builds the simulator model and its calibration table | Re-solve every proposal and the combined design on the server before it can be applied |
| Plans the study, chooses which runs to make, proposes the changes | Check limits, relief paths (`pid.relief_scan`), the electrical load flow (pandapower), exchanger detail (ht/fluids) and combustion (Cantera) |
| Writes the answer and drafts the deliverables | Decide pass/fail on the discipline gates; citations and cited runs are checked without an LLM |

> Draft engineering output for review by a licensed professional engineer. It is not a substitute for one.

## Try it in three minutes

Open `web/home.html` and press **Start the 3-minute demo**. It opens the salt crystalliser (`plant.html?case=salt_mvr&tour=1`) and walks through it in six steps: the source P&ID and the model Muse built from it; the +20 % question; what limits it; the fixes, each re-solved in DWSIM; before and after; the evidence.

Then look at:
- **Existing / Proposed** above the drawing: Rev B of the P&ID with the changes clouded.
- **Engineering impact**: one gate per discipline. Click a gate to see its checks and their sources.
- **Decision / Engineering**: the short decision, or the full calculations, alternatives, sources and audit.
- **Issue engineering package**: the MOC pack, pre-FEED gate, vendor RFQ duty sheet and commissioning plan.

## Flagship: salt crystalliser, one change checked across disciplines

`plant.html?case=salt_mvr` is a vacuum-salt plant with a mechanical vapour recompression (MVR) evaporator. It is built from **US Patent 5,366,514** (Texas Brine, 1994), FIG. I and Table I.
- PlantAgent drew the P&ID tags, line numbers and relief settings on the patent's flowsheet.
- Equipment ratings the patent does not give are marked ILLUSTRATIVE.

**Model**
- Muse (muse-wonder-1.0) built the DWSIM model in 1,096 s for $4.03.
- The brine boiling-point elevation (Sparrow 2003) and the brine heat capacity (Laliberte, via WaterTAP) are applied explicitly in `plantagent/brine.py`, because DWSIM's NRTL has no electrolyte parameters.
- The automatic model review caught three modelling errors: a free steam feed, a vapour feed to the purge evaporator, and a free circulation feed. Each was fixed as a recorded correction revision (`runs/ws/salt_mvr/revisions.json`).
- The model is calibrated to Table I: 226.8 t/h to the compressor K-201.

**+20 % salt**
- The first limit is K-201 suction.
- The verified design has three changes:
  - clean E-201 back to its clean U;
  - add a parallel vapour compressor K-202, operating at 48.8 t/h and 2.0 MW in the solve, with a provisional rating of 55 t/h / 2.4 MW for the vendor to confirm;
  - trim the purge-heater steam.
- DWSIM re-solves the combination at 120.1 %.
- From the solve PlantAgent draws Rev B of the P&ID (new lines 3004-ST and 3005-ST, block and check valves on K-202) and writes the data sheet, work order, summary and MOC pack.

**Discipline gates on the same change** (`prefeed.discipline_gates`). Each gate reads a solved state, not LLM text. Pass/fail comes only from a check with a named source; anything over an illustrative rating stays *open*.

| Gate | Result | From |
|---|---|---|
| Process | ✓ reaches 120 % | DWSIM re-solve of the combined changes |
| Robustness | ✕ 3 of 4 operating scenarios pass; fails with E-201 fouled back | DWSIM, pre-FEED operating envelope |
| Mechanical | ○ K-202 within its provisional rating; vendor curve needed | solve vs rating |
| Electrical | ✕ TX-1 45 → ~131–133 %, 29 % start dip direct-on-line; a VFD fixes the dip, not the transformer | pandapower on an illustrative one-line diagram |
| Heat transfer | ○ E-201 needs 7,130 of 8,800 m² clean; pump and shell-side ratings illustrative | ht/fluids (Gnielinski, Bell-Delaware) |
| Combustion | ○ +20 % steam needs about 10.1 MMBtu/h (3.0 MW) of duct firing on the proposed design | Cantera GRI-Mech 3.0 |
| Piping, controls, safety, civil | ○ no calculation adapter; listed as open work | change register |

The MOC pack carries the failed gates as risks and its decision reads "Do not approve yet".

**Fouling forecast** (`plantagent/forecast.py`, no LLM)
- It fits E-201's U from the historian.
- It then bisects the model for the U at which the first limit reaches 100 % at today's throughput.
- The historian is **SYNTHETIC** and the prices behind the daily loss are **illustrative**.

## Second opinion: two models, one simulator

`plant.html?case=chem_c01` opens a chemical unit from its **DEXPI P&ID** (the DEXPI e.V. reference example C01). Its operating data sheet is illustrative, written for this demo, and the page says so.

- Muse (Spark, contributor) built the DWSIM model in 221 s for $0.0095.
- **P&ID reader** (`plantagent/pid.py`, standard library only). It flags inconsistent design data, for example:
  - a pump whose 60 kW shaft power implies 9 % efficiency;
  - a tank whose dimensions give 1,257 m³ against a stated 26 m³.
- **+20 %: two changes are enough.** Cooling water 20 → 27 m³/h (90 % of the branch supply), and tank working level 80 → 85 % (the documented maximum).
  - DWSIM re-solves the unit at 120 %, with a new maximum of 124 % set by the tank hold time.
  - Muse's first answers also raised the H1008 chilled water to 18 m³/h. The re-solve gives the same 124 % without it.

Tick **+ open-model second opinion** and **Muse Spark Open** (open weights, on Baseten) answers the same request independently, on the same model and tools. A deterministic comparison, with no third model involved, checks five things: the limiting equipment, each change (same path, values within 10 %), which proposals verify, the target verdict and the stated energy saving.

| Case | Agree | Disagree |
|---|---|---|
| Chemical unit, +20 % | Cooling water to 27 m³/h and tank level up; both reach 120 % (124 % max) | Muse Spark also raised the H1008 chilled water. The open model left it out, and the re-solve shows the open model's fix was the cheaper one |
| Dairy refrigeration, N+1 and floating head | The new load fits with N+1; the condensers are the closest limit | Annual saving 1,716 MWh (Spark) vs 1,330 MWh (Open). A direct bin calculation gives 1,329 MWh, so the open model was right here |

Neither model is always right; the engineer is shown the disagreements (`runs/ws/*/second_opinion_answer.json`).

## Blind test vs the 2008 pilot decision

`plant.html?case=swro_brownsville` screens the 2004 Brownsville 25 MGD seawater concept in WaterTAP.
- The membrane coefficients are illustrative, calibrated at the study's average condition (75 F, 36,100 mg/L) to 60.5 % recovery.
- The WaterTAP model is a deterministic screening template, not built by Muse.
- Muse was asked whether the concept holds at the cold, salty corner of the record (60 F, 49,000 mg/L).

Muse's answer: **no**. Recovery reaches only 47.2 % and permeate 0.539 g/L at the documented pressure cap, so 25 MGD is provisional until a vendor or pilot membrane projection exists.

The 2008 pilot report (`cases/swro_brownsville/hidden_outcome.md`) was withheld from the agent.
- **What matched:** the pilot also did not go straight to 25 MGD. It found the source difficult and a full-scale design possible only if conservative.
- **What the agent did not reach:**
  - the pilot's recommendation of a phased 2.5 MGD demonstration plant;
  - its post-treatment and concentrate findings, which came from pilot data the agent never had.

**Monterey** (`swro_monterey`), a second RO screen: nine first-pass trains with one out, 8.66 vs 8.75 gfd maximum average flux at 12.8 MGD. Second-pass performance and boron are not claimed.

## Evidence: blind benchmark against real engineers

On each real project the pages holding the engineers' conclusions are **withheld** from the agent: recommendation clauses are redacted, and a leak check runs against the answer key. The agent does the study, and **muse-wonder-1.0**, a different model, grades its findings against the engineers' conclusions.

- **Scope:** 13 graded cases and 6 task types (capacity, troubleshooting, energy audit, surge, failure investigation, force-main design), covering water and wastewater, canal pumping, campus cooling, a data centre, a gas plant and an olefins plant.
- **Score:** the latest Muse Spark run per case averages **64 %** of the engineers' conclusions (n = 13, range 33–100 %). Open-weights runs are reported separately.
- **Run-to-run variance is large.** Roseburg, with strict redaction and four independent runs, scored 93 %, 64 %, 57 % and 50 %. The latest run is the one counted.
- **Judge check:** every graded run was re-graded by muse-spark-1.3. It agreed on 88 % of 134 items, and the mean moved from 66 % to 64 % (`evidence/judge_agreement.json`). This shows consistency between models; it is not a human check.
- **CSB incidents:**
  - Pascagoula scored 67 % with the water-network tools, then 92 % and 83 % with the DWSIM process tools; the latest, 83 %, is counted.
  - Williams Geismar scored 67 % in all three Muse Spark runs. One run computed a blocked-in expansion pressure of 6,260 psig, against the CSB's estimate of about 5,000 psig.
- **Contamination check:** with no documents, Muse says it does not know the Roseburg report's conclusions (`evidence/contamination_check.json`).
- **Cost:** a full blind study costs $0.04–0.64 on Muse Spark (median $0.10 over 22 runs).
- **Records:** results, per-run deliverables and grades are in [`evidence/`](evidence/README.md).

**NETL design reproduction** ([`evidence/designcheck/`](evidence/designcheck/README.md)) compares agent-built DWSIM outlet states with withheld published stream tables, using deterministic thresholds:

| NETL 2022 Case 2 section | Supplied-inlet conservation | Inferred outputs, Muse Spark | Inferred outputs, Muse Spark Open |
|---|---:|---:|---:|
| Syngas cooler (8→9) | 8/8 within ±10 % | 0/2 | 0/2 |
| CO2 compression/drying (18+19→20) | 2/2 within ±10 % | 3/5 | 2/5 |

**A negative result we report:** on 20 real factories from the US DOE Industrial Assessment Center database, Muse was given only the plant profile and utility bills.
- It named 47–53 % of the auditors' measures.
- A plain base-rate baseline named 54 %.
- Its savings estimates were off by about 4×.

We do not claim this capability.

**Open weights.** The same agent runs on Muse Spark Open (`baseten:meta-models/muse-spark-open-1026`): same tools, same blind setup, same judge.

| Test | Muse Spark | Muse Spark Open |
|---|---|---|
| Williams Geismar, CSB conclusions reached | 67 % (3 runs) | 58 % (1 run) |
| 20 factories (IAC), auditors' measures found | 53 % | 48 % |
| 20 factories (IAC), median savings error | 3.5× | 2.9× |

The open model sometimes writes a tool call as text (`<x:invoke ...>`). The loop recovers it (`study.text_tool_calls`).

## What the workspace does

| | |
|---|---|
| **Ask / Fix / Get me to target** | Muse plans, reads, simulates and proposes. A proposal can be applied only if the solver reproduces it; the server re-checks before writing. |
| **Live load on the P&ID** | Each item shows its load; the throughput slider re-solves the model (DWSIM about 0.3–0.5 s). |
| **Citation and solver check** | No LLM involved. Cited runs must exist and re-solve to the same result; cited page values must appear on the page. |
| **Draft revisions and audit** | Applying a change needs a reason and creates a draft revision, not an approval. Undo on process plants adds a revert revision. Audit entries are hash-chained (`plantagent/audit.py`). |
| **Provisional answers** | When a deciding value is missing, the answer says so and lists field checks: what to measure, where, and which conclusion it would change. |
| **Drawing reading** | DEXPI XML, or a PDF/scanned sheet read by Muse vision as a full sheet plus zoomed tiles, reconciled (Roseburg: 35/35 elevations agree). |
| **Field photo, voice** | A nameplate or gauge photo read by Muse against a schema, with plausibility checks. Push-to-talk through Muse Voice Transcribe. |
| **CAD round trip** | Exports editable DXF/DWG; edits dropped back become revisions and the model is re-solved. |
| **Deliverables** | Water: memo, calc sheets, redlined DWG, profile sheet, pump data sheets, test plan, AACE Class 5 cost, Ten States Standards check. Process: data sheet, work order, summary, Rev B P&ID, MOC pack, pre-FEED gate, RFQ duty sheet, commissioning plan. |

## Under the hood

**DWSIM layer** (`plantagent/process.py`) runs headless through pythonnet, as one long-lived worker.
- **Unit operations:** pumps (centrifugal or positive displacement), rated heat exchangers, heaters and coolers, valves, tanks, mixers, splitters, compressors, an evaporator with brine BPE, and recycle loops.
- **Limits checked:**
  - pump rated and minimum flow, motor power, NPSH, and relief margin;
  - compressor power and discharge temperature;
  - exchanger area, with U and ΔP following flow;
  - hold time, utilities at no more than 90 % of supply;
  - the API 521 blocked-in check, in both regimes.
- **Other tools:** a capacity search, bubble point, fluid properties, control-valve Cv and travel, Darcy-Weisbach pipe segments, and annual energy by bins.

**Pre-FEED gate** (`plantagent/prefeed.py`) turns a verified design into a deterministic draft gate:
- up to 24 clean/fouled, min/normal/max and off-design scenarios;
- mass closure;
- a new-equipment screen and a preliminary data sheet;
- a change-focused HAZOP and relief register (P&ID tags only);
- tie-ins, outage and unpriced cost items;
- a vendor RFQ duty sheet and a commissioning acceptance plan, which closes only on sourced field observations.

It makes no paid model call.

**Safety and records**
- **Relief scan** (`pid.relief_scan`, no LLM) finds equipment sides that can be blocked in without a relief path. On C01 it finds both coolers' water sides unprotected on the drawing (the API 521 blocked-in cooling-water case).
- **Coverage check** compares the model with the P&ID line by line. An earlier chem_c01 model put H1008 in series instead of in the recirculation loop (`runs/ws/chem_c01/model_v1_series.json`). A practitioner review caught it, which is why the check exists.

**Data centre (IIT Kanpur), a gap we report.** Muse read the liquid-cooling schematic correctly. Five model builds were still not usable: the chillers were missing, or the loop flows were wrong. No capacity answer is shown for that case.

## Limits and honesty

- **Illustrative and synthetic inputs are labelled where they appear.** Labelled data includes:
  - the chem_c01 data sheet;
  - salt ratings the patent does not give, and its one-line diagram;
  - the salt historian, which is **SYNTHETIC**;
  - fouling prices;
  - RO membrane coefficients.
- **The model's calibration table** compares measured values with the solved model. Some of those values are model inputs, and the table marks which.
- **"Verified" means process-verified.** Other disciplines are shown next to it as gates, and an electrical or robustness fail is never hidden by a process pass.
- **DWSIM is steady state.** Valve and pipe calculations are incompressible-liquid screens. The solve scales exchanger U from one test point; the ht/fluids check computes U from geometry and flags any disagreement.
- **Surge is a pre-screen.** TSNet has no pump inertia or column separation.
- **The gravity profile has no open-channel step method.**
- **Costs are AACE Class 5, with no contingency.**
- **No vendor curves, no rigorous dynamics, no multidisciplinary HAZOP, no relief sizing.** Everything PlantAgent produces is a draft for a licensed engineer.

## Run it

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env && chmod 600 .env          # then add keys
.venv/bin/python -m plantagent.web --port 8765  # open http://127.0.0.1:8765/home.html
.venv/bin/python -m plantagent.study --case roseburg   # a full blind study (about 20 min, $0.04–0.64)
.venv/bin/python -m plantagent.grade                   # grade the latest runs against the engineers
```

**From a clean clone, with no API key and no DWSIM**
- `home.html`, the blind-study replays and the committed process answers can be browsed.
- The throughput slider replays precomputed solutions.
- Asking, building and applying changes need the API key and DWSIM 9 with .NET 8.
- Optional: ODA File Converter (DWG), LibreCAD, and `.venv-surge` with TSNet.
- Public PDFs are not redistributed; their URLs are in `cases/*/case.json`.

**Money and access**
- Muse spend is capped by `MUSE_BUDGET_USD` and logged in `runs/usage.jsonl`.
- The page header's **AI cost** is the Muse spend of the questions on record for that case. Model builds are listed separately on the case.
- Muse-spending actions are disabled unless `WEB_ALLOW_RUNS=1`.
- The server binds to localhost by default. A non-local `--host` requires `WEB_AUTH_TOKEN`, and writes need `WEB_ALLOW_WRITES=1`.
  The stock browser UI does not send the bearer header, so a remote deployment needs a reverse proxy that adds it.
  POSTs must be same-origin `application/json` (form and cross-site posts are refused), and a local server only answers its own host name.

## Timeline

Built during the hackathon window. Kickoff was Oct 26, 2026 at 12:00 PM ET. The first source file was created on Oct 27 at 01:44 Istanbul time (Oct 26, 6:44 PM ET). The git history shows the order of the work.

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
- US Patent 5,366,514 (Texas Brine)
- Brownsville PUB / TWDB seawater desalination feasibility study (2004) and pilot report (2008)
- US DOE ITAC/IAC database
- NETL 2022 baseline report

Field photos are from Wikimedia Commons (De Laval pump label by Loozrboy, CC BY-SA 2.0; standpipe gauge by Mark Cross, CC BY 4.0; others are listed in `case-data/raw/field_photos/SOURCE.txt`).

Cost curves: TWDB 2024, City of Phoenix 2024, US EPA WBS, EPA-600/2-79-162b. Design rules: Recommended Standards for Water Works (2022) and Wastewater Facilities (2014).
