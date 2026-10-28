"""Process-plant workspace: the agent reads a smart P&ID (DEXPI) and the operating data sheet, builds the DWSIM model
itself, then answers the engineer's questions with simulator-verified proposals the engineer accepts or rejects.
"""
import copy
import hashlib
import json
import time
from pathlib import Path

from . import llm, pid, process
from .docs import DATA
from .study import ARR, Study, submit

ROOT = Path(__file__).resolve().parent.parent
S, N, B = {"type": "string"}, {"type": "number"}, {"type": "boolean"}

RULES = ("Rules: every number comes from the P&ID (cite the tag and attribute), the operating data sheet (cite the row), or a "
         "logged simulator run (cite its label). Never invent equipment ratings. State each assumption. Use the simulator, not "
         "your own arithmetic, for temperatures, duties, areas and capacity.")

SUBMIT_MODEL = submit("submit_model", "The process model you built and calibrated.", {
    "label": {"type": "string", "description": "label of the calibrated run_process run (the model)"},
    "mapping": ARR({"tag": S, "modelled_as": S, "source": S}),
    "calibration": ARR({"item": S, "measured": S, "simulated": S, "source": S}),
    "assumptions": {"type": "array", "items": S},
}, ["label", "mapping", "calibration"])

ANSWER = submit("answer", "Final answer, shown on the P&ID and as calc cards (not as chat).", {
    "headline": {"type": "string", "description": "the answer in at most 8 plain words, e.g. 'No - cooler H1007 limits at +17%'"},
    "summary": {"type": "string", "description": "at most 2 plain sentences with the key numbers and their sources"},
    "cards": ARR({"title": S, "result": {"type": "string", "description": "headline value(s) with units, at most 14 words"},
                  "inputs": ARR({"name": S, "value": S, "source": S}), "runs": {"type": "array", "items": S},
                  "assumptions": {"type": "array", "items": S},
                  "status": {"type": "string", "enum": ["ok", "warn", "fail", "info"]}}),
    "highlights": ARR({"tag": {"type": "string", "description": "equipment tag on the P&ID, e.g. H1007"}, "text": S,
                       "severity": {"type": "string", "enum": ["ok", "warn", "fail", "info"]}}),
    "proposals": {"type": "array", "description": "fixes, each a change to the model; the workspace re-solves it in DWSIM before "
                  "the engineer can accept it", "items": {"type": "object", "properties": {
                      "title": S, "tag": S,
                      "changes": ARR({"path": {"type": "string", "description": "feeds.<stream>.<field> | units.<id>.<field> | limits.<id>.<field>"},
                                      "value": N}),
                      "cost_class": {"type": "string", "enum": ["no capex", "<$100k", "$100k-$1M", ">$1M"]},
                      "why": S}}},
}, ["headline", "summary", "cards"])


def patch(spec, changes):
    """Apply dotted-path changes to a copy of the spec. Installed HX area also moves the area limit (same plates)."""
    s = copy.deepcopy(spec)
    units = {u["id"]: u for u in s["units"]}
    for c in changes:
        kind, oid, field = c["path"].split(".", 2)
        if kind == "units":
            units[oid][field] = c["value"]
            if field == "area_m2" and oid in (s.get("limits") or {}):
                s["limits"][oid]["area_m2"] = c["value"]
        elif kind == "feeds":
            s["feeds"][oid][field] = c["value"]
        elif kind == "limits":
            s.setdefault("limits", {}).setdefault(oid, {})[field] = c["value"]
        else:
            raise ValueError(f"bad path {c['path']}")
    return s


