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
- **Initially rejected proposal:** a new 600 mm shell. At the time, the guardrail correctly refused a plain limit edit but had no explicit replacement change. `replace_unit` now re-solves the new geometry while keeping vendor confirmation open; the later loop below verifies the 600 mm shell.
- **Engineering loop, first run** (`work/20261101-203737`, before the purity check existed):
  - Process, robustness (2 of 2 envelope scenarios, draft) and confidence (100 % of 48 uncertainty re-solves, draft) passed.
  - Nothing failed.
  - The status is still **max_rounds**, not *done*, because Muse proposed the rejected shell again in every round, and a rejected proposal counts as an open issue.

## Product purity added afterwards: the reflux cut does not hold

The first loop "verified" cutting reflux 1.5 → 0.8 without looking at product purity. A purity and minimum-reflux check now runs on every column (`designchecks.purity_checks`, test `tests/test_purity.py`):
- **Spec:** the drawing gives none, so a draft (`drafts/purity.json`, *draft (assumed values)*) holds today's key-component purity within 0.5 mass-% points: distillate ethanol ≥ 90.8 % (today 91.3 %), bottoms water ≥ 23.8 % (today 24.3 %). An engineer must replace it with the real specification.
- **Minimum reflux:** DWSIM bisection on reflux for the column as built (15 stages, same reboiler spec) at the target throughput.

**Deterministic re-check of the stored design (no model call):**

| Check at 120 % | Result |
|---|---|
| Flooding | 63.3 % of flood vs 80 % limit: pass |
| Distillate ethanol | 90.3 vs 90.8 mass-% minimum: **fail** |
| Bottoms water | 25.4 vs 23.8 mass-% minimum: pass |
| Reflux | 0.8 vs **1.10** minimum to hold the spec: **fail** |

So the reflux cut buys throughput by spoiling the overhead product. A direct DWSIM sweep at 120 % shows a valid no-capex window does exist: reflux 1.10 holds the spec at 73.6 % of flood, reflux 1.15 at 75.3 %, while reflux 1.5 floods (87.6 %). The stored "verified" proposal is withdrawn; reflux ≈ 1.1–1.15 is the candidate for the next run.

**Second loop with the check in place** (`work/20261101-211936`, Muse Spark Open on Baseten, 3 rounds, $3 cap):
- Muse kept reflux 1.5 and proposed raising the bottoms draw from 3.0 to 3.6 mol/s instead (rounds 1 and 2). The server re-solved it: it reaches only 113 %, because K 2750 is still at 110 % of flood at the target. It was not verified.
- The loop told Muse "no proposal made" instead of the flood number, because that proposal had no explicit rejection text. Fixed after the run (`loop._why`, test in `tests/test_loop.py`): an unverified proposal now goes back with the limits still over at the target.
- Round 3 ended with an **error**: Muse used its 26 tool steps on its own solves without returning an answer.
- Outcome: **no verified design**. Cost $2.38 (Baseten).

**Replacement loop** (`work/20261101-232245`, Muse Spark Open, $0.58): Muse used `replace_unit` for a 600 mm shell. DWSIM re-solved 120 % and the +10 % envelope; flooding, both purity checks, minimum reflux and 48/48 uncertainty re-solves pass. The terminal state means **simulation checks passed, approval open**: vendor confirmation of the new rating remains mandatory. A draft MOC pack with the replacement cloud, calculation and PSSR was regenerated after the decision-pack path was fixed.

- **Disciplines not calculated** (shown as open on the page): mechanical, heat transfer, electrical, combustion, piping, controls, safety and civil. This file carries no data for them.

## Cost

| Step | Baseten USD |
|---|---:|
| Build | 0.7674 |
| Ask | 0.2294 |
| Loop (3 rounds) | 0.5474 |
| **Total, first run** | **1.5442** |
| Second loop with the purity check | 2.3774 |
| Replacement loop | 0.5791 |

The Baseten ledger went from $18.147 to $19.692.

## Limits (read these before quoting the result)
- **The whole duty is a Muse assumption.** The drawing does not say what the column separates. The +13 % flood limit is a property of the assumed water/ethanol duty on the documented 500 mm shell, not of BASF's real service.
- **The purity spec is a draft.** No purity target is on the drawing; the check holds today's purity within 0.5 points until an engineer sets the real one. Against that draft, reflux 0.8 fails (see above).
- **Fixed after the run:** `economics.throughput.base` (24 t/d) was tagged *documented* but comes from Muse's assumed 1,000 kg/h; drafts now tag a built model's feed as assumed.
- **The replacement is simulator-screened, not mechanically approved.** `replace_unit` verifies the process consequences; the shell, internals, materials, nozzles and relief basis still require vendor and engineer confirmation.
- **Two diameter screens differ.** DWSIM's column object reports a 0.638 m estimated diameter at the envelope, while PlantAgent's Fair screen gives 60.4 % flood in a 0.600 m shell against the assumed 80 % limit (a 0.525 m shell is 78.9 %). Muse's stored phrase “Fair requires 0.638 m” conflates them; the decision is therefore a provisional 600 mm selection, not a vendor sizing claim.
- **One renderer fix was needed.** This exporter writes coordinates in metres. `tools/render_pid.py` now scales padding to the sheet and converts metre sheets to millimetres; before that, the drawing came out about 10 units wide.

## Files
- `runs/ws/basf_process_column_k_2750_dexpi_c02_uns/`: the build run, `answers.json` per session, `work/20261101-203737/worklog.json`, `drafts/`, `assumptions_log.jsonl`, `model.json`
- `cases/basf_process_column_k_2750_dexpi_c02_uns/`: `case.json` and `basis.md` (both generated by `new_project`), `pid.svg` (rendered) and the unmodified DEXPI file. The upload went to the data root; the file was copied next to the case so a fresh clone opens it, and `case.json` `pid` points there. That path edit is the only change made to a generated file.
- `tools/onboard_unseen.py`: the script that ran all of this
