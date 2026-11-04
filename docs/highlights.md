# Highlighted cases in full

Moved from the README so it stays short. Every claim keeps its evidence link.

## What it has done
- **The engineering loop** (`plantagent/loop.py`): the engines re-solve Muse's design and run every check (process, robustness, electrical, compressor curves and surge, start-up transient, uncertainty; limits and N-1 for grids). Failed checks go back to Muse with their numbers until everything passes or Muse says why it cannot. Every round is logged with who did what.
- **Deterministic engines** (DWSIM, WaterTAP, EPANET, pandapower, ht/fluids, Cantera) re-solve every proposal before it can be applied; a change that only edits a limit is refused.
- **Not only our demos.** An official DEXPI drawing we had never used (BASF column C02), with no hand-written case file: Muse built the DWSIM column and found it floods first at +13 % ($1.54 on open weights). Its first fix, a reflux cut to 0.8, fails the purity check added afterwards (minimum reflux 1.10); a 600 mm shell then gave **simulation checks passed**, vendor confirmation open. [Below](#basf-c02-the-loop-then-the-red-team).
- **A second model attacks the design** (`plantagent/redteam.py`): Muse Spark 1.3 proposes credible operating deviations within the +10 % envelope band, and DWSIM re-solves each one. BASF's 600 mm design held **8 of 8** attacks (worst flood 90 % of the limit; $0.13). [Evidence](../evidence/redteam/README.md).
- **A real plant, blind.** Shell's Norco C2 splitter before its 2015 revamp, outcome withheld. Muse Spark Open re-trayed the same shell, as Shell did: **round 1 failed** the +10 % feed case, **round 2 passed** every simulation check ($4.30). Against Shell's measurements: 5 match, 3 partial, 1 miss, 1 not predicted. [Below](#a-real-plant-blind-shell-norco-c2-splitter).
- **Open weights in the loop.** Muse Spark Open on Baseten: on UCTE, where the Meta-hosted endpoint refused the prompt four times (content policy), it found a switching plan that passes line limits and N-1; on Freeport it matched Muse Wonder; on the salt plant neither model finished. [Below](#open-weights-the-2006-european-blackout).
- **The engineer's red pen** (`web/redline.html`, `plantagent/redline.py`): Muse Wonder reads the red ink on an uploaded drawing into changes, the engineer confirms them, and the same checks run on the engineer's design and Muse's side by side. First live read (salt, typed notes): 3 of 3 transcribed, 1 mapped. [Evidence](../evidence/redline/README.md).
- **The honest denominator.** Across all 69 recorded engineering-loop runs during development (3 Nov, including the discarded first revamp-benchmark runs), 21 (30 %) ended with every deterministic check passing ($192 in total); most of those still carry an open vendor or human check. Each featured run is the last of several attempts, with harness fixes between them in the git log. Table: `PYTHONPATH=. python tools/loop_stats.py`.
- Blind benchmark: on 13 real projects with the engineers' conclusions withheld, Muse reaches **64 %** of the engineers' conclusions on average (range 33–100 %), graded by Muse Wonder against a fixed answer key, not by a person. [Details](cases.md#evidence-blind-benchmark-against-real-engineers).

The full, unshortened list (including the salt flagship and the two incidents) is in [docs/cases.md](cases.md#full-what-it-has-done-list).

| Muse does | The deterministic engines do |
|---|---|
| Reads P&IDs (DEXPI or PDF), data sheets, reports and photos | Solve the model: DWSIM (process, and trapped liquid along an isochore), WaterTAP (RO), EPANET/WNTR and TSNet (water), pandapower (grids), a gravity profile solver |
| Builds the simulator model and its calibration table | Re-solve every proposal and the combined design on the server before it can be applied |
| Plans the study, chooses which runs to make, proposes the changes | Check limits, relief paths (`pid.relief_scan`), the electrical load flow (pandapower), exchanger detail (ht/fluids) and combustion (Cantera) |
| Writes the answer and drafts the deliverables | Decide pass/fail on the discipline gates; citations and cited runs are checked without an LLM |

> Draft engineering output for review by a licensed professional engineer. It is not a substitute for one.

## Try it in three minutes

With the server running (above), open `http://127.0.0.1:8765/home.html` and press **Open the engineering desk**. It opens the salt crystalliser (`plant.html?case=salt_mvr&tour=1`) and walks through it in six steps: the source P&ID and the model Muse built from it; the +20 % question; what limits it; the fixes, each re-solved in DWSIM; before and after; the evidence.

Then open the BASF column card (`plant.html?case=basf_process_column_k_2750_dexpi_c02_uns`): a drawing the tool had never seen, with no hand-written case file.

Then open the two incident rows on the home page, `plant.html?case=ucte_2006` and `plant.html?case=freeport_lng_2022`. Drag the slider: grid transit for UCTE, hours blocked in for Freeport. Then open **Compare with the recorded decision**.

On the salt plant, look at:
- **Existing / Proposed** above the drawing: Rev B of the P&ID with the changes clouded.
- **Engineering impact**: one gate per discipline. Click a gate to see its checks and their sources.
- **Decision / Engineering**: the short decision, or the full calculations, alternatives, sources and audit.
- **Issue engineering package**: the MOC pack, pre-FEED gate, vendor RFQ duty sheet and commissioning plan.

## BASF C02: the loop, then the red team

`plant.html?case=basf_process_column_k_2750_dexpi_c02_uns`: the official DEXPI example C02 Process Column (BASF), unmodified, run through the upload path with no hand-written case file (`tools/onboard_unseen.py`).
- **Answer:** the column floods first: it reaches its 80 % flood allowance at +13 % of today's feed (reflux 1.5).
- **Loop 1:** cut reflux to 0.8; it passed the checks of the time. The purity check added afterwards fails it on replay (distillate ethanol 90.3 vs 90.8 % minimum). **Loop 2:** reflux 1.5 and a larger bottoms draw; everything passed except the +10 % feed case. **Loop 3:** a 600 mm shell (vendor to confirm): flooding 60.8 vs 80 %, purities pass, envelope 2/2, target held in 100 % of 48 uncertainty re-solves. $8.39 in total, all on Baseten.
- **Red team:** eight bounded attacks from Muse Spark 1.3, each re-solved by DWSIM; the design held 8 of 8. A harsher, unrealistic stacked set broke it, and the loop answered with a 700 mm shell (see caveats).
- Record: [docs/cases.md](cases.md#an-unseen-drawing-no-hand-written-files), [`evidence/generality-c02/`](../evidence/generality-c02/README.md), [`evidence/redteam/`](../evidence/redteam/README.md). The duty is Muse's assumption and the drawing already holds a 600 mm section; see [caveats](limits.md#caveats-of-the-headline-results).

## A real plant, blind: Shell Norco C2 splitter

`plant.html?case=shell_norco_c2splitter`: given Shell Norco's published pre-revamp operating data; the revamp, the after data and the paper's title are withheld, and the run starts with no earlier answers. Asked with no documents, all three Muse models say they do not know what Shell did ([probe](../evidence/real-plant-norco/closed_book_probe.json)).
- Muse Spark Open re-trayed the same shell, as Shell did. Round 1 failed the +10 % feed case; with those numbers, round 2 passed every simulation check: ethylene 1.25x (the server verified at today's 62.4 wt % feed composition; Muse's own runs at the 69 wt % premise gave 77 % of flood), 74 % of flood (85 % allowed), purity, minimum reflux, 48 of 48 uncertainty samples.
- Against what Shell measured: 5 match, 3 partial, 1 miss (the feed-tray move), 1 not predicted ([scorecard](../runs/ws/shell_norco_c2splitter/comparison.json)).
- Record: [`evidence/real-plant-norco/`](../evidence/real-plant-norco/README.md). The flood result rests mostly on Muse's assumed tray capacity; see [caveats](limits.md#caveats-of-the-headline-results).

## Open weights: the 2006 European blackout

`plant.html?case=ucte_2006` rebuilds the German 380 kV grid around Landesbergen from the UCTE Final Report (2007), stopping at the 22:08 request to couple two busbars. Blind, Muse found the coupling raises the tripping line 1,779 → 1,831 A instead of relieving it, as the report found.
- In the engineering loop the Meta-hosted endpoint rejected four attempts on content policy (not a quality result). **Muse Spark Open** on Baseten ran the same loop: redispatch + open the BIO-SPX 220 kV tie; line limits pass and N-1 has **0 violations**, in one independent paid run ($1.73).
- Record: [`evidence/open-weights-engineering/`](../evidence/open-weights-engineering/README.md) and [docs/cases.md](cases.md#incident-1-the-2006-european-blackout-power-grid). Loop evidence, not a controlled benchmark.

**More cases**, verbatim with their limits, in [docs/cases.md](cases.md): the salt crystalliser flagship, the scanned 1994 patent read, Freeport LNG, NREL cellulosic ethanol, the second opinion, the 2008 pilot decision, the blind benchmark, the workspace features, under the hood, and the roadmap.
