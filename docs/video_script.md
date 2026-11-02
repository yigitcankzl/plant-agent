# Demo video: 3 minutes

## Organiser rules (Nov 1)
- The video is at most 3:00, in English. Judges stop watching at 3:00.
- It shows the working product, not slides, end to end, with **live Meta model calls visible**. Show briefly where and how Meta's models are used.
- **Open with one line on what existed before the event and what was built this week.**
- An AI English voice-over is allowed, but a video made and presented by a person is preferred.
- Most of the video must be real footage of the product running.
- No hosted URL needed. Judges need the public GitHub repo with setup instructions, plus the video.

## The story in one line
Muse proposes, physics disposes: Meta's Muse builds the simulator and designs the change, engineering engines check every round, failures go back to Muse, and the engineer signs the package.

## Recording setup
- 1920×1080, browser at 100 %, presentation mode once it exists (`?present=1`).
- Server: `WEB_ALLOW_RUNS=1 .venv/bin/python -m plantagent.web --port 8765`.
- **Live calls:**
  - The BASF loop runs live on Muse Spark Open, about 5 min, ~$0.60. Record it in full and speed up the waiting parts on screen, labelled "×8".
  - Record one live question on Muse (Meta API) on the salt plant (~$0.10–0.50), with the model name and cost visible.
- Keep the terminal or the page's AI-cost readout in frame once, so the calls are visibly live. No API keys on screen.
- Before recording, use a fresh copy of the BASF case so the live loop starts from Muse's first answer, not from the stored "done".

| Time | Screen | Voiceover |
|---|---|---|
| 0:00–0:08 | Title over the home page | "Before this event: no code. Everything you'll see, the agent, the engine integrations and the loop, was built this week, on Meta's Muse." |
| 0:08–0:20 | UCTE page: drag the slider, LAN–WEH turns red | "One switching action in 2006 split Europe's grid. Engineers check every plant change like this one by hand, for weeks. We gave it to Muse, with physics checking every step." |
| 0:20–0:45 | Scan page (salt patent FIG. I → 13 tags found → connections, with the 9 engineer corrections highlighted) | "Muse Wonder read this scanned 1994 patent drawing: all 13 equipment items, and most of the connections. The engineer corrected nine before anything was simulated, and both versions are kept." |
| 0:45–1:50 | **Live:** BASF column page, a drawing the tool had never seen. Type the goal "+20 % feed, pass every check" → Run full engineering. The strip fills: Muse Spark Open's proposal → server re-solve ✓ → checks: flooding 61 %, purity ✓, envelope ✓, uncertainty ✓ → **Done**. Speed up the waits. Rev B cloud on the column. | "This is an official BASF drawing we had never used. No hand-written files. Live now, on Muse Spark Open, the open-weights model: it proposes a 600 mm column shell. DWSIM re-solves it, then every check runs: flooding, product purity, a +10 % feed case, uncertainty. Earlier rounds failed purity, and those numbers went back to Muse. This one passes. The only open item is the vendor confirming the new shell." |
| 1:50–2:15 | Salt plant: **live** question on Muse via the Meta API (e.g. "What limits +20 %?"); the answer appears with its model name and cost. Then the engineering-impact gates (Electrical ✕ TX-1 133 %) and the featured loop strip ending UNSOLVABLE | "On the salt plant, the design reaches 120 % in the simulator, but the electrical check fails: the transformer would be 133 % loaded. Asked to close the loop, Muse stops and names the data it needs, the vendor compressor curve, instead of guessing." |
| 2:15–2:40 | UCTE "refused, then solved" story: hosted refused ×4 | open-weights fix, lines go green, "N-1: 0 violations" | "For the blackout grid, Meta's hosted endpoint refused the prompt. Muse Spark Open, the open-weights model, ran the same loop and found a switching plan that holds every line and passes N-1." |
| 2:40–2:55 | `review.html`: the sign-off page with failed checks needing a disposition, then reviewer and approver | "The engineer gets a marked-up drawing and a change package to sign. Nothing is approved by the AI." |
| 2:55–3:00 | End card: repo URL, "Muse Wonder · Muse Spark · Muse Spark Open" | "PlantAgent. Muse proposes, physics disposes." |

## Before recording
- The Codex video work is merged: `?present=1`, the scan page and the UCTE story.
- `git status` is clean. After the live BASF run, either keep the new worklog as evidence or reset the case.
- Rehearse the live loop once; if Muse needs more than one round, keep it: red → back to Muse → green is the better shot.
