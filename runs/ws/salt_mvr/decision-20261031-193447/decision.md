# Management of Change: Vacuum-salt plant with vapour recompression evaporator (US 5,366,514 flowsheet)

**DRAFT - NOT APPROVED.** Prepared 2026-10-31 19:34 +03 by PlantAgent from the working model. Nothing in this file is an approval.

## 1. Summary

| | |
|---|---|
| **Decision requested** | Do not approve yet: 3 changes to reach 120 % of today's throughput - (1) Clean the main circulating heater back to its clean performance; (2) Add a small parallel vapour compressor K-202; (3) Hold purge-heater steam at today's rate by trimming the overhead split. The process changes pass in DWSIM; the electrical screen fails 8 checks (section 6.1b): resolve the supply first. Failed discipline gate(s): robustness, electrical (section 6.1c). |
| **Target** | 120 % of today's throughput (Salt production 2,511 → 3,013 short t/d) |
| **Result (DWSIM, re-solved for this file)** | At 120 %, existing plant: 3 limits over 100 % (highest K-201 compressor suction flow vs capacity 120 %); with the changes: all modelled process limits within 100 % (highest K-201 compressor suction flow vs capacity 100 %). Discipline screens outside the process model: 5 checks over their limit (section 6.1c). Simulated maximum throughput: 100.1 % → 120.1 % of today. |
| **Cost class (agent estimate, unpriced)** | (1) <$100k; (2) >$1M; (3) no capex |
| **Needs approval** | (1) Clean the main circulating heater back to its clean performance: cost class <$100k (agent estimate); (2) Add a small parallel vapour compressor K-202: cost class >$1M (agent estimate), purchase of new equipment (vendor quote to confirm), piping tie-ins (outage); (3) Hold purge-heater steam at today's rate by trimming the overhead split: cost class no capex (agent estimate); Pre-startup safety review: 17 items (section 6.2). |
| **Status** | DRAFT for engineering review; to be checked by a licensed engineer. Sign-off in section 7. |

**Agent's explanation on record** (model text, quoted; its figures are not re-checked here: sections 3 and 4 are the calculation record): Yes, with cleaning and extra compression. At 120% the vapour compressor needs 120%, the main heater 111.3% and the purge heater 106.1% of installed area. Cleaning the main heater, adding a 49.5 t/h parallel compressor and holding purge-heater steam at today's rate clears all modelled checks at 120%, with the main heater at 89.0%, purge heater at 88.4% and the existing compressor at 100%.


## 2. Basis

**Question.** Can the plant make 3,000 short tons of salt per day instead of 2,500 (+20%)? What limits it first, and what is the most economical way to get there?

**Plant and data sources.** US Patent 5,366,514 (Texas Brine Corp., 1994), FIG. I and Table I; P&ID drawn by PlantAgent on that flowsheet; illustrative ratings where the patent gives none. https://patents.google.com/patent/US5366514A

**Data status.** Design data from US Patent 5,366,514 (Texas Brine, 1994). The P&ID is drawn by PlantAgent on the patent's flowsheet; ratings marked illustrative are not from the patent.

Values marked **ILLUSTRATIVE** in the data sheet (confirm before approval):

- E-201 circulating heater: 8,800 m², U 2,000 W/m²K in service (ILLUSTRATIVE; 2,500 W/m²K clean).
- P-201 forced-circulation pump: 15,000 m³/h rated (ILLUSTRATIVE).
- E-301 purge-evaporator heater: 1,500 m², U 1,500 W/m²K (ILLUSTRATIVE).

**Model.** vrc_cal_v2_desup_hx built by muse-wonder-1.0 on 2026-10-29 22:17; simulator DWSIM (headless). Review status: **ok** (0 findings, 0 blocking; details in appendix C).

Model corrections applied before this study (not plant changes):

