DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Crissey Lock Pumping Station — Pump Assessment Technical Memorandum
**Facility:** Crissey Lock Pumping Station, Canal du Centre, France
**Source:** Arcadis for Voies navigables de France, VNF Crissey Lock Pumping Station Pump Assessment Report, 2020 (Interreg Green WIN public deliverable)

## Purpose
Assess VNF plan to replace out-of-service pumps with one new Xylem CT3400/736 submersible pump nominal 600 l/s (p.5, p.7) lifting from River Saone varying ~6 m (p.8):
1. Is CT3400/736 a good match for system and river range 171.45 to 177.48 mNGF (p.8)?
2. Would variable speed drives (VSD) save energy given batch use?
3. Expected annual energy and saving vs old pump?
4. Is proposed DN700 vertical riser with automated gate valve directly upstream of DN600 flowmeter right against 2.2 m/s station limit and meter accuracy?
5. List recommended measures quantified with simulator where possible.

## Background
- Existing: equipped with 2 RATEAU - Type: ID BV 57 pumps although these are out of service (p.6).
- Existing control precedent: duty/standby via intermediate + far upstream sensors (p.6).
- Future: a pump is required with a nominal flow of 0.6m3/s and an automated gate valve (p.7), automated from the control desk with driven by signals from the upstream level measurement system (p.7).
- Target: monoblock centrifugal submersible, dry-well arrangement per Fig.2 (p.5); smart water and energy monitoring + automation, supervision, telecontrol; optimise operating periods (p.5).
- River data: river level data between January 2016 and November 2019 has been gathered (p.8); level remains between 172.1m and 173.1m for 85% of the time (p.9).
- Levels from Fig.3 (p.8): Saone high: 177.48 mNGF (p.8); Saone low: 171.45 mNGF (p.8); pump: 170.353 mNGF (p.8); backflow: 182.963 mNGF (p.8); level of River Saone can vary by six metres (p.8).
- System curves (p.11): Highest Lift - River BWL 171.45mNGF (p.11); Design Lift - River 172.4mNGF (p.11); Lowest Lift - River TWL 177.48mNGF (p.11).
- Pump selection: selection of CT3400/735 ~830 490 mm impeller pump to meet the nominal flow of 600 l/s (p.11); superseded by newer 8-pole motor model CT3400/736 ~830 490 mm impeller which essentially achieves the same performance (p.11). Alternative: 12-pole motor pump from Xylem, model reference CT3531/806 ~1240 710 mm impeller (p.11).
- Units on path assessed: River Saone intake / suction sump (pump level 170.353 mNGF) (p.8) > Xylem CT3400/736 submersible monoblock centrifugal pump (dry-well) (p.5, p.11) > DN700 vertical discharge riser [ASSUMPTION per brief — see RFI below] > Automated gate / sectioning valve (p.7) > DN600 electromagnetic flowmeter [ASSUMPTION per brief] > Discharge pipework to canal / backflow 182.963 mNGF (p.8) > Upstream canal level sensors - intermediate + far upstream (p.6) > Control desk / API + IHM automation, supervision, telecontrol + smart energy monitoring (p.5, p.7).

## Design Criteria
| Criterion | Value | Source |
|---|---|---|
| Targeted / nominal pump flow | 0.6 m3/s (600 l/s) | p.5 + p.7 |
| Pump type | Monoblock centrifugal submersible, dry-well per Fig.2 | p.5 |
| Motor energy performance target | IE3 or IE4 | p.5 |
| Station pipework velocity limit | 2.2 m/s max in station pipework | Task brief citing CTCG Paper 73 — ASSUMPTION: not in pages [5,6,7,8,9,10,11,12,14]; applied as firm criterion per brief instruction (see RFI-07) |
| Flowmeter accuracy - straight lengths | Requires 5D upstream / 3D downstream undisturbed; gate valve is disturbance | ASSUMPTION: standard electromagnetic practice; not in pages (see RFI-02) |
| Control philosophy | Automated from control desk / API driven by upstream level sensors (intermediate + far upstream); gate valve opens fully on low level, pump runs to high level | p.6 + p.7 |
| Monitoring | Smart water and energy monitoring + automation, supervision, telecontrol; optimise operating periods | p.5 |
| Operating duty for energy comparison | 400 basins/year = 880,000 m3/year ~ 408 h/year at 600 l/s | p.14 VNF advice |
| River operating range | Saone 171.45 (BWL/highest lift) to 177.48 mNGF (TWL/lowest lift); Design 172.4 mNGF; ~6 m variation | p.8 + p.11 |

