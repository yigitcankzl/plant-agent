# Generality proof: an unseen DEXPI drawing, no hand-written case files

**Question:** can PlantAgent take a P&ID it has never seen and do the engineering without anyone writing case files?

**Input:** the official DEXPI 1.3 example *C02 Process Column (BASF)*, `C02V03-VER.EX02.xml`, from [gitlab.com/dexpi/TrainingTestCases](https://gitlab.com/dexpi/TrainingTestCases), used unmodified.

**Model:** Muse Spark Open (`baseten:meta-models/muse-spark-open-1026`, open weights on Baseten). No Meta-hosted model was called.

## Why this file
- **C02V01 rejected:** it is the same DEXPI reference plant as our `chem_c01` (same tags, e.g. P4711), so it is not unseen.
- **C08 unavailable:** the repository has no C08.
- **C02V03 chosen:** the BASF column is the only unseen example with a process unit.
- **The drawing gives very little:**
  - one packed column, K 2750: 500 mm inside diameter, 14 m high, a 600 mm section KX 2750
  - design limits −1 to 6 bar and 150 °C, material 1.4571
  - one bottoms line, fluid code 8503
  - three operated valves and two pressure transmitters

  It does not give the feed, the composition, the flows or the duties.

## What was done, and by whom

| Step | How | Hand-written? |
|---|---|---|
| Create the project | `web.new_project` (the upload code path), task type *capacity* | No |
| Data sheet | `tools/onboard_unseen.py` writes every attribute the DEXPI file states into the data-sheet field; no number was typed | No (generated) |
| P&ID drawing | `tools/render_pid.py` renders it from the DEXPI file | No |
| Process model | Muse built a rigorous DWSIM column in 25 tool steps (NRTL, 15 stages, feed on stage 8, total condenser). Because the drawing gives no duty, Muse **assumed** it: water/ethanol, 1,000 kg/h, 85 °C, 3 bar, reflux 1.5. | No (Muse) |
| Discipline files | `drafts.ensure` drafted economics, uncertainty and the operating envelope. Electrical and curves were not drafted: the drawing has no motors, pumps or compressors. | No (deterministic drafts) |
| Engineer confirmation | A scripted "engineer" confirmed three assumptions through `assumptions.confirm` (logged in `assumptions_log.jsonl`): vent design temperature 150 °C, 330 operating days, 10 % discount rate | Scripted confirmation, not authored data |
| Question and loop | "+20 % feed: what limits it first and what does it cost?", then `loop.run` (3 rounds, $8 cap) | No |

The only manual step was choosing this file and starting the script.

## Results
- **Muse's answer:** "K 2750 floods first: the limit is +13 %, not +20 %."
  - At design reflux 1.5 and 1.2× feed, the Fair flood fraction is 0.876 against the 0.80 limit (110 %). Reboiler duty rises from 427 to 570 kW.
- **Verified proposal:** cut reflux to 0.8. DWSIM re-solved it: 120 % is reached (maximum 142 %) and the column runs at 79 % of the flood limit. No capex.
- **Rejected proposal:** a new 600 mm shell. The server's guardrail rejected it every round, because replacing the shell removes, or tries to raise, the existing K 2750 diameter and flood limit. The guardrail is working as designed; replacing equipment is a change the loop cannot verify yet.
- **Engineering loop** (`work/20261101-203737`):
  - Process, robustness (2 of 2 envelope scenarios, draft) and confidence (100 % of 48 uncertainty re-solves, draft) passed.
  - Nothing failed.
  - The status is still **max_rounds**, not *done*, because Muse proposed the rejected shell again in every round, and a rejected proposal counts as an open issue.
- **Disciplines not calculated** (shown as open on the page): mechanical, heat transfer, electrical, combustion, piping, controls, safety and civil. This file carries no data for them.

## Cost

| Step | Baseten USD |
|---|---:|
| Build | 0.7674 |
| Ask | 0.2294 |
| Loop (3 rounds) | 0.5474 |
| **Total** | **1.5442** |

The Baseten ledger went from $18.147 to $19.692.

## Limits (read these before quoting the result)
- **The whole duty is a Muse assumption.** The drawing does not say what the column separates. The +13 % flood limit is a property of the assumed water/ethanol duty on the documented 500 mm shell, not of BASF's real service.
- **Cutting reflux to 0.8 lowers separation, and product purity was not checked.** No purity target is on the drawing, and no check exists for it. An engineer must set the purity specification before this proposal means anything.
- **One provenance tag is wrong.** `economics.throughput.base` (24 t/d) is tagged *documented*, but it comes from Muse's assumed 1,000 kg/h.
- **The loop cannot verify a shell replacement**, so the capex option went to the engineer unverified.
- **One renderer fix was needed.** This exporter writes coordinates in metres. `tools/render_pid.py` now scales padding to the sheet and converts metre sheets to millimetres; before that, the drawing came out about 10 units wide.

## Files
- `runs/ws/basf_process_column_k_2750_dexpi_c02_uns/`: the build run, `answers.json` per session, `work/20261101-203737/worklog.json`, `drafts/`, `assumptions_log.jsonl`, `model.json`
- `cases/basf_process_column_k_2750_dexpi_c02_uns/`: `case.json` and `basis.md` (both generated by `new_project`), `pid.svg` (rendered) and the unmodified DEXPI file. The upload went to the data root; the file was copied next to the case so a fresh clone opens it, and `case.json` `pid` points there. That path edit is the only change made to a generated file.
- `tools/onboard_unseen.py`: the script that ran all of this
