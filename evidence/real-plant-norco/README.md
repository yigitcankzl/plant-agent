# Real plant: Shell Norco C2 splitter, blind against the 2015 revamp

> **Correction, 2026-11-02.** The flood figures of the earlier runs below (62 %, 61 %, 65 % against Shell's 64.7 %) were computed under a column-flow scaling that has since been fixed: fixed column flow amounts were not scaled with the feed. We no longer claim that flood match. Under the corrected scaling and the current checks (which also require the ethylene product, not only the feed, to reach the target), the featured run is Muse Spark Open on Fireworks, `work/20261102-183619`: **done** in one round for $2.81, ethylene 1.26x today, flood **75 %** of the 85 % limit, ethane 0 ppm (idealised simulation), minimum reflux held, the +10 % feed case and 39 of 39 uncertainty samples passing. The envelope and uncertainty rows use drafted (assumed) inputs. The new tray rating is Muse's assumption (vendor to confirm); the feed-tray move was not proposed. The tables below are kept as the record of the earlier runs.

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
3. **First engineering loop** ($4.97, 2 rounds, `work/20261102-001014`): stopped at its $5 cap with no newly verified design. Its re-tray proposals were rejected as "not verified" with no reason. That was a bug, explained below; the checks, including purity, never ran.
4. **Second engineering loop, with the documented purity spec** ($5.88, `work/20261102-005617`, session in `work/20261102-005617/session`): one round, then the $6 cap.
   - Muse's design: re-tray the same shell (capacity factor 1.85, efficiency 0.88, vendor to confirm), reflux ratio 5.0, bottoms 310 mol/s, at Shell's Feb 2017 feed of 103,960 kg/h at 69 wt % ethylene.
   - The server refused it: "DWSIM re-solve failed at 1.25×: PR EOS: unable to calculate compressibility factor". Muse had set the feed rate itself, and the server then scaled it by 1.25 again (about 130,000 kg/h against a 310 mol/s bottoms rate).
   - The verifier now names that mistake to Muse. The budget was spent before a second round could use it.

**Total recorded spend:** $49.11: $29.30 on Baseten (build, blind answer and four Spark Open loops) and $19.81 on Meta-hosted Muse Wonder (two loops). One loop ended done (screening checks pass, approval items open); none is an approved design.

## Purity: what was wrong, and what the check now does
- **Why the first loop said nothing:** when the DWSIM re-solve itself failed, the server marked the proposal "not verified" without a reason. The real error was a Peng–Robinson flash failure: Muse had changed only the tray rating and left the bottoms and vent rates at today's values, which is infeasible at 1.25× feed. The reason now reaches the worklog and Muse (`plantagent/plant.py` verify, `tests/test_verify_reason.py`).
- **The spec is documented,** not drafted (`cases/shell_norco_c2splitter/purity.json`): polymer-grade ethylene, read as ethane in the product at most 0.1 wt % (1,000 ppm). It rests on Table 1 (product ethane 486.7 ppm at AI-5417A, 99.942 wt % ethylene) and the premise "at polymer-grade purity".
  - It limits ethane, the key the tower separates, rather than "ethylene ≥ 99.9 wt %". The model's product impurity is methane and nitrogen from the vent split, about 0.11 wt %. The real tower removes those in its pasteurisation trays, which the model lumps; on an ethylene-wt % spec the model's own today would fail (99.887 %).
- **Deterministic check, no model call:**

| Design | Ethane in product | Flood vs limit | Purity spec |
|---|---|---|---|
| Today, 1.0× | 0 ppm | 99.6 % | pass, reflux 6.08 vs 4.86 minimum |
| Blind answer (factor 1.65, reflux 3.6, bottoms 280 mol/s), 1.25× | 152,137 ppm | 91.6 % | **fail at any reflux**: the bottoms rate is below the feed's ethane, so ethane goes overhead |
| Same trays, bottoms scaled to 405.5 mol/s, reflux 5.54, 1.25× | 0 ppm | 88.5 % | pass, minimum reflux 4.94 |
| Second loop's design at its own feed (103,960 kg/h, 69 wt %), 1.0× | 1 ppm | 73.5 % | pass, reflux 5.0 vs 4.30 minimum |

  Muse's first design failed through its product rates, not its trays.

## Scorecard of the second loop's design (`tools/norco_compare.py <session>`, no LLM; on the page)
Re-solved in DWSIM at the feed Muse chose, Shell's Feb 2017 slate (run `PV1767-PROVEN-104K-R53-B310`, 103,960 kg/h at 69.0 wt % ethylene). The server did not verify this design at 1.25× (above); this is the agent's design checked here, not a loop that ended done.

**Inputs/current state reproduced:** 2. **Withheld or after-revamp outcomes:** 8 match, 1 partial, 1 miss, 1 not predicted.

The current bottleneck and the approximate future feed slate were supplied to the agent, so they are reported separately rather than counted as blind predictions.

| Item | Agent (loop, purity spec in force) | Shell, measured | Verdict |
|---|---|---|---|
| Bottleneck section today | above feed, 85 % flood | above feed, 87 % (in the before data) | match |
| Change to the internals | high-capacity trays (factor 1.85), higher efficiency, same shell | all 154 trays replaced with HiFi Plus | match |
| Feed the design was solved for | 103,960 kg/h at 69.0 wt % | 103,896 kg/h at 69.3 wt % | match |
| **Ethylene product purity** | **99.89 wt %, ethane 1 ppm** | **99.944 wt %; spec ethane ≤ 1,000 ppm** | **match** |
| Jet flood above feed after | 62 % | 64.7 % | match |
| Ethylene product rate | +26 % | +25 % | match |
| Reflux (mass) | +5 % | +14 % | match (within 10 points) |
| Reboiler duty per kg ethylene | −17 % | −6 % (plant) to −15 % (paper) | match |
| Condenser duty | +6 % | not addressed; now limits | match |
| Flags condenser / refrigeration | yes | left unaddressed, now the limit | match |
| Tray efficiency of the new trays | 88 % (assumed) | 82.6 % | partial |
| Feed tray | not moved | moved up, 37 → above 45 | miss |
| Column pressure drop | not predicted | 170 → 99 kPa | not predicted |

## Scorecard of the blind answer (first pass, before the purity spec)
The blind design is re-solved in DWSIM at the feed Muse designed for: its cited run `PV1767-proven-36R-28B`, 115,000 kg/h at 68 wt % ethylene. Its operating specs do not converge on Shell's exact Feb 2017 feed (103,896 kg/h at 69.3 wt % at our scale).

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
- **The ask step does not run the purity check.** The blind answer's design is "verified" for capacity only. The page's what-if says "runs at 125 %"; that is a capacity statement, not a product-quality one.
- **With the documented purity spec,** the second loop's design holds polymer grade, keeping reflux up (mass +5 %) and the bottoms rate matched to the feed. It lands within a few points of Shell's measured flood, ethylene rate and reboiler duty. It is still not a verified-done design: the server refused it for setting the feed rate, and the $6 cap ended the loop before a second round.
- **Missed:** it did not move the feed tray.
- **Possible training-data exposure:** the paper is public since 2018, and Muse named the tray class in the blind answer.

## Third loop (`work/20261102-015254`) and the server re-check, no model call
- **In the loop:** Muse kept today's feed rate and sent the feed composition as `feeds.FEED.x.Ethylene` / `x.Ethane`. Its own run converged at 1.25×. The server re-solve failed with "PR EOS: unable to calculate compressibility factor".
- **First root cause (ours, fixed):** `patch()` wrote `feeds.FEED.x.Ethylene` as a flat key the simulator never reads. The server therefore solved the old 64 wt % ethylene feed. At 1.25× that feed carries about 378 mol/s of ethane, more than the 347 mol/s bottoms Muse specified, so the column was infeasible. Nested paths now set the composition (`plant._set_field`; test `tests/test_patch_nested.py`).
- **Second gap (fixed as a clearer rejection, not a loosened rule):** Muse raised the tray rating with a path edit, `units.PV-1767.tray_capacity_factor` 1.3 → 1.85. The flood check reads the rating from `limits`, so the server solved the new trays but judged them against the old rating. A rated limit now has to change through `replace_unit` (vendor to confirm), and the rejection says how. Muse's own runs had also raised the limit in their spec, which the server never accepts.
- **Re-check of Muse's answer 4** (`work/20261102-015254/server_reverify.json`, no model call; Muse's recorded text unchanged):
  - **As written:** rejected, with the fixable reason above.
  - **Same numbers, tray rating sent as `replace_unit`** (our translation, labelled so): verified at 125 % (new rating, vendor to confirm).

    | Check | Result | Verdict |
    |---|---|---|
    | Flooding | 69.7 vs 85 % | pass |
    | Ethane in the ethylene product | 0 vs 1,000 ppm (documented spec) | pass |
    | Reflux | 5.2 vs 4.40 minimum | pass |
    | Process | reaches 125 % | pass |
    | Draft envelope at feed +10 % (1.375×) | does not solve | fail |
    | Uncertainty | all 48 samples fail to solve | open |

  - **Why the last two fail:** Muse's column is specified by a fixed bottoms rate (347 mol/s). At 1.375× the feed carries about 416 mol/s of ethane, so a fixed bottoms rate cannot follow a feed swing; a plant would hold the bottoms on level or ratio control. The capacity search fails for the same reason, so the page shows "maximum not found" instead of a made-up 0 %.
