DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Briare Pumping Station — Energy Audit Memo
**Facility:** Briare Pumping Station, Canal de Briare, France  
**Source:** Arcadis for Voies navigables de France, Briare Pumping Station Pump Assessment Report, 2020 (Interreg Green WIN public deliverable)  
**Question:** is existing Xylem CP3231 selection appropriate for twin-900 mm / 2650 m / ~43 m system, would VSDs save energy, and which measures should VNF take?

## Purpose
Energy audit of Briare PS: assess if existing Xylem CP3231 pump selection is appropriate for the system, whether Variable Speed Drives (VSD) would save energy, and which measures (new pump, IE3/IE4 motors, operating periods, automation, metering) should be taken to reduce energy use. Quantify with simulator where possible and state data needed to confirm.

## Background
* 6 pumps installed; operates with only 2 pumps for most of the time and up to 3 if necessary (p.6).
* Duty / Duty / Assist + 3 Standby units assumed (p.6).
* Existing: Xylem (Flygt) CP3231 / 705 with 53-455 performance curve (p.6); Impeller Diameter 435 mm (p.6); Rated Motor Output 170 kW (p.6); Energy Conformance IE2 (p.6); Drives Fixed Speed (assumed star-delta) (p.6).
* Selection tables list CP3231 / 735 455 435mm existing and CP3231 / 736 455 435mm (IE3) (p.10); system curves legend lists Xylem CP 3231 735/745 435mm impeller 2No. Pumps (p.8).
* Review notes best fit was existing pump with closed C impeller (p.10); VNF assessment correlation very good (p.9).
* 2020 implementation scope: Automation, supervision and telecontrol of pumping operations; Optimising of operations time periods; Implementing at least one new pump; Motor IE3 or IE4 energy performance, Variable Speed Drive (VSD); Smart water and energy monitoring (p.5).
* Energy reports: Energy consumption reports from EDF from 2017 and 2018 were reviewed (p.11). No flow measurement have been undertaken (p.11).

## Design Criteria
* Normal operating duty: 2 pumps most of time, up to 3 if necessary (p.6).
* Installed / duty configuration: 6 pumps installed; Duty / Duty / Assist + 3 Standby units assumed (p.6).
* Firm capacity definition: Firm capacity = capacity with largest unit out of service; with 6 installed and 2-pump normal duty (p.6), firm 2-pump duty requires 3 pumps available.
* Units on path: Wet well / sump (124.2 to 125.8 mNGF) (p.6) > 6x CP3231 pumps, 435 mm impeller, 170 kW IE2 fixed-speed (p.6) > 300 mm diameter branch pipework per pump (p.6) > 750 mm diameter manifold per 3 pumps (p.6) > Twin 900 mm diameter rising mains approx. 2650 m (p.6, p.7) > Discharge at 168.1 mNGF, approx. 43 m rise (p.6, p.7).
* Suction / wet-well levels: 124.2 to 125.8 mNGF (p.6); Sump TVL 125.8 mNGF, Design ~124.9 mNGF, SWL 124.2 mNGF (p.9).
* Discharge / static lift: Discharge 168.1 mNGF (p.6); Elevation rise ~43 m (p.6); 43 metres schematic (p.7); Assumed Hydraulic Discharge levels ~168.0 mNGF (p.9); Static lift Minimum ~42.3 m / Design ~43.1 m / Maximum ~43.9 m (p.9) [168.1 minus 125.8/124.9/124.2].
* Rising main: twin 900 mm diameter rising mains (p.6); approximately 2650 m in length (p.6); 2 x 2650 m (O 900 mm) on schematic (p.7).
* Roughness: Design ks 0.3 mm; sensitivity curves for 0.03 mm and 1.5 mm (p.6, p.8, p.9: Low 0.03 / Design 0.3 / High 1.5 mm).
* Benchmarks: Existing 174 kWh/1000 m3 for 2- or 3-pump operation, 172 for 1 pump (p.10, p.11); IE3 option 170 kWh/1000 m3 for 2- or 3-pump, 167 for 1 pump (p.10); reduction ~4 kWh/1000 m3 (p.10).
* Annual volume: 2,907,360 m3 in 2016 (p.11); single IE3 pump at 66% utilisation saves 3,873 kWh/annum, all pumps 11,629 kWh/annum (p.11).
* Electrical: Base supplementary load ~10 kW summer and ~20 kW winter (p.11); typical summer total ~280 kW, pumping ~270 kW after base, vs predicted 265 kW for 2 pumps (p.11).

