# NREL 2011 ethanol plant: interim status (2026-11-01)

Source: Humbird et al. 2011, NREL/TP-5100-47764. Stream tables of Appendix E extracted by `tools/nrel_tables.py`: 154 of 155
streams parsed; 150 close their mass balance within 0.2 %.

## Feasibility per area (DWSIM)
| Area | Verdict | Why |
|---|---|---|
| A100 feed handling | not simulated | solids conveying only, no process change |
| A200 pretreatment | feasible, simplified | xylan/cellulose stand-ins with mass-balanced reactions; flash and ammonia conditioning |
| A300 hydrolysis + fermentation | **built** | fixed-conversion reactors, stand-in stoichiometry (Tables 9-14) |
| A400 enzyme production | feasible, simplified | aerobic conversion reactor |
| A500 distillation + dehydration | in progress | rigorous columns converge only with CO2 taken off upstream and the beer column modelled from the side-draw tray down |
| A600 wastewater | feasible, simplified | anaerobic/aerobic conversion of the organic lumps |
| A700 storage | trivial | |
| A800 boiler/turbogenerator | not feasible in DWSIM | solid lignin combustion; Cantera could do the gas side |
| A900 utilities | partial | cooling water and chilled water loads only |

## Engine changes
- Rigorous column: several feeds, vapour/liquid side draws, Murphree efficiency, partial-condenser vapour rate, solver method.
- Column products report their compound split (DWSIM leaves compound flows empty there).
- The DWSIM worker no longer crashes on compound pairs without NRTL data (auto-estimation needs IPOPT, not shipped).
- Plant cases can list `areas`; the plant model is their deterministic join (forward streams joined, recycles torn).

## Compounds
DWSIM's own sugars stall its column solver and furfural's liquid-liquid split does too, so ChemSep glycols stand in for
sugars, polymers and solids (mass for mass), acetic acid for furfural. Reactions are scaled by molar mass.

## Match against the withheld stream tables
- A300 (Muse Wonder, $4.30, 463 s): 8 streams, 35 checks: 26 within 3 %, 33 within 5 %. Beer S501 ethanol 21,229 vs
  21,941 kg/h (-3.2 %).
- A500: first build failed after 16 column-convergence trials and an API connection error ($1.78); rebuilding.

## Spend
$6.08 of this task's $30 (main ledger $34.25).
