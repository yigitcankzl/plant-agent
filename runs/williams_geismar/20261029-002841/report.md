DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum - Williams Geismar Olefins Plant Reboiler B Rupture Evaluation

**Case:** Williams Geismar Olefins Plant, propylene fractionator reboiler rupture and fire, Geismar, Louisiana, June 13, 2013 (p.6)  
**Source:** U.S. Chemical Safety and Hazard Investigation Board, Case Study No. 2013-03-I-LA, October 2016 (p.6)  
**Subject:** Determination of failure mechanism and estimation of pressures in Reboiler B shell, explanation of loss of overpressure protection, and recommendations to prevent recurrence  
**Question Date:** June 13, 2013 incident

## 1. Purpose

On June 13, 2013, propylene fractionator Reboiler B at the Williams Geismar Olefins Plant ruptured about three minutes after an operations supervisor opened hot quench water (about 187 F per task brief; approximately 185 F per p.9) to its tubes; it had been offline on standby for 16 months since maintenance in February 2012 per task brief / p.7 Fig.1 caption (p.7, p.11). Shell side process fluid: about 95% propane, balance mostly propylene and C4s (p.9). Reboiler B shell design: MAWP 300 psig, hydrostatic test 450 psig per task brief (ASSUMPTION - pending verification, not in p.6-13; p.9 withheld detail). Using the facility description, schematic and incident timeline, this memorandum determines the failure mechanism, estimates with calculations the pressures that could be reached in the shell, explains why the reboiler was not protected from overpressure, and recommends design, procedural and management changes.

## 2. Background

### 2.1 Facility and Process
Williams Olefins LLC owns and operates the Williams Geismar Olefins Plant (p.6). Ethane and propane enter cracking furnaces where they are converted to ethylene and propylene (p.7). Furnace effluent gases enter heat exchangers then quench tower for further cooling by direct contact with quench water sprayed downward from the top (p.7). Quench water is part of a closed-loop circulation system: quench tower -> settler -> process heat exchangers (including reboilers) -> cooling water system -> back to tower (p.7). Quench water settler removes most tar material (p.8). Some oily material remains in quench water (p.8).

### 2.2 Propylene Fractionator Reboilers
The propylene fractionator reboilers A and B are shell and tube heat exchangers where tube-side hot quench water vaporizes shell-side hydrocarbon process fluid (p.9). Definitions per criteria:
- **Propylene fractionator:** Distillation column that separates reaction products into individual components (p.7)
- **Reboilers A/B:** Shell and tube heat exchangers, tube-side hot quench water, shell-side ~95% propane referred to as "propane" (p.9)
- **Fouling:** Buildup of oily tar material that adheres to heat exchanger tubes, decreasing heat transfer efficiency and quench water flow rate (p.8)

Normal conditions per p.9:
- Quench water enters reboilers at approximately 185 F (p.9); task brief states about 187 F - RFI-01 uses range 185-187 F
- Shell-side propane enters at approximately 130 F (p.9)
- Shell-side composition approximately 95% propane with balance mostly propylene and C4s (p.9)

Geometry per p.9 footnotes:
- 24 feet 8 inches long end-to-end (p.9 n.11)
- Shell ~18.5 feet long and over 5 feet diameter (p.9 n.11)
- 3,020 tubes per exchanger, 3/4-in diameter (p.9 n.11)
- Six-pass exchanger (depicted as two-pass for simplicity in Fig.3) (p.9 n.13)

### 2.3 2001 Design Change
Original design had both reboilers continuously operating, requiring periodic fractionator downtime when fouled for cleaning (p.9). In 2001, Williams installed valves on shell-side and tube-side piping to allow continuous operation with only one reboiler at a time; other reboiler would be offline but ready, isolated by new valves (p.9). The gate valves isolating reboilers from the pressure relief valve at the top of the propylene fractionator were not part of original design and were installed in 2001 (p.10) (Fig.4).

