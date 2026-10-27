DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum – K-State Campus Chilled Water System N+1 Capacity Through 2025

## Purpose

Evaluate whether existing chilled water production and distribution maintains N+1 reliability to 2025 peak of approximately 11,384 tons (p.24), identify what limits capacity and when, and summarize what should be built or upgraded (chillers, plants, pumps, piping) with order-of-magnitude cost class.

**Finding:** No. Existing N+1 of 6,050 tons (p.13), flow-limited to 5,840 tons if largest pump lost (p.14), covers existing peak 5,480 tons (p.17) with ~570 tons excess (p.17) but fails 2017 peak 8,946 tons (p.22) and 2025 peak 11,384 tons (p.24). Secondary N+1 11,680 gpm (p.14) and primary N+1 11,800 gpm (p.14) are similarly exceeded. Satellite plant, phased 2,000-ton chillers, added pumping, and 18-in loop cross-connects / upsizes are required.

## Background

Facility: Kansas State University campus chilled water system, Manhattan, Kansas. Source: Stanley Consultants, Kansas State University Chilled Water Master Plan, March 2013.

System configuration per JSON register:

* 7 chillers totaling 7,300 tons (p.13):
  * Chiller #1 York electric centrifugal 900 tons at CHW Plant 2004 (p.13)
  * Chiller #2 York electric centrifugal 1,250 tons at CHW Plant 2011 (p.13)
  * Chiller #3 York electric centrifugal 1,250 tons at CHW Plant 2011 (p.13)
  * Chiller #4 York electric centrifugal 1,250 tons at CHW Plant 2011 (p.13)
  * Chiller #5 York steam absorption 1,250 tons at CHW Plant 1998 (p.13)
  * Chiller #6 York steam absorption 1,000 tons at Power Plant 1997 (p.13)
  * Chiller #7 York electric centrifugal 400 tons at Power Plant mid-1990s (p.13)
* Chillers #5 and #6 nearing end of service life by 2020 (p.14); Chiller #7 by 2025 (p.14).
* Primary-secondary-tertiary pumping: Cooling Plant primary-secondary with three sub-loops: North, South, Chem-Biochem, fed from common header by secondary pumps; tertiary at buildings (p.14-p.15).
* Primary pumps PP-1 1,800 gpm, PP-2 to PP-5 2,500 gpm each, PP-6 2,800 gpm (p.14).
* Secondary pumps SP-1 to SP-5 2,920 gpm each (p.14).
* Cooling towers CT1-4 1,460 tons each at 3,500 gpm; CT5-6 918 tons at 2,200 gpm; CT7-9 487 tons at 1,168 gpm; CT10 501 tons at 1,200 gpm; EWT 95F LWT 85F (p.15).
* 31 buildings served by three loops (p.15).
* Distribution piping generally reliable with no known leaks, useful life beyond timeframe (p.18).
* Existing Cooling Plant has no space for additional chillers (p.24). Satellite plant site near Wind Erosion Lab (p.24) shown as six-chiller plant ~12,000 tons total (p.24).
* Proposed distribution: 18-in cross-connect Chem/BioChem to South Loop (p.46-view), 18-in cross-connect North Loop to Chem/Biochem (p.47-view), plus Increase CHW to 18-in at Hale/Willard/Waters, tunnel 10-in replacement with larger (12-18-in), 24-in north feed per Sheets 1-2 (viewed p.46-47).

Load growth:

* Existing connected 7,307 tons (p.17); estimated peak with diversity 5,480 tons (p.17); 2011 operating check ~5,400 tons with Chillers #2, #3, #4, #5 and #7 in operation (p.17).
* 2017 total ~11,928 tons (p.22); peak ~8,946 tons (p.22).
* 2025 total ~15,178 tons (p.23); peak ~11,384 tons (p.24).

## Design Criteria