## Data and Assumptions
### Verifiable data register (only facts in pages)
- D01 VNF planned flow: Targeted water flow: 0.6 m3/s (p.5) — 0.6 m3/s.
- D02 Existing: 2x RATEAU ID BV 57 out of service (p.6).
- D03 Future: nominal 0.6 m3/s + automated gate valve (p.7).
- D04 Automation: control desk + upstream levels (p.7).
- D05–D08 Levels: 177.48 / 171.45 / 170.353 / 182.963 mNGF (p.8 Fig.3).
- D10 River data 01/2016 to 11/2019 (p.8).
- D11 Typical band 172.1 to 173.1 mNGF for 85% time (p.9).
- D12–D14 System curves for 171.45 / 172.4 / 177.48 mNGF (p.11).
- D15 Selected CT3400/735 ~830 490mm to meet 600 l/s (p.11).
- D16 Newer CT3400/736 ~830 490mm 8-pole same performance (p.11).
- D17 Alternative CT3531/806 ~1240 710mm 12-pole (p.11).
- D18 Fixed-speed runout: pumped flows would reach approximately 800 l/s at minimum lift when river high (p.11) — ~800 l/s.
- D19 CT3400/736 design: 610 l/s, NPSHr 4.25 m, 95.4 kW, 77.5%, 43.5 kWh/1000m3 (p.12 Table 1).
- D20 CT3400/736 low-lift: Minimum 803 l/s, NPSHr 8.22 m, 96.2 kW, 67.3%, 33.3 kWh/1000m3 (p.12 Table 1).
- D21 Alternative design: 604 l/s, NPSHr 2.66 m, 92.7 kW, 78.8%, 42.6 kWh/1000m3 — labelled CT3500/806 in Table 1 (p.12) vs CT3531/806 in text (p.11) — source naming inconsistency flagged.
- D22 Alternative low-lift: Minimum 821 l/s, NPSHr 5.06 m, 95.8 kW, 70.5%, 32.4 kWh/1000m3 (p.12).
- D23 Motors: available pumps have IE2 motors, and an IE3 high efficiency motor does not appear as option (p.12) — IE2 only.
- D24 Power factor: 0.52 to 0.6 for 12-pole vs 0.8 to 0.82 for CT3400 8-pole (p.12).
- D25 Old measured flow 880 l/s (p.14 Table 3).
- D26 Old measured: 300A, 380V, 166 kW input, 99 kW hydraulic, 60%, 52.4 kWh/1000m3 (p.14 Table 3).
- D27 Prior estimate ~75 kWh/1000m3 without running time — unreliable (p.14).
- D28 Annual: 400 basins/year, 880,000 m3/year, ~408 hours/year at 600 l/s (p.14).

### RFIs / Assumptions (labelled)
- ASSUMPTION RFI-01: DN700 riser, DN600 meter, automated gate valve immediately upstream of meter with zero straight length worst case. Reason: brief states arrangement; Fig.2 scan illegible, diameters not in pages [5,6,7,8,9,10,11,12,14].
- ASSUMPTION RFI-02: Adopt Arcadis derived system curves Highest/Design/Lowest for River 171.45/172.4/177.48 mNGF (p.11, p.8) as basis. Do not recompute static head from backflow 182.963 mNGF (p.8) alone. Reason: curves are study basis.
- ASSUMPTION RFI-03: Use Table 1 duties (p.12) + Fig.6 intersections ~600 l/s design, ~800 l/s low lift (p.11) as pump-system match evidence. Reason: full Q-H-P curves not in pages.
- ASSUMPTION RFI-04: 172.4 mNGF (p.11) is representative mid-band low-water design within 85% band 172.1–173.1 mNGF (p.9). Reason: lies inside band.
- ASSUMPTION RFI-05: Compare specific energies 52.4 vs 43.5/42.6 kWh/1000m3 (p.14 vs p.12) directly as indicative. Reason: only common metric; test head/river level not given — not normalised like-for-like.
- ASSUMPTION RFI-06: Proceed with IE2 documented (p.12) and flag vs IE3/IE4 target (p.5). Reason: explicit p.12 takes precedence for these models.
- ASSUMPTION RFI-07: Apply 2.2 m/s + 5D/3D as criteria. Reason: brief + industry norm; not in pages.
- ASSUMPTION Energy tariff EUR 0.15/kWh typical French industrial for payback. Reason: no tariff in pages — REJECTED for firm conclusion per QA (see QA/QC).
- ASSUMPTION EPANET single-point curve rated 610 l/s, 11.35 m, eff 77.5% (p.12), C=120, L=120 m, minor 3.0 to reproduce design. Reason: pipe geometry not in pages; tuned — circular, illustrative only.
- ASSUMPTION Annual duty 880,000 m3/year at design-like lift. Reason: VNF advice (p.14); 85% in 172.1–173.1 mNGF (p.9) supports design-point annualisation but low-lift mix not in pages.

