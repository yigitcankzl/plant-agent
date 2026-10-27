DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum – CSB Pascagoula (csb_pascagoula) – A-Train BAHX Rupture, June 27, 2016

## Purpose

Identify the most likely initial failure point among 12-13 A-Train breaches using DCS/event log/surveillance/physical evidence sequence (p.60-p.62) (p.21); explain sudden rupture on June 27, 2016 during curtailment/shut-in (p.13) (p.61); determine damage mechanism from BAHX history, lab examination and Table 1 elimination (p.15-p.16) (p.22) (p.31-p.34); and recommend operation, monitoring, repair practice, mechanical integrity / risk assessment changes to prevent repeat.

Investigation objectives per criteria:

- Initial failure point (p.21) (p.60-p.62)
- Damage mechanism – thermal fatigue / thermal shock vs other mechanisms (p.15-p.16) (p.22) (p.31-p.34)

## Background

- Facility: Enterprise Products Pascagoula Gas Plant, brazed aluminum heat exchanger (BAHX) rupture, fires and explosions, Pascagoula, Mississippi, June 27, 2016. Source: U.S. Chemical Safety and Hazard Investigation Board, Report No. 2016-02-I-MS, 2019 (public record).
- Staffing and build: employs 30 people. Built in 1998/1999 (p.12).
- Ownership: Amoco Production Company (60 percent) and Shell Midstream Enterprises Inc. (40 percent) as original partners. In 1998, BP acquired Amoco, and in mid-1999, Enterprise Products Partners LP acquired Shell's interest, but BP maintained operation (p.12). Value: BP operator until March 2016 Enterprise full acquisition per data register.
- Design capacity: design capacity of 1.5 billion cubic feet per day of raw gas and up to 50,000 barrels per day (bpd) of NGLs (p.58).
- Throughput at incident: throughput was approximately 500 million standard cubic feet per day of raw gas and 16,000-18,000 bpd of NGLs (p.58).
- Operating context: production of natural gas liquids due to pipeline problems downstream... operators initiated necessary steps from control room, when, at 11:22 p.m., a sudden explosion and fire occurred. No abnormal alarms (p.13). Value: Curtailment then shut-in of NGL production on A-Train; sudden explosion 11:22 p.m. with no warning alarms.
- Escalation: intensified several times over approximately the next 35 minutes (p.14). Value: ~35 minutes of intensification.
- Process path (units on path):
  - Offshore Destin raw-gas pipeline inlet; Slug catcher; Dehydrator + dust collector; Warm separator; Demethanizer column; Turboexpander train (A-Train and B-Train); JT / expansion-valve parallel cooling path; A-Train cold side reboiler ACSR – A-pass and B-pass core; A-Train warm side reboiler AWSR – A-pass and B-pass core; B-Train cold side reboiler; B-Train warm side reboiler; Residue-gas Destin outlet; NGL product to storage bullets then Tri-States pipeline; Condensate truck loading; Flare / atmospheric vent + let-it-burn response; DCS metal/stream temperature and differential-pressure instrumentation on ACSR/AWSR.
- Definitions (from JSON):
  - ACSR: A-Train cold side reboiler, BAHX in cryogenic area; most likely initial rupture location per DCS sequence (p.61-p.62).
  - AWSR: A-Train warm side reboiler, second BAHX in area; B-pass DP steady until 11:22-11:23 p.m. (p.61).
  - BAHX: stacked layers of parting/cap sheets, side bars, fins brazed; width/height sets hydrocarbon flow capacity (p.15).
  - DCS: Distributed control system data, event log and metal/stream temperature and differential pressure sensors used with surveillance to reconstruct timeline; timestamps did not match and required shifting (p.60-p.61).
  - LOC / Internal / Interpass leak: Loss of containment to atmosphere or internal leak between passes (p.66-p.67).
  - ROC: Change per minute in inlet, outlet or metal temperature; stream ROCs much larger than metal ROCs; guidance limits in degF/min (p.32) (p.37-p.38).
  - Thermal fatigue: Progressive cracking from cyclic pushing/pulling of aluminum parts due to temperature differences; also single-event thermal shock (p.16) (p.34).
