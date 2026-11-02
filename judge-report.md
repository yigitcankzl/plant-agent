# Judge report — 2026-11-01

Four read-only reviewers:
- **Rubric judges:** one per criterion, about 5 minutes each.
- **Competitor and past-winner scan.**
- **Wow critic:** watched the replays and screenshotted pages (`/tmp/wow/`).
- **First-time judge:** fresh clone, no API key, followed the README only.

## Scores
| Criterion (equal weight) | Score /10 | Why | Biggest fix |
|---|---|---|---|
| Impact | 6 | The problem is real and costly. But nobody is shown using it, the flagship plant is a 1994 patent with ILLUSTRATIVE ratings, and its headline result fails | 10 s from a practising engineer: "this took me X weeks" |
| Use of Meta AI tooling | 7 | Central, not incidental. Muse builds the simulators, designs the change and fixes it from numeric feedback. Vision reads a scanned patent; the same loop runs on open weights | Lead with one unmistakably-Muse capability: scan → running simulator, side by side |
| Technical depth | 8 | Six engines, server re-solve, limit-edit refusal, blind benchmarks with withheld answers, rigorous honesty. But the README is a wall of caveats | A loop diagram at the README top; a 5-line first screen |
| Demo | 5 | Rev B clouds and red tags look good. But the flagship replay ends in "Step limit, round 2"; four scenes in 3 min; sidebar text unreadable at 1080p | One loop that visibly goes red → numbers back to Muse → green, as the spine of the video |
| **Total** | **26/40** | Top-50 competitive, not yet top-5 | |

## Estimated standing and win probability
- **The gallery is gated** (Cerebral Valley, no projects visible), so this is not measured against live competitors.
- **Past Meta/Llama winners** were OpenGlass, Guardian (NHS triage), Gripmind and Llama Navigator. Each had a named human beneficiary in one sentence, a visual "it works" moment, and a demo that a non-expert understands in 10 s. None was a deep B2B engineering tool.
- **Novelty is real.** Cognite and AVEVA contextualise plant data; academic agents build steady-state HYSYS flowsheets. Nothing closes "Muse proposes → physics engines check → failures go back".
- **Estimate:**
  - Technical depth and Meta-usage: top decile.
  - Impact and demo: middle.
  - Top-10 plausible; top-5 a coin flip at best (~35–45 %); track win ~10–12 %.
  - Strong fit for **Best Agentic Use-Case ($5k)** and **Best Open Weight Build ($10k)**. Submit to both explicitly.

## Mocks, stubs, unbacked claims
The grep for mock/fake/dummy/stub/TODO/placeholder found nothing hidden. Most numbers match records.

| Claim / location | Reality | Fix or remove |
|---|---|---|
| README clean-clone list: BASF "works from stored results" | Fresh clone: "could not be loaded"; no `states.json` (`plant.py:3134`). `salt_mvr_vision` is the same | Precompute and commit `states.json` for both, or remove them from the list |
| Salt "verified at 120.1 %" | On a fresh clone the Proposed view shows "✗ Not at 120 %". `plant.html:1868` falls back to the existing-plant replay when `whatif` 500s (no DWSIM) and still labels it "proposed" | Store the proposed-design states, or label the fallback honestly |
| Roadmap 2 / BASF: "replace-equipment… loop cannot verify yet" | Stale: `replace_unit` exists (`plant.py`, `tests/test_replace_unit.py`) | Update; it is a feature now |
| Roadmap 4: "reviewer/approver missing" | Stale: `plantagent/signoff.py`, `web/review.html` | Move to features |
| Salt open-weights table | Omits loops `221341` (Spark Open, 5 rounds, $6.66) and `224302` (Muse Wonder, $0.52, UNSOLVABLE). The pinned `214821` is labelled "the latest word" | Add both; reword the pin as "featured run" |
| UCTE "refused four times" | Only a summary in `results.json`; no raw refusal responses | Commit the raw responses |
| Video script: Muse proposes K-202 | README: the K-202 idea was the engineer's in the original session. (In loop `214821` Muse proposed K-202 itself, but from a session that already contained it) | Say what the replay shows, attribute it carefully |
| BASF banner "Product purity is not checked" and headline "600 mm shell passes" | The purity check now exists and passes in `214001`; the shell was rejected in that run; robustness fails | Update the banner; don't say "passed at 120 %" without "robustness still fails" |

