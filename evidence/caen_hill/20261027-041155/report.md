DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum — Caen Hill Pumping Station Audit, Kennet and Avon Canal, UK

## Purpose
Audit the Caen Hill Pumping Station (PS) for reported short bearing and seal life, gasket failures and higher than expected energy use (p.8, p.14, p.18, p.12) (p.8, p.12, p.14, p.18). Using site tests 11 September 2019 (p.9), SCADA data (p.11, p.13), and system description (p.7), diagnose causes (hydraulic, vibration, surge, control), quantify unexplained losses with the simulator, and recommend measures with expected benefit.

## Background
- Facility: Caen Hill PS near Devizes, Wiltshire, UK; purpose to supply water up from Lock 22 to Lock 50 on the Kennet and Avon Canal (p.7).
- Construction: 1996; dry well construction, housing 2 no. Xylem dry well submersible pumps (p.7).
- Pumps: Xylem (Flygt) CT3240 (p.7); 2 pumps; Table 1 Duty Configuration Duty / Assist (p.7); 535 mm impeller (p.7); 215 kW rated motor output (p.7); Variable Speed (Mitsubishi) drives (p.7); 30 s ramp & 48.0 Hz Operating Frequency (p.7).
- Station pipework: 300 mm diameter (p.7); Ball Non-Return Valves (p.7); each pump delivery branch has ball check valves (p.18); each branch has untied flange adaptors (p.19); manifold supported off floor and back wall by fabricated bracing, tied coupling present (p.19).
- Wet well: level 55.5 mAOD (p.7); pump centre line 54.3 mAOD (p.7); Ultrasonic level sensor (p.7); relatively large wide aspect ratio, low velocity and dead spots, solids deposition (p.19); floating trash baffles appear satisfactory (p.20).
- Rising main: 3602 m length (approx 3600 m) (p.7); 600 mm diameter (p.7); Ductile Iron (p.7); Elevation Rise 72 m (p.7); Discharge Level 127.6 mAOD (p.7); comprises 2 no. intermediate discharge points, with in-line NRVs complete with return bypass (p.7).
- Intermediate NRV #1 1270 m from PS (p.7); NRV #2 2410 m from PS (p.7); condition and operational effectiveness not known (p.7); not inspected recently; covered with large area concrete infill covers in remote towpath locations (p.7).
- Burst history: no reports of bursts since construction (p.7).
- Operator issues for investigation (p.8): poor pump reliability, notably bearing life, suspected high vibration (p.8); impeller damage from cavitation, suspected NPSH or poor intake design (p.8); cracks and spalling of pump plinths (p.8); pipework flange leaks (p.8).
- Failure detail Pump 1: seized solid due to failed bearings (p.14); both seals failed, oil into stator housing (p.14); water ingression emulsified oil (p.14); pitting centre of impeller around sleeve/cover possibly cavitation, water into locking assembly (p.14); leaking glycol coolant from top seal (p.14).
- Bearing life: typical 2,000 to 3,000 hours vs design life expectation 50,000 hours (p.14).
- Impeller: 2-vane (2-channel) (p.16); twin passage 78 mm throughlet (p.18); sewage type dry well submersible, generated head up to 85 m (p.17); impact damage present on Pump 2 from AMCO visit (p.11).
- Debris: 2 other occasions since November 2017 debris necessitated reactive removal (p.18); Aug 2019 both intake screens 30% loss due to silt (p.19); circa 40 tonnes silt, brick, concrete rubble and vegetation removed (p.19); pipework inspected clear Aug 2019 (p.19).
- Hydraulics context: performance improved 121 l/s to 169 l/s after return to operation (p.11).

