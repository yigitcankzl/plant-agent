# NSM-II data centre cooling, IIT Kanpur: design data and operating scenario

REAL DESIGN DATA from IIT Kanpur's public tenders: the HVAC schematic (12-AC-EE-2025, Drawing 2) and the 1000 TR
chiller plant contract documents (04-AC-EE-2025). The page numbers below refer to the contract documents.
The IT load scenario further down is ILLUSTRATIVE, written for this demonstration, and is not IIT Kanpur's actual load.

## Chiller plant (contract documents)
- 2 water-cooled screw chillers, minimum 500 TR each at duty condition (datasheet 5.15, p. 36). Total 1000 TR.
- Chilled-water flow 1200 USGPM per chiller; evaporator pressure drop at most 20 ft (p. 36).
- Condenser 1500 USGPM per chiller, 90 F in, below 100 F out; pressure drop at most 25 ft (p. 36).
- Condenser pumps 1500 GPM at 22 m, 30 kW (datasheet 5.20, p. 43).
- Cooling towers: induced draft, two cells, range 7.0 C, wet-bulb approach at most 2.77 C (p. 63).
- Efficiency: screw chillers of 300 TR and above, at most 0.61 kW/TR at ARI conditions (p. 54).

## Cooling distribution (schematic, Drawing 2)
- Chilled water at 8 C supply and 13 C return.
- 2 plate heat exchangers of 750 kW each between chilled water and the coolant distribution (CDU) loop at 15/20 C.
- 14 rear-door heat exchangers (RDHX) on chilled water, 20 gpm each, for the air-cooled racks.
- Warm-water loop at 30/38 C with a 300 kW plate heat exchanger and dry coolers of 300 kW each.
- Thermal storage tank on the chilled-water header.

## Operating scenario (ILLUSTRATIVE)
| Item | Value |
|---|---|
| Direct-liquid-cooled (DCLC) IT load on the CDU loop | 900 kW |
| Air-cooled racks on the RDHX (14 doors at 20 gpm, 8 to 13 C) | about 350 kW |
| Warm-water loop load rejected by the dry coolers | 220 kW |
| Chilled-water pumps | 2 duty, each sized for one chiller's 1200 USGPM |

## Requirements
- N+1 redundancy for chillers, plate heat exchangers and pumps: losing the largest single unit must not drop cooling.
  Each chiller is rated 500 TR = 1,758 kW of cooling; each CDU-loop plate heat exchanger 750 kW.
- Only the DCLC load on the CDU loop grows with the expansion; the RDHX and warm-water loads stay as they are.
- The CDU loop must return to 15 C supply; chilled water at 8 C supply.

## Request
The institute plans to add **8 DCLC GPU racks at 130 kW each (+1,040 kW)** on the CDU loop. Can the cooling
infrastructure take it with N+1, what limits first, and what is the cheapest fix?
