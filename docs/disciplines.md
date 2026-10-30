# Engineering disciplines beyond the process simulators

Each discipline is a deterministic module with an agent tool, cited correlations, screening checks in the process-check
format (`id, check, value, limit, unit, utilisation`) and a calculation-sheet artifact (markdown + PDF). Inputs the
documents do not give are labelled ILLUSTRATIVE in the case files and on the sheet.

## Heat-exchanger detail rating (`plantagent/hxdetail.py`, tool `hx_detail`)

Libraries (installed in the main `.venv`):

| Package | Version | Installed size | Used for |
|---|---|---|---|
| `ht` (Caleb Bell, MIT) | 1.2.0 | 2.4 MB (wheel 0.8 MB) | Gnielinski / Dittus-Boelter, Bell-Delaware corrections, Zukauskas bank, Martin plate Nu, bundle sizing, F_LMTD |
| `fluids` (Caleb Bell, MIT) | 1.3.1 (already present) | — | Darcy friction (Clamond), plate geometry and Martin friction |
| `chemicals` (Caleb Bell, MIT) | 1.5.2 | 71 MB (wheel 22 MB, mostly data tables) | IAPWS-95 water/steam, IAPWS 2008 viscosity, IAPWS 2011 conductivity |

Inputs: duty, flows, temperatures and pressures from the DWSIM solve at a throughput multiple (with an answer's proposal
applied when asked); geometry from `cases/<case>/hx_geometry.json` (salt_mvr E-201, chem_c01 H1007 plate / H1008
shell-and-tube). When the model folds a heater into an evaporator body (salt_mvr V-201), the brine circulation is the flow
that carries the solved duty within the data sheet's brine-rise limit, checked against the circulation pump's rating.

Liquid properties: water IAPWS; NaCl brine Laliberté & Cooper (2004) density and Laliberté (2009) cp with the WaterTAP
parameters, Laliberté (2007) viscosity, Sharqawy et al. (2010) conductivity (extrapolated above 160 g/kg); mixtures from
DWSIM's liquid properties (`process.props` now also returns liquid viscosity, conductivity and cp).

Checks: tube/channel velocity window (salting brine minimum), area required with the correlation U vs installed, tube- and
shell-side pressure drop vs allowable, LMTD correction factor, brine circulation vs pump rating, and the model's U vs the
correlation U (flag above 20 %). A measured pressure drop on the data sheet is compared with the calculated one as a
geometry-consistency note.

## Combustion and fired equipment (`plantagent/combustion.py`, tool `combustion_check`)

| Package | Version | Installed size | Used for |
|---|---|---|---|
| `cantera` | 3.2.0 | 16 MB (wheel 19 MB) + `ruamel.yaml` 0.19.1 | GRI-Mech 3.0 thermochemistry: heating values, HP equilibrium (adiabatic flame temperature, equilibrium NO), complete-combustion products, isothermal post-flame NO kinetics |

Burner screening: heating values, stoichiometric air, excess air or flue O2, adiabatic flame temperature, flue-gas
composition and flow, water dew point, efficiency by the ASME PTC 4 energy-balance (stack-loss) method simplified
(25 °C reference, ABMA standard air humidity 0.013 kg/kg), equilibrium NO and thermal NO formed in a stated residence
time at the flame temperature. NOx numbers are screening tendencies for comparing cases, not emission guarantees.

Gas turbine + HRSG (`cases/salt_mvr/combustion.json`, US 5,366,514 Table I: 112.28 MMBtu/h natural gas, 35,000 lb/h of
600 psig / 820 °F steam): the turbine exhaust closes an energy balance on the fuel and the DWSIM K-201 shaft power (the
exhaust temperature is ILLUSTRATIVE), the HRSG sections are calibrated (UA) at the documented steam rate, off-design
steam and stack temperature use the calibrated UA scaled by (gas flow ratio)^0.6, and a steam target solves the duct
firing it needs. The patent HRSG is unfired, so any supplementary firing is flagged as a modification.
