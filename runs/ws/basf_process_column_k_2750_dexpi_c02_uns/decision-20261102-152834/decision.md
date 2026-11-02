# Management of Change: BASF process column K 2750 (DEXPI C02, unseen)

**DRAFT - NOT APPROVED.** Prepared 2026-11-02 15:28 +03 by PlantAgent from the working model. Nothing in this file is an approval.

## 1. Summary

| | |
|---|---|
| **Decision requested** | Simulator screening passed; proceed to data and vendor verification (not ready for approval): 1 change to reach 120 % of today's throughput - (1) Replace column with 600 mm ID rated shell (vendor to confirm). |
| **Target** | 120 % of today's throughput |
| **Result (DWSIM, re-solved for this file)** | At 120 %, existing plant: 1 limit over 100 % (highest K 2750 distillation Fair flood fraction vs limit 110 %); with the changes: all modelled process limits within 100 % (highest K 2750 distillation Fair flood fraction vs limit 76 %). Simulated maximum throughput: 113.1 % → 145.1 % of today. |
| **Cost class (agent estimate, unpriced)** | (1) not stated |
| **Needs approval** | (1) Replace column with 600 mm ID rated shell (vendor to confirm): cost class not stated (agent estimate), replacement rating (vendor confirmation open); Pre-startup safety review: 6 items (section 6.2). |
| **Status** | DRAFT for engineering review; to be checked by a licensed engineer. Sign-off in section 7. |

**Agent's explanation on record** (model text, quoted; its figures are not re-checked here: sections 3 and 4 are the calculation record): Flood limits first - 600 mm shell needed for envelope. K 2750 (ProcessColumn-1: 500 mm ID, 14 000 mm, 6 bar / 150 °C) is tight at +20 % feed and fails the +10 % operating envelope. With bottoms held at 3.0 mol/s flood is 0.79 vs 0.80 = 98.8 % at 1.2× and 1.008 vs 0.80 = 126 % at 1.32× (K2750_1p2_scaled_500, K2750_1p32_fixed_500) and base split is lost. Ratio-controlled bottoms 3.0→3.6 mol/s at 1.2× (3.96 at 1.32×) holds purity and 600 mm ID gives 0.604 vs 0.80 = 75.5 % at 1.32× (K2750_1p32_600_verify) with +20 % duty (+32 % at envelope) and all documented P/T checks < 61 %.


## 2. Basis

**Question.** +20 % feed: what limits it first and what does it cost?

**Plant and data sources.** Uploaded by the engineer.

**Data status.** The drawing (official DEXPI example C02, unmodified) shows the column but not its service: Muse assumed the duty (water/ethanol, 1,000 kg/h, 85 °C, 3 bar). Results hold for that assumed duty, not BASF's real one. The purity spec is a draft (today's purity within 0.5 points) until an engineer sets one.

**Model.** K2750_submitted built by baseten:meta-models/muse-spark-open-1026 on 2026-11-01 20:35; simulator DWSIM (headless). Review status: **ok** (0 findings, 0 blocking; details in appendix C).

## 3. Existing vs proposed at 120 % (DWSIM, re-solved for this file)

| Item | Check | Limit | Existing | Proposed | Proposed value |
|---|---|---|---|---|---|
| K 2750 distillation | Fair flood fraction vs limit | 0.8 fraction of flood | 110 % | **76 %** | 0.61 fraction of flood |

Existing and Proposed are utilisation (value / limit) of each limiting item at the target; over 100 % fails. For an energy-closure check the limit is the heat available in that solve.

## 4. Changes

### 4.1 Replace column with 600 mm ID rated shell (vendor to confirm)

Cloud 1 on the Rev B drawing. Cost class (agent estimate, unpriced): not stated.

**What physically changes.**

- Replaces K 2750 distillation: diameter m 0.6 (DWSIM Fair flood requires 0.638 m at 1.32× scaled 3.96 mol/s; 600 mm uniform (next standard matching KX 2750 600 mm section) gives 0.604 vs 0.80 =75.5 % at envelope (K2750_1p32_600_verify) and 0.549 =68.6 % at 1.2× (K2750_1p2_600 family); 525 mm gives 0.789 =98.6 % no margin (K2750_1p32_525). Height 14000 mm, 6 bar/150 °C, 1.4571, 15 stages same.; vendor to confirm)
- On the drawing: K 2750 REPLACED: diameter m 0.6 (vendor to confirm).

