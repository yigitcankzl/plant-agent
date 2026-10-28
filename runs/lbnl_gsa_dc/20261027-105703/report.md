DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum - Energy Assessment, Seventh Floor Data Centers, RAY Federal Building

## Purpose
Assess energy waste in seventh-floor Data Centers DC 1 and DC 2, Robert A. Young (RAY) Federal Building, St. Louis, Missouri, using Lawrence Berkeley National Laboratory (R. Mahdavi) for GSA/FEMP, *Seventh Floor Data Centers RAY Building Energy Usage Efficiency Assessment Report, April 2014* (p.25, p.11).
Address: end-use estimates, UPS readings, chilled-water and glycol plant observations, rack and CAU temperature monitoring and sub-floor pressure data; identify waste by air management, cooling plant, pumps, electrical, lighting; state expected savings (kW, kWh/yr, $/yr) and cost/simple payback, and reachable PUE.

## Background
- Building: RAY building is an office building 1,130,000+ square feet ... located in Saint Louis, Missouri ... owned by GSA (p.8).
- Vintage: seventh floor data centers were built in 1990 (p.8).
- Metering/service mapping: Most of the automatic transfer switches (ATS) are metered. ATS 5 supports the glycol system's dry coolers and primary pumps, as well as other non-data-center systems. ATS 7 supports the glycol system's secondary pumps and other non-data-center systems. Different automatic transfer switches support the chiller plant. ATS 10 serves Data Center 1 and ATS 11 serves Data Center 2 (p.11).
- Floor plan equipment labels DC1/DC2: CAU17 20 Tons ... PDU PC-01 PC-5-1 PC-5-2 PC-5-3 PC-6-1 PDU PC-06 PDU PC-07 30KVA 75KVA CAU 28 Rack 78-D CR1-1 Comm Rack 160 KVA UPS Rack 67-G CAU-27 Liebert (p.9).
- Cooling architecture: The DC 1 and DC 2 equipment is air-cooled. Cool air is provided by five CAUs in DC ... For the two dual-coil CAU units, the chilled water coil is the primary cooling coil, and the DX coil is the secondary cooling coil. There was one chilled-water-only unit (p.15).
- CAU mapping per Tables 3-4: DC1 7-1 to 7-5 five units (p.11); DC2 7-6 to 7-9 four units (p.12) with 7-6 OFF 0kW; Table 6 lists 9 labels 7-1 to 7-9 (p.16).
- Electrical: steps the voltage down from 13.8 kilovolts (kV) to 480 kV [source typo, should be 480V - see QA/QC] (p.17). Power is delivered to the building at this voltage for motor loads, UPS ... stepped down to 277 V for the lighting ... 120/208 volts [plug loads] (p.17).
- Chilled water plant: The chilled water system consists of four chillers, but during LBNL's visit, only a 400-ton stacked chiller was operational. The other three (one 1,000-ton chiller and 1,200-ton chillers) were off (p.14). Schematic: CT-1: 400 Chiller 3: 1000 CT-2: 1200 Chiller 2: 1000 CT-3: 1200 Chiller 1: 1200 Chiller 4: 400 ... PCHWP CHWS CHWR HX HXWP (p.15).

## Design Criteria
- Assessment basis and baseline period: LBNL RAY Building Energy Usage Assessment Report April 2014; field baselining January 28-31, 2014; Table 3-4 spot readings not averages (p.25, p.11).
- Energy cost rate for savings valuation: $0.07 per kWh (Task question statement (about $0.07/kWh)).
- Continuous operation hours: **ASSUMPTION:** 8760 hr/yr - reason: data centers operate 24/7, standard for audit (IT and cooling run continuously).
- PUE definition: EM.M.1 PUE (Total Power/IT Power) 2.20 Poor (p.18 Table 8): PUE = Total facility power / IT power; current 2.20 Poor.
- HVAC effectiveness definition: EM.M.2 HVAC Effectiveness (IT Power/HVAC power) (p.18 Table 8): IT Power divided by HVAC power.
- ASHRAE environmental class: 2011 ASHRAE Ranges (GSA data center considered class A1) (p.23 Table 11): Class A1 data center.
- Ideal rack intake temperature target: AM.M.4 Rack Intake Temperatures 70F Lower than ideal 80F (p.20 Table): 80 F ideal intake; current average 70 F indicates overcooling.
- Temperature rate-of-change limit: ASHRAE limit of 9F (p.30): 9 F limit; observed 1-2 F.
- IT power measurement convention: UPS display reading was assumed to be actual IT power (p.11): Use UPS display as IT load; UPS loss from efficiency curve; PDU loss estimated.
- Firm capacity definition used: largest unit out.