* N+1 reliability requirement: Maintain N+1 for chilled water production; N+1 attained when design capacity is met with largest chiller out of service (p.20).
* Firm capacity: Capacity with largest unit of station out of service (p.20).
* N+1 reliability: Design capacity met with largest chiller out of service (p.20).
* Firm (N+1) cooling capacity – existing: 7,300 tons total, 6,050 tons N+1; flow-limited N+1 5,840 tons if largest pump lost (p.13).
* Diversity factor for peak: 0.75 applied to connected total to get estimated peak load (p.20).
* Chilled water design temperatures: 40 degF supply, 54 degF return (14F delta) (p.15).
* Design specific flow: 2 gpm per ton at design temperatures (p.18).
* Low delta-T check flow: 3.5 gpm per ton assuming 8F delta, most likely during low load (p.18).
* Local chillers excluded from loop capacity: University does not desire to use local chillers to supply campus loop, nor viable backup; not used to calculate loop capacity (p.18).
* Pump N+1 redundancy target: Add pump redundancy to achieve N+1 pumping capacity >= corresponding flow through chillers at N+1 cooling capacity (p.18).
* Distribution piping basis for new lines: For line sizes in Appendix B, assumed all distribution originates from existing Cooling Plant location; most existing piping sized sufficiently at 2 gpm/ton with some expansion capacity (p.24).
* Definitions: tons = cooling capacity in tons of refrigeration serving campus loop (p.13); gpm = flow in gallons per minute; 2 gpm/ton at 40F/54F design, 3.5 gpm/ton at 8F low delta-T (p.18); diversity factor = 0.75 factor to account for not all buildings at full load simultaneously (p.17); SF/Ton = square feet per ton cooling load by occupancy type from ASHRAE data (p.16); EWT/LWT = entering and leaving water temperature for condenser cooling towers (p.15).
* Standards basis: ASHRAE median service life and SF/ton loads; 2010 Facility Conservation Improvement Program report source for existing loads; Building Summary Report Dec 5 2011 + construction drawings Dec 16 2010 + field verification basis for square footage and chiller/pump/tower info.

## Data and Assumptions

Data used (register):

* CH-TOT 7,300 tons (p.13); CH-FIRM 6,050 tons N+1 (p.13); CH-FIRM-FLOWLIM 5,840 tons (p.14).
* SP-TOT 14,600 gpm (p.14); SP-FIRM 11,680 gpm N+1 (p.14); PP-FIRM 11,800 gpm N+1 (p.14).
* CHW-TEMP 40F supply, 54F return (p.15); FLOW-DESIGN 2 gpm/ton (p.18); FLOW-LOWDT 3.5 gpm/ton at 8F (p.18); FLOW-NOW ~10,960 gpm current loads require (p.20).
* PUMP-LIFE 20 years median for chilled water pumps (p.14); CT-LIFE CT1-4 modified 2011, fill/mechanical internals of these may require replacement before 2025; CT5-10 internals before 2025 (p.15).
* NEW-CHILLER-SIZE 2,000-ton for all new chillers except replacements in Scenario 1 (p.27); SCEN1-ADD 8,000 tons new + 1,250 tons replacement, largest 2,000 tons (p.26); SCEN2-ADD 10,000 tons new, 2,650 tons removed, largest 2,000 tons (p.27).

ASSUMPTION: Future flows 17,892 gpm (2017) = 8,946 tons (p.22) x 2 gpm/ton (p.18) and 22,768 gpm (2025) = 11,384 tons (p.24) x 2 gpm/ton; reason is report gives only tons, design flow per p.18.

ASSUMPTION: Costs are order-of-magnitude only; reason is capital costs withheld/not in pp.11-27,41-49.

ASSUMPTION: Throckmorton 2,300 gpm = 1,150 tons (p.42) x2 (p.18) = 3.312 mgd for velocity check; Union 2,400 gpm = 1,200 tons (p.42-43) x2 = 3.456 mgd; reason is to test 10-in adequacy noted undersized (p.42).

ASSUMPTION: Chiller/plant N+1 verified via flow proxy (gpm/tons at 2 gpm/ton p.18) because run_hydraulics models pumps; reason is chiller tons convert directly to required primary/secondary flow.

ASSUMPTION: Use reported totals 11,928 tons (2017) and 15,178 tons (2025) and peaks 8,946 and 11,384 tons as governing; reason is report explicitly states those totals with diversity despite table-sum differences ~100-300 tons.

ASSUMPTION: Treat 90-ft secondary and 40/70-ft primary heads as nameplate only; flag head/friction analysis as further study; reason is insufficient hydraulic data and report warns frictional losses may grow to exceed design head (p.25).

ASSUMPTION: Assume CT5-10 internals need replacement before 2025 and condenser pumps need review at 20 years; reason follows report guidance (p.15) and 20-yr pump life (p.14).

ASSUMPTION: List upsizes and 18-in cross-connects as proposed mitigations to be hydraulically verified later; reason is drawings are planning-level.

## Model Calibration

Header nameplate summation checks only; not loop friction/head proof.

