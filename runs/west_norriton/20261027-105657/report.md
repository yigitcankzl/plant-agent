DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum — Rittenhouse Boulevard Pump Station and Force Main Capacity

## Purpose

Evaluate whether the existing Rittenhouse Boulevard Pump Station and Force Main, West Norriton Township, Pennsylvania can convey the projected 20-year peak flow of 4,960 gpm (7.14 MGD) (p.3) with one pump out of service (i.e., with two pumps operating), identify what limits it, and verify least-cost alternatives (pumps, impellers, force main) that achieve at least 4,960 gpm (p.3) with two pumps operating at the intersection of system-head curve and parallel-pump curve.

Source: Gilmore & Associates, Rittenhouse Boulevard Pump Station capacity study for West Norriton Township, November 2020 (public record) — https://westnorritontwp.org/DocumentCenter/View/1369

## Background

- Station: originally constructed circa 1965 (p.4), designed and built as a conventional wet well/dry well triplex pump station (p.4).
- Original pumps: three 75 hp pumps, each capable of delivering 1,750 gpm (2.5 MGD) (p.4).
- Gravity influent: 24-inch cast iron gravity pipe discharged into wetwell, which was approximately 37 feet below grade (p.4).
- Force-main route: pumped directly to headworks of Norristown Municipal Wastewater Authority (NMWA) Wastewater Treatment Plant at 368 E. Washington Street via approximately 13,500 LF of 18-inch cast iron force main (p.4); force main generally runs parallel to Schuylkill River (p.4).
- 1983 upgrade: three 100 hp pumps, each rated 100 hp and capable of 2,000 gpm (2.9 MGD) (p.4).
- 1992 field test: approximately 3,200 gpm (4.6 MGD) with all three pumps operating (p.4), measured 06/19/1992 (p.4).
- 2016 field inspection: approximately 3,200 gpm (4.6 MGD) with two pumps operating (p.3).
- Prior projections/capacities for context:
  - Rettew Design Engineer's Report August 2013: 6,600 gpm or 9.5 MGD (p.3).
  - Capacity prior to 2015 upgrade: 6.8 MGD (p.3), approximately 2.2 MGD lower than previous (p.3).
  - PA DEP permitted capacity: 8.74 MGD (p.3), 4.14 MGD higher than 2016 observation (p.3).

## Design Criteria

1. **Projected 20-year peak flow need:** 4,960 gpm (7.14 MGD; 7,141,500 gpd) governs the study (p.3).
2. **Firm-capacity requirement:** Station must convey at least 4,960 gpm (p.3) with one pump out of service, i.e. with two pumps operating (Task brief + p.3).
3. **Existing force-main break history — ASSUMPTION:** ASSUMPTION: existing 18-inch cast-iron force main broke in past at about 90 psi; treat ~90 psi as upper operating-pressure limit for existing cast-iron main — reason: client record via task brief is only evidence of pressure capability, conservative to avoid repeat break; no rating in visible pages.
4. **Operating-point verification rule:** Each alternative must be verified at intersection of system-head curve and parallel-pump curve for two pumps operating; quote run_hydraulics outputs; use document units (Task brief + p.13).
5. **Hydraulic basis to retain:** Use listed pipe diameters, lengths, C-values, static head 29.35 ft (p.10) and equivalent lengths as basis for all runs (p.10).

## Data and Assumptions

Projected flow basis (p.3):

- Average daily flow Jan 2016–Sept 2020: approximately 2,106,900 gpd (p.3).
- Average daily dry weather peaking factor: 3.0 (p.3).
- Projected new EDUs in 20 years: 960 EDUs (p.3).
- Unit flow: 285 gpd/EDU (p.3).
- Projected 20-year flow addition: 273,600 gpd (p.3), comprised of Riverview 330 EDU x 285 = 94,050 gpd (p.3); Main & Schuylkill 22 EDU x 285 = 6,270 gpd (p.3); Office Bldg @ Egypt 8 EDU x 285 = 2,280 gpd (p.3); Westover 500 EDU x 285 = 142,500 gpd (p.3); Miscellaneous 100 EDU x 285 = 28,500 gpd (p.3).
- Total projected 20-year average daily flow: 2,380,500 gpd text / 2,380,511 gpd Table 1 — 11 gpd difference noted (p.3).
- Projected 20-year peak: 7,141,500 gpd (7.14 MGD) after x 3.0 (p.3); 20-Year Peak Flow 7.14 MGD 4,960 gpm (p.3).

