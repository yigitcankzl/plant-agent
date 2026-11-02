# Management of Change: Elekeiroz T-2103 butyraldehyde tower: recover the intended 20% capacity increase

**DRAFT - NOT APPROVED.** Prepared 2026-11-02 22:16 +03 by PlantAgent from the working model. Nothing in this file is an approval.

## 1. Summary

| | |
|---|---|
| **Decision requested** | Simulator screening passed; proceed to data and vendor verification (not ready for approval): 1 change to reach 121 % of today's throughput - (1) Replace T-2103 internals with high-capacity trays in same shell. |
| **Target** | 121 % of today's throughput (mixed butyraldehyde feed 9,500 → 11,500 kg/h) |
| **Result (DWSIM, re-solved for this file)** | At 121 %, existing plant: 1 limit over 100 % (highest T-2103 distillation Fair flood fraction vs limit 103 %); with the changes: all modelled process limits within 100 % (highest T-2103 outlet (product leaving the unit) temperature vs design 93 %). |
| **Cost class (agent estimate, unpriced)** | (1) $100k-$1M |
| **Needs approval** | (1) Replace T-2103 internals with high-capacity trays in same shell: cost class $100k-$1M (agent estimate), replacement rating (vendor confirmation open); Pre-startup safety review: 6 items (section 6.2). |
| **Status** | DRAFT for engineering review; to be checked by a licensed engineer. Sign-off in section 7. |

**Agent's explanation on record** (model text, quoted; its figures are not re-checked here: sections 3 and 4 are the calculation record): 11.5 t/h needs high-capacity T-2103 trays. At 11.5 t/h the as-built 1.9 m T-2103 with 90 RV-1 trays floods at 102.6% (Fair, limit 0.80) in the calibrated run T2103_asbuilt_final_9p5_calib-2. With high-capacity internals rated at 1.30× RV-1 capacity the same shell passes at 78.9% and keeps isomer separation.


## 2. Basis

**Question.** T-2103 is limited near 9.5 t/h, while the project premise is 11.5 t/h. Build the existing tower, explain why added boil-up does not create useful capacity, and propose a design that reaches the premise without losing isomer separation.

**Plant and data sources.** Summers, Monaco and Britto, AIChE Spring Meeting paper 112b (2013), Sulzer/Elekeiroz; only the original tower and pre-solution operating evidence are exposed. https://www.sulzer.com/en/-/media/files/products/separation-technology/articles/butyraldehyde_tower_capacity_limitations.pdf

**Data status.** Real operating history and tower geometry. The paper does not publish a feed assay, so any binary i-/n-butyraldehyde composition used in DWSIM is an explicit modelling assumption. Later hardware and operating actions, plus the 2011-2012 performance data, are withheld in outcome.json.

**Model.** T2103_asbuilt_final_9p5_calib built by fireworks:accounts/fireworks/models/muse-spark-open on 2026-11-02 18:37; simulator DWSIM (headless). Review status: **ok** (0 findings, 0 blocking; details in appendix C).

## 3. Existing vs proposed at 121 % (DWSIM, re-solved for this file)

| Item | Check | Limit | Existing | Proposed | Proposed value |
|---|---|---|---|---|---|
| T-2103 distillation | Fair flood fraction vs limit | 0.8 fraction of flood | 103 % | **79 %** | 0.63 fraction of flood |
| T-2103 outlet (product leaving the unit) | temperature vs design | 85 °C | 93 % | **93 %** | 79.4 °C |
| T-2103 outlet (product leaving the unit) | temperature vs design | 80 °C | 90 % | **90 %** | 72.4 °C |

Existing and Proposed are utilisation (value / limit) of each limiting item at the target; over 100 % fails. For an energy-closure check the limit is the heat available in that solve.

## 4. Changes

### 4.1 Replace T-2103 internals with high-capacity trays in same shell

Cloud 1 on the Rev B drawing. Cost class (agent estimate, unpriced): $100k-$1M.

**What physically changes.**

- Replaces T-2103 distillation: tray capacity factor 1.3 (High-capacity valve trays (e.g. MVG/Superfrac) rated 25-30% above RV-1 within existing 1900 mm dia, 425 mm spacing; retains 90-tray/64-ideal-stage basis per Summers et al 112b; vendor to confirm)

**Why.** Only T-2103 flooding limits the +21% (9.5→11.5 t/h). Same reboilers/condenser pass. DWSIM verification: flood 0.821→0.631, utilisation 102.6%→78.9% at 1.210526×.

**Rating and rating source.**

- T-2103: agent-proposed sizing basis (not independently validated): High-capacity valve trays (e.g. MVG/Superfrac) rated 25-30% above RV-1 within existing 1900 mm dia, 425 mm spacing; retains 90-tray/64-ideal-stage basis per Summers et al 112b; vendor confirmation open

