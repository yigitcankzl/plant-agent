"""Engineering workspace copilot: the engineer asks (or clicks a structure), the agent answers with calc cards and
drawing layers backed by simulator runs, then exports deliverables on demand.

The workspace preloads the project's calibrated models from the latest completed study, so a question takes seconds,
not a full study. All project documents are readable (nothing is withheld: this is the engineer's own project).
"""
import base64
import json
import re
import subprocess
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

from . import llm
from .docs import DATA, _pages, _paragraphs
from .study import DRAWING_RULES, ENG_TOOLS, EPS_TOOLS, PROFILE_TOOLS, RULES, SIM_TOOLS, SURGE_TOOLS, Study, read_drawing, submit

ROOT = Path(__file__).resolve().parent.parent
S, N = {"type": "string"}, {"type": "number"}

ANSWER = submit("answer", "Final answer for this request, shown as calc cards and drawing layers (not as chat).", {
    "summary": {"type": "string", "description": "at most 2 sentences, plain, with the key number and its source"},
    "cards": {"type": "array", "items": {"type": "object", "properties": {
        "title": S, "result": {"type": "string", "description": "headline only: the value(s) with units, at most 14 words"},
        "inputs": {"type": "array", "items": {"type": "object", "properties": {"name": S, "value": S, "source": S}}},
        "runs": {"type": "array", "items": S}, "standards": {"type": "array", "items": S},
        "cost_label": S, "assumptions": {"type": "array", "items": S}, "status": {"type": "string", "enum": ["ok", "warn", "fail", "info"]}}}},
    "layers": {"type": "array", "description": "marks on the drawing", "items": {"type": "object", "properties": {
        "anchor_value": N, "structure": S, "text": S, "severity": {"type": "string", "enum": ["ok", "warn", "fail", "info"]}}}},
    "headline": {"type": "string", "description": "the answer in at most 8 plain words, e.g. 'No - filters and basin limit 18 mgd'"},
    "proposals": {"type": "array", "description": "model changes that fix the problem, each verified before the engineer accepts it",
                  "items": {"type": "object", "properties": {"kind": {"type": "string", "enum": ["profile", "unit"]},
                                                            "unit": S, "capacity_mgd": N, "run_label": S,
                                                            "title": S, "element": S, "field": S, "value": N, "structure": S,
                                                            "profile_label": S, "resolves": {"type": "string", "description": "issue id it fixes"},
                                                            "cost_label": S}}},
    "flow_mgd": {"type": "number", "description": "plant flow the drawing view should show for this answer, if relevant"},
    "chart": {"type": "object", "description": "optional: {dataset, parameter_contains, as_of_year} to plot a history series"},
}, ["summary", "cards"])

DOC_TOOLS = [
    {"type": "function", "function": {"name": "search_docs", "description": "Keyword search over all project documents; returns [doc, page].",
     "parameters": {"type": "object", "properties": {"query": S}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "read_page", "description": "Text of one page of a project document.",
     "parameters": {"type": "object", "properties": {"doc": S, "page": {"type": "integer"}}, "required": ["doc", "page"]}}},
    {"type": "function", "function": {"name": "view_page", "description": "A page as an image (figures, tables, drawings).",
     "parameters": {"type": "object", "properties": {"doc": S, "page": {"type": "integer"}}, "required": ["doc", "page"]}}},
]
HISTORY_TOOL = {"type": "function", "function": {"name": "history", "description": "Measured or projected record from a project "
                "dataset. Returns the points, a least-squares linear trend (per year and % per year) over the selected years, and "
                "the trend extrapolated to `project_to` years. Use as_of_year to see only what was known at that date.",
                "parameters": {"type": "object", "properties": {"dataset": S, "parameter_contains": S, "from_year": N, "as_of_year": N,
                               "project_to": {"type": "array", "items": N}}, "required": ["dataset", "parameter_contains"]}}}


class Project:
    def __init__(self, case):
        self.case = case
        ws = case.cfg.get("workspace", {})
        self.docs = {d["id"]: d for d in ws.get("documents", [{"id": "main", "title": case.cfg["title"], "pdf": case.cfg["pdf"]}])}
        self.datasets = ws.get("datasets", {})

    def page(self, doc, n):
        d = self.docs[doc]
        if d["pdf"] == self.case.cfg["pdf"] and any(a <= int(n) <= b for a, b in self.case.cfg.get("withheld_pages", [])):
            return (f"[{doc} p.{n}] withheld: this page holds the engineers' conclusions used to score the agent, so the "
                    f"workspace does not read it (the comparison stays blind)")
        pages = _pages(DATA / d["pdf"])
        if not 1 <= int(n) <= len(pages):
            return f"{doc} has {len(pages)} pages"
        return f"[{doc} p.{n}]\n" + "\n".join(_paragraphs(pages[int(n) - 1]))

    def image(self, doc, n, dpi=100):
        png = subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-r", str(dpi), "-png", str(DATA / self.docs[doc]["pdf"])],
                             capture_output=True, check=True).stdout
        return "data:image/png;base64," + base64.b64encode(png).decode()

    def search(self, query):
        terms = [t.lower() for t in query.split()]
        hits = []
        for doc, d in self.docs.items():
            for i, text in enumerate(_pages(DATA / d["pdf"])):
                if d["pdf"] == self.case.cfg["pdf"] and any(a <= i + 1 <= b for a, b in self.case.cfg.get("withheld_pages", [])):
                    continue
                low = text.lower()
                score = sum(low.count(t) for t in terms)
                if score:
                    hits.append((score, doc, i + 1))
        return [[doc, p] for _, doc, p in sorted(hits, reverse=True)[:10]]

    def history(self, dataset, parameter_contains, from_year=None, as_of_year=None, project_to=None):
        import csv
        rows = [r for r in csv.DictReader(open(DATA / self.datasets[dataset]["file"]))
                if parameter_contains.lower() in r["parameter"].lower()]
        if not rows:
            return {"error": f"no parameter matching {parameter_contains!r}",
                    "parameters": sorted({r["parameter"] for r in csv.DictReader(open(DATA / self.datasets[dataset]["file"]))})}
        pts = [(float(r["date"][:4]), float(r["value"])) for r in rows]
        pts = [p for p in pts if (from_year is None or p[0] >= from_year) and (as_of_year is None or p[0] <= as_of_year)]
        out = {"dataset": dataset, "parameters": sorted({r["parameter"] for r in rows}), "unit": rows[0]["unit"],
               "points": pts, "source": rows[0]["source"]}
        if len(pts) >= 3:
            x, y = np.array(pts).T
            slope, icpt = np.polyfit(x, y, 1)
            out["trend"] = {"per_year": round(float(slope), 4), "pct_per_year": round(float(100 * slope / y.mean()), 2),
                            "years": [int(x.min()), int(x.max())], "mean": round(float(y.mean()), 3),
                            "max": round(float(y.max()), 3), "max_year": int(x[y.argmax()])}
            if project_to:
                out["trend"]["projection"] = {int(t): round(float(slope * t + icpt), 2) for t in project_to}
        return out