class PlantWorkspace(Study):
    def __init__(self, case_name, model="muse-spark-1.3-contributor"):
        self.name, self.model = case_name, model
        self.cfg = json.loads((ROOT / "cases" / case_name / "case.json").read_text())
        self.pid = pid.overview(DATA / self.cfg["pid"])
        self.basis = (ROOT / "cases" / case_name / self.cfg["basis"]).read_text()
        self.dir = ROOT / "runs" / "ws" / case_name / time.strftime("%Y%m%d-%H%M%S")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log = (self.dir / "log.jsonl").open("w")
        self.steps, self.listener, self.answers, self.revisions = 0, None, [], []
        self.runs = {}
        self.model_file = ROOT / "runs" / "ws" / case_name / "model.json"
        self.built = json.loads(self.model_file.read_text()) if self.model_file.exists() else None
        if self.built:
            self.runs[self.built["label"]] = {"spec": self.built["spec"], "purpose": "calibrated model", "result": self.built.get("result")}
        self._state = {}

    @property
    def spec(self):
        return self.built["spec"] if self.built else None

    def emit(self, event):
        if self.listener:
            self.listener(event)

    def tools(self):
        f = lambda name, desc, props, req=(): {"type": "function", "function": {  # noqa: E731
            "name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": list(req)}}}
        return [
            f("read_pid", "The smart P&ID: equipment with design data and limits, connections (with inline valves), lines with fluid "
                          "codes, valves, control loops.", {}),
            f("read_data_sheet", "The operating data sheet: current operation, process requirements, equipment performance, utilities.", {}),
            f("run_process", "Solve a DWSIM flowsheet and log it under `label`. Returns stream T/P/flows, unit results and every "
                             "limit check (utilisation = value/limit). Spec: " + json.dumps(process.SPEC_HELP),
              {"label": S, "purpose": S, "spec": {"type": "object"}, "scale": {"type": "number", "description": "multiplies non-utility feeds"}},
              ["label", "spec"]),
            f("process_capacity", "Throughput multiple of a logged run at which the first stated limit reaches 100 %, and which.",
              {"label": S}, ["label"]),
            f("get_spec", "Full spec of a logged run (the calibrated model is preloaded), to copy and modify.", {"label": S}, ["label"]),
        ]

    def call(self, name, a):
        if name == "read_pid":
            return self.pid
        if name == "read_data_sheet":
            return {"text": self.basis}
        if name == "run_process":
            label = a.get("label") or f"run{len(self.runs) + 1}"
            label = f"{label}-{len(self.runs) + 1}" if label in self.runs else label
            r = process.run(a["spec"], float(a.get("scale") or 1.0))
            self.runs[label] = {"spec": a["spec"], "purpose": a.get("purpose", ""), "scale": a.get("scale") or 1.0, "result": r}
            return {"label": label, **r}
        if name == "process_capacity":
            r = self.runs[a["label"]]
            r["capacity"] = process.capacity(r["spec"])
            return {"label": a["label"], **r["capacity"]}
        if name == "get_spec":
            r = self.runs.get(a["label"])
            return {"label": a["label"], "spec": r["spec"]} if r else {"error": f"unknown label; logged: {list(self.runs)}"}
        raise ValueError(f"unknown tool {name}")

    def build(self):
        """The agent reads the P&ID and data sheet and builds + calibrates the DWSIM model itself."""
        t0, usd0 = time.time(), llm.spent()
        llm.TAG = "plant:" + self.name
        sub = self.loop("build", "You are a process engineer building a steady-state simulation model of a unit from its P&ID. " + RULES,
                        f"Unit: {self.cfg['title']}\n\nRead the P&ID and the operating data sheet. Build the DWSIM flowsheet "
                        "with run_process: every process equipment item on the main flow path as a unit with its P&ID tag as id, "
                        "utilities as feeds with utility: true, and `limits` holding EVERY rating and requirement you can cite "
                        "(pump rated flow and power from the P&ID, exchanger installed area and the outlet temperature the process "
                        "needs, frame limits, tank residence time, utility supply limits on the utility feed streams). Calibrate "
                        "against the measured temperatures in the data sheet and report measured vs simulated. Then call submit_model.",
                        self.tools() + [SUBMIT_MODEL], "submit_model", 14)
        run = self.runs.get(sub["label"]) or list(self.runs.values())[-1]
        self.built = {"label": sub["label"] if sub["label"] in self.runs else list(self.runs)[-1], "spec": run["spec"],
                      "result": run["result"], "mapping": sub.get("mapping"), "calibration": sub.get("calibration"),
                      "assumptions": sub.get("assumptions"), "model": self.model, "seconds": round(time.time() - t0),
                      "cost_usd": round(llm.spent() - usd0, 4), "at": time.strftime("%Y-%m-%d %H:%M")}
        self.model_file.write_text(json.dumps(self.built, indent=1))
        self._state = {}
        return self.built

    def verify(self, p):
        """Re-solve a proposal in DWSIM at the target throughput. It is verified when every limit of the equipment it targets
        is within 100 % and it pushes no other limit over 100 % that was within it before."""
        target = float(self.cfg.get("target_scale", 1.0))
        before = {(c["id"], c["check"]): c["utilisation"] for c in self.state(target)["checks"] if "utilisation" in c}
        spec = patch(self.spec, p.get("changes") or [])
        at = process.run(spec, target)
        cap = process.capacity(spec)
        over = [c for c in at["checks"] if c.get("utilisation", 0) > 1.0]
        tag = p.get("tag")
        own = [c for c in over if c["id"] == tag or any(c["id"] in ch["path"] for ch in p.get("changes") or [])]
        broke = [c for c in over if before.get((c["id"], c["check"]), 0) <= 1.0]
        return {"verified": not at["errors"] and not own and not broke, "fixes": tag, "still_over": own, "breaks": broke,
                "capacity_multiple": cap.get("capacity_multiple"), "limited_by": cap.get("limited_by"),
                "reaches_target": not over and not at["errors"], "over_limits_at_target": over, "target_scale": target}

    def ask(self, text, context=None):
        if not self.built:
            self.build()
        t0, usd0 = time.time(), llm.spent()
        llm.TAG = "plant:" + self.name
        brief = {"unit": self.cfg["title"], "target_throughput_multiple": self.cfg.get("target_scale"),
                 "model_label": self.built["label"], "model_mapping": self.built.get("mapping"),
                 "revisions": [r["title"] for r in self.revisions], "earlier_answers": [a["summary"] for a in self.answers[-4:]]}
        ans = self.loop("ask", "You are the process engineering copilot inside the engineer's P&ID workspace. The calibrated DWSIM "
                        "model is preloaded (get_spec, then modify and re-run). Answer quickly and precisely and finish with "
                        "`answer`: a plain headline, calc cards, highlights on P&ID tags, and for a fix, proposals as model "
                        "changes (paths into the spec) that respect every utility and frame limit in the data sheet. Prefer the "
                        "cheapest fix that works (operating changes, cleaning) before new equipment. Write for a non-specialist; "
                        "no acronyms in the headline. " + RULES,
                        json.dumps(brief) + "\n\nRequest: " + text + (f"\nContext: {json.dumps(context)}" if context else ""),
                        self.tools() + [ANSWER], "answer", 10)
        for k in ("cards", "highlights", "proposals"):
            ans[k] = ans.get(k) if isinstance(ans.get(k), list) else []
        for p in ans["proposals"]:
            for c in p.get("changes") or []:  # the value it replaces, for the diff view
                try:
                    k, oid, fld = c["path"].split(".", 2)
                    o = next(u for u in self.spec["units"] if u["id"] == oid) if k == "units" else self.spec.get(k, {}).get(oid, {})
                    c["from"] = o.get(fld)
                except (ValueError, StopIteration):
                    c["from"] = None
            try:
                p.update(self.verify(p))
            except Exception as e:  # noqa: BLE001 - a proposal that does not solve is shown as failed
                p.update(verified=False, error=f"{type(e).__name__}: {e}")
        if len(ans["proposals"]) > 1:  # the fixes together: does the unit then reach the target?
            try:
                both = self.verify({"changes": [c for p in ans["proposals"] for c in p.get("changes") or []]})
                ans["combined"] = {k: both[k] for k in ("reaches_target", "capacity_multiple", "limited_by", "over_limits_at_target")}
            except Exception as e:  # noqa: BLE001
                ans["combined"] = {"error": f"{type(e).__name__}: {e}"}
        logged = set(self.runs)
        ans["checks"] = [{"item": f"run {r}", "ok": r in logged} for c in ans["cards"] for r in (c.get("runs") or [])]
        ans.update(seconds=round(time.time() - t0), cost_usd=round(llm.spent() - usd0, 4), request=text)
        self.answers.append(ans)
        (self.dir / "answers.json").write_text(json.dumps(self.answers, indent=1))
        return ans

    def accept(self, p):
        v = self.verify(p)  # never trust the client's copy
        if not v["verified"]:
            raise ValueError("proposal does not verify in DWSIM: " + json.dumps(v["over_limits_at_target"])[:300])
        self.revisions.append({"rev": len(self.revisions) + 1, "title": p.get("title"), "changes": p["changes"],
                               "spec_before": self.built["spec"], "capacity_multiple": v["capacity_multiple"],
                               "at": time.strftime("%H:%M:%S")})
        self.built = {**self.built, "spec": patch(self.built["spec"], p["changes"])}
        self._state = {}
        return {**v, "revisions": self.revisions}

    def restore(self, rev):
        """Undo back to before revision `rev` (0 restores the built model)."""
        keep = [r for r in self.revisions if r["rev"] < rev]
        if len(keep) < len(self.revisions):
            self.built = {**self.built, "spec": self.revisions[len(keep)]["spec_before"]}
            self.revisions = keep
            self._state = {}
        return {"revisions": self.revisions}

    def state(self, scale=1.0):
        """Solved unit at a throughput multiple: what the P&ID view colours. Cached per spec and scale."""
        if not self.built:
            return None
        key = hashlib.sha1(json.dumps([self.spec, round(scale, 3)], sort_keys=True).encode()).hexdigest()
        if key not in self._state:
            self._state[key] = {"scale": scale, **process.run(self.spec, scale)}
        return self._state[key]

    def capacity(self):
        key = "cap:" + hashlib.sha1(json.dumps(self.spec, sort_keys=True).encode()).hexdigest()
        if key not in self._state:
            self._state[key] = process.capacity(self.spec)
        return self._state[key]


if __name__ == "__main__":
    s = {"units": [{"id": "H1", "type": "hx", "area_m2": 10}], "feeds": {"CW": {"m3_h": 20}}, "limits": {"H1": {"area_m2": 10}}}
    p = patch(s, [{"path": "units.H1.area_m2", "value": 12}, {"path": "feeds.CW.m3_h", "value": 26}])
    assert p["units"][0]["area_m2"] == 12 and p["limits"]["H1"]["area_m2"] == 12 and p["feeds"]["CW"]["m3_h"] == 26
    assert s["units"][0]["area_m2"] == 10
    print("ok")