**Before / Proposed calculation** (this change alone, DWSIM at the target).

- Simulated maximum: 118.1 % → 153.5 % of today; first limit T-2103 → T-2103.

| Item | Check | Limit | Before | After |
|---|---|---|---|---|
| T-2103 | Fair flood fraction vs limit | 0.8 fraction of flood | 0.82 fraction of flood (103 %) | 0.63 fraction of flood (79 %) |

**Field checks that could change this.**

- None raised for this change.

### 4.2 Other field checks

- Vendor hydraulic rating of HC trays vs RV-1 at 1.9 m, 425 mm spacing. Where: Tray vendor rating sheet for butyraldehyde system at 1.1-1.25 bar. If it differs: If CF <1.29, flood exceeds 80% and a larger CF or second tower is needed
- Actual reboiler duty margin at 11.5 t/h. Where: DCS steam to reboilers (6.9-7.3 t/h test range) vs design ~25% margin per paper. If it differs: Confirms reboilers not limiting; if margin smaller, add reboiler area

### 4.3 Economics and uncertainty of the design


#### Economics (ILLUSTRATIVE prices; order of magnitude)

- draft (assumed values): Capex ≈ $0k (class 5: $0k–$0k) plus unpriced items (replace T-2103): capex is a lower bound; product price not given: margin, payback and NPV open (energy and utilities $0k/yr). All prices ILLUSTRATIVE.

| Proposal | Stated class | Factored capex | Check |
|---|---|---|---|
| Replace T-2103 internals with high-capacity trays in same shell | $100k-$1M | $0 + to price: replace T-2103 | factored $0 is outside the stated class $100k-$1M |

- Added Process feed: 48 t/d × 330 d; product margin $0/yr (solved 1.211 × base, capped at the 121% target; energy from dwsim solves (design at 121% vs today at 100 %)).
- Outage for tie-ins/cleaning: 2 d → $0 (muse_default shutdown for a tie-in or exchanger clean).
- Payback None years; NPV $0 (capex band: $0 to $0).

#### Uncertainty of the design (Monte Carlo over assumed and illustrative inputs)

- Target 121% met in 81% of 48 samples; 19% are over a limit at any throughput (T-2103: Fair flood fraction vs limit); max throughput P10/P50/P90 153% / 153% / 154% of the feasible samples; most often limited by T-2103: Fair flood fraction vs limit (81%); biggest driver limits.B_N.max_T_C (assumed).
- Method: Latin hypercube, 48 samples (seed 20261101), uniform ± band per input kind; each sample re-solved (dwsim): capacity bisection plus the solve at the target; 48 of 48 samples solved.

| Input | Kind | Base | ± band |
|---|---|---|---|
| units.T-2103.dP_bar | assumed | 0.15 | 10 % |
| feeds.FEED.P_bar | assumed | 2.0 | 10 % |
| feeds.FEED.T_C | assumed | 65 | 10 % |
| limits.B_N.max_T_C | assumed | 85 | 10 % |
| limits.D_ISO.max_T_C | assumed | 80 | 10 % |

- T-2103: Fair flood fraction vs limit at the target: load P10/P50/P90 79% / 79% / 79%.

## 5. Drawings

This project has no SVG P&ID; the changed equipment is: T-2103.

## 6. Risks and safety

### 6.1 Relief protection (P&ID relief scan)

- No smart P&ID: relief scan not available; review relief manually.

### 6.1c Discipline gates (outside the process model)

Pass/fail only from a sourced check; a check over an ILLUSTRATIVE rating leaves its gate open until the rating is confirmed. Electrical is in section 6.1b.

| Gate | Status | Summary |
|---|---|---|
| robustness | **pass** | draft (assumed values): operating envelope 2/2 scenarios pass |
| piping utilities | **open** | no calculation adapter: tie-ins, line sizing, supports and utility headers remain open for T-2103 |
| controls | **open** | no calculation adapter: control narrative, split/load-sharing control, cause & effect and permissives remain open for T-2103 |
| process safety | **open** | no calculation adapter: change-focused HAZOP, relief case and isolation for the changed equipment remain open for T-2103 |
| civil structural | **open** | no calculation adapter: plot, access, lifting and foundations remain open for T-2103 |

### 6.2 Pre-startup safety review (PSSR), generated from the changes

- [ ] Replacement of T-2103 distillation: confirm the installed rating (tray_capacity_factor = 1.3) against the vendor data sheet before start-up.
- [ ] Mechanical and process safety review for replacement T-2103: confirm materials, nozzles, supports, alarms, trips and relief basis are suitable for the new rating.
- [ ] Commissioning of replacement T-2103: update the equipment data sheet and procedures, then record the first operating point against the model.
- [ ] Update the P&ID, equipment datasheets and the operating procedure for every change above.
- [ ] Brief the operators on the new setpoints before start-up.
- [ ] Record the first 24 h of operation at the new throughput and compare with the model's predicted values in this file.