## Design Criteria
| Criterion | Value applied |
|---|---|
| Normal operating speed and control mode | Both pumps in parallel (duty/duty) at fixed manually-set 48.0 Hz with 30 s ramp; start on low level at Lock Flight 50 via telemetry, stop on high level (p.7, p.13) |
| Pump preferred operating range (POR) | 70% to 120% of flow rate at BEP (p.14) |
| Vibration acceptance limit applied | 11.2 mm/s RMS velocity as reasonable acceptance limit for 2-vane pump (p.16) |
| Vibration measurement standard | Generally in accordance with BS ISO 10816 Part 7; WIMES 1.03 covers dry-well submersible pumps (p.15, p.16) |
| NPSH compliance | NPSH available must exceed NPSH required; site calculation shows ~4 m margin (p.12) |
| Intake bellmouth clearance | ANSI/HI 9.8 ideal 0.3D to 0.5D off wet-well floor (D=bellmouth diameter) (p.19) |
| Bearing design life | 50,000 hours design vs observed 2,000 to 3,000 hours (p.14) |
| System duty | Supply Lock 22 to Lock 50; 72 m rise; discharge 127.6 mAOD; 3602 m x 600 mm Ductile Iron (p.7) |
| Energy objective | Minimise wire-to-water specific energy; 48 Hz lower than 50 Hz or 45 Hz, single-pump lower than 2-pump (p.12, p.13) |
| Surge withstand objective | Withstand calculated peaks at PS manifold: 17.5 bar.g (2-pump trip), 20 bar.g (1-pump trip with two running), 13 bar.g (controlled 30 s ramp stop) assuming intermediate NRVs open — for comparison to pipe/fitting rating (p.19) |

Standards use: BS EN 9906:2012 Grade 2B as-new tolerance (p.11); BS ISO 10816-7 guidance (p.15-p.16); WIMES 1.03, 2-vane outside multivane/single-channel definitions (p.16); ANSI/HI 9.8 intake and 0.3D-0.5D clearance (p.19).

## Data and Assumptions
Site testing 11 September 2019 by Arcadis and Samatrix (p.9). Measurements: input power to each drive (Fluke), flow (installed flowmeter), wet-well depth (portable ultrasonic), GPS elevation, suction/delivery pressures (transducers), spot RMS velocity (magnetic accelerometer), dimensions/levels (p.9). Scenarios: P1+P2 parallel, P1 only, P2 only (p.9). Transducer X,Y,Z at drive bearing end just above volute + mounting plate corner (p.15).

Control: on low level pumps start, each ramps to manually set 48 Hz both parallel (duty/duty) fixed speed; on high level both ramp down/stop (p.13). Auto via Lock 50 telemetry (p.13). Flow measured by electromagnetic flowmeter not utilised for control (p.13). Protection: MAS 711 + low-level suction protection (p.13). Central SCADA available (p.13).

Energy Table 3 (p.12) — String Efficiency wire-to-water incl VSD (p.12):
- P1 only 50 Hz: 199 l/s, 224.0 kW, PF 0.92, 69%, 312.7 (p.12)
- P1 only 48 Hz: 168 l/s, 187.5 kW, PF 0.90, 68%, 310.0 (p.12)
- P1 only 45 Hz: 118 l/s, 137.5 kW, PF 0.87, 62%, 323.7 (p.12)
- P2 only 50 Hz: 201 l/s, 214.5 kW, PF 0.90, 73%, 296.4 (p.12)
- P2 only 48 Hz: 168 l/s, 179.0 kW, PF 0.90, 71%, 296.0 (p.12)
- P2 only 45 Hz: 118 l/s, 133.0 kW, PF 0.89, 64%, 313.1 (p.12)
- Both 50 Hz: 310 l/s total, 201.0 kW at P1, 192.0 kW at P2, 66%/69%, 352.2 avg (p.12)
- Both 48 Hz normal: 266 l/s (P1 meter) / 267 l/s (P2 meter) total, 170.0 kW at P1, 163.5 kW at P2, 64%/66%, 347.6 avg (p.12)
- Both 45 Hz: 191 l/s total, 126.0 kW at P1, 122.0 kW at P2, 57%/60%, 360.7 avg (p.12)
- Finding: 48 Hz lowest specific energy vs 50/45 Hz (p.13); parallel duty further left of Q-H, away from BEP (p.13).

BEP: 262 l/s @ 70 m 1-pump, 524 l/s @ 70 m 2-pump (p.11). Curve derate equivalent 0.3 Hz on VSD, still within BS EN 9906:2012 2B (p.11).