## Data and Assumptions
Only source facts used; all interpolations labelled ASSUMPTION.

* **ASSUMPTION – roughness base case:** adopt ks=0.3 mm as design base case and retain 0.03/1.5 mm as sensitivity band (p.6) because report provides curves for those values; require CCTV/coupon or pressure-drop test to confirm. Pipe Material Not known (p.6).
* **ASSUMPTION – pump designation:** treat CP3231/705 53-455 (p.6) vs CP3231 735/745 435mm (p.8) vs CP3231/735 455 and /736 455 (p.10) as same 435 mm closed-C CP3231 family and use Table 3/Figure 2 hydraulics (p.10, p.8) for audit because Xylem tool confirmed best fit to existing (p.10); require nameplate/curve confirmation.
* **ASSUMPTION – Table 3 totals:** interpret Table 3 flows 634/422/214 l/s and powers 398/265/133 kW labelled Per Pump (p.10) but scaling with pump count and matching 265 kW 2-pump station load (p.11) as station totals for n pumps in parallel; require Xylem duty-point printouts to confirm per-pump split. IE3 totals 638/424/216 l/s, 390/260/130 kW (p.10).
* **ASSUMPTION – duty/drives/levels:** adopt Duty/Duty/Assist +3 standby, fixed-speed assumed star-delta, and 124.2 low/124.9 design/125.8 high mNGF (p.6, p.9) for base model because they are only stated basis; require VNF ops log, starter panel check, and level survey to confirm.
* **ASSUMPTION – hydraulics:** fix geometry to 300 mm branches, 750 mm manifold, 2x900 mm x2650 m mains (p.6), areas 0.070686/0.441786/0.63617 m2, roughness Low 0.03/Design 0.3/High 1.5 mm, Total K 1.15/3.99/2.55/3.10, sump 125.8/124.9/124.2 mNGF, discharge ~168.0-168.1 mNGF, static ~42.3/43.1/43.9 m (p.6, p.9) because text tables control over pixels; require native calc file to rerun exactly. Branch/manifold ~9 m, rising main 2650 m (p.9).
* **ASSUMPTION – simulator tuning:** rated 211 l/s @ 48 m, pump eff 0.80 ASSUMPTION, motor_eff 0.945 ASSUMPTION, branch minor_k 8.0 ASSUMPTION to represent valves/bends, Hazen-Williams C=110 ASSUMPTION proxy for ks=0.3 mm, C=140 ASSUMPTION proxy for ks=0.03 mm, C=80 ASSUMPTION proxy for ks=1.5 mm. Junction elevs 125/126/130 m ASSUMPTIONS for connectivity. All AUD-*/BASE-*/CHK-* runs are illustrative audit model reproducing Table 3 station totals (p.10) within ~1%, not independent verification. Pump eff vs overall 75.4-75.7% (p.10) gap is motor/drive assumption.
* **ASSUMPTION – flows:** use Xylem station flows 422 l/s (2 pumps) and 634-638 l/s (3 pumps) (p.10) for simulator and retain VNF 222 kWh/1000 m3 based on arbitrary 200 l/s per pump (p.11) as VNF-estimate only; require clamp-on/inline flow + power logging to confirm.
* **ASSUMPTION – loads:** accept 10/20 kW base and 280 total/270 pumping/265 predicted for 2-pump validation (p.11) and flag 15 kW Jul-Aug 2018 dip as unexplained anomaly requiring investigation (p.11); require half-hourly EDF data and sub-meter to confirm.
* **ASSUMPTION – annual savings:** accept 2,907,360 m3 and 66% utilisation (p.11) for illustrative IE3 savings 3,873 / 11,629 kWh/annum (p.11) only; 3873x3=11619 vs 11629 kWh (p.11) 10 kWh gap noted as rounding/unclear basis. Require run-hours per pump, volumes, and tariff bands to confirm economics and VSD/period-optimisation case. Blended single-IE3 to 172 kWh/1000 m3 (p.11) vs all-IE3 170 2-pump /167 1-pump (p.10) unexplained – interpreted as 1xIE3+1xIE2 average, needs printout.