- Heating steam taken from the compressor discharge (model review)
- Purge evaporator: liquid feed, boil-off set by its heating steam (model review)
- Model review: circulation internal to the evaporator, crystallisation and elutriation heat, purge-evaporator balance

## 3. Existing vs proposed at 120 % (DWSIM, re-solved for this file)

| Item | Check | Limit | Existing | Proposed | Proposed value |
|---|---|---|---|---|---|
| K-201 compressor | suction flow vs capacity | 226.8 t/h | 120 % | **100 %** | 226.8 t/h |
| E-201 (V-201) | heater area needed (BPE included) vs installed | 8,800 m² | 111 % | **89 %** | 7,836 m² |
| E-301 (V-301) | heater area needed (BPE included) vs installed | 1,500 m² | 106 % | **88 %** | 1,326 m² |
| V-201 evaporator | boil-up duty vs heat from the heating steam (2 % closure tolerance) | available 191.1 MW | 99 % | **98 %** | 187.4 MW |
| V-301 evaporator | boil-up duty vs heat from the heating steam (2 % closure tolerance) | available 13.1 MW | 98 % | **98 %** | 12.9 MW |
| K-202 compressor | suction flow vs capacity | 55 t/h | - | **90 %** | 49.5 t/h |
| K-202 compressor | shaft power vs motor | 2.4 MW | - | **86 %** | 2.05 MW |
| K-201 compressor | shaft power vs motor | 14 MW | 81 % | **67 %** | 9.4 MW |

Existing and Proposed are utilisation (value / limit) of each limiting item at the target; over 100 % fails. For an energy-closure check the limit is the heat available in that solve.

## 4. Changes

### 4.1 Clean the main circulating heater back to its clean performance

Cloud 1 on the Rev B drawing. Cost class (agent estimate, unpriced): <$100k.

**What physically changes.**

- Clean E-201 circulating heater tubes (chemical/mechanical clean during a planned outage) to restore clean heat transfer; E-201 is modelled as the heating side of evaporator unit V-201 in vrc_cal_v2_desup_hx
- E-201 (heating side of V-201 in the model) heat-transfer coefficient: 2,000 → 2,500 W/m²K
- On the drawing: E-201: U 2,000 → 2,500 W/m²K.

**Why.** Cheapest fix first: at 120% the fouled heater needs 9,794 m² of 8,800 m²; restoring the documented clean coefficient of 2,500 W/m²K drops the need to 7,836 m² (89%). No new equipment and no rating is changed.

**Rating and rating source.**

- V-201 evaporator: Data sheet Equipment ratings row: E-201 U 2,000 W/m²K in service, 2,500 W/m²K clean (marked ILLUSTRATIVE - confirm achieved clean coefficient by post-clean temperature/flow survey)

**Before / Proposed calculation** (this change alone, DWSIM at the target).

- Simulated maximum: 100.1 % → 100.1 % of today; first limit K-201 → K-201.

| Item | Check | Limit | Before | After |
|---|---|---|---|---|
| V-201 | boil-up duty vs heat from the heating steam (2 % closure tolerance) | available 188.4 MW | 187.3 MW (99 %) | 187.4 MW (99 %) |
| E-201 (V-201) | heater area needed (BPE included) vs installed | 8,800 m² | 9,794 m² (111 %) | 7,836 m² (89 %) |

**Field checks that could change this.**

- Clean heat transfer coefficient actually achieved on E-201 after cleaning (documented 2,500 W/m²K is marked ILLUSTRATIVE). Where: Post-clean survey on E-201: brine in/out temperatures on lines 2002/2003, condensate temperature on line 4001 and steam flow on line 3003, at steady rate; back-calculate the coefficient. If it differs: If the cleaned coefficient is below about 2,230 W/m²K, the 8,800 m² installed area is again too small at 120% and a parallel heater would be needed instead of cleaning alone
- Circulation rate and brine temperature rise through E-201 at 120% (not in the calibrated model). Where: Flow on line 2002 (P-201 discharge, rated 15,000 m³/h on the P&ID) and brine temperatures in lines 2002/2003 to confirm the rise stays within the 3 K data-sheet limit. If it differs: If circulation cannot keep the rise at or below 3 K at 120%, P-201 becomes a fourth limiting item and would need its own proposal