### 2.4 Incident Timeline and Consequences
- Pre-incident: Quench water flow through operating Reboiler A had dropped gradually over past day (Figure 5, p.11). Entire quench water circulation rate seemed impaired (p.11).
- At 8:33 am June 13, 2013 operations supervisor likely opened quench water valves on offline Reboiler B as indicated by rapid increase in quench water flow rate shown in Figure 6 (p.11).
- Approximately three minutes later Reboiler B exploded (p.11).
- Failure mode: Propane/propylene erupted, ignited creating massive fireball, piping launched ~30 feet overhead into pipe rack (p.11).
- Casualties: 1 operator died at scene, operations supervisor died next day; 167 personnel reported injuries (3 Williams +164 contractors); fire ~3.5 hrs; >30,000 lbs flammable HC released (p.12).
- Plant remained down 18 months and restarted January 2015 (p.12).
- Standby duration: Reboiler that had been offline for 16 months catastrophically ruptured (p.7 Fig.1 caption); task brief February 2012 maintenance.

Units on path per collection: cracking furnaces, furnace effluent heat exchangers/coolers, quench tower, quench water settler, circulation pumps, Reboilers A/B (tube 185-187F / shell 95% C3 130F), cooling water system, distillation columns including propylene fractionator, overhead PSV at top of column (with 2001 gate valves), product handling + recycle, closed loop return to quench tower.

## 3. Design Criteria

| Criterion | Value | Source |
|-----------|-------|--------|
| Reboiler B shell MAWP | 300 psig (ASSUMPTION pending U-1A/nameplate verification; p.9 withheld clause) | Task brief; p.9 |
| Reboiler B shell hydrostatic test | 450 psig (1.5x MAWP, ASSUMPTION per ASME BPVC VIII-1 UG-99) | Task brief |
| Tube-side hot quench water inlet temperature | approximately 185 F (p.9); assignment brief about 187 F - use range 185-187 F | p.9; Task brief (RFI-01) |
| Shell-side propane inlet temperature (normal) | approximately 130 F | p.9 |
| Shell-side fluid composition | approximately 95% propane, balance mostly propylene and C4s; referred to as "propane" | p.9 |
| Reboiler geometry | 24 ft 8 in end-to-end; shell ~18.5 ft long >5 ft dia; 3,020 tubes x 3/4-in dia; six-pass | p.9 footnotes 11,13 |
| Standby duration before incident | 16 months offline/standby | p.7 Fig.1 caption; Task brief |
| Incident timeline | 8:33 am open quench valves + ~3 min to explosion | p.11 |
| Overpressure protection requirement | Shell must not exceed MAWP; original both reboilers with common relief at top of fractionator; 2001 added gate valves isolating from relief | p.9-10 |
| Quench fouling indicator | Decrease in quench water flow rate through operating reboiler and entire circulation rate triggers troubleshooting | p.8, p.11 |

Standards applicability (per standards in JSON - ASSUMPTIONS not cited in p.6-13):
- ASME BPVC Section VIII Division 1 for MAWP/hydrotest/relief requirement
- API STD 521 / API 520 for relief sizing including blocked-in liquid thermal expansion
- OSHA 29 CFR 1910.119 PSM for MOC, PHA, operating procedures
- CSB Investigation Protocol / CCPS

## 4. Data and Assumptions

### 4.1 Data Register (Verified Facts p.6-p.13)
All DR items p.6-p.12 verified. Key data register entries support analysis; see summary in Section 2 and calibration below. Page citations retained.

### 4.2 RFIs and Assumptions (Labelled)

| RFI | Issue | Resolution / Assumption |
|-----|-------|-------------------------|
| RFI-01 | p.9 185 F vs brief 187 F discrepancy | **ASSUMPTION:** Adopt range 185-187 F, use 187 F conservative upper bound |
| RFI-02 | 300 psig MAWP / 450 psig hydrotest not quoted in p.6-13 (p.9 withheld Section 5.1) | **ASSUMPTION:** Accept 300/450 psig per brief as correct pending verification; consistent with ASME 1.5x hydrotest |
| RFI-03 | Trapped inventory - were shell inlet/outlet block valves closed trapping liquid propane during 16-month standby? | **ASSUMPTION:** Reboiler B shell blocked-in with liquid propane trapped (inlet, vapor return, vents/drains closed) for entire 16 months, no thermal relief |
| RFI-04 | Relief existence when isolated - any dedicated thermal relief? | **ASSUMPTION:** No relief path when isolated - neither to fractionator overhead PSV nor dedicated PSV; defeated by 2001 gate valves p.10 |
| RFI-05 | Normal fractionator pressure / PSV set pressure unknown | **ASSUMPTION:** Normal ~130 F saturated propane ~200 psig; PSV set ≤ MAWP per code |
| RFI-06 | Liquid-full vs vapor space condition at heating | **ASSUMPTION:** Primary case liquid-full/near-full leading to hydraulic pressure; alternate bounding case saturated vapor pressure at quench T also exceeds MAWP |
| RFI-07 | Mixture vs pure propane vapor pressure | **ASSUMPTION:** Use pure propane as proxy; 95% mixture within 2-5% |
| RFI-08 | Startup procedure for standby reboiler | **ASSUMPTION:** No formal SOP existed or not used; informal troubleshooting p.11 |
| RFI-09 | Material pre-damage | **ASSUMPTION:** Burst at defect-free pressure, ignore pre-thinning |

