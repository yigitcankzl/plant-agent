DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum — Williams Geismar Olefins Plant Reboiler B Rupture (June 13, 2013)

**Case:** williams_geismar
**Facility:** Williams Geismar Olefins Plant, propylene fractionator reboiler rupture and fire, Geismar, Louisiana, June 13, 2013
**Source:** U.S. Chemical Safety and Hazard Investigation Board, Williams Geismar Olefins Plant Reboiler Rupture and Fire, Case Study No. 2013-03-I-LA, October 2016 (public record) — https://www.csb.gov/williams-olefins-plant-explosion-and-fire-/
**Model:** muse-spark-1.3-contributor

## Purpose

Determine failure mechanism for propylene fractionator Reboiler B rupture about three minutes after hot quench water admission on June 13, 2013 (p.11), estimate pressures reachable in the shell when heated blocked-in, explain why the reboiler was not protected from overpressure, and recommend design, procedural and management changes to prevent recurrence.

## Background

Plant and units on path (all citations from JSON only):

- Plant location: located in Geismar, Louisiana, approximately 20 miles southeast of Baton Rouge (p.6) [D-02: approx 110 persons; D-03: 600 million lb/yr ethylene original; D-04: 1.35 billion ethylene and 80 million propylene pre-incident; D-05: approx 800 contractors, goal 1.95 billion ethylene].
- Path: Cracking furnaces (ethane/propane to ethylene/propylene) - p.7; Quench tower - p.8 Fig.2; Quench water settler - p.8 Fig.2; Quench water pumps - p.8 Fig.2; Quench water distribution header to process heat exchangers (parallel bank incl. Reboilers A/B) - p.8 Fig.2; Reboiler A shell-and-tube - p.6, p.9, Fig.3/4; Reboiler B shell-and-tube - ruptured - p.9 fn11-13; Reboiler A/B tube-side ball isolation valves (2001) - p.10 Fig.4; Quench water coolers - p.8 Fig.2; Propylene fractionator column - p.6, p.10 Fig.4; Reboiler A/B shell-side piping: liquid feed from fractionator bottom + vapor return to fractionator mid (each with 2001 gate valve) - p.10 Fig.4; Fractionator overhead: pressure relief valve - p.9-p.10; Fractionator overhead condenser + reflux drum - p.10 Fig.4; Quench water FT/FO control loop - p.10 Fig.4.
- Reboiler geometry (p.9 fn11-13): The heat exchangers are 24 feet 8 inches long end-to-end (p.9 fn11) [D-16]; Each exchanger shell is approximately 18.5 feet long and over 5 feet in diameter (p.9 fn11) [D-17]; The tubes are each 3/4-inch in diameter, and each heat exchanger contains 3,020 tubes (p.9 fn11) [D-18]; tubes would span over 10.5 miles (p.9 fn11) [D-19]; six-pass heat exchangers (p.9 fn13) [D-20] depicted as two-pass for simplicity.
- Tag conflict — **ASSUMPTION for Steps 1-2 only, RFI-01:** The reboiler that failed, EA-425B ("Reboiler B") was one of two reboilers (Reboiler A and Reboiler B) (p.6) [D-06] conflicts with EA-435A "Reboiler A" EA-435B "Reboiler B" (p.8) [D-07]. Functional identity (B = standby 16 mo, ruptured) is consistent; tag typo does not change mechanism. Verify via nameplate/P&ID before calculations.
- Operating philosophy: In 2001, Williams installed valves on the shell-side and tube-side reboiler piping to allow for continuous operation with only one reboiler operating at a time (p.9) [D-14]. The other reboiler would be offline but ready for operation, isolated from the process by the new valves (p.9).
- Relief claim vs hazard: Pressure relief valve protected propylene fractionator and shells of Reboilers A and B (p.10 Fig.4 legend) [D-23]; Gate valves installed on shell-side reboiler piping in 2001 (p.10 Fig.4 legend) [D-21]; Ball valves installed on tube-side reboiler piping in 2001 (p.10 Fig.4 legend) [D-22]. If the new valves were not in the proper position (open or closed) for each phase of operation, the reboiler could be isolated from its protective pressure relief valve located on top of the propylene fractionator (Figure 4) (p.9) [D-15].
- Fouling / trigger: some oily material remains in the quench water. Over time, some of this material adheres to and builds up on the inside of process equipment such as heat exchanger tubes, resulting in a decrease in both heat transfer efficiency and quench water flow rate. The buildup of such material is called fouling (p.8); quench water flow through the operating propylene fractionator reboiler (Reboiler A) had dropped gradually over the past day (Figure 5) (p.11) [D-24].
- Timeline: at 8:33 am, the operations supervisor likely opened the quench water valves on the offline reboiler, Reboiler B, as indicated by the rapid increase in quench water flow rate shown in Figure 6 (p.11) [D-25]; Approximately three minutes later, Reboiler B exploded (p.11) [D-26]; Reboiler B ruptures approximately three minutes later (p.11-p.12 Fig.6 caption).
- Consequences: launched a portion of the propylene fractionator reboiler piping into a pipe rack approximately 30 feet overhead (Figure 8) (p.11) [D-27] — **corrected: vertical height to rack, not horizontal throw**; A Williams operator working near the propylene fractionator at the time of the explosion died at the scene. The operations supervisor succumbed to severe burn injuries the next day (p.12) [D-28: 2 dead]; 167 personnel reported injuries (p.12) [D-29]; Of the 167 workers who reported injuries, three were Williams employees and 164 were contractors (p.12 fn14) [D-30]; The fire lasted approximately 3.5 hours (p.12) [D-31]; Williams reported releasing over 30,000 pounds of flammable hydrocarbons during the incident (p.12) [D-32]; The plant remained down for 18 months and restarted in January 2015 (p.12) [D-33]. Standby: Reboiler B had been offline for 16 months while Reboiler A was in operation (p.6) [D-08].

