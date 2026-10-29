"""An engineering study done the way a consulting engineer does it, in eight steps.

1 scope & criteria  2 data collection & RFI  3 calibration  4 hydraulic model  5 capacity analysis
6 alternatives  7 independent QA/QC  8 deliverables (memo, model.inp, calc appendix, findings)

Usage: python -m plantagent.study --case roseburg [--model muse-spark-1.3-contributor]
"""
import argparse
import json
import time
from pathlib import Path

from . import cad, cost, eps, llm, process, profile, sim, standards, surge
from .docs import DATA, Case
from .deliver import write_deliverables

RULES = """Engineering rules:
- Never compute hydraulics, energy or velocities yourself. Use run_hydraulics and velocity; quote their outputs.
- Every number must cite a page (p.N) or be labelled ASSUMPTION with a reason. Never invent data silently.
- Some recommendation clauses in the document are withheld; reach your own conclusions from the facts.
- Use the document's units. Firm capacity = capacity with the largest unit of a station out of service.
- Give every run_hydraulics / run_profile call a short unique label; later steps refer to runs by label."""

DRAWING_RULES = """
- A hydraulic profile drawing is available. Call read_drawing first: it returns every elevation on the sheet, read twice
  independently; cite drawing values as (dwg p.N). Values marked "single read" need confirmation.
- Gravity flow between structures (channels, weirs, launders, gravity pipes, filters) goes in run_profile; pumped legs go
  in run_hydraulics. Calibrate the profile against field tests AND the drawing's water surfaces (drawing_ws_ft) at the
  drawing's design flow, and report residuals. Use profile_capacity to find the flow at which each limit binds.
- Put each limit the documents give (spill/overflow levels, freeboard, stated unit capacities or ratings) on the element.
- Model the whole treatment train on the drawing's flow path, one element per structure (rapid mix, flocculation, sedimentation
  launders, settled-water channel and pipe, filter inlet, filters, filter effluent, clearwell), each with drawing_ws_ft where the
  drawing labels it. A calibration point used to fit a coefficient cannot also validate it: validate on an independent point,
  and report residuals in ft and as a percentage of the headloss, not of the elevation."""

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
    {"type": "function", "function": {"name": "firm_capacity", "description": "Firm capacity of a logged pump-station run: EPANET "
     "solved with each pump out of service in turn; the worst outage governs. Use this, never your own arithmetic, for firm capacity.",
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}}},
    {"type": "function", "function": {"name": "velocity",
     "description": "Mean velocity. US: flow in mgd with diameter (in) or area (ft2) -> fps. SI: flow in l/s with diameter (mm) or area (m2) -> m/s. `openings` divides the flow.",
     "parameters": {"type": "object", "properties": {"flow": {"type": "number"}, "diameter": {"type": "number"}, "area": {"type": "number"},
                    "openings": {"type": "integer"}, "units": {"type": "string", "enum": ["US", "SI"]}}, "required": ["flow"]}}},
]

PROFILE_TOOLS = [
    {"type": "function", "function": {"name": "read_drawing", "description": "Read every elevation label on a hydraulic profile drawing page (vision, two independent reads).",
     "parameters": {"type": "object", "properties": {"page": {"type": "integer"}}, "required": ["page"]}}},
    {"type": "function", "function": {"name": "run_profile",
     "description": "Gravity hydraulic profile (US units) at one or more plant flows; logs it under `label`. Spec: " + json.dumps(profile.SPEC_HELP),
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "purpose": {"type": "string"}, "spec": {"type": "object"},
                    "flows_mgd": {"type": "array", "items": {"type": "number"}}}, "required": ["label", "spec", "flows_mgd"]}}},
    {"type": "function", "function": {"name": "profile_capacity", "description": "For a logged profile run: the plant flow at which each limit reaches zero margin.",
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}}},
]

SURGE_TOOLS = [
    {"type": "function", "function": {"name": "run_surge",
     "description": "Transient (water hammer) simulation of a pump trip on a run_hydraulics network spec; logs it under `label`. "
                    "Returns steady, max and min pressure at every junction and a vapour (column separation) flag. Args: " + json.dumps(surge.SPEC_HELP),
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "purpose": {"type": "string"}, "spec": {"type": "object"},
                    "event": {"type": "object"}, "protection": {"type": "array", "items": {"type": "object"}},
                    "wave_speed_mps": {"type": "number"}, "sim_time_s": {"type": "number"}}, "required": ["label", "spec", "event"]}}},
]

