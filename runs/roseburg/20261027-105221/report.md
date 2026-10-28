DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Winchester Water Treatment Plant — Hydraulic Capacity Review: 12 mgd to 18 mgd Expansion
**Facility:** Winchester Water Treatment Plant, Roseburg, Oregon  
**Source:** City of Roseburg, Water Treatment Facilities Preliminary Design Report, July 2009 (public record)  
**Question:** Can the plant be expanded from 12 mgd to 18 mgd? For each unit along the flow path, does it limit 18 mgd, at what flow does it bind, and least-cost fix to make 18 mgd work?

## 1. Purpose
Determine, on a hydraulic basis only, whether each unit along the flow path limits 18 mgd, the flow at which it becomes limiting (`binds_at`), and the least-cost modification that makes 18 mgd work. This memorandum does not conclude treatability at 18 mgd.

## 2. Background
- Recent plant flow 3.5 to 11.6 mgd summer peak (p.108) (D01).
- Plant runs 24/7 to keep Reservoir Hill full (p.108).
- Existing floc/sed basin rated 12 mgd; plan adds parallel basin for nominal 18 mgd (p.111) (D15).
- Current 12 mgd treatment by 4 filters (p.107); 18 mgd nominal by 6 filters (p.107).
- Max all-on nominally 22 mgd (p.107); 20.9 mgd 2003 test (p.107) per findings.
- Drawing basis: ULTIMATE PLANT FLOW OF 22 MGD + HIGH WATER ELEVATION 453.0 (dwg p.136) (D68).
- Hydraulic vs treatment capacity distinction applies per p.107 General: piping/pumping/volume/flow-control ability to pass flow vs ability to meet regulatory requirements.

## 3. Design Criteria
- **Study objective:** Existing floc/sed rated 12 mgd; parallel basin for nominal 18 mgd; determine if 18 mgd works and what limits (p.111 + Question).
- **Firm capacity definition:** Capacity with largest unit out of service (Engineering rules).
- **Maximum desirable velocity in transmission mains:** 6.0 fps desirable; short WTP-site segments may exceed 6.0 fps as acceptable (p.110, p.116-117).
- **Minimum treated-water storage / detention:** Desirable minimum ~60 minutes detention at peak flow; at 24 mgd use 1-hour criterion = 1,000,000 gal (p.115).
- **Filter treatment rating vs hydraulic:** Current 3 mgd/filter is treatment limit; hydraulically 4 mgd/filter to clearwell; 6 filters = 24 mgd hydraulic (p.112).
- **Filter driving head available:** Normal filter level 463-464 ft to clearwell 446.5-448 ft = 15-17.5 ft; terminal headloss alarm 11.0 ft; max clearwell level 449.0 ft (p.112).
- **Surge protection performance:** Protect to 9,700 gpm (14.0 mgd) (p.117); max upsurge 150 psi; min downsurge HGL 630 ft (~175 ft head / 75 psi at grade 455 ft) (p.117).
- **Overflow / freeboard limits:** Floc/sed overflow weir 465.0 ft (p.111); settled channel ~6-in below weir at 13.1 mgd test (p.111); freeboard 1.5 ft at 466.0 ft max WS (p.111); clearwell overflows 449.5 ft (19 mgd at 1-ft depth) and 450.0 ft; combined 24 mgd (p.114).

Units: mgd, fps, ft, gpm, scfm, psi, gallons throughout. Gravity legs in `run_profile`, pumped legs in `run_hydraulics`; calibrate to field tests + drawing water surfaces at drawing design flow with residuals.

## 4. Data and Assumptions
Key source data retained with citations:

- River intake firm 15.0 mgd 2002 test (p.109) (D02); 14 mgd with Pumps 1,2,4 Sept 14 2006 (p.109) (D03); Pump No. 3 substantially below rated capacity (p.109) (D04).
- Raw-water pump swap: three 6 mgd + three 8 mgd = 22 mgd firm; four 8 mgd = 24 mgd firm (p.110) (D05).
- 30-in steel raw pipeline, 1/4-in wall (p.110) (D06); 30-in mag meter 2002 vault (p.110) (D07).
- Table 4-1 raw: 8 mgd: 2.6 fps, 0.05/100ft; 12 mgd: 3.9 fps, 0.11/100ft; 18 mgd: 5.9 fps, 0.54 V2/2g, 0.25/100ft; 20 mgd: 6.5 fps, 0.32/100ft; 24 mgd: 7.8 fps, 0.44/100ft (p.110) (D08-D12). 6.0 fps desirable; short length minimal surge even above 18 mgd (p.110) (D13).
- Rapid mix: 2 basins in parallel, only 1 operated now, both at higher flows (p.110) (D14).
- Pretreatment demonstrated to 11.5 mgd warm low-turbidity; normal 3.5-5.0 mgd cold high-turbidity (p.111) (D16).
- Settled path via launders to settled channel then 42-in pipeline (p.111) (D17). 42-in velocity 2.9 fps at 18 mgd, 3.9 fps at 24 mgd (p.111) (D25). Ultimate 22-24 mgd limited by settled pipe (p.112) (D27).
- Basin: max WS ~466.0 ft at 12 mgd one rapid-mix, gates open (p.111) (D18); launder weir invert 465.83 ft, trough bottoms 464.63 ft (12-in deep) (p.111) (D19); 1.5 ft freeboard adequate (p.111) (D20); overflow weir 465.0 ft, +1.0 ft above normal filter level (p.111) (D21); weir 9 ft long ~12 mgd at 9-in depth (p.111) (D22); 30-in drain ~10 mgd (p.111) (D23); second weir with second basin adequate to 24 mgd (p.111) (D24).
- Settled test Sept 14 2006: 2.8-in loss at 13.1 mgd; WS 6-in below 465.0 ft weir (p.111) (D26).
- Filters: 20-in inlet per filter (p.112) (D28); normal 463-464 ft, 5-6 ft submergence (p.112) (D29); 16-in per bay to 18-in common per filter to clearwell, with propeller meter and modulating butterfly valve to unbaffled clearwell under filters (p.112) (D30); clearwell max 449.0 ft, 0.5 ft below overflow (p.112) (D31); clearwell 446.5-448 ft, 15-17.5 ft head (p.112) (D32); 11.0 ft alarm; plan add 2 filters (total 6) (p.112) (D33); 3 mgd treatment vs 4 mgd hydraulic each, 24 mgd total with 6 (p.112) (D34); filter meters 7% low vs raw mag (straight-pipe not met) (p.112) (D35).
- Filter-to-waste: 8-in too small for 3 mgd (p.112) (D36); ~2 mgd FTW with Filter 3 offline at 9.1 mgd raw, others >3.4 mgd June 29 2006 (p.113) (D37); >2 mgd needs reconfig to allow FTW at filtering rate beyond 18 mgd (p.113) (D38).
- Clearwell: 170k + 324k + 133k = 627k gal at 10.5 ft depth (p.114) (D39); 627k = 75 min (1.26 hr) at 12 mgd (p.114) (D40); 1.0 ft drop per backwash (p.114) (D41); HS weir 449.5 ft, 9 ft, ~19 mgd at 1-ft depth to 18-in pipe to N. Umpqua River (p.114) (D42); Filter 3 weir 450.00 ft, 15 ft, combined 24 mgd, HS weir first (p.114) (D43); backwash 65-75k gal each, 260-300k gal/day for 4 filters (p.114) (D44).
- VFDs in progress on 1 raw + 1 finished pump to balance and hold clearwell level without throttling (p.115) (D45).
- Expanded: +85k gal under Filters 5-6 = 712k gal; 57 min at 18 mgd (p.115) (D46); at 24 mgd need 1,000k gal, short 288k gal with 6 filters (p.115) (D47).
- High-service: No.1 1,400 gpm (2.0 mgd) at 305 ft TDH 150 hp; Nos.2-4 each 2,800 gpm (4.0 mgd) at 305 ft TDH 300 hp (p.115) (D48); firm nominally 10 mgd, true ~11.5 mgd (3x3,300 gpm under current hydraulics) (p.115) (D49); expansion keep 1-4 add 6 mgd VFD + 4 mgd in available spaces for 18 mgd firm (p.116) (D50).
- Finished header 18-in to 30-in; site main wall 3/8-in, ID 29.25-in (p.116) (D51); 30-in propeller low, replace with mag (p.116) (D52); Table 4-3 (29.25-in ID): 8:2.65/0.05; 12:3.98/0.11; 18:5.97 fps, 0.553, 0.25/100ft; 20:6.63/0.32; 24:7.96/0.44 (p.117) (D53-D54); >6.0 fps at ~18 mgd but short segment acceptable (p.116) (D55); headloss raises TDH slightly reducing HS capacity (p.116).
- Surge: 1,900 cf (14,200 gal) to 9,700 gpm (14.0 mgd) (p.117) (D56); 150 psi max, HGL 630 ft (175 ft head/75 psi at 455 ft grade) (p.117) (D57) (grade 455 ft p.117 D69); replace with larger if beyond existing, 2nd tank impractical (p.117) (D58).
- Offsite: 20-in OD steel 3/16-in wall + 30-in DI Class 50 northerly (p.117) (D59); 1986 study to 18 mgd in 2 phases: Phase 1 ~9,400 ft parallel done; Phase 2 ~1,600 ft 27-in parallel 24-in (p.118) (D60) (now 30-in per development); second 30-in timing TBD vs 18 mgd expansion (p.118) (D61).
- Backwash/air/wastewater: blower 1,050 scfm at 6.4 psi 60 hp through 8-in (p.118) (D62); 2x3,250 gpm at 41 ft TDH 50 hp, 1 duty +1 spare (p.118-119) (D63); 16-in header (p.119); deep-bed optimum ~4,400 gpm (to 1.1 mm anthracite), tested 4,060 gpm at ~45 deg open Sept 14 2006 (p.119) (D64); 24-in waste to be replaced, upsizable to 30-in with filters (p.119) (D65); wastewater 3x1,500 gpm at 40 ft TDH 35 hp, firm 3,000 gpm one out (p.119) (D66); 2x300k gal solids basins (p.119) (D67).