## Model Calibration
Single-point EPANET model tuned to Table 1 (p.12); canal reservoir 182.963 mNGF (p.8) retained only to allow run, not as recomputed head. Per QA, prior calibration circular; FIX runs are order-check only.

| Test | Measured (p.N) | Simulated (run label) | Residual | Note |
|---|---|---|---|---|
| Design-lift River 172.4 mNGF (p.11) to canal 182.963 mNGF (p.8) | 610 l/s Design CT3400/736: 610 l/s, 95.4 kW, 77.5%, 43.5 kWh/1000m3 (p.12 Table 1) | Run CAL-BASE-DES: 609.5 l/s, 11.36 m TDH, 92.2 kW electric, 1.58 m/s DN700, 42.0 kWh/ML | -0.08% flow | ASSUMPTION tuned rated head 11.35 m, L=120 m, C=120, minor 3.0, motor 0.95 to force nominal 0.6 m3/s (p.5+p.7). Specific 42.0 vs 43.5 (p.12) within 3.5%. Meaningless as independent verification — base for illustration only. Illustrative check Run FIX-DES-610: 633.7 l/s, 11.05 m TDH, 93.3 kW, 1.65 m/s, 40.9 kWh/ML — pipe L=20 m ASSUMPTION, no geometry in pages. |
| Low-lift runout River TWL 177.48 mNGF (p.8+p.11) | ~800 l/s runout (p.11); Table 1 Minimum 803 l/s, 96.2 kW, 67.3%, 33.3 kWh/1000m3, NPSHr 8.22 m (p.12) | Run CAL-BASE-MIN: 887.8 l/s, 7.12 m TDH, 84.2 kW, 2.31 m/s DN700, 146% rated warning | +10.6% flow | Single-point constant-efficiency model invalid far from BEP (holds 77.5% vs true 67.3% (p.12)). Overpredicts flow and understates specific 26.3 vs 33.3 (p.12) ~21% low. Illustrative Run FIX-MIN-ILLUS: 921.2 l/s, 6.51 m, 91.9 kW, 2.39 m/s, 151% warning — overpredicts 803 l/s (p.12); do not use sim specific 27.7, use Table 1 33.3 (p.12). Directionally confirms runout well above 600 l/s (p.5). |
| Old RATEAU ID BV 57 (p.6+p.14) | 880 l/s at 166 kW input, 99 kW hydraulic, 60%, 52.4 kWh/1000m3, 300A 380V (p.14 Table 3) | Run ALT-OLD-880: 819.6 l/s, 11.97 m TDH, 168.8 kW, 2.13 m/s DN700 | -6.86% flow, +1.7% power | Confirms baseline inefficiency vs new 77.5–78.8% (p.12). Flow residual reflects unknown test lift/head; power match validates electric model order. Not like-for-like head — rejected as normalisation. |

Additional runs logged: Run CAL-BASE-MAX at BWL 171.45 mNGF (p.8): 542.0 l/s, 87.7 kW, 1.41 m/s — shows low-flow end compliant; total swing ~540–890 l/s across ~6 m (p.8). Run ALT-VSD-080 at speed 0.80: 584.3 l/s, 6.21 m, 55.7 kW, 1.52 m/s — with manually set 67.3% (p.12), limiter illustration only, not affinity prediction. Run ALT-THROT-LOW with minor_k 18.0 ASSUMPTION: 744.1 l/s at 94.2 kW, 1.93 m/s — still passes 744 l/s vs 600 l/s target (p.5+p.7), fails to demonstrate required throttling. Run FIX-VSD08-ILLUS at 0.80: 607.6 l/s, 5.93 m, 55.3 kW, 1.58 m/s — limiter illustration only.

