DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum - Caen Hill Pumping Station Pump Audit

## Purpose

Audit the Caen Hill Pumping Station, Kennet and Avon Canal, UK (p.7) to diagnose reported short bearing and seal life, gasket failures and higher than expected energy use (p.14, p.18, p.12).
Using site tests 11 September 2019 (p.9), SCADA data (p.13, p.11) and system description (p.7), diagnose causes (hydraulic, vibration, surge, control) (p.15, p.19, p.13), quantify unexplained losses with the simulator (p.11), and recommend measures with expected benefit.

Source: Arcadis for Canal & River Trust, Caen Hill Pumping Station Pump Audit Summary Report, 2020 (Interreg Green WIN public deliverable) (p.6).

## Background

- Facility: Caen Hill PS near Devizes, Wiltshire, UK. Purpose is to supply water up from Lock 22 to Lock 50 (p.7).
- Construction: 1996, dry well construction (p.7).
- Pumps: 2x Xylem (Flygt) CT3240 (p.7), twin / 2-vane (or 2-channel) impeller, sewage type dry well submersible (p.15, p.17, p.18), 535 mm diameter (p.7), 78 mm throughlet (p.18), 215 kW rated motor output (p.7), generated head up to 85 m (p.17).
- Installed duty: Duty / Assist (p.7). Operated: both in parallel (duty/duty) at fixed 48 Hz via Lock 50 level telemetry (p.13).
- Drives: Variable Speed Mitsubishi VSDs (p.7), 48.0 Hz operating frequency normal (p.7), 30 s ramp (p.7), tests at 50, 48, 45 Hz (p.13).
- Station pipework: 300 mm diameter (p.7). Each delivery branch has ball check valves (p.7, p.18). Non-return valves located close to pump delivery not achieving 3 or 5 diameters (p.18, p.19). Each branch has untied flange adaptors (p.19). Manifold supported off floor and back wall by bracing supports, with tied coupling present (p.19).
- Controls/Instrumentation: Lock Flight 50 level monitored and transmitted; falling to pre-set low level pumps start, rising to pre-set high level both ramp down and stop (p.13). Flow via on-site electromagnetic flowmeter, but not utilised for control (p.13). MAS 711 relay protection and low level suction protection (p.13). Wet-well ultrasonic sensor (p.7). Suction/delivery pressure transducers + portable Fluke power meter + portable ultrasonic + GPS elevation for audit (p.9).
- Levels: Wet-well level 55.5 mAOD (p.7), Pump centreline 54.3 mAOD (p.7), Discharge level 127.6 mAOD (p.7), Elevation rise 72 m (p.7).
- Rising main: ~3600 m length (p.7), 3602 m (p.7), 600 mm diameter (p.7), Ductile Iron, no bursts since construction (p.7). Intermediate NRV #1 1270 m from PS (p.7), Intermediate NRV #2 2410 m from PS (p.7), in-line NRVs with return bypass immediately downstream of each discharge point (p.7). Condition and operational effectiveness not known, covered with large concrete infill covers in remote locations (p.7).
- Observed failures:
  - Pump 1 seized solid due to failed bearings; both seals failed, oil into stator, water ingression emulsified oil, pitting in centre of impeller possibly cavitation (p.14). Pump 1 leaking glycol coolant from top seal (p.14).
  - Typical bearing life 2,000-3,000 hours vs design 50,000 hours (p.14).
  - Pipe flange gasket failures (p.18).
  - Debris: two occasions since Nov 2017 significant debris necessitated reactive removal (p.18) plus July 2019 inspection (p.18).
  - Wet well Aug 2019: both intake screens 30% loss due to silt, circa 40 tonnes silt/brick/concrete rubble/vegetation removed, pipework confirmed clear (p.19).

Units on path (p.7, p.13, p.18, p.19, p.20):
Wet well with floating trash baffles and bar screens > intake bellmouths/screens > suction to 2x CT3240 vertical base-mounted > Mitsubishi VSDs 30 s ramp + MAS711/low-level > DN300 delivery branches with ball checks (<3-5D) > untied adaptors > common manifold on bracing + tied coupling > magflow (indication only) + pressure transducers + ultrasonic > DN600 DI ~3602 m to 127.6 mAOD > NRV1+bypass 1270 m > NRV2+bypass 2410 m > Lock 50 telemetry to SCADA.