**ASSUMPTIONS** (labeled; no cost source in pp.107-119,136):
- ASSUMPTION: Existing raw station is four 6-mgd nominal pumps (largest out =>18 nominal but ~14-15 demonstrated firm); model as system-head increase from Table 4-1 (p.110). Reason: p.110 swap implies 6-mgd base; intake tests (p.109) show deficiency without curves.
- ASSUMPTION: Short WTP-site lengths (raw ~500-800 ft, settled full-flow ~300 ft, finished site ~500 ft) for screening; settled leg calibrated to field 2.8-in at 13.1 mgd (p.111) rather than computed length. Reason: short lengths stressed + field anchor.
- ASSUMPTION: Cite only confirmed drawing values 453.0 high water + 22-MGD basis (dwg p.136); other drawing WS treated as UNCONFIRMED pending second read; calibrate to field points 466.0 at 12 mgd (p.111), 465.0 weir (p.111), 449.5/450.0 weirs (p.114), 463-464 ft filters (p.112), 446.5-448 ft clearwell (p.112). Reason: avoids invention.
- ASSUMPTION: Filter N-1: treatment-firm 5x3=15 mgd vs hydraulic-firm 5x4=20 mgd; 18 mgd requires all 6 in service on treatment basis unless higher rate approved. Reason: p.112 distinguishes 3 vs 4 mgd.
- ASSUMPTION: Usable clearwell = total minus 1-ft backwash drop (~10% ~70k gal p.114) minus CT dead zone; 57 min at 712k (p.115) is maximum; VFD level control holding near full mitigates (p.115). Reason: p.114-115 state actual <total + VFD fix.
- ASSUMPTION: New larger surge tank required beyond 14 mgd (p.117) carried as lump sum; no volume invented. Reason: replacement mandated but unsized.
- ASSUMPTION: Phase 2 first 30-in built with development and second parallel 30-in completed prior to/concurrent with 18-mgd expansion. Reason: p.118 ties timing to 18-mgd decision.
- ASSUMPTION: 18 mgd nominal treatability met only if second basin + 2 filters + full clearwell with VFDs; CT/detention verification follow-on using Section 3. Reason: 18 nominal intent (p.111) and 3 mgd/filter basis (p.112) but treatment text withheld. 18 mgd =12,500 gpm arithmetic and strict 60-min bind ~17.1 mgd (712k/60min) are ASSUMPTION arithmetic.

## 5. Model Calibration
Gravity profile calibrated to field tests; pumped runs screening only — field governs.

