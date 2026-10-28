# Step 1 - Scope and design criteria

**Question:** Energy audit of the Briare pumping station: is the existing pump selection appropriate for the system, would variable speed drives save energy, and which measures should the operator take to reduce energy use? Quantify with the simulator where possible and state the data needed to confirm.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| Normal operating duty | 2 pumps most of time, up to 3 if necessary (p.6) | p.6 |
| Installed / duty configuration | 6 pumps installed; Duty / Duty / Assist + 3 Standby units assumed (p.6) | p.6 |
| Firm capacity definition | Firm capacity = capacity with largest unit out of service; with 6 installed and 2-pump normal duty (p.6), firm 2-pump duty requires 3 pumps available | Engineering rules + p.6 |
| Suction / wet-well levels | 124.2 to 125.8 mNGF (p.6); Sump TVL 125.8 mNGF, Design ~124.9 mNGF, SWL 124.2 mNGF (p.9, partly legible) | p.6, p.9 |
| Discharge level and static lift | Discharge 168.1 mNGF (p.6); Elevation rise ~43 m (p.6); Static lift Minimum ~42.3 m / Design ~43.2 m / Maximum ~43.9 m (p.9, 168.1 minus 125.8/124.9/124.2) | p.6, p.9 |
| Rising-main geometry | Twin 900 mm diameter mains, approx. 2650 m length (p.6); 2 x 2650 m (O 900 mm) on schematic (p.7) | p.6 |
| Station pipework | 300 mm diameter branch into 750 mm diameter manifold (3 pumps) (p.6) | p.6 |
| Hydraulic roughness - design and sensitivity | Design ks 0.3 mm; sensitivity curves for 0.03 mm and 1.5 mm (p.6, p.8, p.9: Low 0.03 / Design 0.3 / High 1.5 mm) | p.6, p.8, p.9 |
| 2020 implementation scope / efficiency target | Automation, supervision and telecontrol; optimising operations time periods; at least one new pump; Motor IE3 or IE4, Variable Speed Drive (VSD); Smart water and energy monitoring (p.5) | p.5 |
| Existing motor standard | IE2, Rated Motor Output 170 kW, Fixed Speed assumed star-delta (p.6) | p.6 |
| Specific-energy benchmark | Existing 174 kWh/1000 m3 for 2- or 3-pump operation, 172 for 1 pump (p.10, p.11); IE3 option 170 kWh/1000 m3 for 2- or 3-pump, 167 for 1 pump (p.10); reduction ~4 kWh/1000 m3 (p.10) | p.10, p.11 |
| Annual pumped volume for savings | 2,907,360 m3 in 2016 (p.11); single IE3 pump at 66% utilisation saves 3,873 kWh/annum, all pumps 11,629 kWh/annum (p.11) | p.11 |
| Electrical load benchmark | Base supplementary load ~10 kW summer and ~20 kW winter (p.11); typical summer total ~280 kW, pumping ~270 kW after base, vs predicted 265 kW for 2 pumps (p.11) | p.11 |

## Standards
_none_

## Units on the flow path
- Wet well / sump (124.2 to 125.8 mNGF) (p.6)
- 6x Xylem (Flygt) CP3231 pumps, 435 mm impeller, 170 kW IE2 fixed-speed (p.6)
- 300 mm diameter branch pipework per pump (p.6)
- 750 mm diameter manifold per 3 pumps (p.6)
- Twin 900 mm diameter rising mains approx. 2650 m (p.6, p.7)
- Discharge at 168.1 mNGF, approx. 43 m rise (p.6, p.7)