Vibration Table 4 11 Sept 2019 (p.16): all rows 8.9–29.4 avg, max to 37.5 mm/s; all exceed 11.2 (p.16). Example P1 50 Hz 199 l/s: X 24.0 Y 20.0 Z 12.0 Mtg 21.2 avg, max to 37.5 (p.16). Conclusion both pumps significantly exceed 11.2 mm/s under all scenarios (p.16). Mount plate similar to pump; floor near plinths noticeable reduction by touch (p.17). Vertical base-anchored, motor unsupported = low stiffness/natural frequency (p.17). Most likely cause poorly anchored installation (p.18).

Transient VariSim model at 48 Hz current setup (p.19). Events: uncontrolled 2-pump trip, uncontrolled 1-pump trip (when two running), controlled 30 s ramp stop (p.19). Simulations both NRVs open and working (p.19). Peaks: 17.5 bar.g 2-pump trip (p.19); 20 bar.g 1-pump trip (p.19); 13 bar.g 30 s ramp (p.19). Qualifier: high transients if intermediate NRVs failed open (p.19). Ball checks poor dynamic, slam risk after trips/stops (p.18). NRVs close to delivery (criterion truncated) (p.18).

Intake: generally conforms, no submergence issue (p.19); exception bellmouth height above floor vs 0.3D-0.5D (p.19); trash baffles satisfactory (p.20); bar spacing trade-off debris vs blockage (p.20).

ASSUMPTIONS (labelled per RFI resolution):
- ASSUMPTION: Normal is both parallel at 48 Hz (duty/duty) with single-pump fallback; Table 1 Duty/Assist (p.7) is standby capability. Reason: explicit Section 6 (p.13) and 2-pump tests (p.12, p.16).
- ASSUMPTION: Assess surge both bounds, adopt NRVs open (failed) as conservative base. Reason: high transients assuming NRVs not operational (p.19).
- ASSUMPTION: Treat 13–20 bar.g (p.19) as high/potentially damaging given gasket failures, pending rating confirmation. Reason: called high/excessive, linked to slam (p.18-p.19).
- ASSUMPTION: Model 3602 m x 600 mm DI with 72 m static and calibrate added loss to +6 m at 300 l/s (≈orifice 224 mm) (p.11, p.7).
- ASSUMPTION: Accept qualitative intake findings (no submergence; clearance too high; large wide well deposition; 30% screen loss; 40 t debris) (p.19) as facts.
- ASSUMPTION: Use BEPs (p.11) and 50/48/45 Hz test flows 118–310 l/s (p.12) with 0.3 Hz derate (p.11) to represent curves.
- ASSUMPTION: Apply 11.2 mm/s RMS limit (p.16); cite energy as Table 3 (p.12); rely on slam+untied+ bracing (p.18-p.19) for NRV spacing (truncated).
- ASSUMPTION: Treat SCADA as corroborating tests (p.11); flowmeter correct for comparison; plinths poorly anchored per most-likely finding and touch-test (p.17-p.18).

## Model Calibration
Pump curve shape fitted ASSUMPTION: [[0,105],[150,88],[200,80],[262,70],[320,55]] anchored to BEP 262 l/s @70 m (p.11). Rising main 3602 m x 600 mm (p.7) C130 ASSUMPTION; document coefficient 120 (p.11) applied as minor_k 120 units unstated. Speed 0.96 ASSUMPTION for 48/50 Hz (p.7). Pumps identical CT3240 535 mm 215 kW ASSUMPTION (p.7).