EPS_TOOLS = [
    {"type": "function", "function": {"name": "eps_model_summary", "description": "Summary of the utility's existing EPANET model "
     "(element counts, pumps, tanks, patterns, controls) and the observed SCADA series available for calibration.",
     "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "eps_run", "description": "Extended-period run of the existing model with explicit "
     "changes; returns fit statistics (RMSE, bias, NSE) per observed series plus sampled tank levels and pump flows. "
     "Logged under `label`. " + eps.__doc__.split("Changes to the model")[1].strip(),
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "purpose": {"type": "string"},
                    "changes": {"type": "array", "items": {"type": "object"}}, "duration_h": {"type": "number"}}, "required": ["label"]}}},
    {"type": "function", "function": {"name": "eps_fit", "description": "Calibrate: fit scale factors on the parameter groups you "
     "consider uncertain (each {target, attr, min, max}) against all observed series; logged under `label`.",
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "purpose": {"type": "string"},
                    "params": {"type": "array", "items": {"type": "object"}}, "base_changes": {"type": "array", "items": {"type": "object"}},
                    "duration_h": {"type": "number"}}, "required": ["label", "params"]}}},
]

PROCESS_TOOLS = [
    {"type": "function", "function": {"name": "run_process", "description": "Solve a DWSIM process flowsheet (pumps, heat exchangers, "
     "heaters, valves, tanks, mixers, splitters, compressors) and log it under `label`; returns streams, unit results and limit "
     "checks. Spec: " + json.dumps(process.SPEC_HELP),
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "purpose": {"type": "string"}, "spec": {"type": "object"},
                    "scale": {"type": "number"}}, "required": ["label", "spec"]}}},
    {"type": "function", "function": {"name": "bubble_pressure", "description": "DWSIM: bubble-point (equilibrium vapour) pressure of a "
     "liquid mixture at each temperature, e.g. the pressure a liquid-filled vessel reaches when heated. compounds: DWSIM names "
     "(Propane, Propylene, n-Butane, Ethane, Water, ...); x: mole fractions.",
     "parameters": {"type": "object", "properties": {"compounds": {"type": "array", "items": {"type": "string"}}, "x": {"type": "object"},
                    "T_C": {"type": "array", "items": {"type": "number"}}}, "required": ["compounds", "x", "T_C"]}}},
    {"type": "function", "function": {"name": "blocked_in_pressure", "description": "DWSIM: pressure a liquid-full, blocked-in vessel "
     "reaches when heated from T1_C to T2_C starting at P1_bar (API 521 hydraulic expansion, rigid vessel), with the liquid's "
     "expansion coefficient and compressibility.",
     "parameters": {"type": "object", "properties": {"compounds": {"type": "array", "items": {"type": "string"}}, "x": {"type": "object"},
                    "T1_C": {"type": "number"}, "P1_bar": {"type": "number"}, "T2_C": {"type": "number"}},
                    "required": ["compounds", "x", "T1_C", "P1_bar", "T2_C"]}}},
    {"type": "function", "function": {"name": "fluid_properties", "description": "DWSIM: density (kg/m3) and vapour fraction of a mixture "
     "at each {T_C, P_bar} point (Peng-Robinson). Use for liquid thermal expansion and fill-level calculations.",
     "parameters": {"type": "object", "properties": {"compounds": {"type": "array", "items": {"type": "string"}}, "x": {"type": "object"},
                    "points": {"type": "array", "items": {"type": "object"}}}, "required": ["compounds", "x", "points"]}}},
]

