"""An engineering study done the way a consulting engineer does it, in eight steps.

1 scope & criteria  2 data collection & RFI  3 calibration  4 hydraulic model  5 capacity analysis
6 alternatives  7 independent QA/QC  8 deliverables (memo, model.inp, calc appendix, findings)

Usage: python -m plantagent.study --case roseburg [--model muse-spark-1.3-contributor]
"""
import argparse
import json
import time
from pathlib import Path

from . import llm, sim
from .docs import Case
from .deliver import write_deliverables

RULES = """Engineering rules:
- Never compute hydraulics, energy or velocities yourself. Use run_hydraulics and velocity; quote their outputs.
- Every number must cite a page (p.N) or be labelled ASSUMPTION with a reason. Never invent data silently.
- Some recommendation clauses in the document are withheld; reach your own conclusions from the facts.
- Use the document's units. Firm capacity = capacity with the largest unit of a station out of service.
- Give every run_hydraulics call a short unique label; later steps refer to runs by label."""

DOC_TOOLS = [
    {"type": "function", "function": {"name": "search_pages", "description": "Keyword search over the available pages; returns page numbers.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_page", "description": "Read the text of one page.",
     "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}, "required": ["page"]}}},
    {"type": "function", "function": {"name": "view_page", "description": "Look at a page as an image (figures, curves, drawings, scanned tables).",
     "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}, "required": ["page"]}}},
]
SIM_TOOLS = [
    {"type": "function", "function": {"name": "run_hydraulics",
     "description": "Run an EPANET steady-state simulation and log it under `label`. Spec: " + json.dumps(sim.SPEC_HELP),
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "purpose": {"type": "string"},
                    "spec": {"type": "object"}}, "required": ["label", "spec"]}}},
    {"type": "function", "function": {"name": "velocity",
     "description": "Mean velocity. US: flow in mgd with diameter (in) or area (ft2) -> fps. SI: flow in l/s with diameter (mm) or area (m2) -> m/s. `openings` divides the flow.",
     "parameters": {"type": "object", "properties": {"flow": {"type": "number"}, "diameter": {"type": "number"}, "area": {"type": "number"},
                    "openings": {"type": "integer"}, "units": {"type": "string", "enum": ["US", "SI"]}}, "required": ["flow"]}}},
]


def unstring(v):
    """The model sometimes sends nested objects/arrays as JSON strings; decode them."""
    if isinstance(v, str) and v[:1] in "[{":
        try:
            return unstring(json.loads(v))
        except json.JSONDecodeError:
            return v
    if isinstance(v, dict):
        return {k: unstring(x) for k, x in v.items()}
    if isinstance(v, list):
        return [unstring(x) for x in v]
    return v


def submit(name, description, properties, required):
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required}}}


ARR = lambda props: {"type": "array", "items": {"type": "object", "properties": props}}  # noqa: E731
S, N, B = {"type": "string"}, {"type": "number"}, {"type": "boolean"}

SUBMIT_COLLECT = submit("submit_collection", "Steps 1-2: design criteria, data register and RFI.", {
    "criteria": {"type": "object", "properties": {
        "question": S, "definitions": ARR({"term": S, "definition": S, "source": S}),
        "criteria": ARR({"name": S, "value": S, "source": S}), "standards": ARR({"name": S, "use": S})}},
    "units_on_path": {"type": "array", "items": S},
    "data_register": ARR({"id": S, "item": S, "value": S, "unit": S, "source": S, "quote": S}),
    "rfi": ARR({"item": S, "issue": S, "resolution": S, "reason": S}),
}, ["criteria", "data_register", "rfi"])

