DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum – Rittenhouse Boulevard Pump Station and Force Main Capacity

## Purpose

Evaluate whether the Rittenhouse Boulevard Pump Station and Force Main, West Norriton Township, Pennsylvania can convey the projected 20-year peak flow of 4,960 gpm (7.14 MGD) (p.3) [D01] with one pump out of service.

Firm capacity is defined as capacity with the largest unit out of service; here 2 of 3 pumps operating (Developer instruction).

Determine what limits firm capacity, and evaluate least-cost alternatives (pumps, impellers, force main) that achieve at least 4,960 gpm with two pumps operating. Verify each alternative's operating point.

Source: Gilmore & Associates, Rittenhouse Boulevard Pump Station capacity study for West Norriton Township, November 2020 (public record) (p.3, p.4, p.10, p.13).

## Background

- Station configuration: designed and built as a conventional wet well/dry well triplex pump station (p.4) [D17].
- Original pumps (c.1965): three 75 hp pumps, each capable of delivering 1,750 gpm (2.5 MGD) (p.4) [D18].
- Influent: A 24-inch cast iron gravity pipe discharged into the wetwell, which was approximately 37 feet below grade (p.4) [D19].
- Force main: pumped directly to the headworks of the Norristown Municipal Wastewater Authority (NMWA) Wastewater Treatment Plant (WWTP) located at 368 E. Washington Street via approximately 13,500 LF of 18-inch cast iron force main (p.4) [D20].
- 1983 upgrade pumps: new enlarged pumps, each rated at 100 hp, and capable of 2,000 gpm (2.9 MGD) (p.4) [D21].
- 1992 field test capacity (3 pumps): station had a capacity of approximately 3,200 gpm (4.6 MGD) with all three pumps operating. The recorded pump capacity was measured during a field test conducted on June 19, 1992 (p.4) [D22].
- 2016 field inspection capacity (2 pumps): field inspection concluded the flow capacity of the station, with two pumps operating, was approximately 3,200 gallons per minute (gpm) or 4.6 million gallons per day (MGD) (p.3) [D13].
- Rettew Aug 2013 projected capacity: less than half of the projected flow capacity of 6,600 gpm or 9.5 MGD as documented in the Rettew Design Engineer's Report dated August 2013 (p.3) [D14].
- Pre-2015 upgrade capacity: approximately 2.2 MGD lower than the previous flow capacity prior to the 2015 upgrade (6.8 MGD) (p.3) [D15].
- PA DEP permitted capacity: 4.14 MGD lower than the Pennsylvania Department of Environmental Protection (PA DEP) permitted capacity of 8.74 MGD (p.3) [D16].
- Existing pump impeller size: Existing Pump Performance Curve (17.25" Impeller) (p.13) [D33].

## Design Criteria

From collection criteria:

- Required firm capacity (largest unit out of service): >=4,960 gpm (7.14 MGD) with two pumps operating, one pump out of service (Task brief + p.3).
- Projected 20-year peak flow - design flow: 4,960 gpm = 7.14 MGD = 7,141,500 gpd (p.3).
- Peak flow methodology: 2,106,900 gpd historical avg (Jan 2016-Sept 2020) + 273,600 gpd growth (960 EDU x 285 gpd/EDU) = 2,380,500 gpd avg x PF 3.0 = 7,141,500 gpd peak (p.3).
- Static head basis for hydraulics: 29.35 ft (73.9 ft high point minus 44.55 ft wetwell Pump Off) (p.10).
- Force-main roughness basis: C=85 for 13,500 ft 18.24-in CIP existing force main; C=120 for 97 ft 18.49-in DIP and 32.3 ft 12.34-in DIP station piping (p.10).
- Existing pump curve basis: Existing Pump Performance Curve 17.25-in impeller, 1-pump and 2-/3-pump parallel curves vs system head curves as tabulated (p.13).
- 20-year peak flow definition: Total projected 20-year average daily flow multiplied by average daily dry-weather peaking factor 3.0 (p.3).
- EDU definition: Estimated dwelling unit; growth projected as 960 EDU at 285 gpd/EDU (p.3).
- Static head definition: High Point Elev minus Low Point Elev (Wetwell Pump Off) (p.10).
- C definition: Hazen-Williams roughness coefficient for force-main pipe (p.10).
- Equivalent length definition: Pipe length plus equivalent length of bends/valves/meters for head-loss calculation; total 14,505 ft (p.10).
- Parallel pump operation definition: 2 Pumps (Parallel) or 3 Pumps (Parallel) combined head-capacity curve vs 1/2/3-pump system head curves (p.13).

Standards / units use:

- PA DEP permitted capacity 8.74 MGD (p.3): Permit ceiling cited p.3 for comparison; design must not exceed permit without modification.
- Township Chapter 94 reporting + historical flows (p.3): Basis cited p.3 for growth and peaking projections.
- Hazen-Williams head-loss method (implied by C values): Use C=85/120 and diameters/lengths/equivalent lengths from p.10 in run_hydraulics.
- Document units (gpm, MGD, gpd, ft, in, hp): Retain as printed; 1 MGD = 694.44 gpm for checks.

## Data and Assumptions

Data register (available pages pp.3,4,10,13):

- D01: 4,960 gpm = 7.14 MGD = 7,141,500 gpd projected 20-year peak flow (p.3).
- D02: 2,106,900 gpd historical average daily flow Jan 2016-Sept 2020 (p.3).
- D03: 3.0 average daily dry weather peaking factor (p.3).
- D04: 960 EDU projected new connections within 20 years (p.3).
- D05: 285 gpd/EDU standard (p.3).
- D06: 273,600 gpd projected 20-year flow addition (p.3).
- D07: Riverview 330 EDU = 94,050 gpd (p.3).
- D08: Main & Schuylkill 22 EDU = 6,270 gpd (p.3).
- D09: Office Bldg @ Egypt 8 EDU = 2,280 gpd (p.3).
- D10: Westover 500 EDU = 142,500 gpd (p.3).
- D11: Miscellaneous 100 EDU = 28,500 gpd (p.3).
- D12: 2,380,500 gpd total projected 20-year average daily flow (Table 1 shows 2,380,511) (p.3).
- D23: 18.24-in dia x 13,500 ft CIP C=85, STA 0+00 to 135+00 (p.10).
- D24: 18.49-in dia x 97 ft DIP C=120, STA -0+97 to 0+00 (p.10).
- D25: 12.34-in dia x 32.3 ft DIP C=120, inside pump station piping (p.10).
- D26: 73.9 ft HIGH POINT ELEV. (p.10).
- D27: 44.55 ft LOW POINT ELEV. Wetwell Pump Off (p.10).
- D28: 29.35 ft STATIC HEAD (=73.9-44.55) (p.10).
- D29: 124.6 ft TOTAL EQV. LENGTH 18-in DIP fittings (p.10).
- D30: 156.4 ft TOTAL EQV. LENGTH 12-in DIP (p.10).
- D31: 594.2 ft TOTAL EQV. LENGTH 18-in CIP (p.10).
- D32: 14,505 ft Total Equivalent Length of Pipe (p.10).
- D34: 0 gpm = 29.35 ft (all 1/2/3-pump system heads) (p.13).
- D35: 3034 gpm: 114.04/111.29/110.74 ft; 3200 gpm: 122.81/119.78/119.16 ft (p.13).
- D36: 4800 gpm: 227.23/220.81/219.51 ft; 5000 gpm: 242.75/235.83/234.42 ft (p.13).
- D37: e.g., 0 gpm 152.68 ft; 2-pump 4800 gpm 111.47 ft; 2-pump 6000 gpm 101.67 ft; 1-pump points 1600 gpm 124.22 ft, 2000 gpm 116.44 ft, 4800 gpm 70.80 ft (p.13).
- D38: e.g., 3-pump 4800 gpm 124.22 ft; 6000 gpm 116.44 ft; 9000 gpm 101.67 ft; 9600 gpm 98.27 ft; 2400 gpm 137.48 ft; 3000 gpm 134.23 ft (p.13).

Units on path:

- 24-in CIP gravity influent to wetwell (~37 ft below grade) (p.4).
- Wetwell (low point 44.55 ft Pump Off) (p.10).
- Triplex dry-well pumps (existing 17.25-in impeller curves, p.13) (p.4, p.13).
- 12.34-in DIP discharge piping inside pump station (32.3 ft + 156.4 ft equiv, C=120) (p.10).
- 18.49-in DIP force main STA -0+97 to 0+00 (97 ft + 124.6 ft equiv, C=120) (p.10).
- 18.24-in CIP force main STA 0+00 to 135+00 (13,500 ft + 594.2 ft equiv, C=85) (p.10).
- High point (73.9 ft) controlling 29.35 ft static head (p.10).
- NMWA WWTP headworks discharge (368 E Washington St) (p.4).

Assumptions – RFIs (must be labeled):

- R-01: **ASSUMPTION:** Use run_hydraulics with D23-D32 geometry, C=85/120, static 29.35 ft (p.10); treat p.13 system-head columns as check data, not design basis. Reason: System-head table values withheld on p.10; only geometry/equivalent lengths legible.
- R-02: **ASSUMPTION:** Treat p.13 17.25-in curves as the as-tested existing-pump basis for no-change case; evaluate pump/impeller upsizes only by their published curves when pages become available, holding station piping as-is unless force-main alternative is tested. Reason: Pump make/model, speed, motor HP and VFD status for current 17.25-in pumps not on available pages (p.13 gives only impeller size and head-capacity points).
- R-03: **ASSUMPTION:** Adopt p.3 3,200 gpm with 2 operating as existing firm baseline for deficiency = 4,960-3,200 = 1,760 gpm shortfall; cite p.4 1992 3-pump value only as history. Reason: Conflicting capacity statements: 3,200 gpm with 2 pumps (p.3, 2016) vs 3,200 gpm with 3 pumps (p.4, 1992).
- R-04: **ASSUMPTION:** Design to 4,960 gpm firm; note Rettew 6,600 gpm and DEP 8.74 MGD only for context/permit headroom. Reason: Conflicting projections: Rettew 6,600 gpm/9.5 MGD (p.3) vs G&A 4,960 gpm/7.14 MGD (p.3).
- R-05: **ASSUMPTION:** Use 29.35 ft static head as printed for all run_hydraulics cases; note that lower wetwell levels would increase required head and would only worsen existing deficiency. Reason: Suction (wetwell operating) level for duty point vs 44.55 ft Pump-Off level (p.10) – duty static may be larger at low water.
- R-06: **ASSUMPTION:** Use listed actual IDs (18.24/18.49/12.34 in), lengths (13,500/97/32.3 ft), C values, and total equivalent 14,505 ft exactly as p.10; sensitivity to lower C to be noted as risk, not base case. Reason: Actual internal diameters/roughness (18.24 vs nominal 18; C=85 old CIP) and fitting counts partially legible.
- R-07: **ASSUMPTION:** Reach conclusions from facts on available pages; verify each alternative operating point by run_hydraulics intersection with quoted pump curves and velocity checks, and rank least-cost by pipe/pump scope qualitatively pending cost pages. Reason: Least-cost alternative costs, proposed impellers, parallel force-main sizing not on available pages.

Additional assumptions in analysis:

- **ASSUMPTION:** Arithmetic differences (e.g., 5049.2 minus 4960 = ~89 gpm; 4960 minus 3280.8 = ~1679 gpm; 6402.3 minus 4960 = ~1442 gpm; 5976.2 minus 4960 = ~1016 gpm) are arithmetic only.
- **ASSUMPTION:** Tool defaults default eff 0.80 / motor 0.95 used for shaft hp / kW (e.g., runs BASE2, ALT-A-HH2, ALT-B-PFM-EX, ALT-C-PFM-NP); no efficiency data on pp.3,4,10,13.
- **ASSUMPTION:** New parallel barrel same 18.24-in x 14094.2 ft with C=120 new-pipe roughness vs existing C=85 (p.10); 594.2 ft equiv (p.10) reuse is assumption; new-pipe diameter/material/C not on pages.
- **ASSUMPTION:** Illustrative pump ratings 2500 gpm at 240 ft (Alt A) and 2500 gpm at 105 ft (Alt C) selected to overcome ~235.83 ft at 5,000 gpm 2-pump (p.13) and ~90 ft duty; no manufacturer curve/HP/speed/VFD/eff/NPSH on pages.
- **ASSUMPTION:** Motor > shaft for margin (e.g., ~250 hp motors for ~190.3 hp shaft, run ALT-A-HH2); no motor data on pages.
- **ASSUMPTION:** Influent and outfall adequate pending Chapter 94 (p.3) review; lack of data, not proof of adequacy. No surcharge or headworks backup data on pp.3,4,10,13.
- **ASSUMPTION:** Linear interpolation between tabulated p.13 values for check only (e.g., ~124.17 ft at 3,280.8 gpm).
- **ASSUMPTION:** 14,094.2 ft modeled FM reach = 13,500 ft + 594.2 ft per p.10.

## Model Calibration

| Test | Measured (source) | Simulated (run) | Residual | Note |
|---|---|---|---|---|
| 2016 firm-capacity test (2 pumps) | 3,200 gpm (4.6 MGD) with two pumps operating, Feb 2016 field inspection (p.3) | 3,280.8 gpm total (4.724 MGD), per pump 1640.4 gpm at 123.43 ft TDH (run BASE2) | 2.5% (run BASE2) | Model reproduces firm-capacity test within 2.5%; geometry C=85 13,500 ft 18.24-in (p.10) plus C=120 station piping (p.10) and 29.35 ft static (73.9 ft minus 44.55 ft) (p.10); curves 17.25-in (p.13) |
| 1992 installed-capacity test (3 pumps) | 3,200 gpm (4.6 MGD) with all three pumps operating on 1992-06-19 (p.4) | 3,446.9 gpm total (4.964 MGD), per pump 1149.0 gpm at 131.74 ft TDH (run BASE3) | 7.7% (run BASE3) | **ASSUMPTION:** 1992 test was on 1983 100-hp 2,000 gpm pumps (p.4), not current 17.25-in pumps (p.13), so not direct calibration; shown for history. Current 3-pump model gives 3,446.9 gpm (run BASE3), +7.7% above 1992 value, consistent with different pump vintage. |
| System-head curve check (2-pump) | 2-pump system head 119.78 ft at 3,200 gpm and 136.08 ft at 3,500 gpm (p.13); interpolated ~124.17 ft at 3,280.8 gpm (**ASSUMPTION:** linear interpolation between tabulated p.13 values for check only) | 123.43 ft TDH at 3,280.8 gpm total (run BASE2) | -0.6% (run BASE2) | TDH matches interpolated system head within -0.6%, confirming Hazen-Williams C=85/120 (p.10), IDs 18.24/18.49/12.34-in (p.10), lengths 13,500/97/32.3 ft (p.10) and equiv 124.6/156.4/594.2 ft total 14,505 ft (p.10) are correctly coded |

Additional calibration sensitivity:

- C=70 sensitivity 2777.3 gpm 3.999 MGD (run BASE2-C70) shows C=85 (p.10) may be optimistic (findings evidence).
- 1-pump 2847.6 gpm at 104.16 ft (run BASE1).
- 1992 3200 gpm 3-pump (p.4) vs BASE3-3P +7.7% high (**ASSUMPTION:** arithmetic) not direct calibration (**ASSUMPTION:** different 100-hp 2000 gpm vintage p.4).

Checked runs: BASE2, BASE1, BASE3, ALT-PUMP-BIG, ALT-PFM-EX, ALT-PFM-NEWP (review checked_runs). Resolution runs: ALT-A-HH2, ALT-B-PFM-EX, ALT-C-PFM-NP, BASE2-C70.

## Capacity Evaluation (table)

| Unit | Limit | Binds at target? | Evidence / Binds at |
|---|---|---|---|
| Pump station firm (triplex, 2 of 3 operating; triplex p.4) | Firm 3,280.8 gpm (4.724 MGD) with 2 pumps, 17.25-in impeller (p.13) (run BASE2) | Yes | BASE2 firm 3,280.8 gpm (4.724 MGD) (run BASE2) < 4,960 gpm (7.14 MGD) (p.3), shortfall ~1,680 gpm (**ASSUMPTION:** 4,960 minus 3,280.8 arithmetic); 1-pump 2,847.6 gpm at 104.16 ft (run BASE1); 3-pump 3,446.9 gpm (run BASE3) still < 4,960 gpm (p.3); adds only ~166 gpm for 3rd pump (**ASSUMPTION:** 3,446.9 minus 3,280.8) showing steep system. Binds at ~3,281 gpm firm intersection (run BASE2); target 4,960 gpm (p.3) not reached. Low-C case ~2777 gpm (run BASE2-C70). |
| Force main STA 0+00 to 135+00 | Friction-controlled; existing 18.24-in x 13,500 ft CIP C=85 (p.10) + 594.2 ft equiv (p.10) | Yes | System 227.23 ft 1-pump / 220.81 ft 2-pump at 4,800 gpm and 242.75 ft / 235.83 ft at 5,000 gpm (p.13) vs 2-pump pump head only 111.47 ft at 4,800 gpm and 101.67 ft at 6,000 gpm (p.13); velocity at 7.14 MGD (p.3) in 18.24-in (p.10) is 6.089 fps (velocity tool) and at 6.8 MGD (p.3) is 5.798 fps (velocity tool); BASE2 FM velocity 4.03 fps at 3,280.8 gpm (run BASE2) rising to 6.2 fps at 5,049.2 gpm (run ALT-PUMP-BIG). Binds below 4,960 gpm (p.3); at 4,800-5,000 gpm system needs 220.81-235.83 ft 2-pump (p.13). |
| Station/connector piping (12.34-in + 18.49-in DIP C=120) (p.10) | Adequate; no independent limit below 4,960 gpm (p.3) in available pages – WITHDRAWN, see QA/QC. Revised: not proven adequate below 4,960 gpm (p.3); 6.77-8.59 fps branch velocities + 99.5-190.3 hp shafts vs unknown motors/ratings | Yes (revised) | 12.34-in x 32.3 ft + 156.4 ft equiv (p.10) and 18.49-in x 97 ft + 124.6 ft equiv C=120 (p.10); BASE2 branch 4.4 fps and PS18 3.92 fps at 3,280.8 gpm (run BASE2); ALT-PUMP-BIG PS18 6.03 fps at 5,049.2 gpm (run ALT-PUMP-BIG) high but system head still dominated by 14,094.2 ft FM reach (**ASSUMPTION:** 13,500 ft + 594.2 ft per p.10). Revised evidence: ALT-A-HH2 branch 6.77 fps PS18 6.03 fps at 5049.2 gpm (run ALT-A-HH2); ALT-B-PFM-EX branch 8.59 fps PS18 7.65 fps at 6402.3 gpm (run ALT-B-PFM-EX); ALT-C-PFM-NP branch 8.02 fps PS18 7.14 fps at 5976.2 gpm (run ALT-C-PFM-NP); per-pump 2524-3201 gpm exceeds original 1750 gpm 75-hp (p.4) and 1983 2000 gpm 100-hp (p.4) ratings. Binds as verification required. |
| Static head / wetwell level | 29.35 ft static (p.10) | No | 29.35 ft at all flows 0 gpm (p.13); 73.9 ft high point minus 44.55 ft Pump Off (p.10). Static 29.35 ft (p.10) << friction ~190-210 ft at 4,800-5,000 gpm (**ASSUMPTION:** system minus static using 220.81-29.35 and 235.83-29.35 from p.13 values); BASE2 TDH 123.43 ft (run BASE2) minus 29.35 ft (p.10) = ~94 ft friction (**ASSUMPTION:** subtraction for illustration). Does not bind before FM/pumps. |
| Gravity influent + NMWA WWTP headworks outfall | No evidence of limit (**ASSUMPTION:** lack of data, not proof of adequacy) | No | n/a in available pages; 24-in CIP ~37 ft below grade influent (p.4) to NMWA headworks via ~13,500 LF 18-in (p.4). No surcharge or headworks backup data on pp.3,4,10,13; pump/FM intersection (runs BASE2/BASE3) binds first; **ASSUMPTION:** influent and outfall adequate pending Chapter 94 (p.3) review. |

Finding summary:

- Existing firm ~3280.8 gpm 4.724 MGD 2 pumps 17.25-in (p.13) (run BASE2), ~1679 gpm short of 4960 gpm 7.14 MGD (p.3) (**ASSUMPTION** arithmetic); low-C case ~2777 gpm (run BASE2-C70). No-change: cannot convey 20-year peak firm; 2016 test 3200 gpm (p.3) confirms.

## Alternatives (table with cost class)

All cost classes n/a – no costs on pp.3,4,10,13. Cost basis qualitative only (**ASSUMPTION**).

| Option | Unit / Run | Verified operating point (2 pumps firm) | Meets >=4,960 gpm (7.14 MGD) (p.3)? | Cost class / Cost basis |
|---|---|---|---|---|
| A – High-head replacement pumps on existing single FM (pump-only, illustrative) – RECOMMENDED (qualitative only) | Triplex pumps firm 2 of 3 largest out (triplex p.4) / run ALT-A-HH2 (also ALT-PUMP-BIG) | 5049.2 gpm total 7.271 MGD with 2 pumps (run ALT-A-HH2) exceeds 4,960 gpm 7.14 MGD (p.3) by ~89 gpm (**ASSUMPTION:** 5049.2 minus 4960 arithmetic); per pump 2524.6 gpm at 238.42 ft TDH (run ALT-A-HH2) vs system 220.81 ft at 4,800 gpm and 235.83 ft at 5,000 gpm 2-pump (p.13); HDR 121.55 psi and N1 122.72 psi (run ALT-A-HH2); FM 6.2 fps, PS18 6.03 fps, branch 6.77 fps (run ALT-A-HH2); shaft 190.3 hp, 101% of rated flow (run ALT-A-HH2) with default eff 0.80/motor 0.95 (**ASSUMPTION:** tool defaults, no data on pages) | Yes, thin ~89 gpm 1.8% margin (**ASSUMPTION** arithmetic) | n/a / **ASSUMPTION:** qualitative only – no costs on pp.3,4,10,13; pump/motor/VFD/electrical + pressure-rating review only avoids ~13,500 LF (p.4) parallel FM along Schuylkill River (p.4); illustrative rating 2500 gpm at 240 ft (**ASSUMPTION:** selected to overcome ~235.83 ft at 5,000 gpm 2-pump p.13); shaft ~190.3 hp (run ALT-A-HH2) needs ~250 hp motors (**ASSUMPTION:** motor > shaft for margin, no motor data on pages) |
| B – Parallel FM retaining existing 17.25-in pumps (force-main-only) | 18.24-in CIP FM STA 0+00 to 135+00 13,500 ft C=85 (p.10) plus parallel barrel (**ASSUMPTION**) / run ALT-B-PFM-EX (also ALT-PFM-EX) | 6402.3 gpm total 9.219 MGD with 2 existing pumps (run ALT-B-PFM-EX) exceeds 4,960 gpm 7.14 MGD (p.3) by ~1442 gpm (**ASSUMPTION:** arithmetic); per pump 3201.1 gpm at 98.25 ft TDH (run ALT-B-PFM-EX) vs single-pump curve 98.27 ft at 3200 gpm (p.13) and shutoff 152.68 ft at 0 gpm (p.13); split 2654.6 gpm existing C=85 and 3747.7 gpm new C=120 (run ALT-B-PFM-EX; C existing p.10, C new **ASSUMPTION**); branch 8.59 fps PS18 7.65 fps (run ALT-B-PFM-EX); shaft 99.5 hp default eff (run ALT-B-PFM-EX, **ASSUMPTION** defaults) | Yes, ~1442 gpm margin (**ASSUMPTION**) | n/a / **ASSUMPTION:** qualitative only – no costs on pp.3,4,10,13; ~13,500 LF (p.4) parallel 18.24-in FM (p.10) along Schuylkill River (p.4) dominates; retains existing 17.25-in pumps (p.13) so no pump cost; new-barrel diameter/length/C **ASSUMPTION:** same 18.24-in x 14094.2 ft C=120 as new-pipe roughness, existing C=85 (p.10) |
| C – Parallel FM plus moderate new pumps (combined, illustrative) | System pumps + parallel FM (**ASSUMPTION** ratings/barrel) / run ALT-C-PFM-NP (also ALT-PFM-NEWP) | 5976.2 gpm total 8.606 MGD with 2 pumps rated 2500 gpm at 105 ft (**ASSUMPTION** rating) (run ALT-C-PFM-NP) exceeds 4,960 gpm 7.14 MGD (p.3) by ~1016 gpm (**ASSUMPTION:** arithmetic); per pump 2988.1 gpm at 90.0 ft TDH 120% of rated flow (run ALT-C-PFM-NP); HDR 56.76 psi (run ALT-C-PFM-NP); branch 8.02 fps PS18 7.14 fps (run ALT-C-PFM-NP); shaft 85.0 hp default eff (run ALT-C-PFM-NP, **ASSUMPTION** defaults) | Yes, ~1016 gpm margin (**ASSUMPTION**) | n/a / **ASSUMPTION:** qualitative only – no costs on pp.3,4,10,13; combines ~13,500 LF (p.4) parallel FM cost plus new pumps/motors; illustrative rating 2500 gpm at 105 ft (**ASSUMPTION:** selected for ~90 ft duty); highest capital by avoiding nothing, lowest head/energy |

Notes for all alternatives:

- HDR 121.55 psi (run ALT-A-HH2) vs 72.33 psi base (run BASE2); FM 6.2 fps (run ALT-A-HH2) vs 6.088 fps target velocity (velocity tool for 7.14 MGD p.3).
- ALT-B-PFM-EX FM-E 2654.6 gpm C=85 FM-N 3747.7 gpm C=120 total 6402.3 gpm TDH 98.25 ft; existing-pump 3201 gpm operation within documented to 5000 gpm 67.46 ft (p.13) but motor/NPSH unknown on pages.
- ALT-C-PFM-NP FM-E 2477.9 gpm FM-N 3498.2 gpm (run ALT-C-PFM-NP); HDR 56.76 psi (run ALT-C-PFM-NP) vs 121.55 psi pump-only (run ALT-A-HH2).
- Shaft 190.3 hp total electric 298.8 kW (run ALT-A-HH2, **ASSUMPTION** defaults) vs 100.5 kW base (run BASE2).
- Table 2380511 gpd vs text 2380500 gpd 11 gpd and 7141500 gpd = 4959.4 gpm not 4960 gpm (p.3) immaterial rounding noted.

## QA/QC Summary

Checked citations (from review):

- D01 4960gpm=7.14MGD peak flow p.3 verified.
- D02/D03 2106900gpd + PF3.0 p.3 verified.
- D04-D06 960EDU x285=273600gpd p.3 verified.
- D13 3200gpm 2-pump 2016 test p.3 verified vs D22 3200gpm 3-pump 1992 p.4 conflict noted.
- D23-D28 FM geometry 18.24-in 13500ft C85, 18.49-in 97ft C120, 12.34-in 32.3ft C120, static 29.35ft (73.9-44.55) p.10 verified.
- D29-D32 equiv lengths 124.6/156.4/594.2 total 14505ft p.10 verified by summation.
- D33-D38 17.25-in impeller pump vs system heads incl 235.83ft at 5000gpm 2-pump p.13 verified.

Checked runs: BASE2, BASE1, BASE3, ALT-PUMP-BIG, ALT-PFM-EX, ALT-PFM-NEWP; resolution runs ALT-A-HH2, ALT-B-PFM-EX, ALT-C-PFM-NP, BASE2-C70.

Issues and resolution:

- Major – Alternatives pump curves not verified as selectable: 2500gpm@240ft and 2500gpm@105ft rated points are **ASSUMPTION** with no manufacturer curve, HP, speed, VFD, efficiency or NPSH on pp.3,4,10,13. EPANET single-point curve derivation + default eff 0.80 used. No selectable pump proven to deliver 2524.6gpm@238.42ft or 2988.1gpm@90ft. Fixed by disclosure: intersections verified hydraulically (runs ALT-A-HH2/ALT-C-PFM-NP) but selectable pump not proven; procurement submittal required.
- Major – Least-cost / RECOMMENDED ranking has zero cost basis on available pages. All cost_basis entries are **ASSUMPTION** about ~13500 LF parallel FM (p.4) dominating cost. Fixed: changed cost_class to n/a and cost_basis to explicit **ASSUMPTION** qualitative. RECOMMENDED for A retained only as engineering judgment (avoids ~13,500 LF p.4) not document-proven least-cost.
- Major – Pump-only Alt A pressure/power margin & static datum: 5049.2gpm exceeds 4960gpm by only ~89gpm (1.8%). Requires 238.42ft TDH, header 102.23psi, shaft 190.3hp, FM 6.2fps, branch 6.77fps, PS18 6.03fps (run ALT-A-HH2). No evidence 1965 18.24-in CIP FM, 12.34-in DIP, valves/mag meter rated for 102psi+surge. Uses optimistic 29.35ft static from 44.55ft Pump-Off (p.10); lower Pump-On level increases head and erases margin. Fixed by disclosure.
- Major – Station piping claimed Adequate withdrawn: reruns show 8.59fps branch +7.65fps PS18 (ALT-PFM-EX), 8.02fps+7.14fps (ALT-PFM-NEWP), 6.77fps (ALT-PUMP-BIG) vs 4.4/3.92 fps base (run BASE2); per-pump 2988-3201gpm far exceeds 1750gpm (p.4) and 2000gpm (p.4) ratings; shaft 85-99.5hp vs unknown existing motor. Velocity, scour, hammer, runout, motor overload not evaluated. Fixed.
- Major – Parallel-FM Alts B/C new-barrel assumption: 6402.3gpm and 5976.2gpm assume new parallel barrel 18.24-in x14094.2ft C120 same ID as old CIP. New-pipe diameter/material/C and 594.2ft equiv (p.10) reuse are **ASSUMPTION**, not on pages. Existing-pump operation at 3201gpm@98.25ft near runout with default eff, no motor/NPSH check. Fixed by disclosure.
- Minor – Calibration bias / C-factor optimism: BASE2 3280.8gpm +2.5% above 2016 3200gpm 2-pump (p.3); BASE3 3446.9gpm +7.7% above 1992 3200gpm 3-pump (p.4) dismissed as different vintage without install-date evidence. C85 for old CIP (p.10) may be optimistic if tuberculated; added C=70 sensitivity BASE2-C70 2777.3gpm (run BASE2-C70). Fixed/acknowledged.
- Minor – Source arithmetic + energy numbers: Table 2380511 vs text 2380500 11gpd and 7141500/1440=4959.4 not 4960 (p.3) – immaterial rounding but shortfall/margin presented as exact. kW/shaft_hp/specific_energy (e.g., 298.8kW vs 100.5kW) use EPANET defaults eff 0.80/motor 0.95, not document data. Fixed by labeling **ASSUMPTION** arithmetic and defaults.
- Minor – Influent + outfall not on path analysis: 24-in CIP gravity ~37ft below grade influent to NMWA headworks via ~13500 LF (p.4) and high-point control assumed, but no evidence influent or headworks can pass 7.14MGD. Noted: pump/FM intersection binds first in model but firm-adequacy incomplete pending Chapter 94 (p.3) influent/outfall review.

## Recommendations

- Existing station + single FM (No-change) cannot convey 20-year peak firm; 2016 test 3200 gpm (p.3) confirms. Firm BASE2 3280.8 gpm 4.724 MGD (run BASE2) vs 4,960 gpm 7.14 MGD need (p.3).
- Limiting unit is friction-controlled existing 18.24-in x 13,500 ft CIP C=85 (p.10) + 594.2 ft equiv (p.10); needs 220.81-235.83 ft 2-pump at 4800-5000 gpm (p.13) vs 2-pump pump head only 111.47 ft at 4800 gpm and 101.67 ft at 6000 gpm (p.13).
- Alternative A – Replace pumps/motors with high-head units on existing FM (RECOMMENDED qualitative least-capital by avoiding ~13500 LF p.4, NOT document-proven; verify selectable pump 2524.6 gpm at 238.42 ft, 102+ psi + surge rating, VFD/electrical, low-level head) (run ALT-A-HH2/target p.3). Meets firm with ~89 gpm 1.8% margin (**ASSUMPTION:** 5049.2 minus 4960) (run ALT-A-HH2); shaft 190.3 hp total electric 298.8 kW (run ALT-A-HH2, **ASSUMPTION** defaults) vs 100.5 kW base (run BASE2).
- Alternative B – Add parallel ~13,500 LF FM (p.4) 18.24-in C=120 (**ASSUMPTION** new-pipe), retain pumps; verify new-pipe sizing/material/C, station velocities 8.59 fps (run ALT-B-PFM-EX), motors (run ALT-B-PFM-EX/target p.3).
- Alternative C – Parallel FM (**ASSUMPTION** as in B) plus moderate new pumps (**ASSUMPTION** rating); verify selectable pump 2988 gpm at 90 ft, velocities 8.02 fps (run ALT-C-PFM-NP) (run ALT-C-PFM-NP/target p.3).
- For selected alternative, verify/replace 12.34-in/18.49-in DIP (p.10), valves/meter, motors, surge; Alt A thin ~89 gpm margin (**ASSUMPTION** arithmetic) erased by lower Pump-On level vs 44.55 ft Pump Off (p.10). Per-pump 2524-3201 gpm (runs ALT-A-HH2/ALT-B-PFM-EX/ALT-C-PFM-NP) exceeds original 1750 gpm 75-hp (p.4) and 1983 2000 gpm 100-hp (p.4) ratings; existing motor/NPSH/hammer/scour not on pp.3,4,10,13; 1965 FM/valves/meter pressure rating for 121.55 psi HDR 122.72 psi suction (run ALT-A-HH2) not on pages.

## Limitations

- Available pages only pp.3,4,10,13; pp.10 system-head friction/minor values withheld – recomputed via run_hydraulics (R-01).
- No pump make/model, speed, motor HP, VFD, efficiency, NPSH for 17.25-in pumps on pages; p.13 only impeller size and head-capacity points (R-02, QA/QC major).
- Conflicting 3200 gpm statements (2-pump 2016 p.3 vs 3-pump 1992 p.4); adopted p.3 as firm baseline (**ASSUMPTION** R-03).
- Conflicting projections Rettew 6600 gpm/9.5 MGD vs G&A 4960 gpm/7.14 MGD (p.3); designed to 4960 gpm per task (**ASSUMPTION** R-04).
- Static 29.35 ft uses 44.55 ft Pump Off (p.10); operating Pump-On/low-water level withheld – lower level increases head, worsens deficiency, erases Alt A 89 gpm margin (**ASSUMPTION** R-05).
- Actual IDs/roughness/fittings per p.10 used exactly; C=85 (p.10) may be optimistic if tuberculated – sensitivity BASE2-C70 2777.3 gpm (run BASE2-C70) (**ASSUMPTION** R-06).
- No costs, proposed impellers, parallel FM sizing on pages; cost_class n/a, qualitative ranking only (**ASSUMPTION** R-07).
- Illustrative pump ratings, new-barrel C=120, default eff 0.80/motor 0.95, kW, arithmetic margins are **ASSUMPTION**, not document-proven.
- Station/connector 12.34-in/18.49-in DIP (p.10), valves/meter, motors, surge, scour, hammer, runout not proven for 6.77-8.59 fps and 99.5-190.3 hp duties.
- 24-in CIP gravity ~37 ft below grade influent (p.4) to NMWA headworks via ~13500 LF 18-in (p.4) adequacy at 7.14 MGD (p.3) unevaluated; no surcharge/headworks data.
- Requires review and approval by a licensed professional engineer; procurement submittal, pressure-rating review, VFD/electrical review, and low-level head verification required before design.