- Turboexpander refrigeration: passes through a turboexpander, where its temperature is reduced to about -90 degF (p.59).
- BAHX structure: fins and braze joints hold the layers together, acting like a truss on a bridge (p.15).
- Breaches: After the incident, 12 different breaches were identified in the A-Train equipment, piping, and vessels (p.62). Task states 13 pieces ruptured.
- Emergency philosophy: plan was to vent fuel to the flare or vent to atmosphere and to let any existing fire burn until it self-extinguished (p.19). Value: Let-it-burn to minimize vapor-cloud explosion extending off property.

## Design Criteria

- BAHX operation RAGAGEP – rate of change limit start-up/shutdown: ROC of no more than 3.6 degF (2 degC)/min during start-up or shutdown – Yes in all four guidances (p.32). Sources: ALPEMA, Chart, GPA Midstream, API 662 per Table 3.
- BAHX operation RAGAGEP – normal operation ROC: 1.8 degF (1 degC)/min during normal operation per standards (p.36).
- BAHX operation RAGAGEP – hourly temperature change: Total temperature change of no more than 108 degF (60 degC) in an hour – Yes for ALPEMA/Chart/GPA Midstream, No for API 662 (p.32).
- BAHX structural integrity criterion: Brazed fin-to-cap/parting sheet joints act as truss to hold pressurized layers; pushing/pulling from temperature differences causes thermal fatigue cracking and loss of containment; single large event can cause thermal shock (p.15-p.16).
- Mechanical integrity / inspection criterion: PSM-covered BAHX requires inspection/maintenance (preventive and reactive); external surface examination for leaks/cracks at each HETSCO repair, grind-out and weld repair (p.43) (p.66).
- MOC / repair practice criterion: Blocking (welding closed) leaking passes and sealing/venting blocked-layer vent holes are changes requiring MOC, manufacturer approval and risk assessment; sealed holes prevent venting of interpass leak into blocked layer (p.44-p.45).
- Risk assessment / PHA criterion for cyclic service: BAHX in service with temperature fluctuations/cycling and external curtailment upsets requires evaluation of suitability, leak-before-break basis with crack-growth calculation and in-service monitoring – not assumed safe on leak history alone (p.41) (p.33) (p.40-p.42). Includes BP GP-26-10 discussion.
- Consequence mitigation criterion: PGP emergency plan: vent to flare/atmosphere and let fire burn to minimize vapor-cloud explosion extending off property; cool equipment where feasible; unified command with Jackson County Emergency Services (p.19-p.20).
- Standards considered: ALPEMA guideline for BAHX; Chart (manufacturer) BAHX guideline; GPA Midstream BAHX guidance; API 662 (American National Standard) – Only Table 2 source generated under American National Standards process; BP Group Practice GP-26-10 Guidance on Practice for Heat Exchangers – advises against BAHX in fluctuating-temperature service; considered in 2012 ACSR replacement evaluation.

## Data and Assumptions

Data register (facts only):