## Capacity Evaluation
| Unit | Limit | Binds at | Evidence (with run) | Limits target? |
|---|---|---|---|---|
| CT3400/736 at design lift | Nominal 600 l/s (p.5+p.7) at BEP ~77.5% (p.12) | Design River 172.4 mNGF (p.11) within 85% band 172.1–173.1 mNGF (p.9) | Run CAL-BASE-DES 609.5 l/s vs nominal 0.6 m3/s (p.5+p.7) and Table 1 610 l/s 77.5% 43.5 (p.12); Fig.6 ~600 l/s (p.11). Good match. | No |
| CT3400/736 at low lift / river variation | Runout + off-BEP + NPSHr rise; overshoots nominal by ~33% | Lowest lift River TWL 177.48 mNGF (p.8+p.11): ~800 l/s (p.11), Table 1 803 l/s 67.3% 33.3 NPSHr 8.22 m (p.12) | Run CAL-BASE-MIN 887.8 l/s 146% warning confirms runout; eff falls 77.5% to 67.3% (p.12); Run CAL-BASE-MAX at BWL 171.45 mNGF (p.8) 542.0 l/s 87.7 kW 1.41 m/s — swing ~540–890 l/s across ~6 m (p.8). Fixed speed cannot hold 600 l/s. | Yes |
| DN700 vertical riser | 2.2 m/s station limit — ASSUMPTION (brief/CTCG) | 600 l/s in DN700 =1.559 m/s PASS; 803 l/s (p.12) in DN700 =2.087 m/s PASS (velocity tool outputs) | Run CAL-BASE-DES 1.58 m/s, Run CAL-BASE-MAX 1.41 m/s, Run CAL-BASE-MIN 2.31 m/s in DN700 (C=120 ASSUMPTION). Riser compliant except extreme sim overprediction. | No |
| DN600 flowmeter + gate valve order | 2.2 m/s + 5D/3D — ASSUMPTION | 600 l/s in DN600 =2.122 m/s marginal; 803 l/s (p.12)=2.84 m/s FAIL; 880 l/s old (p.14)=3.112 m/s FAIL; valve directly upstream zero straights — ASSUMPTION | Run CAL-BASE-MIN 887.8 l/s equiv ~2.8–3.1 m/s in DN600; standard requires 5D/3D (ASSUMPTION). Accuracy+headloss+wear compromised at runout. | Yes |
| Motor efficiency class | IE3/IE4 target (p.5) | Catalogue IE2 only (p.12) vs target IE3 or IE4 (p.5) | p.12 explicitly no IE3 option; CT3531 pf 0.52–0.6 vs CT3400 0.8–0.82 (p.12). | Yes |
| Control / VSD justification | Intermittent static-dominated batch — VSD little annual benefit | 400 basins/year=880,000 m3/year ~408 h/year at 600 l/s (p.14); on/off via intermediate+far upstream sensors + control desk/API (p.6+p.7), 85% time 172.1–173.1 mNGF (p.9) | New 43.5 (p.12) x 880,000 (p.14)=38,280 kWh/yr; old 52.4 (p.14)=46,112 kWh/yr; saving 7,832 kWh/yr ~17% per Table 4 (p.14). Run ALT-VSD-080 55.7 kW vs fixed 96.2 kW (p.12) applies <15% hours. Document notes running costs typically low given use (p.14). | Yes — VSD not justified on energy |