## Data and Assumptions
End-use and observed data (all spot-reading basis):

- Estimation basis: most of the data were estimates based on motor nameplates, plus assumed efficiency ... The numbers are result of one spot reading and not an average (p.11).
- UPS reading convention: The UPS display reading was assumed to be actual IT power. By using the UPS efficiency curve, electrical power loss in the UPS was calculated (p.11).
- PDU loss and generator heater assumption: The PDU electrical power loss was estimated. Also, it was assumed that the generator block heater power used 10 kW, which is typical for many such generators (p.11).
- DC1 CAU fan power each: CAU 7-1 Fan ON 5 ... CAU 7-2 Fan ON 5 ... CAU 7-5 Fan ON 5 (Table 3) (p.11): 5 per CAU fan (kW).
- DC1 total DX+fan power Jan28-31: Total DX/Fan Power 45 40 45 30 (p.11): 45 (Jan28), 40 (Jan29), 45 (Jan30), 30 (Jan31) (kW).
- DC1 CAU DX loading example CAU7-5: CAU 7-5 Dx % 75 15 50 10 75 15 25 5 Each DX 20 15 20 10 (p.11).
- DC2 CAU 7-6 status: CAU 7-6 Fan OFF 0 OFF 0 OFF 0 OFF 0 (p.11): 0 (OFF Jan28-31) (kW).
- DC2 CAU 7-7/7-8 operation: CAU 7-7 Fan ON 5 ON 5 ON 5 ON 5 Dx % 25 5 25 5 25 5 25 5 Each DX 10 10 10 10 CAU 7-8 Fan ON 5 ON 5 ON 5 ON 5 Dx % 75 15 75 15 100 20 50 ... (p.12).
- DC1 end-use split: Fans 11% Cooling, Dry coolers/pumps 16% IT Load 46% Cooling, Chilled water 5% Cooling DX compressors 11% Lighting 2% Standby Gen block heater 2% PDU/trans loss 2% UPS Loss 5% (p.13).
- DC2 end-use split: Fans 8% Cooling, Dry coolers/pumps 17% IT Load 43% Cooling, Chilled water 4% Cooling DX compressors 17% Standby Gen block heater 3% Lighting 2% PDU/trans loss 2% UPS Loss 4% (p.14).
- PUE and benchmarking: EM.M.1 PUE (Total Power/IT Power) 2.20 Poor ... The DC 2 numbers are very close to those of DC 1 (p.18).
- Air management metrics summary: Average Rack Temperature Rise degF 8 Poor Return Temperature Index % 125 Fair amount of air is recirculating Rack Intake Temperatures degF 70 Lower than ideal 80degF Rack Cooling Index % Lo 94 Hi 100 Some overcooled ... Airflow Efficiency W/cfm .52 Fair (p.20).
- UPS redundancy: There are no redundant UPS at the data center, so one UPS was supplying all the IT power (p.21).
- UPS efficiency curves reference: Factory Measurements of UPS Efficiency (tested using linear loads) Flywheel UPS Double-Conversion UPS Delta-Conversion UPS [Figure 10 UPS load factor] (p.21).
- BAS chilled water anomaly: The chilled water return [CHWR] is going from 60degF to 62degF, and the chilled water supply [CWS] is going from 52degF to 58.3degF ... many obvious erroneous temperature readings ... heat was rejected to both sides of the heat exchanger! (p.22).
- Overcooling observation SAT: Generally, the data center was over-cooled. The Average Supply Air Temperature (SAT) was low (approximately 62degF) (p.23).
- Underfloor and rack leakage: No major obstructions were observed under the raised floor except for few areas. Chilled water piping and cables were observed in some areas. Rack densities were low ... empty racks, open spots, and tile openings ... Many openings within the racks ... Large openings were observed by and under PDUs ... top of the racks was open (p.23).
- DCPro air management tool results: IAT max Typical (not extreme) max IT equipment intake temperature 82 F IAT min Typical (not extreme) min IT equipment intake temperature 58 F SAT Typical (airflow weighted) AHU supply air temperature 60 F deltaSAT Maximum difference between AHU supply air temperatures 11 F (p.26).
- Rack recirculation evidence: intake air temperatures at three levels (top, middle, and bottom) are very different. The top and middle temperatures measured much warmer than the bottom, which illustrates major recirculation ... intake air at the top is at higher temperature, the exhaust will be at a higher temperature as well (p.27).
- Temperature rate of change: The temperature rate of change was only about 1degF to 2degF, which is much lower than the ASHRAE limit of 9degF (p.30).
- RCI compliance: Based on an RCIHi of more than 98 percent, Based on an RCILo of more than 94 percent ... similar to those derived from execution of DCPro (p.30).
- Cooling load and CHW temps: approximately 500 tons of cooling were provided to the data center. The chilled water from the chiller plant was supplied at 56degF. The chilled water return temperature was 60.7degF (according to the BAS). It was not possible to measure exactly how much cooling was provided by the chilled water system and the DX system (p.31).
- Humidity: Humidity ranged between 20 and 30 percent. Make-up air entering the data centers was as dry as the data center environment (p.34).
- Subfloor pressure: The pressure under the raised floor varied between 0.02 inches of water column (inwc) to 0.05 inwc. ... The big increase in pressure on January 30 at 12:00 pm was the result of covering some of the misplaced perforated tiles (p.34).
- Lighting power: The total power used by the lighting in the data center and UPS rooms is estimated to be 4 kW for DC 1 and 3 kW for DC 2 (p.18).
- Cooling detail Table 14 (p.31): DC1 DX25 CHW12 dry/pumps35 fans25 total97 / DC2 DX30 CHW8 dry/pumps31 fans15 total84 (kW).
- IT denominator conflict (p.10, p.12): text IT 118kW DC1 and 88kW DC2 vs Table 2 102kW DC1 and 77kW DC2; Table 5 102/77kW with PUE 2.2/2.34 (p.12); DC2 TOTAL 280kW typo should be 180kW (77+8+3+5+3+30+8+31+15=180) to give PUE 2.34.