- DR-03/DR-04: Design 1.5 Bcf/d raw gas; up to 50,000 bpd NGLs (p.58). Incident ~500 MMscf/d raw gas; 16,000-18,000 bpd NGLs (p.58).
- DR-05: Curtailment then shut-in, 11:22 p.m. sudden explosion, No abnormal alarms (p.13).
- DR-06: ~35 minutes intensification (p.14).
- DR-07: about -90 degF after turboexpander (p.59).
- DR-08: Fins/braze joints to cap/parting sheet carry pressure load as truss (p.15).
- DR-09/DR-10/DR-11: 3.6 degF/min (2 degC/min) max per ALPEMA, Chart, GPA Midstream, API 662 (p.32). 108 degF (60 degC) per hour max – Yes/Yes/Yes/No (p.32). 1.8 degF/min (1 degC/min) normal operation (p.36).
- DR-12: Bins: 1.8-3.6; 3.6-12.6; 12.6-21.6; 21.6-30.6; >30.6 degF/min (p.37).
- DR-13: Metal ROC ~10x (also stated 4x) less than stream; in 2011 metal exceedances 2-3% of A-Train run time (p.38).
- DR-14/DR-15/DR-16: ACSR bottom metal 11:20-11:21 p.m. loss; remainder within next minute (p.61). A- and B-pass DP drop 11:21-11:22 p.m.; both passes compromised (p.61). ACSR DP stop by 11:24 p.m. (p.61).
- DR-17/DR-18: AWSR B-pass slight drop 11:22-11:23, stop 11:23-11:24; metal stop 11:23-11:25 p.m. (p.61). AWSR A-pass DP began dropping 10:50 p.m. with curtailment (p.61).
- DR-19: 12 breaches identified (task states 13 pieces ruptured) (p.62).
- DR-20/DR-21: 4 BAHXs repaired total 9 times by HETSCO (p.66). ACSR 4 repairs, most recent Sept 2015; 16 defects total (p.66).
- DR-22: 5 side-bar + 9 cap-sheet + 1 under attachment + interpass sealing(s) =16 (p.66). Detail: five leaks on the side bars (9, 11, 12, 13, 14), nine cracks on the cap sheet (1,2,3,4,5,6,8,15,16), one leak on cap sheet under attachment plate (7), and two pass sealings on either end (10) (p.66).
- DR-23: Repairs dated 10/16/2007, 9/15/2011, 10/23/2014, 9/16/2015 (p.67).
- DR-24: B-Train cold: 3 repairs: 4/12/2007 LOC, 2/26/2010 LOC, 3/7/2012 LOC interpass passes 97-99 (p.67). Detail: taken out of service for repair three times: (1 & 2) two cracks on cap sheet, and (3) sealing passes 97, 98, and 99 (p.67).
- DR-25: AWSR 1 repair 1/8/2008 4 edges; BWSR 1 repair 9/21/2010 (p.68). Detail: A-Train warm side reboiler has only one recorded repair. HETSCO welded all four edges along joint where cap sheet and attachment plate meet (1/8/2008). B-Train warm side reboiler repaired only once 9/21/2010 same crack (p.68).
- DR-26: Lab: thermal fatigue present; other Table 1 mechanisms eliminated (p.22). Detail: post-incident laboratory examination revealed clear evidence of service-related thermal fatigue at several locations. Available evidence eliminated several other well-known potential damage mechanisms (Table 1) (p.22).
- DR-27: Let-it-burn to minimize vapor-cloud explosion extending off property (p.19).

Assumptions – labelled ASSUMPTION with reason (from RFI):

- ASSUMPTION: Adopt CSB shifted relative order (ACSR metal > ACSR DP > AWSR) as correct because multiple independent sensors show same order; reason – consistent loss-of-signal progression and fire location. Addresses timestamp misalignment: DCS vs event log vs surveillance relative shifts (p.60). Timestamps did not match and required shifting.
- ASSUMPTION: Treat 12 breaches and 13 pieces as same event population (12 breach sites on 13 pieces) because both describe A-Train cryogenic area destruction; reason – avoids understating escalation. Addresses breach count conflict 12 vs 13 (p.62).
- ASSUMPTION: Use that metal ROCs are substantially smaller (order-of-magnitude) than stream ROCs, with 2-3% metal exceedance in 2011 as lower bound; reason – both statements agree directionally that stream sensors overstate metal stress. Addresses metal-vs-stream ROC factor conflict: p.38 states about 10 times less and also about four times less.
- ASSUMPTION: Treat each mobilization date as at least one LOC event and all cap/side-bar defects as thermal-fatigue candidates; reason – conservative given repeated LOC history. Addresses which ACSR defect leaked: Documentation does not state which crack resulted in leak that needed repair (p.67).
- ASSUMPTION: Assume blocked layers could pressurize if next pass leaked because vent path not assured; reason – HETSCO/Chart correspondence shows sealed-hole concern and BP asked about blocked-pass thermal stress approval (p.44-p.45). Addresses blocked-pass venting state unknown.
- ASSUMPTION: Assume curtailment caused flow reduction, boiling-regime instability and rapid localized T fluctuation in B-pass as described p.34; reason – mechanism description matches unmonitored rapid transient that would not alarm. Addresses no quantified stream T/P, flow, level or valve positions 10:50-11:22 p.m.; only DP trends described (p.61).
- ASSUMPTION: Assume LBB was invalid for ACSR because repeated LOCs show cracks reached through-wall without assured detection/analysis; reason – p.46 requires calculation + monitoring which are not evidenced. Addresses no crack dimensions, growth-rate calculations or monitoring threshold (p.46).
- ASSUMPTION – model geometry: All pipe diameters, lengths, C-factors, reservoir heads used in illustrative hydraulic runs are illustrative only; reason – no geometry/heads in document. Example: 6.0-in diameter, 100-ft/20-ft/10-ft lengths, 1.0-ft and -5.0-ft heads. Velocity-tool arithmetic 1.206 fps for 0.153 mgd in 6.0-in diameter is ASSUMPTION diameter/flow for arithmetic only; reason – no geometry in document; circular with model, not independent validation.
- ASSUMPTION – costs: cost bases are order-of-magnitude; reason – no cost data in pages, no new exchanger. See Alternatives table.
- ASSUMPTION – leak topology: illustrative leak to low-head reservoir; reason – document provides no leak geometry. Applies to RUPT-ILLUS P_LEAK 1315.1 gpm.