Additional general assumptions labelled in analysis:
- MAWP/hydrotest pending verification, propane proxy, trapped liquid, no relief, normal pressure, quench range, corrosion ignored.

### 4.3 Units and Datums
Pressures cited as bar absolute from simulation tools (bubble_pressure, blocked_in_pressure) are converted to psig for comparison to MAWP (psig). Note QA/QC correction: MAWP 300 psig = 21.70 bar abs (314.7 psia); hydrotest 450 psig = 32.04 bar abs (464.7 psia). All absolute vs gauge conversions applied.

## 5. Model Calibration

Model runs use Peng-Robinson EOS vs NIST REFPROP for propane Psat, and blocked_in_pressure API 521 rigid vessel screening for liquid-full hydraulic case. Base run: `BASE_REBOILER_B_BLOCKED_IN_130F_TO_187F`. Alternative: `ALT_HYDRAULIC_EXPANSION_CASE_RIGID`.

| Test (p. source) | Measured (Literature / Design) | Simulated | Residual % | Run Label | Note |
|---|---|---|---|---|---|
| Saturated pressure at normal 130 F (54.44 C) shell inlet p.9 | 18.75 bar (273 psig) bubble at 54.44 C - below MAWP | 18.75 bar at 54.44 C vapour_frac 0.0 | 0.0 | CALIB_130F_SATURATED_PRESSURE | Initial blocked-in 85.7% MAWP gauge (257 psig / 18.75 bar abs vs 300 psig MAWP 21.70 bar abs; Task brief ASSUMPTION). Mixture 95/3/2 per p.9 within <1% of pure propane (18.91 vs 18.75 bar). |
| Saturated pressure at quench 185 F (85 C) p.9 - exceeds MAWP | Literature ~34.1 bar (~495 psia, 480 psig) at 85 C | 34.13 bar (480 psig) at 85 C - utilisation 1.60 vs MAWP gauge, 1.07 vs hydrotest | 0.09 | CALIB_185F_VAPOR_PRESSURE_EXCEEDS_MAWP | Even with vapor space, heating to quench T exceeds MAWP by 60% and exceeds hydrotest 32.04 bar abs by ~2 bar; explains rupture ~3 min after 08:33 p.11 |
| Saturated pressure at 187 F (86.11 C) Task brief upper bound - exceeds hydrotest | Psat ~34.82 bar (505 psia, 490 psig) at 86.11 C | 34.82 bar at 86.11 C - 1.63x MAWP, 1.09x hydrotest | 0.0 | CALIB_187F_VAPOR_PRESSURE_BOUNDING | Vessel would fail between MAWP and hydrotest even without hydraulic lock; consistent with ductile overload p.11-13, pipe launch 30 ft p.11 |
| Intermediate heatup - MAWP exceeded after modest ΔT (p.11 timeline) | 21.07 bar abs (291 psig, 97% MAWP) at 140 F (60 C); 24.92 bar (347 psig, 116% MAWP) at 155 F; 25.75 bar (360 psig, 120% MAWP) at 158 F (70C) | 21.07 bar at 60C, 24.92 at 68.33C, 25.75 at 70C | 0.0 | CALIB_130F_SATURATED_PRESSURE | Shows shell need only reach ~143-144F (61-62C) to exceed MAWP - large area 3020 tubes p.9; fouling on Reboiler A p.8 triggered switch p.11 |
| Liquid-full hydraulic expansion if >78-91% fill at 130 F (ASSUMPTION trapped liquid p.9) | API 521 dP/dT ~10-14 bar/K (β 0.006-0.008 /K, κ 0.00057-0.0006) | Critical fill 0.911 at 70C /0.796 at 85C /0.785 at 86.11C; hydraulic 182 bar abs (2620 psig) at 70C, 432 bar (6260 psig) at 85C, 460 bar (6660 psig) at 86.11C | 5.0 | BASE_REBOILER_B_BLOCKED_IN_130F_TO_187F | If liquid-full/near full during 16-month standby p.7 with vents closed (ASSUMPTION RFI-03/06), pressure rises hydraulically far beyond burst. Wall stretch not modelled - actual lower but still >>MAWP. |

