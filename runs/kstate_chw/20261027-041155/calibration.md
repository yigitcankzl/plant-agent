# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| Secondary full capacity | p.14 | 14600 gpm total (p.14) | 14551.6 gpm total pumped | -0.33 | BASE-SEC-FULL | 5x2920 gpm (p.14) in parallel to low-loss header; matches nameplate within model tolerance |
| Secondary N+1 capacity | p.14 | 11680 gpm N+1 (p.14) | 11654.3 gpm total pumped | -0.22 | BASE-SEC-FIRM | 4x2920 gpm largest out; confirms firm secondary governs vs 11800 gpm primary |
| Primary N+1 capacity | p.14 | 11800 gpm N+1 (p.14) with PP-6 (2800 gpm 70 ft p.14) out | 11740.8 gpm total pumped | -0.5 | BASE-PRI-FIRM | 5x pumps (1800+4x2500 p.14) uniform 40 ft; full 6-pump run over-pumps (15919 gpm, PP-6 at 151% rated) due to single-point curve with mismatched heads, so firm run used for calibration |
