# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| 2-pump station flow | p.10 Table 3 | 422 l/s station (2 pumps) (p.10) | 423.7 l/s total, 211.8 l/s per pump, TDH 47.87m | 0.4 | BASE-2P | Design sump 124.9 mNGF (p.9), discharge 168.1 mNGF (p.6); branch K ASSUMPTION 8.0 to represent valves/bends because Total K 1.15/3.99/2.55/3.10 (p.9) image illegible |
| 2-pump input power | p.10 Table 3 + p.11 EDF | 265 kW station (2 pumps) (p.10); EDF pumping ~270 kW, total ~280 kW summer (p.11) | 263.8 kW total, 131.9 kW per pump, spec 172.9 kWh/ML | -0.5 | BASE-2P | Sim 263.8 kW within -0.5% of Xylem and -2.3% of EDF deduction; aligns with predicted load for two pumps (p.11) |
| 3-pump station flow/power | p.10 Table 3 | 634 l/s / 398 kW station (3 pumps) (p.10) | 622.6 l/s total, 207.5 l/s per pump at 392.9 kW total | -1.8 | CHK-3P | Same BASE-2P parameters with 3rd pump; manifold 750mm (p.6) velocity 1.41 m/s sim |
| 1-pump duty | p.10 Table 3 | 214 l/s / 133 kW (1 pump) 172 kWh/1000m3 (p.10) | 214.7 l/s at 132.4 kW, 171.4 kWh/ML, branch 3.04 m/s | 0.3 | CHK-1P | Single-pump sim matches; specific energy 171.4 vs 172 (p.10) -0.3% |
| Specific energy | p.10 Table 3 + p.11 | Specific energy 174 kWh/1000m3 2- or 3-pump (p.10, p.11) | 172.9 kWh/ML base; CHK-2P-LOW 174.9, CHK-2P-HIGH 170.4 | -0.6 | BASE-2P | Sim 172.9 (BASE-2P), 175.3 (CHK-3P), 174.9 low-level, 170.4 high-level bracket report; level range 124.2-125.8 mNGF (p.6) |