## Alternatives
| Option | Run label / unit | Result | Meets target? | Cost class / basis | Recommended? |
|---|---|---|---|---|---|
| A1 Fixed-speed DOL + gate-valve throttling to cap high-river flow to ~600 l/s | Run ALT-THROT-LOW on CT3400/736 low-lift runout | ALT-THROT-LOW with minor_k 18.0 ASSUMPTION still passes 744.1 l/s at 94.2 kW, 1.93 m/s vs target 600 l/s (p.5+p.7). Wastes head, holds 122% rated warning, eff stays low, valve disturbance ruins DN600 accuracy. Proves throttling poor limiter. | No | <$100k — ASSUMPTION: uses existing automated gate valve (p.7), only logic change | No |
| A2 VSD speed-capped to ~600 l/s at high river (limiter, not saver) | Run ALT-VSD-080 on CT3400/736 low-lift | ALT-VSD-080 at 0.80 speed: 584.3 l/s, 6.21 m, 55.7 kW, 1.52 m/s DN700 vs fixed Table 1 Minimum 803 l/s, 96.2 kW, 67.3%, 33.3 (p.12). Caps velocity <2.2 m/s ASSUMPTION limit and restores accuracy, but per-volume similar and high-river hours <15% (85% in 172.1–173.1 (p.9)), so annual <1–2 MWh/yr. Not justified on energy alone. | Yes (as limiter) | $100k–$1M — ASSUMPTION: 110 kW-class LV drive + filters ~EUR 25–40k installed; no price in pages; sized for 95.4–96.2 kW input (p.12) | No (for energy) |
| A3 Alternative CT3531/806 1240 710mm 12-pole fixed speed [naming per p.11; Table 1 shows CT3500/806 (p.12) — inconsistency] | Run CAL-BASE-DES basis / CT3400 low-lift | Table 1 Design 604 l/s, 92.7 kW, 78.8%, 42.6 (p.12) and Minimum 821 l/s, 95.8 kW, 70.5%, 32.4 (p.12) vs CT3400 Design 610 l/s, 95.4 kW, 77.5%, 43.5 (p.12). Still runout ~821 l/s (p.12), same velocity fail, plus pf 0.52–0.6 vs 0.8–0.82 (p.12) increases cable/transformer burden. +1.3% eff outweighed. | No | $100k–$1M — ASSUMPTION: larger 1240 vs 830 mm frame (p.11) + civils; no price in pages | No |
| B0 Keep proposed DN700 riser + DN600 meter + valve immediately upstream (do nothing) — ASSUMPTION arrangement | Run CAL-BASE-MIN on DN600+valve | Velocity tool: 600 l/s in DN600=2.122 m/s marginally <2.2 m/s ASSUMPTION, but 803 l/s (p.12) in DN600=2.84 m/s FAIL; 880 l/s old (p.14)=3.112 m/s FAIL. Run CAL-BASE-MIN 887.8 l/s gives 2.31 m/s in DN700 confirming runout exceeds small meter. Zero straights violates 5D/3D ASSUMPTION. | No | n/a — ASSUMPTION retain as-drawn | No |
| B1 RECOMMENDED — Upsize meter to DN700 and relocate automated gate valve downstream with 5D/3D straights | Run CAL-BASE-DES on DN700+valve | Velocity tool: 600 l/s in DN700=1.559 m/s PASS; 803 l/s (p.12) in DN700=2.087 m/s PASS; Run CAL-BASE-DES 609.5 l/s gives 1.58 m/s DN700. Restores accuracy, keeps design 610 l/s (p.12) and runout ~800 l/s (p.11) compliant without throttling. | Yes | <$100k — ASSUMPTION: short spool + valve move + DN700 meter upsizing during 2020 resize (p.5); small vs pump | Yes |
| B2 If DN600 retained: enforce flow cap ~600–620 l/s via level-control trip + high-flow alarm from smart monitoring (p.5) | Run ALT-VSD-080 on DN600+valve | ALT-VSD-080 proves 584.3 l/s at 55.7 kW holds 1.52 m/s compliant; Run CAL-BASE-MAX 542.0 l/s at BWL 171.45 mNGF (p.8) at 87.7 kW 1.41 m/s shows low end compliant. Cap keeps DN600 at ~2.122 m/s at 600 l/s but sacrifices free extra flow and leaves meter disturbed. Inferior to B1. | Yes (conditionally) | <$100k — ASSUMPTION: software in control desk/API (p.7), no hardware; automation already required (p.5+p.7) | No (fallback only) |

## QA/QC Summary
- Checked citations: D01 p.5 0.6 m3/s; D02 p.6 2x RATEAU; D05–D08 p.8 levels 177.48/171.45/170.353/182.963; D11 p.9 172.1–173.1 85%; D12–D14 p.11 BWL171.45/Design172.4/TWL177.48; D19–D22 p.12 Table 1 610/803 l/s 95.4/96.2 kW 77.5/67.3% 43.5/33.3 and 604/821 l/s 92.7/95.8 kW; D25–D26 p.14 Table 3 880 l/s 300A 380V 166 kW 99 kW 60% 52.4; D28 p.14 400 basins 880,000 m3/year ~408 h — all verified by page view.
- Checked runs: Run CAL-BASE-DES rerun matches 609.5 l/s 11.36 m 92.2 kW true; Run CAL-BASE-MIN rerun matches 887.8 l/s 7.12 m 84.2 kW 146% true; Run ALT-VSD-080 rerun matches 584.3 l/s 6.21 m 55.7 kW true.
- Issues and resolution:

