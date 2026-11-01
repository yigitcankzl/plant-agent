# Demo video: 3 minutes

Judges score the video as "genuinely cool to watch?" and the Meta AI criterion as "capabilities that surprised even us?". So the video needs one clear story (the loop), visible engines and drawings rather than chat, and three surprises: the loop catches what the process answer hides; a drawing it had never seen; the open model solves what the hosted endpoint refused.

Recording: 1920×1080, browser at 100 %, server `WEB_ALLOW_RUNS=1 .venv/bin/python -m plantagent.web --port 8765`. The replay URLs (`&replay=<id>`) play stored runs, so nothing waits on a model call. The voiceover is recorded separately and fits about 150 words a minute.

| Time | Screen | Voiceover |
|---|---|---|
| 0:00–0:15 | `home.html`, hero. Slow zoom on "Give it the change. It does the engineering." | "A plant engineer asked for 20 % more output spends weeks on it: build the model, find the limit, design the fix, then check the electrics, the compressor, the start-up. PlantAgent does that work with Meta's Muse, and shows every step." |
| 0:15–0:35 | `plant.html?case=salt_mvr`: the P&ID and the question on the strip. Click **Existing**: limits light up on K-201, V-201, V-301. | "This salt plant comes from a 1994 patent. Muse read the flowsheet and built the simulator model itself. The question: can it make 3,000 tons a day instead of 2,500? The model says the compressor is the first limit." |
| 0:35–1:20 | `&replay=20261101-214821`. Let round 1 play: Muse's four changes, each re-solved ✓; then the checks: process 120 % ✓, envelope 4/4 ✓, curves ✓, then the red rows: start-up voltage dip 46 %, surge at today's flow. Pause on a red row with its tag lit on the drawing. | "Muse proposes the changes: clean the heater, add a parallel compressor, upsize the transformer. Every change is re-solved in DWSIM before it counts, and a change that only edits a limit is refused. Then the engines run every check. The process passes. The electrical and start-up checks don't: starting the new compressor drops the voltage 46 %. A process answer alone would have said yes. The failed checks go back to Muse with their numbers, round after round." |
| 1:20–1:35 | **Proposed** view: Rev B clouds on the drawing; open the details drawer to the MOC package. | "What the engineer gets is a marked-up drawing, the checks with their sources, and a change package that says 'do not approve yet', and why." |
| 1:35–2:05 | `plant.html?case=basf_process_column_k_2750_dexpi_c02_uns`: the banner, then `&replay=20261101-214001` fast (2×), stopping on the purity rows ✓. | "Is it only our prepared demos? This is an official DEXPI drawing from BASF that we had never used. No hand-written files: the drawing is rendered from the file, Muse built the column, the discipline files were drafted and labelled as assumptions. A first fix, cutting reflux, failed the purity check. The next round kept purity and passed at 120 %." |
| 2:05–2:30 | `plant.html?case=ucte_2006`: the open-weights comparison card, then the N-1 row ✓. | "It isn't only process plants. For the 2006 European blackout, Meta's hosted endpoint refused the prompt. Muse Spark Open, the open-weights model, ran the same engineering loop on Baseten and found a switching plan that holds every line limit and passes N-1." |
| 2:30–2:50 | Assumptions panel: "Top 10 that change the answer"; then an open row "upload the real rating". | "Missing data is shown, not hidden: every value carries its source, and the ten assumptions that change the answer come first, for the engineer to confirm or replace with the vendor's data." |
| 2:50–3:00 | Back to the salt drawing, Rev B. Title card: "PlantAgent · built on Muse · github.com/yigitcankzl/plant-agent". | "Muse does the engineering. The engines check it. The engineer decides." |

## Checks before recording
- The salt loops are finished and their cache files restored (`git status runs/ws/salt_mvr` clean apart from new work folders).
- Pick the replay id that tells the story best once the Muse Wonder salt run is in; update the table above.
- Hide the browser bookmarks bar; dark OS theme; cursor highlight on.
- No API keys or `.env` on screen.