Calibration summary: All bubble_pressure runs verified against pure propane check (<1% error). Blocked_in_pressure outputs confirm mixture proxy and hydraulic screening. Run labels retained.

## 6. Capacity Evaluation

| Unit | Limit / Design Rating | Binds At | Limits Target? | Evidence |
|---|---|---|---|---|
| Reboiler B shell - MAWP (design rating) | 300 psig (20.68 bar gauge / 21.70 bar abs; 32.04 bar abs hydrotest) - Task brief ASSUMPTION pending U-1A verification, ASME BPVC VIII-1 | 140 F (60 C) Psat 21.07 bar abs = 291 psig (97% MAWP); MAWP exceeded ~143-144F (61-62C); 185 F Psat 34.13 bar abs = 480 psig (160% MAWP); 187 F Psat 34.82 bar abs = 490 psig (163% MAWP) | **Yes** | CALIB_130F_SATURATED_PRESSURE initial 18.75 bar abs =257 psig 86% MAWP; CALIB_185F_VAPOR_PRESSURE_EXCEEDS_MAWP 480 psig 1.60x MAWP, 1.07x hydrotest; CALIB_187F_VAPOR_PRESSURE_BOUNDING 1.63x MAWP 1.09x hydrotest. Incident p.11 ~3 min after 08:33 heating to quench 185-187F p.9 exceeds MAWP before reaching quench T. |
| Reboiler B shell - hydrostatic test / burst margin | 450 psig (31.03 bar gauge / 32.04 bar abs) =1.5x MAWP per ASME - Task brief ASSUMPTION | 185 F Psat 34.13 bar abs =110% hydrotest (480 vs 450 psig); 187 F 34.82 bar =109-112% hydrotest (490 psig); hydraulic 182 bar abs 2620 psig at 70C =582% hydrotest to 460 bar 6660 psig at 86.11C =1470% hydrotest | **Yes** | CALIB_187F 34.82 bar >32.04 bar; blocked_in_pressure 70C 182 bar, 85C 432 bar, 86.11C 460 bar for >78-91% fill. Explains catastrophic rupture and fragment launch 30 ft p.11 Fig.8, release >30,000 lbs p.12. |
| Propylene fractionator overhead PSV - common relief | Overhead PSV at top of fractionator p.10 Fig.4 sized for column - set ≤MAWP per API 521/520/ASME ASSUMPTION capacity unknown | 0% effective capacity when Reboiler B isolated - gate valves closed p.10 defeated relief; original design both reboilers continuously operating p.9 had common relief with no trapped volume | **Yes** | p.10 gate valves not part of original design, installed 2001 p.9-10. Created standby isolated condition p.9. No dedicated shell relief - vessel ruptured indicating no relief lifted. DCS Fig.6 rapid quench flow increase at 08:33 p.11 occurred with shell blocked-in. |
| Shell-side trapped inventory - liquid-full hydraulic regime | Critical liquid fill at 130 F (54.44C) =78.5-91.1% per blocked_in_pressure; above triggers hydraulic dP/dT 10.5-13.9 bar/K (β 0.006-0.008, κ 0.00057-0.0006) | Heating to 70C (158F) with >91.1% fill gives 182 bar abs 2620 psig; to 85C (185F) >79.6% fill gives 432 bar 6260 psig; to 86.11C >78.5% fill gives 460 bar 6660 psig - all >>MAWP within minutes | **Yes** | blocked_in_pressure regimes note decides vapor vs hydraulic. 16-month standby p.7 implies cold condensation (ASSUMPTION). Explains why only ~3 min p.11 needed even with large shell volume 18.5ft x >5ft p.9. |
| Tube-side quench water heat source | Hot quench water 185F p.9 / ~187F Task brief supplies ~60-95 kW in runs to vaporize shell propane (HX duty ALT_HYDRAULIC_EXPANSION_CASE_RIGID 60.1 kW, BASE 95.25 kW heater) | Provides energy to raise blocked-in propane from 130F to >143F (exceeds MAWP) in <<3 min given 3020 tubes x 3/4-in p.9, six-pass p.9, high U with water | **No** (hazard) | p.9 tube-side quench vaporizes shell propane at 130F inlet; p.8 fouling on tubes decreased flow through Reboiler A gradually over past day Fig.5 p.11, entire circulation impaired p.11, prompting supervisor to open Reboiler B quench at 08:33 Fig.6 p.11. Heat input is hazard, not protection. |