class Workspace(Study):
    """A study session that stays open: preloaded models, question by question."""

    def __init__(self, case_name, model="muse-spark-1.3-contributor"):
        from .docs import Case
        self.case, self.model = Case(case_name), model
        self.project = Project(self.case)
        self.dir = ROOT / "runs" / "ws" / case_name / time.strftime("%Y%m%d-%H%M%S")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log = (self.dir / "log.jsonl").open("w")
        self.runs, self.profiles, self.surges, self.eps_runs, self.costs, self.std_checks = {}, {}, {}, {}, {}, {}
        self.steps, self.drawing, self.answers, self.listener = 0, None, [], None
        self.revisions = []
        self.study, self.study_dir = None, None
        self.current, self.resolved = None, set()
        self.base = self._preload()

    def _preload(self):
        """Calibrated models and data register from the latest completed study of this project."""
        done = sorted(p for p in (ROOT / "runs" / self.case.name).glob("2*") if (p / "study.json").exists())
        if not done:
            return {}
        st = json.loads((done[-1] / "study.json").read_text())
        an = st["analysis"]
        self.study = st
        self.study_dir = done[-1]
        self.runs.update(st.get("runs") or {})
        self.profiles.update(st.get("profiles") or {})
        self.eps_runs.update(st.get("eps_runs") or {})
        self.drawing = st.get("drawing")
        return {"from_study": str(done[-1].relative_to(ROOT)), "base_model_run": an.get("base_model_run"),
                "base_profile_run": an.get("base_profile_run"), "design_profile_run": an.get("design_profile_run"),
                "criteria": st["collection"].get("criteria"), "data_register": (st["collection"].get("data_register") or [])[:80],
                "runs": {k: v["purpose"] for k, v in self.runs.items()}, "profiles": {k: v["purpose"] for k, v in self.profiles.items()}}

    def emit(self, event):
        if self.listener:
            self.listener(event)

    def call(self, name, a):
        p = self.project
        if name == "search_docs":
            return p.search(a["query"])
        if name == "read_page":
            return p.page(a["doc"], a["page"])
        if name == "view_page":
            return {"image": p.image(a["doc"], a["page"])}
        if name == "history":
            return p.history(**{k: a[k] for k in ("dataset", "parameter_contains", "from_year", "as_of_year", "project_to") if k in a})
        if name == "get_spec":  # the full spec of a preloaded run, to copy and modify
            r = self.runs.get(a["label"]) or self.profiles.get(a["label"])
            return {"label": a["label"], "spec": r["spec"], "flows": r.get("flows")} if r else {"error": "unknown label"}
        return super().call(name, a)

    def tools(self):
        c = self.case.cfg
        t = DOC_TOOLS + SIM_TOOLS + ENG_TOOLS + [HISTORY_TOOL, {"type": "function", "function": {
            "name": "get_spec", "description": "Full spec of a preloaded calibrated run or profile, to copy and modify.",
            "parameters": {"type": "object", "properties": {"label": S}, "required": ["label"]}}}, ANSWER]
        if "profile" in c.get("simulators", []):
            t += PROFILE_TOOLS[1:]
        if "tsnet" in c.get("simulators", []):
            t += SURGE_TOOLS
        if "eps" in c:
            t += EPS_TOOLS
        return t

    def ask(self, text, context=None):
        c = self.case
        docs = {k: {"title": d["title"], "pages": len(_pages(DATA / d["pdf"]))} for k, d in self.project.docs.items()}
        system = ("You are the engineering copilot inside the engineer's CAD/model workspace. Answer the request quickly and "
                  "precisely: reuse the preloaded calibrated models (get_spec, then modify and re-run), compute with the tools, "
                  "and finish with `answer`: calc cards (inputs with sources, run labels, standards checked, assumptions) and "
                  "drawing layers anchored to drawing elevations (always at least one layer on the structure the request is about, "
                  "with a short label and severity). Card results are headlines; details go in inputs. Do only what was asked. "
                  "Be fast: the preloaded data register already holds the documented values, so read pages only for what it "
                  "lacks; call independent tools together in one turn; aim for 2-4 turns before `answer`. Write for a non-specialist: "
                  "a plain headline, no acronyms in the headline. When a fix is a change to the gravity profile model, return it in "
                  "`proposals` (element id and field from get_spec of the current profile run, the new value, and the issue id it "
                  "resolves); the workspace verifies it in the solver and the engineer accepts it. For any other unit (pumps, intake, "
                  "filters, pipelines) use kind 'unit': the unit name as in the capacity table, its new capacity_mgd, and the "
                  "run_label of the simulator run (run_hydraulics or run_profile) you made that proves it.\n" + RULES +
                  (DRAWING_RULES if self.drawing else ""))
        brief = {"project": c.cfg["title"], "documents": docs, "datasets": {k: v.get("title", k) for k, v in self.project.datasets.items()},
                 "preloaded": self.base, "earlier_answers": [a["summary"] for a in self.answers[-6:]],
                 "current_profile_run": current_label(self), "target_mgd": target_flow(self),
                 "open_issues": [{k: i[k] for k in ("id", "kind", "text", "structure")} for i in problems(self)[:8]]}
        if self.drawing:
            brief["drawing_elevations"] = [{k: e[k] for k in ("value", "structure", "feature")} for e in self.drawing["elevations"]]
        user = json.dumps(brief) + "\n\nRequest: " + text + (f"\nContext: {json.dumps(context)}" if context else "")
        llm.set_tag("ws:" + c.name)
        usd0 = llm.spent()
        t0 = time.time()
        ans = self.loop("ask", system, user, self.tools(), "answer", 9)
        ans["seconds"] = round(time.time() - t0)
        ans["cost_usd"] = round(llm.spent() - usd0, 4)
        ans["request"] = text
        for k in ("cards", "layers", "proposals"):  # the model sometimes returns a list as (malformed) JSON text
            v = ans.get(k)
            if isinstance(v, str):
                try:
                    ans[k] = json.loads(v)
                except json.JSONDecodeError:
                    ans[k] = [{"title": "Calculation notes", "result": "", "inputs": [{"name": "notes", "value": v[:1500], "source": ""}],
                               "status": "info"}] if k == "cards" else []
            if not isinstance(ans.get(k), list):
                ans[k] = []
        for p in ans.get("proposals") or []:  # verify each proposal in the solver before showing it
            try:
                p.update(preview(self, p))
            except Exception as e:
                p["error"] = f"{type(e).__name__}: {e}"
        ans["checks"] = check_answer(self, ans)
        for layer in ans.get("layers") or []:  # place layers on the sheet
            a = _anchor_of(self.drawing, layer)
            layer["bbox"] = a["bbox"] if a else None
        self.answers.append(ans)
        (self.dir / "answers.json").write_text(json.dumps(self.answers, indent=1))
        return ans


def _anchor_of(drawing, layer):
    if not drawing:
        return None
    from .deliver import _anchor
    return _anchor(drawing, layer.get("anchor_value") or -1, layer.get("structure", ""))


@lru_cache(maxsize=8)
def structures(case_name):
    """Clickable structures on the drawing: union of the label boxes the drawing reader found for each structure."""
    from .docs import Case
    c = Case(case_name)
    if "drawing_page" not in c.cfg:
        return []
    d = read_drawing(c, c.cfg["drawing_page"])
    groups = {}
    for e in d["elevations"]:
        groups.setdefault(e["structure"], []).append(e)
    out = []
    for name, es in groups.items():
        bx = np.array([e["bbox"] for e in es])
        out.append({"name": name, "bbox": [float(bx[:, 0].min()), float(bx[:, 1].min()), float(bx[:, 2].max()), float(bx[:, 3].max())],
                    "elevations": [{k: e[k] for k in ("value", "feature", "bbox")} for e in es]})
    return out