| Test | Measured (source) | Simulated | Residual | Run label |
|---|---|---|---|---|
| Settled 42-in headloss | 2.8-in loss at 13.1 mgd (p.111) | 0.233 ft =2.80-in (calibrate point) | 0.0% | BASE-CALIB-EXIST |
| Basin influent WS | ~466.0 ft at 12 mgd, 1 rapid-mix, gates open (p.111); top wall ~467.5 ft (1.5 ft freeboard p.111) | 466.0 ft at 12 mgd (binds_at 12.0 mgd on 466.0 limit) | 0.0% | BASE-CALIB-EXIST |
| Settled channel WS | 464.5 ft (465.0 weir p.111 minus 6-in p.111) at 13.1 mgd | ~464.25 ft (464.0 filter p.112 +0.2 ft pipe/inlet) | -0.05% (-0.2 to -0.3 ft; unmodeled launder/channel) | BASE-CALIB-EXIST |
| High-service firm | ~11.5 mgd true (nominally 10 mgd; 3 largest at ~3,300 gpm p.115); ratings 1,400 gpm/2.0 +3x2,800 gpm/4.0 at 305 TDH (p.115) | 8,293 gpm =11.942 mgd firm (2x4+1x2, largest 4 out) | +3.8% (assumed 500-ft 29.25-in ID p.116 + offsite HGL 710 ft ASSUMPTION) | HS-FIRM-TRUE |
| Raw-water firm | 14 mgd with 1,2,4 (p.109); 15.0 mgd 2002 (p.109); Pump 3 below rating (p.109) | Field-governed 14-15 mgd; model ALT-RAW-REHAB18 proves rehabbed 3x6-mgd firm >18 (23.429 mgd total) — screening only | 0.0% field governs | ALT-RAW-REHAB18 |
| Filter-to-waste | ~2 mgd FTW at 9.1 mgd total with 1 offline (p.113); 8-in too small for 3 mgd (p.112) | 8-in <3 mgd confirmed by velocity: 8.865 fps at 2 mgd, 13.297 fps at 3 mgd | 0.0% | BASE-CALIB-EXIST |
| Clearwell storage | 627k gal =75 min at 12 mgd (p.114: 170k+324k+133k at 10.5 ft); 712k =57 min at 18 mgd (p.115 +85k); 1-ft drop/wash (p.114); 65-75k gal/wash, 260-300k/d (p.114) | 627k/712k accepted; 57-min max at 18 mgd | 0.0% | BASE-CALIB-EXIST |
| Drawing 22-MGD WS | Drawing ultimate 22 MGD + high water 453.0 ft (dwg p.136); filters 463-464 ft (p.112), clearwell 446.5-448 ft (p.112) max 449.0 ft (p.112), overflows 449.5 9-ft 19 mgd +450.0 15-ft combined 24 mgd (p.114) | EXP2B-18PROOF at 22 mgd: filters 464.0 residual 0.0, settled 464.65 vs 464.83 -0.18 ft, basins 466.16 vs 466.0 +0.16 ft over influent max | 0.03% | EXP2B-18PROOF |

Note: PROF-1B-CAL settled residual -0.60 ft at 13.1 mgd vs 464.83 ft dwg p.136 reflects UNCONFIRMED drawing WS; field headloss exact 0.233 ft (p.111); offset = unmodeled launders/channels. At 22 MGD dwg p.136, PROF-2B-FUT residuals -0.22 ft settled, +0.12 ft basins.

## 6. Capacity Evaluation
`limits_target` = limits 18 mgd. `binds_at` = flow where unit binds.