ENG_TOOLS = [
    {"type": "function", "function": {"name": "cost_catalogue", "description": "Published capital cost curves available "
     "(id, item, x variable and unit, valid range, dollar basis).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "cost_estimate", "description": "Order-of-magnitude capital cost of an alternative "
     "from the curves, escalated by ENR CCI, with the AACE class range. lines: [{id, x, qty (count, or length ft for per-foot "
     "curves), note}]. Logged under `label` (use the alternative's name). Match the curve's scope: complete-station curves "
     "only for a new or rebuilt station; equipment curves (pump, VFD, tank) for equipment added to an existing one.",
     "parameters": {"type": "object", "properties": {"label": {"type": "string"}, "lines": {"type": "array", "items": {"type": "object"}},
                    "aace_class": {"type": "integer", "enum": [4, 5]}}, "required": ["label", "lines"]}}},
    {"type": "function", "function": {"name": "treatment_capacity", "description": "Rated capacity of treatment units (flocculation, "
     "sedimentation, filters) from their dimensions against Ten States Standards: the plant flow in mgd at which each criterion "
     "binds, with the largest filter out of service. Use it rather than quoting a documented rating. " + standards.TREATMENT_HELP,
     "parameters": {"type": "object", "properties": {"units": {"type": "array", "items": {"type": "object"}}}, "required": ["units"]}}},
    {"type": "function", "function": {"name": "standards_list", "description": "Design-standard rules (Ten States Standards water "
     "2022 / wastewater 2014, HI operating region) with section numbers.",
     "parameters": {"type": "object", "properties": {"standard": {"type": "string", "enum": ["water", "wastewater", "all"]}}}}},
    {"type": "function", "function": {"name": "standards_check", "description": "Check values against rules; give each value from "
     "a simulator run (basis = run label) or a page. items: [{rule_id, value | numerator + denominator, basis}]. Returns "
     "pass/FAIL with the citation.", "parameters": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object"}}},
                                                   "required": ["items"]}}},
]

# How a consulting engineer approaches each kind of question (added to the analysis step).
TASK_GUIDES = {
    "capacity": "Capacity study: for every unit on the flow path find the flow at which it limits (hydraulic and treatment "
                "ratings separately), firm capacity with the largest unit out of service, then the least-cost fix per limiting unit.",
    "troubleshoot": "Troubleshooting: list every plausible fault hypothesis from the system description (each valve, non-return "
                    "valve, bypass, partly closed or stuck valve, worn impeller, air, blockage). Simulate each hypothesis as its own "
                    "network variant and compare it with EVERY measured point; rank hypotheses by residual. The diagnosis is the "
                    "hypothesis that reproduces the measurements, not the first plausible one. Then quantify the gain from fixing it.",
    "energy": "Energy audit: establish the measured baseline (kWh per volume, duty points). Simulate where each pump runs "
              "relative to its best efficiency point. Split losses into pump, motor, drive, throttling and control strategy. "
              "Check whether a VFD really saves energy here (static-head-dominated systems often lose efficiency when slowed). "
              "Give each measure with simulated savings and a simple payback basis.",
    "surge": "Surge analysis: build the steady-state network first, then simulate pump trips with run_surge. Compare the minimum "
             "and maximum pressures with the pipe pressure rating and with vapour pressure (column separation at high points). "
             "Test protection options (air chamber, surge tank, slower valve closure) in the simulator and size the smallest one that works.",
    "failure": "Failure investigation: build the timeline, identify the failure mode, check the hydraulic conditions at failure "
               "(pressure vs. rating, transients, velocity) in the simulator where data allows, separate root cause from contributing "
               "factors, and give recommendations that prevent recurrence.",
    "design": "Pump station and force main design: system curves for existing and proposed mains, pump/impeller selection by "
              "simulated operating point, maximum operating pressure vs. pipe rating, and alternatives compared on life-cycle cost.",
}


def task_guide(task_type):
    t = task_type.lower()
    keys = [k for k, words in {"capacity": ["capacity", "expansion", "uprate"], "troubleshoot": ["troubleshoot", "diagnos"],
                               "energy": ["energy", "efficiency"], "surge": ["surge", "transient", "hammer"],
                               "failure": ["failure", "incident", "investigation"], "design": ["design", "force main"]}.items()
            if any(w in t for w in words)]
    return "\n".join(TASK_GUIDES[k] for k in keys)


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


_INVOKE = __import__("re").compile(r"<(?:\w+:)?invoke name=\"([\w.-]+)\">(.*?)</(?:\w+:)?invoke>", __import__("re").S)
_PARAM = __import__("re").compile(r"<(?:\w+:)?parameter name=\"([\w.-]+)\">(.*?)</(?:\w+:)?parameter>", __import__("re").S)