## Judge walkthrough friction
1. "Try it in three minutes" says open `web/home.html`. As a file it fails. The server command is about 300 lines down. Put the 3 commands and the URL at the top. A hosted URL would be best.
2. The salt Proposed view and the BASF page break without DWSIM (above).
3. "Run full engineering" looks live without a key. Disable it, or label it "replay only".
4. `dc_iitk` card "could not load"; Roseburg and Edgebrook workspaces 500 (their PDFs are not shipped).

**Disqualification risks**
- **Repo is private.** The rules say repositories must be public. Make it public before submission.
- **No LICENSE file.**
- **The README never names the theme.** Add one line: "Push the Frontier — manufacturing/energy".
- **First commit timing.** It is about 22 h after kickoff with 1,304 lines. The Timeline section explains it; fine as long as only event work is shown.

## Wow moment
**Today: none that lands on video.**
- The closest is the UCTE slider turning lines red. It is a pandapower result, not Muse.
- The Meta surprise (hosted refused, open weights solved) is only spoken in the script, never shown.
- The salt replay is small sidebar text, and the drawing barely changes.

**Two options, both replay-only, $0:**
1. **Scan → simulator (25 s).** Full-screen 1994 patent FIG. I; Muse's tags appear on it; cross-fade to the rendered P&ID with DWSIM numbers; "226.8 t/h to K-201 — matches Table I"; the three model-review corrections flip red → green.
2. **Refused, then solved (30 s).** Split screen: the hosted endpoint refused ×4 | Muse Spark Open. Drag UCTE to red, play the open-weights fix on the one-line (tie opens, redispatch), lines turn green, then the stamp "N-1: 0 violations".

## Strategic read
- **What decides win vs lose:** whether a non-chemical-engineer judge gets the "aha" in the first 45 s. The depth is already a finalist's. The losing mode is a dense, hedged, many-case video whose payoff ends in red, where the viewer can't tell what Muse did versus what the scripts did.
- **Framing:** "AI engineer" overreaches as a headline; the project's own evidence undercuts it. "Muse proposes, physics disposes" / "the AI is not trusted, it is checked" is believable and still bold.
- **Breadth:** too broad in presentation, deep in substance. The video should be one plant's loop + one unseen-drawing beat + one open-weights beat. Everything else goes in a "library" link.

## Prioritized fix list (to Nov 4 18:00 Istanbul)
1. **Make the repo public; add LICENSE; name the theme in the README.** (Disqualification risk.)
2. **Fresh-clone truth.** Commit precomputed states for BASF, `salt_mvr_vision` and the salt proposed design, or label the fallbacks. Put the 3 run commands at the README top.
3. **Rebuild the video around one closed loop** with a "Muse did / engine checked" split on screen. Use the cold open "refused, then solved" and the "scan → simulator" beat. Cut the assumptions scene; keep BASF to 10 s. Zoom every sidebar shot.
4. **Get one loop that ends green on video.** Candidates:
   - BASF with `replace_unit` (600 mm shell now verifies: flood 60.8 %, purity unchanged), ~$4 Baseten;
   - salt with the demo vendor curve uploaded.
   If none closes, end the video on a deliberate "UNSOLVABLE: needs the vendor surge curve", not "step limit".
5. **README top:** a 5-line pitch, a loop diagram, and "Muse proposes, physics disposes". Move the caveats lower. Fix the stale roadmap lines and the open-weights table.
6. **The two $0 wow animations** (scan → simulator; refused → solved) from stored data.
7. **Optional:** a 10 s clip or quote from a practising process engineer.
