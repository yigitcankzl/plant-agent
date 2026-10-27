DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum - Stanislaus Finished Water Surge Screening (stanislaus_surge)

## Purpose
Evaluate abrupt power failure of the new WTP Finished Water Pump Station (FWPS) at design flow and pressure response before standby generator restart:
- Phase 1 design flow (p.3): 15 mgd total — 10 mgd to Turlock terminal tank, 5 mgd to Ceres terminal tank.
- Buildout design flow (p.3): 45 mgd total — 30 mgd Turlock, 15 mgd Ceres.
- Mains (p.1): ~41,000 LF 42-inch Turlock, ~29,000 LF 30-inch Ceres.
- Determine if surge protection is needed to keep 10 psi regulatory margin (p.3), and if so type/size (volume and air ratio) for each pipeline in Phase 1 and buildout.
- Note anything design-build (DB) team could change to reduce it.

## Background
- Facility: Regional Surface Water Supply Project finished water pipelines (Turlock 42-inch, Ceres 30-inch), Stanislaus Regional Water Authority, California. Source: West Yost Associates for SRWA Technical Advisory Committee, Regional Surface Water Supply Project - Finished Water System Surge Analysis, Technical Memorandum, August 1, 2018 (public record).
- Turlock Finished Water Transmission Main (p.1): ~41,000 linear feet (LF) of 42-inch diameter cement mortar lined and coated steel pipe from WTP to Turlock terminal tank.
- Ceres Finished Water Transmission Main (p.1): ~29,000 LF of 30-inch diameter cement mortar lined and coated steel pipe from WTP to Ceres terminal tank.
- Path (per JSON): Regional WTP clearwell (WS El. 114 ft) (p.2) > Finished Water Pump Station (El. 107 ft) (p.2) - Turlock pumps + Ceres pumps with VFDs > transmission mains > altitude valves with sustaining feature at terminal tanks (35 psi / 80.9 ft above tank bottom; HGL 198 ft Turlock, 190 ft Ceres) (p.3) > terminal tanks.
- Definitions:
  - TDH = Total Dynamic Head - pre-design duty point head per pump (p.2).
  - HGL = Hydraulic Grade Line (p.2-p.3).
  - Firm capacity = capacity with largest unit out of service (duty pumps only) (Engineering rules; pump counts p.2).
  - VFD = Variable Frequency Drives - all finished water pumps assumed with VFDs (p.2).
  - InfoSurge = Software tool using University of Kentucky surge code, running within InfoWater, using InfoWater hydraulics plus transient data (p.1).
- Pumps (p.2):
  - Turlock Phase 1: 3,500 gpm at 92 ft TDH; 3 pumps (2 duty, 1 standby).
  - Turlock Buildout: 3,500 gpm at 142 ft TDH; total 7 pumps (6 duty, 1 standby).
  - Ceres Phase 1: 3,500 gpm at 83 ft TDH; 2 pumps (1 duty, 1 standby).
  - Ceres Buildout: 3,500 gpm at 132 ft TDH; total 4 pumps (3 duty, 1 standby).
- Terminal tanks (p.3): bottom El. 117.1 ft Turlock; 108.7 ft Ceres. Water surface modeled 10 ft above bottom (p.3).
- Alignment high point (p.6): 141 ft. Full pipeline elevations based on survey data (p.2); profiles p.10, p.13 (low-resolution images only in available pages).
- Generator/restart (p.2-p.3, Figure 2 p.7): Generator(s) start 10 seconds following power failure; first pump starts with generator and ramps to full speed in 30 seconds; each subsequent pump ramps in 30 seconds with 30 second lag before next pump starts.

## Design Criteria
- Minimum transient pressure - finished water system (p.3 - State Water Resources Control Board, DDW, 2018): 10 psi minimum.
- High-pressure surge risk criterion - steel pipe (p.3): steel pipeline has surge allowance of 150 percent of design pressure; mitigation for low pressures will reduce highest pressures to close to normal operating conditions.
- Transient scenarios to evaluate - power failure (p.2): evaluate low-pressure event and water column separation following abrupt power failure and subsequent high-pressure surge on rejoin, and maintaining pressurized flow to meet regulatory requirements and avoid pathogen intrusion.
- Phase 1 design flow (p.3): 15 mgd total: 10 mgd Turlock, 5 Ceres.
- Buildout design flow (p.3): 45 mgd total: 30 mgd Turlock, 15 Ceres.
- Pump restart sequence (p.2-p.3, p.7 Figure 2): 10-sec generator start; first pump 30-sec ramp; each subsequent 30-sec ramp with 30-sec lag.
- Standards: AWWA M-11 Steel Pipe - A Guide for Design and Installation, basis for Hazen-Williams C=140 (p.3); State Water Resources Control Board, DDW, 2018, basis for 10 psi minimum (p.3).