| Test (p.12) | Measured (p.12) | Run | Simulated | Residual |
|---|---|---|---|---|
| P1 only 50 Hz | 199 l/s | TRY-A-1P50 | 201.7 l/s, TDH 78.58 m | +1.4% |
| Single-pump 48 Hz | 168 l/s P1, 168 l/s P2 | TRY-A-1P48 | 171.7 l/s, TDH 76.85 m, 194.6 kW | +2.2% |
| Single-pump 45 Hz | 118 l/s | TRY-A-1P45 | 107.9 l/s | -8.6% — low-speed underprediction, VSD/meter uncertainty; SCADA corroborates tests (p.11) |
| Both 50 Hz | 310 l/s | TRY-A-2P50 | 311.7 l/s total, 155.9 l/s per pump | +0.5% — validates minor_k 120 fouled main |
| Both 48 Hz normal duty/duty | 266 / 267 l/s | BASE-CAL | 259.8 l/s total, 129.9 l/s per pump, TDH 82.64 m, manifold 8.22 bar, 316.7 kW total; measured power sum 333.5 kW (170.0+163.5) (p.12) within 64–66% string scatter (p.12) | -2.3% |
| Both 45 Hz + P2 50 Hz check | 191 l/s both 45 Hz; 201 l/s P2 50 Hz | TRY-A-2P45 / TRY-A-1P50 | 166.3 l/s total 2×45 Hz; P2 50 Hz 201.7 l/s | -12.9% 2×45 Hz; P2 50 Hz within 0.3% |

Corrected consistent-efficiency runs: S-1P48-C130K120 168.6 l/s TDH 76.35 m 195.5 kW; BASE-2P48-FIX 245.6 l/s total 122.8 l/s per pump TDH 80.89 m 301.7 kW manifold 8.05 bar; C-2P50-C130K120 304.8 l/s vs 310 l/s (p.12). Low-speed misfit acknowledged; conclusions limited to 48–50 Hz.

Unexplained loss: additional coefficient 120 needed to match SCADA pressures (p.11); +6 m at 300 l/s (p.11) = orifice 224 mm (p.11); velocity 1.061 m/s in 600 mm vs 7.613 m/s in 224 mm at 300 l/s; <25 yr main (p.11) so not roughness alone. Station 300 mm/manifold/meter/valves (p.7) lumped in MAIN minor_k — ASSUMPTION.

## Capacity Evaluation
| Unit | Limit | Binds at / Evidence | Limits target? |
|---|---|---|---|
| Pumps P1+P2 CT3240 | Run back left of curve in parallel, away from BEP (p.13) | Normal 266 l/s total ≈133 l/s per pump (p.12), ~51% BEP 262 l/s (p.11) ASSUMPTION arithmetic, outside POR 70–120% (p.14); single inside POR, dual left/outside (p.15); TRY-A-2P48 129.9 l/s per pump vs BEP 262 l/s @70 m (p.11); vibration >11.2 mm/s all duties (p.16); bearing 2000–3000 h vs 50000 h (p.14) | Yes |
| Rising main 3602 m x 600 mm DI | Unexplained loss coefficient 120 (p.11) | +6 m at 300 l/s (p.11); BASE-CAL TDH 82.64 m 2-pump vs 76.85 m 1-pump; orifice 224 mm equivalence (p.11) | Yes |
| Wet well / screens / bellmouths | Deposition + debris ingress, skewed flow risk (p.19) | 30% screen loss, ~40 t removed Aug 2019 (p.19); 78 mm twin throughlet (p.18); debris 2× since Nov 2017 (p.18); bellmouth too high vs 0.3D–0.5D (p.19); large wide well dead spots (p.19); 121 to 169 l/s recovery after unblock (p.11); pitting despite ~4 m NPSH margin (p.12) | Yes |
| Delivery branches / manifold / NRVs | Check-valve slam + unknown intermediate NRVs 1270 m, 2410 m (p.7) | Peaks 17.5 / 20 / 13 bar.g (p.19) assuming NRVs open (p.19); ball checks poor dynamic (p.18); untied adaptors + braced manifold with tied coupling (p.19); gasket failures (p.18); NRV status unknown under concrete covers (p.7) | Yes |
| Control / flowmeter / SCADA | Fixed duty/duty forces off-BEP inefficient operation | Both parallel fixed 48 Hz 30 s ramp, start low stop high via Lock 50 telemetry (p.7, p.13); meter not for control (p.13); 48 Hz lowest energy but 2-pump 347.6 vs 1-pump 296–310 kWh/1000 m3 (p.12); dual points further left with speed reduction (p.13); Duty/Assist Table 1 (p.7) vs duty/duty text (p.13) ASSUMPTION normal duty/duty | Yes |
| Pump plinths / mountings | Excessive vibration all scenarios incl 48 Hz normal | Averages 8.9–29.4 mm/s, maxima to 37.5 mm/s (p.16) vs 11.2 mm/s (p.16) for 2-vane (p.16) per BS ISO 10816-7/WIMES 1.03 (p.15-p.16); mount comparable to pump (p.16); floor lower by touch (p.17); vertical base-anchored motor unsupported low stiffness (p.17); up to 85 m head 2-vane thrust (p.17); most likely poorly anchored (p.18) | Yes |

