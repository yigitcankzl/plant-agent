# NREL 2011 cellulosic ethanol plant, Area 500: product, solids and water recovery (distillation, dehydration, separation)

Source: Humbird et al., NREL/TP-5100-47764 (May 2011), report pp. 44-46 (section 3.5) and Appendix A/E. The plant processes 2,205 dry US tons/day (2,000 dry tonnes/day) of corn stover. This area is one part of the plant; its inputs come from other areas at the flows below, and its outputs go to other areas.

## Compounds (DWSIM stand-ins)

DWSIM's databank has no biomass polymers or lumped solids, so the report's components are represented by these compounds (by mass):

- Ethanol, Water, CO2, O2, N2, Ammonia, Methane, Acetic acid: themselves
- Furfurals (furfural + HMF): Acetic acid (furfural-water is partly immiscible; its liquid-liquid split stalls the column solver)
- Other Organics (glycerol, succinic acid, ...): Glycerol
- Glucose: Tetraethylene glycol
- Xylose: Triethylene glycol
- Cellulose: PentaEthylene Glycol
- Xylan: TetraPropylene Glycol
- Soluble solids lumps: other sugars, sugar oligomers, organic and inorganic soluble solids, sulfuric acid: HexaEthylene Glycol
- Insoluble solids lumps: lignin, protein, cell mass, acetate, other structural carbohydrates, other insolubles: HexaPropylene Glycol

Every stand-in carries the report component's MASS (1 kg of glucose is 1 kg of Tetraethylene glycol). The glycols are non-volatile and water-miscible, like the sugars and solids they replace (DWSIM's own sugar compounds stall its rigorous column solver). A reaction on a stand-in keeps its mass balance by scaling the coefficients with molar mass, e.g. glucose -> 2 ethanol + 2 CO2 becomes 1 Tetraethylene glycol -> 2.1562 Ethanol + 2.1562 Carbon dioxide. Missing NRTL pairs are treated as ideal.