**ASSUMPTIONS (labeled):**
- **ASSUMPTION:** 8760 hr/yr continuous - reason: 24/7 IT duty. Used for all kWh/yr = kW x 8760.
- **ASSUMPTION:** $0.07/kWh - reason: task statement. Used for all $/yr = kWh x 0.07.
- **ASSUMPTION:** Hydraulic model is secondary-CHW distribution analog only - reason: pump/motor nameplates withheld except 5kW fans (p.11-p.12) and 400/1000/1200T chillers (p.14-p.15); topology from Fig5 (p.15). Used to show sizing/runout sensitivity, not to meter air.
- **ASSUMPTION:** Air/thermal savings cannot be derived from water hydraulic runs - reason: EPANET cannot model air/thermal; report gives only spot DX/fan kW (p.11-p.12) and % splits (p.13-p.14).
- **ASSUMPTION:** PUE 1.5-1.65 reachable retained only as engineering estimate - reason: if 16-17% dry/pumps + 11-17% DX + 8-11% fans (p.13-p.14) cut; requires metered savings and withheld costs, not verified.

## Model Calibration
Hydraulic analog runs are for pump sizing sensitivity only; not air/thermal calibration. Prior CHW-cal / CHW-vfd08 / CHW-1p12in / CHW-base runs rejected as fictional sizing (see QA/QC).

