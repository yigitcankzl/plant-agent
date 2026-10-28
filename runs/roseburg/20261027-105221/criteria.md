# Step 1 - Scope and design criteria

**Question:** Can Winchester WTP be expanded from 12 mgd to 18 mgd? For each unit along flow path, does it limit 18 mgd, at what flow does it bind, and least-cost fix to make 18 mgd work?

## Definitions
| term | definition | source |
|---|---|---|
| Firm capacity | Capacity with largest unit out of service | Engineering rules |
| Hydraulic vs treatment capacity | Piping/pumping/volume/flow-control ability to pass flow; Treatment = ability to meet regulatory requirements | p.107 General |
| Source document | WTP Preliminary Design Report July 2009, Section 4 Capacity Review + Figure 4-2 hydraulic profile (p.136, ultimate 22 MGD note) | p.107-119, dwg p.136 |

## Criteria
| name | value | source |
|---|---|---|
| Study objective - expand from 12 to 18 mgd | Existing floc/sed basin rated 12 mgd; plan adds parallel basin for nominal 18 mgd; determine if 18 mgd works and what limits | p.111 + Question |
| Firm capacity definition | Apply to intake, high-service, filters, backwash, wastewater pumps | Engineering rules (Firm capacity = capacity with largest unit out of service) |
| Maximum desirable velocity in transmission mains | 6.0 fps desirable; short WTP-site segments may exceed 6.0 fps as acceptable | p.110 (raw water) and p.116-117 (finished water) |
| Minimum treated-water storage / detention | Desirable minimum ~60 minutes detention at peak flow; at 24 mgd use 1-hour criterion = 1,000,000 gal | p.115 |
| Filter treatment rating vs hydraulic | Current 3 mgd/filter is treatment limit; hydraulically 4 mgd/filter to clearwell; 6 filters = 24 mgd hydraulic | p.112 |
| Filter driving head available | Normal filter level 463-464 ft to clearwell 446.5-448 ft = 15-17.5 ft; terminal headloss alarm 11.0 ft; max clearwell level 449.0 ft | p.112 |
| Surge protection performance | Protect to 9,700 gpm (14.0 mgd); max upsurge 150 psi; min downsurge HGL 630 ft (~175 ft head / 75 psi at grade 455 ft) | p.117 |
| Overflow / freeboard limits to enforce in profile | Floc/sed overflow weir 465.0 ft; settled channel ~6-in below weir at 13.1 mgd test; freeboard 1.5 ft at 466.0 ft max WS; clearwell overflows 449.5 ft (19 mgd at 1-ft depth) and 450.0 ft; combined 24 mgd | p.111, p.112, p.114 |

## Standards
| name | use |
|---|---|
| Document units: mgd, fps, ft, gpm, scfm, psi, gallons | Use document units throughout; conversions cited |
| Gravity legs in run_profile, pumped legs in run_hydraulics; calibrate to field tests + drawing water surfaces at drawing design flow with residuals; profile_capacity for limiting flows | Hydraulic method rule |

## Units on the flow path
- River intake / raw-water pump station
- 30-in raw-water pipeline + mag meter to floc/sed basin
- Rapid mix (2 basins, 1 now)
- Flocculation/sedimentation basin (1 now + 1 parallel) + launders/weirs/overflow weir + drain
- 42-in settled-water pipeline to filters
- Filters (4 now + 2 new = 6) + influent channel/20-in inlets + 16-in/18-in effluent + meters/valves + 8-in filter-to-waste
- Clearwell / treated storage (3 compartments + 85k under Filters 5-6) + overflows
- High-service pump station (4 now + 2 new) + 18-to-30-in header
- 30-in (29.25-in ID) finished-water site main + propeller/mag meter + hydropneumatic surge tank
- Offsite transmission to Reservoir Hill terminal reservoirs (20-in steel + 30-in DI + phased parallels)
- Backwash system (pumps/header) + air scour + backwash drains/channel
- Wastewater pump station + solids/washwater basins/drying beds
