# UX references: the engineering workspace

**Problem:** the plant page has to tell one story: "give it the change, the AI engineer works it in rounds, the engines check every round, you review the package". Today it reads as a dashboard of panels: a decision card, gate rings, a what-if band, a work log and an ask box, all on screen at once.

## References

### GitHub Copilot Workspace: task → spec → plan → implementation → review
- Everything starts from a natural-language **task**.
- The tool proposes a **specification**: success criteria for what must be true when the task is done, not implementation detail.
- The **plan** lists every file to touch. The user approves it, edits it, or rejects individual steps before anything is generated.
- **Implementation** follows. A **review** step checks the result in a terminal and iterates.
- Why it works: it is one linear story with an obvious checkpoint at each step. The human edits the plan, not the code.
- Sources: [official user manual](https://github.com/githubnext/copilot-workspace-user-manual/blob/main/overview.md), [review on DEV](https://dev.to/pickuma/github-copilot-workspace-review-task-level-ai-coding-in-the-browser-11d).

### Devin: session = step timeline + tool views (Shell, IDE, Browser) + Progress
- Each step of the agent is clickable. Selecting a step shows the state of the tools at that moment.
- "All shell commands, code edits, and browser activity will be logged in one unified view."
- You can scrub back to an earlier step to see what the agent tried.
- Why it works: you watch the agent work, and the big tool surface always shows the state behind the selected step.
- Sources: [Devin session tools docs](https://docs.devin.ai/work-with-devin/devin-session-tools.md), [guide](https://fast.io/resources/devin-session-tools-guide/).

### AVEVA Process Simulation: canvas + properties inspector + mini inspector + tree
- The flowsheet **canvas** is the main surface, with zoom-to-fit and an overview map.
- A **Properties Inspector** lets you view and edit the selected model in place. A **Mini Inspector** sits on the canvas, and a **Simulation Manager** tree shows the structure.
- Why it works: engineers expect the drawing to be the centre and the details of the selected item beside it.
- Source: [AVEVA docs: Build simulations](https://docs.aveva.com/bundle/process-simulation/page/3814.html).

## Options
- **A. Change request flow (Copilot Workspace).** One vertical flow: Change → success criteria (the checks) → Muse's plan (proposals) → rounds → package. The P&ID appears as a before/after diff inside the flow.
- **B. Engineering session (Devin + AVEVA).** Left: the change and the round-by-round step timeline (Muse / engine, ✓ / ✕). Right: the P&ID canvas, which shows the state of the selected step: the tags of a failed check highlighted, or the Rev B clouds of Muse's fix. The decision and package come at the end of the timeline. Details go in an inspector drawer.