**Why.** Existing 500 mm ID cannot pass the +10 % operating envelope even with correct split: 0.869 vs 0.80 =108.6 % at 1.32× scaled (K2750_1p32_scaled_500) and 1.008 =126 % fixed (K2750_1p32_fixed_500). All documented P/T checks pass (<61 % at 1.32×) so flooding and purity are the only documented limits. New 600 mm ID provides required capacity with margin; vendor to confirm tray/valve design, downcomers, nozzles for line 2750.001.6 and *at N3*/*C2* valve.

**Rating and rating source.**

- K 2750: agent-proposed sizing basis (not independently validated): DWSIM Fair flood requires 0.638 m at 1.32× scaled 3.96 mol/s; 600 mm uniform (next standard matching KX 2750 600 mm section) gives 0.604 vs 0.80 =75.5 % at envelope (K2750_1p32_600_verify) and 0.549 =68.6 % at 1.2× (K2750_1p2_600 family); 525 mm gives 0.789 =98.6 % no margin (K2750_1p32_525). Height 14000 mm, 6 bar/150 °C, 1.4571, 15 stages same.; vendor confirmation open

**Before / Proposed calculation** (this change alone, DWSIM at the target).

- Simulated maximum: 113.1 % → 145.1 % of today; first limit K 2750 → K 2750.

| Item | Check | Limit | Before | After |
|---|---|---|---|---|
| K 2750 | Fair flood fraction vs limit | 0.8 fraction of flood | 0.88 fraction of flood (110 %) | 0.61 fraction of flood (76 %) |

**Field checks that could change this.**

- Actual product purity spec for 2750.001.6 and *at N3* vent/distillate. Where: BASF process datasheet/DCS lab specs for K 2750 - confirm bottoms and distillate targets that define if fixed 3.0 mol/s is off-spec. If it differs: If spec is tighter than base split, required reflux or stages may increase and flood/duty numbers change; if looser, fixed bottoms could be tolerated at 1.2× but still fails flood at 1.32×

### 4.2 Other field checks

- Feed rate/composition envelope and actual reboiler/condenser capacity. Where: DCS historian for FEED flow, temperature and lab composition; nameplates for reboiler steam valve and condenser - measure max duties available. If it differs: If available duty <563 kW the 1.32× envelope cannot be met even with new shell - would need utility upgrade
- Tray type, spacing and fouling/pressure-drop. Where: Column internals drawing and manway inspection - confirm sieve/valve trays and actual 0.5 m spacing assumed. If it differs: Different spacing or high-pressure-drop internals shifts flood correlation and the 0.638 m required diameter

### 4.3 Economics and uncertainty of the design


#### Economics (ILLUSTRATIVE prices; order of magnitude)

- draft (assumed values): Capex ≈ $0k (class 5: $0k–$0k) plus unpriced items (replace K 2750): capex is a lower bound; product price not given: margin, payback and NPV open (energy and utilities $0k/yr). All prices ILLUSTRATIVE.

| Proposal | Stated class | Factored capex | Check |
|---|---|---|---|
| Replace column with 600 mm ID rated shell (vendor to confirm) |  | $0 + to price: replace K 2750 |  |

- Added Process feed: 5 t/d × 330 d; product margin $0/yr (solved 1.451 × base, capped at the 120% target; energy from DWSIM solves (design at 120% vs today at 100 %)).
- Outage for tie-ins/cleaning: 2 d → $0 (muse_default shutdown for a tie-in or exchanger clean).
- Payback None years; NPV $0 (capex band: $0 to $0).

## 5. Drawings

The next pages show the P&ID **Rev A** (existing, as received) and **Rev B** (proposed): each change is drawn in, clouded and numbered as in section 4, with the new design values written next to the equipment or line and a revision block (DRAFT - NOT APPROVED). Files in the pack: `rev_a.svg`, `rev_b.svg`, `rev_b.png`.

## 6. Risks and safety

### 6.1 Relief protection (P&ID relief scan)

- **Finding:** K 2750 all side: no relief on this P&ID. no relief device reachable (lines leave the drawing: check the connecting P&ID).

### 6.1c Discipline gates (outside the process model)

Pass/fail only from a sourced check; a check over an ILLUSTRATIVE rating leaves its gate open until the rating is confirmed. Electrical is in section 6.1b.

| Gate | Status | Summary |
|---|---|---|
| robustness | **pass** | draft (assumed values): operating envelope 2/2 scenarios pass |
| piping utilities | **open** | no calculation adapter: tie-ins, line sizing, supports and utility headers remain open for K 2750 |
| controls | **open** | no calculation adapter: control narrative, split/load-sharing control, cause & effect and permissives remain open for K 2750 |
| process safety | **open** | no calculation adapter: change-focused HAZOP, relief case and isolation for the changed equipment remain open for K 2750 |
| civil structural | **open** | no calculation adapter: plot, access, lifting and foundations remain open for K 2750 |

### 6.2 Pre-startup safety review (PSSR), generated from the changes

- [ ] Replacement of K 2750 distillation: confirm the installed rating (diameter_m = 0.6) against the vendor data sheet before start-up.
- [ ] Mechanical and process safety review for replacement K 2750: confirm materials, nozzles, supports, alarms, trips and relief basis are suitable for the new rating.
- [ ] Commissioning of replacement K 2750: update the equipment data sheet and procedures, then record the first operating point against the model.
- [ ] Update the P&ID, equipment datasheets and the operating procedure for every change above.
- [ ] Brief the operators on the new setpoints before start-up.
- [ ] Record the first 24 h of operation at the new throughput and compare with the model's predicted values in this file.

### 6.3 Second opinion

No second opinion was requested for this answer.

### 6.4 Open risks

- 1 relief finding on changed equipment (section 6.1).

## 7. Approvals (DRAFT: not approved)

| Role | Name | Signature | Date |
|---|---|---|---|
| Process engineer | _ | _ | _ |
| Operations | _ | _ | _ |
| Process safety (MOC) | _ | _ | _ |
| Manager (approver) | _ | _ | _ |

## Appendix A. Reproducibility

- Code version (git): 4299e5d; simulator: DWSIM (headless) via plantagent.process.
- Audit-chain head hash: `a8bcd9bcd14f1fd0eab97d0d269de52ea4f08fea990ad6d441e1aee46714e0bb` (chain intact: True).
- Model: K2750_submitted by baseten:meta-models/muse-spark-open-1026 on 2026-11-01 20:35; answer by baseten:meta-models/muse-spark-open-1026.
- Run labels and calculation records: K2750_submitted.
- Sections 1, 3 and 6.2 were recomputed when this file was made; re-run `python -m plantagent.decision basf_process_column_k_2750_dexpi_c02_uns` on the same revisions to reproduce them.

## Appendix B. Capability gaps

- None recorded.

## Appendix C. Model review

Status: **ok**.
- No findings.

An overall energy balance is not closed: the simulator's streams do not report enthalpy. Unit duties are checked one by one instead.

## Appendix D. Model assumptions

Recorded by the model builder when the model was built (model text). Later model corrections (section 2) take precedence; items the current model no longer matches are marked **superseded**.

- Fluid composition assumption: Line 2750.001.6 fluid code 8503 and piping class 10HB25T10B1 not defined in project documents (search_documents for K2750/C02/8503/10HB25T10B1/BASF/DEXPI returned no pages). Data sheet states no process conditions on drawing. Model uses Water+Ethanol with NRTL as generic organic-water proxy to demonstrate column hydraulics; all temperatures/duties/compositions illustrative and must be replaced with actual fluid 8503 assay.
- Operating condition assumption: No feed temperature, pressure, flow or product specs on P&ID or data sheet. Assumed feed 1000 kg/h, 85 C, 3 barg, x Water 0.3 / Ethanol 0.7; reflux ratio 1.5, reboiler product 3.0 mol/s; condenser total. No measured values to calibrate against - calibration section reports design-limit utilisation only.
- Column staging assumption: Height 14000 mm with tray spacing 0.5 m allows ~28 theoretical trays max. Model uses 15 stages feed stage 8 efficiency 0.7 for numerical stability and to fit within shell; actual internals (trays vs packing, stage count) not on DEXPI export.
- Diameter conflict/assumption: K 2750 Chamber 1 InsideDiameter 500 mm vs KX 2750 ColumnSection InsideDiameter 600 mm - both Material 1.4571. Interpreted as single column with two diameters (enlarged section). Model uses conservative 0.5 m for flood screening; DWSIM estimates 0.555 m required at assumed rate, indicating tight fit - to be checked once actual vapour loads known. Listed as assumption per instruction to note site/P&ID conflicts.
- Exclusions justified: Valves *at P3*/OperatedValve and *at P4*/OperatedValve and lines *at P3*/*at P4* are instrument root valves to BlindFlange -> PI(Z) 275003A/B -> PIS+Z+A 275003 pressure measurement loops, not process flow lines; no connection to off-page flow. Closed per check_coverage guidance and not modelled as process valves. No data_quality warnings present on latest P&ID export.
- Topology assumption: Recirculation/utility loops: none on this DEXPI C02 extract. Both documented connections carry normal flow and are modelled: model stream VENT_INT via *at N3*/*C2* to open-out (*at N3*) and bottoms to 2750.001.6 off-page connector via PipeReducer. No recycle unit needed (no temperature-by-mixing loop; no closed coolant loop at known supply temperature).
- Limits assumption: All limits taken from P&ID design_limits (max_P 6 barg, max_T 150 C for K2750 and derived for streams 2750.001.6/*at N3*/model stream VENT_INT/FEED). No pump, exchanger area, tank residence, relief or utility supply ratings appear on this column-only P&ID extract; none added. Later alternatives must not raise these 6 barg/150 C ratings per instruction.