| Test | Run label | Simulated | Measured (source) | Residual | Note |
|---|---|---|---|---|---|
| Secondary full capacity | BASE-SEC-FULL | 14,551.6 gpm total pumped | 14,600 gpm total (p.14) | -0.33% | 5x2,920 gpm (p.14) in parallel to low-loss header; matches nameplate within tolerance |
| Secondary N+1 capacity | BASE-SEC-FIRM | 11,654.3 gpm total pumped | 11,680 gpm N+1 (p.14) | -0.22% | 4x2,920 gpm largest out; confirms firm secondary governs vs 11,800 gpm primary |
| Primary N+1 capacity | BASE-PRI-FIRM | 11,740.8 gpm total pumped | 11,800 gpm N+1 (p.14) with PP-6 (2,800 gpm 70 ft p.14) out | -0.5% | 5x pumps (1,800+4x2,500 p.14) uniform 40 ft; full 6-pump run over-pumps due to single-point curve with mismatched heads, so firm run used |

Full 6-pump primary run not used for verification due to single-point curve simplification with mismatched 40-ft vs 70-ft heads (p.14).

## Capacity Evaluation (table)

| Unit / Subsystem | Limit (source) | Evidence (run + source) | Binds at / When | Limits 11,384-ton target? |
|---|---|---|---|---|
| Chillers – production N+1 | 6,050 tons N+1 (p.13), 5,840 tons flow-limited if largest pump lost (p.14); largest now 1,250 tons, new 2,000 tons (p.26-p.27) | BASE-SEC-FIRM 11,654.3 gpm firm vs 10,960 gpm current (p.20); chiller N+1 6,050 tons (p.13) flow-limited to 5,840 tons (p.14) | Existing peak 5,480 tons (p.17) leaves 570 tons excess (p.17); binds ~2013-2014 when load curve crosses N+1 (p.25-p.26 Fig 3-1), fails 2017 peak 8,946 tons (p.22) and 2025 peak 11,384 tons (p.24) | Yes |
| Secondary pumps SP-1 to SP-5 (2,920 gpm each) (p.14) | Secondary N+1 11,680 gpm (p.14) = ~5,840 tons at 2 gpm/ton (p.18) | BASE-SEC-FULL 14,551.6 gpm vs 14,600 gpm (p.14); BASE-SEC-FIRM 11,654.3 gpm vs 11,680 gpm (p.14); 2017 need 17,892 gpm ASSUMPTION per p.22,p.18; 2025 need 22,768 gpm ASSUMPTION per p.24,p.18 ~2x firm | Fails by 2017 (8,946 tons p.22 needs 17,892 gpm) | Yes |
| Primary pumps PP-1 (1,800 gpm) PP-2 to PP-5 (2,500 gpm each) PP-6 (2,800 gpm) (p.14) | Primary N+1 11,800 gpm (p.14) = ~5,900 tons at 2 gpm/ton (p.18) | BASE-PRI-FIRM 11,740.8 gpm vs 11,800 gpm N+1 (p.14); report warns add pump redundancy >= flow through chillers at N+1 (p.18) | Fails by 2017 alongside secondary; secondary binds first (11,680 vs 11,800 p.14) | Yes |
| Distribution – Throckmorton lateral | 10-in lateral hydraulically limited; most piping sized sufficiently with some expansion (p.18) except this segment | Velocity 9.395 fps in 10-in at 3.312 mgd (velocity tool) for 2,300 gpm (p.42,p.18) ASSUMPTION conversion; Sheet 2 shows Increase CHW to 18-in at Waters/Cardwell (viewed p.47) | Existing 1,150 tons / 2,300 gpm (p.42); already noted undersized (p.42) | Yes |
| Common header / North Loop – tunnel to Union/Kedzie | 10-in tunnel to Union/Kedzie via steam tunnel (p.18) | Velocity 9.804 fps in 10-in at 3.456 mgd (velocity tool) for 2,400 gpm Union alone (p.42,p.18) ASSUMPTION; Sheet 1 Replace 10-in in Tunnel with Larger (12-18-in) (viewed p.46) | Existing Union 610 tons (p.17) growing to 1,200 tons (p.42-43) + Kedzie; tunnel limits South Loop expansion to 2025 | Yes |
| Proposed 18-in cross-connect Chem/BioChem to South Loop (and North to Chem/BioChem) | 0 gpm isolated loops; frictional losses with expanded distance may exceed 90-ft secondary / 40-70-ft primary heads (p.14-p.15,p.25) | Sheets 1-2 propose 18-in Chem/BioChem to South + 18-in North to Chem/BioChem (viewed p.46-47); text requires cross-connection between loops + operational flexibility to isolate without compromising delivery (p.25) | No cross-connection existing; needed by 2017 to share backup and by 2025 for 15,178-ton connected / 11,384-ton peak (p.23-p.24) | Yes |