Hydraulic basis retained (p.10):

- Existing force main Sta 0+00 to 135+00: 18.24 in, 13,500 ft, C.I.P., C=85 (p.10).
- Force main Sta -0+97 to 0+00: 18.49 in, 97 ft, DIP, C=120 (p.10).
- Inside pump station piping: 12.34 in, 32.3 ft, DIP, C=120 (p.10).
- Static head: HIGH POINT ELEV. 73.9 ft (p.10) minus LOW POINT ELEV. 44.55 ft Wetwell Pump Off (p.10) = 29.35 ft (p.10).
- Equivalent lengths: 594.2 ft for 18-in CIP segment (p.10); 124.6 ft for 18-in DIP 97-ft segment (p.10); 156.4 ft for 12-in inside station (p.10); Total Equivalent Length of Pipe 14,505 ft (p.10).
- Existing pump: 17.25-inch Impeller curve (p.13).
- System-head table points (p.13): e.g., 0 gpm = 29.35 ft (p.13); 2000 gpm 2-pump = 67.25 ft (p.13); 3200 gpm 2-pump = 119.78 ft (p.13); 4000 gpm 2-pump = 165.99 ft (p.13); 4800 gpm 2-pump = 220.81 ft (p.13); 5000 gpm 2-pump = 235.83 ft (p.13).
- Parallel pump-head table points (p.13): shutoff 152.68 ft (p.13); e.g., 2-pump at 4800 gpm = 111.47 ft (p.13); 2-pump at 4000 gpm = 116.44 ft (p.13).

Key ASSUMPTIONS (with reasons):

- ASSUMPTION: ~90 psi is hard upper limit at J3 (CIP Sta 0+00 inlet) for flow in existing CIP main — reason: Township break record via brief is only capability evidence; visible pages give no rating; conservative to avoid repeat.
- ASSUMPTION: use 29.35 ft static head (73.9–44.55 ft per p.10) for base runs — reason: pump-on level not in visible pages; matches p.13 system-curve basis.
- ASSUMPTION: retain C=85 for existing 18.24-in CIP and C=120 for 18.49-in and 12.34-in DIP as listed (p.10) — reason: preserves 11/10/2020 system-head calculation basis.
- ASSUMPTION: firm-capacity verdict limited to flow-vs-head operating point and discharge pressure vs ~90 psi limit; motor/electrical adequacy flagged as follow-on — reason: p.4 gives 100-hp rating only, no efficiency, amps, or NPSH in visible pages.
- ASSUMPTION: p.3 two-pump 3,200 gpm observation and p.4 three-pump 3,200 gpm 1992 test treated as dated historical observations, not current firm capacity — reason: p.3 vs p.4 pump-count conflict; decide by hydraulic operating point from p.10/p.13 data.
- ASSUMPTION: govern by 4,960 gpm / 7.14 MGD / 7,141,500 gpd stated need (p.3) — reason: 11 gpd text-vs-table mismatch and MGD-gpm rounding differences are negligible (<0.001 MGD) and brief fixes 4,960 gpm as pass threshold.

## Model Calibration

All runs use 29.35 ft static (p.10) and 14,505 ft total equiv (p.10) with 17.25-in curve (p.13) unless noted.