# --- deliverables on demand ------------------------------------------------------------------
def export(ws, kind):
    """kind: calc (xlsx of every answer's cards and the runs they cite) | memo | dwg (redline from the answers' layers) |
    profile (new hydraulic profile sheet of the latest profile run)."""
    from openpyxl import Workbook

    from . import cad, design
    d = ws.dir
    if kind == "calc":
        wb = Workbook()
        sh = wb.active
        sh.title = "Calc cards"
        sh.append(["request", "card", "result", "status", "input", "value", "source", "runs", "standards", "assumptions"])
        for a in ws.answers:
            for c in a.get("cards", []):
                for i, inp in enumerate(c.get("inputs") or [{}]):
                    sh.append([a["request"], c.get("title"), c.get("result") if i == 0 else "", c.get("status"), inp.get("name"),
                               inp.get("value"), inp.get("source"), ", ".join(c.get("runs") or []),
                               ", ".join(c.get("standards") or []), "; ".join(c.get("assumptions") or [])])
        cited = {r for a in ws.answers for c in a.get("cards", []) for r in (c.get("runs") or [])}
        rs = wb.create_sheet("Simulation runs")
        rs.append(["label", "purpose", "spec", "result"])
        for k, v in {**ws.runs, **ws.profiles}.items():
            if any(k in r for r in cited):
                rs.append([k, v["purpose"], json.dumps(v["spec"]), json.dumps(v.get("result") or v.get("results"))[:32000]])
        out = d / "calc_sheets.xlsx"
        wb.save(out)
        return out
    if kind == "memo":
        memo = llm.chat(ws.model, [
            {"role": "system", "content": "Write a technical memorandum to the utility from these workspace answers. Keep every "
             "number, page citation and run label; label assumptions. Sections: Purpose, Findings (one per request), "
             "Recommendations, Limitations. Markdown. First line: 'DRAFT - prepared with an AI engineering copilot; requires "
             "review and approval by a licensed professional engineer.'"},
            {"role": "user", "content": json.dumps([{k: a[k] for k in ("request", "summary", "cards")} for a in ws.answers])}])
        out = d / "memo.md"
        out.write_text(memo)
        return out
    if kind == "dwg":
        import pymupdf
        page = pymupdf.open(ws.case.pdf)[ws.drawing["page"] - 1]
        sheet = cad.pdf_page_to_dxf(ws.case.pdf, ws.drawing["page"], d / "sheet.dxf")
        layers = [l for a in ws.answers for l in (a.get("layers") or []) if l.get("bbox")]
        changes = [{"bbox": [b[0] - 0.012, b[1] - 0.012, b[2] + 0.012, b[3] + 0.012], "note": l["text"][:120]}
                   for l in layers for b in [l["bbox"]]]
        rev = {"number": "B", "date": time.strftime("%Y-%m-%d"), "by": "COPILOT",
               "description": "WORKSPACE MARKUPS - FOR ENGINEER REVIEW, NOT FOR CONSTRUCTION"}
        red = cad.redline(sheet, d / "markup.dxf", changes, rev, [0, 0, page.rect.width, page.rect.height])
        sheet.unlink()
        return cad.oda_convert(red, "DWG")
    if kind == "profile":
        label = ws.base.get("design_profile_run") or next(reversed(ws.profiles))
        for a in reversed(ws.answers):  # prefer the latest profile run the copilot made
            mine = [r for c in a.get("cards", []) for r in (c.get("runs") or []) if r in ws.profiles]
            if mine:
                label = mine[-1]
                break
        p = ws.profiles[label]
        design.profile_sheet(p["spec"], sorted({float(q) for q in p["flows"]}), d / "profile_sheet.dxf",
                             "Hydraulic profile", f"{ws.case.cfg['title']} - {label}")
        return cad.oda_convert(d / "profile_sheet.dxf", "DWG")
    raise ValueError(f"unknown export {kind}")


# --- edits: properties panel and the CAD round trip --------------------------------------------
EDITABLE = {"control": ["ws_ft", "required_drop_ft"], "pipe": ["length_ft", "diameter_in", "c_factor", "minor_k"],
            "weir": ["crest_ft", "length_ft", "notches"], "orifice": ["area_ft2", "cd"], "drop": ["loss_ft"]}
COMMON = ["max_ws_ft", "max_flow_mgd", "share"]
PARAM_LAYER = "PA-PARAMS"


def elements(ws, label):
    """Editable fields of every element of a profile run, with the drawing structure each one is anchored to."""
    from .deliver import _anchor
    spec = ws.profiles[label]["spec"]
    out = []
    for e in [{"type": "control", **spec["start"]}] + spec["elements"]:
        fields = [f for f in EDITABLE.get(e["type"], []) + COMMON if f in e or f in EDITABLE.get(e["type"], [])]
        a = _anchor(ws.drawing, e["drawing_ws_ft"], e["id"]) if ws.drawing and "drawing_ws_ft" in e else None
        out.append({"id": e["id"], "type": e["type"], "structure": a["structure"] if a else None, "bbox": a["bbox"] if a else None,
                    "calibrated": bool(e.get("calibrate")),
                    "fields": {f: e.get(f) for f in fields}})
    return out


def _changed_spec(spec, element_id, field, value):
    spec = json.loads(json.dumps(spec))
    e = next(x for x in [spec["start"]] + spec["elements"] if x["id"] == element_id)
    old = e.get(field)
    cal = e.get("calibrate")
    if cal and e.get("type") == "pipe" and old and field in ("diameter_in", "length_ft", "c_factor"):
        # keep the field calibration and scale its measured loss by Hazen-Williams: h ~ L / (C^1.852 D^4.87)
        k = {"diameter_in": (old / float(value)) ** 4.87, "length_ft": float(value) / old,
             "c_factor": (old / float(value)) ** 1.852}[field]
        cal["headloss_ft"] = cal["headloss_ft"] * k
    elif cal and e.get("type") == "pipe" and field in ("diameter_in", "length_ft", "c_factor"):
        raise ValueError(f"{element_id} is calibrated without a stated {field}; edit its calibration loss instead")
    e[field] = float(value)
    return spec, old


def edit(ws, label, element_id, field, value, source="properties panel"):
    """Apply one engineering change to a copy of a profile run; logs a revision. No LLM: the solver re-runs instantly."""
    from . import profile
    base = ws.profiles[label]
    spec, old = _changed_spec(base["spec"], element_id, field, value)
    root = label.split("~")[0]
    n = sum(1 for k in ws.profiles if k.startswith(root + "~")) + 1
    new = f"{root}~r{n}"
    ws.profiles[new] = {"purpose": f"{label} with {element_id}.{field} {old} -> {value} ({source})", "spec": spec,
                        "flows": base.get("flows") or [12, 18]}
    rev = {"n": len(ws.revisions) + 1, "time": time.strftime("%H:%M:%S"), "from": label, "to": new, "element": element_id,
           "field": field, "old": old, "new": float(value), "source": source}
    ws.revisions.append(rev)
    (ws.dir / "revisions.json").write_text(json.dumps(ws.revisions, indent=1))
    ws.current = new
    return {"label": new, "revision": rev, "capacity": profile.capacity(spec)}


LIMIT_FIELDS = {"max_ws_ft", "min_ws_ft", "max_flow_mgd"}


