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
- The live scene is a real run recorded on 3 Nov: `work/20261103-183706`, Muse Spark Open on Baseten, no earlier answers (`PLANT_FRESH=1`), 246 s, $0.20, every simulation check passed. It is shown sped up with a visible badge "RECORDED LIVE · 246 s shown at ×12 · $0.20". Never call a stored replay live.
- Run one heavy job at a time (14 GB RAM).

## Script (one end-to-end story; the wow moment is the transformer block)

| Time | Screen | Big caption | Narration |
|---|---|---|---|
| 0:00–0:10 | Salt drawing, full sheet (`plant.html?case=salt_mvr`, Drawing page) | PlantAgent · AI proposes, physics decides | "Before this event there was no PlantAgent code. PlantAgent lets Meta's Muse propose a change to a real plant drawing, and makes the simulators prove it." |
| 0:10–0:22 | Punch-in 2× on K-201 | **K-201 · 100 %** · goal **+20 %** | "This salt plant should make twenty percent more. DWSIM already shows the first limit: compressor K-201 at one hundred percent." |
| 0:22–1:00 | Live run on BASF, agent log streaming, then the Draft design | RECORDED LIVE · 246 s at ×12 · $0.20 | "Here is the loop live, on a drawing Muse had never seen: BASF's official DEXPI example. Muse Spark Open, Meta's open-weights model, reads it, runs DWSIM itself and proposes a new 600-millimetre column shell. Then the server, not the model, re-solves the design: the target, purity, the plus-or-minus ten percent envelope and all 48 uncertainty samples pass. Two hundred forty-six seconds, twenty cents." |
| 1:00–1:15 | Salt: Existing → Draft design, Rev B clouds appear | Rev B · 3 changes · 120 % | "On the salt plant the change is drawn as Rev B: clean the heater, add a parallel compressor K-202, trim the purge. DWSIM re-solves the whole plant at one hundred and twenty percent." |
| 1:15–1:45 | BASF Evidence page, red team, punch-in on the result | **8 / 8 HELD** · worst 90 % of flood limit | "Then a second Muse model attacks the design with eight bounded bad days: hot feed, low pressure, fouled trays. DWSIM is the referee. All eight stay inside the modelled limits. This is robustness screening, not a safety approval." |
| 1:45–2:15 | Salt Decision page, punch-in on the result, hold 3 s in silence | **TRANSFORMER 133 % — APPROVAL BLOCKED** | "Back at the salt plant, the process answer is yes. … The electrical answer is no: the new compressor loads transformer TX-1 to one hundred and thirty-three percent. The process simulation passed, and approval stays blocked. A process-only answer would have said yes." |
| 2:15–2:35 | `review.html?case=salt_mvr`, failed checks with disposition fields | The AI never approves its own change | "Every failed check needs a written disposition, a reviewer and a separate approver. The AI never approves its own change; these are workflow records, not electronic signatures." |
| 2:35–2:50 | Home page | **+20 % · 246 s · $0.20 · 8/8 · 133 % caught** | "Twenty percent more, found in four minutes for twenty cents, attacked eight times, and an overload caught before approval. Muse proposes. Physics checks. Engineers approve." |

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