| Run label | Simulated | Measured (p.N) | Agreement |
|---|---|---|---|
| RAY-PMP-CORR | 2x1241gpm 82.36ft 27.1kW each total 54.1kW 96.0kWh/ML 10.14fps 95% rated no warnings | 500 tons at CHWS 56F CHWR 60.7F BAS, split CHW vs DX unknown (p.31); CAU fans 5kW each, Total DX/Fan 45/40/45/30 DC1 (p.11) | Realistic % rated; shows attainable duty if pipes/pumps sized correctly; does not prove site kW |
| RAY-PMP-14B | 2x1789gpm 56.17ft 26.6kW each total 53.2kW 65.5kWh/ML 7.46fps 138% warnings | Same 500T 4.7F delta (p.31) implies ~2550gpm, not 4380gpm prior | Runout warning; proves overspeed/oversized-flow penalty |
| RAY-PMP-BASE | 2x2525gpm 3.05ft 2.0kW each total 4.1kW 3.6kWh/ML 10.52fps 194% warnings | CAU 7-7 25%/5kW +10kW DX, 7-8 75-100%/15-20kW, 7-6 OFF 0 (p.11-p.12) | Extreme runout; head collapse; not operable |
| velocity checks | 10-in 1.8mgd=5.106fps, 10-in 3.672mgd=10.416fps, 14-in 3.672mgd=5.315fps | Subfloor 0.02-0.05 inwc air (p.34) - not water psi; do not conflate | Pipe context only; 7.0-12.43fps prior runs were 2-3x normal water practice, proving prior sizing wrong |
| Thermal qualitative | n/a - no air simulation performed | SAT ~62F overcooled (p.23); SAT 60F deltaSAT 11F IATmax82F IATmin58F (p.26); intake avg70F < ideal80F (p.20); rate 1-2F <9F limit (p.30); RCIHi>98 RCILo>94 (p.30); stratification Rack1/15/2 (p.27-p.29); RTI125% (p.20) vs 90% average bypass (p.25) and Table13 RTI 128% (p.25) | Mixed recirculation+bypass; DCPro tool vs monitoring not reconciled (p.25-p.26) |

No verified pump kW savings; prior 11.1kW=97236kWh/yr $6807/yr and 18.7kW=163812kWh/yr $11467/yr rejected as artifact. Residuals 7-15% withdrawn.

## Capacity Evaluation

| Unit | Limit | Binds at (p.N) | Evidence (run label) | Limits target? |
|---|---|---|---|---|
| DC1 5xCAU + floor/racks/PDU openings (p.15 p.23-p.24) | Air-management bypass/recirculation, not room capacity | RTI 125% + rack dT 8F Poor + intake 70F <80F + 0.52W/cfm Fair (p.20); SAT 60-62F (p.23 p.26); recirculation top/middle vs bottom (p.27-p.29) | RAY-PMP-CORR vs RAY-PMP-14B shows excess bypass flow wastes energy; air diagnosis from observations | Yes |
| DC2 CAUs 7-6/7-7/7-8 + 17/27/28 (p.9 p.12) | Firm CAU redundancy lost | 7-6 OFF 0kW all days (p.11); 7-7 25% + 7-8 75-100% loaded (p.12); DC1 7-1 to 7-5 five units (p.11), DC2 7-6 to 7-9 four units (p.12) | Firm = largest out: DC2 already degraded; next failure leaves 3/4 - no N+1 | Yes |
| Chillers 1200/1000/1000/400T + CT400/1200/1200 + HX (p.14-p.15) | ~500T low delta-T + DX-assist dependence | 500 tons at 56F/60.7F 4.7F delta split unknown (p.31); BAS 60-62F/52-58.3F erroneous both-side reject (p.22); only 400T stacked running (p.14) | RAY-PMP-BASE 194% runout proves low delta-T forces high flow; CHW 4-5% vs DX 11-17% + dry/pumps 16-17% (p.13-p.14) | Yes |
| Glycol dry coolers + primary/secondary pumps via ATS5/7 (p.11 p.16) | Glycol condensing + pumping overhead | Dry/pumps 16% DC1 17% DC2 + DX 11% DC1 17% DC2 + fans 11% DC1 8% DC2 (p.13-p.14); ATS5 dry+primary+other ATS7 secondary+other (p.11) | Table14 35/31kW dry/pumps (p.31); allocation includes unknown non-DC share | Yes |
| Secondary CHW loop pumps (p.15 Fig5) | Secondary pumps runout, no speed control | 2-pump analog at 95% (RAY-PMP-CORR) vs 138-194% runout (RAY-PMP-14B/BASE); 7.46-10.52fps high | Pumps far right of BEP without VFD; motor/drive loss secondary to control loss | Yes |
| UPS + PDU/transformers 480V/277V/120-208V (p.17) | UPS/PDU part-load + transformer loss | UPS Loss 5% DC1 4% DC2 + PDU 2% (p.13-p.14); single UPS no redundancy (p.21); Fig10 load-factor curves (p.21); 30/75/160kVA (p.9); Table5 12/8kW UPS +4/3kW PDU (p.12) | Low load factor = low efficiency per Fig10; block heater 10kW typical (p.11) =2-3% (p.13-p.14) | No |
| DC/UPS lighting (p.18) | Lighting 7kW continuous, no sensors | 4kW DC1 +3kW DC2 (p.18) =2% each (p.13-p.14) continuous 8760hr **ASSUMPTION** | 7kW x8760=61320kWh/yr base; small vs PUE 2.20 (p.18) | No |