## Data and Assumptions
Data used (with source):
- D01 (p.1): ~41,000 LF 42-inch Turlock; D02 (p.1): ~29,000 LF 30-inch Ceres.
- D04 (p.2): clearwell WS 114 ft; D05 (p.2): FWPS El. 107 ft per Trussell pre-design HGL.
- D07 (p.2): all FW pumps with VFDs; D08-D11 (p.2): duty points above.
- D12 (p.2): 10-sec generator + first pump 30-sec ramp; D13 (p.3): 30-sec ramp + 30-sec lag; D14 (p.7): Figure 2 timeline as printed.
- D15 (p.3): wave speed 3,840 ft/s based on materials/diameters; cf. D03 (p.1) general ~3,600 ft/s background.
- D16 (p.3): Hazen-Williams C=140 per AWWA M-11.
- D17-D20 (p.3): tank bottoms 117.1/108.7 ft; 10 ft depth; sustaining 35 psi (80.9 ft); HGL 198 ft Turlock, 190 ft Ceres.
- D24 (p.10) / D25 (p.13): mitigated max HGL/pressure = normal operating pressure (with mitigation, Phase 1 Turlock/Ceres).
- D26 (p.3): 10 psi minimum.

ASSUMPTIONS (labeled per requirement):
- ASSUMPTION - Trip location: Model trips FWPS at WTP clearwell (El. 107 ft, D04-D05). REASON: p.2 raw-water pump station wording treated as TM typo; all pump, generator, profile data (p.2-p.3, p.10, p.13) are finished-water.
- ASSUMPTION - Wave speed: Use 3,840 ft/s (p.3) for analysis. REASON: p.3 explicitly labeled assumed analysis value; 3,600 ft/s (p.1) is general background.
- ASSUMPTION - Elevations/profile: Hold p.2-p.3 elevations and p.6 141-ft high point fixed; 3-segment screening profile using clearwell 114 ft (p.2), El. 107 ft (p.2), HGLs 198/190 ft (p.3), 35 psi/80.9 ft sustaining (p.3), C=140 (p.3), lengths ~41,000/~29,000 ft (p.1). REASON: full survey profile withheld except low-res p.10/p.13; high-point chainage assumed (Turlock mid-pipe ~15,000 ft, Ceres ~4,000 ft from FWPS) therefore conservative at assumed high point. Final survey/tank/clearwell elevations TBD by DB team.
- ASSUMPTION - Pump/valve characteristics: Pumps trip instantly, coast-down per simulator defaults, VFDs (p.2) govern only restart ramps; no check/air valves credited. REASON: inertia, curves beyond single 3,500 gpm points at 92/83 ft Phase 1 and 142/132 ft buildout (p.2), valve data not in available pages; conservative for downsurge.
- ASSUMPTION - Restart timing: Apply written rule (D12-D13: 10-sec + 30-sec ramp + 30-sec lag) for Phase 1 and buildout. REASON: written rule unambiguous; Figure 2 numbers garbled (p.7) treated illustrative only.
- ASSUMPTION - Vessel type/air ratio: Closed bladder hydropneumatic chambers at/near FWPS discharge, ~50% air / 50% water. REASON: type/volume/air-ratio clauses withheld on p.1, p.2, p.3 (and p.6); 50% balances feed volume vs pressure maintenance; final gallons/ft3, vessel count by DB team.
- ASSUMPTION - High-pressure compliance: Judge as max transient <= ~normal operating HGL/pressure per p.10/p.13 notes. REASON: pipe design pressure rating not quoted; only 150% surge allowance noted (p.3).