## Model Calibration

Prior steady-state single-phase water-pipe calibration runs BASE-CAL, ALT-CURT, ALT-FIRM, ACSR-RUPT are rejected for verification (see QA/QC Summary). Retained illustrative topology runs only – they do NOT represent cryogenic two-phase temperatures, boiling-regime instability (p.34), or thermal stress/fatigue (p.15-p.16), and do NOT verify DP-collapse order (p.61):

- BASE-ILLUS: intact split 106.0/106.0 gpm vs total 212.0 gpm at 1.2 fps – run label BASE-ILLUS – illustrates intact topology only.
- CURT-ILLUS: 110.7 gpm total, 55.3 gpm per pass at 0.63 fps vs BASE-ILLUS 212.0 gpm total, 106.0 gpm per pass at 1.2 fps; illustrates turndown topology only and does NOT demonstrate compliance with 3.6 degF/min shutdown / 1.8 degF/min normal / 108 degF/hr (p.32) (p.36) or control of rapid localized T fluctuation (p.34) – run label CURT-ILLUS.
- FIRM-ILLUS: 204.4 gpm through single A_PASS at 2.32 fps with B_PASS closed (0.0 gpm) vs BASE-ILLUS 106.0 gpm per pass intact; illustrates single-pass flow concentration only and does NOT prove firm thermal duty – run label FIRM-ILLUS.
- RUPT-ILLUS: leak-path topology with P_LEAK 1315.1 gpm (ASSUMPTION: illustrative leak to low-head reservoir, reason – document provides no leak geometry); illustrates blocked-layer pressurization concept (p.45) requires venting; does NOT reproduce 11:21-11:22 p.m. DP collapse (p.61) or verify initial failure point – run label RUPT-ILLUS.
- Supporting DCS order (relative-only per shifted-source method p.60): ACSR bottom metal stop 11:20-11:21, remainder next minute (p.61); A- and B-pass DP began dropping 11:21-11:22 p.m. both passes compromised (p.61); ACSR DP stop by 11:24 p.m. (p.61); AWSR B-pass steady until 11:22-11:23 then stop 11:23-11:24; metal stop 11:23-11:25 p.m. (p.61); AWSR A-pass DP began dropping 10:50 p.m. with curtailment (p.61) – run labels ACSR-RUPT / ALT-CURT retained only for relative-order illustration.

No heat-transfer calculation proves firm duty; BAHX capacity is heat-transfer duty with blocked-layer area loss (p.44), not pipe gpm/fps.

## Capacity Evaluation (table)

Relative times are bins per shifted-source method (p.60); ACSR-first rests on relative order, not absolute interval.