| Unit along flow path | Limits 18 mgd? | Binds at | Evidence (with run) |
|---|---|---|---|
| River intake / raw-water pumps firm | Yes | ~14-15 mgd field (14 with 1,2,4; 15.0 in 2002) (p.109) | Field governs (p.109); ALT-RAW-REHAB18 rehabbed firm >18 (23.429 mgd total, 7.38 fps screening). Raw main 5.673 fps at 18 mgd (velocity, 30-in) vs 5.9 fps Table 4-1 (p.110) <6.0 desirable (p.110). |
| 30-in raw pipeline + mag meter | No | ~20 mgd on 6.0 fps (6.5 fps at 20 mgd Table 4-1 p.110); short length acceptable above 18 (p.110) | Velocity 5.673 fps at 18 mgd (30.0-in) and 5.867 fps at 29.5-in ID ASSUMPTION ID; Table 4-1 18:5.9/0.25 per 100ft, 20:6.5/0.32, 24:7.8/0.44 (p.110); 30-in mag 2002 (p.110). |
| Floc/sed basin + launders/weirs/overflow | Yes (single); No with 2nd basin | 12.0 mgd single (BASE-CALIB-EXIST / PROF-1B-CAL binds_at 12.0 on 466.0 ft); 21.17-21.38 mgd with 2 basins (EXP2B-6F-CORR / PROF-2B-FUT profile_capacity) | Single rated 12 mgd, 18 nominal +~24 hydraulic with parallel (p.111); 466.0 ft at 12 mgd (p.111), weir 465.0 ft 9-ft ~12 mgd at 9-in (p.111), 30-in drain ~10 mgd (p.111); 2 weirs to 24 (p.111). PROF-2B-FUT passes 18: settled 464.42 ft margin 0.58 ft to 465.00 ft (p.111 dwg p.136); basins 465.43 ft margin 0.57 ft to 466.0 ft (p.111 dwg p.136). |
| 42-in settled pipeline to filters | No | 24.0 mgd rating (22-24 ultimate p.112); 27.8-28.84 mgd on 465.0 weir submergence (profile_capacity) | 42-in (p.111) velocity 2.895 fps at 18, 3.86 at 24; calibrated 2.8-in at 13.1 mgd (p.111); 2.9 fps at 18 /3.9 at 24 (p.111); ultimate limited by settled pipe 22-24 (p.112). EXP2B-18PROOF settled 464.45 margin 0.55 ft. |
| Filters (4 existing) treatment + hydraulic | Yes | 12 mgd treatment (4x3) /16 mgd hydraulic (4x4); 6-filter 18 treatment /24 hydraulic | 3 mgd treatment vs 4 mgd hydraulic each (p.112); normal 463-464 ft 5-6 ft submergence (p.112); 20-in inlet (p.112), 16-in to 18-in effluent (p.112); 11.0 ft alarm, 15-17.5 ft head (p.112); meters 7% low (p.112). |
| Filters (6 future) N vs N-1 | Yes on firm treatment | 18.0 mgd treatment exactly (6x3); hydraulic 24 (6x4); treatment-firm 15 (5x3) if N-1 ASSUMPTION | Add 2 filters to 6 total (p.112); PROF-2B-FUT 16.0 ft driving head >11.0 ft (p.112) margin 5.0 ft; 18 requires all 6 on treatment basis. Hydraulically passes at 464.0 ft filters dwg p.136. |
| 8-in filter-to-waste | Yes | ~2 mgd observed (p.113); <3 mgd rating (p.112) | 8-in too small for 3 mgd (p.112); ~2 mgd FTW at 9.1 total (p.113) others >3.4 mgd; velocity 8.865 fps at 2 mgd, 13.297 fps at 3 mgd; >2 mgd needs reconfig at filtering rate (p.113). Run PROF-1B-CAL. |
| Clearwell detention + overflows | Yes on strict 60-min; No hydraulically | ~17.1 mgd on strict 60-min (712k/60min ASSUMPTION); 57 min max at 18 mgd | 627k (170+324+133k at 10.5 ft p.114)=75 min at 12 (p.114); +85k=712k=57 min at 18 (p.115); 1-ft drop/wash (p.114); 1,000k needed at 24 short 288k (p.115); VFDs hold level (p.115); overflows 449.5 9-ft 19 mgd +450.0 15-ft combined 24 (p.114) do not limit flow. Run PROF-2B-FUT. |
| High-service pumps firm | Yes | ~11.5-11.9 mgd existing firm (10 nominal, 11.5 true p.115; 11.942 model HS-FIRM-TRUE) | 1x1,400 gpm 2.0 +3x2,800 gpm 4.0 at 305 TDH (p.115); max all-on nominally 16 achieved ~14 (p.107); keep 1-4 add 6 VFD +4 for 18 firm (p.116). HS-EXIST-FIRM errored; no pumped proof claimed. |
| 30-in (29.25-in ID) finished site main + meter | No (short segment) | ~18.1 mgd on 6.0 fps (5.97 fps at 18 Table 4-3 p.117; 5.968 velocity) ASSUMPTION; acceptable (p.116) | Header 18-to-30-in (p.116), ID 29.25-in 3/8 wall (p.116); Table 4-3 18:5.97/0.553/0.25, 20:6.63/0.32, 24:7.96/0.44 (p.117); 30-in propeller low replace mag (p.116). |
| Hydropneumatic surge tank | Yes (protection, not conveyance) | 14.0 mgd (9,700 gpm protection p.117) | 1,900 cf 14,200-gal (p.117) to 14.0 mgd; 150 psi upsurge, HGL 630 ft (175 head/75 psi at 455 grade p.117) (D69); replace if beyond existing, 2nd impractical (p.117). 18 mgd=12,500 gpm ASSUMPTION exceeds 29%. Run PROF-2B-FUT. |
| Offsite transmission to Reservoir Hill | Yes | <18 mgd existing (improvements to 18 required p.118) ASSUMPTION unmodeled | 20-in OD steel 3/16 +30-in DI northerly (p.117); Phase 1 9,400 ft done, Phase 2 1,600 ft 27-in (now 30-in) parallel 24-in (p.118); second 30-in timing TBD vs 18 mgd (p.118); 24/7 to keep Reservoir Hill full (p.108). No run_hydraulics proves delivery to 710.0 ft reservoir dwg p.136. |
| Backwash / air / wastewater / solids | No | >18 mgd (deep-bed 4,400 gpm threshold p.119); conventional passes 18 | 2x3,250 gpm at 41 TDH 50hp 1+1 spare (p.118-119), 16-in header (p.119) adequate (p.119); 4,060 gpm at 45deg tested (p.119) vs 4,400 deep-bed optimum (p.119); air 1,050 scfm 6.4 psi 60hp 8-in (p.118); 24-in waste to 30-in (p.119); WW 3x1,500 at 40 TDH 35hp firm 3,000 gpm (p.119)=4.32 mgd > washwater; 2x300k basins (p.119). |