- **Verdict:** at the target, the design matches what Shell built and measured (re-tray, purity held, flood in the 60s). **It is not a verified-done design:** it is not robust to a feed swing as specified.

## Later comparison loops
- **Spark Open, `work/20261102-025639`** ($5.81, four rounds): stopped at the round limit with no verified proposal. Its stored headline says the re-tray passes, but its result rows are empty and three vendor/utility/feed confirmations remain; this is not a completed design.
- **Muse Wonder, `work/20261102-105748`** ($8.58, two rounds): stopped at its budget after its proposals were rejected. The stored optimistic headline is model text, not a verified result. New worklogs replace such a headline with “No verified design before budget limit”; the historical record is left unchanged.

## The loop that ended done: Muse Wonder, `work/20261102-143533` ($11.23, two rounds)
Run after the agent's own trial runs started naming what the verifier refuses (`proposal_rules` in `run_process` results, `plantagent/plant.py` `sandbox_notes`). Both earlier models had edited a rated limit by path and re-set the feed rate in their own runs, seen them pass, and been refused at verify. The verifier's rules did not change.
- **Round 1** ($5.50): rejected. The tray efficiency change had no `physical_change` and `rating_source`.
- **Round 2** ($5.74): verified. Muse's design:
  - replace the trays in the same 4,877 mm shell, sent as `replace_unit` (tray capacity factor 1.30 → 1.85, vendor to confirm);
  - tray efficiency 0.78 → 0.88, with its physical change and rating source;
  - feed composition 64.1 → 70.5 wt % ethylene, at today's feed rate (the server scales it by 1.25);
  - reflux ratio 6.08 → 5.2, bottoms 324 → 405.5 mol/s.