def _loosened_limits(ws, run):
    """Limits a cited profile run relaxes against the current model (same element ids)."""
    base = ws.profiles.get(current_label(ws), {}).get("spec") or {}
    cur = {e["id"]: e for e in [base.get("start", {})] + base.get("elements", []) if e}
    out = []
    for e in [run["spec"].get("start", {})] + run["spec"].get("elements", []):
        b = cur.get(e.get("id"))
        for f in ("max_ws_ft", "max_flow_mgd"):
            if b and f in b and e.get(f) is not None and float(e[f]) > float(b[f]) + 1e-9:
                out.append(f"{e['id']}.{f} {b[f]} -> {e[f]}")
        if b and "min_ws_ft" in b and e.get("min_ws_ft") is not None and float(e["min_ws_ft"]) < float(b["min_ws_ft"]) - 1e-9:
            out.append(f"{e['id']}.min_ws_ft {b['min_ws_ft']} -> {e['min_ws_ft']}")
    return out


def preview(ws, p):
    """What a proposed model change does, before the engineer accepts it (no revision logged)."""
    from . import profile
    if p.get("kind") == "unit":
        from . import sim
        q = target_flow(ws)
        run_label = p.get("run_label") or ""
        r = ws.runs.get(run_label) or station_runs(ws).get(run_label) or ws.profiles.get(run_label)
        proved, proof = None, None
        if r and len(r.get("spec", {}).get("pumps", [])) >= 2:  # pump station: EPANET with each pump out in turn
            f = sim.firm_capacity(r["spec"])
            proved, proof = f["firm"], f"EPANET N-1 firm capacity of run {run_label} (worst outage {f['governing_outage']})"
        elif r and "elements" in r.get("spec", {}):  # gravity unit: the solver's limit for the element at this structure
            els = [e for e in [r["spec"]["start"]] + r["spec"]["elements"] if _structure_of(ws, e["id"], e["id"]) == p.get("structure")]
            lims = [x for x in (_profile_limit(r["spec"], e["id"]) for e in els) if x is not None]
            if lims:
                proved, proof = min(lims), f"gravity profile {run_label}: binding limit of {', '.join(e['id'] for e in els)}"
        loosened = _loosened_limits(ws, r) if r and "elements" in r.get("spec", {}) else []
        if loosened:
            proved, proof = None, None
        ok = proved is not None and proved >= q
        why = ("no simulator run cited" if not r else f"the cited run raises documented limits ({', '.join(loosened)})" if loosened
               else "the cited run has no computed limit for this unit (nothing to verify)"
               if proved is None else f"solver gives {proved:g} MGD < {q:g}" if not ok else "")
        return {"kind": "unit", "target_mgd": q, "old": next((u["capacity_mgd"] for u in unit_capacities(ws) if u["unit"] == p.get("unit")), None),
                "value": proved, "claimed_mgd": p.get("capacity_mgd"), "element": p.get("unit"), "field": "capacity_mgd",
                "passes_after": bool(ok), "proved_mgd": proved, "proof": proof, "failing_after": [why] if why else []}
    label = p.get("profile_label") if p.get("profile_label") in ws.profiles else current_label(ws)
    if p.get("field") in LIMIT_FIELDS:  # a documented limit does not move without a physical change behind it
        return {"profile_label": label, "old": None, "target_mgd": target_flow(ws), "passes_before": None, "passes_after": False,
                "failing_after": [f"{p['field']} is a documented limit: it only changes with a physical modification and its own "
                                  "evidence, so the simulator cannot verify this"], "unverified_reason": "changes a documented limit"}
    spec, old = _changed_spec(ws.profiles[label]["spec"], p["element"], p["field"], p["value"])
    q = target_flow(ws)
    before, after = profile.run(ws.profiles[label]["spec"], q), profile.run(spec, q)
    return {"profile_label": label, "old": old, "target_mgd": q, "passes_before": before["passes"], "passes_after": after["passes"],
            "failing_after": [f"{c['id']}: {c['check']}" for c in after["checks"] if c["margin"] < 0]}


def accept(ws, p):
    check = preview(ws, p)  # recompute: the client's claim is never trusted
    if not check["passes_after"]:
        raise ValueError("not verified by the solver: " + "; ".join(check["failing_after"] or ["fails at target"]))
    p = {**p, **check}
    if p.get("kind") == "unit":
        ws.unit_overrides = {**getattr(ws, "unit_overrides", {}), p["unit"]: p["proved_mgd"]}
        rev = {"n": len(ws.revisions) + 1, "time": time.strftime("%H:%M:%S"), "from": current_label(ws), "to": current_label(ws),
               "element": p["unit"], "field": "capacity_mgd", "old": p.get("old"), "new": p["proved_mgd"],
               "source": "accepted proposal: " + p.get("title", "") + f" (run {p.get('run_label')})"}
        ws.revisions.append(rev)
        ws.accepted = getattr(ws, "accepted", []) + [{"element": p["unit"], "unit": p["unit"], "structure": p.get("structure"),
                                                      "title": p.get("title", ""), "label": current_label(ws), "resolves": p.get("resolves"),
                                                      "rev": rev["n"], "capacity_mgd": p["proved_mgd"], "proved_mgd": p["proved_mgd"],
                                                      "proof": p["proof"]}]
        if p.get("resolves"):
            ws.resolved.add(p["resolves"])
        return {"label": current_label(ws), "revision": rev, "capacity": []}
    r = edit(ws, p["profile_label"], p["element"], p["field"], p["value"], source="accepted proposal: " + p.get("title", ""))
    lim = _profile_limit(ws.profiles[r["label"]]["spec"], p["element"])
    ws.accepted = getattr(ws, "accepted", []) + [{"element": p["element"], "structure": p.get("structure"), "title": p.get("title", ""),
                                                  "label": r["label"], "resolves": p.get("resolves"), "rev": r["revision"]["n"],
                                                  "proved_mgd": lim if lim is not None else target_flow(ws) if p.get("passes_after") else None,
                                                  "proof": f"gravity profile {r['label']}: {p['element']} " +
                                                           (f"binds at {lim:g} MGD" if lim is not None else f"passes {target_flow(ws):g} MGD with no limit reached")}]
    if p.get("resolves"):
        ws.resolved.add(p["resolves"])
    return r


def restore(ws, upto_rev):
    """Checkpoint restore: keep accepted changes up to revision `upto_rev` (0 = existing plant)."""
    keep = [a for a in getattr(ws, "accepted", []) if a["rev"] <= int(upto_rev)]
    ws.accepted = keep
    ws.current = next((a["label"] for a in reversed(keep) if "unit" not in a), None)
    ws.unit_overrides = {a["unit"]: a["capacity_mgd"] for a in keep if "unit" in a}
    ws.resolved = {a["resolves"] for a in keep if a.get("resolves")}
    return {"current": current_label(ws), "accepted": keep}


def target_flow(ws):
    t = ws.case.cfg.get("workspace", {}).get("target_mgd")
    if not t:
        raise ValueError(f"{ws.case.name}: case.json workspace.target_mgd is not set")
    return float(t)


def current_label(ws):
    w = ws.case.cfg.get("workspace", {})
    for k in (getattr(ws, "current", None), w.get("existing_profile"), (ws.base or {}).get("base_profile_run")):
        if k in ws.profiles:
            return k
    return next(iter(ws.profiles), None)