Findings summary:
- Hydraulic parallel off-POR: ~51% BEP ASSUMPTION; string 64–66% vs 68–71% single at 48 Hz (p.12); S-1P48-C130K120 168.6 l/s TDH 76.35 m 195.5 kW vs BASE-2P48-FIX 245.6 l/s 122.8 l/s per pump TDH 80.89 m.
- Hydraulic loss: +6 m at 300 l/s (p.11); S-1P48-C130K120 168.6 vs ALT-1P48-CLEAN2 180.9 l/s; BASE-2P48-FIX 245.6 l/s; C-2P50-C130K120 304.8 vs 310 l/s (p.12).
- Vibration/mechanical: >11.2 mm/s ASSUMPTION for 2-vane (p.16); bearing/seal/glycol/emulsified/seizure (p.14); plinth cracks + flange leaks (p.8).
- Surge/gaskets: 20/17.5/13 bar.g VariSim (p.19); steady BASE-2P48-FIX 8.05 bar; rating not stated.
- Cavitation/debris not NPSH: ~4 m margin (p.12) so not suction head; blockage/siltation alternative (p.12); centre pitting (p.14) despite margin.
- Energy/control: 347.6 (2×48 Hz) vs 310.0/296.0 (1×48 Hz) (p.12); 48 Hz optimum (p.13); +12% vs P1-only and +17% vs P2-only ASSUMPTION arithmetic (p.12).

## Alternatives
| Option | Run | Result / Benefit | Cost class / Basis | Rec.? | Meets target? |
|---|---|---|---|---|---|
| Normal single-pump duty/assist at 48 Hz instead of fixed duty/duty | TRY-A-1P48 / S-1P48-C130K120 | TRY-A-1P48: 171.7 l/s at 194.6 kW TDH 76.85 m vs BASE-CAL 259.8 l/s at 316.7 kW; moves each running pump ~133 l/s (~51% BEP outside POR p.11 p.14 p.16) to ~172 l/s inside POR; measured 296–310 (1-pump) vs 347.6 (2-pump) (p.12) | <$100k — ASSUMPTION labour only, telemetry setpoint + instruction, existing VSD+SCADA (p.7, p.13) | Yes | Yes |
| Investigate/remove 6 m at 300 l/s restriction + prove intermediate NRVs | ALT-1P48-CLEAN / ALT-1P48-CLEAN2 | ALT-1P48-CLEAN minor_k 20 ASSUMPTION clean: 181.8 vs 171.7 l/s (+10.1); 299.3 vs 259.8 l/s 2-pump (+39.5); TDH 76.85 to 75.3 m; calibrates orifice 224 mm 7.613 vs 1.061 m/s in 600 mm (p.11); ALT-1P48-CLEAN2 180.9 vs 168.6 l/s hypothetical pending inspection | $100k–$1M — ASSUMPTION CCTV/pressure survey + lift covers at 1270/2410 m + clean/flush (p.7), no main replacement | Yes | Yes |
| Scheduled wet-well/screen cleaning + benching review (retain debris buffer) | ALT-1P48-CLEAN | No steady head change modelled; protects 4 m NPSH margin (p.12), prevents skewed/air-inflow from 30% loss (p.19); addresses pitting despite sufficiency and 121 to 169 l/s recovery (p.11); supports ALT flows | $100k–$1M — ASSUMPTION clean opex + minor civils after 40 t removal (p.19); large well (p.19-p.20) | Yes | Yes |
| Replace ball checks, tie manifold, re-anchor pumps/plinths; retain 30 s ramp | BASE-CAL / BASE-2P48-FIX | Steady unchanged (BASE-CAL 8.22 bar; BASE-2P48-FIX 8.05 bar); targets VariSim 17.5 / 20 / 13 bar.g (p.19) and slam (p.18) linked to gaskets (p.18); targets >11.2 mm/s (p.16) and 2000–3000 vs 50000 h (p.14); plinth-floor touch difference, unsupported motor (p.17) | $100k–$1M — ASSUMPTION exchange 2×300 mm ball checks (p.7, p.18), tie adaptors, re-anchor/motor support (p.17-p.19), no main works | Yes | Yes |
| Flow/level-based alternating VSD control, keep 48 Hz sweet-spot | ALT-1P50-1P | ALT-1P50-1P 206.8 l/s at 240.7 kW (323.3 kWh/ML); 48 Hz lowest vs 50/45 Hz (p.13); 45 Hz duties 118 single /191 dual (p.12) with TRY-A-2P45 166.3 l/s low-speed inefficiency; avoids fixed duty/duty (p.13), enables rotation | <$100k — ASSUMPTION controls integration only, existing EM meter (p.13)+SCADA+Mitsubishi VSDs (p.7) | No — further study | Yes |

