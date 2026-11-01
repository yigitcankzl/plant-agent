# Muse Spark Open engineering runs

## Method

Muse Spark Open ran through Baseten against the same saved PlantAgent cases used by the closed-model engineering loop. Muse proposed actions; PlantAgent's deterministic engines decided pass/fail. The two incident studies are explicitly **post-hoc engineering runs**: their blind answers were not changed. Repeated runs used a fresh prompt; cached calls are identified rather than counted as independent paid evidence.

## Results

| Case | Model and run | Outcome | Deterministic evidence | Cost |
|---|---|---|---|---:|
| Salt MVR | Muse Wonder, `20261101-151639` | Unsolved after 2 rounds | Process, robustness and uncertainty passed; electrical, compressor curve and start-up checks failed. It stopped for vendor surge data. | $5.5610 |
| Salt MVR | Muse Spark Open, `20261101-154622` | Error after round 1 | It proposed a plausible parallel K-202 and cleaning, but the 26-step agent limit expired. The checks exposed heater robustness, a 27% DOL voltage dip, start-up recycle and low-flow surge failures. | $2.4914 |
| Salt MVR | Muse Spark Open, `20261101-155907` | Budget stop after 3 rounds | By round 3, process reached 120%, the 4/4 envelope passed and the VFD reduced starting dip to 0.5%. Cable ampacity, today's K-202 surge and start-up recycle still failed. No completed design is claimed. | $4.9326 |
| UCTE 2006 | Meta endpoint | No valid run | Four attempts were rejected by the endpoint's content policy before an engineering result. This is not a model-quality comparison. | $0.6178 |
| UCTE 2006 | Muse Spark Open, `20261101-163840` | Done, cache replay | DOL redispatch to 1,200 MW plus opening the BIO-SPX 220 kV tie passed the line limits and N-1 with 0 violations. | $0.0000 |
| UCTE 2006 | Muse Spark Open, `20261101-164315` | Done, independent repeat | A more conservative DOL/GRO redispatch plus the same tie opening also passed line limits and N-1 with 0 violations. | $1.7297 |
| Freeport LNG | Muse Wonder, `20261101-150535` | Done | Restore relief; limits and documented worst case passed, while relief capacity remained open. | $0.6760 |
| Freeport LNG | Muse Spark Open, `20261101-164131` | Done | Restore PSV-101 and forbid double block. Base pressure was 47.8 psig; the worst-case calculation reached the ideal 230 psig relief boundary. | $0.1517 |
| Freeport LNG | Muse Spark Open, `20261101-164847` | Done, independent repeat | Restore PSV-101 or avoid LNG block-in. Limits and worst case passed; relief capacity remained open. | $0.1484 |

The UCTE runs converged on the same physical strategy, and both Freeport runs converged on keeping relief available. The salt runs did something useful but did not finish: the multi-discipline loop found problems that a process-only answer would miss, then exhausted its step/budget limits while trying to repair them.

## Spend

This experiment added 208 ledger entries and **$12.26068** of Baseten spend: salt $7.93888, UCTE $4.02169 and Freeport $0.30011. The UCTE total includes one failed post-processing run and one operator-interrupted run; the $0 cache replay is not presented as a free independent model call. Total Baseten ledger spend after the experiment was $18.14749, below the separate $90 provider cap.

## Limits

- This is engineering-loop evidence, not a controlled model benchmark. Prompt wording and cache state were not held as experimental variables.
- A single successful round was sufficient for UCTE and Freeport. Salt exercised feedback across rounds, but did not converge, so there is no successful open-vs-closed salt design comparison.
- UCTE switching and redispatch are screening results from the saved pandapower model, not an operating instruction.
- Freeport uses an **ideal relief boundary — relieving capacity not checked**. PSV sizing, backpressure and discharge-system capacity remain human/vendor work.
- Salt equipment curves and ratings are illustrative until vendor data confirms them.

Machine-readable run selection and spend are in [results.json](results.json).