## Model Calibration
Steady-state duty-point checks (C=140 p.3; HGLs 198/190 ft p.3; clearwell 114 ft p.2; El. 107 ft p.2; screening profile ASSUMPTION as above):

| Run label | Test (measured p.2) | Simulated | Residual |
|---|---|---|---|
| SS-TUR-P1 / SS-TUR-P1-FIX | Turlock Phase 1 10 mgd (p.3): 7,000 gpm firm (2x3,500 gpm) at 92 ft TDH (p.2) | 7,050.9-7,051.2 gpm at 91.55 ft TDH, DIS 42.7 psi (42.74 psi steady) | 0.7% |
| SS-CER-P1 / SS-CER-P1-FIX | Ceres Phase 1 5 mgd (p.3): 3,500 gpm (1x3,500 gpm) at 83 ft TDH (p.2) | 3,473.7-3,473.9 gpm at 83.41 ft TDH, DIS 39.2 psi (39.21 psi steady) | 0.8% |
| SS-TUR-BO / SS-TUR-BO-FIX | Turlock buildout 30 mgd (p.3): 21,000 gpm firm (6x3,500 gpm) at 142 ft TDH (p.2) | 21,104.8-21,107 gpm at 141.53-141.51 ft TDH, DIS 64.4 psi | 0.5% |
| SS-CER-BO / SS-CER-BO-FIX | Ceres buildout 15 mgd (p.3): 10,500 gpm firm (3x3,500 gpm) at 132 ft TDH (p.2) | 10,418.3-10,419.4 gpm (15.004 mgd) at 132.68-132.67 ft TDH, DIS 60.6 psi | 0.8% |

Nominal velocities (velocity tool, exact mgd): 10 mgd/42-in 1.608 fps; 5 mgd/30-in 1.576-1.58 fps; 30 mgd/42-in 4.824 fps; 15 mgd/30-in 4.728 fps. SS velocities 1.63/1.58/4.89/4.73 fps differ only by pumped-flow rounding/duty-point residual - ASSUMPTION noted.

## Capacity Evaluation
Unprotected power-failure response (generator 10-sec start p.2 occurs after separation; wave 3,840 ft/s p.3):

| Unit | Evidence (run label) | Limit | Binds at / Limits target? |
|---|---|---|---|
| Turlock 42-in ~41,000 ft Phase 1 10 mgd (p.1,p.3) | SUR-TUR-P1-NONE-FIX: DIS min 3.04 psi (steady 42.74 psi), SURG 3.03 psi, HIGH -12.48 psi, MID -4.13 psi, max 75.02 psi at DIS; vapour true in screening; steady 1.608 fps | 10 psi minimum (p.3); vapour = column separation/pathogen risk (p.2) | Binds at mid-pipe and 141 ft high point (p.6) within seconds, well before 10-sec generator (p.2). Yes - fails. |
| Ceres 30-in ~29,000 ft Phase 1 5 mgd (p.1,p.3) | SUR-CER-P1-NONE-FIX: DIS min 3.04 psi (steady 39.21 psi), HIGH -12.01 psi, MID -3.76 psi, max 68.29 psi; steady 1.576 fps | 10 psi minimum (p.3) | Binds at 141 ft high point (p.6) and mid-pipe before restart. Yes - fails. |
| Turlock 42-in buildout 30 mgd (p.3) | SUR-TUR-BO-NONE-FIX: SURG 2.74 psi, HIGH -19.0 psi vapour true, MID -17.09 psi vapour true; steady 4.824 fps; steel 150% allowance (p.3) so high not binding | 10 psi minimum (p.3) | Binds entire main incl. discharge header on trip; rejoinder highs ~75-82 psi. Yes - fails low. |
| Ceres 30-in buildout 15 mgd (p.3) | SUR-CER-BO-NONE-FIX: SURG 2.58 psi, HIGH -14.49 psi vapour true, MID -13.49 psi; steady 4.728 fps | 10 psi minimum (p.3) | Binds high point and header on trip. Yes - fails. |

Finding: Generator restart alone (p.2-p.3, Fig.2 p.7) occurs after separation. Provide surge protection at/near FWPS discharge on each main.

