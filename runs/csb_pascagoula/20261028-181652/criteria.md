# Step 1 - Scope and design criteria

**Question:** On the night of June 27, 2016, while operators were curtailing and then shutting in NGL production on A-Train, a sudden explosion and fire destroyed much of the A-Train cryogenic area of the Pascagoula gas plant; 13 pieces of piping and equipment ruptured. Using the timeline, DCS data, physical evidence, the plant's brazed aluminum heat exchanger (BAHX) operating and repair history and the industry guidance, identify the most likely initial failure point and damage mechanism, explain how it led to a sudden rupture on that night, and recommend what the operator and industry should change (operation, monitoring, repair practice, mechanical integrity / risk assessment) to prevent a repeat.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| BAHX rate-of-change limit - start-up / shutdown | ROC no more than 3.6 degF (2 degC)/min during start-up or shutdown | p.32 Table 3 - ALPEMA / Chart / GPA Midstream / API 662 guidance |
| BAHX rate-of-change limit - normal operation | 1.8 degF (1 degC)/min during normal operation | p.36 - standards summary; p.32 Table 3 |
| BAHX total temperature change limit | Total temperature change no more than 108 degF (60 degC) in an hour | p.32 Table 3 - ALPEMA / Chart / GPA guidance (API 662 No) |
| BAHX cyclic operation suitability | Advise against using BAHXs in service that experiences fluctuations in temperature / thermal cycling | p.41 - BP Group Practice GP-26-10 Guidance on Practice for Heat Exchangers |
| PSM coverage | PGP is PSM-covered; requires PHA, operating procedures, MOC, mechanical integrity, incident investigation | p.12 - OSHA 29 CFR 1910.119 |
| RMP coverage | PGP is RMP-covered; requires hazard review and release prevention | p.12 - EPA 40 CFR 68 |
| Emergency response philosophy | Vent fuel to flare or vent to atmosphere and let fire burn to minimize vapor-cloud explosion extending offsite | p.19 - PGP emergency response plan |
| Leak-before-break (LBB) use conditions | LBB only valid if crack growth rate low, leaking fluid not above auto-ignition / dangerous condition, in-service monitoring to detect leaks, and engineering calculation that leaking crack size < critical crack size | p.46 - LBB methodology discussion |
| BAHX structural integrity criterion | Fins and braze joints must hold layers together against fluid pressure; loss of braze / fatigue crack = loss of containment integrity | p.15 Fig.5 discussion - brazed fin to cap/parting sheet joints act as truss |

## Standards
_none_

## Units on the flow path
- Offshore feed - Destin pipeline (raw gas from Gulf of Mexico deepwater)
- Slug catcher (condensate collection; condensate trucked offsite)
- Dehydrator + dust collector (water/particulate removal)
- Warm separator (liquids to demethanizer bottom; vapor splits to 3 streams)
- Turboexpander (refrigeration to about -90 degF) + parallel JT/expander paths
- Cold separator
- Demethanizer column (cryogenic fractionation)
- A-Train cold side reboiler ACSR - BAHX (suspected initial failure point)
- A-Train warm side reboiler AWSR - BAHX
- B-Train cold side + warm side reboilers - BAHXs (sister units)
- NGL product - onsite storage bullets (limited surge) -> Tri-States pipeline (curtailed downstream cause)
- Residue gas (methane) -> Destin pipeline
- Flare / atmospheric vent (emergency fuel venting; let-burn philosophy)