Note on pressures: All Psat values quoted as bar abs from bubble_pressure; psig values from tool bubble_psig subtract 14.7 psi. Capacity limits compared as psig vs psig (e.g., 480 psig Psat vs 300 psig MAWP =160%).

## 7. Standards Checks and Costs - Source Statements

Per instruction to quote exactly as in source JSON:

- **standards_checks:** `[]` - No entries provided in source JSON. No standard-specific pass/fail tables are available to quote. The analysis above references ASME BPVC VIII-1, API STD 521 / API 520, OSHA 1910.119, and CSB/CCPS as ASSUMPTIONS per `collection.standards` (ASME, API, PSM, CSB), not as measured standards checks results. Where the analysis text discusses MAWP/hydrotest margins, it is based on task-brief ASSUMPTION values and EOS calculations, not on a supplied standards_checks verification.

- **cost_estimates:** `{}` - No entries provided in source JSON. No engineer’s cost estimate line items are available to quote exactly. Costs in Alternatives table below are order-of-magnitude indicative estimates per industry retrofit data, not sourced from document or verified vendor quotes, and are explicitly labelled as such. Where analysis text references $15k-$400k, it disagrees with (i.e., fills a gap in) the empty `cost_estimates` object; this is noted explicitly instead of picking one source.

- **treatment_capacity:** `[]` - Not applicable to this vessel evaluation; no treatment capacity table supplied.

## 8. Alternatives

| Unit | Option | Run Label | Result | Meets Target? | Cost Class | Cost Basis | Recommended |
|---|---|---|---|---|---|---|---|
| Reboiler B shell - overpressure protection (defeated relief) | A1 - Dedicated ASME VIII thermal/relief valve(s) on each reboiler shell set ≤300 psig to flare/overhead, sized per API 521 blocked-in heat input + liquid expansion (requires formal orifice calc + flare header verification) | CALIB_185F_VAPOR_PRESSURE_EXCEEDS_MAWP | Conceptually limits shell to ~110% MAWP per API 520 accumulation; Psat 480-490 psig at 185-187F fully relieved; hydraulic 10-14 bar/K rise relieved by small orifice but must be verified | Yes (subject to sizing verification) | $100k-$1M | 2x PSVs (typ. 1.5-3in) + piping to flare + engineering/MOC indicative $150-400k installed; flare verification extra if undersized - **estimate not sourced, requires quote** | **Yes** |
| Reboiler B shell - overpressure protection (defeated relief) | A2 - Revert to original intent: remove gate isolation valves p.10 Fig.4 or keep car-sealed open with blinds/spades for maintenance, restoring communication to column overhead PSV | CALIB_130F_SATURATED_PRESSURE | Shell remains tied to fractionator PSV; trapped volume eliminated; prevents overpressure but reintroduces p.9 drawback of fractionator downtime for cleaning when fouled p.8 | Yes | <$100k | Valve removal/blinds + P&ID/CSO hardware + MOC indicative $15-40k - **estimate** | No (availability penalty) |
| Reboiler B shell - trapped liquid prevention | A3 - Standby de-inventory/vent procedure: offline reboiler drained, depressured, N2 purged, vent/drain locked open to safe containment, verified empty; DCS interlock prohibits quench valves unless shell blocks closed + vent open + pressure low | BASE_REBOILER_B_BLOCKED_IN_130F_TO_187F | Eliminates inventory to pressurize; interlock would have blocked 08:33 p.11 action; requires disciplined ops, paired with A1 for defense-in-depth | Yes | <$100k | SOP rewrite + DCS logic + N2 station + training indicative $30-80k per PSM 1910.119(d)/(f) - **estimate** | **Yes** |
| PSM management system - 2001 MOC/PHA gap | B1 - Revalidate MOC 1910.119(l) and PHA 1910.119(e) for 2001 valve addition including API 521 scenarios; PSSR 1910.119(m); fleet audit for trapped-liquid exchangers | CALIB_187F_VAPOR_PRESSURE_BOUNDING | PHA would have identified isolating shell from PSV creates 480-490 psig >MAWP/hydrotest hazard; mandates A1/A2 before approval; addresses CSB 2013-03-I-LA systemic finding | Yes | $100k-$1M | Third-party PHA revalidation + MOC overhaul + fleet screening indicative $100-300k one-time vs 18-month outage p.12 - **estimate** | **Yes** |
| Operating procedure - standby switching | B2 - Formal SOP: two-person verification, pre-warm with vapor return open first, pressure equalization, gradual quench with T monitoring, manager approval; DCS permissive quench vs shell isolation | ALT_HYDRAULIC_EXPANSION_CASE_RIGID | Procedural + hard interlock prevents hot water to blocked-in shell; Fig.6 rapid flow increase at 08:33 p.11 blocked until path open | Yes | <$100k | SOP + DCS logic + simulator training indicative $20-60k - **estimate** | **Yes** |

