# Demo video: 2:50 (hard limit 3:00)

## Organiser rules (Nov 1)
- At most 3:00, in English; judges stop at 3:00. Aim for 2:45–2:50.
- Working product, not slides, with **live Meta model calls visible**; show where Meta's models are used.
- **Open with one line on what existed before the event and what was built this week.**
- A person presenting is preferred over an AI voice-over. Most of the video is real footage of the product.
- No hosted URL needed: public GitHub repo with setup instructions, plus the video.

## Recording setup
- Everything is scripted in `/home/kizil/Desktop/hackathon/video` (outside the repo): `record.js` films each scene at 1920×1080 with Playwright from the real app; `cut.json` + `cut.py` trim, punch in (1.5–2× crops), add large captions and the speed badge, and concatenate; `voice.wav` (or `voice/v01.wav` … `v08.wav`) is laid over the cut. Re-shoot after any UI change: `node record.js` then `python3 cut.py`.
- Stored scenes use the plain server `.venv/bin/python -m plantagent.web --port 8765`.
- The live scene is a real run recorded on 4 Nov: `work/20261104-163619`, Muse Spark Open on Baseten, no earlier answers (`PLANT_FRESH=1`), neutral goal "Twenty percent more feed. Pass every engineering check.": 4 rounds, purity and envelope failures fed back, then every simulation check passed; 774 s, $1.36. Shown at ×27 with a visible badge. The BASF simulator model was built from the drawing earlier (1 Nov); the live session starts with no earlier answers. Never call a stored replay live.
- Run one heavy job at a time (14 GB RAM).

## Script (2:48; problem → what Muse did → what the calculation said → the decision)

On screen there are no subtitles: short labels sit next to the highlighted item, the chapter name is in the window bar. Rule for the voice: at most one technical term per sentence; the screen carries DWSIM, N-1, purity and vendor details. Everything is narrated by one voice; the 0:57 line is the same person speaking the goal into the product (recording: ~/Desktop/meta1.flac, already placed in the cut).

| Time | Screen | Caption | Narration |
|---|---|---|---|
| 0:00–0:08 | Salt drawing, full sheet | BUILT FROM ZERO DURING THE EVENT · For process engineers · Meta's Muse proposes plant changes, simulators check them | "This plant change met its production target. PlantAgent still blocked it: the transformer reached 133 percent. PlantAgent, built from zero during this event, lets Meta's Muse propose the change and makes real engineering software prove whether it works." |
| 0:08–0:15 | Model & data (built by Muse Wonder in 1096 s) | Muse Wonder drafted the first DWSIM model from US Patent 5,366,514 · 1,096 s · $4.03 | "Muse Wonder turned this patent flowsheet into a first draft simulation, in eighteen minutes, for four dollars." |
| 0:15–0:25 | K-201 on the drawing | Today's plant at +20 %: K-201 at 120 % of its limit | "The goal is twenty percent more output. At that rate, the main compressor would run twenty percent beyond its rating." |
| 0:25–0:37 | Existing → Draft design, K-202 and the What-changed list | Rev B, drafted with an engineer · 3 changes · DWSIM re-solves at 120 % | "With an engineer, Muse drafts three changes: clean the heater, add a second compressor, and trim a steam flow. The plant model recalculates, and the target is met." |
| 0:37–0:57 | Salt Decision page, the Result line; hold 3 s in silence | Throughput check: 120 % ✓ → TRANSFORMER 133 % (illustrative rating) — APPROVAL BLOCKED | "But another check catches a hidden problem: on an illustrative rating, the transformer reaches one hundred and thirty-three percent. … The change cannot be approved." |
| 0:57–1:06 | BASF Run page: the engineer speaks into the mic; Muse Voice's real transcript lands in the goal box | The engineer speaks the goal · Muse Voice transcribes it | (the engineer, into the mic:) "With twenty percent more feed, you should pass every engineering check." |
| 1:06–1:42 | Recorded live run with the same goal, agent log at ×38, round ladder in captions | Round 1 studies · Round 2 ✕ product quality · Round 3 ✕ flooded at high feed · Round 4 ✓ modelled checks passed, ○ vendor tray rating open | "Here is a recorded live run with that goal, on BASF's official DEXPI drawing, with an illustrative process duty. Muse Spark Open lowers the reflux; the simulator rejects it, because product quality falls. It tries a reflux between the two; now the column floods on a high-feed day. On round four, high-capacity trays pass the modelled checks; the tray rating still needs a vendor. Four rounds, thirteen minutes, one dollar thirty-six." |
| 1:42–1:53 | BASF Evidence page, red team on that design | A second Muse attacked that design · 7 / 7 bounded deviations held · worst 96 % of the flood limit | "Then a second Muse attacked that same design with seven bounded operating deviations. The simulator checked each one; all seven held." |
| 1:53–2:09 | Shell Norco: overview, then the blind comparison table | REAL PLANT, BLIND · Same revamp type as Shell: high-capacity trays in the existing shell · 5 match · 3 partial · 1 miss · 1 not predicted | "Now a real plant, tested blind. Muse saw only Shell's data from before the upgrade, and chose the same type of revamp Shell built: high-capacity trays in the existing column. Against Shell's measured results: five match, three partial, one miss, one not predicted." |
| 2:09–2:22 | UCTE 2006 open-weights story view | Hosted endpoint: blocked by content policy · Muse Spark Open: completed the checked engineering loop · N-1: 0 violations | "On a reduced reconstruction of the 2006 European grid, the hosted endpoint was blocked by content policy; Spark Open finished the loop, and every simulated single-line outage stayed within limits." |
| 2:22–2:35 | review.html?case=salt_mvr, failed checks with disposition fields | Every failed check needs a disposition · the AI never approves its own change | "PlantAgent never approves its own work. Every failed check needs a written response, a reviewer, and a separate approver." |
| 2:35–2:48 | Home page; last 5 s without narration | Proof wall: BASF live 4 rounds · 2 rejections · $1.36 · red team 7/7 · Shell Norco same revamp type · Salt 133 % caught · github.com/yigitcankzl/plant-agent | "Muse proposes. Physics checks. Engineers approve. (then silence)" |

Reading tips for the narrator: about 140 words per minute, calm; level about -16 LUFS, peaks -1 dB, no music; pause where "…" is written; numbers as words ("one hundred and thirty-three percent").

## Do not say
"Every check passed", "the design is safe", "Muse approved / verified the design", "the patent model was calibrated to 100 %", "the red team proves safety", "Muse reproduced Shell exactly", "the 600 mm shell is vendor-sized".

Say instead: "process screens passed", "vendor confirmation remains open", "stored bounded scenarios passed", "draft recommendation", "screening model".

## Likely judge questions
- **Does DWSIM do the real work?** Muse reads the drawing, chooses the tools, proposes the physical change and revises it from the numerical failures; the deterministic engines only referee.
- **Is 600 mm already on the drawing?** One section is; the demo sweeps a whole-shell replacement and the duty is assumed, so the result is a screening recommendation, not a vendor-confirmed design.
- **Does the red team prove safety?** No: seven bounded operating scenarios, not HAZOP, dynamics, relief sizing or mechanical approval.
- **What if the model is wrong?** Sources, assumptions, missing data and open discipline gates stay visible; a separate engineer and approver decide.
- **Why is Meta central?** Muse Voice takes the goal, Spark Open runs the engineering loop, Spark 1.3 writes the adversarial scenarios, Wonder reads drawings; the engines test what Meta's models propose.