def export_editable(ws, label):
    """The real sheet as DXF + DWG with the model's design parameters as plain text on layer PA-PARAMS
    ('settled42.diameter_in = 42'), placed at each structure. Edit any value in AutoCAD/LibreCAD and import the file back."""
    import ezdxf
    import pymupdf

    from . import cad
    page = pymupdf.open(ws.case.pdf)[ws.drawing["page"] - 1]
    W, H = page.rect.width, page.rect.height
    d = ws.dir
    dxf = cad.pdf_page_to_dxf(ws.case.pdf, ws.drawing["page"], d / f"{label}_editable.dxf")
    doc = ezdxf.readfile(dxf)
    if PARAM_LAYER not in doc.layers:
        doc.layers.add(PARAM_LAYER, color=3)
    msp = doc.modelspace()
    params, free_y = [], 0.06
    for el in elements(ws, label):
        rows = [(f, v) for f, v in el["fields"].items() if v is not None]
        if el["bbox"]:
            x, y = el["bbox"][0] * W, H - el["bbox"][3] * H - 9
        else:  # unanchored elements go in a parameter table at the lower left
            x, y = 0.05 * W, free_y * H
            free_y += 0.012 * (len(rows) + 1)
        for i, (f, v) in enumerate(rows):
            txt = f"{el['id']}.{f} = {v:g}" if isinstance(v, (int, float)) else f"{el['id']}.{f} = {v}"
            msp.add_text(txt, height=4.2, dxfattribs={"layer": PARAM_LAYER, "insert": (x, y - 6 * i)})
            params.append({"element": el["id"], "field": f, "value": v})
    msp.add_text(f"PLANTAGENT MODEL {label} - EDIT VALUES ON LAYER {PARAM_LAYER}, SAVE, IMPORT BACK", height=6,
                 dxfattribs={"layer": PARAM_LAYER, "insert": (0.05 * W, 0.03 * H)})
    doc.saveas(dxf)
    counts = {}
    for e in msp:
        k = f"{e.dxf.layer}:{e.dxftype()}"
        counts[k] = counts.get(k, 0) + 1
    (d / f"{label}_editable.json").write_text(json.dumps({"label": label, "params": params, "counts": counts}, indent=1))
    try:
        cad.oda_convert(dxf, "DWG")
    except Exception:
        pass
    return dxf


def import_cad(ws, path):
    """Read a sheet the engineer edited in CAD: changed PA-PARAMS values become model revisions (re-solved), and any
    entities they added elsewhere (lines, notes) are listed so the copilot can be asked about them."""
    import ezdxf

    from . import cad
    path = Path(path)
    if path.suffix.lower() == ".dwg":
        path = cad.oda_convert(path, "DXF")
    msp = ezdxf.readfile(path).modelspace()
    found, notes, counts = {}, [], {}
    for e in msp:
        k = f"{e.dxf.layer}:{e.dxftype()}"
        counts[k] = counts.get(k, 0) + 1
        if e.dxftype() in ("TEXT", "MTEXT"):
            t = e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text
            m = re.match(r"\s*([\w\-. ]+?)\.(\w+)\s*=\s*(-?[\d.]+)", t)
            if e.dxf.layer == PARAM_LAYER and m:
                found[(m.group(1), m.group(2))] = float(m.group(3))
            elif e.dxf.layer != PARAM_LAYER and e.dxf.layer.upper() not in ("0",) and len(t) > 2:
                notes.append({"layer": e.dxf.layer, "text": t})
    manifests = sorted(ws.dir.glob("*_editable.json"), key=lambda p: p.stat().st_mtime)
    if not manifests:
        raise ValueError("export an editable sheet first")
    man = json.loads(manifests[-1].read_text())
    label, changes = man["label"], []
    for p in man["params"]:
        v = found.get((p["element"], p["field"]))
        if v is not None and isinstance(p["value"], (int, float)) and abs(v - p["value"]) > 1e-9:
            r = edit(ws, label, p["element"], p["field"], v, source=f"CAD import {path.name}")
            label = r["label"]
            changes.append(r["revision"])
    added = {k: counts.get(k, 0) - man["counts"].get(k, 0) for k in counts if counts.get(k, 0) > man["counts"].get(k, 0)}
    removed = {k: man["counts"][k] - counts.get(k, 0) for k in man["counts"] if counts.get(k, 0) < man["counts"][k]}
    from . import profile
    return {"file": path.name, "changes": changes, "label": label, "added_entities": added, "removed_entities": removed,
            "engineer_notes": notes[:20], "capacity": profile.capacity(ws.profiles[label]["spec"])}



# --- problems panel and tasks ------------------------------------------------------------------
PLAIN = {"standard": "Design standard", "limit": "Over capacity", "QA/QC": "Checker concern", "RFI": "Missing information",
         "calibration": "Model fit", "assumption": "Assumption"}


def _structure_of(ws, text, element=None):
    """Which drawing structure an issue is about: the element's drawing anchor, else a structure named in the text."""
    from .deliver import _anchor
    if element and ws.drawing:
        for lab in ws.profiles:
            e = next((x for x in [ws.profiles[lab]["spec"]["start"]] + ws.profiles[lab]["spec"]["elements"]
                      if x["id"] == element and "drawing_ws_ft" in x), None)
            if e:
                a = _anchor(ws.drawing, e["drawing_ws_ft"], e["id"])
                return a["structure"] if a else None
    generic = {"water", "pump", "pumps", "station", "basin", "basins", "main", "plant", "overflow", "with"}
    hints = {"raw": "intake", "fish": "intake", "screens": "intake", "settled": "sedimentation", "launder": "sedimentation"}
    words = {w.rstrip("s") for w in re.findall(r"[a-z]{3,}", text.lower())}
    words |= {hints[w] for w in list(words) if w in hints}
    best, score = None, 0.0
    for name in {e["structure"] for e in (ws.drawing or {}).get("elevations", [])}:
        sc = sum((0.4 if w in generic else 2.0) for w in {x.rstrip("s") for x in re.findall(r"[a-z]{3,}", name.lower())} if w in words)
        if sc > score:
            best, score = name, sc
    return best if score >= 2.0 else None


SIDE = re.compile(r"wastewater|backwash|drain|solids|sludge", re.I)


def failing_units(ws):
    q = target_flow(ws)
    return [u for u in unit_capacities(ws) if u["capacity_mgd"] is not None and u["capacity_mgd"] < q and not SIDE.search(u["full_unit"])]


def check_answer(ws, ans):
    """Second-engineer check, deterministic: cited runs exist in the log, cited pages contain the quoted number,
    proposals reproduce in the solver."""
    runs = [r for c in ans.get("cards") or [] if isinstance(c, dict) for r in (c.get("runs") or [])]
    known = set(ws.runs) | set(ws.profiles) | set(ws.surges) | set(ws.eps_runs)
    runs_found = sum(1 for r in runs if any(k in str(r) for k in known))
    cites, ok = 0, 0
    docs = list(ws.project.docs)
    for c in ans.get("cards") or []:
        for i in (c.get("inputs") or []) if isinstance(c, dict) else []:
            m = re.search(r"p\.(\d+)", str(i.get("source", "")))
            num = re.search(r"\d+(?:\.\d+)?", str(i.get("value", "")))
            if not (m and num):
                continue
            cites += 1
            # the cited document must be named (or be the only one), and the number must appear as a whole number
            doc = next((d for d in docs if d in str(i.get("source", "")).lower()), docs[0] if len(docs) == 1 else None)
            if doc is None:
                continue
            try:
                text = ws.project.page(doc, int(m.group(1)))
            except Exception:
                continue
            ok += bool(re.search(rf"(?<![\d.]){re.escape(num.group(0))}(?![\d]|\.\d)", text.replace(",", "")))
    props = [p for p in ans.get("proposals") or [] if isinstance(p, dict)]
    return {"runs_cited": len(runs), "runs_found": runs_found, "cites": cites, "cites_ok": ok,
            "proposals": len(props), "proposals_verified": sum(1 for p in props if p.get("passes_after")),
            "assumptions": sum(len(c.get("assumptions") or []) for c in ans.get("cards") or [] if isinstance(c, dict))}