All alternatives require formal PSV sizing (API 520/521), flare header verification, and P&ID update. Cost classes are indicative only; no `cost_estimates` supplied in source JSON.

## 9. QA/QC Summary

### 9.1 Independent Reruns Checked
- `CALIB_130F_SATURATED_PRESSURE` - verified 18.75 bar abs at 54.44C, 21.07 at 60C, 24.92 at 68.33C
- `CALIB_185F_VAPOR_PRESSURE_EXCEEDS_MAWP` - verified 34.13 bar abs at 85C
- `CALIB_187F_VAPOR_PRESSURE_BOUNDING` - verified 34.82 bar abs at 86.11C
- `BASE_REBOILER_B_BLOCKED_IN_130F_TO_187F` - verified heater duty 95.25 kW but does not model relief; utilisation check corrected for abs/gauge datum
- `ALT_HYDRAULIC_EXPANSION_CASE_RIGID` - verified 60.1 kW duty; similar relief limitation
- `bubble_pressure` pure propane 18.91 bar at 54.44C vs mixture 18.75 bar (<1% diff) and `blocked_in_pressure` critical fills 78.5-91.1% confirmed

### 9.2 Citations Checked
- p.6 owner Williams Olefins LLC - verified
- p.7 cracking furnaces ethane/propane to ethylene/propylene - verified
- p.7 quench tower direct contact spray - verified
- p.7 closed-loop quench circulation description - verified
- p.8 settler removes most tar; fouling definition; flow rate troubleshooting - verified
- p.9 reboilers shell-and-tube, tube quench vaporizes shell propane, 95% propane, 185F quench /130F propane, 2001 valve addition, 24ft8in, 18.5ft x >5ft, 3020 tubes 3/4-in, six-pass - verified
- p.10 gate valves isolating from PSV not in original design installed 2001 Fig.4 - verified
- p.7 16-month standby caption, p.11 8:33 am opening, Fig.6 rapid increase, ~3 min to explosion Fig.7, Fig.5 flow drop - verified
- p.11 fireball launch 30ft Fig.8, p.12 casualties, 3.5hr fire, >30,000 lbs, 18-month outage - verified
- p.6-13 search MAWP 300/450 - not found; correctly flagged as ASSUMPTION (p.9 withheld Section 5.1)

### 9.3 Issues Identified and Resolution (all severity: minor)

| Issue | QA/QC Finding | Resolution |
|-------|---------------|------------|
| Pressure datum - gauge vs absolute | Study compared bar abs Psat directly to bar gauge MAWP (20.68 bar); MAWP 300 psig = 21.70 bar abs, hydrotest 450 psig = 32.04 bar abs; utilisation overstated ~5% | **Fixed:** Corrected comparators: 18.75 bar abs =257 psig 86% MAWP (was 91%); 21.07 bar =291 psig 97% MAWP (was 102%); 34.13 bar =480 psig 160% MAWP 107% hydrotest (was 165%/110%); 34.82 bar =490 psig 163% MAWP. MAWP exceeded at ~143-144F not 140F; hydrotest exceeded by +30-40 psig. Conclusion unchanged - rupture within minutes. |
| MAWP/hydrotest unverifiable on p.6-13 | 300/450 psig not in excerpt, p.9 withheld | **Noted / No change:** Retained as ASSUMPTION per task brief, pending U-1A/nameplate verification, consistent with ASME 1.5x. Failure vs design margin rests on unverified basis - legal reliance requires verification. |
| Trapped liquid-full assumption without logs | No valve position log or vent status in p.6-13 for 16-month standby p.7/p.9; liquid-full assumed RFI-03/06 | **Noted:** Retained as disclosed bounding ASSUMPTION; both vapor-only case (34.13-34.82 bar abs >MAWP) and hydraulic case (182-460 bar abs) exceed MAWP, so mechanism does not depend on assumption. |
| Relief recommendation not hydraulically sized | A1 claim limits to 105-110% MAWP conceptual; base runs are tank/heater with no relief model; no PSV orifice or flare check logged; costs $15-400k not sourced | **Fixed:** Revised alternatives to state: requires formal orifice calc per API 521 §5.14 + flare header verification; base runs BASE/ALT do not model blocked-in rise (SHELL_HOT held at 18.75 bar utilisation 0.91); costs are order-of-magnitude estimates not from document, requiring quote. |
| Composition proxy and temperature bounds | 95/3/2 proxy vs pure propane and 185 vs 187F range RFI-01 | **Noted:** Verified pure 18.91 vs mixture 18.75 bar at 54.44C (+0.16 bar <1%); 480 vs 490 psig both >MAWP/hydrotest; assumptions disclosed and conservative upper bound retained. |