## QA/QC Summary
Checked citations: HYD-02 6 m at 300 l/s (p.11); HYD-08 BEP 262 @70 m (p.11); EN-02 P1 48 Hz 168 l/s 187.5 kW 68% 310.0 (p.12); EN-08 Both 48 Hz 266 l/s 170 kW 64% 347.6 (p.12); VIB-06 >11.2 all scenarios (p.16); SUR-04/05/06 17.5/20/13 bar.g (p.19); RM-01 3602 m x 600 mm DI 72 m 127.6 mAOD (p.7); FAIL-04 2000–3000 vs 50000 h (p.14). Checked runs: BASE-CAL, TRY-A-1P48, TRY-A-2P48, ALT-1P48-CLEAN.

| Issue | Severity | Action |
|---|---|---|
| Energy inconsistency: BASE-CAL vs TRY-A-2P48 same 259.8 l/s/82.64 m but 316.7 vs 346.4 kW; measured sum 333.5 kW (170.0+163.5) (p.12) between. Efficiency 0.7 vs 0.64 drives difference; benefit uncertain ~30 kW (~9%) | Major | Fixed: rejected low BASE-CAL 316.7 kW; use BASE-2P48-FIX 245.6 l/s 301.7 kW, S-1P48-C130K120 168.6 l/s 195.5 kW; quote measured specific energies, simulator comparative with efficiency ASSUMPTION |
| Unsupported curve/roughness: curve shape + C130 invented, 120 used for both C and minor_k 120 (p.11 units unstated); residuals -8.6% single 45 Hz, -12.9% dual 45 Hz | Major | Fixed: labelled rated 262 @70 m (p.11), shape fitted ASSUMPTION, C130 ASSUMPTION, minor_k 120; C-2P50-C130K120 304.8 vs 310 l/s (p.12) good at 50 Hz; limit conclusions to 48–50 Hz |
| Missed units/unverified cleaning: all extra loss lumped on 600 mm main; station 300 mm/manifold/meter/valves (p.7) not separate; ALT minor_k 20 clean no basis; +10.1 / +39.5 l/s hypothetical | Major | Fixed: admit lumping; ALT-1P48-CLEAN2 minor_k 20 ASSUMPTION clean, 180.9 vs 168.6 l/s hypothetical pending inspection; fouling vs valve/meter not distinguished |
| Surge not verified: no transient re-run with slow-closing times; steady 8.22 bar cannot verify slam; rating unknown; NRV open/working bound unresolved | Major | Fixed: no transient re-run; remedy justified only by VariSim 13–20 bar.g (p.19)+slam (p.18)+gaskets (p.18); link plausible not proven |
| Vibration fix unverified: no stiffness/frequency calc, no post-fix prediction; touch-test qualitative; 11.2 mm/s for 2-vane ASSUMPTION (p.16); off-POR ~51% BEP ASSUMPTION + 2-vane thrust to 85 m (p.17) not excluded | Major | Fixed: no calc/prediction; 11.2 reasonable ASSUMPTION (p.16); retain off-POR and thrust contributors; anchoring most likely per p.18 not proven |
| Control vs demand not proven: volume/time proof unavailable Fig7 graph only (p.13); selective +12%; firm capacity Duty/Assist (p.7) vs duty/duty (p.13) unstated | Major | Fixed: corrected +12% vs P1 and +17% vs P2 (p.12) range; Duty/Assist standby, normal duty/duty; single-pump firm=0 with one out, dual non-firm; level check required |
| Vibration table mis-parse: 37.50 under Min cannot be Min if 24.0 Average (p.16) | Minor | Fixed: cite ranges/maxima only, not exact upper average |
| Editorial: energy header kWh/100 0 m3 truncated (p.12); Table 5 vs Table 3 cross-ref error (p.13); NRV 3-or-5 diameters truncated (p.18) | Minor | Noted: kWh/1000 m3 inferred verified 224 kW/199 l/s=312.7; flag ambiguities |

