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
        self.base = self._preload()

    def _preload(self):
        """Calibrated models and data register from the latest completed study of this project."""
        done = sorted(p for p in (ROOT / "runs" / self.case.name).glob("2*") if (p / "study.json").exists())
        if not done:
            return {}
        st = json.loads((done[-1] / "study.json").read_text())
        an = st["analysis"]
        self.runs.update(st.get("runs") or {})
        self.profiles.update(st.get("profiles") or {})
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
                  "with a short label and severity). Card results are headlines; details go in inputs. Do only what was asked; "
                  "3-8 tool calls is typical.\n" + RULES +
                  (DRAWING_RULES if self.drawing else ""))
        brief = {"project": c.cfg["title"], "documents": docs, "datasets": {k: v.get("title", k) for k, v in self.project.datasets.items()},
                 "preloaded": self.base, "earlier_answers": [a["summary"] for a in self.answers[-6:]]}
        if self.drawing:
            brief["drawing_elevations"] = [{k: e[k] for k in ("value", "structure", "feature")} for e in self.drawing["elevations"]]
        user = json.dumps(brief) + "\n\nRequest: " + text + (f"\nContext: {json.dumps(context)}" if context else "")
        llm.TAG = "ws:" + c.name
        usd0 = llm.spent()
        t0 = time.time()
        ans = self.loop("ask", system, user, self.tools(), "answer", 14)
        ans["seconds"] = round(time.time() - t0)
        ans["cost_usd"] = round(llm.spent() - usd0, 4)
        ans["request"] = text
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


if __name__ == "__main__":
    import sys
    from .docs import Case
    p = Project(Case("roseburg"))
    h = p.history("production", "MDD maximum day", as_of_year=2005, project_to=[2025])
    assert h["trend"]["years"] == [1992, 2005] and "projection" in h["trend"], h
    assert structures("roseburg") and all(len(s["bbox"]) == 4 for s in structures("roseburg"))
    print("ok", h["trend"], [s["name"] for s in structures("roseburg")])
    if len(sys.argv) > 1:
        ws = Workspace("roseburg")
        print(json.dumps(ws.ask(" ".join(sys.argv[1:])), indent=1)[:3000])


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