def problems(ws, flow_mgd=None):
    """Everything currently wrong or unverified in the project, like a compiler's problem list."""
    from . import profile
    out = []
    st = ws.study or {}
    for c in st.get("standards_checks") or []:
        if c.get("status") == "FAIL":
            out.append({"severity": "error", "kind": "standard", "text": f"{c['rule_id']} {c['rule']} (value {c['value']}, limit {c['limit']})",
                        "source": c.get("citation", ""), "ref": c.get("basis")})
    label = current_label(ws)
    flow_mgd = flow_mgd or (target_flow(ws) if label else None)
    if label in ws.profiles and flow_mgd:
        r = profile.run(ws.profiles[label]["spec"], float(flow_mgd))
        for c in r["checks"]:
            if c["margin"] < 0:
                out.append({"severity": "error", "kind": "limit", "text": f"{c['id']}: {c['check']} exceeded at {flow_mgd:g} MGD "
                            f"(margin {c['margin']})", "source": f"profile run {label}", "ref": c["id"]})
    for i in (st.get("review") or {}).get("issues") or []:
        resp = next((r for r in (st.get("resolution") or {}).get("responses") or [] if str(r.get("issue", ""))[:40] == str(i.get("issue", ""))[:40]), None)
        if not resp or resp.get("action") != "fixed":
            out.append({"severity": "warning" if i.get("severity") == "minor" else "error", "kind": "QA/QC",
                        "text": f"{i.get('item', '')}: {i.get('issue', '')}"[:220], "source": "independent checker",
                        "ref": (resp or {}).get("action", "open")})
    for r in (st.get("collection") or {}).get("rfi") or []:
        out.append({"severity": "warning", "kind": "RFI", "text": f"{r.get('item', '')}: {r.get('issue', '')}"[:200],
                    "source": "data register", "ref": r.get("resolution", "")[:80]})
    scored = {k: v for k, v in ws.eps_runs.items() if (v.get("result") or {}).get("mean_relative_rmse") is not None}
    best = min(scored, key=lambda k: scored[k]["result"]["mean_relative_rmse"]) if scored else None
    for k, v in ([(best, scored[best])] if best else []):
        for f in (v.get("result") or {}).get("fit") or []:
            if f.get("nse") is not None and f["nse"] < 0.8 and ":flow" in f["series"]:
                out.append({"severity": "warning", "kind": "calibration", "text": f"{f['series']} NSE {f['nse']} (target >= 0.8), bias {f['bias']}",
                            "source": f"run {k}", "ref": f["series"]})
    for a in (st.get("analysis") or {}).get("assumptions") or []:
        out.append({"severity": "info", "kind": "assumption", "text": str(a)[:200], "source": "analysis", "ref": ""})
    import hashlib
    for p in out:
        p["id"] = hashlib.sha1((p["kind"] + p["text"][:80]).encode()).hexdigest()[:8]
        p["plain_kind"] = PLAIN.get(p["kind"], p["kind"])
        p["structure"] = _structure_of(ws, p["text"], p.get("ref") if p["kind"] == "limit" else None) if p["severity"] == "error" else None
    order = {"error": 0, "warning": 1, "info": 2}
    out = [p for p in out if p["id"] not in ws.resolved]
    return sorted(out, key=lambda p: order[p["severity"]])


def tasks(case):
    """Long agent tasks the workspace can launch for this project (each is a full study with its own question)."""
    c = case.cfg
    out = [{"id": "study", "title": f"Run the {c['task_type']} study", "detail": c["question"][:220]}]
    out.append({"id": "testplan", "title": "Write the field test plan", "task_type": "field test planning",
                "question": "Review the project documents and the current model. List every missing or unverified input that "
                            "matters to the hydraulic conclusions, and write a field test plan that would close each one "
                            "(what to measure, where, how, acceptance criteria), prioritised by how much it changes the answer."})
    out.append({"id": "standards", "title": "Check against design standards", "task_type": "design standards review",
                "question": "Check the facility as documented, and its recommended modifications, against the applicable Ten States "
                            "Standards rules. Compute each checked quantity with the simulators and cite the section."})
    if "eps" not in c:
        out.append({"id": "surge", "title": "Pump-trip surge check", "task_type": "surge analysis", "simulators": ["tsnet"],
                    "question": "Build the pumped system from the documents and check what happens on a power failure that trips all "
                                "pumps: minimum and maximum pressures along the pipeline, column separation risk, and the smallest "
                                "protection that works."})
    else:
        out.append({"id": "calibrate", "title": "Calibrate the model to SCADA", "task_type": "model calibration against SCADA time series",
                    "question": c["question"]})
    return out


def _profile_limit(spec, element_id):
    """The flow at which the solver says this element hits a limit (None when the model has no limit for it)."""
    from . import profile
    v = [c["binds_at_mgd"] for c in profile.capacity(spec) if c["id"] == element_id and isinstance(c["binds_at_mgd"], (int, float))]
    return min(v) if v else None


def _station_for(ws, unit_text):
    """EPANET station model that represents a pump-station unit (raw water / high service), by its pump id prefix."""
    t = unit_text.lower()
    if "pump" not in t:
        return None
    prefix = "RW" if "raw" in t else "HS" if ("high-service" in t or "high service" in t or "finished" in t) else None
    if not prefix:
        return None
    # the existing station with every installed pump available (firm capacity then takes the largest one out)
    runs = [(k, v) for k, v in station_runs(ws).items() if all(p["id"].upper().startswith(prefix) for p in v["spec"]["pumps"])
            and all(p.get("on", True) for p in v["spec"]["pumps"])
            and not re.search(r"ALT|UPG|ADD|FIX|NEW|PROP|FUT|DESIGN|6PUMP|[-_](1[89]|2[0-4])([^0-9]|$)", k.upper())]
    # one source of truth: the run the study itself computed firm capacity on wins (that is the number in its report);
    # then an explicitly 'existing' run; then the one with the most installed pumps
    return max(runs, key=lambda kv: (bool(kv[1].get("firm")), "EXIST" in kv[0].upper(), len(kv[1]["spec"]["pumps"]),
                                     "NOM" in kv[0].upper(), kv[0]), default=None)


