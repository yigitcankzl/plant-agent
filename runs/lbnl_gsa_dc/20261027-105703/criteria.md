# Step 1 - Scope and design criteria

**Question:** Energy assessment of the two seventh-floor data centers (DC 1 and DC 2) in the RAY federal building. Using the end-use estimates, UPS readings, chilled water and glycol plant observations, rack and CAU temperature monitoring and sub-floor pressure data, tell us where energy is being wasted, which measures we should implement (air management, cooling plant, pumps, electrical, lighting), and the expected savings for each (kW, kWh/yr, $/yr at about $0.07/kWh, cost and simple payback), plus the PUE we could reach.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| Assessment basis and baseline period | LBNL RAY Building Energy Usage Assessment Report April 2014; field baselining January 28-31, 2014; Table 3-4 spot readings not averages | p.25, p.11 |
| Energy cost rate for savings valuation | $0.07 per kWh | Task question statement (about $0.07/kWh) |
| Continuous operation hours | 8760 hr/yr | ASSUMPTION - data centers operate 24/7, standard for audit (reason: IT and cooling run continuously) |
| PUE definition | PUE = Total facility power / IT power; current 2.20 Poor | p.18 Table 8: EM.M.1 PUE (Total Power/IT Power) |
| HVAC effectiveness definition | IT Power divided by HVAC power; peer comparison Figs 8-9 | p.18 Table 8: EM.M.2 HVAC Effectiveness (IT Power/HVAC power) |
| ASHRAE environmental class | Class A1 data center; evaluate SAT, intake temps and rate-of-change against 2011 ranges | p.23 Table 11: 2011 ASHRAE Ranges (GSA data center considered class A1) |
| Ideal rack intake temperature target | 80 F ideal intake; current average 70 F indicates overcooling | p.20 Table: AM.M.4 Rack Intake Temperatures 70F Lower than ideal 80F |
| Temperature rate-of-change limit | 9 F limit; observed 1-2 F | p.30: ASHRAE limit of 9F |
| IT power measurement convention | Use UPS display as IT load; UPS loss from efficiency curve; PDU loss estimated | p.11: UPS display reading was assumed to be actual IT power |

## Standards
_none_

## Units on the flow path
- Utility 13.8kV service and switchgear
- Standby generator + 10kW block heater
- ATS5 (glycol dry coolers + primary pumps + other)
- ATS7 (glycol secondary pumps + other)
- ATS10 (DC1 total) + ATS11 (DC2 total)
- Chiller plant ATS feeds
- Cooling towers CT-1/CT-2/CT-3 + condenser water pumps
- Chillers 1 (1200T) /2 (1000T) /3 (1000T) /4 (400T stacked, running)
- Primary CHW pumps PCHWP + secondary CHW pumps
- Heat exchanger HX + HXWP
- CHWS/CHWR distribution to data centers
- Glycol dry coolers + primary/secondary glycol pumps
- DC1 CAUs 7-1 to 7-5 (fans 5kW + DX compressors)
- DC2 CAUs 7-6 (off) 7-7/7-8 + CAU-17/27/28 Liebert units
- Raised-floor cold plenum + perforated tiles + racks/PDUs
- UPS systems (incl 30/75/160 kVA) + PDUs PC-01/PC-05/PC-06/PC-07
- IT racks + communication racks CR1-1 to CR1-4
- Lighting 277V (4kW DC1 + 3kW DC2)
- Building automation system BAS sensors
