# Step 1 - Scope and design criteria

**Question:** After a rupture, Goochland County will replace the first 2.5 miles (about 10,755 ft) of the 48-inch FRP force main from the Eastern Goochland Pump Station (EGPS) with 42-inch IPS DR-21 HDPE (37.76-inch ID); the rest of the FRP and the ductile iron stay. With the smaller pipe, can EGPS still meet the current required capacity (14.1 MGD with 2 duty pumps) and the 2045 requirement (27.1 MGD with 5 duty pumps) for every operating mode: pumping to the Richmond outfall, to the Henrico outfall, and to Henrico while Gambles Mill Pump Station also pumps? What flows, heads, steady pressures and velocities result? Then check a pump-station power failure with all duty pumps running: do transient pressures stay within the allowable surge pressures of the HDPE and the remaining FRP and DI, now and as the station grows to 3, 4 and 5 duty pumps? Recommend what the County should do.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| C-CAP-NOW — current required EGPS capacity | 14.06 MGD total (≈14.1 MGD in task) = 1.06 MGD Goochland peak-hour + 13.0 MGD Henrico peak-hour; to be met with 2 duty pumps | p.31 Table 3-3 |
| C-CAP-2045 — 2045 required EGPS capacity | 27.09 MGD total (≈27.1 MGD in task) = 14.09 MGD Goochland peak-hour + 13.0 MGD Henrico peak-hour; to be met with 5 duty pumps | p.31 Table 3-3 |
| C-MODES — operating modes to check for every pump count | To Richmond outfall with Gambles Mill inactive; to Henrico outfall with Gambles Mill inactive; to Henrico outfall with Gambles Mill active | p.31 Table 3-4 and p.41 Table 3-9 |
| C-PUMP-COUNT — duty pumps by planning horizon | Now S1/S3 = 2 duty; future S2/S4 = 5 duty; intermediate transient growth = 3 and 4 duty | p.31 Table 3-4 (steady S1=2, S2=5) and p.41 Table 3-9 (transient S3=2, S4=5); task adds 3 and 4 for transient growth check |
| C-FIRM — firm-capacity definition | Firm capacity is the station flow with the largest duty unit out of service; 2-duty firm means 1 pump out, 5-duty firm means 1 of 5 out | Task instruction (Engineering rules: Firm capacity = capacity with largest unit out of service) |
| C-STEADY-R — steady-state roughness | Hazen-Williams C = 120 for all EGFM pipes (FRP, MJ DI, HDPE) in steady-state analysis | p.29 Table 3-1 |
| C-TRANS-R — transient roughness (worst-case) | Hazen-Williams C = 150 for all pipes in transient analysis because high C enables higher velocities (worst case); PPI PE 150-155, FRP tested 150-160, DIPRA cement-lined DI up to 150-157, practice DI 110-150 | p.38 para 2 |
| C-TRIP — worst-case transient event | Pump-station trip with all duty pumps running at 100% speed and wet well at maximum level; caused by total power loss or simultaneous emergency stop | p.38 para 1 |
| C-SURGEMAX-FRP — max allowable surge FRP | 100 psig maximum allowable surge pressure for FRP (CL100) | p.38 Table 3-6 |
| C-SURGEMAX-HDPE — max allowable surge HDPE | 200 psig maximum allowable surge pressure for DR-21 HDPE | p.38 Table 3-6 |
| C-SURGEMAX-DI — max allowable surge ductile iron | 660 psig maximum allowable surge for Flanged DI station piping and for MJ DI force main | p.38 Table 3-6 |
| C-SURGEMIN — minimum allowable surge (vacuum) | -7 psig for FRP; -10 psig for Flanged DI, MJ DI, and DR-21 HDPE | p.38 Table 3-6 |
| C-VEL — allowable velocities (material-independent) | Minimum 2.0 ft/s, maximum 10.0 ft/s | p.38 para below Table 3-6 |
| C-RELIEF — modelled surge mitigation at EGPS | Two surge relief valves in EGPS modelled, with open-pressure set points 110 psi and 120 psi; plus 23 EGFM air valves (8 Phase 1 + 8 Phase 2 + 7 Phase 3), 2-in and 4-in combination air release/vacuum-breaker with anti-surge orifice, plus modelled Gambles Mill / Maple Avenue air valves and 3-in combination valve upstream of control valve on 18-in DI to Maple Avenue FM | p.39 para 2 |
| C-BOUND — hydraulic boundary water levels and high points | Wet-well WSEL max 119.50 / min 114.00; Richmond FM high-point invert 253.00; Henrico FM high-point invert 268.00; static lift to Richmond 133.50 max-WW?/139.00 min-WW ft; to Henrico 148.50/154.00 ft (discharge elev minus wet-well elev) | p.29 EGPS Hydraulic Boundary Conditions |
| C-REPLACE — Section B replacement geometry (post-rupture) | First ~2.5 miles (≈10,755 ft) from EGPS replaced with 42-in IPS DR-21 HDPE, ID 37.76 in, HW 120/150, wave speed 893 ft/s; remaining FRP 36,070 ft ID 49.11 in CL100 wave 1,744 ft/s and MJ DI 2,435 ft ID 49.04 in Class 53 wave 3,616 ft/s stay | p.29 EGFM table + task statement |

## Standards
_none_

## Units on the flow path
- EGPS wet well (WSEL 119.50 max / 114.00 ft ASSUMED, p.29)
- EGPS duty pumps (2 now, up to 5 future; 4,583 GPM / 210 ft design point, 469 hp, inertia 405, p.29)
- EGPS standby pump(s) (1 now per 2/1, p.29; future standby ASSUMED per RFI-03)
- EGPS station piping (100 ft Flanged DI 12- to 42-in Class 53 wave Various, p.29)
- EGPS surge relief valves (110 psi + 120 psi open, p.39)
- Section B replacement — 42-in IPS DR-21 HDPE 37.76-in ID 10,755 ft I-14+95 to I-122+50 wave 893 ft/s (p.29)
- Remaining EGFM FRP — 48-in nom 49.11-in ID 36,070 ft CL100 I-131+90 to III-106+70 wave 1,744 ft/s (p.29)
- Remaining EGFM MJ DI — 48-in nom 49.04-in ID 2,435 ft Class 53 I-0+00 to I-14+95 + I-122+50 to I-131+90 wave 3,616 ft/s (p.29)
- EGFM Phase 1 air valves (8 loc.: 15+25,22+98,115+20,189+46 2-in ARI D-020; 46+05,56+50,65+30 4-in Vent-O-Mat RGX II x2; 148+29 4-in x1, p.39)
- EGFM Phase 2 air valves (8 loc.: 10+75,53+67,69+70,78+00,94+60,109+79,135+42,153+93 2-in ARI D-020, p.39)
- EGFM Phase 3 air valves (7 loc.: 10+54,20+80,33+35,50+69,82+98 2-in ARI D-020; 93+00 4-in x2; 102+80 4-in x1; 42+50 excluded, p.39)
- 18-in DI branch with control valve + 3-in combination valve to Maple Avenue FM toward Henrico (p.39)
- Maple Avenue Force Main to Henrico outfall on Maple Ave + its air valves 20+48,46+40 4-in (orifice ASSUMED same, p.40)
- Gambles Mill Pump Station + Force Main joining toward Henrico + its air valves 809+89,797+97 4-in (orifice ASSUMED same, p.40)
- Richmond outfall on Cary Street Rd via EGFM (high point inv. 253.00 ft ASSUMED, p.29)
- Henrico outfall on Maple Ave via EGFM + Maple Ave FM (high point inv. 268.00 ft ASSUMED, p.29)
