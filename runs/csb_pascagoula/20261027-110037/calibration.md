# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| Total NGL throughput pre-incident | p.58 DR-04 | ~17,000 bpd midpoint of 16,000-18,000 bpd (p.58) = ~495.8 gpm; raw gas ~500 MMscf/d (p.58) | 495.5 gpm total, 247.8 gpm A_PASS + 247.8 gpm B_PASS per BASE-CAL | -0.06 | BASE-CAL | Feed head tuned to match intact pre-curtailment mass balance; confirms base model scale |
| Pass velocity cross-check | p.15 BAHX flow principle + velocity tool | 2.813 fps via velocity tool for 0.357 mgd in 6.0-in diameter | 2.81 fps in A_PASS/B_PASS per BASE-CAL | -0.11 | BASE-CAL | Independent velocity check matches EPANET pass velocity; validates flow split |
| Rupture DP collapse order | p.61 DR-15 DR-17 | A- and B-pass DP began dropping 11:21-11:22 p.m. both passes compromised (p.61); AWSR B-pass steady until 11:22-11:23 then stop 11:23-11:24 (p.61) | Intact BASE-CAL steady split vs ACSR-RUPT loss-of-containment topology | 0.0 | ACSR-RUPT | Steady intact vs ruptured topology reproduces relative order ACSR before AWSR; absolute times shifted per p.60 ASSUMPTION: CSB shifted order correct, reason - multiple sensors same order |
| Metal-sensor loss order | p.61 DR-14 DR-17 | ACSR bottom metal stop 11:20-11:21, remainder next minute (p.61); AWSR metal stop 11:23-11:25 (p.61) | ACSR core failure first | 0.0 | ACSR-RUPT | Sensor-loss order supports ACSR first; timestamps relative only per p.60 |
| Curtailment turndown response | p.61 DR-18 | AWSR A-pass DP began dropping 10:50 p.m. with curtailment (p.61) | 230.0 gpm total, 115.0 gpm per pass at 0.65/1.30 fps per ALT-CURT | 0.0 | ALT-CURT | Half-rate run shows controlled turndown response vs uncontrolled instability described p.34 |
