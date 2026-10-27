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
                  "items": {"type": "object", "properties": {"title": S, "element": S, "field": S, "value": N, "structure": S,
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
                  "resolves); the workspace verifies it in the solver and the engineer accepts it.\n" + RULES +
                  (DRAWING_RULES if self.drawing else ""))
        brief = {"project": c.cfg["title"], "documents": docs, "datasets": {k: v.get("title", k) for k, v in self.project.datasets.items()},
                 "preloaded": self.base, "earlier_answers": [a["summary"] for a in self.answers[-6:]],
                 "current_profile_run": current_label(self), "target_mgd": target_flow(self),
                 "open_issues": [{k: i[k] for k in ("id", "kind", "text", "structure")} for i in problems(self)[:8]]}
        if self.drawing:
            brief["drawing_elevations"] = [{k: e[k] for k in ("value", "structure", "feature")} for e in self.drawing["elevations"]]
        user = json.dumps(brief) + "\n\nRequest: " + text + (f"\nContext: {json.dumps(context)}" if context else "")
        llm.TAG = "ws:" + c.name
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


def preview(ws, p):
    """What a proposed model change does, before the engineer accepts it (no revision logged)."""
    from . import profile
    label = p.get("profile_label") if p.get("profile_label") in ws.profiles else current_label(ws)
    spec, old = _changed_spec(ws.profiles[label]["spec"], p["element"], p["field"], p["value"])
    q = target_flow(ws)
    before, after = profile.run(ws.profiles[label]["spec"], q), profile.run(spec, q)
    return {"profile_label": label, "old": old, "target_mgd": q, "passes_before": before["passes"], "passes_after": after["passes"],
            "failing_after": [f"{c['id']}: {c['check']}" for c in after["checks"] if c["margin_ft"] < 0]}


def accept(ws, p):
    r = edit(ws, p["profile_label"], p["element"], p["field"], p["value"], source="accepted proposal: " + p.get("title", ""))
    ws.accepted = getattr(ws, "accepted", []) + [{"element": p["element"], "structure": p.get("structure"), "title": p.get("title", "")}]
    if p.get("resolves"):
        ws.resolved.add(p["resolves"])
    return r


def target_flow(ws):
    return float(ws.case.cfg.get("workspace", {}).get("target_mgd") or 18)


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
            if c["margin_ft"] < 0:
                out.append({"severity": "error", "kind": "limit", "text": f"{c['id']}: {c['check']} exceeded at {flow_mgd:g} MGD "
                            f"(margin {c['margin_ft']})", "source": f"profile run {label}", "ref": c["id"]})
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


def unit_capacities(ws):
    """The capacity-by-unit chart of a capacity study: each unit's limiting flow (from the study's capacity table, or the
    current model when the engineer accepted a change there), mapped to its structure on the drawing."""
    from . import profile
    st = ws.study or {}
    rows = []
    num = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*mgd", re.I)
    for r in (st.get("analysis") or {}).get("capacity_table") or []:
        m = num.search(str(r.get("binds_at", ""))) or num.search(str(r.get("limit", "")))
        cap = float(m.group(1)) if m else None
        rows.append({"unit": str(r.get("unit", ""))[:40], "capacity_mgd": cap, "limit": str(r.get("limit", ""))[:80],
                     "limits_target": bool(r.get("limits_target")), "structure": _structure_of(ws, str(r.get("unit", "")) + " " + str(r.get("limit", "")))})
    # units changed by accepted proposals take their capacity from the current model
    label = current_label(ws)
    if label and getattr(ws, "accepted", None):
        caps = profile.capacity(ws.profiles[label]["spec"])
        for a in ws.accepted:
            el = [c for c in caps if c["id"] == a["element"]]
            lim = min((c["binds_at_mgd"] for c in el if isinstance(c["binds_at_mgd"], (int, float))), default=None)
            key = (a.get("structure") or "").split(" ")[0].lower()
            for r in rows:
                if a.get("structure") and (r["structure"] == a["structure"] or (key and key in r["unit"].lower())):
                    r.update({"capacity_mgd": lim if lim is not None else 60.0, "limits_target": False, "changed": a["title"]})
    return rows

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
