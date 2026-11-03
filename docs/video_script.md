# Demo video: 2:50 (hard limit 3:00)

## Organiser rules (Nov 1)
- At most 3:00, in English; judges stop at 3:00. Aim for 2:45–2:50.
- Working product, not slides, with **live Meta model calls visible**; show where Meta's models are used.
- **Open with one line on what existed before the event and what was built this week.**
- A person presenting is preferred over an AI voice-over. Most of the video is real footage of the product.
- No hosted URL needed: public GitHub repo with setup instructions, plus the video.

## Recording setup
- 1920×1080, browser at 100 %. Stored scenes use presentation mode (`&present=1`); the live run is recorded in the normal view (presentation mode hides the goal box and run button).
- Server for the live run (Spark Open on Fireworks, no earlier answers):
  `PLANT_FRESH=1 COPILOT_MODEL=fireworks:accounts/fireworks/models/muse-spark-open WEB_ALLOW_RUNS=1 .venv/bin/python -m plantagent.web --port 8765`
- Run nothing else on the machine during the live run (other DWSIM loops slowed the 3 Nov rehearsal to 76 min and it ran out of budget).
- **Record the live run separately, before the final cut.** Keep it only if it really finishes; if it fails, record another real take. Speed up waits on screen, labelled "×8". If you fall back to the stored run, do not call it live.
- Use a detailed goal in the box (the voice line is short): "Twenty percent more feed. Pass every engineering check. Keep the existing column if it can be done; if not, replace it with a rated shell, vendor to confirm."

## Script

| Time | Screen | Narration |
|---|---|---|
| 0:00–0:08 | `home.html` | "Before this event, there was no PlantAgent code. This repository, its agent loop and its engineering integrations were built after kickoff." |
| 0:08–0:19 | `home.html`, hero | "AI can produce a plausible plant answer. In a plant, plausible is not enough. PlantAgent makes every proposed change face the simulators and the engineers." |
| 0:19–0:34 | `plant.html?case=basf_process_column_k_2750_dexpi_c02_uns`; click the mic next to *Engineering goal* and say the goal | "We upload BASF's official DEXPI example unchanged. Muse builds a screening model and labels the missing process duty as an assumption." Voice: "Twenty percent more feed. Pass every check." |
| 0:34–0:57 | BASF, evidence `evidence/generality-c02/README.md` table "Product purity added afterwards" | "An early Muse run cut reflux. It passed the checks available then. We added a purity guardrail and replayed it: 90.3 against 90.8 weight percent, and reflux 0.8 against a 1.10 minimum. We withdrew that design." |
| 0:57–1:30 | The recorded live run, ×8 on waits; model, time and cost visible in the worklog | "This is a real Muse Spark Open call. It proposes replacing the column with a uniform 600-millimetre shell. The server, not the model, applies the change and re-solves it. The target, draft purity, the plus-or-minus ten percent feed envelope and all 48 uncertainty samples pass. Vendor sizing and uncalculated disciplines remain open." (Say only what the take shows.) |
| 1:30–1:45 | `…&present=1`, *Proposed* view, Rev B cloud | "PlantAgent draws the Rev B cloud and records the calculation. This is a draft engineering recommendation, not an approved design." |
| 1:45–2:08 | Red-team panel, set *600 mm, envelope* | "A second Muse proposes eight bounded bad days: hot feed, low pressure and fouled trays. DWSIM is the referee. All eight stay inside the modelled process limits; the worst uses 90 percent of the flood limit. This is robustness screening, not a HAZOP or a safety approval." |
| 2:08–2:27 | `plant.html?case=salt_mvr&present=1`, *Proposed* | "Process simulation alone is not enough. On the salt plant DWSIM reaches 120 percent, but the illustrative electrical model loads the transformer to 133 percent. Engineering approval stays blocked." |
| 2:27–2:43 | `review.html?case=basf_process_column_k_2750_dexpi_c02_uns` | "Every failed and open item needs a disposition, a reviewer and a separate approver. The AI never approves the change. These are workflow records, not authenticated electronic signatures." |
| 2:43–2:50 | `home.html` | "Muse proposes. Physics disposes. Engineers approve. PlantAgent is open source." |

## Do not say
"Every check passed", "the design is safe", "Muse approved / verified the design", "the patent model was calibrated to 100 %", "the red team proves safety", "Muse reproduced Shell exactly", "the 600 mm shell is vendor-sized".

Say instead: "process screens passed", "vendor confirmation remains open", "stored bounded scenarios passed", "draft recommendation", "screening model".

## Likely judge questions
- **Does DWSIM do the real work?** Muse reads the drawing, chooses the tools, proposes the physical change and revises it from the numerical failures; the deterministic engines only referee.
- **Is 600 mm already on the drawing?** One section is; the demo sweeps a whole-shell replacement and the duty is assumed, so the result is a screening recommendation, not a vendor-confirmed design.
- **Does the red team prove safety?** No: eight bounded operating scenarios, not HAZOP, dynamics, relief sizing or mechanical approval.
- **What if the model is wrong?** Sources, assumptions, missing data and open discipline gates stay visible; a separate engineer and approver decide.
- **Why is Meta central?** Muse Voice takes the goal, Spark Open runs the engineering loop, Spark 1.3 writes the adversarial scenarios, Wonder reads drawings; the engines test what Meta's models propose.