SUBMIT_ANALYSIS = submit("submit_analysis", "Steps 3-6: calibration, model, capacity table, alternatives, findings.", {
    "calibration": ARR({"test": S, "source": S, "measured": S, "simulated": S, "residual_pct": N, "run_label": S, "note": S}),
    "base_model_run": {"type": "string", "description": "label of the calibrated existing-conditions run"},
    "capacity_table": ARR({"unit": S, "limit": S, "binds_at": S, "limits_target": B, "evidence": S}),
    "alternatives": ARR({"unit": S, "option": S, "run_label": S, "result": S, "meets_target": B,
                         "cost_class": {"type": "string", "enum": ["<$100k", "$100k-$1M", "$1M-$10M", ">$10M", "n/a"]},
                         "cost_basis": S, "recommended": B}),
    "findings": ARR({"unit": S, "limits_target": B, "limiting_value": S, "evidence": S, "modification": S}),
    "assumptions": {"type": "array", "items": S},
}, ["calibration", "capacity_table", "alternatives", "findings"])

SUBMIT_REVIEW = submit("submit_review", "Step 7: QA/QC review result.", {
    "checked_runs": {"type": "array", "items": S}, "checked_citations": {"type": "array", "items": S},
    "issues": ARR({"severity": {"type": "string", "enum": ["major", "minor"]}, "item": S, "issue": S, "evidence": S}),
}, ["issues"])

SUBMIT_RESOLUTION = submit("submit_resolution", "Respond to every QA/QC issue and give the final findings.", {
    "responses": ARR({"issue": S, "action": {"type": "string", "enum": ["fixed", "rejected", "noted"]}, "explanation": S}),
    "findings": SUBMIT_ANALYSIS["function"]["parameters"]["properties"]["findings"],
    "alternatives": SUBMIT_ANALYSIS["function"]["parameters"]["properties"]["alternatives"],
}, ["responses", "findings"])


