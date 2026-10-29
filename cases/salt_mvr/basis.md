# Vacuum-salt plant, vapour recompression evaporator: data sheet

REAL DESIGN DATA from US Patent 5,366,514 (Texas Brine Corp., 1994), FIG. I and Table I: a 2,500 short-ton-per-day
plant making 99.99 % NaCl from solution-mined brine. The P&ID was drawn by PlantAgent on that flowsheet (tags, line
numbers, valves and relief settings are ours). Equipment ratings marked ILLUSTRATIVE are not in the patent.

## Operating point (patent Table I, converted to SI)
| Stream / item | Value |
|---|---|
| Feed brine to E-101 (line 1001), saturated NaCl (~26 wt %) | 362.9 t/h at 24 °C |
| Brine leaving E-101 | 60 °C |
| Elutriating brine to the evaporator legs | 98.0 t/h at 60 °C |
| Brine through E-102 to V-201 (lines 1003/1004) | 264.9 t/h, 60 → 125.6 °C |
| V-201 VRC evaporator | 1.70 bar(a) (10 psig), brine boiling at 125.6 °C |
| V-201 overhead to K-201 (line 3001) | 226.8 t/h steam, saturation 115.2 °C at 1.70 bar(a) |
| K-201 discharge | 3.08 bar(a) (30 psig), pressure ratio 1.8 |
| Steam to E-201 after D-201 (line 3003), incl. 15.9 t/h turbine exhaust | 251.7 t/h at 135 °C, 3.08 bar(a) |
| E-201 condensate (line 4001) | 251.7 t/h at 134.4 °C, cooled in E-102 to about 82 °C |
| Excess V-201 vapour to E-301 (line 3101) | 20.9 t/h |
| Purge liquor V-201 → V-301 (line 5001) | 47.6 t/h at 125.6 °C |
| V-301 purge evaporator | about 1.01 bar(a), 108.9 °C |
| Purge to disposal well (line 5101) | 6.8 t/h at 108.9 °C |
| Purge-evaporator overheads to E-101 (line 3201) | 25.4 t/h at 100.6 °C after desuperheating |
| Salt produced (dry) | 94.9 t/h (2,511 short t/d) |

## What the patent says about the equipment
- K-201 is a single-wheel centrifugal compressor, 1.8:1, driven by a gas turbine. "The VRC compressor can only pass a
  fixed amount of steam": the vapour above its suction capacity (about 90 % of the boil-up passes it) is the excess sent
  to the purge evaporator heater E-301 (patent col. 7-8).
- Desuperheating condensate is sprayed into the compressor discharge (D-201) because superheated steam transfers heat
  poorly in the large circulating heaters (col. 7).

## Equipment ratings
- K-201 suction capacity: 226.8 t/h (the patent's fixed compressor throughput). Shaft power: not stated in the patent.
- E-201 circulating heater: 8,800 m², U 2,000 W/m²K in service (ILLUSTRATIVE; 2,500 W/m²K clean).
- P-201 forced-circulation pump: 15,000 m³/h rated (ILLUSTRATIVE).
- E-301 purge-evaporator heater: 900 m² (ILLUSTRATIVE).
- Relief: PSV-201 on V-201 set 3.5 barg, PSV-202 on D-201 set 4.5 barg, PSV-301 on V-301 set 1.0 barg (ours).

## Process requirements and design rules
- Brine temperature rise through E-201 at most 3 K: a larger rise flashes in the tubes and scales them with salt.
- Condensate leaves E-201 saturated at the shell pressure.
- The brine boils above the steam saturation temperature by its boiling point elevation (use the brine_bpe tool).

## Request
Sales wants the plant to make **3,000 short tons per day instead of 2,500 (+20 %)**.
