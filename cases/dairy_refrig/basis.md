# Dairy plant ammonia refrigeration: data sheet

ILLUSTRATIVE refrigeration-plant data, written for this demonstration around a real context: a California dairy
(milk powder, butter, cream, ice cream; 385 employees; 8,760 h/yr; 47.7 GWh/yr electricity at $3.37M, i.e.
$0.0707/kWh) audited by the US DOE Industrial Assessment Center program (ITAC record SF0459). The plant
description and refrigeration numbers below are illustrative and are not that plant's measurements.

## Refrigeration system (single-stage ammonia, R-717)
| Item | Value |
|---|---|
| Refrigeration load (milk silos, cold rooms, process chilling), average | 2,400 kW |
| Evaporating temperature (suction) | -8 C, saturated vapour at the compressor inlet |
| Compressors | 3 screw compressors, 450 kW motor each, adiabatic efficiency 75 % |
| Condensing pressure today | fixed at 12.0 bar(a) all year (about 31 C) |
| Liquid leaving the condensers | saturated, about 1 K subcooled |
| Evaporative condensers | 2 units, 2,000 kW heat rejection each at 21 C wet bulb, 8 K approach (condensing temperature at least wet bulb + 8 K) |
| Lowest condensing pressure allowed (hot-gas defrost and liquid feed) | 8.6 bar(a) (about 20 C) |

## Site wet-bulb temperature (hours per year, illustrative bins for California's Central Valley)
| Wet bulb | Hours |
|---|---|
| below 5 C (use 3 C) | 1,500 |
| 5 to 10 C (use 8 C) | 2,200 |
| 10 to 15 C (use 13 C) | 2,600 |
| 15 to 20 C (use 18 C) | 2,000 |
| above 20 C (use 22 C) | 460 |

## Requirements
- N+1 on compressors: the largest compressor out must still carry the load.
- Condensers must reject compressor heat plus the refrigeration load.

## Request
1. A new ice cream line adds **700 kW** of refrigeration load (2,400 to 3,100 kW). Can the plant take it, with N+1?
2. How much electricity a year would floating head pressure save (condensing at wet bulb + 8 K, never below 8.6 bar(a))?
