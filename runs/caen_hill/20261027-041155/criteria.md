# Step 1 - Scope and design criteria

**Question:** Audit the Caen Hill pumping station. The operator reports short bearing and seal life, gasket failures and higher than expected energy use. Using the site tests, SCADA data and system description, diagnose the causes (hydraulic, vibration, surge, control), quantify any unexplained losses with the simulator, and recommend measures with their expected benefit.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| Normal operating speed and control mode | Both pumps in parallel (duty/duty) at fixed manually-set 48.0 Hz with 30 s ramp; start on low level at Lock Flight 50 via telemetry, stop on high level (p.7, p.13) | p.7 Table 1; p.13 Section 6 |
| Pump preferred operating range (POR) | 70% to 120% of flow rate at best efficiency point (BEP) (p.14) | p.14 Section 7.1 |
| Vibration acceptance limit applied | 11.2 mm/s RMS velocity as reasonable acceptance limit for 2-vane pump (p.16) | p.16 Section 7.3 |
| Vibration measurement standard | Generally in accordance with BS ISO 10816 Part 7; WIMES 1.03 covers dry-well submersible pumps (p.15, p.16) | p.15 Section 7.2; p.16 Section 7.3 |
| NPSH compliance | NPSH available must exceed NPSH required; site calculation shows ~4 m margin (p.12) | p.12 Section 4 |
| Intake bellmouth clearance standard | ANSI/HI 9.8 ideal bellmouth elevation 0.3D to 0.5D off wet-well floor (D=bellmouth diameter) (p.19) | p.19 Section 8.4 |
| Bearing design life expectation | 50,000 hours design life vs observed 2,000 to 3,000 hours typical (p.14) | p.14 Section 7.1 |
| System duty - static lift and discharge level | Supply Lock 22 to Lock 50; elevation rise 72 m; discharge level 127.6 mAOD; rising main 3602 m x 600 mm Ductile Iron (p.7) | p.7 Table 2 |
| Energy efficiency objective | Minimise wire-to-water specific energy; 48 Hz lower than 50 Hz or 45 Hz, single-pump lower than 2-pump (p.12, p.13) | p.12 Table 3; p.13 Section 5 |
| Surge withstand objective | Withstand calculated peaks at PS manifold: 17.5 bar.g (2-pump trip), 20 bar.g (1-pump trip with two running), 13 bar.g (controlled 30 s ramp stop) assuming intermediate NRVs open - for comparison to pipe/fitting rating (p.19) | p.19 Section 8.3 Table 5 |

## Standards
_none_

## Units on the flow path
- Wet well (large wide volume; 55.5 mAOD level; low-level suction protection) (p.7, p.13)
- Floating trash baffles + intake screens/bar screens (30% loss observed) (p.19-p.20)
- Intake bellmouths (height above floor too high per ANSI/HI 9.8; pump centre 54.3 mAOD) (p.7, p.19)
- Inlet pipework to pumps (inspected clear Aug 2019) (p.19)
- Pump 1 - Xylem Flygt CT3240 535 mm, 215 kW, Mitsubishi VSD (p.7)
- Pump 2 - Xylem Flygt CT3240 535 mm, 215 kW, Mitsubishi VSD (p.7)
- Pump delivery branches 300 mm with ball check (non-return) valves close to delivery + untied flange adaptors (p.7, p.18-p.19)
- Common manifold with tied coupling + fabricated floor/wall bracing supports (p.19)
- Electromagnetic flowmeter (measurement only, not for control) (p.13)
- Rising main 3602 m x 600 mm Ductile Iron to 127.6 mAOD (72 m rise) (p.7)
- Intermediate discharge point + in-line NRV #1 with bypass at 1270 m (status unknown) (p.7)
- Intermediate discharge point + in-line NRV #2 with bypass at 2410 m (status unknown) (p.7)
- Discharge at Lock Flight 50 with level telemetry to PS for auto start/stop (p.13)
- MAS 711 relay protection + CRT central SCADA (p.13)