## Design Criteria

- C-01 Overpressure protection path must remain open — p.9: 'If the new valves were not in the proper position (open or closed) for each phase of operation, the reboiler could be isolated from its protective pressure relief valve located on top of the propylene fractionator (Figure 4).' + p.10 Fig.4 legend 'Pressure relief valve protected propylene fractionator and shells of Reboilers A and B' — Value: Reboiler A/B shells protected only via fractionator overhead PRV; 2001 shell-side gate valves can isolate shell from PRV = hazard
- C-02 Operating philosophy - single-reboiler continuous operation — p.9: 'In 2001, Williams installed valves on the shell-side and tube-side reboiler piping to allow for continuous operation with only one reboiler operating at a time. The other reboiler would be offline but ready for operation (see Section 5.1), isolated from the process by the new valves.' — Value: One reboiler in service, one offline isolated standby; firm capacity = one reboiler with largest (other) unit out of service
- C-03 Tube-side heating medium temperature — p.9: 'Quench water enters the propylene fractionator reboilers at approximately 185 degF' — Value: approx 185 F quench water inlet (task brief states about 187 F - see RFI-02)
- C-04 Shell-side process fluid composition and inlet temperature — p.9: 'tube-side hot quench water vaporizes shell-side hydrocarbon process fluid, which is approximately 95% propane with the balance composed mostly of propylene and C4s' + 'which enters the reboiler at a temperature of approximately 130 degF' — Value: approx 95% propane, balance propylene + C4s; shell inlet approx 130 F
- C-05 Standby duration before failure — p.6: 'Reboiler B had been offline for 16 months while Reboiler A was in operation' + p.11 incident date June 13, 2013 — Value: 16 months offline (Feb 2012 to June 2013 per task brief - to be verified RFI-04)
- C-06 Failure timeline — p.11: 'at 8:33 am, the operations supervisor likely opened the quench water valves on the offline reboiler, Reboiler B' + 'Approximately three minutes later, Reboiler B exploded.' + p.12 Fig.6 caption 'Reboiler B ruptures approximately three minutes later.' — Value: Hot water admission ~08:33, rupture ~3 min later
- C-07 Shell mechanical limits — Task brief (not in p.6-13): shell MAWP 300 psig, hydrostatic test 450 psig - See RFI-03 — **ASSUMPTION for scoping only: MAWP 300 psig, hydrotest 450 psig. Reason: provided in task brief; no page citation in 6-13; must verify from nameplate/dossier before any pressure calculation**
- C-08 Fouling service duty — p.8: 'some oily material remains in the quench water. Over time, some of this material adheres to and builds up on the inside of process equipment such as heat exchanger tubes, resulting in a decrease in both heat transfer efficiency and quench water flow rate. The buildup of such material is called fouling.' + p.6 fn7 — Value: Quench-water-side fouling reduces flow and heat transfer; triggers nonroutine switching activity
- C-09 Consequence severity baseline — p.11: 'launched a portion of the propylene fractionator reboiler piping into a pipe rack approximately 30 feet overhead' + p.12: 'fire lasted approximately 3.5 hours, and Williams reported releasing over 30,000 pounds of flammable hydrocarbons' — Value: 30 ft missile throw, 3.5 h fire, >30,000 lb release - confirms catastrophic shell rupture, not tube leak [corrected to vertical height per QA/QC]

