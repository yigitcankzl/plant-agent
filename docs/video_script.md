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
  - The voice request goes through Muse Voice Transcribe live (cents).
  - The red-team panel replays the stored attacks; one live attack (~$0.13) can be fired from the panel if time allows.
- Keep the terminal or the page's AI-cost readout in frame once, so the calls are visibly live. No API keys on screen.
- Before recording, use a fresh copy of the BASF case so the live loop starts from Muse's first answer, not from the stored "done".

| Time | Screen | Voiceover |
|---|---|---|
| 0:00–0:08 | Title over the home page | "Before this event: no code. The agent, the engine integrations and the loop were all built this week, on Meta's Muse." |
| 0:08–0:25 | UCTE story: hosted endpoint refuses ×4 → Muse Spark Open runs the same loop → the switching plan → lines go green, "N-1: 0 violations" | "2006: one switching action split Europe's grid. We asked Meta's hosted model to find a safe plan; it refused. Muse Spark Open, the open-weights model, ran the same engineering loop, and a power-flow engine checked every plan it proposed. This one holds every line, even with any single line lost." |
| 0:25–0:35 | BASF column page. The engineer presses the mic and says "Twenty percent more feed. Pass every check." Muse Voice Transcribe types it into the goal box | "An official BASF drawing we had never used. I say what I need; Muse Voice writes it down." |
| 0:35–0:55 | Cut-in of the stored round (`work/20261101-214001`, labelled "earlier run"): Muse cuts reflux to save energy → purity check ✕ (minimum reflux 1.10) → the numbers go back to Muse | "Muse's first idea was free: cut the reflux. The purity check failed it, with numbers, and those numbers went back to Muse. The model does not get to decide it passed." |
| 0:55–1:35 | **Live:** Run full engineering. The strip fills: Muse Spark Open proposes a 600 mm shell → server re-solve ✓ → flooding, purity, +10 % feed, uncertainty ✓ → **Done**. Waits sped up, labelled "×8". Rev B cloud on the column | "Live now, on open weights: Muse proposes a wider shell. DWSIM re-solves it and every check runs: flooding, product purity, a ten-percent feed swing, uncertainty. Done. The vendor still has to confirm the shell." |
| 1:35–2:05 | Red team panel on the same page: "Muse Spark 1.3 tries to break this design". Eight attack cards drop in (hot feed, cold feed, low pressure, fouled trays plus reflux…), flood bars fill, **8 / 8 held, worst 90 %** | "Then a second Muse attacks the design. It invents eight realistic bad days: hot feed, fouled trays, a pressure dip. DWSIM is the referee. The design holds all eight; the worst case uses ninety percent of the flood limit." |
| 2:05–2:25 | Scan page: the 1994 patent figure → equipment found by Muse → the engineer's corrections highlighted | "It also reads what plants actually have: a scanned 1994 drawing. Muse finds every equipment item; the engineer fixes the connections it missed, and both versions are kept." |
| 2:25–2:40 | Salt plant engineering-impact gates: Process ✓, Electrical ✕ "transformer 133 %" | "On a salt plant, the process answer looks fine, but the electrical check says the transformer would be overloaded. That is the finding a process-only tool misses." |
| 2:40–2:55 | `review.html`: failed checks need a disposition, then reviewer and approver | "The engineer gets a marked-up drawing and a change package to sign. Nothing is approved by the AI." |
| 2:55–3:00 | End card: repo URL, "Muse Spark · Muse Spark Open · Muse Wonder · Muse Voice" | "PlantAgent. Muse proposes, physics disposes." |

## Before recording
- The Codex video work is merged: `?present=1`, the scan page and the UCTE story.
- `git status` is clean. After the live BASF run, either keep the new worklog as evidence or reset the case.
- Rehearse the live loop once; if Muse needs more than one round, keep it: red → back to Muse → green is the better shot.