## Design Criteria

- Duty philosophy: 2x pumps duty/assist installed but operated duty/duty in parallel at fixed 48 Hz via Lock 50 telemetry; 30 s VSD ramp (p.7, p.13).
- Operating speed: 48 Hz normal; test points 50, 48, 45 Hz (p.7, p.13).
- Preferred Operating Region (POR): 70% to 120% of flow at BEP - vibration lowest inside POR (p.14).
- Vibration acceptance: 11.2 mm/s RMS velocity (WIMES 1.03 single-channel/screw limit applied as reasonable limit to 2-channel CT3240) (p.15). BS ISO 10816-7 damage risk >9.5 mm/s noted but submersibles excluded from scope (p.15).
- Vibration basis: Generally per BS ISO 10816 Part 7, magnetic transducer at drive bearing end above volute X/Y/Z + mounting plate corner, 11 Sept 2019 (p.15).
- NPSH: NPSHa must exceed NPSHr with margin; report calculates ~4 m margin, volute below canal level fully primed (p.12).
- Intake: ANSI/HI 9.8 ideal 0.3D to 0.5D bellmouth above floor (p.19).
- Energy metric: STRING wire-to-water including VSD efficiency and specific energy from VSD input power, flow and pressure (p.12).
- Energy ranking: 48 Hz lower specific energy than 50 Hz or 45 Hz; 2-pump parallel higher specific energy / lower efficiency than single due to left-of-BEP (p.13).
- Bearing life: Design 50,000 h vs observed 2,000-3,000 h - short life indicative of excessive vibration (p.14).
- Surge basis: VariSim basic transient at 48 Hz: uncontrolled 2-pump trip, uncontrolled 1-pump trip (two running), controlled stop 30 s ramp; with intermediate NRVs failed open and working (p.19).
- Pipework: Xylem: critical length 6-7 m, first support <=2.3 m, subsequent at 4.8 m; NRVs should achieve 3 or 5 diameters from delivery; supports/anchors to avoid residual forces/moments (p.17).
- Definitions: Firm capacity = one pump running alone (Engineering rules + p.7); STRING efficiency = wire-to-water incl VSD from measured VSD input (p.12); Check valve slam = ball-check pressure spike after trip/stop due to poor dynamic response (p.18).
- Standards: BS ISO 10816-7 vibration guidance (9.5 mm/s risk, submersibles excluded); WIMES 1.03 cl.7.2.3/7.1.1 (70-120% BEP, 7.1 mm/s multivane/vortex, 11.2 mm/s single-channel/screw); ANSI/HI 9.8 intake 0.3D-0.5D.

## Data and Assumptions

Site test data used (p.12 Table 3):

- Pump 1 only: 199 l/s 50 Hz 0.92 PF 224.0 kW 69% string 312.7 (p.12); 168 l/s 48 Hz 0.90 187.5 kW 68% 310.0 (p.12); 118 l/s 45 Hz 0.87 137.5 kW 62% 323.7 (p.12).
- Pump 2 only: 201 l/s 50 Hz 0.90 214.5 kW 73% 296.4 (p.12); 168 l/s 48 Hz 0.90 179.0 kW 71% 296.0 (p.12); 118 l/s 45 Hz 0.89 133.0 kW 64% 313.1 (p.12).
- Both pumps: 266 l/s total (P1 power) 48 Hz 0.91 170.0 kW 64% 347.6 avg (p.12); 267 l/s total (P2 power) 48 Hz 0.91 163.5 kW 66% 347.6 avg (p.12); 310 l/s total 50 Hz 0.92 192.0-201.0 kW 66-69% 352.2 avg (p.12); 191 l/s total 45 Hz 0.88-0.89 122.0-126.0 kW 57-60% 360.7 avg (p.12).
- SCADA: Daily volume pumped 2018 up to ~23000 m3/day, suggests optimisation opportunity (p.13).
- System loss: <25 years pipeline, additional K=120 necessary to correlate with SCADA delivery pressure (p.11).
- Vibration examples: 1+2 48 Hz 266 l/s Average 12.60 X 13.50 Y 16.40 Z (p.16); 1 50 Hz 199 l/s 37.50 X max 30.00 Y max 19.50 Z max / mounting plate 27.80 max 23.60 avg (p.16).
- Surge: Uncontrolled 2-pump trip 17.5 bar.g (p.19); Uncontrolled 1-pump trip (two running) 20 bar.g (p.19); Controlled stop 30 s ramp 13 bar.g (p.19); high transients assuming intermediate NRVs not operational (p.19).
- Mounting: plate vibration comparable to pump, plinths not firm, cracking and groundwater/clay seepage at plinth-floor joint (p.15); vertical base-anchored motor unsupported, lower natural frequency/stiffness exacerbated by poorly anchored plinths (p.17). Pipe supports within distances (p.17). Intake baffles satisfactory (p.20). Large wide well low velocity dead spots inevitably solids deposition (p.19). Bar/benching trade-offs and Fig12 benching option (p.20).

