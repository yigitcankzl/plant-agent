# Decision file: Dairy plant ammonia refrigeration (new ice cream line, floating head pressure)

**Status: DRAFT for engineering review, not approved.** Prepared 2026-10-29 11:15 +03 by PlantAgent from the working model.

**Question:** Can the ammonia plant take a new ice cream line (+700 kW refrigeration, 2,400 to 3,100 kW) with N+1 on compressors, what limits first, and how much electricity a year would floating head pressure save?

**Answer on record:** Plant handles new load; floating saves yearly. With one compressor out at 3100 kW fixed head, DWSIM run n1_fixed_verify gives 352.9 kW per compressor and 1902.9 kW per condenser, all within data-sheet limits. Annual_energy over the five data-sheet wet-bulb bins gives 6182 MWh fixed versus 4466 MWh floating, saving 1716 MWh ($121,332 at $0.0707/kWh).

**Result at 129 % of today's throughput (re-solved in DWSIM for this file):** all stated limits within 100 %.

## 1. What changes and why

| Rev | Change | Reason | Proposed by | Applied |
|---|---|---|---|---|
| - | No change to the plant: the answer on record needs none | | | |

## 2. Limits before and after, at 129 % (DWSIM, re-solved now)

| Equipment or stream | Check | Before | After | Value after | Limit |
|---|---|---|---|---|---|
| COND-101A cooler | outlet temperature vs heat-sink minimum (ambient + approach) | 99 % | 99 % | 30.0 C | 28.0 C |
| COND-101B cooler | outlet temperature vs heat-sink minimum (ambient + approach) | 99 % | 99 % | 30.0 C | 28.0 C |
| COND-101A cooler | duty vs design | 99 % | 99 % | 1983.94 kW | 2000 kW |
| COND-101B cooler | duty vs design | 99 % | 99 % | 1983.94 kW | 2000 kW |
| COND-101A outlet to EV-101 | temperature vs design | 97 % | 97 % | 30.0 C | 31 C |

## 3. Drawing

This project has no smart P&ID; the changed equipment is: .

## 4. Relief protection (P&ID relief scan)

- No smart P&ID: relief scan not available; review relief manually.

- The changes are operating changes; the relief scan reads the drawing, so its findings above are unchanged by them and still need closing.

## 5. Field checks and assumptions

- No field checks were raised in the answer.
- Assumption (model): No P&ID drawing in project (read_pid: take equipment/connections from data sheet) - equipment list and topology taken from operating data sheet only.
- Assumption (model): Property package Peng-Robinson (PR) for R-717 ammonia cycle.
- Assumption (model): Suction pressure 3.16 bar(a) - saturation pressure of ammonia at -8 C from simulator (data sheet gives -8 C saturated vapour, no pressure).
- Assumption (model): Circulation 7600 kg/h is tuned (not metered) so EV-101 2400 kW duty just evaporates to saturated vapour at suction: SUCTION vf 0.9997.
- Assumption (model): Condenser outlet 30.0 C at 12.0 bar(a) used to represent data-sheet 'saturated, about 1 K subcooled' (sat ~31 C at 12 bar(a)).
- Assumption (model): 3x compressors modelled as C-101A/B/C in parallel via SPL-SUC/MIX-DIS with equal split; 2x condensers as COND-101A/B in parallel via SPL-DIS/MIX-LIQ; SPL/MIX are flow helpers, not P&ID equipment.
- Assumption (model): XV-101 expansion valve modelled as P_out 3.16 bar(a) isenthalpic flash (no tag in data sheet - required to close loop suction to -7.88 C).
- Assumption (model): Compressor eff_pct 75% and motor max_kW 450 each, condenser max_kW 2000 each taken directly from data-sheet rows into limits.
- Assumption (model): Floating-head cases (wet-bulb+8K, floor 8.6 bar(a)/~19-20 C) evaluated in separate runs e.g. float_86_again, not in calibrated fixed-head model.
- Assumption (model): Model correction: condenser outlet at least 28 C at design conditions (design wet bulb 21 C + 8 K approach = 29 C condensing, 1 K subcooled), from the data sheet; floating head is evaluated with annual_energy over the bins

## 6. Second opinion (Muse Spark Open, answered independently)

Status: **partly**.
- Differs: units.C-101A.P_out_bar: only the open model changes it
- Differs: units.C-101B.P_out_bar: only the open model changes it
- Differs: units.C-101C.P_out_bar: only the open model changes it
- Differs: units.COND-101A.T_out_C: only the open model changes it
- Differs: units.COND-101B.T_out_C: only the open model changes it
- Differs: annual energy saving: 1,716 vs 1,330 MWh
- Agrees: limiting equipment: COND-101A, COND-101B vs COND-101A, COND-101B

## 7. Pre-startup safety review (PSSR) checklist (generated from the changes)

- [ ] No plant change: confirm the operating limits in this file before running at the higher load, and record the first 24 h against the model.

## 8. Sign-off (DRAFT: not approved)

| Role | Name | Signature | Date |
|---|---|---|---|
| Process engineer |  |  |  |
| Operations |  |  |  |
| Process safety (MOC) |  |  |  |
| Approver |  |  |  |

## 9. Reproducibility

- Model: calibrated_fixed_head_v2 built by muse-spark-1.3-contributor on 2026-10-28 18:43; P&ID coverage missing connections: 0
- Audit-chain head hash: `1655c5620726eaa6c8006245687223a20822523e8f6ca7e32e5b4c2dd8b30b49` (chain intact: True)
- Code version: 648a410; simulator: DWSIM (headless) via plantagent.process
- Values in sections 2 and 7 were recomputed when this file was made; re-run `python -m plantagent.decision dairy_refrig` on the same revisions to reproduce them.