Chiller firm: largest 1200T out leaves 2400T >500T (p.31) adequate. Pump firm not evaluable - nameplates withheld.

## Alternatives

| Alternative (unit) | kW / kWh/yr / $/yr at $0.07 | Cost class / Payback | Run label | Rec? |
|---|---|---|---|---|
| AM-1 Blanking + seal bypass: blank empty racks/open spots, brush cable cutouts, close PDU/under-rack openings, cap open tops, replace misplaced perforated tiles (p.23-p.24) (DC1/DC2 air distribution + CAU fans 5kW each p.11-p.12) | No verified kW; enables SAT 60F (p.26)/~62F (p.23) rise and intake 70F to ideal 80F (p.20); corrects RTI 125% (p.20) vs 90%/128% (p.25) and IAT 58-82F spread deltaSAT 11F (p.26); subfloor 0.02-0.05 inwc rises after covering tiles (p.34 p.36) | **ASSUMPTION** <$100k panels/grommets/brush + tile re-layout labor; payback TBD pending metering | n/a - judgement from p.23-p.24 p.26-p.29 p.34-p.36; hydraulic proxy rejected | Yes |
| AM-2 CAU fan VFD + raise SAT/control: slow fans to 0.02-0.05 inwc plenum (p.34) and ~80F intake (p.20), standby unneeded CAU (7-6 OFF precedent p.11) (DC1 7-1 to 7-5 + DC2 7-7/7-8 + Liebert 17/27/28 p.9 p.11-p.12 p.15-p.16) | No verified kW; CAU Total DX/Fan 45/40/45/30kW (p.11) unloads similarly; RCI Lo94 Hi100 preserved (p.20 p.30) | **ASSUMPTION** $100k-$1M VFDs + SAT reset + TAB (5 CAUs/DC p.15, 5kW each p.11-p.12); payback TBD | n/a - affinity not proven by water model | Yes |
| CP-1 Water-side optimization: calibrate BAS (CHWR 60-62F CWS 52-58.3F erroneous p.22), raise CHWS from 56F (p.31) reset, maximize CHW-primary dual-coil use (p.15-p.16), lock out DX secondary except peak (DX 11% DC1 17% DC2 p.13-p.14) (Chiller plant 1200/1000/1000/400T + towers p.14-p.15) | No verified kW; addresses 500T at 4.7F delta (56 to 60.7F p.31); shifts off glycol DX/dry 16% DC1 17% DC2 (p.13-p.14) via shared ATS5/7 (p.11) to 400T stacked (p.14) | **ASSUMPTION** <$100k sensor calibration + logic + commissioning; payback TBD | n/a - requires CHW vs DX split metering withheld | Yes |
| PM-1 Secondary CHW pump VFD + duty-standby (Secondary pumps p.15 Fig5) | No verified kW savings; prior CHW-cal 23.2kW vs CHW-vfd08 12.1kW vs CHW-1p12in 4.5kW rejected; RAY-PMP-CORR 54.1kW 96.0kWh/ML vs RAY-PMP-14B 53.2kW 65.5kWh/ML vs RAY-PMP-BASE 4.1kW shows sizing sensitivity only | **ASSUMPTION** $100k-$1M 2x secondary-pump VFDs + DP control; payback TBD pending metered DP/flow | RAY-PMP-CORR / RAY-PMP-14B / RAY-PMP-BASE | Study only - do not commit without metering |
| EL-1 UPS/PDU efficiency: raise load factor/retire lightly loaded 30/75/160kVA (p.9), enable ECO/delta-conversion, high-efficiency transformers; keep 10kW heater standby only (p.11) (UPS+PDUs PC-01/05/06/07 p.17) | UPS 12/8kW + PDU 4/3kW (p.12); 4-5%+2% (p.13-p.14); no redundant UPS single carries IT (p.21); Fig10 curves (p.21) show 2-4pts gain; small vs HVAC but improves PUE 2.20 Poor (p.18) | **ASSUMPTION** <$100k study/enablement; payback TBD | n/a - no electrical simulation | No - study only |
| LT-1 Lighting controls + LED from 4kW DC1 +3kW DC2 (p.18) 2% each (p.13-p.14) (DC+UPS 277V p.17-p.18) | Base 7kW (p.18) x 8760hr **ASSUMPTION** =61320kWh/yr; 50% cut =3.5kW 30660kWh/yr $2146/yr rejected as unverified **ASSUMPTION**; judgement only | **ASSUMPTION** <$100k LED + sensors; payback TBD (<3yr claim withdrawn) | n/a | Yes - low risk |