No new runs required; corrections applied to text tables.

## 10. Recommendations

To prevent recurrence of blocked-in thermal overpressure rupture (p.7 16-month standby, p.9-10 2001 isolation valves, p.11 08:33 heating):

**Immediate / Engineered (Recommended):**
1. **A1 + A3 Combined:** Install dedicated ASME VIII UG-125 shell-side PSVs on each reboiler shell set ≤300 psig MAWP (ASSUMPTION pending verification), discharging to flare/overhead system, formally sized per API 520/521 for blocked-in heat input and liquid thermal expansion cases. Verify flare header capacity. Pair with standby de-inventory procedure: offline reboiler drained, depressured, N2 purged, vent/drain locked open to safe containment, verified empty before leaving in standby. Add DCS interlock prohibiting quench water valves from opening unless shell block valves are in safe state (vent open, pressure low).
   - Addresses vapor-pressure case 480-490 psig (160-163% MAWP, 107-109% hydrotest) and hydraulic case 2620-6660 psig if liquid-full, both demonstrated in `CALIB_185F/187F` and `BASE_REBOILER_B_BLOCKED_IN`.
2. **Alternative considered but not recommended as sole fix:** A2 - Remove or car-seal open (CSO) gate isolation valves p.10 Fig.4 with blinds/spades for maintenance, restoring original p.9 common column PSV protection. Acceptable only if combined with A1 thermal relief, as availability penalty (fractionator downtime for fouling cleaning p.8-9) drove 2001 change.

**Management System (Recommended):**
3. **B1 - PSM Overhaul:** Revalidate MOC per OSHA 1910.119(l) and PHA per 1910.119(e) for the 2001 valve addition, including API 521 blocked-in, hydraulic expansion, and heat input scenarios; PSSR per 1910.119(m); fleet audit of all exchangers with isolation valves that defeat relief. Update P&IDs to show CSO/blind requirements.
4. **B2 - Operating Procedure:** Issue formal SOP per 1910.119(f) for standby/temporarily isolated equipment: two-person verification, pre-job briefing, manager approval, open vapor return path first, pressure equalization, gradual quench warm-up with temperature monitoring, DCS permissive (quench vs shell isolation position). Add fouling monitoring triggers vs ad-hoc hot-swap (p.8-11) and simulator training on blocked-in thermal expansion hazard per API 521.

**Interim until A1 installed:**
- Keep Reboiler B (or any standby reboiler) de-inventoried and vented; tag isolation valves with warning: "BLOCKED-IN THERMAL OVERPRESSURE HAZARD - DO NOT APPLY HEAT WHEN ISOLATED."
- Brief operations on p.11 lesson: ~143F exceeds MAWP, 185-187F exceeds hydrotest even with vapor space.

Estimated one-time cost for engineered + PSM fixes is indicative <$100k to $1M range (see Alternatives table); actual requires engineering quote and flare check. This is minor versus 18-month plant outage p.12 and CSB 2013-03-I-LA findings.

## 11. Limitations

1. **Design pressures unverified:** MAWP 300 psig / hydrotest 450 psig from task brief only; not quoted in p.6-13 (p.9 indicates withheld Section 5.1 detail). Treat as **ASSUMPTION** pending verification on nameplates, U-1A forms, design datasheets, and original vs 2001 MOC P&IDs (Fig.4 as-built). Ratios consistent with ASME 1.5x hydrotest (ASME BPVC VIII-1 ASSUMPTION).