class Study:
    def __init__(self, case, model):
        self.case, self.model = Case(case), model
        self.dir = Path("runs") / case / time.strftime("%Y%m%d-%H%M%S")
        self.dir.mkdir(parents=True)
        self.log = (self.dir / "log.jsonl").open("w")
        self.runs = {}  # label -> {purpose, spec, result}
        self.steps = 0

    # --- tools -------------------------------------------------------------------------------
    def call(self, name, a):
        c = self.case
        if name == "search_pages":
            return c.search(a["query"])
        if name == "read_page":
            return c.page(a["page"])
        if name == "view_page":
            return {"image": c.page_image(a["page"])}
        if name == "run_hydraulics":
            label = a.get("label") or f"run{len(self.runs) + 1}"
            if label in self.runs:
                label = f"{label}-{len(self.runs) + 1}"
            result = sim.run(a["spec"])
            self.runs[label] = {"purpose": a.get("purpose", ""), "spec": a["spec"], "result": result}
            return {"label": label, **result}
        if name == "rerun":
            r = self.runs[a["label"]]
            fresh = sim.run(r["spec"])
            return {"label": a["label"], "matches_logged_result": fresh == r["result"], "result": fresh, "spec": r["spec"]}
        if name == "velocity":
            return sim.velocity(**{k: v for k, v in a.items() if v is not None})
        raise ValueError(f"unknown tool {name}")

    def loop(self, phase, system, user, tools, submit_name, max_steps):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for step in range(max_steps):
            self.steps += 1
            if step == max_steps - 3:
                messages.append({"role": "user", "content": f"Step limit near. Call {submit_name} now with what you have."})
            msg = llm.complete(self.model, messages, tools=tools)
            self.log.write(json.dumps({"phase": phase, "step": step, "assistant": msg}) + "\n")
            if not msg["tool_calls"]:
                messages += [{"role": "assistant", "content": msg["content"] or ""},
                             {"role": "user", "content": f"Use the tools. Finish by calling {submit_name}."}]
                continue
            messages.append({"role": "assistant", "content": msg["content"] or "", "tool_calls": [
                {"id": t["id"], "type": "function", "function": {"name": t["name"], "arguments": t["arguments"]}}
                for t in msg["tool_calls"]]})
            images = []
            for t in msg["tool_calls"]:
                try:
                    args = unstring(json.loads(t["arguments"] or "{}"))
                except json.JSONDecodeError as e:
                    args, result = {}, {"error": f"arguments are not valid JSON: {e}"}
                else:
                    if t["name"] == submit_name:
                        self.log.write(json.dumps({"phase": phase, "submit": args}) + "\n")
                        self.log.flush()
                        print(f"  {phase}: submitted after {step + 1} steps")
                        return args
                    try:
                        result = self.call(t["name"], args)
                    except Exception as e:  # tool errors go back to the engineer, as they would in real work
                        result = {"error": f"{type(e).__name__}: {e}"}
                if isinstance(result, dict) and "image" in result:
                    images.append(result.pop("image"))
                    result = {"note": f"page {args.get('page')} image attached below"}
                print(f"  {phase}> {t['name']}({json.dumps(args)[:120]}) -> {json.dumps(result)[:140]}")
                self.log.write(json.dumps({"phase": phase, "tool": t["name"], "args": args, "result": result}) + "\n")
                messages.append({"role": "tool", "tool_call_id": t["id"], "content": json.dumps(result)})
            for url in images:
                messages.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]})
            self.log.flush()
        raise RuntimeError(f"{phase}: no {submit_name} after {max_steps} steps")

    # --- the eight steps -----------------------------------------------------------------------
    def run(self):
        c, t0 = self.case, time.time()
        llm.TAG = c.name
        usd0 = llm.spent(c.name)
        head = (f"Facility: {c.cfg['title']}\nSource: {c.cfg['source']}\nTask type: {c.cfg['task_type']}\n"
                f"Question: {c.question}\nAvailable pages: {c.pages}")
        print(f"[{c.name}] steps 1-2: scope, criteria, data collection")
        collect = self.loop("collect", "You are the lead engineer starting a study. " + RULES,
                            head + "\n\nRead the available pages. Define the design criteria (with sources), list every unit "
                            "on the flow path, and build the data register (every value with page and quote). List missing or "
                            "conflicting data as RFI items; resolve each as an explicit ASSUMPTION with a reason.",
                            DOC_TOOLS + [SUBMIT_COLLECT], "submit_collection", 30)

        print(f"[{c.name}] steps 3-6: calibration, model, capacity, alternatives")
        analysis = self.loop("analyse", "You are the lead engineer. " + RULES,
                             head + "\n\nYour steps 1-2 output:\n" + json.dumps(collect) +
                             "\n\nNow: (3) build the hydraulic model and calibrate it against every field test in the data "
                             "register, reporting residuals; (4) name the calibrated base run; (5) evaluate every unit against "
                             "the question; (6) for each limiting unit, verify 2-4 alternatives in the simulator and give an "
                             "order-of-magnitude cost class with its basis. Mark the recommended option.",
                             DOC_TOOLS + SIM_TOOLS + [SUBMIT_ANALYSIS], "submit_analysis", 45)

        print(f"[{c.name}] step 7: independent QA/QC")
        run_index = {k: v["purpose"] for k, v in self.runs.items()}
        checker_tools = DOC_TOOLS + SIM_TOOLS + [
            {"type": "function", "function": {"name": "rerun", "description": "Re-execute a logged simulation by label and compare with its logged result.",
             "parameters": {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}}},
            SUBMIT_REVIEW]
        review = self.loop("qaqc", "You are the independent checking engineer (QA/QC). You did not do this work. " + RULES +
                           "\nCheck: re-run at least 3 logged simulations, verify at least 5 citations against the pages, look "
                           "for unit errors, unsupported numbers, weak assumptions, missed units, and alternatives that were not "
                           "actually verified. Report issues; do not rewrite the study.",
                           head + "\n\nStudy under review:\n" + json.dumps({"collection": collect, "analysis": analysis}) +
                           "\n\nLogged runs (label: purpose):\n" + json.dumps(run_index), checker_tools, "submit_review", 25)

        resolution = {"responses": [], "findings": analysis["findings"]}
        if review.get("issues"):
            print(f"[{c.name}] step 7b: lead resolves {len(review['issues'])} QA/QC issues")
            resolution = self.loop("resolve", "You are the lead engineer answering the checker. " + RULES,
                                   head + "\n\nYour analysis:\n" + json.dumps(analysis) + "\n\nQA/QC issues:\n" +
                                   json.dumps(review["issues"]) + "\n\nFix what is right (re-run simulations where needed), "
                                   "reject what is wrong with a reason, then submit the final findings.",
                                   DOC_TOOLS + SIM_TOOLS + [SUBMIT_RESOLUTION], "submit_resolution", 20)
            analysis["findings"] = resolution["findings"]
            if resolution.get("alternatives"):
                analysis["alternatives"] = resolution["alternatives"]

        return self.deliver(collect, analysis, review, resolution, t0, usd0)

    def deliver(self, collect, analysis, review, resolution, t0, usd0, wall_s=None):
        c = self.case
        print(f"[{c.name}] step 8: deliverables")
        study = {"case": c.name, "facility": c.cfg["title"], "source": c.cfg["source"], "url": c.cfg.get("url"),
                 "question": c.question, "model": self.model, "collection": collect, "analysis": analysis,
                 "review": review, "resolution": resolution, "runs": self.runs}
        memo = llm.chat(self.model, [
            {"role": "system", "content": "You write technical memoranda for a consulting engineering firm. Use only facts and "
             "numbers present in the JSON; keep page citations (p.N) and run labels; label assumptions. Sections: Purpose; "
             "Background; Design Criteria; Data and Assumptions; Model Calibration; Capacity Evaluation (table); Alternatives "
             "(table with cost class); QA/QC Summary; Recommendations; Limitations. Markdown. Start with the line: "
             "'DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.'"},
            {"role": "user", "content": json.dumps({k: v for k, v in study.items() if k != "runs"})}])
        summary = {"case": c.name, "model": self.model, "llm_steps": self.steps, "simulations": len(self.runs),
                   "wall_time_s": round(wall_s if wall_s is not None else time.time() - t0), "cost_usd": round(llm.spent(c.name) - usd0, 4)}
        write_deliverables(self.dir, study, memo, summary)
        print(f"[{c.name}] done: {json.dumps(summary)} -> {self.dir}")
        return self.dir

    @classmethod
    def recover(cls, run_dir, model):
        """Rebuild a study whose deliverable step failed from its log (no new agent calls except the memo)."""
        run_dir = Path(run_dir)
        self = cls.__new__(cls)
        self.case, self.model, self.dir, self.runs, self.steps = Case(run_dir.parent.name), model, run_dir, {}, 0
        subs = {}
        for line in (run_dir / "log.jsonl").read_text().splitlines():
            e = json.loads(line)
            if "submit" in e:
                subs[e["phase"]] = unstring(e["submit"])
            elif e.get("tool") == "run_hydraulics" and isinstance(e["result"], dict) and "label" in e["result"]:
                r = dict(e["result"])
                self.runs[r.pop("label")] = {"purpose": e["args"].get("purpose", ""), "spec": unstring(e["args"]["spec"]), "result": r}
            elif "assistant" in e:
                self.steps += 1
        analysis, review = subs["analyse"], subs.get("qaqc", {"issues": []})
        resolution = subs.get("resolve", {"responses": [], "findings": analysis["findings"]})
        analysis["findings"] = resolution["findings"]
        if resolution.get("alternatives"):
            analysis["alternatives"] = resolution["alternatives"]
        started = time.mktime(time.strptime(run_dir.name, "%Y%m%d-%H%M%S"))
        wall = (run_dir / "log.jsonl").stat().st_mtime - started
        self.log = open(run_dir / "recover.log", "w")
        return self.deliver(subs["collect"], analysis, review, resolution, started, llm.spent(self.case.name), wall)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--case")
    ap.add_argument("--model", default="muse-spark-1.3-contributor")
    ap.add_argument("--recover", help="run dir whose deliverable step failed")
    a = ap.parse_args()
    if a.recover:
        Study.recover(a.recover, a.model)
    else:
        Study(a.case, a.model).run()
    print(f"spent ${llm.spent():.4f} of ${llm.BUDGET_USD}")
