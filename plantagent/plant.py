"""Process-plant workspace: the agent reads a smart P&ID (DEXPI) and the operating data sheet, builds the DWSIM model
itself, then answers the engineer's questions with simulator-verified proposals the engineer accepts or rejects.
"""
import copy
import hashlib
import json
import time
from pathlib import Path

from . import audit, llm, pid, process
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


def coverage(pid_ov, spec):
    """Which P&ID equipment-to-equipment connections the model reproduces, and which equipment it leaves out."""
    tags = {e["tag"] for e in pid_ov["equipment"] if e["tag"]}
    units = {u["id"]: u for u in spec.get("units", [])}
    outs, ins = {}, {}
    for u in units.values():
        for k, d in (("in", ins), ("out", outs), ("cold", None), ("hot", None)):
            v = u.get(k)
            if k in ("cold", "hot") and v:
                ins.setdefault(v[0], []).append(u["id"]); outs.setdefault(v[1], []).append(u["id"])
            elif v and d is not None:
                for name in (v if isinstance(v, list) else [v]):
                    d.setdefault(name, []).append(u["id"])
    nxt = {}
    for st, srcs in outs.items():
        for a in srcs:
            nxt.setdefault(a, set()).update(ins.get(st, []))
    for u in units.values():  # a recycle hands its stream on to whoever reads the tear stream
        if u["type"] == "recycle":
            nxt.setdefault(u["id"], set()).update(ins.get(u["out"], []))

    def reaches(a, b):
        seen, todo = set(), [a]
        while todo:
            x = todo.pop()
            for y in nxt.get(x, ()):
                if y == b:
                    return True
                if y not in seen and y not in tags:  # pass through valves, mixers, splitters, recycles only
                    seen.add(y); todo.append(y)
        return False

    tag_of = lambda s: s.split("(")[0]  # noqa: E731
    rows = []
    for c in pid_ov["connections"]:
        a, b = tag_of(c["from"]), tag_of(c["to"])
        if a in tags and b in tags and a != b:
            relief = any("SafetyValve" in v for v in c["inline"])  # a relief path carries no normal flow
            rows.append({"from": a, "to": b, "lines": c["lines"], "relief_path": relief,
                         "modelled": a in units and b in units and reaches(a, b)})
    return {"connections": rows, "missing_connections": [r for r in rows if not r["modelled"] and not r["relief_path"]],
            "missing_equipment": sorted(tags - set(units))}


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
        self.rev_file = None
        self.runs = {}
        self.model_file = ROOT / "runs" / "ws" / case_name / "model.json"
        self.rev_file = self.model_file.with_name("revisions.json")
        self.built = json.loads(self.model_file.read_text()) if self.model_file.exists() else None
        if self.built and self.rev_file.exists():  # revisions survive restarts; the latest one is the current model
            self.revisions = json.loads(self.rev_file.read_text())
            if self.revisions:
                self.built["spec"] = self.revisions[-1]["spec_after"]
        if self.built:
            self.runs[self.built["label"]] = {"spec": self.built["spec"], "purpose": "calibrated model", "result": self.built.get("result")}
        self._state = {}
        # pick up the answers of the latest session made on this same model, so a restart keeps the engineer's thread
        for prev in sorted((ROOT / "runs" / "ws" / case_name).glob("2*/answers.json"), reverse=True):
            if prev.parent != self.dir and self.built and prev.stat().st_mtime > self.model_file.stat().st_mtime:
                self.answers = json.loads(prev.read_text())
                break

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
            f("check_coverage", "Compare a logged run's flowsheet with the P&ID: which equipment-to-equipment connections (by line "
                                "number) the model reproduces, which it misses, and which P&ID equipment it leaves out.",
              {"label": S}, ["label"]),
            f("relief_scan", "Deterministic scan of the P&ID: for each side of each equipment item, whether it reaches a relief "
                             "device without passing a valve that could be closed, and which heated sides could be blocked in.", {}),
            f("blocked_in_pressure", "DWSIM: pressure a liquid-full, blocked-in vessel reaches when heated from T1 to T2 "
                                     "(API 521 hydraulic expansion), for relief checks.",
              {"compounds": {"type": "array", "items": S}, "x": {"type": "object"}, "T1_C": N, "P1_bar": N, "T2_C": N},
              ["compounds", "x", "T1_C", "P1_bar", "T2_C"]),
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
        if name == "relief_scan":
            return pid.relief_scan(DATA / self.cfg["pid"])
        if name == "check_coverage":
            r = self.runs.get(a["label"])
            return coverage(self.pid, r["spec"]) if r else {"error": f"unknown label; logged: {list(self.runs)}"}
        if name == "blocked_in_pressure":
            return process.blocked_in(a["compounds"], a["x"], a["T1_C"], a["P1_bar"], a["T2_C"])
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
                        "with run_process, following the P&ID topology exactly: every process equipment item as a unit with its "
                        "P&ID tag as id, recirculation loops closed with a recycle unit, control valves that carry flow as valves "
                        "with their tags, utilities as feeds with utility: true. Where the site datasheets contradict P&ID "
                        "attributes, use the site data and list the conflict as an assumption; also act on the P&ID data_quality "
                        "warnings. Put in `limits` EVERY rating and requirement you can cite: pump rated and minimum flow, motor "
                        "power, NPSHr and relief set pressure; exchanger installed area with the outlet temperature the process "
                        "needs, frame limit and available pressure drop; tank hold time; product temperature limits; utility "
                        "supply limits on the utility feed streams. Calibrate against EVERY measured value in the data sheet "
                        "(temperatures, flows, pressure drops) and report measured vs simulated. Run check_coverage on your final "
                        "model and fix every missing connection that carries normal flow. Then call submit_model.",
                        self.tools() + [SUBMIT_MODEL], "submit_model", 22)
        run = self.runs.get(sub["label"]) or list(self.runs.values())[-1]
        self.built = {"label": sub["label"] if sub["label"] in self.runs else list(self.runs)[-1], "spec": run["spec"],
                      "result": run["result"], "mapping": sub.get("mapping"), "calibration": sub.get("calibration"),
                      "assumptions": sub.get("assumptions"), "model": self.model,
                      "coverage": coverage(self.pid, run["spec"]), "seconds": round(time.time() - t0),
                      "cost_usd": round(llm.spent() - usd0, 4), "at": time.strftime("%Y-%m-%d %H:%M")}
        self.model_file.write_text(json.dumps(self.built, indent=1))
        self.revisions = []
        self.rev_file.write_text("[]")
        audit.append(self.name, "build", None, "model built from the P&ID and data sheet",
                     {"label": self.built["label"], "model": self.model, "coverage_missing": self.built["coverage"]["missing_connections"]})
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
                        "changes (paths into the spec) that respect every utility and frame limit in the data sheet. Give one "
                        "proposal per limiting equipment item, each with its tag. Prefer the cheapest fix that works: operating "
                        "changes within documented limits (levels, setpoints, utility flows), then cleaning a fouled exchanger "
                        "back to its documented clean performance, and only then new equipment. Write for a non-specialist; "
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

    def accept(self, p, user=None, reason=None):
        """Accept a verified proposal as a new revision. Revisions are kept on disk and never deleted."""
        if not (reason or "").strip():
            raise ValueError("a reason for the change is required")
        v = self.verify(p)  # never trust the client's copy
        if not v["verified"]:
            raise ValueError("proposal does not verify in DWSIM: " + json.dumps(v["over_limits_at_target"])[:300])
        after = patch(self.built["spec"], p["changes"])
        r = {"rev": len(self.revisions) + 1, "kind": "change", "title": p.get("title"), "changes": p["changes"],
             "spec_before": self.built["spec"], "spec_after": after, "capacity_multiple": v["capacity_multiple"],
             "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "user": user, "reason": reason}
        r["audit"] = audit.append(self.name, "accept", user, reason, {"rev": r["rev"], "title": r["title"], "changes": p["changes"],
                                                                      "verified_capacity_multiple": v["capacity_multiple"]})["hash"]
        self._commit(r)
        return {**v, "revisions": self.revisions}

    def restore(self, rev, user=None, reason=None):
        """Return the model to how it was before revision `rev` (0 = as built). History is kept: the return is itself a
        new revision with its own audit entry."""
        if not (reason or "").strip():
            raise ValueError("a reason for the change is required")
        target = self.revisions[rev - 1]["spec_before"] if 0 < rev <= len(self.revisions) else self._built_spec()
        r = {"rev": len(self.revisions) + 1, "kind": "revert", "title": f"Return to the model before Rev {rev}" if rev else
             "Return to the model as built", "changes": [], "spec_before": self.built["spec"], "spec_after": target,
             "capacity_multiple": None, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "user": user, "reason": reason}
        r["audit"] = audit.append(self.name, "revert", user, reason, {"rev": r["rev"], "to_before_rev": rev})["hash"]
        self._commit(r)
        return {"revisions": self.revisions}

    def _built_spec(self):
        return json.loads(self.model_file.read_text())["spec"]

    def _commit(self, r):
        self.revisions.append(r)
        self.built = {**self.built, "spec": r["spec_after"]}
        self.rev_file.write_text(json.dumps(self.revisions, indent=1))
        self._state = {}

    def state(self, scale=1.0):
        """Solved unit at a throughput multiple: what the P&ID view colours. Cached per spec and scale.
        Without DWSIM installed (a judge's clean clone) the unmodified model replays precomputed DWSIM solutions."""
        if not self.built:
            return None
        key = hashlib.sha1(json.dumps([self.spec, round(scale, 3)], sort_keys=True).encode()).hexdigest()
        if key not in self._state:
            if process.available():
                self._state[key] = {"scale": scale, **process.run(self.spec, scale)}
            else:
                demo = self._demo()
                if not demo or demo["spec"] != self.spec:
                    raise RuntimeError("DWSIM is not installed and there are no precomputed solutions for this model")
                near = min(demo["states"], key=lambda st: abs(st["scale"] - scale))
                self._state[key] = {**near, "replayed": True}
        return self._state[key]

    def _demo(self):
        f = self.model_file.with_name("states.json")
        return json.loads(f.read_text()) if f.exists() else None

    def precompute(self):
        """Store DWSIM solutions from 80 % to 150 % throughput, so the slider works without DWSIM."""
        states = [{"scale": round(x / 100, 2), **process.run(self.spec, x / 100)} for x in range(80, 151)]
        self.model_file.with_name("states.json").write_text(json.dumps({"spec": self.spec, "capacity": process.capacity(self.spec),
                                                                        "states": states}))
        return len(states)

    def capacity(self):
        key = "cap:" + hashlib.sha1(json.dumps(self.spec, sort_keys=True).encode()).hexdigest()
        if key not in self._state:
            demo = None if process.available() else self._demo()
            self._state[key] = demo["capacity"] if demo and demo["spec"] == self.spec else process.capacity(self.spec)
        return self._state[key]


if __name__ == "__main__":
    s = {"units": [{"id": "H1", "type": "hx", "area_m2": 10}], "feeds": {"CW": {"m3_h": 20}}, "limits": {"H1": {"area_m2": 10}}}
    p = patch(s, [{"path": "units.H1.area_m2", "value": 12}, {"path": "feeds.CW.m3_h", "value": 26}])
    assert p["units"][0]["area_m2"] == 12 and p["limits"]["H1"]["area_m2"] == 12 and p["feeds"]["CW"]["m3_h"] == 26
    assert s["units"][0]["area_m2"] == 10
    print("ok")