## Data and Assumptions

Data register excerpts used for mechanism (full list D-01 to D-33 in JSON):

- D-09: The process fluid on the shell-side of these reboilers is heated by hot "quench water," flowing through the tubes (p.6) — shell = hydrocarbon, tubes = quench water
- D-11: shell-side hydrocarbon process fluid, which is approximately 95% propane with the balance composed mostly of propylene and C4s (p.9)
- D-12: Quench water enters the propylene fractionator reboilers at approximately 185 degF (p.9)
- D-13: partially vaporizes the shell-side propane, which enters the reboiler at a temperature of approximately 130 degF (p.9)

**ASSUMPTIONS (labelled, with RFI reason):**

- RFI-01 Tag: **ASSUMPTION:** failed unit is Reboiler B (whichever tag), geometry per p.9 fn11. Reason: functional identity consistent; tag typo does not change mechanism.
- RFI-02 Temperature: **ASSUMPTION:** use 185-187 F range as upper-bound heating temperature. Reason: p.9 approx 185F vs brief ~187F; both >>130F shell fluid (p.9); bounds heat input until trend retrieved. Future run RB-HEAT-01 will use measured value.
- RFI-03 MAWP/hydrotest/PRV: **ASSUMPTION:** adopt task-brief 300 psig MAWP / 450 psig hydrotest as provisional limits. Reason: provided for study; flagged UNVERIFIED. No failure-pressure conclusion to rely on them until nameplate/U-1 and PRV datasheet confirm. Future run RB-PRESS-01 will compare against verified values.
- RFI-04 Layup: **ASSUMPTION:** shell block valves were closed (isolated), tube side drained/isolated until June 13. Reason: consistent with 2001 one-reboiler philosophy (p.9) and isolated-shell hazard (p.9-p.10). Whether liquid propane leaked in over 16 mo to be tested. Future run RB-ISO-01 models (a) nitrogen + leaked propane, (b) full-liquid propane.
- RFI-05 Inventory: **ASSUMPTION:** shell contained liquid propane mixture capable of hydraulic expansion + vaporization. Reason: 3-min rupture after hot-water admission (p.11) implies incompressible/boiling liquid present, not nitrogen gas alone. To be closed by sample/level. Future runs RB-PRESS-01 (liquid expansion) and RB-PRESS-02 (vapor pressure at 185-187F) bound it.
- RFI-06 Valve lineup: **ASSUMPTION:** B shell inlet and vapor-return gates were closed (blocked-in, no relief path). Reason: p.9 hazard + fact of rupture in ~3 min (p.11) despite PRV existing on fractionator (p.10) implies no open relief path. Verify via DCS/valve-stem photography.
- RFI-07 PRV: **ASSUMPTION:** no dedicated shell thermal-relief and no administrative control kept relief path open. Reason: rupture occurred; if adequate thermal relief existed it should have prevented hydraulic burst. Confirm via relief study.
- RFI-08 Initial T/P: **ASSUMPTION:** initial shell ~ ambient / ~130F or lower, at or above propane vapor pressure if liquid present. Reason: operating inlet 130F (p.9) is best proxy; ambient Louisiana June also warm. Sensitivity in RB-PRESS-01.
- RFI-09 Flows: **ASSUMPTION:** quench-water flow after opening was sufficient to heat shell inventory within minutes (evidenced by rapid flow rise per p.11-12 Fig.6 caption). Reason: qualitative trend confirms flow, not magnitude; do not assume flow number.
- RFI-10 Volume: **ASSUMPTION:** use nominal 5.0-5.5 ft ID x 18.5 ft for scoping volume only; label all volumes APPROXIMATE. Reason: fn11 is approximate ('approximately', 'over'); precise calc requires U-stamp drawing. Future run RB-VOL-01 will use measured ID.
- Hydraulic screening: EPANET single-point pump curves + Hazen-Williams C screening (C80 fouled vs C120 clean) and water at ~185F proxy. Reason: screening relative change only; absolute gpm not calibrated (no numeric Fig.5/6, RFI-09). No energy computed; heat judged via DWSIM bubble/fluid tools.
- Cost: catalogue has no refinery PSV/flare curve — see Alternatives disagreement.

