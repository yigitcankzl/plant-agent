# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| Two-pump firm test | p.3 2016 Rettew inspection | ~3,200 gpm (4.6 MGD) with two pumps operating (p.3 DR-13) | 3231.7 gpm (4.654 MGD) total_pumped_gpm in BASE-2P; TDH 123.91 ft; P_FM 3231.7 gpm at 3.97 fps | 0.99 | BASE-2P | Validates 14,505-ft equiv (p.10) + C=85/120 + 17.25-in curve (p.13) basis; residual within field-test tolerance |
| Three-pump test | p.4 1992 field test | ~3,200 gpm (4.6 MGD) with all three pumps operating 6/19/1992 (p.4 DR-22) | 3380.2 gpm (4.867 MGD) total_pumped_gpm in BASE-3P; TDH 132.12 ft | 5.63 | BASE-3P | Third pump adds only ~148 gpm vs BASE-2P (3380.2-3231.7); confirms steep system curve; p.3 vs p.4 pump-count conflict treated as dated observations per RFI |
| System-head table check | p.13 system-head table | 119.78 ft system head at 3,200 gpm 2-pump; 67.25 ft at 2,000 gpm 2-pump (p.13 DR-32); static 29.35 ft (p.10 DR-26) | 123.91 ft TDH at 3231.7 gpm in BASE-2P; J1 53.74 psi, J3 51.59 psi | 3.45 | BASE-2P | Confirms pipe diameters/lengths/C and equiv 594.2+124.6+156.4=14,505 ft (p.10 DR-27 to DR-30) reproduce 11/10/2020 table |
