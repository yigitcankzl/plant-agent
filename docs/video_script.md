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
- The live scene is a real run recorded on 3 Nov: `work/20261103-214753`, Muse Spark Open on Baseten, no earlier answers (`PLANT_FRESH=1`), neutral goal "Twenty percent more feed. Pass every engineering check.": 4 rounds, purity and envelope failures fed back, then every simulation check passed; 919 s, $1.41. Shown at ×31 with a visible badge. The BASF simulator model was built from the drawing earlier (1 Nov); the live session starts with no earlier answers. Never call a stored replay live.
- Run one heavy job at a time (14 GB RAM).

## Script (2:19; one plant story, then the same loop live; the wow moment is the transformer block)

| Time | Screen | Big caption | Narration |
|---|---|---|---|
| 0:00–0:08 | Salt drawing, full sheet, Existing | For process engineers · Meta's Muse proposes a plant change, simulators check it | "Before this event there was no PlantAgent code. PlantAgent is for process engineers: Meta's Muse proposes a change to a plant drawing, and the simulators check it." |
| 0:08–0:18 | Punch-in 2× on K-201 | Today's plant at +20 %: K-201 at 120 % of its limit | "This salt plant should make twenty percent more. At that rate DWSIM shows the first limit: compressor K-201 at one hundred and twenty percent of its rating." |
| 0:18–0:30 | Existing → Draft design, Rev B clouds and the What-changed list | Rev B, drafted with an engineer · 3 changes · DWSIM re-solves at 120 % | "Working with an engineer, Muse drafts Rev B: clean the heater, add a parallel compressor K-202, trim the purge. DWSIM re-solves the whole plant at one hundred and twenty percent." |
| 0:30–0:50 | Salt Decision page, then punch-in on the Result line; hold 3 s in silence | Throughput check: 120 % ✓ → **TRANSFORMER 133 % (illustrative rating) — APPROVAL BLOCKED** | "The throughput check passes. … But the electrical answer is no: on an illustrative rating, transformer TX-1 reaches one hundred and thirty-three percent, and the design is not robust if the heater fouls again. Approval stays blocked." |
| 0:50–1:35 | Live run on BASF, fresh session, neutral goal; agent log at ×31; then the draft design | Round 1 … Round 2 **PURITY FAILS** … Round 3 **+10 % FEED CASE FAILS** … Round 4 every simulation check passes · tray rating: vendor to confirm; badge Meta Muse Spark Open on Baseten · RECORDED LIVE | "Now the loop live, in a fresh session on BASF's official DEXPI example, with a neutral goal. Muse Spark Open, Meta's open-weights model, first cuts the reflux. DWSIM says no: the bottoms purity fails its drafted spec. It raises the reflux; now the plus-ten-percent feed case floods. It adds high-capacity trays, and every simulation check passes; the tray rating is Muse's assumption, for the vendor to confirm. Four rounds, fifteen minutes, a dollar forty." |
| 1:35–1:49 | BASF Evidence page, red team, punch-in | Earlier: Muse Spark 1.3 attacked a 600 mm design · 8 / 8 HELD | "Earlier, a second model, Muse Spark 1.3, attacked a 600-millimetre design for the same column with eight bad operating days. DWSIM refereed, and all eight held." |
| 1:49–2:05 | `review.html?case=salt_mvr`, failed checks with disposition fields | Every failed check needs a disposition · the AI never approves its own change | "Every failed check needs a written disposition, a reviewer and a separate approver. The AI never approves its own change." |
| 2:05–2:19 | Home page | BASF live: 4 rounds · 2 rejections · $1.41 · Salt: 133 % overload caught (illustrative TX-1) | "Muse proposes. Physics checks. Engineers approve. PlantAgent is open source." |

Reading tips for the narrator: about 150 words per minute; pause where "…" is written; numbers as words ("one hundred and thirty-three percent").

## Do not say
"Every check passed", "the design is safe", "Muse approved / verified the design", "the patent model was calibrated to 100 %", "the red team proves safety", "Muse reproduced Shell exactly", "the 600 mm shell is vendor-sized".

Say instead: "process screens passed", "vendor confirmation remains open", "stored bounded scenarios passed", "draft recommendation", "screening model".

## Likely judge questions
- **Does DWSIM do the real work?** Muse reads the drawing, chooses the tools, proposes the physical change and revises it from the numerical failures; the deterministic engines only referee.
- **Is 600 mm already on the drawing?** One section is; the demo sweeps a whole-shell replacement and the duty is assumed, so the result is a screening recommendation, not a vendor-confirmed design.
- **Does the red team prove safety?** No: eight bounded operating scenarios, not HAZOP, dynamics, relief sizing or mechanical approval.
- **What if the model is wrong?** Sources, assumptions, missing data and open discipline gates stay visible; a separate engineer and approver decide.
- **Why is Meta central?** Muse Voice takes the goal, Spark Open runs the engineering loop, Spark 1.3 writes the adversarial scenarios, Wonder reads drawings; the engines test what Meta's models propose.
