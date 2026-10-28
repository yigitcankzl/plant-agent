# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| Pump rated-point basis | p.29 | 4583 gpm at 210 ft head pump design point (p.29) | 4583 gpm at 210 ft rated in run CAL-BASE-2P-RICH; operating 5943.2 gpm at 162.28 ft TDH (130% of rated, tool warning) | 0 | CAL-BASE-2P-RICH | Model uses Table 3-1 rated point; Appendix B curves not in available pages; no silent curve invention. |
| Hydraulic boundary levels | p.29 | Wet-well 119.50/114.00; Richmond high point 253.00; Henrico high point 268.00; lifts 133.50/139.00 Richmond and 148.50/154.00 Henrico (p.29) | WW 114.00 RICH 253.00 in CAL-BASE-2P-RICH; WW 114.00 HEN 268.00 in CAP-2P-HEN-DUTY | 0 | CAL-BASE-2P-RICH | Units ASSUMED feet by arithmetic closure 253.00-119.50=133.50 etc (RFI-09); reservoirs set same in runs. |
| Field-test availability check | pp.9,28,29,31,38,39,40,41,56 | No field pressure/flow test data on available pages [9,28,29,31,38,39,40,41,56]; search MGD/field-test returns only Tables 3-3/3-4 criteria | n/a — calibration to design point and boundaries only | 0 | CAL-BASE-2P-RICH | No residual calculable; model is design-basis (WaterGEMS/Hammer per p.28) with C=120 steady (p.29) and geometry HDPE 37.76-in 10755 ft FRP 49.11-in 36070 ft DI 49.04-in 2435 ft (p.29). |
