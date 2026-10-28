# Step 1 - Scope and design criteria

**Question:** On night of June 27 2016 during curtailment/shut-in of NGL production on A-Train, what was most likely initial failure point and damage mechanism, how did it lead to sudden rupture, and what operation/monitoring/repair/mechanical-integrity/risk-assessment changes should operator and industry adopt?

## Definitions
| term | definition | source |
|---|---|---|
| ACSR | A-Train cold side reboiler, BAHX in cryogenic area; most likely initial rupture location per DCS sequence | p.61-p.62 |
| AWSR | A-Train warm side reboiler, second BAHX in area; B-pass DP steady until 11:22-11:23 p.m. | p.61 |
| BAHX | Brazed aluminum heat exchanger: stacked layers of parting/cap sheets, side bars, fins brazed; width/height sets hydrocarbon flow capacity | p.15 |
| DCS | Distributed control system data, event log and metal/stream temperature and differential pressure sensors used with surveillance to reconstruct timeline; timestamps did not match and required shifting | p.60-p.61 |
| LOC / Internal / Interpass leak | Loss of containment to atmosphere or internal leak between passes | p.66-p.67 |
| ROC | Change per minute in inlet, outlet or metal temperature; stream ROCs much larger than metal ROCs; guidance limits in degF/min | p.32, p.37-p.38 |
| Thermal fatigue | Progressive cracking from cyclic pushing/pulling of aluminum parts due to temperature differences; also single-event thermal shock | p.16, p.34 |
| Firm capacity | Capacity with largest unit of a station out of service; not computed here, retained for later hydraulic comparison | Engineering rules |

## Criteria
| name | value | source |
|---|---|---|
| Investigation objective - initial failure point | Identify most likely initial failure point among 12-13 A-Train breaches using DCS/event log/surveillance/physical evidence sequence; explain sudden rupture on June 27 2016 during curtailment/shut-in | Task statement + p.21, p.60-p.62 |
| Investigation objective - damage mechanism | Determine damage mechanism from BAHX history, lab examination and Table 1 elimination; distinguish thermal fatigue / thermal shock from other mechanisms | p.15-p.16, p.22, p.31-p.34 |
| BAHX operation RAGAGEP - rate of change limit start-up/shutdown | ROC of no more than 3.6 degF (2 degC)/min during start-up or shutdown - Yes in all four guidances | p.32 Table 3 (ALPEMA, Chart, GPA Midstream, API 662) |
| BAHX operation RAGAGEP - normal operation ROC | 1.8 degF (1 degC)/min during normal operation per standards | p.36 (Table 3 discussion) |
| BAHX operation RAGAGEP - hourly temperature change | Total temperature change of no more than 108 degF (60 degC) in an hour - Yes for ALPEMA/Chart/GPA Midstream, No for API 662 | p.32 Table 3 |
| BAHX structural integrity criterion | Brazed fin-to-cap/parting sheet joints act as truss to hold pressurized layers; pushing/pulling from temperature differences causes thermal fatigue cracking and loss of containment; single large event can cause thermal shock | p.15-p.16 Fig.5 Fig.6 |
| Mechanical integrity / inspection criterion | PSM-covered BAHX requires inspection/maintenance (preventive and reactive); external surface examination for leaks/cracks at each HETSCO repair, grind-out and weld repair | p.43, p.66 |
| MOC / repair practice criterion | Blocking (welding closed) leaking passes and sealing/venting blocked-layer vent holes are changes requiring MOC, manufacturer approval and risk assessment; sealed holes prevent venting of interpass leak into blocked layer | p.44-p.45 |
| Risk assessment / PHA criterion for cyclic service | BAHX in service with temperature fluctuations/cycling and external curtailment upsets requires evaluation of suitability, leak-before-break basis with crack-growth calculation and in-service monitoring - not assumed safe on leak history alone | p.41 BP GP-26-10 discussion, p.33, p.40-p.42 |
| Consequence mitigation criterion | PGP emergency plan: vent to flare/atmosphere and let fire burn to minimize vapor-cloud explosion extending off property; cool equipment where feasible; unified command with Jackson County Emergency Services | p.19-p.20 |

## Standards
| name | use |
|---|---|
| ALPEMA guideline for BAHX | Construction/operation RAGAGEP; ROC and cycling guidance in Table 2/Table 3 |
| Chart (manufacturer) BAHX guideline | Construction/operation RAGAGEP; ROC and cycling guidance |
| GPA Midstream BAHX guidance | Midstream operation RAGAGEP; ROC guidance |
| API 662 (American National Standard) | Only Table 2 source generated under American National Standards process; RAGAGEP for BAHX operation |
| BP Group Practice GP-26-10 Guidance on Practice for Heat Exchangers | Owner practice on BAHX suitability, advises against BAHX in fluctuating-temperature service; considered in 2012 ACSR replacement evaluation |

## Units on the flow path
- Offshore Destin raw-gas pipeline inlet
- Slug catcher (condensate collection)
- Dehydrator + dust collector
- Warm separator (liquids to demethanizer bottom)
- Demethanizer column
- Turboexpander train (A-Train and B-Train)
- JT / expansion-valve parallel cooling path
- A-Train cold side reboiler ACSR - A-pass and B-pass core
- A-Train warm side reboiler AWSR - A-pass and B-pass core
- B-Train cold side reboiler
- B-Train warm side reboiler
- Residue-gas Destin outlet pipeline
- NGL product to storage bullets then Tri-States pipeline
- Condensate truck loading outlet
- Flare / atmospheric vent + let-it-burn response system
- DCS metal/stream temperature and differential-pressure instrumentation on ACSR/AWSR
