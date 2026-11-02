# Red-team design replay

PlantAgent uses a second Muse model as an adversarial operator, not as the judge. Muse Spark 1.3 proposes credible operating deviations; each accepted deviation is bounded, applied to the verified design, and re-solved by DWSIM with the same limit checks used by the operating envelope. The UI replays the stored evidence without an API call.

## BASF C02 column result

| Design and challenge | Stored result | Worst stored check | Source |
|---|---:|---:|---|
| 600 mm shell, normal envelope band (0.8–1.1× target) | 8/8 held | 89.7% of flood limit | `runs/ws/basf_process_column_k_2750_dexpi_c02_uns/redteam_600mm.json` |
| 600 mm shell, 1.25× target challenge | 8/8 broke | 118% of flood limit among the three detailed attacks | work `20261102-194930` |
| 700 mm shell, normal envelope band | 8/8 held | 83.1% of the limiting check | `runs/ws/basf_process_column_k_2750_dexpi_c02_uns/redteam_700mm.json` |

The successful engineering loop is work `20261102-203128`: it replaces the shell with 700 mm, records all eight bounded attacks as passing, and ends `done` at $1.5934 total loop cost. The earlier work `20261102-194930` also stored a separate worst-case DWSIM sizing check at 1.25× target that reached 86.4% of the flood limit. That sizing point is shown separately in the UI; it is not presented as one of the eight stored envelope attacks.

The first 600 mm attack call cost $0.1275. The later 700 mm attack call cost $0.042. No new paid call was made to create this replay.

## Attacker prompt

The prompt supplies the verified design changes, limits, and an allowlist of operating inputs. It asks Muse Spark 1.3 for at most eight physically credible HAZOP-style deviations:

> Find credible operating deviations under which the verified design is most likely to break a limit: more/less flow, temperature, pressure, composition other than, fouling, degraded efficiency, seasonal utilities, or upstream feed swings. Throughput must remain within the stated band. Change only allowlisted operating inputs, each within ±30% of its design value. Do not change limits, equipment, or connections. Return scenario name, guideword, rationale, scale, and input changes as JSON.

The complete executable template is `plantagent/redteam.py::PROMPT`. Validation rejects unknown paths, equipment/rating edits, duplicate scenarios, non-finite values, deviations outside ±30%, and scales outside 0.8–1.1× target before DWSIM sees them.

## Evidence limits

- The normal red-team run is bounded to the same 0.8–1.1×-target envelope band. It is not an exhaustive HAZOP, relief study, dynamic simulation, or proof of safe operation.
- Work `20261102-194930` retained exact names, inputs, and utilisation for only three of its eight attacks. The UI labels the other five as “detail not stored”; it does not reconstruct or invent them.
- The 700 mm file contains the eight bounded-envelope scenarios. The 86.4% figure comes from the separate 1.25×-target sizing check in work `20261102-194930`.
- Column flooding is simulator screening with the project’s Fair/Souders–Brown check. Vendor hydraulic rating, tray/downcomer design, mechanical design, controls, relief capacity, and an engineer-led HAZOP remain required.
