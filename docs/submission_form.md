# Submission form answers (Cerebral Valley)

**Team name:** Yigitcan Kizil

**Track:** Indie developer

**Bonus categories we target:** Best Agentic Use-Case; Best Build on Meta Open Weight Models

**Problem statement:** Push the Frontier

**Most Viral X post:** (only if posted)

## Project description
PlantAgent is an engineering workspace for changing an existing plant. An engineer gives it a drawing (DEXPI P&ID, scanned PDF or patent figure) and a goal such as "+20 % feed, pass every check". Meta's Muse builds a working simulator from the drawing, finds what limits the plant, and proposes a change. Deterministic engines then check every proposal: DWSIM (process), pandapower (grid), WaterTAP (desalination), and electrical, start-up, purity, operating-envelope and uncertainty checks. Every failed number goes back to Muse for the next round. The result is a marked-up drawing (Rev B) and a change package that the engineer reviews and signs. The AI never approves anything.

Muse proposes, physics disposes. The problem: checking a plant change today takes engineers weeks of manual simulation and cross-discipline review, and an AI answer that only looks right is dangerous in a plant. PlantAgent makes the AI's answer checkable.

What it showed (every item links to its record in the repository):
- **A live loop that is wrong twice.** On BASF's official DEXPI example, Muse Spark Open ran four rounds from a neutral goal: the simulator rejected two designs (product quality, then flooding on a high-feed day), and high-capacity trays then passed every modelled check. 13 minutes, $1.36; the tray rating stays open for a vendor.
- **A second model attacks the design.** Muse Spark 1.3 attacked that design with seven bounded operating deviations; DWSIM re-solved each and all seven held (worst 96 % of the flood limit).
- **A real plant, blind.** From Shell Norco's pre-revamp data only, Muse chose the same revamp type Shell built (high-capacity trays in the existing column). Against Shell's measured after-data: 5 match, 3 partial, 1 miss, 1 not predicted.
- **Process passing is not enough.** On a salt plant the process target passed at 120 %, but an illustrative transformer rating reached 133 %, so approval stays blocked.
- **Open weights.** On the 2006 European blackout grid the hosted endpoint was blocked by content policy; Muse Spark Open completed the checked loop with 0 N-1 violations.
- **Honest denominator.** 21 of 69 recorded loop runs ended with every deterministic check passing; most of those still carry an open vendor or human check.

## Public GitHub repository
https://github.com/yigitcankzl/plant-agent

## 3-minute demo video
(YouTube link)

## Use of Meta products
Each Meta model has a separate job; the deterministic engines (DWSIM, pandapower and others), not the language model, decide pass or fail, and only an engineer approves.
- **Muse Wonder** reads engineering drawings (DEXPI, scanned PDF, patent figure) and drafts the first simulator model, listing every assumption.
- **Muse Spark Open** (open weights, on Baseten and Fireworks) runs the iterative design loop: it proposes a physical change, reads the failed checks with their numbers, and revises. It is load-bearing: the recorded live BASF run and the UCTE grid run used it.
- **Muse Spark 1.3** red-teams a passing design with bounded operating deviations, and answers engineering questions on the page.
- **Muse Voice Transcribe** turns the engineer's spoken goal into the goal text.

All model calls share one budgeted client layer and usage ledger: chat and tool calls use the OpenAI-compatible endpoints of Meta, Baseten and Fireworks; SAM and Voice use Meta's native endpoints. The `openai` package is only the transport SDK; no OpenAI model is called. Every answer in the UI shows its model, cost and time.

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