## Alternatives (table with cost class)

All cost_basis are ASSUMPTION order-of-magnitude ranges only; no capital costs in pp.11-27,41-49. High electrical cost noted but no dollars (p.24).

| Option | Result (run + source) | Cost class + ASSUMPTION basis | Meets 2025? | Recommended? |
|---|---|---|---|---|
| Scenario 2 – Add 2,000 tons in 2017, retire Chillers #5 (1,250 tons), #6 (1,000 tons), #7 (400 tons) (p.13) in 2020 (2,650 tons removed p.27) + add 2,000 tons in 2020/2021 to total 10,000 tons new (p.27); 2,000-ton units (p.27) – Run ALT-SEC-2025-FIRM on unit Chiller #6 steam absorption Power Plant (1,000 tons) | Arithmetic N+1 12,650 tons [7,300 tons (p.13)-2,650 tons (p.27)+10,000 tons (p.27)-2,000 tons largest (p.27)] exceeds 2025 peak 11,384 tons (p.24). Flow proxy ALT-SEC-2025-FIRM delivers 26,473.8 gpm firm (run output) exceeding 2025 need 22,768 gpm (ASSUMPTION: 11,384 tons p.24 x2 gpm/ton p.18) | >$10M – ASSUMPTION: >$10M for 5x2,000-ton chillers + satellite 12,000-ton plant shown (p.24) + towers/electrical near Wind Erosion Lab (p.24); no costs in pages. Basis is 10,000 tons new (p.27) displacing 2,650 tons retired (p.27) with 2,000-ton largest (p.27) | Yes | Yes |
| Scenario 1 – Replace Chiller #5 (1,250 tons p.13) in 2020 + add 8,000 tons (4x2,000 tons p.26-p.27) phased 2014/2018/2020/2023 per Fig 3-1 (p.26) – Run FUT17-FULL on unit Chiller #5 steam absorption at CHW Plant (1,250 tons) | Arithmetic N+1 ~13,300 tons [(7,300 tons p.13+8,000 tons p.26)-2,000 tons largest p.26] exceeds 2017 peak 8,946 tons (p.22) and 2025 peak 11,384 tons (p.24); flow proxy FUT17-FULL delivers 22,432.7 gpm full (run output) = ~11,216 tons at 2 gpm/ton (p.18) | >$10M – ASSUMPTION: >$10M for 4x2,000-ton chillers + towers + pumps + satellite building/electrical; no costs in pages. Basis is 8,000 tons new (p.26)+1,250-ton replacement (p.26) and p.24 high electrical cost note | Yes | No |
| Add secondary pumping: 1x4,000 gpm by 2017 (firm 18,503.7 gpm FUT-SEC-2017-FIRM) then total 4x4,000 gpm installed by 2025 (firm 26,473.8 gpm ALT-SEC-2025-FIRM) to raise firm above 11,680 gpm (p.14) – Run ALT-SEC-2025-FIRM on unit Secondary pumps SP-1 to SP-5 (2,920 gpm each) | FUT-SEC-2017-FIRM 18,503.7 gpm (run output) exceeds 2017 need 17,892 gpm (ASSUMPTION: 8,946 tons p.22 x2 gpm/ton p.18); ALT-SEC-2025-FIRM 26,473.8 gpm firm (run output) exceeds 2025 need 22,768 gpm (ASSUMPTION: 11,384 tons p.24 x2) | $1M-$10M – ASSUMPTION: $1M-$10M for 4x4,000 gpm 90-ft secondary pumps + headers/controls in new satellite; pump schedule 2,920 gpm 90 ft 100 hp (p.14) as basis; no costs in pages | Yes | Yes |
| Add/upgrade primary pumps to match secondary/chiller N+1 and replace CT5-10 fill/internals + condenser pumps as needed – Run BASE-PRI-FIRM on unit Primary pumps PP-1 (1,800 gpm) PP-2 to PP-5 (2,500 gpm each) PP-6 (2,800 gpm) | BASE-PRI-FIRM calibrates 11,740.8 gpm (run output) vs 11,800 gpm N+1 (p.14); future primary must track secondary 26,473.8 gpm (ALT-SEC-2025-FIRM) to avoid flow-limiting N+1 to 5,840 tons (p.14) | $100k-$1M – ASSUMPTION: $100k-$1M for primary pump additions/replacement (2,500-2,800 gpm 40-70 ft per p.14) and tower internals; towers CT5-10 internals may need replacement before 2025 (p.15), pumps 20-yr life (p.14) | Yes | Yes |
| Build Proposed 18-in Chem/Biochem to South Loop + 18-in North Loop to Chem/Biochem cross-connects (p.46-view,p.47-view), Increase CHW to 18-in at Hale/Willard/Waters (Sheet 1-2), Replace 10-in in Tunnel with Larger (12-18-in) – Run ALT-SEC-2025-FIRM on unit Proposed 18-in cross-connect Chem/BioChem to South Loop | Velocity 18-in adequacy not proven hydraulically; confirmed velocity 10-in at 3.312 mgd = 9.395 fps (velocity tool) for 2,300 gpm Throckmorton 1,150 tons (p.42) x2 (p.18) and 10-in at 3.456 mgd = 9.804 fps for 2,400 gpm Union 1,200 tons (p.42-43) x2; cross-connects provide loop redundancy/operational flexibility (p.25) | $1M-$10M – ASSUMPTION: $1M-$10M for buried 18-in loop cross-connects, tunnel 10-in replacement (12-18-in), Throckmorton upsize and 24-in feed to new north loads; routing/sizes per Sheet 1-2 drawings (viewed p.46-47) | Yes | Yes |

