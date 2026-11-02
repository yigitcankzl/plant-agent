# C2 splitter PV-1767, Shell Chemical, Norco, Louisiana: operating basis before the 2015 study

Source: a peer-reviewed open-access paper with the plant's operating data (2018). The citation is withheld from the agent because its title describes the outcome; it is recorded with the withheld outcome in `outcome.json` and in the case's `source` field. Only the operating state before the project (April 2015) is given here; the paper's account of what was done is withheld.

## The tower
- Ethane/ethylene splitter in an olefins unit, highly heat-integrated with the rest of the unit. It has run for more than 35 years.
- 154 trays: conventional 4-pass round-valve trays, 410S stainless (1978 design, straight side downcomers, box-type centre and off-centre downcomers). Shell ID 4,877 mm; tray spacing 508 mm; tower about 91.5 m tall.
- Trays are counted from the bottom (tray 1 is at the bottom):
  - **Feed:** a vapour stream from the overhead of the upstream deethanizer, entering above tray 37.
  - **Ethylene product:** drawn as liquid from a chimney tray 10 trays from the top (trays 145–154, the pasteurization section above the draw, remove light ends to the vent).
  - **Side reboiler:** liquid draw and vapour return at tray 32. There is also a bottom reboiler.
  - **Overhead:** a partial condenser on refrigeration. The vent gas leaves as vapour; the liquid is all reflux.
- **Section loads before** (the paper's hydraulic rating of the 4-pass trays from the pre-project heat and material balance):

| Trays | Count | Section | Jet flood % | Weir loading m³/m·h | Downcomer velocity m/s | ΔP kPa/tray |
|---|---|---|---|---|---|---|
| 145–154 | 10 | Pasteurization | 82 | 73.0 | 0.106 | 0.543 |
| 38–144 | 107 | Above feed | 87 | 63.7 | 0.092 | 0.520 |
| 33–37 | 5 | Above side reboiler | 65 | 63.7 | 0.092 | 0.375 |
| 1–32 | 32 | Bottom | 54 | 55.2 | 0.079 | 0.355 |

- The measured tower ΔP was 170 kPa (about 1.1 kPa per tray including vapour head), which the paper reads as an indication of flooding on some trays.
- The site's assessment: the tower is the bottleneck.

## Operating data, 26–27 April 2015 (steady, pushed to high reflux)
The paper normalises every flow to a 1,000 kg/h feed at the plant's request. **Scale assumption (PlantAgent, not from the paper): absolute flow = normalised × 92.** This scale makes the Fair sieve-tray flooding screen give 87 % in the above-feed section at 4,877 mm and 508 mm spacing (the paper's figure for that section), using DWSIM SRK properties (ρL 420 kg/m³, ρV 42 kg/m³ at 23 bar, σ ≈ 0.0045 N/m). Model the tower at absolute flows, then **calibrate `tray_capacity_factor` (default 1.0)** so the above-feed section screens at about 87 % jet flood.

| Item | Tag | Units | Normalised | Absolute (×92) |
|---|---|---|---|---|
| Feed rate | FF-5758A | kg/h | 1055.83 | 97,136 |
| Feed temperature | TI-6147 | °C | −9.5 | |
| Top pressure | PT-5416 | kPa g | 2194.5 | |
| Column ΔP | PDI-5414 | kPa | 170.3 | |
| Bottoms flow | FT-5164 | kg/h | 405.55 | 37,311 |
| Reflux drum pressure | PI-5415 | kPa g | 2193.9 | |
| Reflux drum temperature | TI-6257 | °C | −27.1 | |
| Reflux | FI-5420 | kg/h | 3503.1 | 322,285 |
| Vent | FI-5425 | kg/h | 42.09 | 3,872 |
| Side reboiler duty | calculated | GJ/h | 22.1 (not a flow; read as absolute, 6.1 MW) | |
| Ethylene draw | FC-5154 | kg/h | 576.4 | 53,029 |
| Ethylene product, ethane | AI-5417A | ppm | 486.7 | |
| Ethylene product, methane | AI-5417B | ppm | 37.34 | |
| Vent, methane | AI-5424B | % | 1.99 | |
| Bottoms, ethylene | AI-5427 | % | 1.88 | |

**Pre-project heat and material balance** (the paper's simulation, SRK; normalised; feed 1,000 kg/h, so 92,000 kg/h absolute):

| wt % | Feed | Vent | Ethylene product | Ethane bottoms |
|---|---|---|---|---|
| Hydrogen | 0.0003 | 0.0075 | 0 | 0 |
| N2 | 0.0453 | 1.2658 | 0.0017 | 0 |
| Methane | 0.0498 | 1.1160 | 0.0049 | 0 |
| Ethylene | 62.40 | 97.606 | 99.942 | 1.751 |
| Ethane | 37.15 | 0.0046 | 0.0522 | 97.318 |
| Propylene | 0.2131 | 0 | 0 | 0.559 |
| Isobutane and heavier | 0.1421 | 0 | 0 | 0.372 |
| Total, kg/h (normalised) | 1000.0 | 42.09 | 576.47 | 381.44 |
| Phase | vapour | vapour | liquid | liquid |
| T, °C | −9.86 | −25.7 | −23.9 | 0.5 |
| P, kPa g | 2550 | 2193.1 | 2203.5 | 2364 |

- Tower top 2193.8 kPa g, top temperature −24.5 °C, reflux 3503.25 kg/h normalised at its bubble point (−25.7 °C).
- The old trays calibrate at about 78 % overall (Murphree) tray efficiency.
- Polymer-grade ethylene purity has to be kept, with minimal ethylene lost to the bottoms.

## Modelling notes
- **Package:** DWSIM SRK (or PR). Lump N2/hydrogen/methane as light ends and isobutane-and-heavier as isobutane if that helps convergence; say so.
- **Stages:** 154 trays plus a partial condenser (vent = vapour product) and a bottom reboiler, with the ethylene product as a liquid side draw at tray 145 counted from the bottom.
- **Side reboiler:** model it as a liquid side draw at tray 32, a heater and a return feed, or fold its duty into the bottom reboiler and say so.
- **Limits** for the column:
  - `diameter_m` 4.877, `tray_spacing_m` 0.508.
  - `flood_frac_max` 0.85 (the site's operating ceiling for jet flood).
  - `tray_capacity_factor` as calibrated above. It is a rating field: a different tray type changes it, and that is a physical replacement.
- DWSIM takes column pressure drop as an input. It does not compute tray ΔP.

## The question (the 2015 project premise)
Upstream cracking changes will raise the ethylene content of the feed to about 69 wt % and raise its rate. The olefins unit needs **about 25 % more ethylene from this tower (about 720 instead of 576 normalised kg/h) at polymer-grade purity**, with the feed slate shifted to about 69 wt % ethylene (about 1,130 normalised kg/h). What limits the tower, and what is the change?

The capacity target is checked as **125 % of today's feed at today's composition**. That gives about 25 % more ethylene and loads the sections above the feed about as the future feed would; it is conservative for the bottom section.