Test plan to close RFIs (TP-03, TP-06, TP-05, TP-09 in JSON): TP-03 Mechanical verification - nameplate, dossier and PRV bench review (closes RFI-03, RFI-07); TP-06 Valve lineup as-found survey (closes RFI-06); TP-05 Inventory and geometry - drain, sample and dimensional (closes RFI-04, RFI-05, RFI-10); TP-09 Thermal-hydraulic historian retrieval + instrument check (closes RFI-02, RFI-08, RFI-09).

## Model Calibration

Base model run: QW-BASE-CAL.

| Test | Run label | Simulated | Measured (source) | Note |
|---|---|---|---|---|
| CAL-01 Fouled single-reboiler operation (A in service, B standby tubes closed) | QW-BASE-CAL | QW-BASE-CAL: total 3625.4 gpm all through fouled A (P-A-TUBES 3625.4 gpm at 10.28 fps); B standby P-B-TUBES 0.0 gpm | Gradual drop over past day through Reboiler A (p.11) + fouling reduces flow and heat transfer (p.8) | Direction matches: fouled C80 branch restrictive. No numeric Fig.5 in pages (RFI-09) so quantitative residual not computable; absolute gpm screening only. residual_pct 0 logged but withdrawn per QA/QC — uncalibrated. |
| CAL-02 Switch event - B tubes opened | QW-SWITCH | QW-SWITCH: total 5353.5 gpm (A 2625.9 gpm + B 2727.6 gpm); increase +1728 gpm (+47.7% vs QW-BASE-CAL 3625.4 gpm) on opening B | Rapid increase in quench flow at ~08:33 when B tube valves opened (p.11) + Fig.6 caption rapid rise then rupture ~3 min later (p.11-p.12) | Step change direction and ~48% surge qualitatively reproduces Fig.6 jump. Timing 08:33 to ~08:36 (p.11) anchors heat-input window; no numeric flow in pages. Absolute gpm withdrawn as evidence per QA/QC. |
| CAL-03 Blocked-shell isolation (existing) | SHELL-ISO-CLOSED | SHELL-ISO-CLOSED: P-B-VRET-GATE 0.0 gpm, P-B-LIQ-GATE 0.0 gpm, J-B-SHELL 11.93 psi (trapped, no relief communication) | B shell gates closed = isolated from top PRV possible (p.9); as-found ASSUMED closed (RFI-06) because rupture occurred despite PRV (p.10 legend claims PRV protects column + both shells) | Exact zero match proves blocked-volume topology used for pressure analysis. |
| CAL-04 Open-relief-path continuity (fixed) | SHELL-ISO-OPEN | SHELL-ISO-OPEN: P-B-VRET-GATE 1412.3 gpm at 5.77 fps, P-B-LIQ-GATE 1412.3 gpm at 9.01 fps, J-B-SHELL 12.43 psi | Fig.4 intent (p.10): open gates communicate shell with fractionator + overhead PRV | Continuity proven; contrast 0.0 vs 1412 gpm validates isolation model. No field flow numeric; residual vs zero-blocked baseline. |

Per QA/QC: QW-BASE-CAL / QW-SWITCH absolute gpm (+47.7%, 3625.4->5353.5 gpm) and 0% residual_pct are withdrawn — models uncalibrated (no numeric Fig.5/6), reservoir balance arbitrary, velocities non-physical (e.g., P-A-TIN 23.14 fps, P-RET 15.19 fps). Retained only qualitative direction (fouled A restrictive, opening B admits heat in minutes consistent with ~3 min p.11).

Per-tube screening correction: velocity tool 0.656 fps for B-branch-corrected 0.0013 mgd/tube through 0.75-in (3020 tubes p.9, OD as ID **ASSUMPTION** for screening, displacement unknown) — not 0.872 fps which used total flow. Fouling-regime conclusion screening only.

## Capacity Evaluation (table)