## Model Calibration
Base model run BASE-2P. Design sump 124.9 mNGF (p.9), discharge 168.1 mNGF (p.6).

| Test | Measured (source) | Simulated (run_label) | Residual |
|---|---|---|---|
| 2-pump station flow | 422 l/s station (2 pumps) (p.10) | BASE-2P: 423.7 l/s total, 211.8 l/s per pump, TDH 47.87m | +0.4% |
| 2-pump input power | 265 kW station (2 pumps) (p.10); EDF pumping ~270 kW, total ~280 kW summer (p.11) | BASE-2P: 263.8 kW total, 131.9 kW per pump, spec 172.9 kWh/ML | -0.5% vs Xylem, -2.3% vs EDF deduction; aligns with predicted load for two pumps (p.11) |
| 3-pump station flow/power | 634 l/s / 398 kW station (3 pumps) (p.10) | CHK-3P: 622.6 l/s total, 207.5 l/s per pump at 392.9 kW total | -1.8% |
| 1-pump duty | 214 l/s / 133 kW (1 pump) 172 kWh/1000m3 (p.10) | CHK-1P: 214.7 l/s at 132.4 kW, 171.4 kWh/ML, branch 3.04 m/s | +0.3% flow, -0.3% spec |
| Specific energy | 174 kWh/1000m3 2- or 3-pump (p.10, p.11) | BASE-2P: 172.9 kWh/ML; CHK-2P-LOW 174.9, CHK-2P-HIGH 170.4 | -0.6% base; level range 124.2-125.8 mNGF (p.6) brackets report |

Notes: Same BASE-2P parameters with 3rd pump; manifold 750mm (p.6) velocity 1.41 m/s sim (CHK-3P). Sim 172.9 (BASE-2P), 175.3 (CHK-3P), 174.9 low-level, 170.4 high-level bracket report.

Illustrative audit reruns (ASSUMPTION tuning): AUD-2P 424.8 l/s at 263.4 kW, 172.2 kWh/ML vs Table 3 422 l/s at 265 kW, 174 kWh/1000m3 (p.10) (+0.7%/-0.6%); AUD-1P 214.6 l/s at 132.1 kW vs 214 l/s at 133 kW (p.10); AUD-3P 627.2 l/s at 393.0 kW vs 634 l/s at 398 kW (p.10). Roughness proxies: AUD-2P-SMOOTH C=140: 427.8 l/s at 264.0 kW 171.4 kWh/ML; AUD-2P-ROUGH C=80: 418.5 l/s at 262.1 kW 174.0 kWh/ML vs AUD-2P C=110 424.8 l/s 263.4 kW 172.2. Level bracket AUD-2P-LOW 417.6 l/s 261.9 kW 174.2 and AUD-2P-HIGH 434.0 l/s 265.1 kW 169.7 (124.2/125.8 mNGF p.6).

## Capacity Evaluation

