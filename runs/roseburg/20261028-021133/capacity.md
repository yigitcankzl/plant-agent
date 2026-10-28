# Step 5 - Capacity evaluation

| unit | limit | binds_at | limits_target | evidence |
|---|---|---|---|---|
| RAW-WATER PUMP STATION + INTAKE | firm pumping <18 mgd | 14-15 mgd demonstrated (14 mgd 2006, 15.0 mgd firm 2002) | True | hsps-exist2-style screening rw-18a shows main can carry 18 mgd at V=5.67 fps; pumps/intake fouling limits |
| 30-IN RAW-WATER PIPELINE | pipeline velocity/headloss | >18 mgd hydraulically (V=5.67 fps at 18 mgd <6.0 fps desirable) | False | velocity 5.673 fps (30-in at 18 mgd) + Table 4-3 5.97 fps at 18 mgd (p.117); rw-18a TDH 57 ft |
| FLOCCULATION/SEDIMENTATION BASIN | 12 mgd treatment rating (single basin) | 12.0 mgd basin rating | True | prof-18test first_limit floc-basin 12.0 mgd; sustained 11.5 mgd warm/low-turbidity (p.111) |
| SED LAUNDERS + SETTLED CHANNEL + WEIR | launder/max WS then overflow spill | 13.1 mgd launder submergence; 18.75 mgd overflow weir | True | profile_capacity: sed-launders 13.13 mgd (max WS 465.98), settled-channel 18.75 mgd (weir 465.0) |
| 42-IN SETTLED-WATER PIPE | headloss | hydraulic >18 mgd (0.42 ft at 18 mgd); calibrated 0.233 ft at 13.1 mgd | False | altB-6filt settled-pipe loss 0.42 ft, V=2.90 fps at 18 mgd (velocity 2.895 fps for 42-in at 18 mgd) |
| FILTERS 1-4 | treatment 12 mgd / hydraulic 16 mgd | 12.02 mgd treatment (4x3 mgd); 16 mgd hydraulic (4x4 mgd) | True | profile_capacity filters 12.02 mgd; p.112 3 mgd treatment vs 4 mgd hydraulic per filter |
| FILTER-TO-WASTE PIPING | 2 mgd filter-to-waste piping | ~8 mgd plant all-in (~6 mgd N-1) at 2 mgd waste limit | True | 9.1 mgd test: ~2 mgd to waste, >3.4 mgd each other two (p.113); need 4.5 mgd/filter at 18/4 |
| CLEARWELL OVERFLOWS | overflow spill capacity | 19 mgd HSPS weir alone; 24 mgd combined | False | p.114 19 mgd at 1-ft depth, combined 24 mgd ultimate; altB clearwell margin 0.45 ft at 18 mgd |
| CLEARWELL STORAGE | detention + CT (Section 3 governs) | 57 min at 18 mgd (712k gal) vs 60-min screen; 75 min at 12 mgd | True | 627k gal total (p.114); +85k under Filters 5&6 =57 min at 18 mgd (p.115); 1.0 ft drop per backwash |
| HIGH-SERVICE PUMP STATION | firm pumping capacity | 11.22 mgd firm (10 mgd nominal); all-pumps 14.85 mgd | True | firm_capacity hsps-exist2: 11.22 mgd governing large-unit outage; hsps-18a 17.90 mgd firm, 19.21 mgd with small out |
| 30-IN SITE FINISHED-WATER MAIN | velocity 6.0 fps + system headloss | 18 mgd V=5.97 fps, 0.553 ft/1000? Table 4-3 0.25? passes short segment; system head governs >18 | False | Table 4-3 (p.117) 5.97 fps at 18 mgd <6.0 fps; velocity 5.968 fps for 29.25-in at 18 mgd; p.117 small headloss not significant |
| SURGE TANK (1900 cf/14200 gal) | transient rating | 14.0 mgd surge rating | True | 9700 gpm/14.0 mgd, 150 psi max, HGL 630 ft min (p.117); re-analysis required for 18 mgd config |
| BACKWASH PUMPS + AIR SCOUR | backwash rate for current media | existing 3250 gpm adequate; 4400 gpm needed only for deep-bed >18 mgd | False | 4060 gpm tested at 45-deg (p.119) vs 4400 est for 1.1 mm anthracite; 1050 scfm air adequate |
| WASTEWATER PS + BASINS | pump-down + basin volume (mass-balance test needed at 18) | 3000 gpm firm; 2x300k gal basins; 65-75k gal per wash | False | p.119 3x1500 gpm (3000 firm), 24-in/30-in drains; p.114 260-300k gal/day at 12 mgd |