| Unit | Limit | Evidence | Binds_at | Limits_target |
|---|---|---|---|---|
| A-Train cold side reboiler ACSR – A-pass and B-pass core | Core rupture from thermal-fatigue-cracked truss (fins/braze joints p.15-p.16) | A- and B-pass DP drop 11:21-11:22 both passes compromised (p.61) per BASE-ILLUS intact 106.0 gpm/pass vs RUPT-ILLUS rupture topology; metal loss 11:20-11:21 (p.61); 16 defects 4 repairs most recent Sept 2015 (p.66); lab thermal fatigue, Table 1 others eliminated (p.22) | 11:21-11:22 p.m. June 27 2016 during curtailment/shut-in (p.13) (p.61) | true |
| A-Train warm side reboiler AWSR – A-pass and B-pass core | Secondary fire/explosion damage, not initial breach | B-pass steady until 11:22-11:23 then slight drop, stop 11:23-11:24; metal stop 11:23-11:25 (p.61); 1 repair 1/8/2008 (p.68) | 11:22-11:25 p.m. after ACSR (p.61) | false |
| B-Train cold side reboiler | Same thermal-fatigue susceptibility but did not initiate | 3 repairs: 4/12/2007, 2/26/2010, 3/7/2012 passes 97-99 sealing (p.67); no 11:20-11:22 DP collapse attributed | n/a – not breached first (p.62) | false |
| B-Train warm side reboiler | Secondary exposure only | 1 repair 9/21/2010 cap-attachment crack (p.68); no early DP/metal loss | n/a – not breached first (p.62) | false |
| Turboexpander train (A-Train and B-Train) | Refrigeration source; transient driver not failed unit | Turboexpander outlet about -90 degF (p.59); no breach attributed | n/a | false |
| Demethanizer column + slug catcher + dehydrator + separators + JT path + outlets + flare | Throughput below design; not capacity-limited | ~500 MMscf/d raw gas, 16,000-18,000 bpd NGLs (p.58) vs design 1.5 Bcf/d and 50,000 bpd (p.58); BASE-ILLUS topology only | n/a | false |

Findings detail supporting table:

- ACSR first in relative order; AWSR 1-3 one-minute bins later (p.61); 12 sites (p.62) vs 13 pieces in task (ASSUMPTION: same population counted differently, reason – pages map 12 breaches (p.62)). Evidence includes BASE-ILLUS 212.0 gpm total 106.0 gpm per pass at 1.2 fps vs RUPT-ILLUS leak-path topology only (ASSUMPTION: water analogy, reason – no cryogenic geometry; cannot represent boiling/thermal stress (p.34) (p.15-p.16)) – run labels BASE-ILLUS, RUPT-ILLUS.
- Mechanism: Fins/braze joints hold layers acting like truss (p.15); pushing/pulling from temperature differences fatigues metal creating thermal fatigue cracks plus single-event thermal shock (p.16); lab found clear service-related thermal fatigue at several locations with Table 1 others eliminated (p.22); 4 repair mobilizations on 10/16/2007, 9/15/2011, 10/23/2014, 9/16/2015 (p.67) within 9 total repairs on 4 BAHXs (p.66). Limiting: 4 ACSR repairs most recent Sept 2015 about 9 months before June 27 2016 rupture (p.67); repeated LOC history (p.67).
- Trigger: Curtailment then shut-in with no alarms then sudden 11:22 p.m. explosion (p.13); AWSR A-pass DP began dropping at 10:50 p.m. with curtailment (p.61); boiling-regime change during rate changes causes fluctuating DP and B-pass instability with rapid localized T fluctuation and liquid/vapor oscillation (p.34); absolute timestamps relative-only per shifted-source method (p.60) so interval 10:50 p.m. bin (p.61) to 11:22 p.m. (p.13) is relative sequence about 32 minutes, not absolute proof of rate.
- ROC monitoring: Guidance ROC bins 1.8-3.6, 3.6-12.6, 12.6-21.6, 21.6-30.6, greater than 30.6 degF/min (p.37); metal ROC stated as about 10 times less and also about four times less than stream ROC (p.38) – unresolved contradiction; metal exceedances 2-3 percent of run time in 2011 as example (p.38); RAGAGEP 3.6 degF/min shutdown, 1.8 normal, 108/hr (p.32) (p.36).
- Repair/MOC: B-Train cold 3 repairs including passes 97-99 sealing on 3/7/2012 (p.67); blocking leaking passes plus sealing/venting vent holes needing MOC and manufacturer approval with BP asking Chart/HETSCO on blocked-pass stress approval (p.44); silicone-filled holes relieve while sealed holes trap leak into blocked layer (p.45); as-found vent-hole state on ACSR unknown (ASSUMPTION: could pressurize if sealed, reason – HETSCO practice varied (p.45)); which crack leaked not stated (p.67) so LOC-to-mobilization is (ASSUMPTION: each mobilization greater than or equal to 1 LOC, reason – Table 8 groups cracks/LOCs (p.67)).
- MI/PHA: PSM MI covers preventive and reactive inspection/maintenance (p.43) (p.66); LBB requires low growth rate plus non-dangerous condition plus in-service monitoring plus calc leaking crack less than critical (p.46) with no evidenced calc/monitoring for repeated 2007-2015 LOCs (p.67) (ASSUMPTION: LBB invalid without calc/monitoring, reason – absence of evidence in available pages, not positive crack-size proof); BP GP-26-10 advises against BAHXs in fluctuating-T service with 2012 replacement evaluated (p.41-p.42); emergency plan vent to flare/atmosphere and let burn (p.19) with unified command and cool-where-feasible (p.20).