| Test | Measured (source) | Simulated (run label) | Residual | Note |
|---|---|---|---|---|
| Two-pump firm test | ~3,200 gpm (4.6 MGD) with two pumps operating (p.3) | Run BASE-2P: 3231.7 gpm (4.654 MGD) total_pumped_gpm; TDH 123.91 ft; P_FM 3231.7 gpm at 3.97 fps | 0.99% | Validates 14,505-ft equiv (p.10) + C=85/120 + 17.25-in curve (p.13) basis; residual within field-test tolerance |
| Three-pump test | ~3,200 gpm (4.6 MGD) with all three pumps operating 06/19/1992 (p.4) | Run BASE-3P: 3380.2 gpm (4.867 MGD) total_pumped_gpm; TDH 132.12 ft | 5.63% | Third pump adds only ~148 gpm vs BASE-2P (3380.2–3231.7); confirms steep system curve; p.3 vs p.4 pump-count conflict treated as dated observations |
| System-head table check | 119.78 ft system head at 3,200 gpm 2-pump (p.13); 67.25 ft at 2,000 gpm 2-pump (p.13); static 29.35 ft (p.10) | Run BASE-2P: 123.91 ft TDH at 3231.7 gpm; J1 53.74 psi, J3 51.59 psi | 3.45% | Confirms pipe diameters/lengths/C and equiv 594.2+124.6+156.4=14,505 ft (p.10) reproduce 11/10/2020 table |

Corrected runs for verdict (pressure test at J3, no shaft_hp): BASE-2P-FIX and BASE-3P-FIX reproduce BASE-2P / BASE-3P flows: 3231.7 gpm firm, 3380.2 gpm three-pump.

## Capacity Evaluation

| Unit on path | Firm limit vs 4,960 gpm target (p.3) | Evidence (operating point) | What binds |
|---|---|---|---|
| Triplex station firm — 2 of 3 operating (100-hp 1983 rating 2,000 gpm each per p.4; 17.25-in curve per p.13) | 3,231.7 gpm (4.654 MGD) firm — 1,728 gpm short of 4,960 gpm (p.3); **limits target = Yes** | Run BASE-2P-FIX: 3231.7 gpm total_pumped_gpm, TDH 123.91 ft, each pump 1615.8 gpm; target 4,960 gpm = 7.14 MGD = 7,141,500 gpd (p.3) not reached; 3-pump BASE-3P-FIX only 3380.2 gpm | Intersection of 2-pump 17.25-in parallel curve (shutoff 152.68 ft, e.g. 111.47 ft at 4800 gpm per p.13) with system curve (29.35 ft static per p.10, 235.83 ft at 5000 gpm 2-pump per p.13) |
| 18-in CIP force main Sta 0+00 to 135+00 — 18.24-in x 13,500 ft C=85 to NMWA WWTP (p.4) | ~3,232 gpm firm on single main; **limits target = Yes** | Run BASE-2P P_FM 3231.7 gpm at 3.97 fps; p.13 system requires 220.81 ft at 4800 gpm 2-pump vs pump can deliver 111.47 ft (p.13) | Friction in 18.24-in x 13,500 ft C=85 (p.10) + 594.2 ft equiv (p.10); velocity tool 6.09 fps at 7.14 MGD in 18.24-in confirms high friction |
| Existing CIP main pressure capability | ~90 psi max operating (ASSUMPTION per brief Township break record); **limits target = Yes** | Run BASE-2P-FIX J3 51.59 psi safe but only 3231.7 gpm; any single-main path to 4,960 gpm needs ~98–103 psi range per rejected proxy runs; p.13 system 235.83 ft at 5000 gpm = ~102 psi + static implies break repeat | ~90 psi break-history ASSUMPTION applies at J3 CIP inlet (Sta 0+00–135+00 per p.4/p.10), not station discharge J1 |
| Inside-station 12-in DIP + 18-in DIP Sta -0+97 to 0+00 (12.34-in x 32.3 ft C=120 per p.10 + 156.4 ft equiv per p.10; 18.49-in x 97 ft C=120 per p.10) | Hydraulically passes if main relieved, but velocities >8 fps flag review; **limits target = No** — main friction + pressure bind first | Run BASE-2P 3231.7 gpm at 8.67 fps in 12.34-in; Run ALT-PAR-EXIST-FIX 5405.2 gpm at 14.5 fps; 18.49-in at 6.46–8.21 fps in passing alts | 12.34-in x 32.3 ft C=120 (p.10) + 156.4 ft equiv (p.10) carries full station flow; no velocity criterion in visible pages so not binding pass/fail |

