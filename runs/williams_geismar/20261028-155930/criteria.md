# Step 1 - Scope and design criteria

**Question:** On June 13, 2013, propylene fractionator Reboiler B at the Williams Geismar olefins plant ruptured about three minutes after an operations supervisor opened the hot quench water (about 187 F) to its tubes; it had been offline on standby for 16 months since maintenance in February 2012, when it was reportedly left filled with nitrogen behind single closed block valves on its shell-side inlet and outlet. Shell side process fluid: about 95% propane, balance mostly propylene and C4s. Reboiler B shell design: maximum allowable working pressure 300 psig, hydrostatic test 450 psig. Using the facility description, the schematic and the incident timeline, determine the failure mechanism and estimate with calculations the pressures that could be reached in the shell, explain why the reboiler was not protected from overpressure, and recommend the design, procedural and management changes that would prevent a recurrence.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| C-01 Overpressure protection path must remain open | Reboiler A/B shells protected only via fractionator overhead PRV; 2001 shell-side gate valves can isolate shell from PRV = hazard | p.9: 'If the new valves were not in the proper position (open or closed) for each phase of operation, the reboiler could be isolated from its protective pressure relief valve located on top of the propylene fractionator (Figure 4).' + p.10 Fig.4 legend 'Pressure relief valve protected propylene fractionator and shells of Reboilers A and B' |
| C-02 Operating philosophy - single-reboiler continuous operation | One reboiler in service, one offline isolated standby; firm capacity = one reboiler with largest (other) unit out of service | p.9: 'In 2001, Williams installed valves on the shell-side and tube-side reboiler piping to allow for continuous operation with only one reboiler operating at a time. The other reboiler would be offline but ready for operation (see Section 5.1), isolated from the process by the new valves.' |
| C-03 Tube-side heating medium temperature | approx 185 F quench water inlet (task brief states about 187 F - see RFI-02) | p.9: 'Quench water enters the propylene fractionator reboilers at approximately 185 degF' |
| C-04 Shell-side process fluid composition and inlet temperature | approx 95% propane, balance propylene + C4s; shell inlet approx 130 F | p.9: 'tube-side hot quench water vaporizes shell-side hydrocarbon process fluid, which is approximately 95% propane with the balance composed mostly of propylene and C4s' + 'which enters the reboiler at a temperature of approximately 130 degF' |
| C-05 Standby duration before failure | 16 months offline (Feb 2012 to June 2013 per task brief - to be verified RFI-04) | p.6: 'Reboiler B had been offline for 16 months while Reboiler A was in operation' + p.11 incident date June 13, 2013 |
| C-06 Failure timeline | Hot water admission ~08:33, rupture ~3 min later | p.11: 'at 8:33 am, the operations supervisor likely opened the quench water valves on the offline reboiler, Reboiler B' + 'Approximately three minutes later, Reboiler B exploded.' + p.12 Fig.6 caption 'Reboiler B ruptures approximately three minutes later.' |
| C-07 Shell mechanical limits - UNVERIFIED, from task brief | ASSUMPTION for scoping only: MAWP 300 psig, hydrotest 450 psig. Reason: provided in task brief; no page citation in 6-13; must verify from nameplate/dossier before any pressure calculation | Task brief (not in p.6-13): shell MAWP 300 psig, hydrostatic test 450 psig - See RFI-03 for verification |
| C-08 Fouling service duty | Quench-water-side fouling reduces flow and heat transfer; triggers nonroutine switching activity | p.8: 'some oily material remains in the quench water. Over time, some of this material adheres to and builds up on the inside of process equipment such as heat exchanger tubes, resulting in a decrease in both heat transfer efficiency and quench water flow rate. The buildup of such material is called fouling.' + p.6 fn7 |
| C-09 Consequence severity baseline | 30 ft missile throw, 3.5 h fire, >30,000 lb release - confirms catastrophic shell rupture, not tube leak | p.11: 'launched a portion of the propylene fractionator reboiler piping into a pipe rack approximately 30 feet overhead' + p.12: 'fire lasted approximately 3.5 hours, and Williams reported releasing over 30,000 pounds of flammable hydrocarbons' |

## Standards
_none_

## Units on the flow path
- Cracking furnaces (ethane/propane to ethylene/propylene) - p.7
- Quench tower (hot furnace effluent in, cooled effluent gas out top, heated quench water out bottom) - p.8 Fig.2
- Quench water settler (tars to waste) - p.8 Fig.2
- Quench water pumps - p.8 Fig.2
- Quench water distribution header to process heat exchangers (parallel bank incl. Reboilers A/B) - p.8 Fig.2
- Reboiler A shell-and-tube (EA-425A / EA-435A - tag conflict RFI-01) - tube-side quench water, shell-side propane - p.6, p.9, Fig.3/4
- Reboiler B shell-and-tube (EA-425B / EA-435B - ruptured) - 6-pass, 3020 x 3/4-in tubes, ~18.5 ft x >5 ft shell - p.9 fn11-13
- Reboiler A tube-side ball isolation valves (2001) + drain/vent - p.10 Fig.4
- Reboiler B tube-side ball isolation valves (2001) opened ~08:33 - p.10 Fig.4, p.11
- Quench water coolers (return to quench tower as cooled quench water) - p.8 Fig.2
- Propylene fractionator column (propylene/propane feed in, propylene product upper, propane recycle bottom, overhead to PRV/condenser) - p.6, p.10 Fig.4
- Reboiler A shell-side piping: liquid feed from fractionator bottom + vapor return to fractionator mid (each with 2001 gate valve) - p.10 Fig.4
- Reboiler B shell-side piping: liquid feed from fractionator bottom + vapor return to fractionator mid (each with 2001 gate valve, ASSUMED closed per RFI-06) - p.10 Fig.4
- Fractionator overhead: pressure relief valve (claimed protection for column + both shells) - p.9-p.10
- Fractionator overhead condenser + reflux drum (reflux back, propylene product out) - p.10 Fig.4
- Quench water FT/FO control loop on common header (Fig.4 bottom) - p.10 Fig.4
