# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| Raw all-pump test 2003 | p.107 | 20.9 mgd all 4 pumps June 24 2003 (p.107 DR-05) | 21.46 mgd all pumps (run raw-existshort) | 2.7 | raw-existshort | validates system curve; 0.56 mgd high = 11% of pump TDH headloss; within Class5 screening |
| 42-in settled pipe headloss | p.111 | 2.8-in (0.233 ft) at 13.1 mgd Sept 14 2006 (p.111 DR-18) | 0.233 ft (run base-grav2 / grav-cal-13 calibrated) | 0.0 | base-grav2 | Fitted C=75 used; independent margin check: 6-in below overflow vs 0.60 ft simulated |
| Settled channel freeboard | p.111 | 6-in (0.50 ft) margin to 465.0 overflow at 13.1 mgd (p.111 DR-18) | 0.60 ft margin (464.40 vs 465.0, run grav-cal-13) | 43.0 | base-grav2 | Residual 0.10 ft = 43% of 0.233-ft pipe headloss; validates profile, not used to fit C |
| High-service firm test | p.115 | 11.5 mgd true firm ~3,300 gpm ea; 14 mgd max achieved (p.115 DR-29) | 11.82 mgd firm, 16.37 mgd all pumps (run hs-exist firm) | 2.8 | hs-exist | Firm residual 0.32 mgd = 2.8% of flow, 12% of TDH margin; validates HS curve |
