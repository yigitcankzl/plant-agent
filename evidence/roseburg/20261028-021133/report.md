DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum - Winchester Water Treatment Plant 12 mgd to 18 mgd Expansion Screening

## Purpose

Evaluate whether the Winchester Water Treatment Plant, Roseburg, Oregon (p.111 rated at 12 mgd; p.114 at current maximum plant flow of 12 mgd; p.115 at the 12 mgd plant capacity) can be expanded to the Study expansion target 18 mgd (p.115 At the expanded plant capacity of 18 mgd; p.111 At 18 mgd pipeline velocity; p.116 exceed 6.0 fps at approximately 18 mgd), and for each unit along the flow path determine whether it limits 18 mgd, the flow at which it becomes limiting, and the least-cost modification that makes 18 mgd work.

Source: City of Roseburg, Water Treatment Facilities Preliminary Design Report, July 2009 (public record).

## Background

- Current plant capacity: 12 mgd (p.111 rated at 12 mgd; p.114 at current maximum plant flow of 12 mgd; p.115 at the 12 mgd plant capacity).
- Study expansion target: 18 mgd (p.115 At the expanded plant capacity of 18 mgd; p.111 At 18 mgd pipeline velocity; p.116 exceed 6.0 fps at approximately 18 mgd).
- Ultimate maximum plant capacity cited in text: 24 mgd (p.111 adequate for an ultimate maximum plant capacity of 24 mgd; p.114 accommodate an ultimate plant flow of 24 mgd; p.115 At 24 mgd using the 1-hour criteria).
- Drawing ultimate design flow: 22 MGD (dwg p.136) (dwg p.136 BASED ON AN ULTIMATE PLANT FLOW OF 22 MGD). **Conflict noted:** dwg 22 MGD (dwg p.136) vs text 24 mgd (p.111, p.114).
- Observed operation: Peak-day operating range observed 3.5 to 11.6 mgd (p.108: "plant flow rate has ranged from approximately 3.5 mgd during low demand periods to 11.6 mgd during a recent peak summer day") (DR-01).
- Flow path for capacity study (p.107-108 general + existing hydraulic profile Figure 4-2): `river intake -> raw-water pumps -> 30-in raw-water pipeline -> rapid mix -> flocculation/sedimentation basin (launders, settled-water channel) -> 42-in settled-water pipe -> filter influent channel -> filters (4 existing) -> filter effluent pipes -> clearwell/treated storage (3 zones) -> high-service pumps -> 30-in site transmission main -> offsite transmission to Reservoir Hill reservoirs -> backwash/wastewater/solids side stream`

## Design Criteria

From collection.criteria:

- Firm capacity definition: capacity with largest unit out of service (Engineering rules provided for this study).
- Hydraulic vs treatment capacity definition: hydraulic capacity is related to piping, pumping, volume and flow control; treatment capacity is related to ability to meet regulatory requirements (p.107). Evaluate both; treatment can limit below hydraulic.
- Existing pretreatment basin rating: 12 mgd (p.111 The single existing basin is rated at 12 mgd).
- Existing filter treatment rating: 3 mgd per filter (p.112 current 3 mgd filter rating is a treatment capacity limitation).
- Filter hydraulic pass-through when filtering to clearwell: 4 mgd per filter hydraulic (p.112 Hydraulically, the piping into and out of each basin can handle 4 mgd when the filter is filtering to the clearwell).
- Observed filter-to-waste piping limit: 2 mgd (p.113 existing filter-to-waste piping does not appear to convey more than 2 mgd; p.113 flow through filter No.1 in filter-to-waste was approximately 2 mgd).
- Clearwell detention desirability criterion: 60 minutes at peak flow (p.115 generally considered desirable that a WTP maintain a minimum clearwell volume of approximately 60 minutes of detention time at the plant's peak flow rate).
- Maximum desirable transmission main velocity: 6.0 fps (p.116 While the maximum desirable velocity in a main of this type is approximately 6.0 fps).
- Surge system performance criteria: 14.0 mgd, 150 psi max upsurge, HGL 630 ft min downsurge (p.117 Surge protection is provided for pumping rates up to 9,700 gpm (14.0 mgd); p.117 maximum upsurge controlled to 150 psi; p.117 minimum allowable downsurge controlled to an HGL of 630 feet (approximately 175 feet of head or 75 psi assuming plant ground elevation of 455 feet)).
- Sedimentation overflow weir rating: 12 mgd at 9-in depth, 9 ft long, elev 465.0 ft (p.111 weir is approximately 9 feet long with a capacity of approximately 12 mgd, assuming a 9-inch water depth over the weir).
- Sedimentation overflow drain pipe rating: 10 mgd, 30-in diameter (p.111 drain pipe is 30-inches in diameter, has a capacity of approximately 10 mgd).
- Clearwell HSPS overflow rating: 19 mgd at 1-ft depth, weir elev 449.5 ft, length ~9 ft (p.114 At 1 foot of water depth over the weir, the overflow capacity is approximately 19 mgd; p.114 overflow weir and piping is sufficient to handle clearwell overflows up to 19 mgd).
- Combined clearwell overflows ultimate rating: 24 mgd combined (p.114 Combined, the two overflow weirs can accommodate an ultimate plant flow of 24 mgd).
- Filter operating level and driving head: 463-464 ft, 5-6 ft submergence, 15-17.5 ft driving head, 11.0 ft terminal alarm (p.112 normal filter operating level ranges from 463 to 464 feet; p.112 provides 5 to 6 feet of submergence over top of media; p.112 provides total filter driving head of approximately 15 to 17.5 feet; p.112 alarm signifying terminal filter headloss is currently set at 11.0 feet).
- Clearwell normal operating band: max 449.0 ft, normal 446.5-448 ft, 8-10 ft depth (p.112 normal maximum water level in treated water storage area and clearwell is 449.0 feet, six-inches below elevation of an overflow weir; p.112 normally operated between about 446.5 feet and 448 feet; p.114 maintain clearwell level between approximately 8 feet and 10 feet depth, which is 3 to 1 feet below overflow weir).

Standards quoted exactly as in `standards_checks` (see QA/QC Summary for disagreements with analysis text):

- `W-PS-02 - status: pass - value: 17.9 - limit: >= 1.0 ratio - rule: Raw water pumping station: firm capacity (largest pump out of service) must convey the treatment facility design flow. - citation: Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 6.2.1 (pdf p.187 (printed p.136)) - basis: hsps-18a`
- `W-PS-03 - status: FAIL - value: 0.9944 - limit: >= 1.0 ratio - rule: Finished-water and booster stations should deliver max-day demand (plus largest fire flow where fire protection is provided) with the largest pump out of service. - citation: Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 6.2.1 (pdf p.187 (printed p.136)) - basis: hsps-18a`
- `W-FIL-01 - status: pass - value: 3.0 - limit: between [2, 4] gpm/sf - rule: Typical rapid-rate gravity filtration rates 2 to 4 gpm/sf; any rate must be justified to the reviewing authority (advisory range, not a hard cap). - citation: Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 4.3.1.2 (pdf p.94 (printed p.43)) - basis: base-profile`
- `W-FIL-02 - status: not checked - rule: At least two filters; with more than two, design capacity met with the largest filter out of service. - reason: basis altB-6filt is a profile run; this rule needs a pumps run - citation: Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 4.3.1.3`

**Explicit disagreement statement:** Analysis text for run `hsps-18a` reports firm 17.90 mgd / 17.896 mgd with largest unit out, which is <18 mgd and therefore FAILS firm = largest unit out. This disagrees with `W-PS-02` status `pass` (value 17.9, basis hsps-18a). It agrees with `W-PS-03` status `FAIL` (value 0.9944, basis hsps-18a). Analysis text for filters reports 6x3 mgd = 18 mgd all-in but N-1 5x3=15 mgd <18 mgd, which cannot be confirmed or cleared by `W-FIL-02` because `W-FIL-02` status is `not checked` for basis `altB-6filt`.

## Data and Assumptions

Key field / report data used (data_register):

- DR-02: sustained 11.5 mgd warm low-turbidity pretreatment (p.111).
- DR-03: 3.5 to 5.0 mgd normal cold high-turbidity flows (p.111).
- DR-04: 14 mgd intake with Pump Nos. 1, 2 and 4 operating on September 14, 2006 (p.109).
- DR-05: firm 15.0 mgd in 2002 test (p.109).
- DR-06/DR-07: 30-in diam, 1/4 wall raw-water pipeline; 30-in mag meter (p.110).
- DR-08/DR-09/DR-11: launder weir invert 465.83 ft (p.111); trough bottoms 464.63 ft, 12 deep (p.111); overflow weir 465.0 ft, ~1.0 above normal filter level (p.111).
- DR-10: 1.5 ft freeboard (p.111).
- DR-12/DR-13/DR-14/DR-15: 42-in settled-water pipe (p.111); 2.9 fps at 18 mgd, 3.9 fps at 24 mgd (p.111); 2.8-in at 13.1 mgd (p.111); channel 6-in below overflow weir at 13.1 mgd (p.111).
- DR-16/DR-17: 20-in filter inlet; 16-in bay drains, 18 common per filter (p.112).
- DR-18: 7% low vs raw-water mag meter (p.112).
- DR-19: 9.1 mgd raw, ~2 to waste, >3.4 each other two, Filter 3 offline June 29 2006 (p.113).
- DR-20/DR-21/DR-22/DR-23: 170000 gal at 10.5 ft zone 1; 324000 gal at 10.5 ft zone 2; 133000 gal at 10.5 ft zone 3; total 627000 gal, 75 (1.26 hr) at 12 mgd (all p.114).
- DR-24: 1.0 ft drop per backwash (p.114).
- DR-25/DR-26/DR-27: 449.5 ft, 9 long HSPS weir; 4.5x4.5 chamber, 18 pipe; 450.00 ft, 15 long Filter 3 weir (all p.114).
- DR-28: 65000-75000 each, 260000-300000 per day backwash (p.114).
- DR-30/DR-31: 85000 added, 57 at 18 mgd (p.115); 1000000 needed, 288000 short at 24 mgd (p.115).
- DR-32/DR-33/DR-34: No.1 1400 (2.0) at 305 TDH 150hp; Nos.2-4 2800 (4.0) at 305 TDH 300hp (p.115); 1987-1988, space for 2 more (p.115); 10 nominal firm, ~3300 each observed (p.115).
- DR-35/DR-36/DR-37: 18 to 30 header, 29.25 ID, 3/8 wall (p.116); 30-in propeller meter (p.116); Table 4-3 8/2.65/0.109/0.05; 12/3.98/0.246/0.11; 18/5.97/0.553/0.25; 20/6.63/0.682/0.32; 24/7.96/0.984/0.44 (p.117).
- DR-38: 1900 (14200) surge tank (p.117).
- DR-40/DR-41: 9400 parallel, 1600 of 27 parallel to 24 (p.118); 30 + second parallel 30 future (p.118).
- DR-42/DR-43/DR-44/DR-45: 1050 at 6.4 60hp, 8 main air (p.118); 3250 at 41, 50hp, 1 duty 1 spare backwash (p.118); 16 header (p.118); 4400 est for 1.1mm anthracite, 4060 tested (p.119).
- DR-46/DR-47/DR-48: 16 to channel, 24 to MH, 30 to WWPS drains (p.119); 3x1500 at 40 35hp, 10 discharges, 16 transfer, 3000 firm WWPS (p.119); 300000 each, 2 basins (p.119).
- DR-49 to DR-54 drawing elevations (dwg p.136): 453.0, 450.0, 432, 425.5, 420, 415.5, 408.0 intake; 467.5 top, 466.0 WS rapid mix; 454.0 floc invert; 465.98 max, 465.00 weir, 464.83 WS, 454.0 invert sed; 464.0 filters, 467.5 top, clearwell 453.5/449.0/452.0, 449.5 weir, 438.5 invert.

ASSUMPTIONS (labelled per RFI resolutions, analysis.assumptions):

- ASSUMPTION (RFI-01): raw-water firm ~14-15 mgd as tested (p.109) until pump curves + retest prove 18 mgd.
- ASSUMPTION (RFI-02): 30-in raw-water headloss proxied by finished-water Table 4-3 form (p.117) until multi-flow test. QA/QC finds this proxy invalid because p.110 Table 4-1 was available (see QA/QC).
- ASSUMPTION (RFI-03): basin limits enforced at OF weir 465.0 ft, launder 465.83 ft, max WS 465.98 ft, 1.5 ft freeboard (p.111)(dwg p.136).
- ASSUMPTION (RFI-04): 4 existing filters x 3 mgd treatment, 4 mgd hydraulic, 2 mgd to waste (p.112-p.113).
- ASSUMPTION (RFI-05): settled-pipe calibration single point 2.8-in at 13.1 mgd (p.111); extrapolated by fitted Q^2, needs step test.
- ASSUMPTION (RFI-06): HSPS firm 10 mgd nominal (p.115); ~3300 gpm observed is system-specific.
- ASSUMPTION (RFI-07): site 30-in main acceptable above 6 fps for short segment (p.116-p.117) but offsite capacity above 18 mgd unproven.
- ASSUMPTION (RFI-08): surge limited to 14.0 mgd / 150 psi / HGL 630 ft (p.117) until transient rerun.
- ASSUMPTION (RFI-09): 60-min rule (p.115) as screening (57 min ~ minimum) but CT pass/fail requires Section 3 + tracer.
- ASSUMPTION (RFI-10): dwg WS values as 22 MGD ultimate-profile targets (dwg p.136 note), not existing; calibrated to Sept 2006 points (13.1 mgd +6-in below weir, 9.1 mgd waste split) (p.111)(p.113).
- ASSUMPTION (profile geometry): lengths 250 ft settled-pipe, 60 ft 18-in effluent, 40 ft 20-in inlet, 800 ft site-main, minor_k 4.5/2.0, weir lengths 100 ft (200 ft doubled), drop loss_ft 0.02/0.05/0.1/0.2/0.3 at 12 mgd have no p.N citation — ASSUMPTION requiring survey/field verification.
- ASSUMPTION (RFI-11): 18 mgd requires measurement/control of filter-to-waste at full filter rate plus compliant metering.
- ASSUMPTION (RFI-12): WWPS/basins adequate for 12 mgd as described; 18 mgd unproven pending mass balance.

Open RFIs RFI-01 to RFI-12 require test plan T-01 to T-12 (pump retests, headloss surveys, level surveys, filter N-1 test, system-head test, surge re-analysis, CT/tracer, datum reconciliation, metering test, solids cycle test).

## Model Calibration

Base runs: `hsps-exist2`, `base-profile`; design run: `altB-6filt`.

| Run | Measured (source) | Simulated | Residual | Note |
|---|---|---|---|---|
| `base-cal` (T-05) | 0.233 ft (2.8-in) at 13.1 mgd (p.111) (DR-14) | 0.233 ft settled-pipe loss | 0.0% | CALIBRATION point: fitted loss coefficient; implied C~75. Cannot also validate. |
| `base-cal` (T-05/T-10) | 464.50 ft (465.0 weir minus 6-in, p.111) at 13.1 mgd (DR-15 + dwg p.136 465.00 weir) | ~464.52 ft settled-channel WS | Analysis claimed 8.0% of settled-pipe+channel headloss (~0.28 ft), not of elevation | QA/QC rerun: validation fails. Rerun `base-profile` at 12 mgd gives 464.43 ft vs drawing 464.83 ft residual -0.40 ft; headloss ~0.25 ft => residual ~160% of headloss, not 8%. Calibration point reused as validation - not independent. C~75 flags fouling/length error. Requires multi-flow test. |
| `base-profile` (T-10) | 449.0 ft normal max (p.112), filters 463-464 ft (p.112), rapid-mix 466.0 ft / sed 464.83 ft (dwg p.136) (DR-50/52/53) | 449.02 ft, 464.0 ft, 466.85 ft at 18 mgd | Analysis claimed 5.0% | Drawing WS check: clearwell residual 0.02 ft, filters 0.0 ft (control), rapid-mix 0.85 ft high at 18 mgd vs 22 MGD drawing target - expected (different flow). Rerun rapid-mix residual +0.48 ft at 12 mgd rising to +1.15 ft at 18 mgd vs 466.0 dwg (p.136). |
| `hsps-exist2` (T-01/T-06) | 10 mgd nominal firm (p.115); ~3300 gpm each observed; 2006 intake 14 mgd with 1,2,4 (p.109) (DR-04/05 + DR-34) | 11.22 mgd firm, 14.85 mgd all-pumps | 12.2% vs 10 mgd nominal | Pumped-leg check: `hsps-exist2` firm 11.22 mgd vs 10 mgd nominal =+12.2%; all-pumps 14.85 mgd reproduces ~3300 gpm observation; intake 14 mgd confirms raw-water limit. |

Additional calibration facts from review: p.109 intake 14 mgd with Pumps 1,2,4 and firm 15.0 mgd 2002; p.110 Table 4-1 30-in raw-water velocities/headloss (18 mgd 5.9 fps, 0.25 ft/100 ft); p.117 Table 4-3 18 mgd 5.97 fps 0.553 ft V2/2g 0.25 headloss + surge 9700 gpm 14.0 mgd 150 psi HGL 630 ft; dwg p.136 BASED ON ULTIMATE PLANT FLOW OF 22 MGD. Runs checked: `hsps-exist2`, `base-profile`, `altB-6filt`.

## Capacity Evaluation (table)

`limits_target` = limits 18 mgd. `binds_at` = flow at which limiting.

| Unit | Limits 18 mgd? | Binds at | Evidence / run |
|---|---|---|---|
| RAW-WATER PUMP STATION + INTAKE | Yes | 14-15 mgd demonstrated (14 mgd 2006, 15.0 mgd firm 2002) (p.109) | `rw-18a` screening 4x4200 gpm firm 26.1 mgd shows 30-in main can carry 18 mgd (V=5.67 fps <6 fps); existing demonstrated 14 mgd / 15 mgd firm. Rehab + firm pump + VFD + retest required. |
| 30-IN RAW-WATER PIPELINE | No (hydraulically) | >18 mgd hydraulically (V=5.67 fps at 18 mgd <6.0 fps desirable) (p.116-p.117) | Velocity 5.673 fps (30-in at 18 mgd) + Table 4-3 5.97 fps at 18 mgd (p.117); `rw-18a` TDH 57 ft. QA/QC: Table 4-1 (p.110) 18 mgd 5.9 fps, V2/2g 0.54, 0.25 ft/100 ft; ID 29.5-in (30-in minus 1/4-in wall p.110) velocity 5.867 fps reconciles table. Uses nominal 30-in in screening — ASSUMPTION. |
| FLOCCULATION/SEDIMENTATION BASIN | Yes | 12.0 mgd basin rating; `prof-18test` first_limit floc-basin 12.0 mgd | Single basin rated 12 mgd (p.111); sustained 11.5 mgd warm/low-turbidity (p.111). |
| SED LAUNDERS + SETTLED CHANNEL + WEIR | Yes | 13.1 mgd launder submergence; 13.13 mgd max WS 465.98 ft; 18.75 mgd overflow weir 465.0 ft | `profile_capacity`: sed-launders 13.13 mgd (max WS 465.98 dwg p.136), settled-channel 18.75 mgd (weir 465.0 p.111). |
| 42-IN SETTLED-WATER PIPE | No | Hydraulic >18 mgd (0.42 ft at 18 mgd); calibrated 0.233 ft at 13.1 mgd (p.111) | `altB-6filt` loss 0.42 ft, V=2.90 fps at 18 mgd (velocity 2.895 fps for 42-in at 18 mgd); velocity 2.9 fps at 18 mgd, 3.9 fps at 24 mgd (p.111). |
| FILTERS 1-4 | Yes | 12.02 mgd treatment (4x3 mgd); 16 mgd hydraulic (4x4 mgd) | `profile_capacity` filters 12.02 mgd; p.112 3 mgd treatment vs 4 mgd hydraulic per filter. With 6 filters: 6x3=18 N but N-1 15 mgd <18 mgd — fails firm definition. |
| FILTER-TO-WASTE PIPING | Yes | ~2 mgd observed per filter; binds ~8 mgd plant all-in (~6 mgd N-1) approx only | 9.1 mgd test: ~2 mgd to waste, >3.4 mgd each other two (p.113); need 4.5 mgd/filter at 18/4. Single uncertain point, meters ~7% low (p.112) + straight-pipe violation — not rated curve. |
| CLEARWELL OVERFLOWS | No | 19 mgd HSPS weir alone; 24 mgd combined (p.114) | p.114 19 mgd at 1-ft depth, combined 24 mgd ultimate; `altB` clearwell margin 0.45 ft at 18 mgd to 449.5 ft weir. |
| CLEARWELL STORAGE | Yes (screen + treatment) | 57 min at 18 mgd (712k gal) vs 60-min screen; 75 min at 12 mgd | 627k gal total (170+324+133k p.114) =75 min at 12 mgd; +85k under Filters 5&6 =57 min at 18 mgd (p.115); 1.0 ft drop per backwash (p.114). CT ratio unproven; Section 3/tracer required. Hydraulic pass does not equal treatment pass (p.107). |
| HIGH-SERVICE PUMP STATION | Yes | 11.22 mgd firm (10 mgd nominal p.115); all-pumps 14.85 mgd; `hsps-18a` 17.90/17.896 mgd firm <18 mgd | `firm_capacity hsps-exist2`: 11.22 mgd governing large-unit outage; `hsps-18a` 17.896 mgd governing large-unit outage, all-pumps 20.402 mgd, 19.21 mgd with small out. Fails firm 18 mgd by ~0.1 mgd. |
| 30-IN SITE FINISHED-WATER MAIN | No (short segment) | 18 mgd V=5.97 fps, V2/2g 0.553 ft, headloss 0.25 ft/100 ft (p.117 Table 4-3) <6.0 fps; system head governs >18 | Table 4-3 (p.117) 5.97 fps at 18 mgd; velocity 5.968 fps for 29.25-in at 18 mgd (29.25 ID, 3/8 wall p.116); p.117 small headloss not significant for short segment. |
| SURGE TANK (1900 cf/14200 gal p.117) | Yes | 14.0 mgd surge rating (9700 gpm/14.0 mgd, 150 psi max, HGL 630 ft min p.117) | No steady-state run proves transient; re-analysis required precondition to HSPS uprate. `hsps-18a` steady-state cannot clear transient. |
| BACKWASH PUMPS + AIR SCOUR | No | Existing 3250 gpm adequate; 4400 gpm needed only for deep-bed >18 mgd | 4060 gpm tested at 45-deg (p.119) vs 4400 est for 1.1 mm anthracite; 1050 scfm air adequate (p.118); two 3250 gpm at 41 ft, 50hp, 1 duty 1 spare (p.118); 16-in header (p.118). |
| WASTEWATER PS + BASINS | Conditionally No — unproven at 18 mgd | 3000 gpm firm; 2x300k gal basins; 65-75k gal per wash (p.114)(p.119) | p.119 3x1500 gpm (3000 firm), 24-in/30-in drains; p.114 260-300k gal/day at 12 mgd. Mass-balance at 18 mgd not run (T-12). Marking non-limiting from screening alone is weak. |
| OFFSITE TRANSMISSION TO RESERVOIR HILL + RESERVOIRS | Conditionally No — unproven >14 mgd | Passes 18 mgd with small added headloss per screening; >18 needs higher head | Phase1 9400 ft + Phase2 1600 ft 27-in parallel 24-in (p.118 DR-40), future 30-in mains (p.118) status unverified; headloss to Reservoir Hill 710 ft (dwg p.136) not measured >14 mgd (T-07 not done). |

## Alternatives (table with cost class)

Costs quoted exactly as in `cost_estimates`. Where analysis text disagrees, stated explicitly.

| Unit | Least-cost modification (run) | Analysis cost_basis | Cost_estimates quote (exact) | Disagreement? |
|---|---|---|---|---|
| FLOCCULATION/SEDIMENTATION | Build 2nd floc/sed basin 12 mgd (2x12=24 total) (`altA-basin2` at 18 mgd passes settled-chan 464.93 ft <465.0 weir; launders 465.95<465.98; base binds 12.0 mgd) | Alt-pretreat-2nd-basin $1.24M Class 4 (-30%/+50%) | `Alt-pretreat-2nd-basin - total: 1238000.0 - dollars: 2023-09 (ENR CCI 13485.67) - aace_class: 4 - range: [866000.0, 1856000.0] - range_basis: AACE 18R-97 class 4: low -15% to -30%, high +20% to +50%; widest band shown - note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them. - lines: [C-FLOC-01 Flocculation basin, horizontal paddle, G=50 /s, construction cost, x: 50000.0 cf, qty: 1.0, unit_cost_base: 261549, base_year: 1978-10, escalation: 4.732, cost: 1238000.0]` | No material disagreement on total ($1.24M ≈ 1238000.0); estimate excludes land/engineering/contingency per note, and warns `low confidence: 1978-10 cost basis escalated x4.7 by ENR`. |
| FILTERS 1-4 + NEW 5-6 | Add Filters 5&6 at 3 mgd each (6x3=18 N; N-1 5x3=15 + margin) (`altB-6filt` at 18 mgd passes per-filter 3.0 mgd, effluent V=2.63 fps; base 4x3=12 binds 12.02 mgd) | Alt-filters-5-6 $4.10M Class 4 for 2000 sf structure (filters include 85k gal storage) | `Alt-filters-5-6 - total: 4100000.0 - dollars: 2023-09 (ENR CCI 13485.67) - aace_class: 4 - range: [2870000.0, 6150000.0] - range_basis: AACE 18R-97 class 4: low -15% to -30%, high +20% to +50%; widest band shown - note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them. - lines: [C-FIL-01 Gravity filtration structure (rapid sand/dual media), construction cost, x: 2000.0 sf, qty: 1.0, unit_cost_base: 866490, base_year: 1978-10, escalation: 4.732, cost: 4100000.0]` | No material disagreement on total; warns `low confidence: 1978-10 cost basis escalated x4.7 by ENR`. **Treatment-firm disagreement:** analysis marks `meets_target true` but corrected resolution marks 6-filter firm false (N-1 15<18). Requires 7th filter or approved higher rate — cost not in estimate. |
| FILTER-TO-WASTE | Re-pipe to full filter rate 4.5 mgd with modulating control + compliant metering/turbidity tap (`altB-6filt`; existing 2 mgd p.113 binds ~8 mgd / ~6 N-1; 9.1 mgd test reconciled) | Alt-waste-pipe-24in $53k Class 4 per 150 ft 24-in + valves/controls allowance -> $100k-$1M installed | `Alt-waste-pipe-24in - total: 53000.0 - dollars: 2023-09 (ENR CCI 13485.67) - aace_class: 4 - range: [37000.0, 79000.0] - range_basis: AACE 18R-97 class 4: low -15% to -30%, high +20% to +50%; widest band shown - note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them. - lines: [C-PIPE-01 Water pipeline, open cut, rural, soil, incl. appurtenances (any material), x: 24.0 in, qty: 150.0, unit_cost_base: 352, base_year: 2023-01, escalation: 1.0, cost: 53000.0]` | **Explicit disagreement:** analysis installed class `$100k-$1M` exceeds cost_estimates pipe-only total 53000.0 range [37000.0, 79000.0]. Cost_estimates is pipe only (150 ft 24-in); valves/controls/metering/turbidity tap not costed. |
| HIGH-SERVICE PS | Add 2x2800 gpm 305-ft TDH in spare spaces (6 total) + upsize No.1 1400->2800 + VFDs (`hsps-18a` firm 17.90 mgd largest-out, 19.21 with small out; existing `hsps-exist2` firm 11.22, nominal 10) | Alt-HSPS-2pumps $81k equipment only -> $100k-$1M installed with VFDs, header, controls | `Alt-HSPS-2pumps - total: 81000.0 - dollars: 2023-09 (ENR CCI 13485.67) - aace_class: 4 - range: [56000.0, 121000.0] - range_basis: AACE 18R-97 class 4: low -15% to -30%, high +20% to +50%; widest band shown - note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them. - lines: [C-PMP-01 Centrifugal booster pump (equipment purchase, uninstalled), x: 2800.0 gpm, qty: 2.0, unit_cost_base: 40306, base_year: 2021, escalation: 1.0, cost: 81000.0]` | **Explicit disagreement:** analysis installed `$100k-$1M` exceeds equipment-only 81000.0 range [56000.0, 121000.0]. Estimate warns `not escalated: source in 2021 $ indexed by PPI` and is uninstalled. Does not clear 18.0 firm (17.896<18). |
| SURGE TANK | Upsize/add vessel + re-analysis for 18 mgd to meet 150 psi / HGL 630 ft (p.117); existing rated 14.0 mgd/9700 gpm; no steady run proves transient | Alt-surge-tank $151k equipment only -> $100k-$1M installed | `Alt-surge-tank - total: 151000.0 - dollars: 2023-09 (ENR CCI 13485.67) - aace_class: 4 - range: [106000.0, 227000.0] - range_basis: AACE 18R-97 class 4: low -15% to -30%, high +20% to +50%; widest band shown - note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them. - lines: [C-TANK-01 Carbon steel pressure vessel (proxy for hydropneumatic / surge tank), equipment only, x: 20000.0 gal, qty: 1.0, unit_cost_base: 151174, base_year: 2021, escalation: 1.0, cost: 151000.0]` | **Explicit disagreement:** analysis installed `$100k-$1M` vs equipment-only 151000.0 range [106000.0, 227000.0]. Analysis marks `meets_target true` with run `hsps-18a`, but steady-state cannot prove transient — corrected to false, re-analysis precondition. Warns `not escalated: source in 2021 $ indexed by PPI`. |
| CLEARWELL STORAGE | 85k gal under Filters 5&6 (627k->712k; 57 min at 18 mgd p.115) + tracer/CT + baffling (`altB-6filt`; base 627k=75 min at 12 mgd p.114) | Alt-clearwell-85k $1.06M proxy (complete tank curve; actual under-filter storage built with Filters 5&6 at far lower incremental cost) | `Alt-clearwell-85k - total: 1063000.0 - dollars: 2023-09 (ENR CCI 13485.67) - aace_class: 4 - range: [744000.0, 1595000.0] - range_basis: AACE 18R-97 class 4: low -15% to -30%, high +20% to +50%; widest band shown - note: Order-of-magnitude capital cost from published curves at a national-average location (no location factor); excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them. - lines: [C-GST-01 Ground storage tank with roof (clearwell / reservoir proxy), x: 0.085 MG, qty: 1.0, unit_cost_base: 1063183, base_year: 2023-01, escalation: 1.0, cost: 1063000.0]` | **Explicit disagreement:** analysis states proxy overstates cost — actual under-filter storage built with Filters 5&6 at far lower incremental cost. Estimate warns `fixed term is most of this cost: the curve prices a complete facility, not added equipment`. 57 min <60-min screen (p.115) + CT unproven. |
| RAW-WATER PS + 30-IN MAIN | Rehab/test pumps (Pump 3 below rated), clean intake, add/replace 1 pump + VFD for 18 firm (`rw-18a` screening 4x4200 gpm firm 26.1 shows main can carry 18 at V=5.67 fps; existing 14 mgd 2006 / 15 firm 2002 p.109) | Alt-HSPS-2pumps (raw-water rehab allowance similar pump equipment + cleaning; cost n/a without curves) - cost_class $100k-$1M | No separate raw-water cost_estimate quoted; do not use HSPS 81000.0 as raw-water cost. | No cost_estimates total to quote for raw water; allowance uncosted pending T-01/T-02. |

Cost class summary per analysis: pretreatment $1M-$10M; filters $1M-$10M; waste <$100k pipe-only but $100k-$1M installed; HSPS $100k-$1M installed; surge $100k-$1M installed; clearwell $1M-$10M proxy; raw-water $100k-$1M allowance.

## QA/QC Summary

- Checked citations: p.109 intake 14 mgd with Pumps 1,2,4 and firm 15.0 mgd 2002; p.110 Table 4-1 30-in raw-water velocities/headloss (18 mgd 5.9 fps, 0.25 ft/100 ft); p.111 single basin rated 12 mgd, sustained 11.5 mgd; p.112 filter operating level 463-464 ft, 3 mgd vs 4 mgd; p.114 clearwell zones 170k/324k/133k gal total 627k gal 75 min at 12 mgd; p.117 Table 4-3 18 mgd 5.97 fps 0.553 ft V2/2g 0.25 headloss + surge 9700 gpm 14.0 mgd 150 psi HGL 630 ft; dwg p.136 BASED ON ULTIMATE PLANT FLOW OF 22 MGD.
- Checked runs: `hsps-exist2`, `base-profile`, `altB-6filt`.
- Major issues found (must resolve before design):
  1. HSPS `hsps-18a` 17.896 mgd firm <18 mgd — FAILS firm = largest out. Prior `meets_target true` / 17.90 meets 18 rejected.
  2. Raw-water Table 4-1 (p.110) available but proxy used; velocity tool 30.0-in 5.673 fps vs Table 5.9 fps. Pipe 1/4-in wall (p.110) => ID ~29.5-in not 30-in; finished main correctly 29.25-in ID (p.116). Headloss/length for `rw-18a` uncalibrated.
  3. Gravity profile lengths/minors/weir lengths/drops invented without p.N — now labelled ASSUMPTION.
  4. Calibration/validation residual misreported; validation fails (~0.40 ft vs ~0.25 ft ≈160%, not 8%; rapid-mix +0.48 to +1.15 ft vs 466.0 dwg p.136). C~75 implies fouling/length error.
  5. No `cost_estimate` runs logged for $1.24M/$4.10M/$53k/$81k/$151k/$1.06M — `cost_estimates` now quoted above but least-cost claim remains provisional pending `C-FLOC`/`C-FIL`/`C-PIPE`/`C-PMP`/`C-TANK`/`C-GST` verification with curve id, x, qty, ENR basis.
  6. Filter N-1 firm fails even with 6 filters (6x3=18 N, N-1 15<18 per firm definition + p.112 3 mgd rating; p.113 waste test Filter 3 offline). Requires 7th filter or 4.5 mgd rate with State approval.
  7. Filter-to-waste ~8 mgd (~6 N-1) extrapolated from single 9.1 mgd difference calc (p.113) with ~7% low meters (p.112) — approximate only, needs metered test.
  8. Steady-state `hsps-18a` used to clear surge transient (9700 gpm/14.0 mgd, 150 psi, HGL 630 ft p.117) — corrected to false; transient re-analysis required.
  9. Clearwell 57 min screening ≠ CT pass (p.107 treatment vs hydraulic; Section 3/tracer unavailable; 1.0 ft drop per backwash p.114, baffling unknown; CT ratio >=1.0 required).
- Minor issues: dwg 22 MGD (dwg p.136) vs text 24 mgd datum unresolved, Figure 4-2 (p.108) not recovered; capacity_table garbled `0.553 ft/1000? Table 4-3 0.25?` — corrected to V2/2g 0.553 ft vs headloss 0.25 ft/100 ft (p.117); offsite/wastewater marked non-limiting without T-07/T-12 (Phase1 9400 ft + Phase2 1600 ft 27-in/24-in p.118; future 30-in p.118; Reservoir 710.0 ft dwg p.136; WWPS 3000 gpm firm, 2x300k gal p.119).

## Recommendations

Per corrected findings (resolution):

- Pretreatment: 2nd 12 mgd floc/sed basin (24 total). ASSUMPTION lengths/minors need survey. Least-cost pretreat option pending `cost_estimate` run. Binds 12.0 mgd treatment (hydraulic ~13.1 mgd launder) (p.111).
- Filters: Add Filters 5&6 (6x3=18 N) PLUS 7th filter or approved higher rate to meet N-1 firm 18 mgd (existing 12 mgd treatment / 16 mgd hydraulic; N-1 with 6 =15 mgd) (p.112).
- Filter-to-waste: Re-pipe to full filter rate with modulating control/metering/turbidity tap; verify by multi-flow test (observed ~2 mgd p.113; meters ~7% low p.112).
- HSPS: Add 2x2800 gpm + upsize No.1 to 2800 gpm + VFDs AND uprate head/pump to clear 18.0 firm (existing 11.2 firm; screening 17.90 with 6x2800 <18) (p.115). Precondition surge re-analysis.
- Surge 1900cf/14200 gal (p.117): Transient re-analysis + upsize/add vessel for 18 mgd — REQUIRED precondition, not cleared (14.0 mgd rating p.117).
- Raw-water: Rehab pumps (No.3 below rated p.109), clean intake, add/replace firm pump + VFD + retest for 18 firm (14-15 demonstrated p.109; pipeline OK ~5.9 fps p.110 Table 4-1, ID 29.5-in per 1/4-in wall p.110, velocity 5.867 fps reconciles table).
- Clearwell: 85k gal under Filters 5&6 + tracer/CT + baffling; usable volume reduced by backwash drawdown (627k=75 min at 12 mgd p.114; 712k=57 min at 18 mgd vs 60-min p.115; 1.0 ft/backwash p.114).
- Drawing changes anchored: 2nd basin at OF weir 465.0 (dwg p.136); Filters 5-6 at oper level 464.0, top 467.5 (dwg p.136); waste header hold 464.0; HSPS hold 449.0/449.5 (dwg p.136); surge protect 150 psi/HGL 630 ft (p.117); raw-water to rapid mix 466.0 (dwg p.136).

No 18 mgd operation until T-01 to T-12 acceptance, surge transient stamp, and CT ratio >=1.0 demonstrated.

## Limitations

- DRAFT only; all conclusions provisional pending field tests T-01 raw-water retest, T-02 30-in headloss, T-03 basin survey, T-04 filter N-1, T-05 42-in headloss, T-06 HSPS/system head, T-07 offsite headloss, T-08 surge re-analysis, T-09 CT/tracer, T-10 datum survey, T-11 metering/waste test, T-12 solids cycle.
- Uses only Section 4 pages available; Section 2 filter design and Section 3 CT not available; Figure 4-2 (p.108) not in pages; p.109, p.110, p.115 truncated clauses withheld.
- Costs are order-of-magnitude Class 4 only, national-average, excluding land/engineering/contingency; raw-water, VFDs, header, controls, valves, baffling, 7th filter/hirate approval not fully costed.
- Treatment capacity (p.107) can limit below hydraulic; 60-min (p.115), 6 fps (p.116-p.117), 14.0 mgd surge (p.117) are screening limits, not design approval.