### 4.2 Add a small parallel vapour compressor K-202

Cloud 2 on the Rev B drawing. Cost class (agent estimate, unpriced): >$1M.

**What physically changes.**

- Adds K-202 compressor, 55 t/h suction (provisional rating: vendor quote to confirm / standard size 55 t/h suction, 2,400 kW shaft at pressure ratio 1.8 (3.08 bar discharge) - proposed rating only, not an existing rating)
- Re-pipes K-201 compressor inlet to the new tie-in (model streams S3001 → S3001_K201)
- Model-only bookkeeping (no field work of its own): Model-only branch K-201_SPLIT (connects the new tie-in in the model; no item of its own); Model-only junction K201_JOIN (connects the new tie-in in the model; no item of its own); Re-pipes D-201MIX junction inlet to the new tie-in (model streams S3002raw + TURBINE_EXH → S3002comp + TURBINE_EXH).
- On the drawing: K-202 drawn parallel to K-201 with tie-ins on the existing lines, block valves and a discharge check valve (sizes to confirm).

**Why.** K-201 is a fixed-throughput machine (data sheet: vapour above its 226.8 t/h suction capacity is the excess vapour). At 120% it is short by about 49.5 t/h; a parallel 55 t/h machine leaves K-201 at its rating and runs itself at 90% flow / 85.5% power. Existing ratings are untouched.

**Rating and rating source.**

- K-202: vendor quote to confirm / standard size 55 t/h suction, 2,400 kW shaft at pressure ratio 1.8 (3.08 bar discharge) - proposed rating only, not an existing rating

**Before / Proposed calculation** (this change alone, DWSIM at the target).

- Simulated maximum: 100.1 % → 107.9 % of today; first limit K-201 → V-201.

| Item | Check | Limit | Before | After |
|---|---|---|---|---|
| K-201 | suction flow vs capacity | 226.8 t/h | 272.2 t/h (120 %) | 223.4 t/h (98 %) |
| K-202 | suction flow vs capacity | 55 t/h | - | 48.8 t/h (89 %) |
| K-202 | shaft power vs motor | 2.4 MW | - | 2.02 MW (84 %) |
| K-201 | shaft power vs motor | 14 MW | 11.3 MW (81 %) | 9.26 MW (66 %) |

#### Preliminary equipment datasheet

Provisional equipment selection only: not a vendor datasheet and not a mechanical design approval. Operating point: combined design at 120 % (all 3 changes applied together, DWSIM).

| Tag | Service | Inlet | Outlet | Operating point | Pressure ratio / head | Rating | Rating source |
|---|---|---|---|---|---|---|---|
| K-202 | compressor | 115.2 °C, 1.7 bar(a) | 191.5 °C, 3.08 bar(a) | 49.5 t/h, 2.05 MW, efficiency 75 % (assumed) | 1.81; head to confirm | 55 t/h / 2.4 MW | vendor quote to confirm / standard size 55 t/h suction, 2,400 kW shaft at pressure ratio 1.8 (3.08 bar discharge) - proposed rating only, not an existing rating |

Missing vendor information (to confirm): vendor curve, mechanical design, materials.

**Simulator screening.** The figures above are a simulator screening solve, not a mechanical design. **Provisional equipment selection.** Ratings of new equipment are preliminary and marked to confirm. **Vendor and mechanical design approval.** Not granted: vendor curve, materials, relief sizing and shop design remain to confirm.


**Field checks that could change this.**

- None raised for this change.

### 4.3 Hold purge-heater steam at today's rate by trimming the overhead split