ASSUMPTIONS (labelled, from RFI/analysis):

- ASSUMPTION: Assess single-pump as firm capacity and two-pump parallel as installed peak; reason - Table 1 Duty/Assist (p.7) conflicts with fixed parallel duty/duty at 48 Hz (p.13) and tests cover both (p.12).
- ASSUMPTION: Adopt wet well 55.5 mAOD (p.7), pump CL 54.3 mAOD (p.7), discharge 127.6 mAOD (p.7) = 72 m rise (p.7) as static basis; reason - only quoted levels, raw pressures/depths/GPS (p.9) not tabulated.
- ASSUMPTION: Treat extra K=120 (p.11) as anomaly range K120-170 vs clean friction; reason - <25 yr DI main (p.11) should not need K120 to match SCADA (p.11).
- ASSUMPTION: Model worst-case intermediate NRVs failed open (p.19) for surge/head; reason - condition unknown under concrete covers remote (p.7).
- ASSUMPTION: Accept installed magflow (p.9, p.13) as reference with uncertainty; reason - same meter for test and SCADA (p.11, p.13) but not used for control (p.13).
- ASSUMPTION: Use STRING wire-to-water incl VSD from VSD input (p.12); reason - VSD/motor/pump split not given and 224.0 kW (p.12) exceeds 215 kW motor (p.7).
- ASSUMPTION: Accept ~4 m NPSHa margin (p.12) and pursue blockage/silt (p.12); reason - volute below canal primed (p.12).
- ASSUMPTION: Adopt 11.2 mm/s RMS (p.15) for 2-vane CT3240 (p.15, p.18) despite BS ISO exclusion and magnetic method (p.15); reason - all tests significantly exceed it (p.15, p.16).
- ASSUMPTION: Treat 13-20 bar.g peaks (p.19) comparatively as slam risk; reason - pipe/gasket rating not stated yet gaskets failed (p.18), to be confirmed by CRT.
- ASSUMPTION: Use fixed 48 Hz parallel level control from Lock 50 (p.13) with 30 s ramp (p.7) and qualitative poor-anchorage evidence (p.15, p.17); reason - setpoints/torques/grout not given.

QA correction: Values labelled kWh/100m3 in Table 3 (p.12) are numerically kWh/ML (off by 10x). Corrected to kWh/ML in this memo (e.g., S1-48-K120 304.9 kWh/ML, F1P50K120 310.8 kWh/ML).

## Model Calibration

Steady simulator vs audit/SCADA. Base run CAL-2P48-K170.

