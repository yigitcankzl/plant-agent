# Vacuum-salt plant, vapour recompression evaporator: data sheet

REAL DESIGN DATA from US Patent 5,366,514 (Texas Brine Corp., 1994), FIG. 1 and Table I: a 2,500 short-ton-per-day
plant making 99.99 % NaCl from solution-mined brine. The drawing is the patent's FIG. 1; numbers in brackets are the
patent's reference numerals. Equipment ratings marked ILLUSTRATIVE are not in the patent.

## Operating point (patent Table I, converted to SI)
| Stream / item | Value |
|---|---|
| Feed brine to the brine cooled condenser (3) (stream 2), "saturated in salt" (about 26 wt % NaCl) | 362.9 t/h at 24 °C |
| Brine leaving the brine cooled condenser | 60 °C |
| Elutriating brine to the evaporator legs (streams 7, 8) | 98.0 t/h at 60 °C |
| Brine through the brine preheater BP (10) to the VRC evaporator (12) (streams 9/11) | 264.9 t/h, 60 → 125.6 °C |
| VRC evaporator (12) | 1.70 bar(a) (10 psig), brine boiling at 125.6 °C |
| VRC evaporator overhead to the VRC compressor (26) (stream 25) | 226.8 t/h steam, saturation 115.2 °C at 1.70 bar(a) |
| VRC compressor (26) discharge | 3.08 bar(a) (30 psig), pressure ratio 1.8 |
| Desuperheated steam to the circulating heater CH1 (stream 36), incl. 15.9 t/h turbine exhaust (stream 33) | 251.7 t/h at 135 °C, 3.08 bar(a) |
| CH1 condensate (stream 21) | 251.7 t/h at 134.4 °C, cooled in BP (10) to about 82 °C |
| Excess VRC evaporator vapour to the purge heater CH2 (stream 31) | 20.9 t/h |
| Purge liquor, VRC evaporator → purge evaporator (5) (stream 14) | 47.6 t/h at 125.6 °C |
| Purge evaporator (5) | about 1.01 bar(a), 108.9 °C |
| Purge to the disposal well facility (18) (stream 16) | 6.8 t/h at 108.9 °C |
| Purge-evaporator overheads to the brine cooled condenser (stream 4) | 25.4 t/h at 100.6 °C after desuperheating |
| Salt produced (dry) (17) | 94.9 t/h (2,511 short t/d) |

The patent describes the FIG. 1 feed as "saturated in salt". It explicitly allows lower-concentration feed; solution-mined
brine can arrive below saturation. Use `feed_x_NaCl` to examine that case rather than treating 26 wt % as universal.

## What the patent says about the equipment
- The VRC compressor (26) is a single-wheel centrifugal compressor, 1.8:1, driven by the combustion gas turbine (37). "The VRC
  compressor can only pass a fixed amount of steam": the vapour above its suction capacity (about 90 % of the boil-up passes
  it) is the excess sent to the purge evaporator heater CH2 (patent col. 7-8).
- Desuperheating condensate is sprayed into the compressor discharge because superheated steam transfers heat poorly in the
  large circulating heaters (col. 7). The desuperheater is not drawn in FIG. 1.

## Equipment ratings
- VRC compressor (26) suction capacity: 226.8 t/h (the patent's fixed compressor throughput). Shaft power: not stated in the patent.
- Circulating heater CH1: 8,800 m², U 2,000 W/m²K in service (ILLUSTRATIVE; 2,500 W/m²K clean).
- Forced-circulation pump of the VRC evaporator (not drawn in FIG. 1): 15,000 m³/h rated (ILLUSTRATIVE).
- Purge heater CH2: 1,500 m², U 1,500 W/m²K (ILLUSTRATIVE).

## Process requirements and design rules
- Brine temperature rise through CH1 at most 3 K: a larger rise flashes in the tubes and scales them with salt.
- Condensate leaves CH1 saturated at the shell pressure.
- The brine boils above the steam saturation temperature by its boiling point elevation (use the brine_bpe tool).

## Modelling scope (from the plant's process engineer)
- The capacity question is decided by the VRC loop: VRC evaporator (12) boil-up, VRC compressor (26), the discharge
  desuperheating and the circulating heater CH1, plus the purge evaporator (5) with CH2 that takes the excess vapour.
  Model that loop in detail.
- The feed preheat train (brine cooled condenser, BP) is not in question: take the brine entering the VRC evaporator from
  Table I (264.9 t/h at 125.6 °C, plus 98.0 t/h elutriating brine at 60 °C, both scaling with throughput) instead of
  closing the condensate-to-brine heat-recovery loops.
- Turbine exhaust steam joining the compressor discharge (stream 33): 15.9 t/h at 3.08 bar(a), fixed (the gas turbine does
  not grow with salt production).

## Request
Sales wants the plant to make **3,000 short tons per day instead of 2,500 (+20 %)**.