## Alternatives
ASSUMPTION: All vessel options are closed bladder air chambers at/near FWPS discharge, ~50% air. Volumes converted to document US units: 30 m3 = 1,060 ft3 = 7,925 gal; 80 m3 = 2,825 ft3 = 21,134 gal (40 m3 air = 1,413 ft3 = 10,567 gal); 200 m3 = 7,063 ft3 = 52,834 gal. Simulator area_m2 x height_m retained only as run parameter. Cost class = n/a - ASSUMPTION: no TM costs in available pages.

| Option (run label) | Unit | Result | Meets 10 psi (p.3)? / Recommended? | Cost class |
|---|---|---|---|---|
| No vessel - rely on 10-sec generator + 30-sec ramps/lags (p.2-p.3) only (SUR-TUR-BO-NONE / SUR-*-NONE-FIX) | Both mains Phase 1 and buildout (p.3) | All NONE-FIX mins -12 to -19 psi vapour true; column separation in seconds before restart; rejoinder highs 68-75 psi near normal but lows violate 10 psi (p.3) | No / Not recommended | n/a |
| Closed bladder 30 m3 total, 50% air (SUR-TUR-P1-AC30-FIX) | Turlock 42-in ~41,000 ft Phase 1 10 mgd (p.1,p.3) | SURG min 2.43 psi, HIGH -2.86 psi - fails | No / Not recommended | n/a |
| Closed bladder 80 m3 total, 50% air (40 m3 air/40 m3 water) (SUR-TUR-P1-AC80-FIX) | Turlock 42-in ~41,000 ft Phase 1 10 mgd (p.1,p.3) | SURG min 13.16 psi (steady 42.73 psi), MID 24.18 psi, HIGH 5.78 psi (steady 26.79 psi), max <=steady; TM mitigated max=normal (p.10) | Yes at header/mid; HIGH screening low due to assumed chainage - holds order; Recommended phased starter | n/a |
| Closed bladder 80 m3 total, 50% air (SUR-CER-P1-AC80-FIX) | Ceres 30-in ~29,000 ft Phase 1 5 mgd (p.1,p.3) | SURG 20.48 psi (steady 39.2 psi), MID 22.36 psi, HIGH 7.51 psi (steady 24.01 psi); TM mitigated max=normal (p.13) | Screening HIGH 7.51 psi driven by ASSUMPTION 141 ft (p.6) chainage 4,000 ft from FWPS; final-profile design passes per TM (p.13); size order 60-80+ m3 50% air to hold >=10 psi (p.3); Recommended | n/a |
| Closed bladder ~200 m3 total, ~50% air - phased expansion of Phase 1 vessels (SUR-TUR-BO-AC200-FIX) | Turlock 42-in buildout 30 mgd (p.3) | SURG 9.76 psi, MID 23.15 psi, HIGH 3.51 psi; HIGH meets trend; station dip is coast-down artifact before 10-sec generator (p.2); mitigation for lows brings highs to normal (p.3,p.10) | Trend shows ~200 m3 order holds system; final DB InfoSurge (p.1) to add volume/distributed air valves to clear 10 psi everywhere; Recommended phased | n/a |
| Closed bladder ~150-200+ m3 total, ~50% air - phased expansion (screening for SUR-CER-BO-AC150 concept) | Ceres 30-in buildout 15 mgd (p.3) | Trend +50 m3 lifts HIGH ~6 psi; ~200 m3 order + final-profile air/vacuum valves holds >=10 psi (p.3); max stays ~steady (p.13) | Yes with final-profile valves/InfoSurge; Recommended phased; to be finalized by DB InfoSurge | n/a |

Summary sizing (ASSUMPTION, to be finalized by DB InfoSurge p.1 using final survey p.10,p.13): Phase 1 order ~80 m3 (~2,825 ft3 / ~21,100 gal total, ~1,413 ft3 / ~10,570 gal air) per main; buildout phased expansion to ~150-200+ m3 (~5,300-7,060 ft3 / ~39,600-52,800 gal total).