Notes: Future 4,000-gpm selections are ASSUMPTION (no future pump sizes in pp.11-27,41-49; only 5x2,920 gpm secondary p.14 and N+1 >= chiller flow rule p.18). FUT17-FULL 22,432.7 gpm (run output) is full (5x2,920 p.14 +2x4,000 ASSUMPTION). Firm FUT-SEC-2017-FIRM is 18,503.7 gpm (run output) (5x2,920+1x4,000). ALT-SEC-2025-FIRM 26,473.8 gpm (run output) is firm of 5x2,920+4x4,000 installed (8 running, largest out). Runs are planning proxies, not document-verified.

## QA/QC Summary

Checked citations verified: CH-TOT p.13 7,300 tons; CH-FIRM p.13 6,050 tons; CH-FIRM-FLOWLIM p.14 5,840 tons; SP-TOT p.14 14,600 gpm; SP-FIRM p.14 11,680 gpm; PP-FIRM p.14 11,800 gpm; CHW-TEMP p.15 40F/54F; LOAD-EXIST-TOT p.17 7,307 tons; LOAD-EXIST-PEAK p.17 5,480 tons; FLOW-DESIGN p.18 2 gpm/ton; LOAD-2017-PEAK p.22 8,946 tons; LOAD-2025-PEAK p.24 11,384 tons; PLANT-SPACE p.24 no space; NEW-PLANT-SIZE p.24 12,000 tons; XCONN-1 p.46-view 18-in Chem/Biochem to South; XCONN-2 p.47-view 18-in North to Chem/Biochem.

Checked runs rerun: BASE-SEC-FIRM 11,654.3 gpm; BASE-SEC-FULL 14,551.6 gpm; BASE-PRI-FIRM 11,740.8 gpm; FUT-SEC-2017-FIRM / ALT-SEC-2025-FIRM proxies noted above.

Major issues (action):

* Future 4,000-gpm pumps are ASSUMPTION without source; firm totals are planning proxies, not document-verified – fixed by labeling and separating full vs firm runs.
* Order-of-magnitude costs invented benchmarks with no source data – noted; recommendation based on N+1 shortfall (6,050 tons p.13 vs 8,946 tons p.22 and 11,384 tons p.24), not cost justification; detailed estimate required.
* Hydraulic models verify nameplate summation only (-0.22% to -0.51%), not loop friction/head for satellite near Wind Erosion Lab (p.24) – fixed by scope limit; p.25 warns losses may exceed 90-ft secondary (p.14) / 40/70-ft primary (p.14); detailed loop model still required.
* Peak flow proxy assumes 2 gpm/ton maintained; low-delta 3.5 gpm/ton (p.18) would be ~31,311 gpm in 2017 and ~39,844 gpm in 2025 ASSUMPTION arithmetic, exceeding proxies – noted; report states low delta-T most likely at low load (p.18); metering project (p.15) must verify per p.15,p.19 before final sizing.

Minor issues (action):