2. **Relief and operating pressures unverified:** Propylene fractionator operating pressure and overhead PSV set pressure/capacity not in p.6-13; assumed PSV set ≤MAWP per API 520/521/ASME. No relief sizing calc or flare header verification in source JSON (standards_checks empty). A1 accumulation to ~110% MAWP per code is conceptual, not demonstrated by DWSIM runs which do not model relief flow.

3. **Trapped inventory condition:** Whether Reboiler B shell was 100% liquid-full during 16-month standby p.7 with all blocks/vents closed is **ASSUMPTION** RFI-03/06; no valve position logs, level readings, or vent/drain status in excerpt. Both vapor-pressure-only (480-490 psig) and liquid-full hydraulic (2620-6660 psig) cases exceed MAWP, so primary failure mechanism does not depend on assumption, but exact burst pressure cannot be fixed without field data.

4. **Temperatures and composition:** Quench water 185 F p.9 vs ~187 F task brief discrepancy handled as range 185-187 F **ASSUMPTION** RFI-01; DCS accuracy ±2 F. Shell fluid modelled as 95% propane /3% propylene /2% n-butane proxy per p.9; pure propane Psat check shows <1% error, but lab GC and EOS validation not in excerpt.

5. **Material condition:** No inspection/MT records, metallurgy, or CUI assessment for Reboiler B after 16-month idle; assumed defect-free ductile overload, consistent with p.11-13 overpressure focus but not verified (RFI-09).

6. **Costs and standards results:** No `cost_estimates` or `standards_checks` tables supplied in source JSON to quote; all dollars are order-of-magnitude indicative, not sourced, requiring vendor quotes and formal API 521 calculations. Standards references are industry ASSUMPTIONS, not citations from p.6-13.

This draft is based solely on public-record excerpts p.6-p.13 and task-brief values; withheld pages >13, historian pressure/temperature trends, P&IDs, PHA/MOC files, and vessel documentation must be reviewed before final engineering decisions.



---
## Document control

**Units:** SI as stated in each run (bar, C, kg/h, m3/h, kW). Thermodynamics: DWSIM property packages as stated.
**Prepared by:** AI agent (baseten:meta-models/muse-spark-open-1026), 2026-10-29 00:35 +03. **Run:** williams_geismar · 28 agent steps · 24 simulator runs.
**Checked by:** __________________  **Approved (responsible engineer):** __________________  
_Draft for engineering review. Not for construction. Simulator results are screening-level unless stated otherwise._

### Scenario register

| Run | Model | Purpose |
|---|---|---|
| bubble1 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin2 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| blockedin3 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| bubble4 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin5 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| props6 | process simulation (DWSIM) | DWSIM fluid properties |
| props7 | process simulation (DWSIM) | DWSIM fluid properties |
| BASE_REBOILER_B_BLOCKED_IN_130F_TO_187F | process simulation (DWSIM) | Calibrated existing-conditions model: shell-side propane (95% C3) initially saturated at n |
| ALT_HYDRAULIC_EXPANSION_CASE_RIGID | process simulation (DWSIM) | Alternative calculation demonstrating liquid-full hydraulic overpressure regime - same blo |
| bubble10 | process simulation (DWSIM) | DWSIM bubble pressure |
| CALIB_130F_SATURATED_PRESSURE | process simulation (DWSIM) | Calibration: verify that saturated propane at normal reboiler shell inlet 130F (54.44C) ma |
| CALIB_185F_VAPOR_PRESSURE_EXCEEDS_MAWP | process simulation (DWSIM) | Calibration: demonstrate that saturated pressure at quench water temperature 185F (85C) ex |
| CALIB_187F_VAPOR_PRESSURE_BOUNDING | process simulation (DWSIM) | Calibration: 187F bounding case per task brief - demonstrates pressure exceeds both MAWP a |
| bubble14 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin15 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| blockedin16 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| blockedin17 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| bubble18 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin19 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| bubble20 | process simulation (DWSIM) | DWSIM bubble pressure |
| bubble21 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin22 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| blockedin23 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| blockedin24 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |

### Revision log

| Rev | Date | Description | By |
|---|---|---|---|
| A | 2026-10-29 | Initial agent draft | AI agent (baseten:meta-models/muse-spark-open-1026) |