Intake openings/screens/gates (4x4-ft to 24+ mgd, screens to 18+ mgd, 5-ft gates to 24+ mgd p.109) do not limit per findings; rapid-mix detention, filter influent channel, backwash drains/channel, drying beds not evaluated for 18 mgd — no binds_at in source.

## 7. Alternatives (Least-Cost Modification per Unit)
Cost class = n/a — no cost source in pp.107-119,136.

| Unit | Option | Result / run | Meets 18? | Cost class / basis | Rec? |
|---|---|---|---|---|---|
| River intake / raw pumps | R1 - Rehab/test raw pumps to prove 18-mgd firm (clean/test/re-rate Pump 3 p.109 + VFDs p.109/p.115 then retest) | Field governs: 14 mgd with 1,2,4 and 15.0 mgd in 2002 (p.109) <18. No run_hydraulics proves firm >18 (HS-EXIST-FIRM failed; prior ALT runs ASSUMED curves/TDH/lengths). | No (NOT proven) | n/a | Yes |
| Floc/sed | F1 - Second basin in parallel (original provision for 18 nominal /~24 hydraulic p.111) | PROF-2B-FUT passes 18: settled 464.42 ft margin 0.58 ft to 465.00 ft (p.111 dwg p.136); basins 465.43 ft margin 0.57 ft to 466.0 ft (p.111 dwg p.136); binds 21.38 mgd vs single 12.02 mgd PROF-1B-CAL | Yes (gravity proof) | n/a | Yes |
| Filters | FI1 - Add Filters 5-6 (6 total) for 18-mgd treatment (N, not N-1 firm) (3 vs 4 mgd each p.112; buildout p.107/p.112) | 4x3=12 treatment (p.107/p.112) <18; 6x3=18 exactly; firm treatment 5x3=15 ASSUMPTION N-1 <18. Hydraulically PROF-2B-FUT passes at 464.0 ft filters dwg p.136; treatment allowability withheld Sec.3. | No (N, not firm) | n/a | Yes |
| Filter-to-waste | W1 - Upsize/reconfigure 8-in FTW to 3-4 mgd/filter (8-in <3 mgd p.112, ~2 mgd observed p.113) | Velocity 8-in: 8.865 fps at 2 mgd, 13.297 fps at 3 mgd confirms limit (p.112/p.113); must allow FTW at filtering rate (p.113). Run PROF-1B-CAL. | Yes | n/a | Yes |
| Clearwell | C1 - VFD level control +85k gal (712k total); accept <60-min unless CT requires more (VFDs p.115; +85k p.115) | 627k =75 min at 12 (p.114); 712k =57 min max at 18 (p.115) <60-min desirable (p.115); usable <total by 1-ft/wash (p.114); strict 60-min binds ~17.1 mgd ASSUMPTION | No (on strict criterion) | n/a | Yes |
| High-service pumps | H1 - Add HS pumps for 18-mgd firm (keep 1-4 add 6+4 concept p.116; ratings 1,400/2.0 +3x2,800/4.0 at 305 TDH p.115) | Existing nominal 16 max all on, ~14 achieved (p.107); true firm ~11.5 (p.115) <18. HS-EXIST-FIRM errored; no model proves H1. Requires new run_hydraulics + test. Run PROF-2B-FUT. | No (NOT proven) | n/a | Yes |
| Surge | S1 - Larger surge tank for 18 mgd + transient study (replace 1,900 cf p.117 if beyond existing; 2nd impractical p.117; 1986 basis p.118) | Existing to 9,700 gpm=14.0 mgd (p.117); 18 mgd=12,500 gpm ASSUMPTION exceeds 29%; protection limit not conveyance limit; size by transient study. Run PROF-2B-FUT. | Yes (protection) | n/a | Yes |
| Offsite transmission | T1 - Phase 2 + second 30-in to Reservoir Hill (Phase 1 9,400 ft done, Phase 2 1,600 ft 27-in now 30-in + second 30-in timing TBD vs 18 mgd p.118) | No run_hydraulics proves 18-mgd delivery to 710.0 ft reservoir dwg p.136; plant runs 24/7 to keep Reservoir Hill full (p.108); 1986 study basis (p.118). Run PROF-2B-FUT. | No (NOT modeled) | n/a | Yes |

