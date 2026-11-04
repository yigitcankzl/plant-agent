# Benchmarks

Every quantitative evaluation in this repo, with the command that re-scores it. No scorer calls a model; the stored runs are scored as they are.

| Benchmark | What it measures | Result | Re-score |
|---|---|---|---|
| [Published revamp, blind](../evidence/revamp-benchmark/README.md) | Does the loop reproduce the change real engineers built, from the pre-revamp data only? | 6 cases re-run blind: 5 done, 0 full match, 2 partial. Passing the checks is not reproducing the engineers' choice; on this PlantAgent is weak. | `python tools/revamp_compare.py` |
| [Real plant: Shell Norco](../evidence/real-plant-norco/README.md) | Muse's revamp vs Shell's measured after-data | same revamp type; 5 match, 3 partial, 1 miss, 1 not predicted | see the README |
| [Engineers' conclusions](../evidence/results.json) | Agent findings vs documented engineers' conclusions | 13 graded studies, mean 64 %, blind, model-graded | `python -m plantagent.grade` |
| [Red team](../runs/ws/basf_process_column_k_2750_dexpi_c02_uns/redteam_trays.json) | Bounded operating deviations against the live-run design, each re-solved in DWSIM | 7 / 7 held, worst 96 % of flood | stored; `plantagent/redteam.py` |
| [Schematic read](../evidence/datasheet-read/README.md) | A drawing read vs an engineer-confirmed read | per-case in the README | `python tools/pid_read_eval.py` |
| Loop outcomes | Every recorded loop run: done, stopped, cost | 22 of 70 ended with every check passing, $193.50 total | `python tools/loop_stats.py` |