| Unit | Limit | Binds at / Evidence | Limits target? |
|---|---|---|---|
| Reboiler B shell (EA-425B/435B tag conflict p.6 vs p.8, 18.5 ft x >5 ft, 3020 x 3/4-in 6-pass p.9) | Shell MAWP 300 psig **ASSUMPTION** (hydro 450 psig **ASSUMPTION**) | Heating trapped liquid 130F (p.9) to 185F (p.9)/187F (brief) in blocked volume. Evidence: bubble_pressure tool: 19.19 bar at 54.44C (130F), 34.96 bar at 85C (185F), 35.67 bar at 86.11C (187F) for 95% propane/5% propylene (p.9 composition) (**ASSUMPTION** 95/5 mole, C4s omitted, mol vs wt unspecified p.9). fluid_properties at 21.7 bar: liquid 441.28 kg/m3 at 54.44C (vap frac 0.0) -> vapor 42.28 kg/m3 at 85C (vap frac 1.0), so at MAWP pressure fluid must vaporize/expand; liquid expansion drives higher still (tool note). MAWP 300 psig + hydro 450 psig **ASSUMPTIONS**. Rupture ~3 min after 08:33 (p.11), missile 30 ft overhead vertical height (p.11, corrected), >30,000 lb release + 3.5-h fire (p.12). Provisional: 300 psig = ~21.7 bara, 450 psig = ~32.0 bara, so 35.67 bara exceeds both **if ratings correct — unverified, TP-03 required**. | true |
| Shell relief path (2001 gates + fractionator overhead PRV) | Overpressure path must remain open (C-01); no block valve between vessel and PSV without controls | 2001 shell gates closed (**ASSUMED** as-found, RFI-06). Evidence: p.9: valves can isolate shell from top PRV; p.10: gates added 2001, single PRV claimed to protect column + both shells. SHELL-ISO-CLOSED 0.0 gpm both shell paths vs SHELL-ISO-OPEN 1412.3 gpm when open. No dedicated thermal relief found (**ASSUMPTION** RFI-07; rupture proves). | true |
| Reboiler A tubes + quench loop (fouled) | Quench circulation / heat-transfer duty (one-reboiler continuous operation p.9) | Past-day gradual flow drop (p.11) from quench-side fouling (p.8). Evidence: p.8 oily fouling reduces flow + heat transfer; p.11 A flow dropped past day; QW-SWITCH fouled A 2625.9 gpm vs clean B 2727.6 gpm; per-tube velocity tool 0.872 fps at 0.00173 mgd through 0.75-in (3020 tubes p.9) = low-velocity fouling regime — **corrected to ~0.66 fps for B-branch 0.0013 mgd/tube, screening only**. Nonroutine switch to standby B precipitated event. | false |
| Reboiler B tubes (quench-water side) | Tube-side heat input rate (quench 185F p.9 heating 130F shell fluid p.9) | 08:33 admission of ~185-187F water to cold blocked B shell; full parallel flow in <minutes. Evidence: QW-BASE-CAL 3625.4 gpm -> QW-SWITCH 5353.5 gpm (+47.7%) — **withdrawn, screening only**; B tubes 2727.6 gpm at 7.74 fps, 8-in leads ~16-17 fps screening (high but screening only). 3-min to burst (p.11) consistent with rapid heating of trapped inventory by 3020-tube bundle (>10.5 miles total tube p.9). Firm philosophy one reboiler in service, other isolated standby (p.9) = no spare relief. | true |

Failure mechanism finding (run SHELL-CLOSED-V2): Blocked-liquid heating. SHELL-CLOSED-V2 P-VRET-GATE 0.0 gpm + P-LIQ-GATE 0.0 gpm proves zero relief communication when gates closed. Heated blocked propane (p.9) reaches bubble 35.67 bar absolute at 86.11C per bubble_pressure vs MAWP 300 psig **ASSUMPTION** - unverified rating, provisional only. Rupture ~3 min after 08:33 admission (p.11) consistent with blocked-liquid heating. Shell burst, not tube leak (>30,000 lb + 3.5-h fire p.12).

## Alternatives (table with cost class)