Ancillary: retain + upsize 24-in waste to 30-in + mag + meter fix (waste 24-in to 30-in p.119; 30-in propeller low replace mag p.116; filter meters 7% low p.112).

## 8. QA/QC Summary
- Checked citations: p.109 intake firm 14 with 1,2,4 and 15.0 2002 + Pump 3 below rating; p.110 30-in steel 1/4-in + 30-in mag 2002; p.111 single 12 mgd, parallel for 18 nominal ~24 hydraulic; p.112 ultimate 22-24 mgd limited by settled pipe; p.114 170k+324k+133k at 10.5 ft =627k gal.
- Checked runs (reruns reproduce): EXP2B-18PROOF, HS-FIRM-TRUE (8,293 gpm=11.942 mgd), HS-FUT-18FIRM (14,830 gpm=21.355 mgd screening), BASE-CALIB-EXIST. Velocity: 30-in at 18 mgd 5.673 fps; 29.25-in at 18 mgd 5.968 fps; 42-in at 18 mgd 2.895 fps; 8-in at 3 mgd 13.297 fps. HS-EXIST-FIRM errored — no pumped proof claimed.
- Major issues dispositioned:
  - Treatment at 18 mgd — rejected as proven: floc detention, sedimentation loading, filter loading, CT text withheld, Sec.3 not provided (p.114-115 ref). 11.5 mgd warm (p.111) and 3.5-5.0 mgd cold (p.111) do not prove 18 mgd. Hydraulic-only conclusion.
  - Raw pump firm proof — rejected: ALT screening with ASSUMED curves/TDH/lengths overstated (7.38 fps) vs 6.0 fps desirable (p.110) and field; field 14/15.0 mgd (p.109) governs; R1 requires retest.
  - Filter N-1 — fixed: 6x3=18 N exactly, 5x3=15 N-1 ASSUMPTION <18; firm 18 needs 7th filter or approved higher rate.
  - Profile to drawing — fixed: two-read dwg p.136 values only (466.0, 465.00, 464.83, 464.0, 467.5, 710.0, 22 MGD note); at 22 MGD PROF-2B-FUT residuals -0.22 ft settled +0.12 ft basins; prior -0.4 to -0.6 ft offsets disclosed as unmodeled launders, not validation.
  - High-service assumptions — noted: runs at 118% runout with ASSUMED HGL 710 ft/lengths/eff; VFD turndown (p.115) not modeled; 11.942 vs 11.5 mgd gap ASSUMPTION.
  - Offsite — rejected as verified: no offsite run_hydraulics; T1 condition per p.118 TBD analysis.
