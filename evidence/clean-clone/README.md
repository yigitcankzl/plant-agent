# Clean-clone browser proof

## Proposed-design replay follow-up (2026-11-03)

Commit `9b7f0cd` adds a separate `proposed_states.json` replay for Salt MVR, chem C01 and BASF C02. Each file contains the featured verified design solved by DWSIM on the same 71-point, 0.80–1.50 throughput grid as `states.json`. The files are 412, 380 and 346 KiB respectively. They do not replace or alter the existing-plant replay.

The follow-up was checked in a fresh clone inside the same `python:3.12-slim` image described below, with an empty home, no `.env`, no external case-data directory, no .NET and `process.available() == False`. The server ran with `WEB_ALLOW_RUNS=0`. The complete browser audit remained **29 pass, 0 warnings, 0 failures**. A focused 1920×1080 check produced this before/after result at 120% throughput:

| Case | Before: Proposed geometry with existing loads | After: stored proposed design | Stored proposed capacity |
|---|---:|---:|---:|
| `salt_mvr` | K-201 120% | K-201 100% | 120.1% |
| `chem_c01` | H1007 106% | cooling-water supply 100% | 124.2% |
| `basf_process_column_k_2750_dexpi_c02_uns` | K-2750 flood 110% | K-2750 flood 69% | 175.0% |

The canvas now names the source as `Stored DWSIM · proposed design`; the result summary uses the proposed capacity rather than today's capacity. When no simulator is installed, engine-dependent controls are disabled and explain that stored results remain replay-only. `redline.html` now uses the plant workspace's dark palette, and its deterministic design-check button is disabled with the same simulator explanation.

Reproduction commands for the new stores and browser proof:

```sh
.venv/bin/python -m plantagent.plant --precompute-proposed salt_mvr
.venv/bin/python -m plantagent.plant --precompute-proposed chem_c01
.venv/bin/python -m plantagent.plant --precompute-proposed basf_process_column_k_2750_dexpi_c02_uns

node tools/clean_clone_audit.js http://127.0.0.1:8783 \
  /tmp/proposed-clean-clone.json /tmp/proposed-clean-clone
node tools/ui_smoke.js http://127.0.0.1:8784 /tmp/proposed-cache-ui-smoke
```

Focused screenshots are in `/tmp/proposed-cache-before/` and `/tmp/proposed-cache-after/`; the updated redline smoke screenshot is `/tmp/proposed-cache-ui-smoke/engineer_redline_stub.png`. Full tests: **318 tests, OK (21 skipped)**. The UI smoke passed every check.

Test date: 2026-11-02. Baseline commit: `fad11b20c2140ed1f147fa184fb53eb87370f083`.
Fixes tested at `42f1082` on `codex/clean-clone-proof`.

Image: `python:3.12-slim`, digest `sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30`.
The clone had no `.env`, source-document directory, DWSIM, .NET, pandapower venv or WaterTAP venv. The standard requirements do install WNTR, Cantera and other Python libraries, so “no engines” here means no separately installed engine runtimes; it does not mean no numerical Python packages.

## Commands and isolation

The first container used a read-only local Git source mount (`/source` was `/home/kizil/Desktop/hackathon/plant-agent`). Git was installed only to execute the clone. The clone copies tracked files, so the source checkout's untracked `.env` was not copied; no key value was read or passed to the application. The final browser run used a clone-only mount with no `/source` mount and a fresh empty home.

```sh
docker run -d --name plantagent-clean-clone --network host \
  -e HOME=/tmp/empty-home \
  -v /home/kizil/Desktop/hackathon/plant-agent:/source:ro \
  python:3.12-slim sleep infinity
docker exec plantagent-clean-clone sh -lc \
  'apt-get update && apt-get install -y --no-install-recommends git'
# Match the local repository owner so Git can read it without a safe.directory override.
docker exec plantagent-clean-clone sh -lc \
  'mkdir -p /workspace /tmp/empty-home && chown -R 1000:1000 /workspace /tmp/empty-home'
docker exec -u 1000:1000 plantagent-clean-clone sh -lc '
  git clone /source /workspace/plant-agent
  cd /workspace/plant-agent
  test ! -e .env && test ! -e ../case-data
  python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
  .venv/bin/python -m plantagent.web --port 8765'
node tools/clean_clone_audit.js http://127.0.0.1:8765 \
  /tmp/clean-clone-baseline.json /tmp/clean-clone-baseline
```

