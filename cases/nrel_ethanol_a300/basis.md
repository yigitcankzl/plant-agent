# NREL 2011 cellulosic ethanol plant, Area 300: enzymatic hydrolysis and co-fermentation

Source: Humbird et al., NREL/TP-5100-47764 (May 2011), report pp. 27-31 (section 3.3, Tables 8-14) and Appendix A/E. The plant processes 2,205 dry US tons/day (2,000 dry tonnes/day) of corn stover. This area is one part of the plant; its inputs come from other areas at the flows below, and its outputs go to other areas.

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

### Design basis (report section 3.3.2, Tables 8-14)

- Neutralised, diluted hydrolysate is cooled with cooling water in H-301 and fed to the continuous high-solids hydrolysis reactor T-310 at slightly more than 20 wt % total solids; the cellulase broth is mixed in by A-308. After the enzyme, total solids are 20 wt % (10.6 % insoluble) at 48 C. 24 h in T-310, then 60 h more in the batch vessels (84 h total).
- Cellulase loading 20 mg protein / g cellulose for 90 % conversion to glucose. Enzymatic hydrolysis reactions (Table 9), fraction of glucan converted: (glucan)n -> n glucose oligomer 4.0 %; (glucan)n + 1/2 n H2O -> 1/2 n cellobiose 1.2 %; (glucan)n + n H2O -> n glucose 90.0 %; cellobiose + H2O -> 2 glucose 100 % of the cellobiose. Xylan conversion happens in pretreatment, not here.
- After hydrolysis the slurry is cooled to 32 C (H-310). 10 % of the saccharified slurry is split off to the seed train (Z. mobilis, 32 C, 24 h batches); the seed broth returns to the production fermentors.
- Contamination: 3 % of the glucose and of the xylose available for fermentation is converted to lactic acid upstream of the fermentors (Table 12): glucose -> 2 lactic acid; 3 xylose -> 5 lactic acid.
- Seed train reactions (Table 11), fraction of the sugar converted: glucose -> 2 ethanol + 2 CO2 90.0 %; glucose -> Z. mobilis cell mass 4.0 %; glucose + 2 H2O -> 2 glycerol + O2 0.4 %; glucose + 2 CO2 -> 2 succinic acid + O2 0.6 %; 3 xylose -> 5 ethanol + 5 CO2 80.0 %; xylose -> cell mass 4.0 %; 3 xylose + 5 H2O -> 5 glycerol + 2.5 O2 0.3 %; xylose + H2O -> xylitol + 0.5 O2 4.6 %; 3 xylose + 5 CO2 -> 5 succinic acid + 2.5 O2 0.9 %.
- Production co-fermentation (Tables 13-14), 32 C, 36 h, 10 vol % inoculum: glucose -> 2 ethanol + 2 CO2 95.0 %; glucose -> cell mass 2.0 %; glucose + 2 H2O -> 2 glycerol + O2 0.4 %; glucose + 2 CO2 -> 2 succinic acid + O2 0.6 %; 3 xylose -> 5 ethanol + 5 CO2 85.0 %; xylose -> cell mass 1.9 %; 3 xylose + 5 H2O -> 5 glycerol + 2.5 O2 0.3 %; xylose + H2O -> xylitol + 0.5 O2 4.6 %; 3 xylose + 5 CO2 -> 5 succinic acid + 2.5 O2 0.9 %. Arabinose follows xylose (it is inside the soluble-solids lump here and is not fermented in this model).
- The fermentor and seed vents (CO2 with entrained ethanol and water) go to the vent scrubber in Area 500; the beer (5.4 wt % ethanol) collects in the beer well T-306 together with the scrubber effluent.

### Reactions on the stand-in compounds (mass-balanced; use these coefficients)

Glucose = Tetraethylene glycol (G), xylose = Triethylene glycol (X), cellulose = PentaEthylene Glycol (C), soluble-solids lump (oligomers, other sugars) = HexaEthylene Glycol (S), insoluble lump incl. cell mass = HexaPropylene Glycol (I), lactic acid, succinic acid, xylitol and glycerol = Glycerol (they are all "other organics").

- C + 1.4696 Water -> 1.3632 G (cellulose to glucose, incl. via cellobiose); C -> 0.8440 S (to glucose oligomer)
- G -> 2.1562 Ethanol + 2.1562 Carbon dioxide; G -> 0.5300 I (cell mass); G + 2.1562 Water -> 2.1562 Glycerol + 1.0781 Oxygen; G + 2.1562 Carbon dioxide -> 2.7650 Glycerol + 1.0781 Oxygen (succinic acid); G -> 2.1092 Glycerol (lactic acid)
- X -> 1.6671 Ethanol + 1.6671 Carbon dioxide; X -> 0.4097 I (cell mass); X + 1.6671 Water -> 1.6671 Glycerol + 0.8336 Oxygen; X + 1.0003 Water -> 1.6527 Glycerol + 0.5001 Oxygen (xylitol); X + 1.6671 Carbon dioxide -> 2.1379 Glycerol + 0.8336 Oxygen (succinic acid); X -> 1.6307 Glycerol (lactic acid)