* Primary full-capacity invalid due to single-point curve – fixed, retained only firm BASE-PRI-FIRM.
* Baseline from 2010 FCIP + SF/ton (p.16) with no historical/metering (p.15), peak from staff interview 2011 operation ~5,400 tons (p.17) vs 5,480 tons estimate (p.17,p.20); totals 11,928/8,946 tons 2017 (p.22) and 15,178/11,384 tons 2025 (p.23-p.24) with 0.75 diversity carry unknown error – noted; future metering verification required.
* Throckmorton/tunnel 10-in inadequacy confirmed and noted undersized (p.42), but 18-in adequacy uses undocumented flow; 7 fps still high – fixed by rejecting undocumented 8.0 mgd check; upsizes planning-level without calculations.
* Condenser-water/tower and primary-pump adequacy for 8,000-10,000 tons new + 2,000-ton largest (p.26-p.27) not modeled; CT totals 9,638 tons [4x1,460+2x918+3x487+501 (p.15)] vs 7,300 tons chillers (p.13); CT1-4 last beyond study, CT5-10 internals before 2025 (p.15); pumps 20-yr life (p.14) – noted; phased renewals tied to retirements Chillers #5-6 by 2020, #7 by 2025 (p.14) require design verification.

## Recommendations

1. Build satellite plant near Wind Erosion Lab (p.24), ultimate ~12,000 tons (p.24) with 2,000-ton units (p.27). Prefer Scenario 2 phased 2,000-ton adds totaling 10,000 tons new (p.27), retiring steam absorbers Chillers #5-6 by 2020 and #7 by 2025 (p.14) (2,650 tons removed p.27) for arithmetic N+1 12,650 tons > 11,384-ton 2025 peak (p.24).
2. Add secondary pumping to maintain N+1 >= chiller flow (p.18): 1x4,000 gpm ASSUMPTION by 2017 to 18,503.7 gpm firm FUT-SEC-2017-FIRM (run output) > 17,892 gpm need ASSUMPTION (8,946 tons p.22 x2 p.18); total 4x4,000 gpm installed by 2025 to 26,473.8 gpm firm ALT-SEC-2025-FIRM (run output) > 22,768 gpm need ASSUMPTION (11,384 tons p.24 x2).
3. Add/upgrade primary pumps with new chillers to track secondary/chiller N+1 (p.18) and avoid flow-limit to 5,840 tons (p.14); replace 20-yr life pumps (p.14) and CT5-10 fill/internals before 2025 (p.15).
4. Build both 18-in cross-connects as loop backbone for satellite and redundancy (viewed p.46-47) to provide flexibility to isolate without compromising delivery (p.25); execute Increase CHW to 18-in at Hale/Willard/Waters + Fiedler 8-in + Architecture 8-in + tunnel 12-18-in + 24-in north feed per Sheets 1-2 (viewed p.46-47); verify head/loss with detailed loop model given 90-ft / 40-70-ft heads (p.14-p.15) and expanded distance friction warning (p.25).
5. Implement metering project (p.15) to verify 5,480-ton baseline (p.17) and 0.75 diversity, peak delta-T, and 2 gpm/ton vs 3.5 gpm/ton risk (p.18) before final pump/pipe sizing.

## Limitations

* Use only register facts; costs are ASSUMPTION ranges, not source estimates; detailed cost and schedule require design.
* Hydraulic runs prove header summation only (BASE-SEC-FULL, BASE-SEC-FIRM, BASE-PRI-FIRM residuals -0.33%, -0.22%, -0.51% vs p.14); do not prove satellite/extended-loop head adequacy; frictional losses may exceed design head (p.25).
* Future pump sizes/flows and 18-in adequacy not hydraulically proven; upsizes planning-level without calculations (viewed p.46-47).
* Low delta-T at peak (3.5 gpm/ton at 8F p.18) would exceed proxies; report assumes most likely at low load (p.18) without peak verification.
* Baseline and projections from ASHRAE SF/ton + 2010 FCIP without metering (p.15), peak from staff interview (p.17); error bars unknown; governing totals 11,928/8,946 tons (p.22) and 15,178/11,384 tons (p.23-p.24) subject to metering verification (p.15,p.19).
* Condenser/tower and primary-pump phasing for 8,000-10,000 tons new (p.26-p.27) not modeled; renewals tied to 2020/2025 retirements (p.14) need detailed verification.
* Existing plant has no expansion space (p.24); distribution sizing assumed from existing plant location (p.24) – satellite location changes hydraulics.