| Test | Measured (p.12) | Simulated (run) | Residual | Note |
|---|---|---|---|---|
| Single 50 Hz | 199 l/s P1 (p.12 EN-01) and 201 l/s P2 (p.12 EN-04) | CAL-1P50-K120: 203.1 l/s at TDH 78.19 m, 218.6 kW electric | 2.1% | K120 (p.11) reproduces single 50 Hz; clean CLEAN-1P50 227.6 l/s at 75.73 m overpredicts ~13.8%, proving anomaly |
| Single 48 Hz normal | 168 l/s both P1/P2 (p.12 EN-02/EN-05), 187.5 kW P1 and 179.0 kW P2 (p.12) | CAL-1P48: 175.9 l/s at 76.71 m, 185.8 kW | 4.7% | K120 + 0.96 speed (48 Hz p.13) within 5%. Re-run S1-48-K120: 172.3 l/s at 76.54 m 189.2 kW |
| Single 45 Hz | 118 l/s both (p.12 EN-03/EN-06), 137.5/133.0 kW (p.12) | CAL-1P45: 127.7 l/s at 74.59 m, 140.5 kW | 8.2% | Larger residual reflects left-of-BEP fall to 62-64% string (p.12) |
| Two-pump 48 Hz normal | 266 l/s (P1) and 267 l/s (P2) total (p.12 EN-07/08), 170.0/163.5 kW (p.12), 347.6 avg (p.12) | CAL-2P48-K170: 270.6 l/s total, 135.3 l/s per pump at 85.03 m, 316.7 kW total | 1.7% | Base run; K170 needed dual because loss scales with square of 3602 m flow (p.7); K120 alone gives 284.4 l/s (CAL-2P48) +6.9% high, proving flow-dependent anomaly |
| Two-pump 50 Hz | 310 l/s total (p.12 EN-09), 192-201 kW per pump (p.12), 352.2 avg (p.12) | CAL-2P50: 328.8 l/s total, 164.4 l/s per pump at 87.54 m, 396.3 kW total | 6.1% | K120 overpredicts dual 50 Hz, anomaly grows with flow; 50 Hz dual less efficient than 48 Hz (p.13) |
| Two-pump 45 Hz | 191 l/s total (p.12 EN-10), 122-126 kW per pump (p.12), 360.7 worst (p.12) | CAL-2P45: 205.8 l/s total, 102.9 l/s per pump at 78.35 m, 222.0 kW total | 7.7% | 51% rated per pump deep left of POR 70-120% (p.14); confirms 48 Hz optimum (p.13) |
| Clean-pipe counterfactual | 199-201 l/s single 50 Hz (p.12) and 168 l/s single 48 Hz (p.12) | CLEAN-1P50: 227.6 l/s at 75.73 m clean and HYP-CLEAN-1P48: 184.9 l/s at 74.57 m clean | 13.8% | Ranking: K120-170 residual 1-5% beats clean 13-14%; diagnosis excess system loss not pump wear |

Unexplained loss: +6 m at 300 l/s (p.11) = 224 mm orifice (p.11). Penalty +2.14 m single (74.57 m HYP-CLEAN-1P48 to 76.71 m CAL-1P48) and +5.76 m dual (79.27 m HYP-CLEAN-2P48 to 85.03 m CAL-2P48-K170), gain ~58.3 l/s dual if cleaned (328.9 l/s HYP-CLEAN-2P48 vs 270.6 l/s CAL-2P48-K170).

## Capacity Evaluation (table)