| Check (server, no model call) | Result | Verdict |
|---|---|---|
| Process | reaches 125 % (the capacity search found no maximum) | pass |
| Flooding | 65.0 vs 85 % | pass |
| Ethane in the ethylene product | 0 vs 1,000 ppm (documented spec) | pass |
| Minimum reflux | 5.2 vs 4.36 to hold the spec at 125 % | pass |
| Operating envelope, feed +10 % | 2/2 scenarios pass (draft, assumed values) | pass |
| Vendor rating of the new trays | to confirm | open |
| Piping and utilities | no calculation adapter | open |
| Uncertainty | all 48 samples failed to solve | open |

- **Reading:** the server verified the change Shell actually made, re-traying the same shell, at the target, with polymer-grade purity and the +10 % feed case. Flood landed at 65 % (Shell measured 64.7 %), but under the flow scaling corrected on 2026-11-02; see the correction at the top. This is a screening result, not an approval: the vendor rating, the piping and the uncertainty run stay open. The feed tray is still not moved.
- The page shows this run (`featured_work` in `case.json`).

## Files
- `cases/shell_norco_c2splitter/basis.md`, `case.json`, `outcome.json` (withheld)
- `runs/ws/shell_norco_c2splitter/`: model, sessions (logs and answers), the loop work log, sweeps, `comparison.json`, `states.json` (precomputed slider states)
- `tools/norco_compare.py`: the scorecard
