# Judge report — 2026-11-03

Four read-only reviewers: rubric judges, competitor scan, wow critic, first-time judge walkthrough with a claims audit. Supersedes the 2026-11-01 snapshot (26/40).

## Scores
| Criterion (equal weight) | Score /10 | Why | Biggest fix |
|---|---|---|---|
| Impact | 6 | Norco is a real plant tested blind and the README withdrew the 65 % flood match honestly; but Norco is bullet 5, the flagship salt case runs on illustrative ratings and ends "do not approve yet", and the 13-study 64 % is graded by Muse Wonder | Lead the README and the pitch with Norco: "blind, it reached Shell's 2015 re-tray decision" |
| Use of Meta AI Tooling | 7 | Three models with distinct roles (Wonder reads drawings and red ink, Spark 1.3 attacks designs, Spark Open closes the loop on Baseten and Fireworks); the newest pieces are not in the video script, and the "surprise" leans on a content-filter refusal | Show the red team (Muse attacks Muse, DWSIM referees) instead of the refusal |
| Technical Depth | 8 | Six engines, server-side re-solve, limit-only edits refused, purity gate caught Muse's reflux cut, schema'd worklog; breadth hurts (386-line README, ~20 cases) | Cut the README to the loop plus three cases; move the rest to a library doc |
| Demo | 6 | Script has a real red → numbers → green loop; 0:20 overclaims the scan (the vision-built model is heat-limited at 92 % and not calibrated; 226.8 t/h came from the drawn P&ID); 1:50 splices two salt runs | Make every line describe the run on screen |
| **Total** | **27/40** | | |

## Estimated standing & win probability
- No public gallery yet; GitHub search found hundreds of entries, mostly consumer apps and wrappers. The Oct 28 "Verifiable Agents" workshop pushed many teams to the propose/verify pattern: RAN Sentinel (LTE co-engineer, 14 stars, polished), UNLOCK (CadQuery redesign, hosted demo), gridtwin (hardware-in-the-loop), autolab, siliconmind, gridxray.
- In process/energy engineering depth PlantAgent is plausibly the strongest entry found: real incidents, a real Shell revamp, blind benchmarks, the broadest Meta model use. Nothing found (Cognite Atlas, AspenTech, Imubit, DWSIM 10's assistant, Sketch2Simulation, BASF/RWTH) goes drawing → simulation → proposed revamp → multi-discipline checks with feedback → red team → blind benchmark.
- Past Meta × Cerebral Valley winners (OpenGlass, Deb8, Atlas) won on a visceral 10-second demo or a clear human stake, not engineering rigour.
- Assumptions: Indie track, 5 prize slots, several hundred serious entries. Estimate: top-10 in track plausible (~35 %), top-5 ~15–20 %, 1st ~5 %. Bonus: Best Agentic Use-Case and Best Open Weights are realistic (~20–25 % each); Creative Build (Wonder) weak.

## Mocks, stubs, unbacked claims
| Claim / location | Reality (file:line) | Fix or remove |
|---|---|---|
| README L25 flagship "TX-1 overloaded (~133 %)", tour step 5 | Verified: the committed `runs/ws/salt_mvr/gates.json` has the electrical gate, but a clean-clone server re-computes gates and `plantagent/prefeed.py:488` silently skips electrical when pandapower is missing; the rewritten file has no electrical row | Emit an "open: engine not installed" row; serve the committed cache instead of recomputing without engines |
| `plantagent/prefeed.py:423-426` | Without engines a recomputed or cached gate still says "re-solved now" | Label the source (cached vs re-solved) |
| README L23/L25 "repeat until everything passes", "+20 % with three verified changes" | No salt loop run ended done (9 runs); featured run `20261101-214821` is status error; the +20 % design came from Ask plus the engineer's K-202 hint | Say so in the bullet; feature a non-error run or none |
| README L34 "Muse reaches 64 % of them" | 0.641 mean over 13 cases is right, but it is 64 % of the engineers' conclusions, graded by Muse Wonder, older study agent (Oct 27–28) | Reword |
| README L234 "$0.04–0.64, median $0.10 over 22 runs" | 20 costed runs, min $0.051, median $0.098 | Fix the numbers |
| `evidence/real-plant-norco/README.md:73,91,154` | Still claims the 62/61/65 % vs 64.7 % "match" the main README withdrew; no mention of the $2.81 Fireworks run | Update |
| `evidence/redline/README.md:5` | Says no live read was run, contradicting its own section at L58 | Delete stale paragraph |
| README L14 "Spark Open on Baseten" | Norco and benchmark runs used Fireworks; `FIREWORKS_API_KEY` missing from `.env.example` | Add Fireworks |
| Video script 0:20 and 1:50 | Scan overclaim; spliced salt runs | Rewrite those two lines |
| UCTE run `20261101-163125` | Stuck at status "running" | Labelled "interrupted" by `tools/loop_stats.py`; mark it in the worklog |
| Red team, redline, BASF, UCTE, Freeport, Norco numbers | Backed by worklogs and evidence files | OK |

## Judge walkthrough friction
1. Clean clone: salt gates and tour step 5 lose the electrical gate (the flagship headline).
2. Salt's featured worklog is an error run.
3. Cold pip install (cantera, pythonnet, pandas) takes 2–4 min, not "three minutes" end to end; `python3.12` is hard-coded.
4. Engine-dependent controls are visible in replay and fail on click.
5. Norco and the redline, the newest headline items, are not in "Try it in three minutes".
6. Top bullets link to evidence READMEs that contradict them.
7. New-work rule: the first commit (Oct 27 10:42) is 1,304 lines; add one explicit sentence that no code existed before kickoff and early commits batch local work from 01:53 Oct 27.

## Wow moment
Today there is none in the first 30 s: a title card and the UCTE slider (our engine, not a Meta model). Best existing beat is the live BASF loop at 0:45–1:50, but it is a text strip at ×8.
- **Option A, "Muse vs Muse, physics referees" (~1 day UI, data exists):** a red-team panel on the BASF page from `redteam_600mm.json` and run `20261102-203128`: eight attacker cards, flood bars green 8/8 (worst 90 %), harder attacks turn them red 116–118 %, the loop answers with 700 mm and goes green. One live attack (~$0.13). Cold open.
- **Option B, real pen to physics verdict (~0.5 day):** print salt Rev A, mark it by hand, photograph, upload to `redline.html`; show the read, the confirmation, and engineer 100 % (compressor) vs Muse 120 % with TX-1 133 % in red. Handwriting accuracy is unmeasured; show misreads if they happen.
- Keep Norco out of the cold open: Muse named Shell's tray brand, which judges may read as memorisation.

## Prioritized fix list (deadline Nov 4, 21:00 ET = Nov 5 05:00 Istanbul)
1. Electrical gate lost on a clean clone: serve the committed gates, emit "open" rows for missing engines, label cached vs re-solved.
2. Stale and overstated claims: salt loop wording, 64 % wording, cost range, Norco and redline evidence READMEs, Fireworks in README and `.env.example`, the stuck UCTE run.
3. Red-team panel in the UI (Option A).
4. README restructure: Norco and the loop first, three cases, the rest to `docs/library.md`; add Norco and the redline to "Try it".
5. Video script lines 0:20 and 1:50 corrected; red team and redline beats added.
6. New-work sentence in README and submission form.
7. Hide or disable engine-dependent controls in replay (Codex is on it).