| Unit | Limit | Binds at | Evidence | Limits target? |
|---|---|---|---|---|
| Pumps 2x CT3240 535 mm 215 kW (p.7) | Firm (one alone, 48 Hz p.13) ~168 l/s measured (p.12), 175.9 l/s simulated (CAL-1P48); peak dual ~266 l/s (p.12), 270.6 l/s simulated (CAL-2P48-K170) | Single 48 Hz 168 l/s (p.12) and single 50 Hz 199-201 l/s (p.12); dual 48 Hz 266-267 l/s (p.12)=133 l/s per pump | Single in POR (p.15) but dual left of POR 70-120% BEP (p.14, p.15); vibration >11.2 mm/s all tests (p.15) e.g. dual 48 Hz avg 12.6/13.5/16.4 mm/s (p.16); bearings 2000-3000 h vs 50000 h (p.14) with seized/failed seals/emulsified oil/pitting (p.14) and glycol leak (p.14); CAL-2P48-K170 68% rated per pump vs CAL-1P48 88% | Yes |
| Station DN300 + ball checks (p.7, p.18) | Passes firm and peak but creates slam/uneven inflow limiting reliability, not flow | Dual 48 Hz per-branch ~133 l/s (266/2 p.12) and single 168 l/s (p.12) | DN300 branches (p.7) 1.882 m/s at 133 l/s (velocity tool, 300 mm p.7); ball checks poor dynamic response (p.18) <3-5D (p.18); VariSim 13-20 bar.g (p.19) with gasket failures (p.18) | Yes |
| Rising main DN600 3602 m 72 m rise to 127.6 mAOD (p.7) | No burst history (p.7) but excess head binds efficiency and dual flow | Dual 48 Hz 266-267 l/s (p.12) and dual 50 Hz 310 l/s (p.12); single 168 l/s (p.12) | Needs K120 to match SCADA (p.11) despite <25 yr age (p.11); clean HYP-CLEAN-2P48 328.9 l/s vs fouled 270.6 l/s (CAL-2P48-K170) penalty 58.3 l/s; main 0.96 m/s dual fouled (CAL-2P48-K170) and 0.707 m/s at 200 l/s (velocity tool, 600 mm p.7); NRVs at 1270 m and 2410 m unknown (p.7) assumed failed open gives 17.5-20 bar.g (p.19) | Yes |
| Wet well + intakes + bar screens (p.19, p.20) | Hydraulic capacity intact but silt/debris forces left-of-BEP recirculation and wear | All flows; Aug 2019 30% screen loss and 40 tonnes (p.19) with pipework clear (p.19) | Large wide well low velocity/dead spots (p.19) baffles satisfactory (p.20); 78 mm twin-passage (p.18) with 2 events since Nov 2017 (p.18); NPSH ~4 m margin (p.12) volute primed (p.12) so pitting (p.14) is blockage/silt-induced (p.12) not NPSHa | No (bulk), Yes (local) |
| VSDs + Lock 50 control (p.7, p.13) | Delivers Lock 50 levels (p.13) but fixed parallel wastes ~12-17% energy vs sequential single and holds pumps left of POR | Fixed parallel duty/duty at 48 Hz via telemetry (p.13) with 30 s ramp (p.7); tests 50/48/45 Hz (p.12, p.13) | 48 Hz lowest specific (p.13); single 48 Hz 296.0-310.0 vs dual 347.6 (p.12, corrected to kWh/ML); 50 Hz dual 352.2 (p.12) and 45 Hz dual 360.7 worst (p.12); daily 0-23000 m3/day (p.13) suits sequential; magflow not for control (p.13) | Yes |

BEP reference 262 l/s @70 m (p.11). Steady heads: F1P50K120 JH 7.77 bar, S1-48-K120 7.63 bar give no transient warning vs VariSim 13-20 bar.g (p.19).

## Alternatives (table with cost class)

