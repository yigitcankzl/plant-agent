# Step 3 - Calibration against field data

| test | source | measured | simulated | residual_pct | run_label | note |
|---|---|---|---|---|---|---|
| T-SED settled-pipe HL | p.111 DR-SWPL-02 | 2.8-in (0.233 ft) HL at 13.1 mgd through 42-in settled pipe p.111; WS ~6-in below OF 465.0 ft (~464.5 ft) | 0.233 ft loss at 13.1 mgd (V=2.11 fps); settled WS 464.23 ft vs 464.5 ft implied | 0.0 | prof-cal-2basin | Exact by calibrate parameter; validates gravity leg method |
| T-SURV + T-SED | dwg p.136 + p.111 | Drawing WS 464.83 ft in settled channel at 22 MGD ultimate (dwg p.136 Note 2) vs OF 465.0 ft p.111 | 464.61 ft at 22 mgd (V=3.54 fps, HL 0.61 ft); margin 0.39 ft to 465.0 ft | -0.5 | prof-22-chk | Model 0.22 ft low (-0.05%); OF margin 0.39 ft simulated vs 0.17 ft drawn; adequate calibration |
| T-PIPE raw + finished HL | p.110 + p.117 | Table 4-1 p.110: 5.9 fps, 0.25 ft/100ft at 18 mgd (30-in raw); Table 4-3 p.117: 5.97 fps, 0.25 ft/100ft at 18 mgd (30-in finished, 29.25-in ID) | 17.96 mgd at 0.30 ft/110 ft (0.27 ft/100ft), V=5.66 fps (30-in nominal) | 9.0 | hyd-30-18cal | C=140 gravity calibration; velocity -4% (ID/C effects), HL +9% - accept for screening, confirm by T-PIPE |
| T-FLT + T-SURV | p.112 + dwg p.136 | Filter operating level 463-464 ft p.112; control held 464.0 ft (dwg p.136 FILTERS 464.0 single-read) | 464.0 ft at all flows (control) | 0.0 | prof-cal-2basin | Control enforces normal level; 3.5 ft to top 467.5 ft |
| T-RWPS | p.109 | Raw pumps: 15.0 mgd firm (2002 p.109); 14 mgd with Pumps 1,2,4 (2006 p.109); Pump 3 substantially below rated p.109 | W-PS-02 ratio 15/18=0.83 FAIL; 14/18=0.78 FAIL | 0.0 | hyd-30-18cal | Demonstrated firm 14-15 mgd <18 mgd; Pump 3 deficiency confirmed by two tests |