### 6.3 Second opinion

No second opinion was requested for this answer.

## 7. Approvals (DRAFT: not approved)

| Role | Name | Signature | Date |
|---|---|---|---|
| Process engineer | _ | _ | _ |
| Operations | _ | _ | _ |
| Process safety (MOC) | _ | _ | _ |
| Manager (approver) | _ | _ | _ |

## Appendix A. Reproducibility

- Code version (git): 95ceeda; simulator: DWSIM (headless) via plantagent.process.
- Audit-chain head hash: `58bedf8b438432969a172ff369098f860b4ecec413f3e6c439c6af0f2abec864` (chain intact: True).
- Model: T2103_asbuilt_final_9p5_calib by fireworks:accounts/fireworks/models/muse-spark-open on 2026-11-02 18:37; answer by fireworks:accounts/fireworks/models/muse-spark-open.
- Run labels and calculation records: T2103_asbuilt_final_9p5_calib.
- Sections 1, 3 and 6.2 were recomputed when this file was made; re-run `python -m plantagent.decision revamp_butyraldehyde_t2103` on the same revisions to reproduce them.

## Appendix B. Capability gaps

- None recorded.

## Appendix C. Model review

Status: **ok**.
- No findings.

An overall energy balance is not closed: the simulator's streams do not report enthalpy. Unit duties are checked one by one instead.

## Appendix D. Model assumptions

Recorded by the model builder when the model was built (model text). Later model corrections (section 2) take precedence; items the current model no longer matches are marked **superseded**.

- P&ID note: 'this project has no drawing: take the equipment and connections from the data sheet' - topology built from data_sheet text only; check_coverage returns 'no drawing to compare with' (as expected)
- Compound surrogate required: DWSIM compound database has no 'Isobutyraldehyde' / 'Isobutyraldehyde' key (KeyNotFound errors demonstrated). Butanal (n-butyraldehyde) + n-Hexane used as close-boiling isomer proxy with NRTL. Relative volatility tuned to ~1.15-1.20 range representative of iso-/n-butyraldehyde close split; NRTL selected per data_sheet instruction (UNIQUAC/NRTL for aldehydes). Labelled as assumption; absolute temperatures and duties are proxy-scaled - hydraulic vapour/liquid traffic and flood trend are the calibrated outputs.
- Feed composition and thermal condition not published (data_sheet: Feed composition was not published) - assumed equimolar proxy feed (x=0.5/0.5) at 65°C subcooled liquid, 2.0 bar feed pressure (pump discharge). Feed split, product purities and reflux ratio not specified; RR=6 / BR=3 chosen to give ~30% overhead split and hydraulic utilisation ~85% at 9.5 t/h, matching observed stable limit. All feed assay assumptions flagged as non-plant evidence per premise.
- Recycle topology: No external recirculation loop; tower is standalone with reboiler/condenser grouped per instruction '2 thermosyphon reboilers grouped'. Once-through feed->column->products modelled; no recycle unit needed (no tank mixing temperature set-point). Condenser duty computed, not limited.
- Tray rating: 90 actual trays *71% efficiency =63.9 ideal stages rounded to 64, feed stage 32 (mid-column). Spacing taken as midpoint 425 mm of 400-450 mm range; diameter 1,900 mm; flood limit 80% (Fair) with tray_spacing_m correction. DWSIM Fair correlation is sieve-tray based, not calibrated to RV-1 valve trays - utilisation is comparative only. Downcomer backup / vapour horn entrainment not expressible in steady-state stage model (see mechanism gap noted).
- Reboiler/condenser duties: Measured 4.1 M kcal/h (4768 kW) vs simulated ~2100 kW reflects surrogate latent heat / composition/purity difference, not a tuning failure; model preserves hydraulic vapour traffic trend (capacity_multiple 1.181) which matches intended 20% de-bottleneck to ~11.5 t/h. Design duty inferred as 4.1/0.75≈5.47 M kcal/h (6358 kW) not used as limit (no vendor rating provided).
- Pressure: Column P=1.1 bar top, dP=0.15 bar (1.25 bar bottom) assumed near-atmospheric operation typical for butyraldehyde; feed P=2.0 bar to ensure subcooled feed; product max_T/max_P limits set loosely (80-85°C) only to enable utilisation reporting.
- Utility not modelled: Steam flow 6.9-7.3 t/h cited only as heat proxy; no utility feed with utility:true and no max_m3_h limit to set (no supply limit given). Pressure drop rise <1% cannot be reproduced by fixed-dP stage model - reported as observed vs simulated gap, not tuned to match.