## Alternatives (table with cost class)

| Option | Result (run label) | Cost_class / Cost_basis | Meets_target | Recommended |
|---|---|---|---|---|
| OP-1 ROC-limited curtailment/shutdown + B-pass instability monitoring and auto-hold – Unit ACSR | CURT-ILLUS reports 110.7 gpm total, 55.3 gpm per pass at 0.63 fps vs BASE-ILLUS 212.0 gpm total, 106.0 gpm per pass at 1.2 fps; illustrates turndown topology only and does NOT demonstrate compliance with 3.6 degF/min shutdown / 1.8 degF/min normal / 108 degF/hr (p.32) (p.36) or control of rapid localized T fluctuation (p.34) – run label CURT-ILLUS | $100k-$1M / DCS ROC alarming + metal-T sensors + procedure rewrite; order-of-magnitude controls upgrade (ASSUMPTION: similar to small controls upgrade, reason – no cost data in pages, no new exchanger) | true | true |
| MI-1 Evaluate replacement of ACSR with design qualified for fluctuating-temperature service – Unit ACSR | FIRM-ILLUS reports 204.4 gpm through single A_PASS at 2.32 fps with B_PASS closed (0.0 gpm) vs BASE-ILLUS 106.0 gpm per pass intact; illustrates single-pass flow concentration only and does NOT prove firm thermal duty; BAHX capacity is heat-transfer duty with blocked-layer area loss (p.44), not pipe gpm/fps; full-rate firm capacity needs thermal/duty analysis – run label FIRM-ILLUS | >$10M / New BAHX or alternative with cyclic qualification + spare + MOC/manufacturer review; order-of-magnitude exchanger + outage (ASSUMPTION: cryogenic exchanger + outage, reason – PGP 500 MMscf/d throughput (p.58) cannot run long degraded) | true | false (deferred – needs thermal/duty study; not proven by hydraulics) |
| MI-2 Prohibit sealing blocked-layer vents shut, require MOC/manufacturer approval for pass blocking, implement LBB leak-monitoring with flare isolation – Unit ACSR | BASE-ILLUS intact split 106.0/106.0 gpm vs RUPT-ILLUS leak-path topology with P_LEAK 1315.1 gpm (ASSUMPTION: illustrative leak to low-head reservoir, reason – document provides no leak geometry); illustrates that blocked-layer pressurization concept (p.45) requires venting; does NOT reproduce 11:21-11:22 p.m. DP collapse (p.61) or verify initial failure point – run label RUPT-ILLUS | $100k-$1M / Procedural MOC + vent standard + LBB engineering study + hydrocarbon detectors tied to flare/de-inventory; engineering study only (ASSUMPTION: no hardware replacement, reason – analysis + detectors only, no cost data in pages) | true | true |

Firm capacity definition retained but rejected for BAHX gpm interpretation: BAHX capacity is heat-transfer duty, not pipe gpm/fps; higher velocity does not prove adequate 500 MMscf/d (p.58) or 1.5 Bcf/d design (p.58) duty.

## QA/QC Summary

Checked citations: DR-03/DR-04 p.58 design 1.5 Bcf/d 50,000 bpd; incident ~500 MMscf/d 16,000-18,000 bpd – verified; DR-05 p.13 curtailment/shut-in 11:22 p.m. sudden explosion No abnormal alarms – verified; DR-06 p.14 intensified several times over ~35 minutes – verified; DR-08 p.15 fins/braze joints hold layers acting like truss – verified; DR-09 p.32 ROC 3.6 degF/min start-up/shutdown – verified; p.36 1.8 degF/min normal – verified; p.38 metal ROC ~10x less also stated 4x less; 2-3% exceedance in 2011 – verified with internal contradiction noted; DR-07 p.59 turboexpander about -90 degF – verified; DR-26 p.22 lab clear thermal fatigue Table 1 others eliminated – verified; DR-27 p.19 vent to flare/atmosphere let-it-burn – verified; DR-20 p.66 4 BAHXs 9 repairs HETSCO external exam – verified; p.60 timestamp mismatch shifted, p.61 sequence order, p.43 17-yr ACSR leaks 2007/2011/2014/2015, p.44-p.45 blocked layers 1,2,98,99 vent holes welded closed vs silicone, p.41 BP GP-26-10 advises against BAHX in fluctuating-T two-phase – verified.

