DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum – Winchester Water Treatment Plant 12 mgd to 18 mgd Expansion Evaluation

## Purpose

Determine whether the Winchester Water Treatment Plant, Roseburg, Oregon can be expanded from its current 12 mgd to 18 mgd, and for each unit along the flow path determine whether it limits 18 mgd, the flow at which it becomes limiting, and the least-cost modification that makes 18 mgd work.

Source: City of Roseburg, Water Treatment Facilities Preliminary Design Report, July 2009 (public record) (https://roseburgor.gov/storage/app/media/PWD/Public%20Works%20Images%20and%20Docs/Water%20Treatment%20Facilities%20Preliminary%20Design%20Report.pdf).

## Background

- Current rated plant capacity: `12 mgd - treatment limitation determined by four existing filters` (p.107).
- Expansion nominal capacity target: `18 mgd - treatment limitation with ultimate buildout of six filters using same media as existing` (p.107).
- Hydraulic profile design flows: `original design 18 mgd max instantaneous; updated Figure 4-2 for 22 mgd max; drawing note ultimate 22 mgd` (p.108 (dwg p.136)).
- Peak operating range recent: `plant flow rate has ranged from approximately 3.5 mgd during low demand periods to 11.6 mgd during a recent peak summer day` (p.108) [DR-01].
- Water rights available: `20 mgd on North Umpqua River; additional rights investigated` (p.107).
- Flow path evaluated (units_on_path): River intake (gates, trash rack, traveling screens, pump bay) > Raw water pumping station (Pumps 1-4) > 30-in raw water pipeline + mag meter > Rapid mix basins > Flocculation/sedimentation basin > launders + channel + overflow weir/drain > 42-in settled pipeline > Filter influent channel + 20-in inlet per filter > Filters (Nos 1-4 + future 5-6) > Filter effluent piping to clearwell > Filter-to-waste piping > Clearwell + overflows > High service pump station > 30-in finished main WTP site + header + meter > Transmission WTP to Reservoir Hill terminal reservoirs > Hydropneumatic surge tank > Backwash pumps/piping + air scour > Backwash waste channel/piping > Wastewater pump station + transfer > Washwater/solids basins + drying beds > Terminal reservoirs on Reservoir Hill.

Definitions used:

- `firm vs true firm: Nominal firm = sum of all installed pumps minus largest pump at rated TDH; True firm = same but at actual operating point on system curve` (p.108 p.115).
- `hydraulic vs treatment capacity: Treatment capacity = ability to meet regulatory/industry standards; Hydraulic capacity = piping/pumping/volume/flow control ability to pass water` (p.107).
- Firm pumping capacity definition: `maximum flow with one of the largest installed pumps out of service` (p.108).

## Design Criteria

Quoted from collection criteria:

- Current rated plant capacity (p.107): `12 mgd - treatment limitation determined by four existing filters`
- Expansion nominal capacity target (p.107): `18 mgd - treatment limitation with ultimate buildout of six filters using same media as existing`
- Firm pumping capacity definition (p.108): `maximum flow with one of the largest installed pumps out of service`
- Fish protection approach velocity (p.109): `0.4 fps maximum at gates outside fish screens, fully submerged`
- Maximum desirable transmission main velocity (p.110 p.116): `6.0 fps in steel transmission main; short WTP-site segment may allow higher`
- Floc/sed basin freeboard adequacy (p.111): `approx 1.5 ft from max water surface to top of walls is adequate`
- Filter normal operating level (p.112): `463 to 464 ft, controlled by effluent flow control; 5 to 6 ft submergence over media`
- Filter driving head available (p.112): `approximately 15 to 17.5 ft from filter water level to treated water storage level (446.5-448 ft); alarm at 11.0 ft terminal headloss`
- Per-filter treatment rating (existing media) (p.112): `3 mgd per filter treatment limitation; hydraulically 4 mgd per filter to clearwell; 6 filters = 24 mgd hydraulic`
- Clearwell normal limits (p.112 p.114): `normal max 449.0 ft, 6-in below overflow; normally operated 446.5 to 448 ft`
- Clearwell detention desirability criterion (p.115): `minimum approx 60 minutes detention at peak flow; 1-hour criterion = 1,000,000 gal at 24 mgd`
- Surge protection performance criteria (p.117): `protection to 9,700 gpm (14.0 mgd); max upsurge 150 psi; min downsurge HGL 630 ft (approx 175 ft head or 75 psi at grade 455 ft)`
- Hydraulic profile design flows (p.108 (dwg p.136)): `original design 18 mgd max instantaneous; updated Figure 4-2 for 22 mgd max; drawing note ultimate 22 mgd`

## Data and Assumptions

Key plant data (data_register quotes retained):

- DR-02 (p.108): `one with a capacity of 2,800 gpm (4.0 mgd) at 49 feet of total dynamic head (TDH)` – Pump 1, 50 hp.
- DR-03 (p.108): `three, each with a capacity of 4,200 gpm (6.0 mgd) at 49 feet of TDH` – Pumps 2,3,4, 75 hp motors.
- DR-04 (p.108 p.107): `nominal firm capacity of the intake is approximately 16 mgd; maximum raw water pumping rate with all raw water pumps operating is nominally 22 mgd`.
- DR-05 (p.109 p.107): `On September 14, 2006 with Pump Nos. 1, 2 and 4 operating, the intake provided only 14 mgd; Testing in 2002 determined firm capacity approx 15.0 mgd; total combined flow of all four raw water pumps was 20.9 mgd on June 24, 2003`.
- DR-08 (p.109): `maximum flow into each sluice gate is 4.14 mgd and maximum flow into intake with all four gates open is 16.5 mgd; limited to 16.5 mgd by current regulatory constraints`.
- DR-06 (p.109): `four gated openings to the North Umpqua River, each 4 feet square` – `adequate to 24 mgd or more`.
- DR-07 (p.109): `two traveling screens which screen the raw water before it enters the pump bay. These screens will pass up to 18 mgd or more; two 5 feet square gated openings between traveling screens and pump bay adequate to 24 mgd or more`.
- DR-12 (p.110): `8 mgd 2.6 fps 0.116 ft 0.05 ft/100ft; 12 mgd 3.9 0.24 0.11; 18 mgd 5.9 0.54 0.25; 20 mgd 6.5 0.66 0.32; 24 mgd 7.8 0.90 0.44`.
- DR-13 (p.111): `single existing basin is rated at 12 mgd; designed to be expanded with parallel basin for ultimate nominal treatment 18 mgd, but with approx 24 mgd hydraulic capacity`.
- DR-15 (p.111): `maximum water surface elevation with one rapid mix operating and slide gates fully open should be approx 466.0 feet; triangular launder weir invert approx 465.83 feet; bottoms of 12-inch deep troughs approx 464.63 feet`.
- DR-16 (p.111): `overflow weir elevation at 465.0 feet, approx 1.0 feet higher than normal filter operating level; approx 9 feet long with capacity approx 12 mgd assuming 9-inch depth; drain pipe 30-inches diam has capacity approx 10 mgd to diversion manhole with weir`.
- DR-18 (p.111): `During flow test Sept 14, 2006 head loss through pipe measured at 2.8-inches at flow rate 13.1 mgd; water surface in settled channel approx 6-inches below basin overflow weir`.
- DR-22 (p.112): `sum of individual filter effluent meters was approx 7 percent less than flow determined by more accurate magnetic flow meter measuring raw water flow (Sept 14, 2006 tour)`.
- DR-23 (p.112-p.113): `existing 8-inch filter-to-waste piping is too small to convey 3 mgd when filtering to waste; with raw 9.1 mgd Filter 3 offline, filter-to-waste approx 2 mgd while other two filters >3.4 mgd (June 29, 2006 Filter 1 to waste calc by difference)`.
- DR-24 (p.114): `Unbaffled under four filters approx 170,000 gallons; Baffled under chemical/blower approx 324,000 gallons; Unbaffled under high service approx 133,000 gallon; total max 627,000 gallons represents approx 75 minutes (1.26 hours) at 12 mgd`.
- DR-25 (p.115): `additional 85,000 gallons under Filters 5 and 6, bringing max to 712,000 gallons; At 18 mgd max detention 57 minutes; At 24 mgd using 1-hour criteria suggested minimum 1,000,000 gallons which is 288,000 gallons more than available at six-filter buildout`.
- DR-28 (p.115): `One pump (No.1) rated 1,400 gpm (2.0 mgd) at 305 feet TDH 150 hp; Three pumps (Nos 2,3,4) each 2,800 gpm (4.0 mgd) at 305 feet TDH 300 hp; installed Phase 2 1987-1988; space for two additional`.
- DR-29 (p.115 p.107): `current firm nominally 10 mgd; Since three largest operate at approx 3,300 gpm each under current hydraulics, true firm about 11.5 mgd; max instantaneous with all operating nominally 16 mgd, max actually achieved about 14 mgd`.
- DR-32 (p.117): `8 mgd 2.65 fps 0.109 ft 0.05 ft/100ft; 12 mgd 3.98 0.246 0.11; 18 mgd 5.97 0.553 0.25; 20 mgd 6.63 0.682 0.32; 24 mgd 7.96 0.984 0.44`.
- DR-33 (p.117): `1,900 cubic feet (14,200-gallon) tank designed for upsurge and downsurge protection between plant and terminal reservoirs caused by power outages`.
- DR-35 (dwg p.136): `RESERVOIR 710.0 (drawing label)`.
- DR-37 (p.119): `two constant-speed vertical turbine each 50 hp rated 3,250 gpm at 41 feet TDH; Only one required; discharge 16-inch header; tested Sept 14 2006 modulating butterfly ~45 deg open produced 4,060 gpm; optimum for deep bed (up to 1.1 mm anthracite) approx 4,400 gpm`.
- DR-39 (p.119): `wetwell three 35 hp submersible solids handling pumps each approx 1,500 gpm at 40 feet TDH each with 10-inch isolation and check valves; 16-inch transfer main to basins 1 and 2; approx firm 3,000 gpm one out`.

Assumptions used in analysis (labelled ASSUMPTION – all from analysis.assumptions):

- ASSUMPTION: Deficit is pump degradation + fouled intake/high TDH; cleaning + Pump1 4->6 mgd + VFD + fish screens achieves 18 mgd firm; verify by test (p.109).
- ASSUMPTION: Raw 30-in length field-measured; short length allows >6fps with higher-head pumps (p.110).
- ASSUMPTION: Accept stated ratings 12 mgd single / 18 mgd nominal two basins / ~24 mgd hydraulic (p.111) as treatment criteria.
- ASSUMPTION: Two basins freeboard adequate to 18 mgd; single basin ~12 mgd by weir/drain (p.111).
- ASSUMPTION: Calibrate 42-in to 2.8-in at 13.1 mgd (p.111) + dwg 464.83; shorten yard piping in expansion (p.111-p.112).
- ASSUMPTION: Accept 3 mgd/filter treatment, 4 mgd/filter hydraulic (p.112).
- ASSUMPTION: Meters 7% low (p.112); 8-in to-waste ~2 mgd (p.112-p.113); reconfigure to pass 3-4 mgd.
- ASSUMPTION: Total volumes 627k/712k at 10.5ft (p.114-p.115) with 1-ft backwash penalty; CT per Sec3.
- ASSUMPTION: Table 4-2 expansion achieves 18 mgd firm (p.116); spaces exist; >18 mgd needs higher head/system study.
- ASSUMPTION: WTP-site short segment >6fps acceptable (p.116-p.117); off-site needs Phase2/2nd 30-in per master plan (p.118).
- ASSUMPTION: Existing surge only to 14 mgd; larger tank needed, 2nd impractical (p.117).
- ASSUMPTION: Backwash adequate existing media to 18 mgd one duty/one standby; upsize 24-in to 30-in (p.119).
- ASSUMPTION: 2x300k gal +2 beds adequate to 18 mgd alternating fill/decant; verify by balance (p.119).
- ASSUMPTION (review fix): new fish screens >=69.6 sf submerged for 0.40 fps at 18 mgd; 30-in raw ID 29.5-in (30-2x0.25) giving 5.87 fps at 18 mgd; settled channel binds ~22-23 mgd two-basin; ~18.4 mgd at 6.0 fps raw.

## Model Calibration

Base runs: `base_model_run raw-existshort`; `base_profile_run base-grav2`; `design_profile_run rec-18grav`.

| Test | Run label | Simulated | Measured (source) | Residual | Note |
|---|---|---|---|---|---|
| Raw all-pump test 2003 | raw-existshort | 21.46 mgd all pumps (run raw-existshort) | 20.9 mgd all 4 pumps June 24 2003 (p.107 DR-05) | 2.7% (0.56 mgd high = 11% of pump TDH headloss) | validates system curve; within Class5 screening |
| 42-in settled pipe headloss | base-grav2 | 0.233 ft (run base-grav2 / grav-cal-13 calibrated) | 2.8-in (0.233 ft) at 13.1 mgd Sept 14 2006 (p.111 DR-18) | 0.0% | Fitted C=75 used; independent margin check: 6-in below overflow vs 0.60 ft simulated |
| Settled channel freeboard | base-grav2 | 0.60 ft margin (464.40 vs 465.0, run grav-cal-13) | 6-in (0.50 ft) margin to 465.0 overflow at 13.1 mgd (p.111 DR-18) | 43.0% (0.10 ft = 43% of 0.233-ft pipe headloss) | validates profile, not used to fit C |
| High-service firm test | hs-exist | 11.82 mgd firm, 16.37 mgd all pumps (run hs-exist firm) | 11.5 mgd true firm ~3,300 gpm ea; 14 mgd max achieved (p.115 DR-29) | 2.8% (0.32 mgd = 2.8% of flow, 12% of TDH margin) | validates HS curve |

Calibration limitations (see QA/QC): raw-existshort uses rated 2800/4200 gpm @49 ft curves, not degraded 14 mgd (2006 Pumps 1,2,4) / 15.0 mgd firm (2002) (p.109); profile not checked at drawing design flow 22 MGD (dwg p.136 Note 2); treatment limits entered as max_flow caps so profile_capacity echoes input.

## Capacity Evaluation

| Unit | Limits 18 mgd? | Binds at | Evidence (with p. citation + run) |
|---|---|---|---|
| River intake – gates fish protection | Yes | 16.5 mgd (4x4.14 mgd); screens 18+ mgd (p.109) | Fish approach 0.4 fps fully submerged (p.109 criterion); run raw-18short needs new screens |
| Raw pumping firm (largest out) | Yes | 16.4 mgd firm existing (run raw-existshort); 15.0 mgd 2002 test, 14 mgd 2006 Pumps1,2,4 (p.109) | Nominal firm 16 mgd (p.108); firm_capacity raw-existshort 16.40 mgd; fixed by 4->6 mgd swap to 18.16 mgd (run raw-18short) |
| 30-in raw pipeline velocity 6 fps desirable | No | ~19.0 mgd at 6.0 fps (5.67 fps at 18 mgd velocity tool; Table 4-1 p.110); corrected to ~18.4 mgd at ID 29.5-in ASSUMPTION | 30-in raw 5.9 fps 0.54 ft at 18 mgd (p.110 DR-12); short WTP-site segment may allow higher (p.110) |
| Floc/sed treatment + freeboard max WS 466.0 / top 467.5 (1.5 ft, p.111 dwg p.136) | Yes | 12.0 mgd treatment single basin; 18.0 mgd nominal two basins; 22-24 mgd hydraulic (p.111-p.112) | Single basin rated 12 mgd (p.111); rec-18grav 9.0 mgd/basin at 18 mgd total; profile_capacity rapidmix-2 18.01 mgd |
| 42-in settled pipe + channel | No | 22.7 mgd settled-channel 465.0 (profile_capacity rec-18grav); pipe per se to 24 mgd at 3.9 fps (p.111) | 2.9 fps at 18 mgd, 3.9 fps at 24 mgd (p.111 DR-17); calibrated loss 0.42 ft at 18 mgd (run rec-18grav) |
| Filters Nos.1-4 (+5-6) treatment vs hydraulic | Yes | 12.0 mgd treatment (4x3.0); 16.0 mgd hydraulic (4x4.0) existing; 18.0/24.0 with six filters | 3 mgd/filter treatment, 4 mgd/filter hydraulic to clearwell (p.112); profile_capacity filters 12.02 mgd existing, 18.03 mgd rec-18grav |
| Filter-to-waste capacity | Yes | ~2 mgd observed vs 3-4 mgd required (June 29 2006 Filter1 to waste calc, p.112-p.113) | 8-in too small to convey 3 mgd (p.112-p.113 DR-23) |
| Clearwell detention 60-min desirability + overflows | Yes (desirability) | 17.1 mgd for 60 min with 712k gal (712k/60min=17.09 mgd); 57 min at 18 mgd (p.115) | 627k gal =75 min at 12 mgd; +85k=712k with Filters5-6 (p.114-p.115); overflows 19 mgd 9-ft + combined 24 mgd (p.114) |
| High-service firm (largest out) | Yes | 11.8 mgd firm true existing (run hs-exist); 10 mgd nominal, 14 mgd max achieved (p.115) | 1x2.0 +3x4.0 mgd at 305 ft (p.115); firm_capacity hs-exist 11.82 mgd; fixed to 22.87 mgd by Table4-2 (run hs-18fix) |
| Finished 30-in WTP-site velocity | No | ~18.1 mgd at 6.0 fps (5.97 fps at 18 mgd Table4-3 p.117; 5.97 fps velocity tool ID29.25) | Short WTP-site header 18-to-30-in 29.25-in ID (p.116); small added loss not significant (p.117) |
| Surge protection | Yes | 14.0 mgd (9,700 gpm) protection; 150 psi upsurge / HGL630 ft downsurge (p.117) | 1900cf/14,200 gal tank (p.117 DR-33); larger tank required beyond 14 mgd total pumping |
| Transmission to Reservoir Hill (Elev 710 dwg p.136) | Yes | Off-site system per 1986 study; Phase1 9,400 ft done, Phase2 1,600 ft 27-in + 2nd 30-in pending (p.118) | Master-plan update determines if 2nd main prior/concurrent with 18 mgd (p.118 DR-34) |
| Backwash pumps/piping/air scour | No | Adequate to 18 mgd existing media/type; 4,400 gpm optimum deep bed > pumps (p.119) | 2x3,250 gpm at 41 ft, 4,060 tested, 1,050 scfm air (p.119); upsize 24-in to 30-in with new filters (p.119) |
| Wastewater PS + equalization | Conditional Yes | Firm 3,000 gpm (4.32 mgd) vs 3,250 gpm backwash (4.68 mgd) (p.119) | 3x1,500 gpm at 40 ft (p.119); 16-in to 2x300k gal basins +2 beds (p.119); mass balance test required |

Detailed findings add: Filters N-1 treatment with 6 filters is 15.0 mgd (5x3); 18.0 mgd requires 7 filters N-1 – not in report buildout; analysis text states 6x3=18 meets target all-in-service only. Clearwell usable < total due to 1-ft backwash drop 65-75k/wash, 8-10 ft band (p.114-p.115); CT per Sec3 withheld.

Standards checks – quoted exactly as in standards_checks:

- `rule_id W-PS-02, status pass, value 18.164, limit >= 1.0 ratio, rule "Raw water pumping station: firm capacity (largest pump out of service) must convey the treatment facility design flow.", citation "Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 6.2.1 (pdf p.187 (printed p.136))", basis raw-18short`
- `rule_id W-PS-03, status pass, value 22.869, limit >= 1.0 ratio, rule "Finished-water and booster stations should deliver max-day demand (plus largest fire flow where fire protection is provided) with the largest pump out of service.", citation "Recommended Standards for Water Works, 2022 Edition (GLUMRB Ten States Standards), Sec. 6.2.1 (pdf p.187 (printed p.136))", basis hs-18fix`

Explicit disagreements between analysis text and standards_checks (instead of picking one):

- W-PS-02 pass (18.164) uses nominal rated curves (run raw-18short). Analysis/review text states true firm is 14 mgd (2006 Pumps 1,2,4) to 15.0 mgd (2002) (p.109) with Pump 3 degraded, and 18.16 mgd after swap assumes cleaning+repair restores curves and must be proven by retest. Pass is therefore conditional, not proven.
- W-PS-03 pass (22.869) is WTP-site only (run hs-18fix). Analysis text states off-site head to Reservoir Hill Elev 710 (dwg p.136) and full transmission curve were not modelled, and deliverability at 18 mgd requires Phase2 1,600 ft + 2nd 30-in prior/concurrent per p.118. Pass does not prove delivery to Reservoir Hill.

## Alternatives

| Unit | Option (least-cost to 18 mgd) | Result (run) | Cost (quoted exactly from cost_estimates) / Cost class |
|---|---|---|---|
| Raw pumping – VFD only, retain 4-mgd Pump 1 | Not recommended – fails | Firm 15.54 mgd (run raw-alt-vfdonly) <18 mgd; fails fish-screen and pump-capacity limit | No separate cost_estimates entry; see raw-18-rec-full below for pump+VFD |
| Raw pumping – Replace Pump1 4->6 mgd + 2nd VFD + new fish screens + clean intake (report p.109) – RECOMMENDED | Meets 18 mgd | Firm 18.16 mgd (run raw-18short, largest out) meets 18 mgd; all-pumps 22.99 mgd | `cost_estimates raw-18-rec-full total 89000.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 5, range [45000.0, 178000.0]` – lines C-PMP-01 4200 gpm $54000 + C-VFD-01 75hp $35000. Analysis cost_class <$100k. **Disagreement to note:** Class 5 range upper bound $178,000 exceeds <$100k label; ranking is indicative. Separate `raw-18-rec total 54000.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 5, range [27000.0, 109000.0]` is pump only. |
| Floc/sed – Build parallel 2nd basin + 2nd overflow weir + shortened yard piping – RECOMMENDED | Meets 18 mgd | Two-basin nominal 18 mgd (run rec-18grav 9.0 mgd/basin); max WS 465.97 ft margin 0.03 ft at 18 mgd | `cost_estimates basin2-rec total 1216000.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 4, range [851000.0, 1824000.0]` – C-SED-01 5000 sf. Analysis cost_class $1M-$10M. |
| Filters – Add Filters 5-6 same media (6x3 mgd treatment, 6x4 mgd hydraulic) – RECOMMENDED for all-in-service | Meets 18 mgd all-in-service; fails N-1 treatment | Treatment 18.0 mgd, hydraulic 24 mgd (run rec-18grav); existing 4 filters limit 12.0 mgd | `cost_estimates filters-56-rec total 3239000.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 4, range [2267000.0, 4859000.0]` – C-FIL-01 1400 sf. Analysis cost_class $1M-$10M. |
| Filter-to-waste – Reconfigure to pass/control 3-4 mgd + relocate turbidity tap – RECOMMENDED | Removes limit | Removes ~2 mgd limit observed 2006 (p.112-p.113); required for 3 mgd/filter to waste | Reconfigure 8-in to-waste piping/valving - O&M piping <$100k ASSUMPTION – no cost_estimates entry. |
| Clearwell – As-is 712k gal max with Filters 5-6 (57 min at 18 mgd) | Does not meet 60-min desirability | 57 min <60-min desirability criterion (p.115); usable <total; CT to be checked in Sec3 | `no added volume; operate 446.5-448 ft + VFD level control` – cost n/a. |
| High service – Table 4-2 buildout: retain 1-4, add 6-mgd VFD + 4-mgd in existing spaces – RECOMMENDED (site only) | Meets site firm | Firm 22.87 mgd (run hs-18fix) >18 mgd; existing firm 11.82 mgd (run hs-exist) | `cost_estimates hs-18-rec-full total 136000.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 5, range [68000.0, 272000.0]` – C-PMP-01 4200gpm $54000 + C-PMP-01 2800gpm $40000 + C-VFD-01 100hp $41000. Analysis cost_class $100k-$1M. Separate `hs-18-rec total 54000.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 4, range [38000.0, 82000.0]` is 6-mgd pump only. **Disagreement:** analysis $100k-$1M label vs Class 5 range up to $272k – both exceed $100k, ranking qualified. |
| Surge tank – Replace 1900cf/14.2kgal with larger vessel (2nd impractical) – RECOMMENDED | Meets 18 mgd trip | Existing protects to 9,700gpm/14.0 mgd only (p.117); upsized vessel for 18 mgd trip to 150psi / HGL630ft | Surge study + vessel replacement $100k-$1M ASSUMPTION (space constrained p.117) – no cost_estimates entry. |
| Finished transmission to Reservoir Hill – Complete Phase 2 parallel + second 30-in per master plan – RECOMMENDED prior/concurrent | Required off-site | WTP-site 30-in 5.97fps at 18 mgd (p.117) ok short length; off-site two-pipe needed concurrent/prior to 18 mgd (p.118) | Phase 2 1600-ft 27-in/30-in + 2nd 30-in per 1986 plan; master-plan update - >$10M ASSUMPTION – no cost_estimates entry. Unused `cost_estimates test-pipe total 0.0, dollars 2023-09 (ENR CCI 13485.67), aace_class 5, range [0.0, 0.0]` applies to no alternative. |

Drawing changes anchored (drawing_changes):

- RIVER INTAKE (453.0): ADD new fish screens per 0.4 fps criterion; CLEAN intake before retest.
- RAW WATER PUMP STATION (466.0): REPLACE Pump 1 (4 mgd) with 6-mgd pump + ADD 2nd VFD (Pump 3 or 4).
- FLOCCULATION/SEDIMENTATION BASIN (466.0): ADD parallel 2nd basin + 2nd 9-ft overflow weir EL 465.0; SHORTEN yard piping.
- FILTERS (464.0): ADD Filters 5-6 same media (6x3 mgd treatment); UPSIZE 24-in waste to 30-in.
- FILTER-TO-WASTE PIPING (464.0): RECONFIGURE 8-in to pass 3-4 mgd + RELOCATE turbidity tap.
- CLEARWELL (449.0): ADD 85-kgal under Filters 5-6 (712 kgal max); HOLD 446.5-448 ft via VFDs.
- HIGH SERVICE PUMP STATION (449.0): ADD 6-mgd VFD + 4-mgd HS pumps in existing spaces per Table 4-2.
- SURGE TANK (449.5): REPLACE vessel for 18 mgd (2nd impractical).
- FINISHED TRANSMISSION (710.0): COMPLETE Phase 2 parallel (1600-ft 27-in/30-in) + 2nd 30-in to Reservoir Hill per master plan.

## QA/QC Summary

Checked citations: DR-04 p.108 nominal firm 16 mgd / 22 all-pumps; DR-08 p.109 fish 4.14 per gate / 16.5 total; DR-12 p.110 Table 4-1 5.9 fps at 18 mgd; DR-24 p.114 170k+324k+133k=627k / 75 min at 12 mgd; DR-28 p.115 1400(2.0)+3x2800(4.0) @305 ft; DR-35 dwg p.136 RESERVOIR 710.0 + Note 2 ultimate 22 MGD. Checked runs: raw-existshort, hs-exist, rec-18grav.

Open issues (review.issues – severity retained):

- Major – Raw pumping firm: Model uses rated curves; field 14 mgd (2006 Pumps1,2,4), 15.0 mgd firm (2002), Pump3 degraded (p.109). 18.16 mgd after swap assumes cleaning+repair; unverified. RFI-01 not closed.
- Major – Gravity profile calibration: Drawing Fig 4-2 Note 2 ultimate 22 MGD (dwg p.136). rec-18grav at 18.0 mgd reports 464.48 vs drawing_ws 464.83 residual -0.35 ft. Residual is not at drawing design flow; -0.35 ft = ~83% of 0.42-ft loss at 18 mgd. 22-mgd check missing.
- Major – Treatment vs hydraulic limits: Fitted to 2.8-in at 13.1 mgd (p.111); margin check residual 0.10 ft = 43% of headloss. Treatment limits (12/18 mgd basins, 3 mgd/filter) entered as max_flow caps, so profile_capacity echoes input. No independent hydraulic limit; N-1 missing.
- Major – Filters N-1: p.112 3 mgd/filter treatment, 4 mgd/filter hydraulic. 6x3=18 all-in-service only. With largest out, 5x3=15 <18 fails treatment (5x4=20 passes hydraulic). Least-cost 2-filter option does not meet N-1 treatment; 7th filter needed.
- Major – Intake fish protection: p.109 criterion 0.4 fps. 4x 4x4 gates =64 sf. 18 mgd =27.85 cfs =>0.435 fps >0.4. New screens not sized; no velocity/headloss calc. DR-08 screens 18+ mgd vs 16.5 mgd gate limit contradictory – gates govern until enlarged.
- Major – High service + transmission: hs-exist TDH 269.9 ft; firm 11.82 mgd matches p.115 true ~11.5. hs-18fix 22.87 mgd has no reservoir 710 ft (dwg p.136) or transmission curve; WTP-site 30-in only. p.118 Phase1 9400 ft + Phase2 1600 ft + second 30-in pending master plan. 18 mgd not proven deliverable.
- Major – Clearwell detention/CT: 627k gal max at 10.5 ft =75 min at 12 mgd; +85k=712k =57 min at 18 mgd (p.114-p.115). Report states actual usable < total (p.115) due to 1-ft backwash drop, 8-10 ft band, CT baffling in Sec3 withheld. No proof 18 mgd meets disinfection.
- Minor – Velocity diameter: Tool 5.673 fps (30.0-in) vs Table 4-1 p.110 5.9 fps. Pipe is 30-in steel 1/4-in wall (p.110) => ID ~29.5-in, ~5.86 fps. Finished main correctly uses 29.25-in ID (p.116) =>5.968 fps matches Table 4-3 5.97. Raw 6.0 fps crossing shifts to ~18.4 mgd ASSUMPTION.
- Minor – Wastewater/Residuals: p.119 3x1500 gpm @40 ft, firm 3000 gpm (4.32 mgd) vs backwash 3250 gpm (4.68 mgd) rated, 4060 tested, 4400 optimum deep bed. Firm < single backwash peak; mass-balance test required.
- Minor – Costs: Logged cost_estimate raw-18-rec-full $89k, hs-18-rec-full $136k Class5; basin2 $1.22M, filters $3.24M Class4. No catalogue IDs, x-quantities, or ENR escalation shown in analysis block; surge >$100k and transmission >$10M labelled ASSUMPTION. Least-cost ranking indicative.

Resolutions applied (from resolution.responses): report true vs nominal separately; calibration only to 13.1 mgd field test; clarify treatment-criteria vs hydraulic; state N-1 requires 7th filter; size screens >=69.6 sf ASSUMPTION; condition HS on Phase2/2nd 30-in; condition clearwell on Sec3 CT; correct raw velocity to ID 29.5-in; condition residuals on balance test; qualify costs as Class5/4 ranges.

## Recommendations

To make 18 mgd work (least-cost per report, with conditions):

1. Clean entire intake, repair/test pumps to verify curves, replace Pump 1 4-mgd with 6-mgd (4200 gpm) + add 2nd VFD on Pump 3 or 4 + install new fish screens >=69.6 sf submerged ASSUMPTION for 0.40 fps at 18 mgd; retest to prove 18 mgd firm per W-PS-02. [run raw-18short 18.16 mgd firm; run raw-alt-vfdonly 15.54 mgd fails].
2. Build parallel 2nd floc/sed basin + 2nd 9-ft overflow weir EL 465.0 + shortened yard piping. Two-basin nominal 18 mgd (run rec-18grav 9.0 mgd/basin). [Single basin limits 12.0 mgd].
3. Add Filters 5-6 same media for 18.0 mgd all-in-service (6x3 treatment, 6x4 hydraulic) (run rec-18grav); reconfigure 8-in filter-to-waste to pass/control 3-4 mgd + relocate turbidity tap [observed ~2 mgd limit (p.112-p.113)]; upsize 24-in waste to 30-in with new filters (p.119). Note: strict N-1 treatment at 18 mgd requires 7th filter (5x3=15 <18) – not in report buildout.
4. Operate clearwell 446.5-448 ft via VFDs with 712k gal max (57 min at 18 mgd on total; usable less). Accept <60-min desirability only if Sec3 CT verified – not proven here. Overflows (449.5 9-ft 19 mgd + 450.00 15-ft, combined 24 mgd (p.114)) adequate.
5. Add Table 4-2 high-service pumps (retain 1-4, add 6-mgd VFD + 4-mgd in existing spaces) + replace surge tank with larger vessel sized by surge study for 18 mgd trip (150 psi / HGL 630 ft (p.117)); 2nd tank impractical (p.117). Site firm 22.87 mgd (run hs-18fix) only – deliverability to Reservoir Hill Elev 710 (dwg p.136) requires completing Phase2 parallel (1600-ft 27-in/30-in) + 2nd 30-in prior/concurrent per master plan (p.118).
6. No upsizing of 30-in raw (ID 29.5-in ASSUMPTION, 5.87 fps at 18 mgd), 42-in settled (2.9 fps at 18 mgd, 3.9 fps at 24 mgd (p.111)), or WTP-site finished header (29.25-in ID (p.116), 5.97 fps at 18 mgd (p.117)) to 18 mgd; short lengths allow >6 fps with higher-head pumps (p.110 p.116-p.117).
7. Verify residuals by 24-hr mass balance: backwash 3250 gpm rated (4060 tested, 4400 deep-bed optimum (p.119)) vs wastewater firm 3000 gpm (p.119) with 2x300k gal basins +2 beds (p.119); upgrade firm if test fails.

Test plan required before design (test_plan): raw firm retest with cleaned intake; raw headloss survey; floc/sed profile; settled-pipe calibration; filter split/to-waste; clearwell volume/drawdown; high-service firm; transmission logging; surge verification; backwash/wastewater/solids balance – each with acceptance as listed (e.g., 2% meter repeatability, freeboard >=1.5 ft with two basins at 18 mgd, upsurge <=150 psi and downsurge >=HGL 630 ft at 18 mgd trip).

## Limitations

- Analysis uses only available pages Sec 4 + drawing Fig 4-2 (dwg p.136); Sec 2/3 treatment bases (G, detention, SOR, weir loading, CT, baffling) withheld – treatment ratings accepted as criteria ASSUMPTION.
- RFIs RFI-01 to RFI-14 unresolved except by ASSUMPTION (pump degradation vs head, pipe lengths, freeboard binding flow, filter rating basis, 7% meter bias, usable clearwell volume, HS system head to Elev 710, transmission Phase status, surge size, waste path coincident flows, solids balance, drawing legibility). Field confirmation and tests required.
- Costs are order-of-magnitude national-average, no location factor, excludes land/engineering/contingency unless curve includes them; Class 5 ranges -20% to -50% / +30% to +100%, Class 4 -15% to -30% / +20% to +50%; catalogue/ENR basis as in cost_estimates lines; surge and transmission costs are ASSUMPTION only.
- 18 mgd is achievable only with all listed modifications plus off-site transmission and CT verification; N-1 treatment compliance at 18 mgd not met by 6-filter buildout.