| Option | Expected benefit (run) | Unit | Cost class | Meets / Recommended |
|---|---|---|---|---|
| Find/remove K120-170 anomaly: desilt, CCTV/pressure-log/air-valve survey, lift/test NRV1 1270 m and NRV2 2410 m with bypasses (p.7), check partly-closed/stuck valve, air, partial blockage; re-test vs SCADA (p.11) | ALT-1P48-CLEAN 184.1 l/s at 74.77 m 189.5 kW vs fouled CAL-1P48 175.9 l/s at 76.71 m; dual clean HYP-CLEAN-2P48 328.9 l/s at 79.27 m vs fouled CAL-2P48-K170 270.6 l/s at 85.03 m, gain ~58.3 l/s dual (tests 266-267 l/s dual 48 Hz p.12 and 199-201 l/s single 50 Hz p.12) | Rising main DN600 3602 m (p.7) | $100k-$1M - Investigation: CCTV/logging/lift covers (p.7)+desilt; remediation depends on find. ASSUMPTION: remote buried NRVs and 3602 m DI main (p.7) keep in range if repair needed | Yes / Yes |
| Return to Duty/Assist sequential single-pump at 48 Hz (p.13) with Lock 50 telemetry (p.13) optimised for 0-23000 m3/day (p.13); use flowmeter for control (p.13) instead of fixed parallel duty/duty 48 Hz (p.13) | Single 48 Hz 168 l/s (p.12) at 68-71% string and 296.0-310.0 (p.12, kWh/ML corrected) in POR (p.15) vs dual 48 Hz 266-267 l/s (p.12) at 64-66% and 347.6 (p.12) left of POR (p.15); ALT-1P48-CLEAN 184.1 l/s at 92% rated vs CAL-2P48-K170 135.3 l/s per pump at 68% rated | Control/VSDs 48 Hz (p.7, p.13) | <$100k - Software+setpoints+flowmeter integration; magflow exists but not for control (p.13), MAS711/low-level exists (p.13). ASSUMPTION: no new switchgear | Yes / Yes |
| Re-anchor plinths (cracking/seepage p.15, plate comparable p.15), add motor-end support for vertical base-mounted CT3240 535 mm 215 kW (p.7, p.17), tie manifold and respect critical 6-7 m first <=2.3 m then 4.8 m (p.17) | Addresses >11.2 mm/s all tests (p.15) e.g. dual 48 Hz 266 l/s (p.12) avg X12.6 Y13.5 Z16.4 (p.16) and single 50 Hz 199 l/s (p.12) maxima 37.5 mm/s pump 27.8 mm/s plate (p.16); returns duty to POR 70-120% BEP (p.14) via single CAL-1P48 88% vs dual 68% (CAL-2P48-K170) | Pumps+plinths+DN300 (p.7) | $100k-$1M - Grout/anchors/plinth rebuild, restraint, realign, replace untied adaptors (p.19) move NRVs to 3-5D (p.18). ASSUMPTION: dry-well access; bespoke steelwork for unsupported motor (p.17) | Yes / Yes |
| Replace ball checks (<3-5D p.18) with fast low-slam reflux, tie adaptors, confirm DI rating (no bursts since 1996 p.7) against 17.5 bar.g 2-pump trip, 20 bar.g 1-pump trip, 13 bar.g 30 s ramp (p.19) with NRVs failed open (p.19) | Steady JH 8.34 bar CAL-2P48-K170 gives no warning; VariSim 13-20 bar.g (p.19) explains gasket failures (p.18) with ball poor response (p.18) and residual moments from untied adaptors/bracing (p.19); 30 s ramp (p.7, p.13) alone still 13 bar.g (p.19) | Ball checks+manifold (p.7, p.18) | $100k-$1M - 2x reflux + transient study + possible vessel/air valves on 3602 m main (p.7). ASSUMPTION: 13-20 bar.g (p.19) exceed margin to be confirmed (rating not stated) | Yes / Yes |
| Planned desilt, maintain baffles satisfactory (p.20), manage 78 mm 2-vane debris risk (p.18) with 2 events since Nov 2017 (p.18), bench well to reduce volume/dead spots (p.19, p.20) while keeping buffer/access (p.20); review bar spacing vs blockage (p.20) and 0.3D-0.5D clearance (p.19) | Removes 30% screen loss (p.19) cavitation/blockage cause (p.12) alternative to NPSHa (~4 m margin p.12 with volute primed p.12); DN300 1.882 m/s at 133 l/s vs main 0.96 m/s dual (CAL-2P48-K170) shows well/bellmouth as low-velocity trap | Wet-well intakes/screens (p.19) | <$100k - Regular clean (40 tonnes Aug 2019 p.19), trash, benching Fig12 (p.20). ASSUMPTION: wide well (p.19) with 0.707 m/s in DN600 at 200 l/s deposits between runs | Yes / Yes |
| Counter-example REJECTED: run both at 50 Hz for flow: 310 l/s total (p.12) at 192-201 kW per pump (p.12) | CAL-2P50 328.8 l/s at 87.54 m vs 310 l/s measured (p.12) +6.1%; specific 352.2 (p.12) worse than 347.6 at 48 Hz dual (p.12) and 296.0-310.0 single 48 Hz (p.12); maxima 37.5 mm/s (p.16) exceed 11.2 (p.15) | Control 50 Hz (p.13) | n/a - No capex; higher wear/energy. 224.0 kW input (p.12) exceeds 215 kW motor (p.7) | No / No |
| Counter-example REJECTED: slow both to 45 Hz: 191 l/s total (p.12) at 122-126 kW per pump (p.12) | CAL-2P45 205.8 l/s at 78.35 m, 51% rated per pump vs 191 l/s (p.12); further left of POR (p.15) than 48 Hz dual 68% (CAL-2P48-K170); specific 360.7 worst (p.12) vs 347.6 at 48 Hz dual (p.12) | Control 45 Hz (p.13) | n/a - No capex; proves static-head penalty. Dual 45 Hz worst (p.12) | No / No |

