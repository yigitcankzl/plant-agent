# Submission form answers (Cerebral Valley)

**Team name:** PlantAgent

**Track:** Indie developer

**Problem statement:** Push the Frontier

**Most Viral X post:** (only if posted)

## Project description
PlantAgent is an engineering workspace for changing an existing plant. An engineer gives it a drawing (DEXPI P&ID, scanned PDF or patent figure) and a goal such as "+20 % feed, pass every check". Meta's Muse builds a working simulator from the drawing, finds what limits the plant, and proposes a change. Deterministic engines then check every proposal: DWSIM (process), pandapower (grid), WaterTAP (desalination), and electrical, start-up, purity, operating-envelope and uncertainty checks. Every failed number goes back to Muse for the next round. The result is a marked-up drawing (Rev B) and a change package that the engineer reviews and signs. The AI never approves anything.

Muse proposes, physics disposes. The problem: checking a plant change today takes engineers weeks of manual simulation and cross-discipline review, and an AI answer that only looks right is dangerous in a plant. PlantAgent makes the AI's answer checkable.

What it has done:
- **An unseen BASF drawing.** The official BASF DEXPI drawing went from upload to a DWSIM column with no hand-written files. Over several loops Muse's proposals were failed by the purity and envelope checks. It ended with a 600 mm shell that passes every check; only the vendor confirmation is left open.
- **A scanned 1994 patent.** Muse Wonder read the patent drawing and built a calibrated simulator from it.
- **The UCTE 2006 grid split.** The hosted endpoint refused the prompt. Muse Spark Open, the open-weights model, found a switching plan that passes N-1.
- **A blind benchmark against real engineers.** Across 13 published engineering studies, with their conclusions withheld, Muse reached 64 % of the engineers' conclusions on average. A second Meta model graded the runs; this is a cross-model check, not a human one.

## Public GitHub repository
https://github.com/yigitcankzl/plant-agent

## 3-minute demo video
(YouTube link)

## Use of Meta products
- **Muse Wonder (Meta Model API):** vision and reasoning. It reads scanned P&IDs, patent figures and equipment datasheets, and builds the first simulator model from them.
- **Muse Spark 1.3 (Meta Model API):** the tool-calling engineer agent. It runs the simulators, answers engineering questions on the page, and proposes changes. It also acts as the cross-model grader in the blind benchmark.
- **Muse Spark Open (open weights, served on Baseten):** runs the same closed engineering loop with the same tools. It solved the UCTE grid case after the hosted endpoint refused it, and it ran the BASF loop that ended with every check passing. An optional "second model" check compares its answer with the hosted model's.

All calls go through one OpenAI-compatible client with a hard budget cap. Every answer in the UI shows its model, cost and time.

## Why Meta's models are important
The loop needs a model that can read engineering drawings, call tools reliably over 20–40 steps, and change its design when a deterministic check fails. Muse does all three in one family: Wonder for vision, Spark for long tool-calling sessions, and Spark Open for the same loop on open weights. Open weights matter in this domain. Plants are reluctant to send their drawings to a hosted API, and the UCTE case showed a hosted content filter blocking legitimate grid-safety work that the open model completed.

## Partner technology feedback (Baseten)
Baseten served Muse Spark Open through an OpenAI-compatible endpoint, so switching between hosted and open weights was a one-line model change. Long agent sessions (up to 40 tool steps) ran reliably. Wish list: per-request cost in the response, and clearer rate-limit headers for budgeting long loops.

## Opinion questions (your own answers; drafts below)
- **How likely to build with Meta Model API:** (your pick)
- **Overall opinion:** (your pick)
- **Recommend Meta Model API / Muse Code:** (your pick. We did not use Muse Code, so answer that one accordingly)
- **Biggest obstacle:** Getting the agent to follow the server's verification rules across rounds. In its own trial runs it edited a rated limit directly and re-set the feed rate, both of which the verifier refuses. We fixed this by surfacing the same rules inside its trial-run results. Separately, the hosted endpoint's content filter refused a legitimate grid-blackout analysis.
- **Compared with other models:** (your own experience)
- **What matters most when choosing:** reliable long tool calling, vision on technical drawings, cost per run, and an open-weights option.
- **Hardest to switch:** prompts and tool contracts tuned to one model's behaviour; re-validating the benchmarks.
- **What would stop production use:** on-premise or data-residency needs (open weights addresses this), hosted content filters on safety-critical engineering, and run-to-run variance on long loops.