The README's top quick-start commands were used verbatim after cloning. Its later `cp .env.example .env` instruction belongs to live usage and was intentionally omitted for this no-key test. Host networking preserves the README's default localhost bind. Port 8765 was free before the task started.

After installing the requirements once, the final verification reused exactly that installed venv read-only in a second `python:3.12-slim` container. The fixed branch was freshly cloned to `/tmp/plantagent-clean-final`, mounted at `/workspace/plant-agent`; the installed venv was mounted at the same absolute path. The final home was `/tmp/judge-home`, with no source-repository mount. This avoided duplicating the environment after a Docker image snapshot exhausted the host disk. The temporary snapshot was removed.

```sh
git clone --no-hardlinks /home/kizil/.codex/worktrees/clean-clone-proof/plant-agent \
  /tmp/plantagent-clean-final
# <installed-venv> is the first container's /workspace/plant-agent/.venv,
# obtained from its Docker inspect GraphDriver.MergedDir.
docker run -d --name plantagent-clean-final --network host \
  -e HOME=/tmp/judge-home \
  -v /tmp/plantagent-clean-final:/workspace/plant-agent \
  -v <installed-venv>:/workspace/plant-agent/.venv:ro \
  python:3.12-slim sh -lc 'mkdir -p /tmp/judge-home && cd /workspace/plant-agent &&
    test ! -e .env && test ! -e ../case-data &&
    .venv/bin/python -m plantagent.web --port 8765'
node tools/clean_clone_audit.js http://127.0.0.1:8765 \
  /tmp/clean-clone-fixed.json /tmp/clean-clone-fixed
```

Playwright ran on the host with Chromium, at 1440×900. Each page used a fresh browser page; the audit captured console errors, uncaught JavaScript exceptions, failed requests, HTTP >=400 API responses, broken images and loading failures. Screenshots are in `/tmp/clean-clone-baseline/` and `/tmp/clean-clone-fixed/`.

## Page results

All URLs below are relative to `http://127.0.0.1:8765/`. “Pass” means the stored replay loaded without browser/API errors; the limitations column remains part of the result.

| Page | Baseline | After fixes | Visible limitation / observation |
|---|---|---|---|
| `home.html` | Pass | Pass | Cards and stored evidence load. |
| `plant.html?case=salt_mvr` | API 500 | Pass | Proposed drawing available; load colours fall back to today's stored plant, explicitly labelled. |
| `plant.html?case=salt_mvr&tour=1` | API 500 | Pass | All six tour steps complete without JavaScript errors; proposed live solve unavailable. |
| `plant.html?case=basf_process_column_k_2750_dexpi_c02_uns` | API 500 | Pass | Proposed geometry available; live proposed-state solve unavailable. |
| `plant.html?case=salt_mvr_vision` | Case unavailable | Pass | Labelled source-drawing placeholder; model and stored read remain accessible. |
| `plant.html?case=ucte_2006` | Pass | Pass | Stored incident states. |
| `plant.html?case=freeport_lng_2022` | Pass | Pass | Stored incident states; ideal-relief capacity limitation remains labelled. |
| `plant.html?case=nrel_ethanol_a300` | Pass | Pass | Stored model and parity chart. |
| `plant.html?case=nrel_ethanol_a500` | Pass | Pass | Stored model and parity chart. |
| `plant.html?case=chem_c01` | API 500 | Pass | Proposed live solve unavailable; today's stored loads are labelled. |
| `plant.html?case=swro_brownsville` | Pass | Pass | Stored WaterTAP results. |
| `plant.html?case=swro_monterey` | Pass | Pass | Stored WaterTAP results. |
| `plant.html?case=dairy_refrig` | Pass | Pass | Stored results. |
| `review.html?case=salt_mvr` | Pass | Pass | Read-only inspection of stored sign-off, failed checks and package links. No approval written. |
| `scan.html?case=salt_mvr_vision` | Broken source image / API 500 | Pass | Source placeholder; 13 stored tags, nine corrections, story finishes. |
| `plant.html?case=ucte_2006&present=1&story=openweights` | Pass | Pass | Story reaches “N-1: 0 violations”. |
| `index.html?case=briare` | Pass | Pass | Stored blind study. |
| `index.html?case=caen_hill` | Pass | Pass | Stored blind study. |
| `index.html?case=csb_pascagoula` | Pass | Pass | Stored blind study. |
| `index.html?case=glwa_120in_break` | Pass | Pass | Stored blind study. |
| `index.html?case=goochland_egps` | Pass | Pass | Stored blind study. |
| `index.html?case=greenwin_crissey` | Pass | Pass | Stored blind study. |
| `index.html?case=kstate_chw` | Pass | Pass | Stored blind study. |
| `index.html?case=lbnl_gsa_dc` | Pass | Pass | Stored blind study. |
| `index.html?case=roseburg` | Broken source image / API 500 | Pass | Stored replay works; unavailable source drawing is now stated in text. |
| `index.html?case=stanislaus_surge` | Pass | Pass | Stored blind study. |
| `index.html?case=stpete_swwrf` | Broken source image / API 500 | Pass | Stored replay works; unavailable source drawing is now stated in text. |
| `index.html?case=west_norriton` | Pass | Pass | Stored blind study. |
| `index.html?case=williams_geismar` | Pass | Pass | Stored blind study. |

