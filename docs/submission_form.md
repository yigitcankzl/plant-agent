# Submission form answers

Copy these into the Cerebral Valley form. The video and optional X links still need to be added.

**Team name:** PlantAgent

**Team members:** Yigitcan Kizil

**Track:** Indie developer

**Problem statement:** Push the Frontier

**Most Viral X post:** Leave blank unless we publish one.

## Project description

PlantAgent started with a question: if an engineer asks an AI whether a plant can run 20% harder, who checks the answer?

It is built for the process engineer who has to answer "can we change this?" before a management-of-change review. Plant changes usually fail across disciplines: the process works, then the electrical supply, the relief case or the operating envelope does not.

An engineer gives PlantAgent a process drawing, operating data and a target. Muse reads the source material, builds a draft simulator model, finds the bottleneck and proposes a physical change. It does not grade its own work. The proposal is applied to the model and re-solved by engineering tools such as DWSIM, pandapower and WaterTAP. When a check fails, Muse gets the failed number and tries again. Documented equipment ratings cannot simply be edited to make a design pass, and any missing vendor or field information stays visibly open for a person.

The result is not a chatbot answer. It is a Rev B drawing with the change clouded on the sheet, the calculations behind each check, a what-if slider on the live model, and a draft change package that moves through a reviewer and a separate approver. Approval freezes the reviewed files into a hash-chained audit record.

I tested this in several ways during the event:

- In a recorded run built around BASF's public DEXPI example drawing and an illustrative process model, Muse Spark Open tried four designs. The server rejected two of them before a high-capacity tray proposal passed the modelled checks. The vendor tray rating remains open.
- A second model, Muse Spark 1.3, then tried to break that BASF design with seven bounded operating deviations. DWSIM re-solved each one; all seven held, the worst at 96 % of the flood limit.
- In a blind study based on Shell Norco's published revamp, Muse saw only the before-state data. It chose the same broad revamp type used by the engineers: high-capacity trays in the existing column. Against the withheld after-data, five conclusions matched, three were partial, one missed and one was not predicted.
- In the salt-plant case, the process model reached the 120% target, but the illustrative electrical model put a transformer at 133%. PlantAgent therefore kept the design blocked instead of presenting the process result as a complete answer.
- On a reduced reconstruction of the 2006 European grid incident, the hosted endpoint refused the task under its content policy. Muse Spark Open completed the same checked loop, and the proposed switching passed every simulated single-line contingency.

Beyond these, the workspace holds 16 documented facilities across process plants, power grids and water systems, with 13 blind studies scored against engineers' published conclusions. Not everything passes: 23 of 71 recorded engineering runs ended with every check passing, and most of those still carry an open vendor or human item. I kept those numbers in the repository rather than showing only the best runs.

PlantAgent is engineering decision support, not autonomous approval. Its job is to make an AI proposal testable and to show exactly what still needs an engineer.

Try it: a hosted replay runs without any key at https://plantagent.63-182-151-178.sslip.io, or `git clone https://github.com/yigitcankzl/plant-agent && cd plant-agent && ./start.sh` (a Dockerfile is included). Live Muse calls use your own Meta API key.

## Public GitHub repository

https://github.com/yigitcankzl/plant-agent

## 3-minute demo video

Add the unlisted YouTube link here.

## Describe your use of Meta products

I used different Meta models for different parts of the engineering workflow:

- **Muse Wonder** reads drawings and data sheets and drafts the first simulator model, including its assumptions.
- **Muse Spark Open** runs the design loop. It proposes a change, reads the failed engineering checks and revises the design. I ran it through Baseten and Fireworks. The recorded BASF run and the UCTE grid run both use the open-weights model.
- **Muse Spark 1.3** acts as a second engineer. It proposes bounded operating deviations to challenge a design that has passed its normal checks.
- **Muse Voice Transcribe** turns the engineer's spoken target into the text that starts a run.

The language model proposes and explains; the configured engineering engines decide whether the numbers pass. The interface records the model, time and cost of each run, and final approval remains with a person.

## Why are Meta's models important to your solution?

This project needs more than a model that can write a plausible answer. It needs vision for technical drawings, reliable tool use over a long sequence and the ability to revise a design after a numerical check fails. The Muse family let me use one model family across those jobs.

The open-weights option is especially important for industrial work. Many plants cannot send drawings and operating data to a hosted service. It also gave me a practical fallback when the hosted endpoint refused a legitimate grid-safety prompt: the same engineering loop could still run with Muse Spark Open.

## Partner technology feedback

**Baseten:** Moving Muse Spark Open to Baseten required only a model-name change because the endpoint was OpenAI-compatible. Long tool-using sessions ran reliably. The main improvement I would ask for is clearer per-request cost and rate-limit information, which would make budgeting long agent runs easier.

**Fireworks:** Fireworks also made it straightforward to run the same open-weights model through an OpenAI-compatible endpoint. It was useful for the larger blind revamp benchmark because I could keep the same tools and prompts while changing providers.

## Opinion questions

Use the closest options offered by the form.

**How likely are you to build with Meta Model API?**  
Very likely / 9 out of 10.

**How would you describe your overall opinion of Meta Model API?**  
Very positive. The combination of drawing understanding, tool use and open weights was unusually useful for this project. The main rough edge was a hosted content-policy refusal on a legitimate grid-safety task.

**How likely are you to recommend Meta Model API?**  
8 out of 10.

**How likely are you to recommend Muse Code?**  
I did not use Muse Code, so select “not applicable” if the form offers it. Do not rate a product we did not test.

**What was the biggest obstacle your team hit?**  
The hardest part was keeping a long agent run inside engineering rules. Early runs tried to change a documented equipment limit or reset the feed rate to make a result pass. I fixed this by having the server reject those shortcuts and return the exact reason to the next round. A separate issue was the hosted endpoint refusing a legitimate grid-blackout analysis.

**Compared with other AI models, how did Meta's models perform?**  
Muse was strong at reading technical material and using tools over long runs. Spark Open was capable enough to complete real multi-round engineering tasks, and being able to run it through different providers was valuable. It was not perfectly consistent: some long runs needed retries or ended without a valid design, which is why PlantAgent never lets the model grade itself.

**When choosing an AI model or coding tool, what matters most?**  
Reliable tool use, technical vision, predictable cost and an open-weights deployment option. For this product, a confident answer is less useful than a model that can accept a failed calculation and revise its work.

**What makes switching models difficult?**  
The prompts and tool contracts become tuned to each model's behaviour. Switching is technically easy, but the engineering benchmarks have to be rerun before I can trust the new setup.

**What would most likely stop you from using Meta's models in production?**  
Data-residency requirements, false-positive content filtering on safety work and run-to-run variation in long agent sessions. Open weights helps with the first two, but production use would still require benchmark gates, cost controls and human approval.