def text_tool_calls(content):
    """Some open-weights deployments emit a large tool call as text (<x:invoke name=..><x:parameter name=..>..) instead of
    a structured call; recover those calls so the agent loop does not spin. Parameter values are JSON where they parse."""
    calls = []
    for k, (name, body) in enumerate(_INVOKE.findall(content or "")):
        args = {}
        for pname, raw in _PARAM.findall(body):
            raw = raw.strip()
            try:
                args[pname] = json.loads(raw)
            except json.JSONDecodeError:
                args[pname] = raw
        calls.append({"id": f"text-call-{k}", "name": name, "arguments": json.dumps(args)})
    return calls


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
    "test_plan": ARR({"test": S, "purpose": S, "closes_rfi": S, "measurements": S, "procedure": S, "acceptance": S}),
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
    "base_profile_run": {"type": "string", "description": "label of the calibrated existing-conditions profile run, if any"},
    "design_profile_run": {"type": "string", "description": "label of the profile run of the recommended design, if any (drawn as a new sheet)"},
    "drawing_changes": ARR({"anchor_value": N, "structure": S, "note": S}),
}, ["calibration", "capacity_table", "alternatives", "findings"])

SUBMIT_REVIEW = submit("submit_review", "Step 7: QA/QC review result.", {
    "checked_runs": {"type": "array", "items": S}, "checked_citations": {"type": "array", "items": S},
    "issues": ARR({"severity": {"type": "string", "enum": ["major", "minor"]}, "item": S, "issue": S, "evidence": S}),
}, ["issues"])

SUBMIT_RESOLUTION = submit("submit_resolution", "Respond to every QA/QC issue and give the final findings.", {
    "responses": ARR({"issue": S, "action": {"type": "string", "enum": ["fixed", "rejected", "noted"]}, "explanation": S}),
    "findings": SUBMIT_ANALYSIS["function"]["parameters"]["properties"]["findings"],
    "alternatives": SUBMIT_ANALYSIS["function"]["parameters"]["properties"]["alternatives"],
    "drawing_changes": SUBMIT_ANALYSIS["function"]["parameters"]["properties"]["drawing_changes"],
}, ["responses", "findings"])


def read_drawing(case, page):
    """Two independent Muse readings of a profile sheet, reconciled; cached per case and page."""
    cache = Path("runs") / "drawings" / f"{case.name}_p{page}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    if page not in case.pages:
        raise ValueError(f"page {page} not available")
    t0 = time.time()
    reading, png = cad.read_profile(case.pdf, page)
    located = cad.locate_labels(case.pdf, page)
    elevations, extra = cad.reconcile(reading, located)
    out = {"page": page, **{k: reading.get(k) for k in ("title", "design_flow_note", "flow_path", "notes")},
           "elevations": elevations, "tile_only_labels": extra, "read_seconds": round(time.time() - t0),
           "read_at": time.strftime("%Y-%m-%d %H:%M"), "model": "muse-spark-1.3-contributor"}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, indent=1))
    return out


def case_file(case, name):
    """Prepared inputs live next to case.json; raw source files under case-data."""
    return case.dir / name if (case.dir / name).exists() else DATA / name


def eps_summary(case):
    cfg = case.cfg["eps"]
    wn = eps._model(str(DATA / cfg["inp"]))
    obs = eps.load_observations(str(case_file(case, cfg["observations"])))
    return {"model": cfg["inp"], "junctions": wn.num_junctions, "pipes": wn.num_pipes, "pumps": wn.pump_name_list,
            "tanks": wn.tank_name_list, "reservoirs": wn.reservoir_name_list, "valves": wn.num_valves,
            "patterns": wn.pattern_name_list[:20], "controls": len(wn.control_name_list),
            "duration_h_default": cfg.get("duration_h", 24),
            "observed_series": {k: {"n": int((~__import__("numpy").isnan(v[1])).sum()), "hours": [float(v[0][0]), float(v[0][-1])]}
                                for k, v in obs.items()}, "notes": cfg.get("notes", "")}


def compact(messages, keep=10, limit=600):
    """Old tool results and page images are shortened before each call; the agent can re-read any page.
    ponytail: fixed window; summarise into the data register instead if studies get much longer."""
    tool_idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    old = set(tool_idx[:-keep]) if len(tool_idx) > keep else set()
    first_kept = tool_idx[-keep] if len(tool_idx) > keep else len(messages)
    out = []
    for i, m in enumerate(messages):
        if i in old and len(m["content"]) > limit:
            m = {**m, "content": m["content"][:limit] + " ...[older result shortened; call the tool again if needed]"}
        elif m["role"] == "user" and isinstance(m["content"], list) and i < first_kept:
            m = {**m, "content": "[page image shown earlier; call view_page again if needed]"}
        out.append(m)
    return out


