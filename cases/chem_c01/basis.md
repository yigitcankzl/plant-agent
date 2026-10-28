# Unit 47 product cooling and storage: operating data sheet

ILLUSTRATIVE DATA. The P&ID is the DEXPI e.V. reference example C01. The operating data and site datasheets below are a
demonstration basis written for it, not measurements from a real plant.

## How the unit runs (operations description)
Product from the upstream reactor (line 47121) is pumped by P4711 through plate cooler H1007 (cooling water, lines
47130/47131) into the atmospheric storage tank T4750 via HV4750.01. Reciprocating pump P4712 takes suction from T4750 and
discharges to dispatch (line 47126, off-page). Part of its discharge recirculates through tubular cooler H1008 (chilled
water, lines 47140/47141) and back-pressure valve PV4712.02 (line 47127) to the tank, which holds the tank temperature;
TICSA 4750.03 throttles the chilled-water outlet valve. PSV 47125 relieves P4712's discharge back to the tank.

## Current operation (DCS averages, last 30 days)
| Item | Value |
|---|---|
| Product feed (line 47121) | 18.0 m3/h, 50 C, 1.5 bar(a); aqueous ethanol, 7 mol% ethanol |
| P4711 differential pressure | 1.0 bar |
| H1007 product outlet to T4750 | 34.0 C |
| Cooling water to H1007 (fluid WK) | 20 m3/h, supply 25 C, return 37.7 C, 4 bar(a) |
| H1007 pressure drop, cooling-water side | 0.5 bar at 20 m3/h (product side 0.3 bar at 18 m3/h) |
| T4750 level | 80 % (working volume 20.8 m3), pressure atmospheric |
| T4750 temperature (= product to dispatch) | 23.6 C |
| P4712 total discharge flow (stroke setting) | 40 m3/h; differential pressure 3.5 bar |
| Recirculation through H1008 and PV4712.02 (line 47127) | 22.5 m3/h; PV4712.02 drop 2.5 bar |
| Chilled water to H1008 (fluid QS) | 15 m3/h, supply 7 C, return 18.0 C, 4 bar(a) |

## Process requirements
- Product entering T4750 at or below **35 C** (atmospheric tank; ethanol vapour losses and vent flammability).
- Product to dispatch (tank temperature) at or below **25 C**.
- At least **60 min** hold time in T4750 on the dispatch flow, for quality control.

## Site datasheets (these supersede the P&ID attributes where they differ)
- P4711 (centrifugal): rated 25 m3/h at 12 m, motor 2.2 kW, minimum continuous flow 8 m3/h, NPSHr 2.5 m.
  (The P&ID attributes 200 m3/h / 60 kW are from the original template and are wrong.)
- P4712 (reciprocating): maximum stroke 50 m3/h, motor 7.5 kW; PSV 47125 set 6 barg (P&ID).
- T4750: 26 m3 nominal; maximum operating level 85 % (22.1 m3), high-level alarm 90 %.
- H1007 and H1008: overall heat-transfer coefficient **600 W/m2K** at the current flows (2024 performance test, fouled).
  H1007 tested at **900 W/m2K** after its last chemical clean (2019); a clean takes one 12-hour shutdown.
- H1007 plate frame accepts plates up to **60 m2** total area.
- Cooling-water branch to H1007: at most **30 m3/h**, with **1.0 bar** available pressure drop across H1007.
- Chilled-water branch to H1008: at most **20 m3/h**.
- Plan no utility above 90 % of its stated supply.

## Request
Sales wants **+20 % throughput (18.0 to 21.6 m3/h)** from next quarter.