Use these DWSIM compound names (only those present in the area's streams are needed): Acetic acid, Ammonia, Carbon dioxide, Ethanol, Glycerol, HexaEthylene Glycol, HexaPropylene Glycol, Nitrogen, Oxygen, PentaEthylene Glycol, TetraPropylene Glycol, Tetraethylene glycol, Triethylene glycol, Water. Use the NRTL property package (ethanol-water). Stream ids are the report's stream numbers prefixed with S (e.g. S501).

### Design basis (report section 3.5.2, design basis text)

- Beer from fermentation (5.4 wt % ethanol) is fed to the beer column D-501 after an economizing exchanger H-512 against the beer column bottoms. The bottoms are cooled to 47 C in that economizer (a suitable temperature for liquid-solid separation).
- D-501 removes the CO2 and as little ethanol as possible to the overhead while removing about 90 % of the water to the bottoms. The ethanol leaves as a vapour side draw and is fed directly to the rectification column D-502. Both columns are modelled in the report with rigorous VLE (Aspen RADFRAC).
- D-501: 32 stages at 48 % efficiency; feed on the fourth tray from the top; molar reflux ratio 3:1; overhead vented to the scrubber (about 85 % CO2, 11 % ethanol and close to 4 % water); all of the CO2 and only 0.3 % of the feed ethanol go overhead; about 0.8 % of the feed ethanol is lost in the bottoms; more than 99 % of the feed ethanol leaves as the vapour side draw at tray 8, at 40 wt % ethanol. Overhead pressure 2 atm (15 psig). Reboiler H-501 uses low-pressure steam at 9.5 atm (125 psig).
- D-502: 45 stages at 76 % efficiency; the D-501 vapour enters on tray 33 counting from the top; the molecular-sieve recycle (72 wt % ethanol) enters on tray 14; molar reflux ratio 3.5:1 to obtain an overhead vapour of 92.5 % w/w ethanol and bottoms of 0.05 % w/w ethanol. The overhead leaves as saturated vapour at about 1.6 atm (PFD-P120-A502/A503 operating pressure). The bottoms are recycled to pretreatment as dilution water.
- Vent scrubber T-512: the beer column overhead and the seed and production fermentor vents are scrubbed with water; it recovers 99 % of the vented ethanol; the effluent (about 1.8 wt % ethanol) returns to the beer well.
- Molecular sieve M-503: the saturated D-502 overhead vapour is superheated and fed to one of two adsorption columns, which removes 95 % of the water and a small amount of ethanol; the 99.5 % ethanol vapour is cooled against the regeneration condensate and finally condensed with cooling water and pumped to storage. Regeneration: a slipstream of pure ethanol vapour strips the water off under vacuum; the mixture (about 70-72 wt % ethanol) is condensed and returned to D-502.
- Pressure filter S-505: operated without a wash; the cake is dried with air to 35 % moisture; the drying air goes to the combustor and the pressed stillage water to wastewater treatment.

### Modelling notes (solver limits found by PlantAgent's engine tests on this case, not from the report)

- DWSIM's rigorous column does not converge with CO2 or O2 in it: take the dissolved CO2 off the preheated beer ahead of D-501 (flash or component_separator) and send it with the D-501 vent to T-512.
- D-501's vapour side draw carries more vapour than leaves the top, which the column solver does not converge: model D-501 from the side-draw tray down, with a partial condenser whose vapour product (vapor_mol_s) is the side draw S510, and a small reflux ratio.
- D-502 with a partial condenser and almost no liquid distillate does not converge: use a total condenser and let H-503 vaporise and superheat the overhead before the sieve; report the condenser duty with that caveat.
- T-512 (absorber with CO2) and M-503 (adsorption) are fixed-split separations here (component_separator) at the documented recoveries.
- Every equipment item on the P&ID must appear as a unit with its tag.


## Equipment (Appendix A)

- H-512 Beer column feed interchanger: plate & frame; beer (cold) against beer column bottoms (hot)
- D-501 Beer column: 32 fixed-valve trays, 24 in spacing, 14 ft diameter (4.27 m), 76 ft tall; reboiler H-501 (LP steam 9.5 atm), condenser H-504
- T-512 Vent scrubber: water scrubber for the beer column and fermentation vents; inlet gas 9,681 acfm at 91 F
- D-502 Rectification column: 45 valve trays; top section 13 ft (3.96 m) diameter, bottom 4.5 ft (1.37 m) below tray 15; thermosiphon reboiler H-502; air-cooled condenser H-505 (92.2 MMBtu/h, 3 cells)
- H-503 Sieve feed superheater: superheats the D-502 overhead vapour before the sieve
- M-503 Molecular sieve adsorption package: two adsorption columns, vapour phase; removes 95 % of the water
- H-506 Product / regeneration condensate interchanger: cools the dry ethanol vapour against the regeneration condensate
- H-509 Product condenser: condenses and cools the ethanol product with cooling water
- H-507 Regeneration condenser: condenses the regeneration vapour under vacuum
- S-505 Pressure filter (lignin separator): 2 Larox FFP 2512 units, 384 m2 filtration area each; no wash; cake air-dried to 35 % moisture

## Input streams (report stream tables; kg/h by stand-in compound)

- S501 Beer from the beer well (fermentation, Area 300; includes the vent-scrubber effluent): 450,741.0 kg/h at 32.0 C and 6.0 atm (6.079 bar); Water 378,525.0, HexaEthylene Glycol 22,818.0, Ethanol 21,941.0, HexaPropylene Glycol 21,541.0, Glycerol 1,400.0, PentaEthylene Glycol 1,255.0, Triethylene glycol 1,062.0, Acetic acid 706.0, Carbon dioxide 549.0, Tetraethylene glycol 521.0, TetraPropylene Glycol 423.0. Mole fractions: {"Ethanol": 0.021964, "Water": 0.969009, "Tetraethylene glycol": 0.000124, "Triethylene glycol": 0.000326, "HexaEthylene Glycol": 0.003727, "Acetic acid": 0.000542, "Glycerol": 0.000701, "Carbon dioxide": 0.000575, "PentaEthylene Glycol": 0.000243, "TetraPropylene Glycol": 7.8e-05, "HexaPropylene Glycol": 0.002711}
- S305 Seed-fermentor vent (Area 300): 1,969.0 kg/h at 32.0 C and 1.0 atm (1.013 bar); Carbon dioxide 1,882.0, Water 38.0, Ethanol 32.0, Oxygen 17.0. Mole fractions: {"Ethanol": 0.015068, "Water": 0.045758, "Carbon dioxide": 0.92765, "Oxygen": 0.011525}
- S317 Production-fermentor vent (Area 300): 19,180.0 kg/h at 32.0 C and 1.0 atm (1.013 bar); Carbon dioxide 18,323.0, Water 369.0, Ethanol 331.0, Oxygen 155.0, Acetic acid 2.0. Mole fractions: {"Ethanol": 0.016006, "Water": 0.045631, "Acetic acid": 7.4e-05, "Carbon dioxide": 0.927498, "Oxygen": 0.010791}
- S524 Fresh scrubber water: 26,836.0 kg/h at 33.0 C and 5.0 atm (5.066 bar); Water 26,836.0. Mole fractions: {"Water": 1.0}
- S559 Pressure-filter drying air (from compressor M-507): 12,105.0 kg/h at 80.0 C and 6.9 atm (6.991 bar); Nitrogen 9,104.0, Oxygen 2,764.0, Water 237.0. Mole fractions: {"Water": 0.03099, "Oxygen": 0.203474, "Nitrogen": 0.765536}

## Streams to report

Name the model streams with these report numbers so they can be compared with the report: S508 (Beer column bottoms after the economizer), S509 (Beer column overhead vent to the scrubber), S510 (Beer column vapour side draw to D-502), S511 (D-502 overhead vapour), S514 (Dehydrated ethanol vapour), S512 (Molecular sieve regeneration vapour), S515 (Ethanol product to storage (Area 700)), S516 (D-502 bottoms, recycled to pretreatment (Area 200)), S521 (Regeneration condensate recycled to D-502), S535 (Pressed stillage water to wastewater treatment (Area 600)), S571 (Lignin wet cake to the combustor (Area 800)), S550 (Scrubber vent to atmosphere), S551 (Scrubber effluent returned to the beer well (Area 300)), S560 (Spent drying air to the combustor (Area 800)), S506 (Preheated beer to D-501), S507 (Beer column bottoms), S519 (Ethanol product vapour after H-506), S517 (Regeneration condensate), S511A (Superheated sieve feed), S523 (Combined vents to the scrubber).

Utilities: low-pressure steam 9.5 atm for the reboilers; cooling water at 28 C (Area 900). The report's heat duties are not given here.