def unit_capacities(ws, view="proposed"):
    """Capacity by unit. Each value says where it comes from: 'simulated' (EPANET N-1 firm capacity or the gravity
    profile's binding limit) or 'documented' (the study's capacity table, quoted with its range). Accepted changes
    replace a value only with the number the solver computed for them."""
    from . import sim
    st = ws.study or {}
    rows = []
    num = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|to|–)?\s*(\d+(?:\.\d+)?)?\s*mgd", re.I)
    for r in (st.get("analysis") or {}).get("capacity_table") or []:
        text = str(r.get("binds_at", "")) + " " + str(r.get("limit", ""))
        m = num.search(text)
        lo, hi = (float(m.group(1)), float(m.group(2)) if m.group(2) else None) if m else (None, None)
        full = str(r.get("unit", ""))
        row = {"unit": re.split(r"\s*[+(/]\s*|\s+-\s+", full)[0].strip()[:26], "full_unit": full, "capacity_mgd": lo,
               "range": f"{lo:g}-{hi:g}" if hi else None, "limit": str(r.get("limit", ""))[:80], "source": "documented",
               "limits_target": bool(r.get("limits_target")), "structure": _structure_of(ws, full + " " + str(r.get("limit", "")))}
        stn = _station_for(ws, full)
        if stn and "FIRM" in stn[0].upper():  # the run already models the station with its largest unit out
            res = sim.run(stn[1]["spec"])
            row.update({"capacity_mgd": round(res.get("total_pumped_mgd") or 0, 1), "documented": lo,
                        "source": f"simulated: EPANET run {stn[0]} (firm configuration as modelled)"})
            stn = None
        if stn and stn[1].get("firm"):  # reuse the study's own N-1 result, so the workspace and the report agree
            f = stn[1]["firm"]
            row.update({"capacity_mgd": round(f["firm"], 1), "documented": lo,
                        "source": f"simulated: EPANET N-1, run {stn[0]} (worst outage {f.get('governing_outage')}), as in the study report"})
            stn = None
        if stn:
            try:
                f = sim.firm_capacity(stn[1]["spec"])
                row.update({"capacity_mgd": round(f["firm"], 1), "source": f"simulated: EPANET N-1, run {stn[0]} (worst outage {f['governing_outage']})",
                            "documented": lo})
            except ValueError:
                pass
        rows.append(row)
    label = current_label(ws) if view != "existing" else ((ws.case.cfg.get("workspace") or {}).get("existing_profile") or current_label(ws))
    if label in ws.profiles:
        spec = ws.profiles[label]["spec"]
        from . import profile
        caps = profile.capacity(spec)
        generic = {"water", "pipeline", "basin", "basins", "nominal", "single", "plant", "limit", "check", "max", "surface"}
        for e in [spec["start"]] + spec["elements"]:
            mine = [c for c in caps if c["id"] == e["id"] and isinstance(c["binds_at_mgd"], (int, float))]
            if not mine:
                continue
            gov = min(mine, key=lambda c: c["binds_at_mgd"])
            words = set(re.findall(r"[a-z]{4,}", (e["id"] + " " + gov["check"] + " " + (_structure_of(ws, e["id"], e["id"]) or "")).lower())) - generic
            words |= {"sedimentation", "flocculation"} if "basin" in gov["check"].lower() else set()
            best = max((r for r in rows if r["source"] == "documented" and not SIDE.search(r["full_unit"])),
                       key=lambda r: len(words & set(re.findall(r"[a-z]{4,}", r["full_unit"].lower()))), default=None)
            if best and words & set(re.findall(r"[a-z]{4,}", best["full_unit"].lower())):
                best.update({"capacity_mgd": round(gov["binds_at_mgd"], 1),
                             "source": f"simulated: gravity profile {label}, {e['id']} ({gov['check']})"})
    # treatment ratings computed from unit dimensions (Ten States) replace documented ratings, or bind if lower
    for t in st.get("treatment_capacity") or []:
        key = {"floc": "floc", "sed": "sedim", "filt": "filter"}.get(t["type"][:4] if t["type"][:4] != "sedi" else "sed")
        row = next((r for r in rows if key and key in r["full_unit"].lower() and not SIDE.search(r["full_unit"])), None)
        if row and t.get("capacity_mgd") is not None and (row["source"] == "documented" or t["capacity_mgd"] < (row["capacity_mgd"] or 1e9)):
            row.update({"documented": row.get("documented") or (row["capacity_mgd"] if row["source"] == "documented" else None),
                        "capacity_mgd": t["capacity_mgd"], "source": f"computed: Ten States, {t['governing']}"})
    if view != "existing":
        for a in getattr(ws, "accepted", []):
            if a.get("proved_mgd") is None:
                continue
            for r in rows:
                if r["unit"] == a.get("unit") or (a.get("structure") and r["structure"] == a["structure"]
                                                  and set(re.findall(r"[a-z]{5,}", a.get("title", "").lower())) & set(re.findall(r"[a-z]{5,}", r["full_unit"].lower()))):
                    r.update({"capacity_mgd": round(a["proved_mgd"], 1), "changed": a["title"], "source": a["proof"]})
    return rows


# --- field photo: nameplate or gauge read by Muse, checked against the model, applied as a revision ----------
PHOTO_SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "kind": {"type": "string", "enum": ["pump nameplate", "motor nameplate", "pressure gauge", "flow meter", "other"]},
    "maker": {"type": "string"}, "model_or_tag": {"type": "string"},
    "flow": {"type": "object", "additionalProperties": False, "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": "string"}}, "required": ["value", "unit"]},
    "head": {"type": "object", "additionalProperties": False, "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": "string"}}, "required": ["value", "unit"]},
    "speed_rpm": {"type": ["number", "null"]},
    "power": {"type": "object", "additionalProperties": False, "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": "string"}}, "required": ["value", "unit"]},
    "pressure": {"type": "object", "additionalProperties": False, "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": "string"}}, "required": ["value", "unit"]},
    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    "unreadable": {"type": "array", "items": {"type": "string"}}, "verbatim": {"type": "string"}},
    "required": ["kind", "maker", "model_or_tag", "flow", "head", "speed_rpm", "power", "pressure", "confidence", "unreadable", "verbatim"]}
TO_US = {"gpm": 1, "usgpm": 1, "us gpm": 1, "m3/h": 4.4029, "m³/h": 4.4029, "l/s": 15.8503, "lps": 15.8503, "m3/s": 15850.3, "l/min": 0.26417,
         "ft": 1, "m": 3.28084, "hp": 1, "kw": 1.34102, "psi": 1, "bar": 14.5038, "kpa": 0.145038, "mpa": 145.038}


def _us(q):
    """Convert a reading to US units; tolerant of plate wording ('GALLONS PER MIN U.S.', 'FEET', 't/h' for water)."""
    if not q or q.get("value") is None:
        return None
    k = q.get("unit", "").strip().lower().replace(" ", "").replace(".", "")
    rules = [("gal", 1), ("gpm", 1), ("m3/h", 4.4029), ("m³/h", 4.4029), ("t/h", 4.4029), ("l/s", 15.8503), ("lps", 15.8503),
             ("l/min", 0.26417), ("feet", 1), ("ft", 1), ("kw", 1.34102), ("hp", 1), ("psi", 1), ("bar", 14.5038), ("kpa", 0.145038),
             ("mpa", 145.038)]
    f = next((v for u, v in rules if u in k), 3.28084 if k in ("m", "meter", "meters", "metre", "metres") else None)
    return round(q["value"] * f, 1) if f else None


