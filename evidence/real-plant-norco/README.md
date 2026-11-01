# Real plant: Shell Norco C2 splitter, blind against the 2015 revamp

**Question:** given only the operating state before the project, does the agent reach what Shell's and Sulzer's engineers did?

**Source:** Summers D., de Villiers W., Green W., 2018, "C2 splitter revamp surpasses capacity and efficiency of 4-pass trays", *Chemical Engineering Transactions* 69, 703–708, [DOI 10.3303/CET1869118](https://www.aidic.it/cet/18/69/118.pdf). The paper is open access, © AIDIC. It is not redistributed here; only the numbers used are transcribed, with their table references.

**Model:** Muse Spark Open (`baseten:meta-models/muse-spark-open-1026`, open weights on Baseten). No Meta-hosted model was called.

## What the agent got, and what it did not
- **Given** (`cases/shell_norco_c2splitter/basis.md`):
  - the tower: 154 four-pass trays, 4,877 mm ID, 508 mm spacing, feed, product draw and side reboiler locations;
  - the April 2015 operating data (Table 1, before column);
  - the pre-project heat and material balance (Table 2) and the tray hydraulics before (Table 3);
  - the project premise: about 25 % more ethylene, with the feed shifted to about 69 wt % ethylene.
- **Withheld** (`cases/shell_norco_c2splitter/outcome.json`, which the agent never reads):
  - the revamp itself: HiFi Plus trays, feed and side-reboiler moved up, reboiler upgrade;
  - the after data (Table 1 after column, Tables 4 and 5);
  - the conclusions, including that condenser and refrigeration were left unaddressed.
- **Scale assumption (ours):** the paper normalises flows to a 1,000 kg/h feed. We took absolute flow = normalised × 92, backed out from the paper's 87 % jet flood above the feed at 4,877 mm with Fair's correlation and DWSIM SRK properties. The side-reboiler duty (22.1 GJ/h ≈ 6 MW) is consistent with that scale.

## What Muse did
1. **Build** ($2.94, 437 s, 15 steps): a rigorous 156-stage DWSIM column.
   - Setup: PR, partial condenser with the vent, Murphree efficiency 0.78.
   - Calibration: a tray capacity factor of 1.30 on Fair's sieve-tray flood screen reproduces the 85–87 % jet flood.
   - Simplifications it stated:
     - the pasteurization section is lumped (ethylene as the liquid distillate);
     - the side reboiler is folded into the bottom reboiler;
     - H2 is dropped and C4+ lumped as isobutane.
   - One mis-citation: its assumption list cites "CET69 Fig 2" for the tray count, but Fig. 2 is a reflux chart.
2. **Answer, blind** ($2.97): "C2 splitter floods at +11 %; re-tray gives +25 %." Its proposal:
   - replace all 154 trays in the same shell with high-capacity, high-efficiency trays (it named the "Shell HiFi Plus / Sulzer UFM Plus class");
   - tray capacity factor 1.30 → 1.65, efficiency 0.78 → 0.85, vendor to confirm;
   - reflux ratio cut from 6.08 to 3.6.

   It also asked for the refrigeration and reboiler headers to be confirmed at 30.7 / 21.3 MW.
   - Naming the tray brand may reflect training data on this published case; we cannot rule that out.
3. **Engineering loop** ($4.97, 2 rounds, `work/20261102-001014`): stopped at its $5 cap with no newly verified design. Its round-2 re-tray (factor 1.85, efficiency 0.88, reflux kept at 6.08) was not verified; the loop recorded no reason. The page's design is the blind answer's re-tray.

**Total spend:** $10.88 on Baseten (88 ledger lines tagged `plant:shell_norco_c2splitter`).

## Scorecard (`tools/norco_compare.py`, no LLM)
The agent's design is re-solved in DWSIM at the feed Muse designed for: its cited run `PV1767-proven-36R-28B`, 115,000 kg/h at 68 wt % ethylene. Its operating specs do not converge on Shell's exact Feb 2017 feed (103,896 kg/h at 69.3 wt % at our scale).

| Item | Agent (blind) | Shell, measured | Verdict |
|---|---|---|---|
| Bottleneck section today | above feed, 85 % flood | above feed, 87 % (this was in the before data the agent saw) | match |
| Change to the internals | high-capacity trays, same shell, higher efficiency | all 154 trays replaced with high-capacity HiFi Plus trays | match |
| Tray efficiency of the new trays | 85 % (assumed) | 82.6 % (fitted after) | match |
| Jet flood above feed after | 61 % (Fair screen, new rating) | 64.7 % | match |
| Flags condenser / refrigeration | yes | left unaddressed, now the limit | match |
| Feed the design was solved for | 115,000 kg/h at 68 wt % | 103,896 kg/h at 69.3 wt % (at our scale) | partial |
| Reboiler duty per kg ethylene | −36 % | −6 % (plant) to −15 % (paper) | partial |
| Condenser duty | −4 % | not addressed; now limits | partial |
| Feed tray | not moved | moved up, 37 → above 45 | miss |
| **Ethylene product purity** | **92.5 wt %** | **99.94 wt % (polymer grade)** | **miss** |
| Ethylene product rate | +37 % | +25 % | miss |
| Reflux (mass) | −13 % | +14 % | miss |
| Column pressure drop | not predicted (DWSIM takes column ΔP as an input) | 170 → 99 kPa | not predicted |

**Reading:**
- **Muse found the right problem and the right kind of fix:** re-tray the existing shell with high-capacity trays. Its predicted flood (61 %) and tray efficiency (85 %) land close to what Shell measured. It also flagged refrigeration, the limit Shell chose not to address.
- **Its operating point is wrong.** To relieve flooding it cut reflux, and polymer-grade purity was lost: 92.5 wt % ethylene, the extra product is mostly ethane. Shell raised reflux by 14 %, and the new trays carried that load.
- **The ask step does not run the purity check.** The blind answer's design is "verified" for capacity only. The loop, which does run the checks, did not reach a verified variant within its $5 cap. The page's what-if says "runs at 125 %"; that is a capacity statement, not a product-quality one.
- **Missed:** it did not move the feed tray.

## Files
- `cases/shell_norco_c2splitter/basis.md`, `case.json`, `outcome.json` (withheld)
- `runs/ws/shell_norco_c2splitter/`: model, sessions (logs and answers), the loop work log, sweeps, `comparison.json`, `states.json` (precomputed slider states)
- `tools/norco_compare.py`: the scorecard
