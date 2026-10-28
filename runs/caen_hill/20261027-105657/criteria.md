# Step 1 - Scope and design criteria

**Question:** Audit Caen Hill PS: diagnose short bearing/seal life, gasket failures and high energy use from site tests, SCADA and system description (hydraulic, vibration, surge, control), quantify unexplained losses with simulator, recommend measures with expected benefit.

## Definitions
| term | definition | source |
|---|---|---|
| Firm capacity | Capacity with largest unit out of service = one pump running alone | Engineering rules + p.7 (2 pumps duty/assist) |
| STRING efficiency | Overall wire-to-water efficiency including VSD, derived from measured VSD input power | p.12 Table 3 note |
| Check valve slam | Check-valve slam pressure spike after pump trip/stop due to poor dynamic response of ball check valves | p.18 |

## Criteria
| name | value | source |
|---|---|---|
| Duty philosophy - normal operation | 2x pumps duty/assist installed but operated duty/duty in parallel at fixed 48 Hz via Lock 50 level telemetry; 30 s VSD ramp | p.7, p.13 |
| Operating speed for assessment | 48 Hz normal running frequency; test points at 50, 48, 45 Hz | p.7, p.13 |
| Preferred Operating Region (POR) | 70% to 120% of flow at BEP - vibration lowest inside POR | p.14 |
| Vibration acceptance limit adopted | 11.2 mm/s RMS velocity (WIMES 1.03 single-channel/screw pump limit applied as reasonable limit to 2-channel CT3240); BS ISO 10816-7 damage risk >9.5 mm/s noted but submersibles excluded from scope | p.15 |
| Vibration measurement basis | Generally per BS ISO 10816 Part 7, magnetic transducer at drive bearing end (above volute) X/Y/Z + mounting plate corner, 11 Sept 2019 | p.15 |
| NPSH adequacy criterion | NPSHa must exceed NPSHr with margin; report calculates ~4 m margin, volute below canal level and fully primed | p.12 |
| Intake submergence / bellmouth clearance | ANSI/HI 9.8 ideal 0.3D to 0.5D bellmouth above wet-well floor (D = bellmouth diameter) | p.19 |
| Energy performance metric | String (wire-to-water including VSD) efficiency and specific energy in kWh/100 m3 from VSD input power, flow and pressure at audit | p.12 |
| Energy ranking observed | 48 Hz lower specific energy than 50 Hz or 45 Hz; 2-pump parallel higher specific energy / lower efficiency than single-pump due to left-of-BEP operation | p.13 |
| Bearing life expectation | Design life 50,000 hours vs observed 2,000-3,000 hours - short life indicative of excessive vibration | p.14 |
| Surge analysis basis | VariSim basic transient model at 48 Hz: uncontrolled 2-pump trip, uncontrolled 1-pump trip (two running), controlled stop 30 s ramp; with intermediate NRVs failed open and working | p.19 |
| Pipework installation criteria | Xylem install: critical pipework length 6-7 m, first support <=2.3 m, subsequent supports at 4.8 m; NRVs should achieve 3 or 5 diameters from pump delivery; supports/anchors to avoid residual forces/moments | p.17 |

## Standards
| name | use |
|---|---|
| BS ISO 10816-7 | Vibration measurement/evaluation guidance; 9.5 mm/s RMS damage risk noted, submersibles excluded |
| WIMES 1.03 cl.7.2.3 / 7.1.1 | Dry-well submersible vibration testing: 70-120% BEP, 7.1 mm/s multivane/vortex, 11.2 mm/s single-channel/screw - 11.2 applied to 2-vane as reasonable limit |
| ANSI/HI 9.8 | Pump intake design - bellmouth-to-floor 0.3D-0.5D to limit silt/debris deposition |

## Units on the flow path
- Wet well with floating trash baffles and intake bar screens
- Pump intake bellmouths and intake screens (30% silt loss observed)
- Pump suction pipework to 2x Xylem Flygt CT3240 dry-well submersible pumps P1/P2 (535 mm, 215 kW, vertical base-mounted)
- Mitsubishi VSDs with 30 s ramp, MAS 711 relay and low-level suction protection
- Pump delivery branches DN300 with ball-type non-return/check valves (<3-5D from pump)
- Untied flange adaptors per branch
- Common discharge manifold on floor/back-wall bracing supports with tied coupling
- On-site electromagnetic flowmeter (indication only) + suction/delivery pressure transducers + ultrasonic wet-well sensor
- Rising main DN600 ductile iron ~3602 m to 127.6 mAOD (72 m rise)
- Intermediate discharge point 1 with in-line NRV1 + return bypass at 1270 m
- Intermediate discharge point 2 with in-line NRV2 + return bypass at 2410 m
- Discharge to Lock Flight 50 with level telemetry to PS SCADA for auto start/stop