| Issue | Severity | Resolution |
|---|---|---|
| Base calibration Run CAL-BASE-DES tuned circular (L=120 m, C=120, minor 3.0, motor 0.95 ASSUMPTIONS, rated 11.35 m to force 609.5 l/s to Table 1 610 l/s (p.12)) | major | Fixed: replaced with Run FIX-DES-610 (633.7 l/s, 93.3 kW) labelled illustrative order-check only; pipe data flagged ASSUMPTION; adopt Arcadis curves/Table 1 (p.11,p.12) as basis. |
| Low-lift Run CAL-BASE-MIN overpredicts +10.6% (887.8 vs 803 l/s (p.11–p.12)), understates specific 26.3 vs 33.3 (p.12) ~21% low; velocity 2.31 m/s overstates tool 2.087 m/s | major | Fixed: Run FIX-MIN-ILLUS (921.2 l/s 151% warning) proves single-point invalid; use Table 1 803 l/s 67.3% 33.3 (p.12) and tool 2.087 m/s for compliance. |
| NPSH: static submergence ~1.1 m at BWL 171.45 (p.8) vs pump 170.353 (p.8) < NPSHr 4.25 m (p.12); ~7.1 m at TWL 177.48 (p.8) vs NPSHr 8.22 m (p.12) tight, but document states margin suitable (p.12) with no calc | major | Noted: suction losses/geometry unknown; target submersible monoblock (p.5); flagged as designer check, not proven failure. |
| Pipework B0/B1 rests on ASSUMPTIONS: DN700/DN600/valve-zero straights, 2.2 m/s, 5D/3D, costs <$100k/$100k–$1M, EUR0.15/kWh, EUR25–40k — none in pages; velocity arithmetic correct (2.122/2.84/3.112/1.559/2.087) but criterion unverified | major | Fixed: reframed CONDITIONAL on brief; rejected payback >20 yr and EUR1,175/yr; annual saving quoted directly Table 4 7,832 kWh (p.14) without tariff. |
| Pump naming CT3531/806 (p.11) vs CT3500/806 3-1240 (p.12 table) vs CP3531 (p.12 text) | minor | Fixed: flagged inconsistency; retain CT3400/736 as VNF proposed. |
| Annual 38,280 vs 46,112 saving 7,832 kWh/yr (880×43.5 vs 880×52.4 (p.12,p.14)) assumes all 880,000 m3 (p.14) at Design 43.5 (p.12), ignores Minimum 33.3/32.4 (p.12) and ~800 l/s (p.11) fewer hours | minor | Fixed: quote Table 4 directly (p.14) as document estimate; 85% band 172.1–173.1 (p.9) containing Design 172.4 (p.11) makes reasonable but no refined mix claimed. |
| Old vs new 52.4 vs 43.5 (p.12,p.14) not normalised (test head/river level not given); Run ALT-OLD-880 819.6 vs 880 l/s (-6.86%) confirms mismatch | minor | Noted: presented as indicative per-document (Table 4 p.14), not firm like-for-like. |
| Alternatives Run ALT-THROT-LOW minor_k=18 ASSUMPTION arbitrary; Run ALT-VSD-080 speed 0.80 manual 0.673 not affinity; valve characteristic unknown beyond automated gate valve (p.7); BWL 171.45 (p.8) left-of-BEP risk unresolved | minor | Fixed: replaced with Run FIX-VSD08-ILLUS (607.6 l/s 55.3 kW) limiter illustration only. |
| Firm capacity: 2x RATEAU duty/standby (p.6) to 1x 0.6 m3/s (p.5,p.7) leaves firm zero | minor | Fixed: added finding; unquantified. |