Formulas retained only as **ASSUMPTION**: kWh/yr = kW x 8760; $/yr = kWh x $0.07. All 8760hr x $0.07 extrapolations require metering + seasonal staging (only 400T running p.14).

## QA/QC Summary
Checked citations: p.11 ATS5/ATS7 shared + ATS10/DC1 ATS11/DC2 + nameplate+assumed efficiency single spot; p.13 DC1 split IT46 Fans11 DX11 Dry/pumps16 CHW5 UPS5 PDU2 Light2 Gen2; p.14 DC2 split IT43 Fans8 DX17 Dry/pumps17 CHW4 UPS4 PDU2 Light2 Gen3 + only 400-ton running; p.18 lighting 4kW+3kW + PUE 2.20 Poor; p.20 RTI125% dT8F intake70F vs 80F RCI Lo94 Hi100 0.52 W/cfm; p.15 five CAUs/DC + chillers/towers; p.16 dual-coil CHW primary DX secondary; p.17 voltages; p.22 BAS errors; p.23 SAT ~62F + openings; p.26 IAT82/58 SAT60 deltaSAT11F; p.10 IT contradiction; p.21 single UPS + Fig10; p.25 RTI90% + VAHU42000cfm VEquip53000cfm RTI128% Table13; p.30 rate 1-2F vs 9F + RCI; p.31 500T CHWS56F CHWR60.7F + Table14 97/84kW; p.34 humidity 20-30% + subfloor pressure rise Jan30.

Checked runs: RAY-PMP-CORR, RAY-PMP-14B, RAY-PMP-BASE + velocity; prior CHW-cal, CHW-vfd08, CHW-1p12in, CHW-base reviewed and rejected.