## QA/QC Summary
- Checked citations: D01 p.1 ~41,000 LF 42-in; D08 p.2 Turlock Phase 1 3,500 gpm at 92 ft 3 pumps; D15 p.3 3,840 fps distinct from p.1 ~3,600 fps; D21 p.3 Phase 1 15 mgd (10/5) + D22 buildout 45 mgd (30/15); D26 p.3 10 psi + D19/D20 35 psi/80.9 ft HGL 198/190 ft; D12/D13 p.2-p.3 10-sec +30-sec ramp/lag vs garbled Figure 2 p.7; D24/D25 p.10/p.13 max=normal.
- Checked runs: SS-TUR-P1, SS-CER-P1, SS-TUR-BO, SS-CER-BO rerun matches_logged_result true. Old SUR-*-NONE/AC30/AC60/AC80/AC100/AC200/ST200/AC40/AC150 precise mins withdrawn; replaced by FIX outputs.
- Issues/resolution:
  - Major - Transient runs not retrievable -> Fixed: re-ran with FIX labels (SUR-TUR-P1-NONE-FIX, SUR-CER-P1-NONE-FIX, SUR-TUR-BO-NONE-FIX, SUR-CER-BO-NONE-FIX, SUR-TUR-P1-AC30-FIX, SUR-TUR-P1-AC80-FIX, SUR-CER-P1-AC80-FIX, SUR-TUR-BO-AC200-FIX). Un-rerun sizes (AC60/AC100/AC150/ST200) withdrawn.
  - Major - Vessel type/size had no page citation -> Fixed: now explicitly ASSUMPTION (withheld clauses); only cited TM facts are max=normal (p.10,p.13), 10 psi (p.3).
  - Major - SI units vs US document -> Fixed: volumes in ft3/gallons; SI only as simulator parameter.
  - Major - Controlling low driven by assumed chainage -> Noted: 3-segment ASSUMPTION conservative; final vapour location/duration requires DB full-profile InfoSurge (p.1) and survey (p.10,p.13). Need conclusion (vessels) does not depend on chainage - header also fails.
  - Minor - High-pressure without rating -> Noted: limited to screening max<=steady + TM max=normal (p.10,p.13); DB to verify vs rating/surge allowance.
  - Minor - Velocity nominal vs SS -> Fixed: nominal exact-mgd vs SS pumped-flow rounding noted.
  - Minor - Open-tank dismissal/costs unsupported -> Fixed: open-tank withdrawn (no retrievable run); costs n/a.

## Recommendations
- Provide surge protection at/near FWPS discharge on each main; generator restart alone (p.2-p.3, Fig.2 p.7) occurs after separation.
- Phase 1 (ASSUMPTION): closed bladder air chambers, ~50% air, order ~80 m3 (~2,825 ft3 / ~21,100 gal) per main (Turlock SUR-TUR-P1-AC80-FIX, Ceres SUR-CER-P1-AC80-FIX).
- Buildout (ASSUMPTION): phased expansion to ~150-200+ m3 (~5,300-7,060 ft3 / ~39,600-52,800 gal) total per main (Turlock SUR-TUR-BO-AC200-FIX trend), plus distributed air valves to clear 10 psi (p.3) everywhere; max stays ~steady per TM (p.10,p.13).
- DB team to reduce/confirm (per analysis): confirm final survey profile (p.10,p.13) and try to lower/avoid sharp 141 ft summit (p.6, anchor 141.0 ft); add combination air/vacuum valves at final summits per AWWA M-11 practice (C=140 per M-11 p.3); add pump inertia/flywheel, expedite restart, re-run InfoSurge (p.1) before vessel purchase; verify highs <= design rating / surge allowance; finalize gallons, vessel count and air ratio.

## Limitations
- Available pages omit pump inertia, curves beyond single points, VFD trip/ramp-down, check-valve type/closure, air-valve locations/sizes; screening assumes instant trip/coast-down defaults, no valves credited - ASSUMPTION conservative.
- Full survey pipeline profile not in available pages except high point 141 ft (p.6) and low-res p.10/p.13; chainage assumed - HIGH-node results flagged conservative.
- Surge-protection type/volume/air-ratio withheld on p.1,p.2,p.3,p.6; all sizes are ASSUMPTION screening orders, not TM quotes; only TM mitigated statement is max=normal (p.10,p.13).
- Pipe design pressure/operating pressures not quoted; high-pressure finding limited to max<=steady screening.
- Elevations preliminary (clearwell 114 ft/pump 107 ft per Trussell pre-design HGL p.2; tank bottoms per preliminary design-team info p.3); final elevations/profile TBD.
- No costs in available pages; cost class n/a.