Checked runs: BASE-CAL, ALT-CURT, ALT-FIRM, ACSR-RUPT – all rerun and dispositioned below. Final illustrative labels: BASE-ILLUS, CURT-ILLUS, FIRM-ILLUS, RUPT-ILLUS.

Issues and resolution:

- Major: Hydraulic analogy invalid and ruptured run does not rupture – EPANET steady-state single-phase water pipe cannot represent cryogenic two-phase BAHX temperatures, boiling-regime instability p.34, thermal stress/fatigue p.15-p.16, or DP collapse. ACSR-RUPT LEAK 0.0 gpm did not rupture though claiming 11:21-11:22 both-passes-compromised DP drop p.61. Action: fixed – rejected BASE-CAL 495.5 gpm verification; re-ran as BASE-ILLUS (212.0 gpm total, 106.0 gpm per pass at 1.2 fps) and RUPT-ILLUS (P_LEAK 1315.1 gpm) explicitly labelled illustrative water-pipe topology only with ASSUMPTION geometry; cannot verify DP-collapse order.
- Major: Alternatives not verified by hydraulics – ALT-CURT halved flow does not demonstrate 3.6 degF/min shutdown / 1.8 normal / 108 degF/hr p.32 p.36 or control of rapid localized T fluctuation p.34; ALT-FIRM single-pass 326.3 gpm at 3.70 fps does not prove firm heat-transfer capacity ignoring blocked-layer area loss. Action: rejected – CURT-ILLUS and FIRM-ILLUS retained only to illustrate topology/flow concentration.
- Major: Invented data – pipe diameters, lengths, C-factors, reservoir heads had no source; velocity cross-check -0.11% circular; NGL gpm conversion ignores cryogenic density/two-phase. Action: fixed – labelled all as ASSUMPTION illustrative only; withdrew validation claim; velocity-tool 1.206 fps quoted only as arithmetic of same ASSUMPTION.
- Major: Misapplication of firm-capacity concept – BAHX capacity is heat-transfer duty with approach temperatures and blocked passes, not pipe gpm/fps; higher velocity does not prove 500 MMscf/d p.58 or 1.5 Bcf/d design p.58 duty. Action: rejected – FIRM-ILLUS illustrates topology only.
- Minor: Over-precise absolute timing despite relative-only basis p.60. Action: fixed – all times as relative-order bins; ACSR-first rests on relative order p.61 plus surveillance/DCS synthesis p.60-p.62.
- Minor: ROC factor 10x vs 4x contradiction p.38. Action: noted – retains only qualitative direction plus firm 2-3% 2011 metal-exceedance example p.38; stream ROC qualitative early warning only.
- Minor: Multiple ASSUMPTIONs (12 vs 13 count, LOC assignment, vent state, curtailment T/P/flows, LBB crack size) – LBB-invalid and blocked-layer pressurization rely on absence of evidence, not positive calc. Action: noted – LBB-invalid judged from absence of evidenced calc/monitoring required by p.46 given repeated LOCs p.67; sealed-vent prohibition and retire-vs-weld retained as precautionary judgment under MOC/manufacturer-approval requirement p.44-p.45.

## Recommendations