| Unit (path) | Limit | Binds at / evidence | Limits target? |
|---|---|---|---|
| 6x CP3231 435mm 170kW (p.6) | Pump-match / duty head | 2-pump duty 422 l/s (p.10) met at TDH ~47.9m; 3-pump 622.6 l/s (CHK-3P) vs 634 l/s (p.10); firm 2-pump with largest unit out requires 3 available – met with 6 installed (p.6). Evidence: BASE-2P 423.7 l/s at 263.8 kW; CHK-3P 622.6 l/s at 392.9 kW; best fit was existing pump closed C (p.10); VNF assessment correlation very good (p.9) | No |
| Twin 900mm x2650m mains +43m lift (p.6, p.7) | Static head floor | Static ~42.3/43.1/43.9m (p.9) from 168.1 mNGF (p.6) minus 125.8/124.9/124.2 mNGF (p.9, p.6); ~43m rise (p.6, p.7) dominates TDH ~47-48m sim. Evidence: BASE-2P TDH 47.87m; CHK-2P-LOW TDH 48.42m flow 416.5 l/s; CHK-2P-HIGH TDH 47.17m flow 432.8 l/s; AUD-VSD80 TDH 43.2m zero flow – static floor; AUD-2P TDH 47.78m; AUD-2P-LOW 48.33m at 417.6 l/s; AUD-2P-HIGH 47.08m at 434.0 l/s | Yes |
| Twin 900mm x2650m (p.6) | Friction / roughness uncertainty | Mains velocity 0.33 m/s per main at 2-pump (BASE-2P), 0.49 m/s at 3-pump (CHK-3P), 0.17 m/s at 1-pump (CHK-1P); friction small, twin 900mm (p.6) oversized for 422-634 l/s (p.10). Evidence: BASE-2P M1/M2 0.33 m/s; CHK-3P 0.49 m/s; velocity check ASSUMPTION SI: 211 l/s in 900mm =0.332 m/s; ks 0.3 design, 0.03/1.5 sensitivity (p.6, p.8, p.9), material Not known (p.6) | No |
| 300mm branches / 750mm manifold (p.6) | Station-pipework loss | Branch 3.0 m/s at 211.8 l/s per pump (BASE-2P); manifold 0.96 m/s at 423.7 l/s (BASE-2P), 1.41 m/s at 622.6 l/s (CHK-3P); 300mm branch into 750mm manifold (3 pumps) (p.6). Evidence: BASE-2P B1/B2 3.0 m/s, M0 0.96 m/s; velocity tool 300mm/211 l/s =2.985 m/s, 750mm/422 l/s =0.955 m/s; high branch loss forces K ASSUMPTION | No |
| IE2 170kW Fixed Speed assumed star-delta (p.6) | Motor efficiency | IE2 (p.6) vs IE3 77.4% vs 75.4-75.5% overall (p.10); IE3 170 vs 174 kWh/1000m3 (p.10); N-impeller <1 kWh/1000m3 not presented (p.10). Evidence: Table 3: 398/265/133 kW existing vs 390/260/130 kW IE3 (p.10); 638/424/216 l/s IE3 vs 634/422/214 l/s (p.10); reduction ~4 (p.10), 172 single-IE3 (p.11), 3873/11629 kWh/annum on 2907360m3 (p.11) | Yes |
| Controls + metering (p.5, p.11) | Metering / tariff control | No flow measurement (p.11); 200 l/s arbitrary (p.11) vs 211-216 Xylem (p.10); base 10kW summer/20kW winter (p.11); 15kW Jul-Aug 2018 dip unexplained (p.11). Evidence: EDF 2017-2018 reviewed (p.11); typical 280 total/270 pumping vs 265 predicted (p.11); need run-hours, volumes, tariffs to confirm optimising periods (p.5) + automation/supervision/telecontrol + smart monitoring (p.5) | Yes |

## Alternatives

| Option | Run_label | Result | Cost class / basis | Meets target? / Recommended? |
|---|---|---|---|---|
| Like-for-like renewal with IE3 (or IE4) motor – at least one new pump (p.5) | AUD-2P | Document: 2-pump 424 l/s at 260kW 170 kWh/1000m3 vs 422 l/s at 265kW 174 (p.10); saving ~4 (p.10). AUD-2P 424.8 l/s 263.4kW 172.2 illustrates hydraulics unchanged; IE gain only. Unit: 6x CP3231 435mm 170kW IE2 fixed-speed (p.6) | $100k-$1M / Supply/install 1x CP3231/736 435mm IE3 170kW pump+motor; no civils, uses 300mm branch/750mm manifold (p.6) | Yes / Yes |
| Extend 1-pump duty + automate Duty/Duty/Assist selection (p.6) | AUD-1P | AUD-1P 214.6 l/s 132.1kW 171.0 vs AUD-2P 424.8 l/s 263.4kW 172.2; document flat 172/174/174 (p.10) almost same regardless number (p.10) so longer 1-pump avoids starts with no penalty. Unit: 6x CP3231 435mm 170kW IE2 fixed-speed (p.6) | $100k-$1M / SCADA/automation + telecontrol + duty-select logic; no hydraulic change (p.5 scope) | Yes / Yes |
| Retrofit VSDs for energy saving (p.5 scope to assess) | AUD-VSD90 | AUD-VSD95 355.3 l/s 214.0kW, AUD-VSD90 273.5 l/s 160.1kW cannot meet 422 l/s duty (p.10); AUD-VSD80 0 l/s TDH 43.2m stalls vs ~43m rise (p.6)(p.7). Static-dominated twin 900mm x2650m (p.6) leaves no like-for-like turndown; drive losses excluded so apparent part-flow gain unproven. Unit: Fixed Speed assumed star-delta (p.6) | $100k-$1M / 2-3x 170kW (p.6) LV VSD panels + harmonics/filter + commissioning; motor derating check | No / No – only if soft-start/control needed with lifecycle cost including drive/harmonic losses |
| Smart water/energy metering + tariff-period optimisation + confirm base load | AUD-2P-LOW | No flow measurement (p.11); VNF 222 kWh/1000m3 on arbitrary 200 l/s (p.11) vs Xylem 211-216 (p.10) and AUD-2P 212.4 l/s per pump. Base ~10kW summer/~20kW winter (p.11), ~280kW total/~270kW pumping vs 265kW predicted (p.11); Jul-Aug 2018 -15kW unexplained (p.11). Metering to verify 174 (p.11) and 3873/11629 kWh on 2907360m3 (p.11). Unit: Controls + metering (p.5)(p.11) | <$100k / Clamp-on/inline flow + kW logging + half-hourly EDF (p.11) + level survey; tariff-band analysis for optimising periods (p.5) | Yes / Yes |