| Option | Run label / Unit | Result | Cost class (analysis) / Recommended? |
|---|---|---|---|
| BASE - As-found: B shell isolated by 2001 gates from fractionator top PRV | SHELL-CLOSED-V2 / Reboiler B shell + 2001 gates + overhead PRV | FAIL: SHELL-CLOSED-V2 P-VRET-GATE 0.0 gpm + P-LIQ-GATE 0.0 gpm proves zero relief communication when gates closed. Heated blocked propane (p.9) reaches bubble 35.67 bar absolute at 86.11C per bubble_pressure vs MAWP 300 psig **ASSUMPTION** - unverified rating, provisional only. Rupture ~3 min after 08:33 admission (p.11) consistent with blocked-liquid heating. | n/a / No (meets_target false). Cost basis: No capital - as-found blocked condition. Topology screening only. |
| OPT-1 Dedicated shell thermal/blocked-outlet PSV on each reboiler shell to flare, always in communication with shell | SHELL-PSV-V2 / Reboiler B shell | CONDITIONAL PASS (topology, not sizing): SHELL-PSV-V2 retains open branch P-PSV to flare with gates closed (P-VRET-GATE 0.0 gpm, P-LIQ-GATE 0.0 gpm, P-PSV 0.0 gpm steady-state with no driving head, J-PSV 13.01 psi same as J-SHELL). Zero flow expected without overpressure driving head - does NOT demonstrate capacity. Capacity must be sized per API 521 thermal + wetted boiling for trapped ~95% propane (p.9) heated 130F (p.9) to 185F (p.9)/187F brief; setpoint/orifice/two-phase calc still required (TP). | **$100k-$1M** / Yes (meets_target true). Cost basis: No catalogue curve for refinery PSV-to-flare. **ASSUMPTION** judgement: flare-tied PSV typically $100k-$1M installed; verify by detailed estimate. Order-of-magnitude only. |
| OPT-2 Eliminate isolation: remove 2001 gates or car-seal-lock open with interlocked permissive | SHELL-OPEN-V2 / 2001 shell gate valves + relief path | TOPOLOGY PASS only: SHELL-OPEN-V2 restores continuity P-VRET-GATE 957.5 gpm at 6.11 fps + P-LIQ-GATE 957.5 gpm at 10.86 fps vs 0.0 gpm closed. Proves open vs blocked status only - water single-phase proxy, absolute gpm/fps not propane relief rate. Restores Fig.4 intent (p.10) but retains single-PRV dependence; requires OPT-1 for defense-in-depth. Interlock not verified by EPANET. | **<$100k** / No (requires OPT-1). Cost basis: Locks, car-seals, position alarms/interlock logic + SOP rewrite. No pressure equipment. **ASSUMPTION** <$100k judgement, no catalogue curve applicable. (meets_target true for topology) |

Drawing changes (anchor 2001.0): Add dedicated thermal/blocked-outlet PSV on each reboiler shell to flare, no block valve between shell and PSV without controls; verify MAWP/setpoint from nameplate/U-1 (TP-03). Remove 2001 shell isolation gates or show CSO-locked open with position alarm + interlocked permissive blocking tube-side quench admission unless shell relief path proven open; add shell PT with control-room alarm.

Quoted catalogue cost estimate — **DISAGREEMENT explicitly noted:**

> cost_estimates.OPT-1-THERMAL-PSV: lines [{id: C-PIPE-01, item: Water pipeline, open cut, rural, soil, incl. appurtenances (any material), x: 6.0 in, qty: 100.0, unit_cost_base: 139, base_year: 2023-01, escalation: 1.0, cost: 14000.0, note: Proxy for 2x dedicated shell thermal-relief laterals + tie-in to flare/relief header: 6-in minimum curve size, 100 ft total screening length. PSV skids, engineering, contingency excluded - order-of-magnitude only, source: TWDB Uniform Costing Model User Guide v3.0 (March 2024), Appendix: 'TWDB UCM Update: Proposed Unit Cost Updates' memo (Feb 27 2024), pdf p.65, memo Table 3 (Page 10 of 33)}], total: 14000.0, dollars: 2023-09 (ENR CCI 13485.67), aace_class: 5, range: [7000.0, 28000.0], range_basis: AACE 18R-97 class 5: low -20% to -50%, high +30% to +100%; widest band shown, note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them.

**DISAGREEMENT:** Analysis text withdraws C-PIPE-01 $14k as scope mismatch (water pipeline vs ASME/API PSV) violating match-curve-scope rule. Prior C-PIPE-01 $14k WITHDRAWN; catalogue has no PSV/flare curve. Analysis cost class $100k-$1M **ASSUMPTION** judgement applies, requiring detailed estimate. Diameters/lengths withdrawn. Do not use $14k for decision.

Quoted standards checks — **DISAGREEMENT explicitly noted:**

> standards_checks: [{rule_id: W-DS-05, status: pass, value: 12.0, limit: >= 6 in, rule: Minimum water main diameter 6 in where fire protection/hydrants are served; 3 in where no fire protection., citation: Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 8.2.2 (pdf p.205 (printed p.154)), basis: QW-BASE-CAL}, {rule_id: W-PS-01, status: pass, value: 2.0, limit: >= 2 pumps, rule: Every pumping station has at least two pumps., citation: Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 6.2.1 (pdf p.187 (printed p.136)), basis: p.6}]

**DISAGREEMENT:** Analysis text rejects W-DS-05 / W-PS-01 passes and firm-capacity application to reboilers as wrong standard. Ten States water rules do not govern ASME VIII / API 521 refinery PSV; no standards_check applicable in available tools. Governed by ASME/API + MOC/PHA. Quoted PASS results shall not be cited as compliance for overpressure protection.