Issues and resolution:
- Major: Baseline IT denominator unresolved 15-16% (p.10 118/88kW vs Table2/Table5 102/77kW p.10 p.12) - fixed: adopt Table5 consistent with PUE 2.2/2.34, note DC2 TOTAL 280 typo to 180kW; all savings/PUE scale flagged unsupported.
- Major: RTI selective citation 125% (p.20) vs 90%/128% (p.25) - fixed: disclose both; diagnosis mixed recirculation+bypass per stratification (p.27-p.29) and tile evidence (p.23-p.24 p.36).
- Major: Fictional hydraulic sizing (1300gpm 55ft +12/10-in, 4380gpm vs ~2550gpm implied by 500T 4.7F p.31, 7-12fps runout) - rejected: replaced with RAY-PMP-CORR 95% vs 138-194% sensitivity; savings 11.1kW/18.7kW withdrawn; residuals withdrawn.
- Major: Water proxy for air/SAT/DX/UPS/lighting verification; air psi vs inwc conflation - rejected: measures judgement from p.23-p.24 p.26-p.29 p.34-p.36, not simulated; velocity quoted separately.
- Major: Glycol apportionment unknown non-DC share on ATS5/7 (p.11), spot x8760 overstates seasonal - fixed: preserve 16%/17% (p.13-p.14) Table14 35/31kW (p.31) as report estimate only.
- Major: Firm capacity not mapped (9 labels 7-1 to 7-9 vs 5/DC) - fixed: DC1 7-1 to 7-5 (p.11), DC2 7-6 to 7-9 (p.12) with 7-6 OFF; DC2 firm degraded; chiller firm 1200T out leaves 2400T >500T adequate.
- Major: Reachable PUE 1.5-1.65 unsupported - fixed: retained only as **ASSUMPTION** estimate, not verified outcome; PUE 2.2 DC1 2.34 DC2 Table5 (p.12) vs 2.20 Poor (p.18) noted.
- Minor: p.17 13.8kV to 480 kV typo - fixed: correct 480V per 277V/120/208V (p.17).
- Minor: 10kW heater typical (p.11), 50% lighting cut, full-load continuous - rejected as payback basis; sensitivity/metering required.

## Recommendations
1. Implement AM-1 first (<$100k **ASSUMPTION**): blanking, brush grommets, PDU slot closure, cap open tops, correct misplaced perforated tiles. Justified by open racks/tiles/PDU leakage (p.23-p.24), IAT 58-82F deltaSAT 11F (p.26), stratification (p.27-p.29), subfloor 0.02-0.05 inwc response Jan30 (p.34 p.36).
2. Calibrate BAS and recommission water-side (CP-1, <$100k **ASSUMPTION**): correct CHWR 60-62F/CWS 52-58.3F errors (p.22), use CHWS 56F/CHWR 60.7F operating point (p.31) for reset, enforce CHW-primary dual-coil (p.15-p.16), DX lockout. Meter CHW vs DX split first - currently unknown (p.31).
3. Proceed AM-2/PM-1 only after metering: CAU fan VFD + SAT toward 80F ideal (p.20) preserving RCIHi>98 RCILo>94 (p.30) and 1-2F <9F rate (p.30); secondary-pump VFD + duty-standby with metered DP/flow. VFD benefit not proven by model (RAY-PMP-CORR/14B/BASE sensitivity only).
4. Electrical/lighting: UPS load-factor/ECO study (single UPS no redundancy p.21, Fig10 p.21); lighting LED/controls low-risk but do not book 3.5kW savings without metering. Keep 10kW block heater (p.11) standby only.
5. PUE: current 2.20 Poor (p.18) [Table5 2.2/2.34 (p.12)]; 1.5-1.65 reachable only as **ASSUMPTION** if AM+CP+PM cut 16-17% dry/pumps +11-17% DX +8-11% fans (p.13-p.14). Do not present as verified.

## Limitations
- Most data were estimates based on motor nameplates, plus assumed efficiency ... single spot reading not average (p.11); Table 3-4 spot readings not averages (p.25, p.11).
- ATS5 dry+primary+other non-DC, ATS7 secondary+other non-DC apportionment unknown (p.11); report 16%/17% (p.13-p.14) preserved as estimate.
- IT denominator 15-16% unresolved (p.10); dry/pumps share unknown; all kW/kWh/$/PUE scale with IT.
- RTI 125% (p.20) contradicts 90%/128% (p.25); DCPro tool vs monitoring not reconciled (p.25-p.26).
- BAS temps erroneous heat to both sides (p.22); CHWS conflict 56F/60.7F text (p.31) vs 52-58.3F display (p.22); CHW vs DX split unknown (p.31).
- CAU count mapping: five CAUs in DC (p.15) vs nine labels 7-1 to 7-9 (p.16); DC mapping per Tables 3-4 (p.11-p.12) used.
- Pump/motor nameplates, CAU tons, recommendation costs withheld; costs/paybacks are **ASSUMPTION** cost classes only; 8760hr x $0.07 extrapolations require seasonal metering (only 400T running p.14).
- Hydraulic runs are analog only; velocities 7-10fps high; no air-flow, thermal, or electrical simulation performed.