The home page links the plant pages and study replays. The scan and open-weights story URLs were also tested explicitly, although the current home page does not directly link those story URLs.

Final automated total: **29 pass, 0 warnings, 0 failures; 0 console errors, 0 uncaught page errors and 0 HTTP-failing API calls.** Raw per-page records: `baseline.json` and `fixed.json`. This total measures page loading; the visible engineering limitations in the table are not counted as browser errors.

## Fixes and tests

- `plantagent/web.py`: unavailable DWSIM/.NET preview returns structured `{error, unavailable: true}` rather than HTTP 500. Unexpected runtime errors still propagate. The existing client then displays its labelled existing-state fallback.
- `plantagent/web.py`: a missing public PDF returns a labelled PNG placeholder and appends the missing-source explanation to project data. This prevents a missing drawing from aborting the entire stored model page.
- `plantagent/web.py` and `web/index.html`: study detail advertises a drawing only when the source PDF exists; otherwise the replay shows an explicit missing-source note.
- Only the README's clean-clone section was edited, to distinguish existing-state replay from proposed-state re-solves.
- `tools/clean_clone_audit.js` records the reproducible per-page browser audit.
- Regression tests: missing coreclr / unavailable preview, placeholder PNG, and missing study source. `tests.test_web_security`: **19 tests, OK**, both on the host and inside the slim container.

## Artefacts and remaining work

No existing-state DWSIM store was missing or regenerated. The four inspected process stores each contain 71 points from 0.80 to 1.50:

- `runs/ws/salt_mvr/states.json`
- `runs/ws/chem_c01/states.json`
- `runs/ws/basf_process_column_k_2750_dexpi_c02_uns/states.json`
- `runs/ws/salt_mvr_vision/states.json`

For future refreshes, the existing producer is `.venv/bin/python -m plantagent.plant --precompute <case>` on a host with DWSIM. Do not run it in this environment.

The proposed slider replay gap described in the original audit is closed by the 2026-11-03 follow-up above. The stores retain the exact verified combined specification and are rejected when that specification changes.

Missing source drawings require downloading the URLs in `cases/salt_mvr_vision/case.json`, `cases/roseburg/case.json` and `cases/stpete_swwrf/case.json` into their configured `PLANTAGENT_DATA_ROOT` paths. They do not require DWSIM. No PDF was added.

The mixed proposed-geometry/existing-load view and clickable no-engine actions described in the original audit are also closed by the follow-up. Stored Ask history remains readable, while new simulator-dependent actions stay disabled.
