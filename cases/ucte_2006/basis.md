# 4 November 2006, Landesbergen area (E.ON Netz / RWE TSO), 380/220 kV: data sheet

Source of the event data: UCTE Final Report, System Disturbance on 4 November 2006 (30 January 2007), https://eepublicdownloads.entsoe.eu/clean-documents/pre2015/publications/ce/otherreports/Final-Report-20070130.pdf. Page numbers are the report's PDF pages. The reduced network below is a
PlantAgent reconstruction (RECONSTRUCTED): substation positions from public maps, line length = straight-line distance x 1.1,
typical per-km parameters. The report gives no impedances. Anything not from the report is marked RECONSTRUCTED.

## Situation at 22:00

- At 21:38 and 21:39 E.ON Netz switched off both circuits of the 380 kV line Conneforde - Diele (at the request of the Meyer Werft shipyard,
  for the ship "Norwegian Pearl" to pass down the river Ems; report p.18). The flow on the 380 kV tie line Landesbergen - Wehrendorf rose by over 600 MW to about
  1,200 MW (report p.19-20, Fig. 3).
- The 380 kV Landesbergen substation is operated with two separated busbars (A and B), its normal configuration, to keep
  the short-circuit current within the switchgear rating (report p.15). The bus coupler is open.
- The 380 kV Borken substation is split in two parts for construction work (report p.15). Not in the reduced model.
- Flows at the Landesbergen substation at 22:00, busbar by busbar (report p.50, Fig. 30), MW, sign = into the busbar:

| Busbar | Element | Flow at 22:00 (MW) |
|---|---|---|
| A | LAN-DOL 1 (from Dollern) | +843 |
| A | LAN TA (from the 220 kV side) | +219 |
| A | LAN-GRO 1 (from Grohnde) | +394 |
| A | LAN-WEH (to Wehrendorf) | -1,225 |
| A | LAN-OVE 1 (to Ovenstädt) | -233 |
| B | LAN-DOL 2 (from Dollern) | +721 |
| B | LAN TB (from the 220 kV side) | +196 |
| B | LAN-GRO 2 (from Grohnde) | +113 |
| B | LAN-OVE 2 (to Ovenstädt) | -1,032 |

- Between 22:02 and 22:09 the flow on Landesbergen - Wehrendorf rose gradually by about 130 MW, to about 1,375 MW just
  before 22:10 (report p.20 Fig. 3 and p.49: German-Dutch exchange variation and three units in the E.ON Netz grid).
  Between 22:05 and 22:07 the current exceeded RWE TSO's 1,795 A warning value (report p.19).

## Protection settings on Landesbergen - Wehrendorf (report p.19, Table 1)

| | E.ON Netz end (Landesbergen) | RWE TSO end (Wehrendorf) |
|---|---|---|
| Thermal capacity | 2,000 A | 2,000 A |
| Warning (alarm) | 1,000 A and 2,000 A | 1,795 A |
| Maximum accepted | 2,550 A for at most 1 h | 1,995 A |
| Tripping current | 3,000 A | 2,100 A |

The line trips at the lower of the two ends' tripping currents. The 220 kV line Bielefeld/Ost - Spexard is electrically
interdependent with it: if the 380 kV tie trips, the 220 kV line cannot carry the load (report p.49 footnote 16).

## Reduced network (RECONSTRUCTED)

Buses: LAN_A and LAN_B (Landesbergen 380 kV busbars A and B), bus coupler `LAN coupler` between them (open at 22:00);
WEH, OVE, DOL, GRO, BEC, ELS, TWI, GUT (380 kV, WEH = Wehrendorf, OVE = Ovenstädt, DOL = Dollern, GRO = Grohnde, BEC = Bechterdissen, ELS = Elsen, TWI = Twistetal, GUT = Gütersloh);
LAN220, BIO220 (Bielefeld/Ost), SPX220 (Spexard) at 220 kV; SOUTH_E (E.ON grid further south) and SOUTH_W (RWE grid
further south-west) are grid equivalents.

Lines (380 kV per circuit: r 0.03 ohm/km, x 0.26 ohm/km, c 13 nF/km, thermal 2000 A;
220 kV: r 0.08, x 0.32, c 11, thermal 1000 A; typical quad/twin-bundle values, RECONSTRUCTED):

| id | from | to | length km | circuits | kV | note |
|---|---|---|---|---|---|---|
| LAN-WEH | LAN_A | WEH | 67.9 | 1 | 380 | tie line E.ON Netz - RWE TSO |
| LAN-OVE 1 | LAN_A | OVE | 23.8 | 1 | 380 | circuit on busbar A |
| LAN-OVE 2 | LAN_B | OVE | 23.8 | 1 | 380 | circuit on busbar B |
| LAN-DOL 1 | LAN_A | DOL | 123.8 | 1 | 380 | circuit on busbar A |
| LAN-DOL 2 | LAN_B | DOL | 123.8 | 1 | 380 | circuit on busbar B |
| LAN-GRO 1 | LAN_A | GRO | 67.2 | 1 | 380 | circuit on busbar A |
| LAN-GRO 2 | LAN_B | GRO | 67.2 | 1 | 380 | circuit on busbar B |
| OVE-BEC | OVE | BEC | 55.8 | 2 | 380 | E.ON corridor south |
| BEC-ELS | BEC | ELS | 33.2 | 2 | 380 | E.ON corridor south |
| ELS-TWI | ELS | TWI | 54 | 2 | 380 | E.ON corridor south |
| TWI-SOUTH_E | TWI | SOUTH_E | 100 | 2 | 380 | equivalent of the E.ON grid further south |
| WEH-GUT | WEH | GUT | 51.5 | 2 | 380 | RWE TSO |
| GUT-SOUTH_W | GUT | SOUTH_W | 100 | 2 | 380 | equivalent of the RWE grid further south-west |
| BIO-SPX 220 | BIO220 | SPX220 | 20 | 1 | 220 | 220 kV Bielefeld/Ost - Spexard, parallel to the tie |

Transformers 380/220 kV, 600 MVA, uk 12 %, ukr 0.3 % (RECONSTRUCTED):

| id | 380 kV bus | 220 kV bus |
|---|---|---|
| LAN TA | LAN_A | LAN220 |
| LAN TB | LAN_B | LAN220 |
| BEC T | BEC | BIO220 |
| GUT T | GUT | SPX220 |

Injections at 22:00 (report Fig. 30 totals): north through Dollern 1,564 MW (gen at DOL), Grohnde 507 MW (gen at GRO),
Landesbergen 220 kV side 415 MW (gen at LAN220); generator voltage set points 1.05 pu (about 400 kV, RECONSTRUCTED).
Grid equivalents SOUTH_E (reference, 1.05 pu, 0 degrees) and SOUTH_W (1.05 pu). UNKNOWN: the voltage angle of SOUTH_W
relative to SOUTH_E, which stands for the north-east to south-west transit through both control areas. It is the one
quantity to calibrate: the Landesbergen - Wehrendorf flow at 22:00 is 1,225 MW. The flow just before 22:10 (about
1,375 MW) is reached with a larger transit (scale or angle).

## Operating request at 22:08

RWE TSO asked E.ON Netz for urgent intervention to bring the Landesbergen - Wehrendorf current back to a safe value
(report p.19). E.ON Netz dispatchers propose to couple the two busbars in Landesbergen (close `LAN coupler`). They expect
the current on Landesbergen - Wehrendorf to fall by about 80 A (report p.19). No load-flow calculation has been made.