## Recommendations
1. **Approve CT3400/736 for nominal duty — good match at design.** Design 610 l/s at 77.5% (p.12) vs nominal 600 l/s (p.5); Fig.6 ~600 l/s at Design 172.4 mNGF (p.11) inside 85% band 172.1–173.1 mNGF (p.9). Run FIX-DES-610 633.7 l/s order-check. Proceed fixed-speed DOL; do not install VSD for energy saving.
2. **River variation — accept or limit runout, no energy payback.** Runout ~800 l/s (p.11); Table 1 Minimum 803 l/s 67.3% 33.3 NPSHr 8.22 m vs Design 77.5% NPSHr 4.25 m (p.12) across ~6 m (p.8). If hard-cap required, use VSD as limiter only (~0.80 speed to hold ~600 l/s, Run FIX-VSD08-ILLUS 607.6 l/s 55.3 kW 1.58 m/s, Run ALT-VSD-080 584.3 l/s 55.7 kW) with no payback; otherwise accept free extra flow. Batch on/off via sensors (p.6) + automation (p.5,p.7) + static dominance = VSD little annual benefit.
3. **Pipework CONDITIONAL on brief — B1.** ASSUMPTION arrangement DN700 riser, DN600 meter, valve directly upstream zero straights; ASSUMPTION limit 2.2 m/s + 5D/3D. Tool: 600 l/s DN600 2.122 m/s, 803 l/s (p.12) DN600 2.84 m/s FAIL, 880 l/s (p.14) DN600 3.112 m/s FAIL; 600 l/s DN700 1.559 m/s PASS, 803 l/s DN700 2.087 m/s PASS. Upsize meter to DN700 and relocate gate valve (p.7) downstream with 5D/3D straights. Retain DN700 riser. If DN600 retained, enforce ~600–620 l/s cap via level trip + alarm — inferior, leaves disturbance.
4. **Annual energy — expect ~38 MWh/yr new, ~7.8 MWh/yr saving.** Table 4 (p.14): 880,000 m3/year =400 basins/year ~408 h/year at 600 l/s (p.14) ×43.5 (p.12)=38,280 kWh/yr new vs 880×52.4 (p.14)=46,112 kWh/yr old, saving 7,832 kWh/yr. Old baseline Table 3: 880 l/s 166 kW 99 kW 60% 52.4 (p.14). Running costs typically low given use (p.14). Indicative only — lifts may differ.
5. **Motor + monitoring + NPSH.** Flag IE2 (p.12) vs IE3/IE4 target (p.5) non-compliance; require IE3/IE4 equivalent or derogation (prefer CT3400 pf 0.8–0.82 vs 0.52–0.6 (p.12)). Commission with smart monitoring (p.5) logging flow/power/river to verify 43.5 vs 52.4 (p.12,p.14). Designer to verify NPSHa vs 4.25/8.22 m NPSHr (p.12) given pump 170.353 vs Saone 171.45/177.48 mNGF (p.8). Note naming CT3531/806 (p.11) vs CT3500/806 (p.12) in procurement.
6. **Firm capacity / resilience.** 1×600 l/s installed, 0 l/s firm (p.5,p.7 vs 2x duty/standby (p.6)). Advise VNF: accept single point of failure or provide standby/mobile + maintenance plan. Not quantified — no data in pages.

## Limitations
- This memo uses only facts/numbers in JSON from pages [5,6,7,8,9,11,12,14]; diameters, arrangement, straights, 2.2 m/s limit, 5D/3D, pipe lengths/roughness, valve characteristics, costs, tariffs are ASSUMPTIONS per brief/industry norm as labelled — pipework verdict CONDITIONAL on brief.
- System curves adopted as given (p.11); full pump Q-H-P curves not reproduced — Table 1 two points (p.12) + Fig.6 ~600/~800 l/s (p.11) only.
- EPANET runs (CAL-BASE-DES, CAL-BASE-MIN, ALT-OLD-880, ALT-THROT-LOW, ALT-VSD-080, FIX-DES-610, FIX-MIN-ILLUS, FIX-VSD08-ILLUS, CAL-BASE-MAX) are illustrative single-point constant-efficiency checks with ASSUMPTION pipe/motor data; invalid far from BEP — do not use sim specifics off-BEP, use Table 1 33.3/32.4 (p.12).
- Old vs new specific comparison not head-normalised; annualisation at Design 43.5 (p.12) ignores lift mix; NPSHa not calculable from pages; IE/tariff/cost conclusions require designer/procurement verification.