Details: Overall efficiency existing 75.5 (3 pumps), 75.4 (2 pumps), 75.7 (1 pump) (p.10); IE3 77.4/77.4/77.8% (p.10). Specific energy existing 174/174/172 (p.10); IE3 170/170/167 (p.10). Specific energy remains almost the same regardless of number of pumps running (p.10). N type semi open impeller gave marginal <1 kWh/1000m3 which has not been presented (p.10). VSD runs use ASSUMPTION eff 0.80 no drive loss, not comparable to Xylem 75-77% overall (p.10).

## QA/QC Summary
Checked citations: 6 pumps (p.6); IE2 (p.6); wet-well 124.2-125.8 mNGF (p.6); discharge 168.1 mNGF (p.6); CP3231/735 and /736 IE3 labels (p.10); Table 3 flows 634/422/214, powers 398/265/133, eff 75.5/75.4/75.7%, spec 174/174/172 and IE3 638/424/216, 390/260/130, 77.4/77.4/77.8%, 170/170/167 (p.10); IE3 saving ~4 (p.10); base 10/20kW, 280/270 vs 265 (p.11); arbitrary 200 l/s, 222, volume 2,907,360 m3 2016 (p.11); scope automation/telecontrol/periods/>=1 pump/IE3-IE4+VSD/smart monitoring (p.5). Checked runs: BASE-2P, CHK-3P, CHK-1P, CHK-2P-LOW, ALT-VSD-90, ALT-VSD-80.

* Major – Calibrated model inputs: simulator rated point, eff, C, minor_k are tuning ASSUMPTIONS to force +0.4%/-0.5% match, not document data. Calibration is circular. **Fixed by disclosure:** relabelled AUD-*/BASE-*/CHK-* as illustrative reproducing Table 3 (p.10) within ~1%.
* Major – Roughness sensitivity not actually simulated with ks; level only; C=110 proxy unsupported. **Fixed:** added AUD-2P-SMOOTH/ROUGH and LOW/HIGH runs; confirms friction/level moves flow only ~+/-2% and spec ~169-174, static dominates. Exact C-ks conversion still ASSUMPTION; material Not known (p.6).
* Major – Table 3 Per Pump heading wrong; values are station totals (p.10) matching 265 kW (p.11); blended 172 single-IE3 (p.11) vs all-IE3 170/167 (p.10) unexplained; 10 kWh gap. **Fixed:** treat as station totals; interpret 172 as 1xIE3+1xIE2 average – needs Xylem printout.
* Major – VSD/IE4/N-impeller verification rests on assumed efficiencies and affinity without drive losses. **Noted/qualified:** AUD-VSD90 273.5 l/s 160.1 kW and AUD-VSD95 355.3 l/s 214.0 kW use ASSUMPTION eff 0.80 constant + affinity no drive/harmonic loss; cannot meet 422 l/s duty (p.10); AUD-VSD80 0 l/s proves stall against ~43m lift (p.6)(p.7). IE4 (p.5) no data, N-impeller <1 (p.10) not presented – need curves/quotes.
* Minor – Datum/K legibility: discharge 168.1 (p.6) vs ~168.0 (p.9); static 43.2 vs 43.1; Total K 1.15/3.99/2.55/3.10 vs possibly 3.89 obscured. **Noted:** 0.1m immaterial vs 47-48m TDH; branch K=8.0 ASSUMPTION adopted; native calc needed.
* Minor – Designation/image-only data: CP3231 conflict; schematic 2x2650m O900mm 43m (p.7 image), Fig.2 curves (p.8 image), Fig.3 sheet (p.9 image) image-only. **Noted:** assume same 435mm closed-C family – requires nameplate/curve and level survey.
* Minor – Metering/tariff basis: baseline, 174 vs 222 dispute, 3873/11629 savings, 1-pump duty and tariff optimisation unverified without logging. **Noted:** all conditional on flow+kW+level logging, half-hourly EDF, sub-metering, run-hours/volumes/tariffs.