Cloud 3 on the Rev B drawing. Cost class (agent estimate, unpriced): no capex.

**What physically changes.**

- OVERHEAD_SPLIT branch split (share of flow per outlet): 8.4 % / 91.6 % → 7.0 % / 93.0 %
- On the drawing: line 3101: share of flow to this line 8.4 → 7.0 %.

**Why.** Operating change only: reducing the excess-vapour share to the purge heater from 8.44% to 7.03% of the overhead keeps its steam at 20,899 kg/h (today's rate) so its area need stays at 1,326 m² of 1,500 m² (88.4%) at 120% feed, instead of 106% with the share unchanged. The extra vapour instead goes through the new parallel compressor. No rating is changed.

**Rating and rating source.**

- Existing equipment; no rating is changed.

**Before / Proposed calculation** (this change alone, DWSIM at the target).

- Simulated maximum: 100.1 % → 98.5 % of today; first limit K-201 → K-201.

| Item | Check | Limit | Before | After |
|---|---|---|---|---|
| K-201 | suction flow vs capacity | 226.8 t/h | 272.2 t/h (120 %) | 276.3 t/h (122 %) |
| V-201 | boil-up duty vs heat from the heating steam (2 % closure tolerance) | available 191.1 MW | 190 MW (99 %) | 187.4 MW (98 %) |
| E-301 (V-301) | heater area needed (BPE included) vs installed | 1,500 m² | 1,592 m² (106 %) | 1,326 m² (88 %) |
| K-201 | shaft power vs motor | 14 MW | 11.3 MW (81 %) | 11.5 MW (82 %) |

**Field checks that could change this.**

- Whether the purge evaporator may boil off less per tonne of purge (no minimum boil-off, outlet concentration or disposal limit is documented). Where: Confirm with the disposal-well permit / purge specification and measure V-301 liquid outlet concentration and temperature on line 5101 at today's rate. If it differs: If a minimum purge evaporation or maximum disposal rate applies, the split trim is not allowed and E-301 would need added area plus more excess vapour, which would also increase the parallel compressor size

### 4.4 Other field checks

- Installed capacity of purge feed valve 5001/FV-301. Where: Nameplate / datasheet for valve 5001/FV-301 on line 5001; the model needs a flow coefficient Cv of 52 (US units) at 120% with nothing to compare it against. If it differs: If the installed valve is smaller than the required coefficient at 120%, it becomes a limiting item needing a trim change

## 5. Drawings

The next pages show the P&ID **Rev A** (existing, as received) and **Rev B** (proposed): each change is drawn in, clouded and numbered as in section 4, with the new design values written next to the equipment or line and a revision block (DRAFT - NOT APPROVED). Files in the pack: `rev_a.svg`, `rev_b.svg`, `rev_b.png`.

## 6. Risks and safety

### 6.1 Relief protection (P&ID relief scan)

- **Finding:** E-201 ST side: isolatable. relief 7002/PSV-202 only through 3003/C1: if one is closed the side has no relief. Heated side that can be blocked in.
- **Finding:** E-301 ST side: isolatable. relief 7001/PSV-201 only through 3101/C1: if one is closed the side has no relief. Heated side that can be blocked in.
- New equipment is not on the as-built P&ID: its relief, isolation and control design need engineering review before approval.

### 6.1b Electrical (one-line load flow, pandapower; ILLUSTRATIVE network)

- TX-1 45 → 133 % loaded; M-K-202 DOL start dip 29.0 % at its terminal; OVER: MV 4.16 kV switchgear: dip during M-K-202 start (DOL), LV 480 V MCC: dip during M-K-202 start (DOL), M-K-202-term start dip at M-K-202 terminal (DOL) (+5 more).
- One-line diagram: `/api/plant/salt_mvr/artifact/20261031-193443-electrical-check-for-the-decision-pack/one-line.svg` (artifact). Network: cases/salt_mvr/electrical.json; One-line diagram for the salt plant. Only two facts come from US 5,366,514 Table I: a 1.7 MW steam turbine generator (item 35) that 'is approximately that amount required to drive all electricity' of the plant, and K-201 driven by a gas turbine (so it is not an electrical load). Every other value is ILLUSTRATIVE: voltages, transformer ratings, the utility tie, cable data and the split of the 1.7 MW demand.

| Item | Check | Value | Limit | Basis |
|---|---|---|---|---|
| MV | 4.16 kV switchgear: dip during M-K-202 start (DOL) | 27.7 % | 10 % | typical practice: other buses dip at most 10 % during a motor start (contactor drop-out, lighting flicker) |
| LV | 480 V MCC: dip during M-K-202 start (DOL) | 27.7 % | 10 % | typical practice: other buses dip at most 10 % during a motor start (contactor drop-out, lighting flicker) |
| M-K-202-term | start dip at M-K-202 terminal (DOL) | 29.0 % | 15 % | typical practice: motor terminal voltage at least 85 % during start (IEC 60034-1 sets no start-dip limit) |
| LV | 480 V MCC: under-voltage 0.912 p.u. vs ±5 % | 8.8 % | 5 % | typical plant practice: steady-state bus voltage within ±5 % of nominal (IEC 60038 allows ±10 % at supply) |
| M-K-202-term | M-K-202 motor terminal: under-voltage 0.920 p.u. vs ±5 % | 8.0 % | 5 % | typical plant practice: steady-state bus voltage within ±5 % of nominal (IEC 60038 allows ±10 % at supply) |
| M-P201-term | M-P201 motor terminal: under-voltage 0.923 p.u. vs ±5 % | 7.7 % | 5 % | typical plant practice: steady-state bus voltage within ±5 % of nominal (IEC 60038 allows ±10 % at supply) |
| MV | 4.16 kV switchgear: under-voltage 0.925 p.u. vs ±5 % | 7.5 % | 5 % | typical plant practice: steady-state bus voltage within ±5 % of nominal (IEC 60038 allows ±10 % at supply) |
| TX-1 | transformer loading vs nameplate | 132.8 % | 100 % | IEC 60076-1: continuous loading within the nameplate rated power |
| M-K-202-cable | cable loading vs ampacity | 99.5 % | 100 % | cable ampacity (manufacturer rating, IEC 60287 basis) |
| TX-2 | transformer loading vs nameplate | 88.1 % | 100 % | IEC 60076-1: continuous loading within the nameplate rated power |
| UTIL | utility tie 34.5 kV: dip during M-K-202 start (DOL) | 3.7 % | 10 % | typical practice: other buses dip at most 10 % during a motor start (contactor drop-out, lighting flicker) |

- **Option: VFD start instead of direct-on-line.** Terminal start dip 29 % → 0.38 %. Still over with a VFD: LV 480 V MCC: under-voltage 0.912 p.u. vs ±5 % 8.8 %; M-K-202-term M-K-202 motor terminal: under-voltage 0.920 p.u. vs ±5 % 8.0 %; M-P201-term M-P201 motor terminal: under-voltage 0.923 p.u. vs ±5 % 7.7 %; MV 4.16 kV switchgear: under-voltage 0.925 p.u. vs ±5 % 7.5 %; TX-1 transformer loading vs nameplate 132.8 %. These are steady-state supply limits: a larger tie transformer or another supply is needed (to confirm).

### 6.1c Discipline gates (outside the process model)

Pass/fail only from a sourced check; a check over an ILLUSTRATIVE rating leaves its gate open until the rating is confirmed. Electrical is in section 6.1b.

| Gate | Status | Summary |
|---|---|---|
| robustness | **fail** | operating envelope 3/4 scenarios pass (fails: Target with heater fouled to the design-basis U (2,000 W/m²K)) |
| mechanical | **open** | 1 new machine within provisional ratings; guaranteed vendor curve, materials and mechanical design still needed |
| heat transfer | **open** | E-201 (clean): area needed 7,130 of 8,800 m² at the correlation U 3,297 W/m²K; the verified process design uses the model U 2,500 W/m²K, which governs until the geometry is confirmed; 2 checks over illustrative ratings or geometry, to confirm before this gate can pass or fail: E-201 brine circulation needed for the rise limit vs pump rating 396 %, E-201 shell-side pressure drop vs allowable 150 %; model-consistency note: model U 2,500 vs correlation U 3,297 W/m²K (clean) are 24 % apart |
| combustion | **open** | GT-201 + HRSG-201: steam 19.1 t/h (42,000 lb/h, ×1.20), stack 205 → 200 °C, duct firing 2.73 MW HHV (9.3 MMBtu/h), NOx added 0.4 ppmvd at 15 % O2 (screening); if HRSG steam rises with throughput (×1.20), it needs supplementary (duct) firing the unfired HRSG does not have: a modification to decide |
| piping utilities | **open** | no calculation adapter: tie-ins, line sizing, supports and utility headers remain open for K-202 |
| controls | **open** | no calculation adapter: control narrative, split/load-sharing control, cause & effect and permissives remain open for K-202 |
| process safety | **open** | no calculation adapter: change-focused HAZOP, relief case and isolation for the changed equipment remain open for K-202 |
| civil structural | **open** | no calculation adapter: plot, access, lifting and foundations remain open for K-202 |

Checks over their limit:

| Gate | Item | Check | Value | Limit | Result | Basis |
|---|---|---|---|---|---|---|
| robustness | V-201 | scenario 'Target with heater fouled to the design-basis U (2,000 W/m²K)': heater area needed (BPE included) vs installed | 9,794 m² | 8,800 m² | 111 % | DWSIM solve; scenario basis: basis.md equipment ratings: E-201 U 2,000 W/m²K in service; … |
| heat transfer | E-201 | shell-side pressure drop vs allowable | 0.1501 bar | 0.1 bar | 150 % (ILLUSTRATIVE rating) | typical practice for a condensing-steam shell at 3 bar(a): a few % of the absolute … |
| heat transfer | E-201 | brine circulation needed for the rise limit vs pump rating | 59,353 m³/h | 15,000 m³/h | 396 % (ILLUSTRATIVE rating) | data sheet Equipment ratings: P-201 forced-circulation pump 15,000 m³/h rated … |
| combustion | HRSG-201 | gas temperature into the superheater vs unfired design inlet | 533.8 C | 485 C | 48.82 K over the limit | the documented HRSG is unfired: above that inlet the superheater sees hotter gas than … |
| combustion | duct burner | local flame temperature vs thermal-NOx onset (screening) | 2,064 K | 1,800 K | 263.5 K over the limit | thermal (Zeldovich) NO formation becomes significant above about 1,800 K (e.g. Turns, An … |

### 6.2 Pre-startup safety review (PSSR), generated from the changes

- [ ] Plan and record the cleaning of E-201 (heating side of V-201); run a performance test after cleaning to confirm U of about 2,500 W/m²K.
- [ ] Confirm the new branch tee in the field (model node K-201_SPLIT), including branch isolation valves, drains, vents and flow direction.
- [ ] Isolation: confirm block valves on each nozzle of new K-202 before the line is opened to process fluid.
- [ ] Check valves and backflow: confirm a non-return device so parallel K-202 cannot be driven backwards. To confirm.
- [ ] Controls and parallel load sharing: confirm how K-202 shares load with the existing machine, including a manual fallback. To confirm.
- [ ] Alarms and trips: confirm process and machine alarms and trips for new K-202 before start-up. To confirm.
- [ ] Relief review: confirm relief protection for new K-202 and the changed piping. This file does not size a relief device.
- [ ] Commissioning: confirm line-up, rotation and a no-load check of new K-202 before process fluid.
- [ ] Materials and wet-service suitability of new K-202: to confirm. No materials certificate is on file.
- [ ] Vendor curve for new K-202: to confirm against vendor quote to confirm / standard size 55 t/h suction, 2,400 kW shaft at pressure ratio 1.8 (3.08 bar discharge) - proposed rating only, not an existing rating. The rating in this file is provisional.
- [ ] Turndown and surge: confirm the surge line, anti-surge control and minimum flow for new compressor K-202. To confirm; no vendor curve is on file.
- [ ] Confirm the new join tee in the field (model node K201_JOIN), including branch isolation valves, drains, vents and flow direction.
- [ ] Walk down the new tie-in at the inlet of K-201; confirm valves, drains, vents and flow direction match the Rev B drawing.
- [ ] Set the new split at OVERHEAD_SPLIT branch: share of flow to this line 8.4 → 7.0 %; confirm the flow control can hold it at the new rate and update the operating procedure.
- [ ] Update the P&ID, equipment datasheets and the operating procedure for every change above.
- [ ] Brief the operators on the new setpoints before start-up.
- [ ] Record the first 24 h of operation at the new throughput and compare with the model's predicted values in this file.

### 6.3 Second opinion

No second opinion was requested for this answer.

### 6.4 Open risks

- The result depends on ILLUSTRATIVE data-sheet values (section 2).
- 2 relief findings on changed equipment (section 6.1).
- Discipline screens over their limit: V-201 scenario 'Target with heater fouled to the design-basis U (2,000 W/m²K)': heater area needed (BPE included) vs installed 111 %; E-201 shell-side pressure drop vs allowable 150 %; E-201 brine circulation needed for the rise limit vs pump rating 396 %; HRSG-201 gas temperature into the superheater vs unfired design inlet 48.82 K over the limit (+1 more) (section 6.1c).

## 7. Approvals (DRAFT: not approved)

| Role | Name | Signature | Date |
|---|---|---|---|
| Process engineer | _ | _ | _ |
| Operations | _ | _ | _ |
| Process safety (MOC) | _ | _ | _ |
| Manager (approver) | _ | _ | _ |

## Appendix A. Reproducibility

- Code version (git): d239d14; simulator: DWSIM (headless) via plantagent.process.
- Audit-chain head hash: `4209d50bcb7b65d056f9b41fe8cbadc107304954725731a8069f40cdcc645d95` (chain intact: True).
- Model: vrc_cal_v2_desup_hx by muse-wonder-1.0 on 2026-10-29 22:17; answer by muse-wonder-1.0.
- Run labels and calculation records: vrc_cal_v2_desup_hx.
- Sections 1, 3 and 6.2 were recomputed when this file was made; re-run `python -m plantagent.decision salt_mvr` on the same revisions to reproduce them.

## Appendix B. Capability gaps

- None recorded.

## Appendix C. Model review

Status: **ok**.
- No findings.

An overall energy balance is not closed: the simulator's streams do not report enthalpy. Each evaporator's heat balance is checked instead (within 2 %; a model is blocked above 10 %).

## Appendix D. Model assumptions

Recorded by the model builder when the model was built (model text). Later model corrections (section 2) take precedence; items the current model no longer matches are marked **superseded**.

- Brine modelled as Water with Steam Tables (IAPWS-IF97) package; saturated crystallising brine in V-201 and V-301 handled by evaporator with NaCl mass fraction omitted, so salt production and boiling-point elevation are reported by the unit. brine boiling-point elevation (Sparrow) at 1.70 bar: water 115.17 C, saturated brine 124.86 C, BPE 9.69 K; at 1.01 bar: brine 108.68 C, BPE 8.72 K.
- CONFLICT used site data: E-201 installed area 8,800 m² from data sheet Equipment ratings row (U 2,000 W/m²K in service) over P&ID E-201 DesignHeatTransferArea 6,500 m².
- CONFLICT used site data: P-201 rated flow 15,000 m³/h from data sheet Equipment ratings row over P&ID P-201 DesignVolumeFlowRate 12,000 m³/h; this rating is entered as a limit check and the simulated circulation exceeds it - not hidden. **[superseded: P-201 is not a unit of the current model (a later model correction removed it)]**
- K-201 shaft-power limit 14,000 kW from P&ID K-201 DesignShaftPower; data sheet states shaft power is not stated in the patent. Suction capacity 226.8 t/h from data sheet Equipment ratings and Table I row for line 3001.
- Feed preheat train P-101, E-101, E-102 and T-401 excluded per data sheet Modelling scope row: 'take the brine entering V-201 from Table I (264.9 t/h at 125.6 C, plus 98.0 t/h elutriating brine at 60 C) instead of closing condensate-to-brine heat-recovery loops'. Their connections 1002,1003,4201,4002,4001,4101,3201 and 4301 are therefore boundary flows, not closed in the VRC model.
- Turbine exhaust 15.9 t/h at 3.08 bar(a) is fixed and does not scale with throughput, per data sheet Modelling scope row; its temperature is not stated, assumed 200 C superheated vapour as a feed - it only affects the D-201 mixer/desuperheating duty, D-201 outlet is fixed at the measured 135 C.
- D-201 desuperheater modelled as a mixer for turbine exhaust followed by cooler unit D-201 fixed at 135 C (data sheet line 3003 row). The condensate spray itself is not recirculated as a material stream because E-201 condensate is produced downstream of D-201 in DWSIM sequence; spray is represented by the cooler duty. Hence simulated S3003/E-201 condensate mass is 242.7 t/h vs measured 251.7 t/h, the 9.0 t/h difference being the spray - stated in calibration.
- V-201 forced-circulation loop 2001-2002-2003 modelled once-through: CIRC_S2001 feed at the measured brine temperature 125.6 C and 1.70 bar vessel pressure plus pump head, through P-201 (dP 1.33 bar, eff 80% assumed - no efficiency on P&ID/data sheet) and E-201 rating, returning as S2003. No recycle unit used because supply temperature is set by V-201 boiling, per instruction for known-temperature loops.
- E-301 is the heating side of evaporator V-301 (heating stream S3101v to S4101, area 900 m² from P&ID E-301 DesignHeatTransferArea and data sheet) plus, in topology terms, its cold circulation is the V-301 feed; a separate E-301 hx rating was probed separately and not sequenced in the final logged run due to DWSIM double-use of the heating stream - E-301 area check is therefore via V-301 area needed vs 900 m². **[superseded: the current model uses 1,500 m² for E-301, not 900 m²]**
- Compressor K-201 efficiency 75% assumed (not on P&ID or data sheet), discharge fixed at 3.08 bar(a) (data sheet K-201 discharge row, ratio 1.8 = P&ID DesignPressureRatio).
- V-301 feed in the final run is taken at its measured body condition 108.9 C liquid (data sheet V-301 row / purge disposal row) via valve 5001/FV-301, because feeding 125.6 C vapour-fraction feed flashes in DWSIM and gives negative boil duty; purge mass 47.6 t/h, excess heating vapour 20.9 t/h and disposal 6.8 t/h are all preserved.
- Relief valves 7001/PSV-201 (3.5 barg, P&ID V-201), 7002/PSV-202 (4.5 barg) and 7003/PSV-301 (1 barg) carry no normal flow and are not modelled as process units; vessel pressure limits in the run use P&ID design pressures V-201 3.5 barg and V-301 1 barg converted to absolute (4.51 / 2.01 bar).
- E-201 brine rise requirement at most 3 K (data sheet Process requirements row) entered as E-201 cold outlet limit 125.6+3.0=128.6 C; condensate leaves saturated at shell pressure entered as hot outlet 134.4 C (data sheet E-201 condensate row).
