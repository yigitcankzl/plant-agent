# Running PlantAgent

**From a clean clone, with no API key and no separately installed engines** (tested in `python:3.12-slim` with an empty `$HOME`; the requirements still install numerical Python libraries)
- Works from the stored results: `home.html`; `plant.html?case=salt_mvr` and its guided tour (`&tour=1`); `ucte_2006`; `freeport_lng_2022`; `nrel_ethanol_a300` and `nrel_ethanol_a500`; `basf_process_column_k_2750_dexpi_c02_uns`; `chem_c01`; `swro_brownsville`; `swro_monterey`; `dairy_refrig`; and the `index.html` blind-study replays. The throughput slider replays precomputed **existing-plant** solutions. Proposed designs without a stored proposed-state file are labelled as unavailable and show today's plant; re-solving them needs the named engine.
- The project-drawn P&IDs ship in `cases/<case>/pid.xml`. The DEXPI examples C01 and C02 ship under CC BY 4.0 (`DEXPI-NOTICE.md` in each case).
- Public source PDFs are not redistributed; their URLs are in `cases/*/case.json`. Cases that read them (roseburg, stpete_swwrf, edgebrook, dc_iitk) need `PLANTAGENT_DATA_ROOT` pointing at the downloaded files (default `../case-data` next to the repo) and `poppler-utils` (`pdftotext`, `pdftoppm`).
- Stored replay is read-only usage: Ask is disabled, while applying changes, arbitrary what-ifs and issuing a new engineering package need the engines. Some of those controls remain visible and report the missing engine when used. The Proposed drawing can still be selected while the verdict labels its loads as today's plant. The vision case uses a labelled placeholder when its public patent scan is absent. Browser results and remaining limits: [`evidence/clean-clone/`](../evidence/clean-clone/README.md).

**Engines, for asking, building and applying changes** (plus a Muse key in `.env`)
- DWSIM 9 under `~/opt/dwsim/usr/local/lib/dwsim` and .NET 8 under `~/opt/dotnet` (paths in `plantagent/process.py`).
- pandapower in its own venv: `uv venv .venv-electrical --python 3.12 && uv pip install --python .venv-electrical -r requirements-electrical.txt`.
- pyDEXPI in its own venv, so an uploaded DEXPI P&ID is drawn as SVG (Rev B clouds on new plants): `uv venv .venv-pid --python 3.12 && uv pip install --python .venv-pid pydexpi` (or set `PID_RENDER_PYTHON`).
- WaterTAP in its own venv: `python3 -m venv .venv-watertap && .venv-watertap/bin/pip install -r requirements-watertap.txt`.
- Optional: ODA File Converter (DWG), LibreCAD, and `.venv-surge` with TSNet.

**Money and access**
- Muse spend is capped by `MUSE_BUDGET_USD` and logged in `runs/usage.jsonl`.
- The page header's **AI cost** is the Muse spend of the questions on record for that case. Model builds are listed separately on the case.
- Muse-spending actions are disabled unless `WEB_ALLOW_RUNS=1`.
- The server binds to localhost by default. A non-local `--host` requires `WEB_AUTH_TOKEN`, and writes need `WEB_ALLOW_WRITES=1`.
  The stock browser UI does not send the bearer header, so a remote deployment needs a reverse proxy that adds it.
  POSTs must be same-origin `application/json` (form and cross-site posts are refused), and a local server only answers its own host name.
- One server process is for one trusted team/project: workspaces and jobs are process-local and are not tenant-isolated. Separate deployments are required for unrelated users.