## Equipment (Appendix A)

- H-301 Hydrolysate cooler: cools the conditioned hydrolysate with cooling water to the hydrolysis temperature
- A-308 Enzyme in-line mixer: 100 hp in-line mixer; mixes the cellulase broth into the slurry
- T-310 Continuous high-solids hydrolysis reactors: 8 x 950 m3 empty towers, 24 h; then batch hydrolysis in F-300 for 60 h more (84 h total) at 48 C
- H-310 Saccharified slurry cooler: cools the saccharified slurry to 32 C for fermentation
- F-301 Seed fermentation train (F-301 to F-305): 2 trains x 5 stages, largest 757 m3; 24 h batches at 32 C; chilled water
- F-300 Production fermentors: 12 x 3,600 m3 (950,000 gal), 36 h at 32 C; 6 W/m3 agitation
- T-306 Beer well: 4 h residence time; receives the fermented broth and the vent-scrubber effluent

## Input streams (report stream tables; kg/h by stand-in compound)

- S301 Conditioned hydrolysate slurry from pretreatment (Area 200): 429,553.0 kg/h at 78.0 C and 4.3 atm (4.357 bar); Water 341,063.0, PentaEthylene Glycol 26,138.0, HexaEthylene Glycol 21,457.0, HexaPropylene Glycol 19,735.0, Triethylene glycol 16,476.0, Tetraethylene glycol 3,550.0, Acetic acid 705.0, TetraPropylene Glycol 423.0, Ethanol 6.0. Mole fractions: {"Ethanol": 7e-06, "Water": 0.980268, "Tetraethylene glycol": 0.000946, "Triethylene glycol": 0.005681, "HexaEthylene Glycol": 0.003935, "Acetic acid": 0.000608, "PentaEthylene Glycol": 0.00568, "TetraPropylene Glycol": 8.7e-05, "HexaPropylene Glycol": 0.002788}
- S422 Cellulase enzyme broth (Area 400): 13,837.0 kg/h at 29.0 C and 1.9 atm (1.925 bar); Water 13,054.0, HexaPropylene Glycol 728.0, HexaEthylene Glycol 41.0, Glycerol 13.0, Carbon dioxide 1.0. Mole fractions: {"Water": 0.996842, "HexaEthylene Glycol": 0.0002, "Glycerol": 0.000194, "Carbon dioxide": 3.1e-05, "HexaPropylene Glycol": 0.002733}
- S309 Corn steep liquor to the seed train: 211.0 kg/h at 20.0 C and 5.4 atm (5.472 bar); Water 106.0, HexaPropylene Glycol 53.0, HexaEthylene Glycol 52.0. Mole fractions: {"Water": 0.947078, "HexaEthylene Glycol": 0.029646, "HexaPropylene Glycol": 0.023276}
- S310 Diammonium phosphate to the seed train: 26.0 kg/h at 20.0 C and 1.0 atm (1.013 bar); HexaEthylene Glycol 26.0. Mole fractions: {"HexaEthylene Glycol": 1.0}
- S311 Corn steep liquor to the production fermentors: 948.0 kg/h at 20.0 C and 5.4 atm (5.472 bar); Water 476.0, HexaPropylene Glycol 237.0, HexaEthylene Glycol 235.0. Mole fractions: {"Water": 0.946991, "HexaEthylene Glycol": 0.029832, "HexaPropylene Glycol": 0.023176}
- S312 Diammonium phosphate to the production fermentors: 116.0 kg/h at 20.0 C and 1.0 atm (1.013 bar); HexaEthylene Glycol 116.0. Mole fractions: {"HexaEthylene Glycol": 1.0}
- S551 Vent-scrubber effluent returned to the beer well (Area 500): 27,198.0 kg/h at 34.0 C and 4.3 atm (4.357 bar); Water 26,743.0, Ethanol 424.0, Carbon dioxide 28.0, Acetic acid 3.0. Mole fractions: {"Ethanol": 0.006159, "Water": 0.993382, "Acetic acid": 3.3e-05, "Carbon dioxide": 0.000426}

## Streams to report

Name the model streams with these report numbers so they can be compared with the report: S302 (Hydrolysate after cooler H-301), S306 (Hydrolysate with enzyme to hydrolysis (T-310)), S303 (Saccharified slurry split to the seed train), S304 (Seed broth to the production fermentors), S305 (Seed-fermentor vent), S315 (Fermented broth from the production fermentors), S317 (Production-fermentor vent), S501 (Beer from the beer well to distillation (Area 500)).

Utilities: low-pressure steam 9.5 atm for the reboilers; cooling water at 28 C (Area 900). The report's heat duties are not given here.