## QA/QC Summary

Checked citations: GEN-01 p.7, PMP-02/CTL-02 p.7 vs p.13 duty conflict, HYD-01 p.11 K120+<25yr, CTL-02/EN p.13 48 Hz optimum +2-pump higher specific, VIB-04/05 p.15 POR+>11.2 mm/s+method, VIB-06 p.16 dual 48 Hz averages, SUR-01 to 03 p.19 17.5/20/13 bar.g + failed-open, WW-01 p.19 30%+40t+clear, PPW-01/02 p.18 ball poor response+<3-5D+gaskets. Checked runs: CAL-1P48, CAL-2P48-K170, ALT-1P48-CLEAN.

| Issue | Severity | Resolution |
|---|---|---|
| Specific-energy unit error: Table 3 labelled kWh/100m3 (p.12) numerically kWh/ML (10x). e.g. 187.5 kW/168 l/s = ~31 kWh/100m3 vs quoted 310.0 (p.12). Simulator ~293 kWh/ML vs quoted 310 inconsistent | major | fixed - Re-run F1P50K120 223.7 kW/200.0 l/s=310.8 kWh/ML matches report numerically; S1-48-K120 304.9 kWh/ML. All values corrected to kWh/ML, ranking unchanged |
| Inconsistent K: K120 singles (CAL-1P50-K120, CAL-1P48 p.11) but K170 dual base CAL-2P48-K170 for 1.7% vs 266-267 l/s (p.12); K120 alone 284.4 l/s +6.9% high. Single K cannot be 120 and 170 | major | fixed - Retained as K120-170 range indicating flow-squared excess on 3602 m DN600 (p.7). Diagnosis flow-dependent anomaly (partly-closed/stuck NRV1 1270 m/NRV2 2410 m p.7, air, blockage) requiring CCTV/logging/lift covers, not single K |
| Surge not verified with steady simulator: steady JH 7.33-8.34 bar (CAL-1P48, CAL-2P48-K170, ALT-1P48-CLEAN) gives no warning; VariSim 17.5/20/13 bar.g (p.19) assuming NRVs failed open (p.19) with rating not stated, gaskets failed (p.18) | major | noted - 13-20 bar.g comparative only. Valve benefit not simulated; conditional on transient study + rating check. Alternative $100k-$1M on unconfirmed rating/operability |
| Vibration limit/method: BS ISO excludes submersibles, WIMES no 2-vane class, magnetic transducer at drive-end+plate (p.15) not bearing-housing 70-120% protocol. 11.2 mm/s (p.15) judgement for CT3240 2-vane (p.7, p.15, p.18) | minor | noted - Retained as ASSUMPTION; large exceedance all tests (p.15, p.16) makes fail robust; 7.1 mm/s would strengthen |
| Motor overload: 224.0 kW input (p.12) vs 215 kW rated (p.7) via Fluke at VSD input (p.9), STRING incl VSD (p.12). F1P50K120 223.7 kW electric shaft 212.5 kW warning | minor | fixed - Flagged overload; avoid 50 Hz single, normal 48 Hz S1-48-K120 189.2 kW within rating; investigate VSD/motor split |
| Flow uncertainty: magflow (p.9) not for control (p.13), calibration and 2018 0-23000 m3/day method (p.13) not stated. Same meter test+SCADA (p.11) | minor | noted - Ranking internally consistent but absolute K/POR uncertain; control using magflow conditional on calibration |
| NPSH ~4 m (p.12) volute primed (p.12) inputs/pressures/depths/GPS (p.9) not tabulated; 30% screens (p.19) skewed/air possible despite bulk margin, pitting (p.14) | minor | noted - Pitting attributed to blockage/silt recirculation, not bulk NPSHa deficit, as hypothesis |
| Pipe supports: critical 6-7 m first <=2.3 m then 4.8 m (p.17) sentence truncated, as-built not verifiable; fixity/torques/grout/cracks and Lock 50 setpoints not given | minor | noted - Qualitative evidence only (cracking/seepage p.15, touch p.17, vertical unsupported p.17, untied/braced p.19); intrusive check high priority |
| Table 4 header Average Min Max (p.16) misordered vs row 10.80 14.30 12.60 where last is average | minor | fixed - Use last value as average (dual 48 Hz X12.6 Y13.5 Z16.4) correctly |