## Recommendations
1. Retain CP3231 435mm hydraulics; renewal like-for-like. Overall 75.4% 2-pump at 174 kWh/1000m3 (p.10). EDF pumping ~270 kW vs 265 kW predicted aligns (p.11); flat spec almost same regardless number (p.10). [AUD-2P, AUD-1P, AUD-3P]
2. Do NOT fit VSDs for energy saving to meet 422 l/s duty (p.10). Keep Fixed Speed assumed star-delta (p.6). Static-dominated; VSD 0.8 stalls at static floor, VSD 0.95 still needs 46.42m; friction small across ks 0.03/0.3/1.5mm (p.6)(p.8). VSD only if soft-start/control needed with lifecycle cost. [AUD-VSD90, AUD-VSD80]
3. Implement >=1 new pump (p.5) with IE3 or IE4 motor; roll to all at renewal. IE3 CP3231/736 424 l/s 260 kW 77.4% 170 kWh/1000m3 vs existing 422 l/s 265 kW 75.4% 174 (p.10); 1-pump IE3 216 l/s 130 kW 77.8% 167 vs 214 l/s 133 kW 75.7% 172 (p.10); N-impeller <1 (p.10) not justified alone; IE4 no data – require quote/curve. [AUD-2P]
4. Prefer extended 1-pump running via automation/duty-select; use 2/3 only for demand; optimise to off-peak tariffs. Operates 2 pumps most time up to 3 (p.6); firm 2-pump requires 3 available – met with 6 installed (p.6). 1-pump 172 vs 2-pump 174 (p.10); no penalty. Scope automation/supervision/telecontrol + optimising periods (p.5). [AUD-1P vs AUD-2P]
5. Sub-meter services, log half-hourly kW + flow + levels, resolve 15 kW dip, re-baseline 174 (p.10)(p.11). Base ~10 kW summer/~20 kW winter (p.11); VNF 222 on arbitrary 200 l/s (p.11) vs Xylem 211-216 (p.10) incorrect. [AUD-2P-LOW]

## Limitations
* No flow measurement undertaken; VNF uses arbitrary 200 l/s per pump (p.11) vs Xylem ~211-216 l/s per pump (422/2, 214, 424/2, 216) (p.10) – cannot validate 174 vs 222 without metering.
* Pipe material Not known (p.6); true ks unknown – design 0.3 mm with 0.03/1.5 mm cases (p.6, p.8, p.9) unverified; need pressure-drop test.
* Pump designation conflict and image-only schematic/curves/calc sheet (p.6, p.7, p.8, p.9) – need nameplate, Xylem duty printouts, native Fig.3 file, digitised Fig.2.
* Duty, drives, levels assumed/from schematic (p.6) – need ops log, starter-panel check, level survey 124.2-125.8 mNGF (p.6).
* Supplementary load split not metered; July-Aug 2018 -15 kW no obvious explanation (p.11); Figure 4 monthly bars not tabulated – need half-hourly EDF + sub-meter.
* Annual volume single-year 2016 only (p.11); 66% utilisation basis unclear (p.11); no 2017-2018 volumes, hours, tariff/ops-period data though optimising operations time periods is goal (p.5) – need run-hours, volumes, tariffs.
* All savings (approx. 4 kWh/1000m3 (p.10); 172 single-IE3 (p.11); 3873/11629 kWh/annum on 2907360m3 (p.11)), VSD stall, and 1-pump strategy conditional on above data; simulator efficiencies and C-values are ASSUMPTIONS excluding drive/harmonic losses and off-BEP drop.