- Minor issues fixed/noted: raw ID handling (5.673 fps nominal 30.0-in vs 5.867 fps at 29.5-in ID ASSUMPTION vs Table 4-1 5.9 fps p.110; finished 5.968 fps at 29.25-in ID p.116 vs Table 4-3 p.117 correct); clearwell 60-min contradiction clarified (passes hydraulically with VFDs p.115 but fails strict 60-min desirable p.115); surge reworded as protection rating to 14.0 mgd (p.117) not conveyance bind; C=83 bundles valves/meter/vault, 300-ft/500-ft lengths ASSUMPTION, TDH not fixed from ft/100ft without lengths; costs n/a; WW 3,000 gpm firm (p.119) adequate vs washwater without silent conversion; missed units listed.

## 9. Recommendations
- Hydraulically, 18 mgd passes gravity with F1 + FI1 + W1 + C1 only if:
  - Build second floc/sed basin + second 9-ft weir at 465.00 ft; keep influent ≤466.0 ft (top wall 467.5 ft); PROF-2B-FUT binds 21.38 mgd (p.111 dwg p.136).
  - Add Filters 5-6; hold 463-464 ft; upsize 8-in FTW to 3-4 mgd/filter; fix 7% low effluent meters (p.112/p.113). Note 18 mgd requires all 6 on treatment basis (5x3=15 firm ASSUMPTION).
  - Operate clearwell full with VFDs (p.115) 446.5-448 ft to max 449.0 ft +85k gal (p.115); overflows 449.5 +450.0 unchanged (p.114); 57-min max — verify CT.
  - Rehab/test raw pumps (Pump 3 p.109 + VFDs p.109/p.115) then retest to prove 18 firm — field 14/15.0 mgd (p.109) governs; no model proves firm >18.
  - Add HS capacity for 18 firm (p.116 concept); replace surge tank (14.0 mgd p.117) with larger 18-mgd unit + transient study; replace propeller with mag (p.116).
  - Complete Phase 2 1,600-ft 30-in + second parallel 30-in prior to/concurrent with 18 mgd (p.118); confirm inlet HGL at 710.0 ft reservoir dwg p.136.
- Do not certify 18-mgd expandability until: treatment (floc/sed loading, filter rate, CT Sec.3) proven, raw and HS firm proven by test with true curves/HGL, and offsite delivery modeled.
- Drawing changes anchored: RIVER INTAKE 453.0 ft dwg p.136; FLOCCULATION/SEDIMENTATION 466.0 ft; FILTERS 464.0 ft; CLEARWELL 449.0 ft; HIGH SERVICE 455.0 ft grade (p.117); RESERVOIR 710.0 ft dwg p.136 — notes per Section 7.

## 10. Limitations
- Hydraulic-only study. Treatment-process capacities (floc detention, sedimentation loading, filter loading rate, disinfection CT) withheld; Sec.3 CT discussion referenced but not provided (p.114-115). ASSUMPTION of 18 mgd nominal treatability (p.111 intent, p.112 3 mgd/filter basis) is not proof.
- Raw pump ratings, curves, TDH, intake screen details, pipe lengths, minor-loss K, yard layout not in pages; lengths ASSUMED; total TDH cannot be fixed from ft/100ft (p.110/p.117) without lengths; settled C=83 bundles valves/meter/vault.
- Drawing elevations except 453.0 high water + 22-MGD basis (dwg p.136) UNCONFIRMED; residuals -0.6 to +0.12 ft include unmodeled detail; cannot claim drawing validation at 22 mgd.
- Pumped runs screening with invented curves/TDH/HGL/lengths; HS-EXIST-FIRM failed; H1/R1/T1 NOT proven; offsite <18 mgd binds_at ASSUMPTION unmodeled.
- Usable clearwell < total (1-ft/wash p.114); strict 60-min desirable (p.115) fails at 18 mgd (57 min max p.115); usable quantification + CT follow-on required.
- No cost source in pp.107-119,136; all cost classes n/a; tank size, offsite phasing, 7th filter vs higher-rate approval require further study.