def plate_checks(r):
    """Deterministic sanity checks on a nameplate reading: specific speed and digits next to a letter O."""
    out = []
    q, h, n = r["us"].get("flow_gpm"), r["us"].get("head_ft"), r.get("speed_rpm")
    ns = lambda q_: n * q_ ** 0.5 / h ** 0.75  # noqa: E731  US specific speed
    if q and h and n:
        r["us"]["specific_speed"] = round(ns(q))
        if not 1000 <= ns(q) <= 10000:  # typical single-stage centrifugal / mixed-flow range
            alt = [x for x in (q * 10, q / 10) if 1000 <= ns(x) <= 10000]
            out.append({"check": "specific speed", "status": "suspicious",
                        "note": f"Ns = {ns(q):.0f} is outside the usual 1,000-10,000 for a single-stage pump (multistage pumps: check per stage)" +
                                (f"; {alt[0]:,.0f} gpm gives Ns = {ns(alt[0]):.0f}" if alt else ""),
                        "suggested_flow_gpm": alt[0] if alt else None})
        else:
            out.append({"check": "specific speed", "status": "ok", "note": f"Ns = {ns(q):.0f}, plausible for a centrifugal pump"})
    m = re.search(r"(\d{3,})\s*O\b", r.get("verbatim", ""))
    if m:
        out.append({"check": "letter O next to digits", "status": "suspicious",
                    "note": f"plate shows '{m.group(0)}': the O may be a zero ({m.group(1)}0)"})
    return out


def read_photo(ws, data, model=None):
    """Muse reads a field photo into a structured reading (vision + JSON schema); Python converts the units and finds the
    model pump it most likely belongs to."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((1600, 1600))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    llm.set_tag("photo:" + ws.case.name)
    msg = llm.complete(model or ws.model, [
        {"role": "system", "content": "You read equipment nameplates and gauges in field photos for an engineer. Report only what is "
                                      "legible; put anything you cannot read in `unreadable`; never guess. Copy the plate text verbatim."},
        {"role": "user", "content": [{"type": "text", "text": "Read this field photo."}, {"type": "image_url", "image_url": {"url": url}}]}],
        response_format={"type": "json_schema", "json_schema": {"name": "field_reading", "schema": PHOTO_SCHEMA, "strict": True}})
    text = msg["content"] or "{}"
    r = json.loads(text[text.index("{"): text.rindex("}") + 1])
    r["us"] = {"flow_gpm": _us(r.get("flow")), "head_ft": _us(r.get("head")), "power_hp": _us(r.get("power")), "pressure_psi": _us(r.get("pressure"))}
    r["checks"] = plate_checks(r)
    sug = next((c["suggested_flow_gpm"] for c in r["checks"] if c.get("suggested_flow_gpm")), None)
    r["candidates"] = match_pumps(ws, sug or r["us"]["flow_gpm"], r["us"]["head_ft"])
    return r


def station_runs(ws):
    """EPANET station models from this and earlier studies of the project (pumps with rated points)."""
    out = {k: v for k, v in ws.runs.items() if len(v.get("spec", {}).get("pumps", [])) >= 2}
    for d in sorted((ROOT / "runs" / ws.case.name).glob("2*")):
        if (d / "study.json").exists():
            for k, v in json.loads((d / "study.json").read_text()).get("runs", {}).items():
                if len(v.get("spec", {}).get("pumps", [])) >= 3:
                    out.setdefault(k, v)
    return out


def match_pumps(ws, gpm, head):
    import math as _m
    cands = []
    for label, r in station_runs(ws).items():
        for p in r["spec"]["pumps"]:
            q, h = p.get("rated_gpm"), p.get("rated_head_ft")
            if not (q and h):
                continue
            d = abs(_m.log(gpm / q)) + abs(_m.log(head / h)) if gpm and head else 9
            cands.append({"run": label, "pump": p["id"], "rated_gpm": q, "rated_head_ft": h, "distance": round(d, 2)})
    cands.sort(key=lambda c: c["distance"])
    seen, out = set(), []
    for c in cands:
        if (c["rated_gpm"], c["rated_head_ft"], c["pump"]) not in seen:
            seen.add((c["rated_gpm"], c["rated_head_ft"], c["pump"]))
            out.append({**c, "match": "close" if c["distance"] < 0.25 else "different equipment" if c["distance"] > 0.8 else "partial"})
    return out[:6]


def apply_photo(ws, run, pump_id, gpm, head, note="", force=False):
    """Replace a pump's rated point with the field reading, re-run EPANET, and log the revision. Refused (nothing is
    written) when the reading cannot be this pump: >2x off the modelled rating, or the motor would be overloaded."""
    from . import sim
    base = station_runs(ws)[run]
    spec = json.loads(json.dumps(base["spec"]))
    p = next(x for x in spec["pumps"] if x["id"] == pump_id)
    old = (p.get("rated_gpm"), p.get("rated_head_ft"))
    blocks = []
    for name, new, was in (("flow", float(gpm), old[0]), ("head", float(head), old[1])):
        if was and not 0.5 <= new / was <= 2.0:
            blocks.append(f"{name} {new:g} is {new / was:.1f}x the modelled {was:g}: probably not this pump, or a misread")
    p.pop("curve", None)
    p["rated_gpm"], p["rated_head_ft"] = float(gpm), float(head)
    before, after = sim.run(base["spec"]), sim.run(spec)
    blocks += [w for w in after.get("warnings", []) if "exceeds" in w and pump_id in w]
    if blocks and not force:
        return {"blocked": True, "reasons": blocks, "before_mgd": before.get("total_pumped_mgd"),
                "note": "Nothing was written to the model. Confirm the equipment tag in the field, or correct the reading."}
    label = f"{run}~field{len(ws.revisions) + 1}"
    ws.runs[label] = {"purpose": f"{run} with {pump_id} at field reading {gpm} gpm @ {head} ft {note}", "spec": spec, "result": after}
    rev = {"n": len(ws.revisions) + 1, "time": time.strftime("%H:%M:%S"), "from": run, "to": label, "element": pump_id,
           "field": "rated point (field photo)", "old": f"{old[0]} gpm @ {old[1]} ft", "new": f"{gpm} gpm @ {head} ft", "source": "field photo " + note}
    ws.revisions.append(rev)
    return {"label": label, "revision": rev, "before_mgd": before.get("total_pumped_mgd"), "after_mgd": after.get("total_pumped_mgd"),
            "pumps_before": before["pumps"], "pumps_after": after["pumps"], "warnings": after.get("warnings", [])}

if __name__ == "__main__":
    import sys
    from .docs import Case
    p = Project(Case("roseburg"))
    h = p.history("production", "MDD maximum day", as_of_year=2005, project_to=[2025])
    assert h["trend"]["years"] == [1992, 2005] and "projection" in h["trend"], h
    assert structures("roseburg") and all(len(s["bbox"]) == 4 for s in structures("roseburg"))
    ws = Workspace("roseburg")
    lab = ws.base["base_profile_run"]
    pipe = next(e for e in ws.profiles[lab]["spec"]["elements"] if e["type"] == "pipe" and "diameter_in" in e)
    before = ws.profiles[lab]["spec"]
    r = edit(ws, lab, pipe["id"], "diameter_in", pipe["diameter_in"] + 6)
    from . import profile as _p
    b0 = {(c["id"], c["check"]): c["binds_at_mgd"] for c in _p.capacity(before)}
    assert any((c["binds_at_mgd"] or 99) > (b0[(c["id"], c["check"])] or 99) for c in r["capacity"]), "a bigger pipe must raise a limit"
    print("ok", h["trend"], [s["name"] for s in structures("roseburg")])
    if len(sys.argv) > 1:
        ws = Workspace("roseburg")
        print(json.dumps(ws.ask(" ".join(sys.argv[1:])), indent=1)[:3000])
