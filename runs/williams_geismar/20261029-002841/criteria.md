# Step 1 - Scope and design criteria

**Question:** On June 13, 2013, propylene fractionator Reboiler B at the Williams Geismar olefins plant ruptured about three minutes after an operations supervisor opened the hot quench water (about 187 F) to its tubes; it had been offline on standby for 16 months since maintenance in February 2012. Shell side process fluid: about 95% propane, balance mostly propylene and C4s. Reboiler B shell design: MAWP 300 psig, hydrostatic test 450 psig. Using the facility description, the schematic and the incident timeline, determine the failure mechanism and estimate with calculations the pressures that could be reached in the shell, explain why the reboiler was not protected from overpressure, and recommend the design, procedural and management changes that would prevent a recurrence.

## Definitions
| term | definition | source |
|---|---|---|
| Propylene fractionator | Distillation column in olefins process that separates reaction products into individual components; cooled furnace effluent gases go to series of distillation columns, such as the propylene fractionator, which separate the reaction products (p.7). | p.7 |
| Propylene fractionator Reboilers A/B | Shell and tube heat exchangers where tube-side hot quench water vaporizes shell-side hydrocarbon process fluid, approximately 95% propane with balance mostly propylene and C4s; report refers to mixture as 'propane' (p.9). | p.9 |
| Quench water system | Closed-loop water circulation that directly contacts heated furnace effluent gases in quench tower, sprayed downward from top; heated quench water serves as heat source in various heat exchangers heating process streams, then cooled by cooling water system before returning to quench tower (p.7). Includes quench water settler that removes most oily tar products (p.8). | p.7-8 |
| Fouling | Buildup of oily tar material that condenses into quench water and adheres to inside of process equipment such as heat exchanger tubes, resulting in decrease in both heat transfer efficiency and quench water flow rate (p.8). | p.8 |
| MAWP (Maximum Allowable Working Pressure) | Design pressure rating stamped on vessel; for Reboiler B shell provided as 300 psig in assignment brief (pending verification on pages >13, not in p.6-13). Withheld clause in p.9 relates to 2001 modification. | Task brief + p.9 [withheld] |
| Hydrostatic test pressure | Shop/field test at 1.5x MAWP per ASME; for Reboiler B shell provided as 450 psig in assignment brief (1.5x300). | Task brief (ASSUMPTION pending p.>13) |
| Standby/Offline isolated reboiler | In 2001 Williams installed valves on shell-side and tube-side reboiler piping to allow continuous operation with only one reboiler operating at a time. Other reboiler would be offline but ready for operation, isolated from process by new valves, allowing cleaning of fouled reboiler while fractionator continued to operate (p.9). Valves isolating reboilers from pressure relief valve at top of propylene fractionator were not part of original design and were installed in 2001 (p.10). | p.9-10 |
| Failure mechanism under investigation | Rapid overpressure rupture due to heating of trapped/blocked-in shell-side liquid propane by hot quench water introduced to tubes after 16-month standby with isolation valves closed, eliminating relief path. | p.7 caption 16 months, p.11 timeline 8:33 am + ~3 min to explosion |

## Criteria
| name | value | source |
|---|---|---|
| Reboiler B shell MAWP | 300 psig (provided in brief; to be verified on nameplate/U-1A) | Task brief; p.9 [withheld] - ASSUMPTION pending page >13 |
| Reboiler B shell hydrostatic test | 450 psig (1.5x MAWP, provided in brief) | Task brief - ASSUMPTION pending verification |
| Tube-side hot quench water inlet temperature to reboiler | approximately 185 F (p.9); assignment brief states about 187 F - use range 185-187 F for calculations | p.9; Task brief (conflict noted as RFI-01) |
| Shell-side propane inlet temperature during normal operation | approximately 130 F | p.9 |
| Shell-side fluid composition | approximately 95% propane with balance mostly propylene and C4s; referred to as 'propane' in report | p.9 |
| Reboiler geometry | 24 ft 8 in long end-to-end; shell ~18.5 ft long and over 5 ft diameter; 3,020 tubes per exchanger, 3/4-in diameter; six-pass exchanger | p.9 footnotes 11,13 |
| Standby duration before incident | 16 months catastrophically ruptured while offline/standby (since maintenance Feb 2012 per brief) | p.7 Fig.1 caption; Task brief |
| Incident timeline criterion | At 8:33 am operations supervisor likely opened quench water valves on offline Reboiler B as indicated by rapid increase in quench water flow rate; approximately three minutes later Reboiler B exploded | p.11 |
| Overpressure protection requirement | Shell must not exceed MAWP; original design both reboilers continuously operating with common relief at top of propylene fractionator; 2001 modification added gate valves isolating reboilers from that relief valve | p.9-10 |
| Quench water fouling performance indicator | Decrease in quench water flow rate through operating reboiler (Reboiler A) and entire circulation rate triggers troubleshooting by analyzing flow rates through pumps and heat exchangers | p.8, p.11 |

## Standards
| name | use |
|---|---|
| ASME BPVC Section VIII Division 1 | Pressure vessel design, MAWP, hydrotest, and requirement for overpressure protection by pressure relief device; to verify 300 psig MAWP / 450 psig hydrotest basis - ASSUMPTION: not cited in p.6-13 but industry standard for such exchangers |
| API STD 521 / API 520 Pressure Relief | Sizing/selection/location of relief devices including blocked-in liquid thermal expansion and heat input cases; relevant to whether reboiler shell isolated from fractionator overhead relief was protected - ASSUMPTION |
| OSHA 29 CFR 1910.119 Process Safety Management (PSM) | MOC, PHA, operating procedures, and pre-startup safety review applicable to 2001 addition of isolation valves creating trapped-liquid scenario - ASSUMPTION |
| CSB Investigation Protocol / CCPS | Failure investigation methodology for rupture mechanism and recommendations - source document is CSB Case Study No. 2013-03-I-LA Oct 2016 |

## Units on the flow path
- Cracking furnaces (ethane + propane feed) (p.7)
- Furnace effluent heat exchangers / coolers (p.7)
- Quench tower - direct contact with quench water sprayed from top (p.7)
- Quench water settler - removes most oily tar (p.8, Fig.2)
- Quench water circulation pumps (implied by flow rate analysis p.8, Fig.5/6)
- Propylene fractionator Reboilers A/B shell-and-tube exchangers - TUBE SIDE: hot quench water ~185-187 F in (p.9); SHELL SIDE: propane ~95% C3, 130 F in (p.9)
- Cooling water system that further cools quench water before return to quench tower (p.7, Fig.2)
- Distillation columns including propylene fractionator (receives reboiler vapor) (p.7, Fig.4)
- Propylene fractionator overhead pressure relief valve at top of column (added isolation gate valves in 2001 per p.10, Fig.4)
- Ethylene/propylene/butadiene/aromatics product handling + unreacted ethane/propane recycle to cracking furnaces (p.7)
- Quench water closed loop returning to quench tower (p.7)