**Verdict: No.** Existing station + single 18-in CIP main cannot convey 4,960 gpm (p.3) firm (two pumps operating). Firm is 3231.7 gpm (Run BASE-2P-FIX).

## Alternatives

Pump-only with documented 17.25-in curve (p.13) cannot reach target — p.13 system 220.81 ft at 4800 gpm 2-pump vs 111.47 ft pump capability. Larger-impeller/new-pump curves are in withheld pages and not verified; 1.2x/1.4x speed proxies rejected as verification. Parallel-main alternatives below retain existing 17.25-in pumps (p.13), two operating, and relieve friction in 18.24-in x 13,500 ft C=85 (p.10) along ~13,500 LF route (p.4).

| Alternative (firm = 2 pumps operating) | Verified operating point (run label) | Meets ≥4,960 gpm (p.3)? | Cost class | Recommended? |
|---|---|---|---|---|
| Parallel 18-in main (conservative C=85 duplicate) + retain existing 17.25-in pumps (p.13), 2 operating. Basis: duplicate existing 18.24-in x 13,500 ft C=85 + 97-ft/inside segments per p.10; ~13,500 LF route per p.4. ASSUMPTION: duplicate C=85 as lower bound — reason: preserves 11/10/2020 basis; new pipe would not be aged CIP. | Run ALT-PAR-EXIST-FIX: 5405.2 gpm total_pumped_gpm; TDH 106.53 ft; J3 40.64 psi — exceeds 4,960 gpm (p.3). Drawdown sensitivity Run ALT-PAR-DRAW-FIX (5-ft drawdown ASSUMPTION — reason: no pump-on level in visible pages; p.10 low point is Pump Off; wetwell 39.55 ft): 5259.4 gpm; J3 41.43 psi — still passes. | Yes — 5405.2 gpm (5259.4 gpm with drawdown) | n/a — No cost data in visible pages; scope only: ~13,500 LF route (p.4) + 14094.2-ft equiv basis (p.10); retains documented 17.25-in pumps (p.13) | Yes |
| Parallel 18-in main (new-pipe C=120 sensitivity) + retain existing 17.25-in pumps (p.13), 2 operating. ASSUMPTION: new-pipe C=120 to bound upside — reason: new pipe would not be aged CIP; same scope/diameters/lengths as above per p.10. | Run ALT-PAR-C120-FIX: 6051.2 gpm total_pumped_gpm; TDH 101.24 ft; J3 37.05 psi — exceeds 4,960 gpm (p.3). | Yes — 6051.2 gpm | n/a — No cost data in visible pages; same scope as above but new-pipe C=120 ASSUMPTION to bound upside | No (sensitivity bound) |

All passing alternatives stay below ~90 psi ASSUMPTION limit at J3 (CIP inlet): Run BASE-2P-FIX J3 51.59 psi; Run ALT-PAR-EXIST-FIX J3 40.64 psi; Run ALT-PAR-C120-FIX J3 37.05 psi; Run ALT-PAR-DRAW-FIX J3 41.43 psi.

Inside-piping disclosure from runs (diameters per p.10 only, no criterion in visible pages): Run BASE-2P-FIX 8.67 fps, Run ALT-PAR-EXIST-FIX 14.5 fps in 12.34-in x 32.3 ft (p.10) — flagged as surge/meter-review follow-on, not binding flow-head-pressure fail.

## QA/QC Summary