## QA/QC Summary

Checked citations: D-11 p.9 ~95% propane verified by read p.9; D-12 p.9 quench ~185F verified by read p.9; D-13 p.9 shell inlet ~130F verified by read p.9; D-14/C-02 p.9 2001 valves one-reboiler standby verified by read p.9 + Fig4 p.10 image; D-23/C-01 p.10 PRV protects column+both shells + gate/ball legend verified by view p.10 image; D-24 p.11 quench flow dropped past day verified by read p.11; D-25/D-26 p.11 08:33 opening + ~3 min rupture verified by read p.11; D-31/D-32 p.12 3.5h fire + >30,000 lb release verified by read p.12.

Checked runs: QW-BASE-CAL rerun matches_logged_result true; QW-SWITCH rerun matches_logged_result true; SHELL-ISO-CLOSED rerun matches_logged_result true (0.0 gpm both gates); SHELL-ISO-OPEN rerun matches_logged_result true (1412.3 gpm); SHELL-PSV-DED rerun matches_logged_result true (0.0 gpm all incl PSV).

Issues and resolution (10 items):

1. Failure-pressure on unverified MAWP/hydrotest (major) — fixed: downgraded to provisional, bara conversion (~21.7/~32.0), require TP-03.
2. OPT-1 PSV claimed verified but zero flow, no sizing (major) — fixed: rewritten as CONDITIONAL topology only (J-PSV=J-SHELL 13.01 psi), API 521 sizing still required.
3. Hydrocarbon flashing with water hydraulics (major) — fixed: re-ran SHELL-CLOSED-V2/OPEN-V2/PSV-V2 as topology screening only with **ASSUMPTION** heads datum + water proxy disclaimer.
4. Cost scope mismatch C-PIPE-01 (major) — fixed: WITHDREW $14k proxy; replaced with $100k-$1M judgement.
5. False calibration 0% residual, non-physical velocities (major) — fixed: withdrew 0% residual and absolute gpm as evidence; uncalibrated.
6. Per-tube velocity inconsistent (minor) — fixed: corrected to 0.656 fps for 0.0013 mgd/tube, OD as ID **ASSUMPTION**.
7. Wrong standards (minor) — rejected/withdrawn: Ten States NOT applicable; ASME VIII/API 521 govern.
8. Pressure-calc traceability + units (minor) — fixed: documented fresh rerunnable bubble_pressure (95/5 mole **ASSUMPTION**, C4s omitted) 19.19/34.96/35.67 bar abs + fluid_properties 440.6 vap 0.0 to 42.28 vap 1.0; prior bubble1/props2 superseded; bar absolute vs psig gauge conversion stated.
9. Consequence metric misread 30 ft (minor) — fixed: corrected to vertical height to rack per p.11.
10. Unverified dates/geometry as fact (minor) — fixed: Feb 2012, tag EA-425B vs EA-435A/B, ~18.5 ft x >5 ft labelled APPROXIMATE/**ASSUMPTION**.

## Recommendations

- ROOT CAUSE fix OPT-1 + OPT-2 + layup/SOP. Verify MAWP/PRV via nameplate/U-1 before final sizing (TP-03).
- DESIGN: dedicated shell PSV(s) to flare per API 521 + CSO-lock/interlock 2001 gates + shell PT alarm; MOC/PHA revalidate 2001 change. (Unit: Overpressure protection path; evidence: SHELL-CLOSED-V2 J-SHELL 20.6 psi trapped 0.0 gpm; SHELL-OPEN-V2 J-SHELL 21.25 psi 957.5 gpm; SHELL-PSV-V2 gates 0.0 gpm but PSV branch J-PSV 13.01 psi = J-SHELL, open status retained. Heads are **ASSUMPTION** datum, water proxy - topology only, not relief sizing. Ten States NOT applicable.)
- CONTRIBUTING fixes: defined layup (drain/depressure/inert/blind/level-verified), leak-check, written switch SOP (prove relief open, drain/vent, slow warmup, monitor P/T), fouling monitoring, training+MOC, resolve tag EA-425B vs EA-435A/B. (Evidence: one-reboiler operation with other isolated standby (p.9); QW screening withdrawn; per-tube ~0.66 fps screening; ad-hoc troubleshooting at morning meeting (p.11); layup reportedly nitrogen behind single blocks (brief) vs propane leakage unverified; geometry APPROXIMATE.)
- Execute TP-03, TP-06, TP-05, TP-09 before detailed relief sizing (RB-PRESS-01/02, RB-VOL-01, RB-ISO-01, RB-HEAT-01).

## Limitations

- All pressure-vs-rating conclusions provisional: MAWP 300 psig / hydro 450 psig are **ASSUMPTIONS** from brief only (no pressure in p.6-13). Require nameplate/U-1 + PRV datasheet (TP-03).
- Blocked-in topology (B shell gates closed 08:33-08:36) is **ASSUMPTION** (RFI-06); verify via as-found survey (TP-06).
- Trapped liquid propane inventory and fill fraction are **ASSUMPTION** (RFI-05); nitrogen-only case would reject hydraulic-burst model; verify via drain/sample/level (TP-05).
- Hot water 185-187F range **ASSUMPTION** (RFI-02); shell initial ~130F proxy (RFI-08); verify via historian (TP-09). No numeric Fig.5/6 flows in pages (RFI-09).
- Geometry ~18.5 ft x >5 ft + 3020 tubes APPROXIMATE (RFI-10, RFI-01 tag conflict); verify via fab drawing.
- Hydraulic runs (SHELL-CLOSED-V2, SHELL-OPEN-V2, SHELL-PSV-V2, SHELL-ISO-CLOSED/OPEN, QW-BASE-CAL/QW-SWITCH) are single-phase water topology screening only; absolute gpm/fps/psi not propane relief rates; EPANET heads datum **ASSUMPTION**.
- Bubble 19.19 bar (54.44C) ->34.96 bar (85C) ->35.67 bar (86.11C) absolute uses 95/5 mole **ASSUMPTION**, C4s omitted, mol vs wt unspecified (p.9); fluid_properties screening only.
- Costs: catalogue $14k WITHDRAWN; analysis $100k-$1M and <$100k are order-of-magnitude judgements, no detailed estimate. Standards: quoted Ten States PASS results NOT applicable to refinery overpressure protection.


---
## Document control

**Units:** US customary (gpm, mgd, ft, in, psi, hp). **Elevations:** feet, datum as shown on the source drawings (not re-surveyed).
**Prepared by:** AI agent (muse-spark-1.3-contributor), 2026-10-28. **Run:** williams_geismar · 38 agent steps · 15 simulator runs.
**Checked by:** __________________  **Approved (PE, seal):** __________________  
_Draft for engineering review. Not for construction. Simulator results are screening-level unless stated otherwise._

### Scenario register

| Run | Model | Pumps | Flow (mgd) | Purpose |
|---|---|---|---|---|
| QW-BASE | EPANET steady state | QW-P1 | 5.378 | Calibrated base: A fouled in service, B tube standby closed, B shell b |
| QW-BASE-CAL | EPANET steady state | QW-P1 | 5.221 | Calibrated base for screening: A fouled in service (C80), B tubes clos |
| QW-SWITCH | EPANET steady state | QW-P1 | 7.709 | Event: B tubes opened at 08:33 while B shell gates closed (blocked she |
| QW-FOULED-VS-CLEAN | EPANET steady state | QW-P1 | 0.0 | Check fouled A (C80) vs standby B (C120) hydraulic signature when both |
| SHELL-ISO-CLOSED | EPANET steady state |  | 0.0 | Existing: B shell gates closed - no path from blocked shell to fractio |
| SHELL-ISO-OPEN | EPANET steady state |  | 0.0 | Fixed: B shell gates car-sealed open - shell communicates with fractio |
| SHELL-PSV-DED | EPANET steady state |  | 0.0 | Alt OPT-1: dedicated thermal PSV path from B shell to flare that stays |
| SHELL-CLOSED-V2 | EPANET steady state |  | 0.0 | Topology screening: 2001 gates closed isolate B shell - zero flow prov |
| SHELL-OPEN-V2 | EPANET steady state |  | 0.0 | Topology screening: 2001 gates open restores continuity to fractionato |
| SHELL-PSV-V2 | EPANET steady state |  | 0.0 | Topology screening: dedicated PSV branch stays open when 2001 gates cl |
| bubble1 | process simulation (DWSIM) | - | - | DWSIM bubble pressure |
| props2 | process simulation (DWSIM) | - | - | DWSIM fluid properties |
| bubble3 | process simulation (DWSIM) | - | - | DWSIM bubble pressure |
| bubble4 | process simulation (DWSIM) | - | - | DWSIM bubble pressure |
| props5 | process simulation (DWSIM) | - | - | DWSIM fluid properties |

### Revision log

| Rev | Date | Description | By |
|---|---|---|---|
| A | 2026-10-28 | Initial agent draft | AI agent |