class Study:
    def __init__(self, case, model, question=None, task_type=None, simulators=None):
        self.case, self.model = Case(case), model
        if question:  # a task launched from the workspace asks its own question of the same project
            self.case.question = question
        if task_type or simulators:
            self.case.cfg = {**self.case.cfg, **({"task_type": task_type} if task_type else {}),
                             **({"simulators": sorted(set(self.case.cfg.get("simulators", [])) | set(simulators))} if simulators else {})}
        self.profiles = {}  # label -> {purpose, spec, flows, results}
        self.surges = {}  # label -> {purpose, spec, args, result}
        self.eps_runs = {}  # label -> {purpose, tool, args, result}
        self.costs, self.std_checks = {}, {}  # cost estimates by label; latest standards check by rule id
        self.drawing = None
        self.dir = Path("runs") / case / time.strftime("%Y%m%d-%H%M%S")
        self.dir.mkdir(parents=True)
        self.log = (self.dir / "log.jsonl").open("w")
        self.runs = {}  # label -> {purpose, spec, result}
        self.steps = 0

    def emit(self, event):
        """Progress hook for live UIs; the batch study ignores it."""

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
        if name == "rerun" and a["label"] in self.profiles:
            r = self.profiles[a["label"]]
            fresh = [profile.run(r["spec"], float(q)) for q in r["flows"]]
            return {"label": a["label"], "matches_logged_result": fresh == r["results"], "results": fresh, "spec": r["spec"]}
        if name == "rerun" and a["label"] in self.surges and (self.surges[a["label"]].get("args") or {}).get("tool") == "dwsim":
            r = self.surges[a["label"]]
            sp = r["spec"]
            if "units" in sp:
                fresh = process.run(sp, float((r.get("result") or {}).get("scale") or 1.0))
            elif "T1_C" in sp:
                fresh = process.blocked_in(sp["compounds"], sp["x"], sp["T1_C"], sp["P1_bar"], sp["T2_C"])
            elif "points" in sp:
                fresh = process.props(sp["compounds"], sp["x"], sp["points"])
            else:
                fresh = process.bubble(sp["compounds"], sp["x"], sp["T_C"])
            return {"label": a["label"], "matches_logged_result": fresh == r["result"], "result": fresh}
        if name == "rerun" and a["label"] not in self.runs:
            return {"label": a["label"], "matches_logged_result": False,
                    "error": f"no logged run with this label; logged: {sorted(list(self.runs) + list(self.profiles) + list(self.surges))[:40]}"}
        if name == "rerun":
            r = self.runs[a["label"]]
            fresh = sim.run(r["spec"])
            return {"label": a["label"], "matches_logged_result": fresh == r["result"], "result": fresh, "spec": r["spec"]}
        if name == "read_drawing":
            self.drawing = read_drawing(c, int(a["page"]))
            return {"page": self.drawing["page"], "title": self.drawing["title"], "design_flow_note": self.drawing["design_flow_note"],
                    "flow_path": self.drawing["flow_path"], "notes": self.drawing["notes"],
                    "elevations": [{k: e[k] for k in ("value", "structure", "feature", "label_text", "confirmed")} for e in self.drawing["elevations"]]}
        if name == "run_profile":
            label = a.get("label") or f"profile{len(self.profiles) + 1}"
            if label in self.profiles or label in self.runs:
                label = f"{label}-{len(self.profiles) + 1}"
            flows = a.get("flows_mgd") or []
            flows = flows if isinstance(flows, list) else [flows]
            results = [profile.run(a["spec"], float(q)) for q in flows]
            self.profiles[label] = {"purpose": a.get("purpose", ""), "spec": a["spec"], "flows": flows, "results": results}
            return {"label": label, "results": results}
        if name == "run_surge":
            label = a.get("label") or f"surge{len(self.surges) + 1}"
            if label in self.surges:
                label = f"{label}-{len(self.surges) + 1}"
            kw = {k: a[k] for k in ("protection", "wave_speed_mps", "sim_time_s") if a.get(k) is not None}
            result = surge.run(a["spec"], a["event"], **kw)
            self.surges[label] = {"purpose": a.get("purpose", ""), "spec": a["spec"], "args": {"event": a["event"], **kw}, "result": result}
            return {"label": label, **result}
        if name == "run_process":
            label = a.get("label") or f"process{len(self.surges) + 1}"
            result = process.run(a["spec"], float(a.get("scale") or 1.0))
            self.surges[label] = {"purpose": a.get("purpose", ""), "spec": a["spec"], "args": {"tool": "dwsim"}, "result": result}
            return {"label": label, **result}
        if name == "bubble_pressure":
            r = process.bubble(a["compounds"], a["x"], a["T_C"])
            self.surges[f"bubble{len(self.surges) + 1}"] = {"purpose": "DWSIM bubble pressure", "spec": a, "args": {"tool": "dwsim"}, "result": r}
            return r
        if name == "blocked_in_pressure":
            r = process.blocked_in(a["compounds"], a["x"], a["T1_C"], a["P1_bar"], a["T2_C"])
            self.surges[f"blockedin{len(self.surges) + 1}"] = {"purpose": "DWSIM blocked-in liquid expansion", "spec": a, "args": {"tool": "dwsim"}, "result": r}
            return r
        if name == "fluid_properties":
            r = process.props(a["compounds"], a["x"], a["points"])
            self.surges[f"props{len(self.surges) + 1}"] = {"purpose": "DWSIM fluid properties", "spec": a, "args": {"tool": "dwsim"}, "result": r}
            return r
        if name == "cost_catalogue":
            return cost.catalogue()
        if name == "cost_estimate":
            result = cost.estimate(a["lines"], int(a.get("aace_class") or 5), label=a.get("label", ""))
            self.costs[a.get("label") or f"estimate{len(self.costs) + 1}"] = result
            return result
        if name == "treatment_capacity":
            r = standards.treatment_capacity(a["units"])
            self.treatment = getattr(self, "treatment", {})
            for x in r:
                self.treatment[x["unit"]] = x
            return r
        if name == "standards_list":
            return standards.list_rules(a.get("standard") or "all")
        if name == "standards_check":
            result = standards.check(a["items"], {**self.runs, **self.profiles})
            for r in result:
                self.std_checks[r["rule_id"]] = r
            return result
        if name == "eps_model_summary":
            return eps_summary(c)
        if name in ("eps_run", "eps_fit"):
            cfg = c.cfg["eps"]
            inp, obs = str(DATA / cfg["inp"]), str(case_file(c, cfg["observations"]))
            dur = float(a.get("duration_h") or cfg.get("duration_h", 24))
            label = a.get("label") or f"{name}{len(self.eps_runs) + 1}"
            if label in self.eps_runs:
                label = f"{label}-{len(self.eps_runs) + 1}"
            if name == "eps_run":
                result = eps.run(inp, obs, a.get("changes") or [], dur)
            else:
                result = eps.fit(inp, obs, a["params"], dur, a.get("base_changes") or [])
            self.eps_runs[label] = {"purpose": a.get("purpose", ""), "tool": name, "args": a, "result": result}
            return {"label": label, **result}
        if name == "profile_capacity":
            return {"label": a["label"], "limits": profile.capacity(self.profiles[a["label"]]["spec"])}
        if name == "firm_capacity":
            r = self.runs[a["label"]]
            res = sim.firm_capacity(r["spec"])
            r["firm"] = res
            return {"label": a["label"], **res}
        if name == "velocity":
            return sim.velocity(**{k: v for k, v in a.items() if v is not None})
        raise ValueError(f"unknown tool {name}")

    def loop(self, phase, system, user, tools, submit_name, max_steps):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for step in range(max_steps):
            self.steps += 1
            if step == max_steps - 3:
                messages.append({"role": "user", "content": f"Step limit near. Call {submit_name} now with what you have."})
            msg = llm.complete(self.model, compact(messages), tools=tools)
            self.log.write(json.dumps({"phase": phase, "step": step, "assistant": msg}) + "\n")
            if not msg["tool_calls"] and msg.get("content") and "invoke name=" in msg["content"]:
                msg = {**msg, "tool_calls": text_tool_calls(msg["content"]), "content": ""}
            if msg.get("content"):
                self.emit({"kind": "say", "text": msg["content"]})
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
                self.emit({"kind": "tool", "name": t["name"], "args": args, "result": result})
                messages.append({"role": "tool", "tool_call_id": t["id"], "content": json.dumps(result)})
            for url in images:
                messages.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]})
            self.log.flush()
        raise RuntimeError(f"{phase}: no {submit_name} after {max_steps} steps")

    # --- the eight steps -----------------------------------------------------------------------
    def run(self):
        c, t0 = self.case, time.time()
        drawing = "profile" in c.cfg.get("simulators", [])
        rules = RULES + (DRAWING_RULES if drawing else "")
        sim_tools = SIM_TOOLS + ENG_TOOLS + (PROFILE_TOOLS if drawing else []) + (SURGE_TOOLS if "tsnet" in c.cfg.get("simulators", []) else []) + \
            (EPS_TOOLS if "eps" in c.cfg else []) + (PROCESS_TOOLS if "dwsim" in c.cfg.get("simulators", []) else [])
        if c.cfg.get("simulators") == ["dwsim"]:  # a process plant: no water-network tools, water standards or water cost curves
            sim_tools = PROCESS_TOOLS
        doc_tools = DOC_TOOLS + (PROFILE_TOOLS[:1] if drawing else [])
        llm.TAG = c.name
        usd0 = llm.spent(c.name)
        head = (f"Facility: {c.cfg['title']}\nSource: {c.cfg['source']}\nTask type: {c.cfg['task_type']}\n"
                f"Question: {c.question}\nAvailable pages: {c.pages}" +
                (f"\nHydraulic profile drawing: page {c.cfg['drawing_page']}" if drawing else ""))
        print(f"[{c.name}] steps 1-2: scope, criteria, data collection")
        collect = self.loop("collect", "You are the lead engineer starting a study. " + rules,
                            head + "\n\nRead the available pages. Define the design criteria (with sources), list every unit "
                            "on the flow path, and build the data register (every value with page and quote). List missing or "
                            "conflicting data as RFI items; resolve each as an explicit ASSUMPTION with a reason. For every RFI "
                            "that a field measurement could close, write a test_plan entry (what to measure, where, how, and the "
                            "acceptance criterion), as you would before a site visit.",
                            doc_tools + [SUBMIT_COLLECT], "submit_collection", 30)

        print(f"[{c.name}] steps 3-6: calibration, model, capacity, alternatives")
        analysis = self.loop("analyse", "You are the lead engineer. " + rules,
                             head + "\n\nYour steps 1-2 output:\n" + json.dumps(collect) +
                             "\n\nNow: (3) build the hydraulic model and calibrate it against every field test in the data "
                             "register, reporting residuals; (4) name the calibrated base run; (5) evaluate every unit against "
                             "the question; (6) for each limiting unit, verify 2-4 alternatives in the simulator and give an "
                             "order-of-magnitude cost class with its basis. Mark the recommended option. Price each "
                             "recommended alternative with cost_estimate, and check the applicable design standards with "
                             "standards_check (values from your simulator runs, cited by label).\n" +
                             task_guide(c.cfg["task_type"]) +
                             (" (7) list drawing_changes: one per recommended PHYSICAL modification (new or changed structure, "
                              "weir, pipe, pump; not documentation remarks), with the drawing elevation of the structure it "
                              "changes (anchor_value), the structure name, and a one-line revision note as it would appear "
                              "on a revised sheet." if drawing else ""),
                             DOC_TOOLS + sim_tools + [SUBMIT_ANALYSIS], "submit_analysis", 45)

        print(f"[{c.name}] step 7: independent QA/QC")
        run_index = {k: v["purpose"] for k, v in {**self.runs, **self.profiles, **self.surges, **self.eps_runs}.items()}
        checker_tools = DOC_TOOLS + sim_tools + [
            {"type": "function", "function": {"name": "rerun", "description": "Re-execute a logged simulation by label and compare with its logged result.",
             "parameters": {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}}},
            SUBMIT_REVIEW]
        review = self.loop("qaqc", "You are the independent checking engineer (QA/QC). You did not do this work. " + rules +
                           "\nCheck: re-run at least 3 logged simulations, verify at least 5 citations against the pages, look "
                           "for unit errors, unsupported numbers, weak assumptions, missed units, and alternatives that were not "
                           "actually verified. Report issues; do not rewrite the study.",
                           head + "\n\nStudy under review:\n" + json.dumps({"collection": collect, "analysis": analysis}) +
                           "\n\nLogged runs (label: purpose):\n" + json.dumps(run_index), checker_tools, "submit_review", 25)

        resolution = {"responses": [], "findings": analysis["findings"]}
        if review.get("issues"):
            print(f"[{c.name}] step 7b: lead resolves {len(review['issues'])} QA/QC issues")
            resolution = self.loop("resolve", "You are the lead engineer answering the checker. " + rules,
                                   head + "\n\nYour analysis:\n" + json.dumps(analysis) + "\n\nQA/QC issues:\n" +
                                   json.dumps(review["issues"]) + "\n\nFix what is right (re-run simulations where needed), "
                                   "reject what is wrong with a reason, then submit the final findings.",
                                   DOC_TOOLS + sim_tools + [SUBMIT_RESOLUTION], "submit_resolution", 20)
            analysis["findings"] = resolution["findings"]
            for k in ("alternatives", "drawing_changes"):
                if resolution.get(k):
                    analysis[k] = resolution[k]

        return self.deliver(collect, analysis, review, resolution, t0, usd0)

    def deliver(self, collect, analysis, review, resolution, t0, usd0, wall_s=None):
        c = self.case
        print(f"[{c.name}] step 8: deliverables")
        study = {"case": c.name, "facility": c.cfg["title"], "source": c.cfg["source"], "url": c.cfg.get("url"),
                 "question": c.question, "model": self.model, "collection": collect, "analysis": analysis,
                 "review": review, "resolution": resolution, "runs": self.runs, "profiles": self.profiles, "surges": self.surges, "eps_runs": self.eps_runs,
                 "cost_estimates": self.costs, "standards_checks": list(self.std_checks.values()),
                 "treatment_capacity": list(getattr(self, "treatment", {}).values()),
                 "drawing": self.drawing}
        memo = llm.chat(self.model, [
            {"role": "system", "content": "You write technical memoranda for a consulting engineering firm. Use only facts and "
             "numbers present in the JSON; keep page citations (p.N) and run labels; label assumptions. Sections: Purpose; "
             "Background; Design Criteria; Data and Assumptions; Model Calibration; Capacity Evaluation (table); Alternatives "
             "(table with cost class); QA/QC Summary; Recommendations; Limitations. Quote standards results exactly as in "
             "standards_checks and costs exactly as in cost_estimates; where the analysis text disagrees with them, say so "
             "explicitly instead of picking one. Markdown. Start with the line: "
             "'DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.'"},
            {"role": "user", "content": json.dumps({k: v for k, v in study.items() if k not in ("runs", "profiles", "drawing", "surges", "eps_runs")})}])
        summary = {"case": c.name, "model": self.model, "llm_steps": self.steps, "simulations": len(self.runs) + len(self.profiles) + len(self.surges) + len(self.eps_runs),
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
        self.profiles, self.drawing, self.surges, self.eps_runs = {}, None, {}, {}
        self.costs, self.std_checks = {}, {}
        subs = {}
        for line in (run_dir / "log.jsonl").read_text().splitlines():
            e = json.loads(line)
            if "submit" in e:
                subs[e["phase"]] = unstring(e["submit"])
            elif e.get("tool") == "run_hydraulics" and isinstance(e["result"], dict) and "label" in e["result"]:
                r = dict(e["result"])
                self.runs[r.pop("label")] = {"purpose": e["args"].get("purpose", ""), "spec": unstring(e["args"]["spec"]), "result": r}
            elif e.get("tool") == "run_profile" and isinstance(e["result"], dict) and "label" in e["result"]:
                a = unstring(e["args"])
                self.profiles[e["result"]["label"]] = {"purpose": a.get("purpose", ""), "spec": a["spec"],
                                                       "flows": a.get("flows_mgd"), "results": e["result"]["results"]}
            elif e.get("tool") == "run_surge" and isinstance(e["result"], dict) and "label" in e["result"]:
                a, r = unstring(e["args"]), dict(e["result"])
                self.surges[r.pop("label")] = {"purpose": a.get("purpose", ""), "spec": a["spec"], "args": {"event": a.get("event")}, "result": r}
            elif e.get("tool") == "cost_estimate" and isinstance(e["result"], dict) and "total" in e["result"]:
                self.costs[e["args"].get("label") or f"estimate{len(self.costs) + 1}"] = e["result"]
            elif e.get("tool") == "standards_check" and isinstance(e["result"], list):
                for r in e["result"]:
                    self.std_checks[r["rule_id"]] = r
            elif e.get("tool") == "read_drawing" and isinstance(e["result"], dict) and "elevations" in e["result"]:
                self.drawing = read_drawing(self.case, e["args"]["page"])
            elif "assistant" in e:
                self.steps += 1
        analysis, review = subs["analyse"], subs.get("qaqc", {"issues": []})
        resolution = subs.get("resolve", {"responses": [], "findings": analysis["findings"]})
        analysis["findings"] = resolution["findings"]
        for k in ("alternatives", "drawing_changes"):
            if resolution.get(k):
                analysis[k] = resolution[k]
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
