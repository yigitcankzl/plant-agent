# Unit 47 product cooling and storage: operating data sheet

Illustrative operating data for the DEXPI reference P&ID "C01" (DEXPI e.V. test case). The P&ID is the industry's
reference example; the operating data below is a demonstration basis, not measurements from a real plant.

## Current operation (DCS averages, last 30 days)
| Item | Value |
|---|---|
| Product feed (line 47121, from upstream reactor) | 18.0 m3/h, 50 C, 1.5 bar(a) |
| Product composition | aqueous ethanol, 7 mol% ethanol (balance water) |
| Cooling water to H1007 (lines 47130/47131, fluid WK) | 20 m3/h, supply 25 C, 4 bar(a) |
| Chilled water to H1008 (lines 47140/47141, fluid QS) | 15 m3/h, supply 8 C, 4 bar(a) |
| P4711 differential pressure | 1.0 bar |
| P4712 differential pressure (to dispatch) | 3.5 bar |
| HV4750.01 pressure drop (open) | 0.3 bar |
| H1007 outlet to tank T4750 | 34 C |
| Product to dispatch after H1008 | 18 C |

## Process requirements
- Product entering T4750 must be at or below **35 C**: the tank is atmospheric (design 0.1 bar) and ethanol vapour
  losses and vent flammability rise above this.
- Product to dispatch (after H1008) must be at or below **20 C**.
- T4750 must give at least **60 min** residence time for quality-control hold before dispatch.

## Equipment performance and utilities
- H1007 and H1008: overall heat-transfer coefficient **600 W/m2K**, from the 2024 performance test (fouled service).
  After the last chemical clean (2019) H1007 tested at 900 W/m2K.
- H1007 plate frame accepts additional plates up to **60 m2** total area.
- Cooling-water branch to H1007 (DN80) can deliver at most **30 m3/h** at header pressure.
- Chilled-water branch to H1008 can deliver at most **20 m3/h**.
- Pump ratings are on the P&ID (P4711, P4712).

## Request
Sales wants **+20 % throughput (18.0 to 21.6 m3/h)** from next quarter.