- Checked citations: DR-12 peak 4,960 gpm / 7.14 MGD (p.3); DR-23 18.24-in x 13,500 ft C=85 (p.10); DR-26 static 29.35 ft (p.10); DR-31 17.25-in impeller (p.13); DR-32 system-head table (p.13); DR-13 3,200 gpm two-pump (p.3).
- Checked runs: BASE-2P, BASE-3P, ALT-PAR-EXIST, ALT-BIG-EXIST, ALT-BIG140-EXIST, ALT-BIG-PAR, plus corrected FIX runs BASE-2P-FIX, BASE-3P-FIX, ALT-PAR-EXIST-FIX, ALT-PAR-C120-FIX, ALT-PAR-DRAW-FIX.
- Review issues dispositioned:
  1. Shaft_hp/motor adequacy (91.0 hp <100 hp etc.) — **fixed:** removed; p.4 gives only 100-hp rating, p.13 gives head-flow only, no efficiency/NPSH; efficiency 0.80 default is uncited ASSUMPTION, not quoted.
  2. Recommended alternative at 14.5 fps in 12.34-in (p.10) — **fixed:** disclose velocities directly from runs (BASE-2P-FIX 8.67 fps, ALT-PAR-EXIST-FIX 14.5 fps); reject invented fail criterion — no velocity criterion in visible pages; flagged follow-on.
  3. Pump-only/big-pump 1.2x/1.4x speed proxies (4094.3, 4943.8, 6869.0 gpm) — **rejected** as verification; visible pages contain only 17.25-in curve (p.13); no larger curve to intersect.
  4. Parallel sizing duplicates existing C=85 (p.10) — **fixed:** replaced with two bounds (C=85 duplicate conservative lower bound + C=120 new-pipe upper-bound ASSUMPTION) using same 18.24-in x 13,500 ft + equiv basis (p.10) and 13,500 LF route (p.4).
  5. Cost classes >$10M / $100k–$1M — **fixed:** removed; no cost/quantity/unit-price in visible pages; cost_class n/a, scope-only comparison.
  6. Static head 29.35 ft for all runs (p.10 Pump Off level) — **fixed:** base runs retain 29.35 ft to match p.13 table; added ALT-PAR-DRAW-FIX 5-ft drawdown sensitivity (wetwell 39.55 ft ASSUMPTION) — still passes.
  7. 90-psi limit applied at J1 vs J3 — **fixed:** corrected pressure test to J3 (CIP Sta 0+00 inlet) for ~90 psi ASSUMPTION (applies to 18-in CIP Sta 0+00–135+00 per p.4/p.10, not DIP station piping).

## Recommendations

1. Do not attempt to convey 4,960 gpm (p.3) firm through single existing 18-in CIP main — firm is 3231.7 gpm (Run BASE-2P-FIX), 1728 gpm short, and pressure to reach target would approach/exceed ~90 psi ASSUMPTION break-history limit at J3.
2. Proceed with parallel ~13,500 LF main (p.4) to relieve 18.24-in x 13,500 ft C=85 friction (p.10) while retaining existing 17.25-in pumps (p.13): Run ALT-PAR-EXIST-FIX verifies 5405.2 gpm firm (5259.4 gpm with 5-ft drawdown per Run ALT-PAR-DRAW-FIX), TDH 106.53 ft, J3 40.64–41.43 psi, providing 299–445 gpm margin over 4,960 gpm (p.3) even on conservative C=85 duplicate ASSUMPTION; C=120 sensitivity (Run ALT-PAR-C120-FIX) bounds upside at 6051.2 gpm, J3 37.05 psi.
3. Re-intersect final parallel diameter/C/routing and any larger impeller/pump selection from withheld pages before design; confirm motors/electrics (100-hp rating per p.4 only), surge, mag-meter range in 18.49-in x 97 ft (p.10) and inside 12.34-in piping velocities, and operating wetwell level (only Pump-Off 44.55 ft given per p.10).

## Limitations

- Visible pages give only 17.25-in head-flow (p.13), 100-hp rating (p.4), diameters/lengths/C and 29.35 ft static (p.10); no larger pump curves, efficiency, NPSH, electricals, costs, pump-on level, or velocity criterion — larger-pump selection, motor/electrical adequacy, surge, meter range, final parallel diameter/C/routing, and dollar least-cost ranking are unverifiable from visible pages and require withheld pages.
- Pressure capability limited to Township operating-record ASSUMPTION of ~90 psi break history (not in visible pages); no pipe rating or safety factor in visible pages.
- Static-head sensitivity bounded only by 5-ft drawdown ASSUMPTION (Run ALT-PAR-DRAW-FIX); actual pump-on level unknown.
- Inside-station 12.34-in x 32.3 ft (p.10) velocities 8.67–14.5 fps from runs disclosed for follow-on review; no pass/fail criterion applied.