## Recommendations

1. Find and remove excess loss first: desilt, CCTV/pressure-log/air-valve survey of 3602 m DN600 (p.7), lift/test NRV1 1270 m + NRV2 2410 m with bypasses (p.7); re-test vs SCADA (p.11). Expected: recover ~58 l/s dual (HYP-CLEAN-2P48 328.9 l/s vs CAL-2P48-K170 270.6 l/s) and +2-6 m head; resolve high-energy root.
2. Return to sequential Duty/Assist single-pump duty at 48 Hz (p.13) via Lock 50 telemetry (p.13) using calibrated magflow (p.13) for 0-23000 m3/day (p.13). Expected: 68-71% vs 64-66% dual (p.12), 296-310 vs 347.6 kWh/ML (p.12 corrected), in POR (p.15) vs left of POR (p.15), ALT-1P48-CLEAN 92% rated vs 68% dual.
3. Re-anchor/grout plinths, add motor-end support, tie manifold, move NRVs to 3-5D (p.18). Addresses >11.2 mm/s all tests (p.15) up to 37.5 mm/s (p.16) and 2000-3000 h vs 50000 h life (p.14). Intrusive foundation check high priority.
4. Replace ball checks with low-slam reflux + tie/anchor + rating check vs 17.5/20/13 bar.g (p.19) + inspect buried NRVs (p.7). Addresses gasket failures (p.18) with poor dynamic response (p.18). Do not rely on 30 s ramp (p.7) alone - still 13 bar.g (p.19).
5. Planned desilt/benching per Fig12 (p.20), maintain baffles (p.20), debris plan for 78 mm throughlet (p.18), review bar spacing vs blockage (p.20) and 0.3D-0.5D (p.19). Removes 30% loss +40 t driver (p.19).
6. Avoid: both at 50 Hz (352.2 vs 347.6/296-310, overload 224 kW >215 kW, vibration) (p.12, p.7, p.16) and both at 45 Hz (360.7 worst, 51% rated) (p.12).

## Limitations

- Raw suction/delivery pressures, wet-well depths, GPS elevations (p.9) not tabulated; static 55.5/54.3/127.6 mAOD =72 m (p.7) adopted by ASSUMPTION.
- K120-170 is fitting range, not separated physical loss; roughness/air/valve/blockage not split (p.11).
- Intermediate NRV operability unknown under concrete remote covers (p.7); surge 13-20 bar.g (p.19) assumes failed open (p.19).
- Flowmeter accuracy/ calibration and 2018 volume estimation (p.13) unknown; absolute K/POR/energy uncertain.
- Power split VSD/motor/pump unknown; 224 kW >215 kW (p.12, p.7) overload flag only.
- NPSH ~4 m (p.12) unverifiable; local blockage/skew/air (p.19) possible.
- Vibration 11.2 mm/s (p.15) judgement outside code scope with deviated method (p.15).
- Pipe/gasket rating not stated; 13-20 bar.g (p.19) vs gaskets (p.18) comparative only.
- Lock 50 setpoints, plinth fixity quantities, as-built support spacings (p.17 truncated) not given; designs need intrusive survey.