## Recommendations
1. Adopt single-pump duty/assist normal at 48 Hz (TRY-A-1P48 / S-1P48-C130K120), retain standby, subject to Lock 50 level/volume check Fig7 (p.13). Benefit: inside POR (p.14-p.15), measured 296–310 vs 347.6 (p.12) (+12% vs P1, +17% vs P2 ASSUMPTION).
2. Investigate 6 m loss (p.11): CCTV/pressure survey, lift covers/prove intermediate NRVs at 1270/2410 m (p.7), clean/flush. Benefit hypothetical ALT-1P48-CLEAN2 180.9 vs 168.6 l/s; 2-pump 299.3 vs 259.8 l/s — verify before claiming.
3. Scheduled wet-well/screen cleaning + benching review (p.19-p.20). Benefit: protect ~4 m NPSH margin (p.12), prevent 30% loss (p.19), address 121 to 169 l/s blockage effect (p.11) and centre pitting (p.14) despite NPSH sufficiency.
4. Replace ball checks with slow-closing, tie adaptors, re-anchor plinths/motor support, retain 30 s ramp (p.7). Benefit: target 17.5/20/13 bar.g VariSim peaks (p.19), slam (p.18), gasket leaks (p.18), and >11.2 mm/s vibration (p.16) with 2000–3000 vs 50000 h life (p.14). Requires surge review and vibration re-test; steady 8.05–8.22 bar unchanged.
5. Implement flow/level-based alternating VSD control using EM meter+SCADA (p.13) at 48 Hz sweet-spot (p.13), not fixed duty/duty (p.13). Further study for demand/standby rotation.

## Limitations
- Pipe/fitting/gasket rating not stated (p.7-p.19); 13–20 bar.g (p.19) judged high ASSUMPTION only; gasket link plausible not proven.
- Intermediate NRV status unknown under concrete covers (p.7); open vs working bound unresolved (p.19).
- System curve inputs: coefficient 120 units unstated (p.11); roughness/elevation sheet Fig6 not legible; pump curve shape and C130 ASSUMPTION; low-speed misfit -8.6% to -12.9%; use 48–50 Hz only.
- Intake: bellmouth D, clearance, well dimensions, level range, suction/discharge pressures not tabulated; rely on qualitative conformance/no submergence/clearance too high (p.19) and 30%/40 t observations (p.19).
- SCADA pressures/daily volumes Fig7 graph only (p.13), meter calibration, VSD efficiencies, plinth anchorage detail not seen (p.17) — flowmeter correct ASSUMPTION, poor anchoring most-likely (p.18) not proven.
- Vibration 11.2 mm/s for 2-vane reasonable ASSUMPTION outside WIMES definitions (p.16); Table 4 column order ambiguous (p.16); energy header truncated, Table 5/3 cross-ref error (p.13), NRV spacing truncated (p.18).
