# PlantAgent: an AI engineer for any plant

PlantAgent opens a plant the way an engineer does: from its drawings, P&IDs, reports, bid documents and SCADA data.
It covers water and wastewater plants, chemical process units, petrochemical incidents, campus cooling, data centers and
pumping stations (open `web/home.html`). You ask a question ("Can this plant make 18 MGD?"), or click an issue and press **Fix**. Meta's **Muse**
models read the documents and the drawing, then run real simulators:

- **EPANET** for pumped systems
- a gravity hydraulic-profile solver
- **TSNet** transients
- extended-period SCADA calibration

The answer comes back as a **proposed change verified in the simulator**. The engineer accepts or rejects it, like a
code diff, and accepted changes are drawn on the real sheet and exported as **DWG**. Every number cites a page or a
simulator run.

> Draft engineering output for review by a licensed professional engineer. It is not a substitute for one.

## Process plants: from a smart P&ID to a verified fix

`web/plant.html?case=chem_c01` opens a chemical unit from its **DEXPI P&ID**, the vendor-neutral P&ID exchange standard.

- The reader (`plantagent/pid.py`, standard library only) turns the P&ID into equipment with design data, connections,
  valves and control loops. It reads all 18 vendor exports in the DEXPI test set.
- **Muse builds the DWSIM model itself** from the P&ID and the operating data sheet. It maps every tag to a unit,
  includes every rating as a limit, and calibrates against the measured temperatures (34 vs 33.9 C, 18 vs 18.4 C).
  This took 136 s and cost $0.006.
- Each equipment item on the P&ID shows its live load. The throughput slider re-solves DWSIM in about 0.3 s.
- **"Get me to target"**: Muse finds that both coolers limit +20 % throughput. It proposes the cheapest fixes, raising
  cooling water to 30 m3/h and chilled water to 20 m3/h within the data-sheet supply limits.
- The workspace re-solves each proposal in DWSIM before it can be accepted, and then all of them together: the unit
  reaches 120 % and the new maximum is 125 %.
- Accepted changes become revisions that can be undone.
- The P&ID is the DEXPI e.V. reference example. Its operating data sheet is illustrative and labelled as such.

DWSIM (`plantagent/process.py`) runs headless through pythonnet as one long-lived worker. It provides:

- pumps, heat exchangers in rating mode, heaters and coolers, valves, tanks, mixers, splitters and compressors
- required exchanger area against installed area
- a throughput capacity search
- bubble-point pressure and fluid properties

The same tools are available in blind studies (`"simulators": ["dwsim"]`).

## What it does

| | |
|---|---|
| **Engineering workspace** (`web/workspace.html`) | The real AutoCAD sheet with live water-surface gauges and capacity by unit. Each value is marked ● simulated or ○ documented. Also: water-surface and demand charts, plus Existing / Proposed views and a revision timeline. |
| **Ask / Fix / Get me to target** | Muse plans, reads, simulates and proposes. A proposal can be accepted only if the solver reproduces it, and the server re-checks before writing. |
| **Second-engineer check** | A deterministic check, not another LLM. Cited runs must exist in the log, cited page values must appear on the page, and proposals must reproduce in the solver. |
| **Drawing reading** | The sheet is read twice by Muse vision, as a full sheet and as zoomed tiles, and the two reads are reconciled. Roseburg: 35/35 elevations agree. An unseen sheet takes about 37 s. |
| **Field photo** | Muse reads a pump nameplate or gauge against a JSON schema. A specific-speed check and a letter-O/zero check catch misreads. The reading is matched to a model pump and applied as a logged revision. Writes are blocked when the reading is more than 2× off or overloads the motor. |
| **Voice** | Push-to-talk, transcribed by Muse Voice Transcribe. |
| **CAD round trip** | Exports an editable DXF/DWG (model parameters on layer `PA-PARAMS`). The engineer edits it in AutoCAD or LibreCAD and drops it back; changes become revisions and the model is re-solved. |
| **Deliverables** | Memo, calc sheets (xlsx), redlined DWG, a new hydraulic-profile sheet, pump data sheets, a field test plan, a cost estimate (published curves, ENR, full AACE band) and a Ten States Standards check. Each report ends with a scenario register, units/datum and a sign-off block. |

## Evidence: blind benchmark against real engineers

On each real project, the pages holding the engineers' conclusions are **withheld** from the agent. Recommendation
clauses are redacted, and a leak check runs against the answer key. The agent then does the study, and
**muse-wonder-1.0**, a different model from the agent, grades its findings against the engineers' conclusions.

- 12 cases, 6 task types: capacity, troubleshooting, energy audit, surge, failure investigation, force-main design.
- **Run-to-run variance (Roseburg, strict redaction, 3 independent runs):** 93%, 64% and 57% of the engineers'
  conclusions, mean 71%. The earlier Roseburg runs (57%, 71%, 79%) used a looser redaction that left hint sentences
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

## Honest limits

- Pump curves defined by a single rated point are flagged as screening only; firm capacity is solved N-1 in EPANET.
- Surge results are a **pre-screen**. TSNet here has no pump inertia, check-valve dynamics or column-separation model.
- The gravity profile models pipes, weirs, orifices and level controls. It has no open-channel step method.
- Costs are AACE Class 5 at a national-average location, with no contingency or engineering added.
- No InfoWater/WaterGEMS/GIS import yet. The data on the test systems comes from public PDFs, bid sets and benchmark datasets.

## Run it

```bash
python -m venv .venv && .venv/bin/pip install openai wntr pymupdf ezdxf openpyxl matplotlib scipy pillow fluids pythonnet pandas
echo "META_API_KEY=..." > .env                 # Meta Model API key
.venv/bin/python -m plantagent.web --port 8765  # open http://127.0.0.1:8765/workspace.html?case=roseburg
.venv/bin/python -m plantagent.study --case roseburg   # a full blind study (about 20 min, about $0.20 on Spark contributor)
.venv/bin/python -m plantagent.grade                   # grade the latest runs against the engineers
```

Optional tools:

- DWSIM 9 (Linux build) and .NET 8, for process plants (`~/opt/dwsim`, `~/opt/dotnet`)

- ODA File Converter (DWG)
- LibreCAD (CAD round trip)
- `.venv-surge` with `tsnet`, `numpy<2` and `wntr<1.2`, for transients

Muse spend is capped by `MUSE_BUDGET_USD` and logged in `runs/usage.jsonl`.

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
