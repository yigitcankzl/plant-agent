# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| P1 only 50 Hz | p.12 Table 3 | 199 l/s P1 only 50 Hz (p.12) | 201.7 l/s, TDH 78.58 m (TRY-A-1P50) | 1.4 | TRY-A-1P50 | Curve [[0,105],[150,88],[200,80],[262,70],[320,55]] (ASSUMPTION: fitted to BEP 262 l/s @70 m p.11 and test duties) + 3602 m x 600 mm C120 minor_k 120 (p.7 p.11) reproduces +6 m at 300 l/s (p.11) |
| Single-pump 48 Hz | p.12 Table 3 | 168 l/s P1 only 48 Hz (p.12); 168 l/s P2 only 48 Hz (p.12) | 171.7 l/s, TDH 76.85 m, 194.6 kW (TRY-A-1P48) | 2.2 | TRY-A-1P48 | Normal frequency 48 Hz (p.7 p.13); speed 0.96 (ASSUMPTION: 48/50) |
| Single-pump 45 Hz | p.12 Table 3 | 118 l/s single 45 Hz (p.12) | 107.9 l/s (TRY-A-1P45) | -8.6 | TRY-A-1P45 | Low-speed underprediction indicates steeper low-flow curve or VSD/meter uncertainty; SCADA corroborates tests (p.11) |
| Both pumps 50 Hz | p.12 Table 3 | 310 l/s both pumps 50 Hz (p.12) | 311.7 l/s total, 155.9 l/s per pump (TRY-A-2P50) | 0.5 | TRY-A-2P50 | Excellent 2-pump high-flow match validates minor_k 120 fouled main |
| Both pumps 48 Hz normal duty/duty | p.12 Table 3 | 266 l/s (P1 meter) / 267 l/s (P2 meter) both 48 Hz normal (p.12) | 259.8 l/s total (BASE-CAL); TRY-A-2P48 259.8 l/s | -2.3 | BASE-CAL | Calibrated base BASE-CAL: 259.8 l/s total, 129.9 l/s per pump, TDH 82.64 m, manifold 8.22 bar, 316.7 kW total; measured power sum 333.5 kW (170.0+163.5 p.12) within efficiency scatter (string 64-66% p.12) |
| Both 45 Hz + P2 50 Hz check | p.12 Table 3 | 191 l/s both 45 Hz (p.12); 201 l/s P2 only 50 Hz (p.12) | 166.3 l/s total 2x45 Hz (TRY-A-2P45); P2 50 Hz represented by 201.7 l/s (TRY-A-1P50) | -12.9 | TRY-A-2P45 | Systematic low-speed 2-pump underprediction; does not affect 48-50 Hz diagnosis; P2 50 Hz matches TRY-A-1P50 within 0.3% (ASSUMPTION: pumps identical CT3240 535 mm 215 kW p.7) |