- Recognize ACSR as initial failure point for emergency planning; assume first breach at most-cracked BAHX and provide auto-de-inventory to flare with remotely operable isolation – Unit ACSR A-pass and B-pass core. Evidence: relative order ACSR metal loss 11:20-11:21 p.m. bin and DP drop 11:21-11:22 p.m. bin (p.61) precedes AWSR 11:22-11:25 bins (p.61) (p.60).
- Classify mechanism as thermal fatigue with final thermal-shock overload of pre-cracked truss; do not operate cracked BAHX on leak history alone; require BP GP-26-10 suitability review (p.41) plus LBB crack-growth calculation and monitoring (p.46) or retire – Unit ACSR. Evidence: truss (p.15), fatigue + shock (p.16), lab thermal fatigue Table 1 eliminated (p.22), 4 repairs 10/16/2007, 9/15/2011, 10/23/2014, 9/16/2015 (p.67) within 9 repairs on 4 BAHXs (p.66).
- Treat cyclic fatigue as root cause and curtailment transient as proximate trigger; require ROC-limited procedures respecting 3.6 degF/min shutdown and 108 degF/hr limits (p.32) and 1.8 degF/min normal operation (p.36) – Unit ACSR. Evidence: curtailment to 11:22 p.m. sequence (p.13) (p.61), B-pass instability rapid localized T fluctuation (p.34), relative-only caveat (p.60).
- Install metal-T ROC monitoring alarming on 1.8/3.6 degF/min and hourly budget; trend stream ROC only as qualitative early warning until factor resolved; enforce hold/slowdown on exceedance – Unit ACSR. Evidence: ROC bins (p.37), 10x vs 4x contradiction and 2-3% 2011 exceedance (p.38), limits (p.32) (p.36).
- Require MOC plus Chart approval for any pass blocking; leave vent holes open or silicone-filled only, never welded sealed; external exam each repair (p.66); track crack counts to retire, not repeatedly weld – Unit ACSR. Evidence: passes 97-99 sealing 3/7/2012 (p.67), MOC/manufacturer approval (p.44), silicone vs sealed (p.45), ASSUMPTION vent state could pressurize, ASSUMPTION each mobilization ≥1 LOC (p.67).
- Operator plus industry: PHA cyclic-service suitability assuming external curtailment upsets (p.33); implement LBB program with monitoring and calcs or replace; retain let-it-burn principle (p.19) but add rapid flare de-inventory, remotely operable isolation, detectors, and unified-command drill – Unit ACSR. Evidence: PSM MI (p.43) (p.66), LBB requirements (p.46) with no evidenced calc for 2007-2015 LOCs (p.67) (ASSUMPTION LBB invalid), BP GP-26-10 (p.41-p.42), below-design throughput (p.58), vent to flare/atmosphere and let burn (p.19) with cool-where-feasible (p.20). Options OP-1 and MI-2 recommended ($100k-$1M each, ASSUMPTION bases); MI-1 (>$10M, ASSUMPTION) deferred pending thermal/duty study.

## Limitations

- All times relative-order bins per shifted-source method (p.60); absolute 11:20-11:25 sequence uncertain; ACSR-first conclusion depends on ASSUMPTION shifted order correct.
- Breach population 12 (p.62) vs 13 pieces per task – ASSUMPTION same population counted differently.
- Metal-vs-stream ROC factor unresolved 10x vs 4x (p.38); quantitative exceedance interpretation limited; 2-3% 2011 example (p.38) is lower bound; ROC bins (p.37) cannot be quantified without resolution.
- Which crack leaked not stated (p.67) – ASSUMPTION each mobilization ≥1 LOC; all defects treated as fatigue candidates.
- Blocked-pass as-found vent condition unknown (p.44-p.45) – ASSUMPTION could pressurize if sealed; precautionary, not quantified proof.
- No quantified stream T/P, flow, level, valve positions 10:50-11:22 p.m.; only DP trends (p.61) – ASSUMPTION curtailment caused flow reduction and B-pass instability (p.34); cannot quantify thermal-shock rate.
- No crack dimensions, growth-rate calcs, leak-detection threshold (p.46) – ASSUMPTION LBB invalid from absence of evidenced calc/monitoring given repeated LOCs (p.67), not positive crack-size proof.
- Hydraulic runs BASE-ILLUS, CURT-ILLUS, FIRM-ILLUS, RUPT-ILLUS are illustrative water-pipe topology only (ASSUMPTION geometry/heads); steady-state single-phase model cannot represent cryogenic two-phase, boiling instability (p.34), thermal stress (p.15-p.16), or verify failure point; firm thermal duty needs heat-transfer analysis considering blocked-layer area loss (p.44) and design/actual throughputs (p.58).
- Costs are order-of-magnitude ASSUMPTIONS (no cost data in pages).
