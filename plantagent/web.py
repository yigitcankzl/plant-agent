"""Web UI for studies: live or replayed agent log, the drawing with a flow slider, deliverables, agent vs. engineers, benchmark.

Usage: python -m plantagent.web [--port 8000]
Muse-spending UI actions are off unless WEB_ALLOW_RUNS=1 (cap: MUSE_BUDGET_USD).
"""
import argparse
import base64
import binascii
import io
import json
import math
import mimetypes
import os
import subprocess
import sys
import time
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.parsers import expat

import pymupdf

from . import eps, profile
from .deliver import _anchor
from .docs import DATA as DATA_ROOT, Case, all_cases

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
STATIC = ROOT / "web"
PHASES = {"collect": "1-2 Scope, criteria, data & RFI", "analyse": "3-6 Calibrate, model, capacity, alternatives",
          "qaqc": "7 Independent QA/QC", "resolve": "7b Lead engineer resolves QA/QC", "deliver": "8 Deliverables"}
DELIVERABLES = ["report.md", "design_profile.dwg", "design_profile.dxf", "pump_datasheets.json", "cost_estimate.md",
                "standards_check.md", "test_plan.md", "drawing_markup.png", "drawing_redline.dwg", "drawing_redline.dxf", "profile_chart.png",
                "profile.md", "calc_appendix.xlsx", "model.inp", "qaqc.md", "rfi.md", "criteria.md", "calibration.md",
                "capacity.md", "alternatives.md", "data_register.json", "findings.json", "grade.json"]


def _runs(case):
    d = RUNS / case
    if not d.is_dir() or not d.resolve().is_relative_to(ROOT.resolve()):
        return []
    return sorted((p.name for p in d.iterdir() if _safe_file(d, p.name, "log.jsonl")), reverse=True)


def _safe_file(base, *parts):
    if any(not p or p in (".", "..") or "/" in p or "\\" in p for p in parts):
        return None
    base = base.resolve()
    if not base.is_relative_to(ROOT.resolve()):
        return None
    f = base.joinpath(*parts).resolve()
    return f if f.is_relative_to(base) and f.is_file() else None


def _require_runs():
    if os.getenv("WEB_ALLOW_RUNS") != "1":
        raise PermissionError("Muse/spending actions are disabled (set WEB_ALLOW_RUNS=1)")


def _json(path, default=None):
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("file outside repository")
    return json.loads(path.read_text()) if path.exists() else default


SIM_OF = {"run_hydraulics": "EPANET", "firm_capacity": "EPANET", "run_profile": "hydraulic profile", "run_surge": "TSNet",
          "eps_run": "EPANET EPS", "eps_fit": "EPANET EPS", "run_process": "DWSIM", "bubble_pressure": "DWSIM",
          "fluid_properties": "DWSIM", "blocked_in_pressure": "DWSIM"}


def _sims_used(case, run):
    """Simulators the agent actually called in a run (from its log), for honest labels."""
    used = set()
    for line in (RUNS / case / run / "log.jsonl").open():
        if '"tool": "' in line:
            used.add(SIM_OF.get(json.loads(line).get("tool")))
    return sorted(u for u in used if u)


def cases():
    out = []
    for name in all_cases():
        c = Case(name)
        runs = _runs(name)
        done = [r for r in runs if (RUNS / name / r / "summary.json").exists()]
        grade = _json(RUNS / name / done[0] / "grade.json") if done else None
        out.append({"name": name, "title": c.cfg["title"], "task_type": c.cfg["task_type"], "question": c.question,
                    "benchmark": c.cfg.get("benchmark", True), "drawing_page": c.cfg.get("drawing_page"), "runs": runs,
                    "score": grade["score"] if grade else None, "judge": grade.get("judge") if grade else None,
                    "summary": _json(RUNS / name / done[0] / "summary.json") if done else None,
                    "simulators_used": _sims_used(name, done[0]) if done else []})
    return out


def _short(v, n=220):
    s = v if isinstance(v, str) else json.dumps(v)
    return s if len(s) <= n else s[:n] + "…"


def log_events(case, run, offset=0):
    """The run log as display events: agent narration, tool calls with short results, submissions."""
    lines = (RUNS / case / run / "log.jsonl").read_text().splitlines()
    events = []
    for line in lines[offset:]:
        e = json.loads(line)
        ph = e.get("phase", "")
        if "assistant" in e:
            if e["assistant"].get("content"):
                events.append({"phase": ph, "kind": "say", "text": e["assistant"]["content"]})
        elif "tool" in e:
            r = e["result"]
            err = isinstance(r, dict) and "error" in r
            events.append({"phase": ph, "kind": "error" if err else "tool", "name": e["tool"], "args": _short(e["args"], 160),
                           "result": _short(r)})
        elif "submit" in e:
            events.append({"phase": ph, "kind": "submit", "text": f"submitted {ph}"})
    finished = (RUNS / case / run / "summary.json").exists()
    if finished and offset + len(lines[offset:]) >= len(lines):
        events.append({"phase": "deliver", "kind": "submit", "text": "deliverables written"})
    return {"events": events, "offset": len(lines), "finished": finished}


def run_detail(case, run):
    d = RUNS / case / run
    study = _json(d / "study.json", {})
    an = study.get("analysis", {})
    key = Case(case).answer_key or {}
    grade = _json(d / "grade.json")
    verdicts = {i["id"]: i for i in (grade or {}).get("items", [])}
    return {"case": case, "run": run, "question": study.get("question") or Case(case).question,
            "summary": _json(d / "summary.json"), "score": grade["score"] if grade else None,
            "judge": grade.get("judge") if grade else None,
            "comparison": [{"unit": i["unit"], "engineers": i["engineers"], "verdict": verdicts.get(i["id"], {}).get("verdict"),
                            "note": verdicts.get(i["id"], {}).get("note")} for i in key.get("items", [])],
            "findings": an.get("findings", []), "alternatives": an.get("alternatives", []),
            "drawing_changes": [{**ch, "bbox": (_anchor(study["drawing"], ch.get("anchor_value") or -1, ch.get("structure", "")) or {}).get("bbox")}
                                for ch in an.get("drawing_changes") or [] if isinstance(ch, dict)] if study.get("drawing") else [],
            "profiles": [{"label": k, "purpose": v["purpose"], "flows": v["flows"]} for k, v in (study.get("profiles") or {}).items()],
            "base_profile": an.get("base_profile_run"), "has_drawing": bool(study.get("drawing")),
            "eps_runs": [{"label": k, "tool": v["tool"], "purpose": v["purpose"],
                          "score": v["result"].get("mean_relative_rmse", v["result"].get("after_mean_relative_rmse"))}
                         for k, v in (study.get("eps_runs") or {}).items()],
            "eps_series": list(eps.load_observations(str(__import__("plantagent.study", fromlist=["x"]).case_file(
                Case(case), Case(case).cfg["eps"]["observations"]))).keys()) if "eps" in Case(case).cfg else [],
            "files": [f for f in DELIVERABLES if (d / f).exists()]}


@lru_cache(maxsize=32)
def _eps_sim(inp, changes_json, hours):
    wn, res = eps.simulate(inp, json.loads(changes_json), hours)
    return wn, res


def eps_series(case, run, label, key):
    """Observed vs. simulated time series for one sensor: nominal model and the run's changes."""
    from .docs import DATA
    from .study import case_file
    c = Case(case)
    cfg = c.cfg["eps"]
    inp, obs = str(DATA / cfg["inp"]), eps.load_observations(str(case_file(c, cfg["observations"])))
    study = _json(RUNS / case / run / "study.json") or {}
    r = (study.get("eps_runs") or {}).get(label, {})
    changes = r.get("args", {}).get("changes") or r.get("result", {}).get("fitted_changes") or []
    hours = float(r.get("args", {}).get("duration_h") or cfg.get("duration_h", 24))
    t_obs, y_obs = obs[key]
    out = {"series": key, "label": label, "changes": changes, "hours": hours}
    for name, ch in (("nominal", []), ("calibrated", changes)):
        wn, res = _eps_sim(inp, json.dumps(ch, sort_keys=True), hours)
        t, y = eps.series(wn, res, key)
        step = max(1, len(t) // 600)
        out[name] = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(t[::step], y[::step])]
    step = max(1, len(t_obs) // 600)
    m = t_obs <= hours
    out["observed"] = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(t_obs[m][::step], y_obs[m][::step])]
    return out


# --- engineering workspace (copilot) -----------------------------------------------------------
import threading  # noqa: E402
import uuid  # noqa: E402

WORKSPACES, PLANTS, JOBS = {}, {}, {}


def workspace(case):
    from .copilot import Workspace
    if case not in WORKSPACES:
        WORKSPACES[case] = Workspace(case, os.getenv("COPILOT_MODEL", "muse-spark-1.3-contributor"))
    return WORKSPACES[case]


def ws_project(case):
    from .copilot import structures
    w = workspace(case)
    c = w.case.cfg
    return {"case": case, "title": c["title"], "question": c.get("question"), "has_drawing": bool(w.drawing),
            "documents": [{"id": k, "title": d["title"]} for k, d in w.project.docs.items()],
            "datasets": [{"id": k, "title": v.get("title", k)} for k, v in w.project.datasets.items()],
            "structures": structures(case) if w.drawing else [], "preloaded": w.base,
            "profiles": [{"label": k, "purpose": v["purpose"], "flows": v.get("flows")} for k, v in w.profiles.items()],
            "answers": w.answers, "session": w.dir.name, "revisions": w.revisions,
            "target_mgd": __import__("plantagent.copilot", fromlist=["x"]).target_flow(w),
            "drawing_meta": {k: w.drawing.get(k) for k in ("read_seconds", "read_at", "model")} if w.drawing else None,
            "rated_mgd": c.get("workspace", {}).get("rated_mgd"), "model": w.model,
            "current_profile": __import__("plantagent.copilot", fromlist=["x"]).current_label(w),
            "task_type": c["task_type"], "study_run": w.study_dir.name if w.study_dir else None,
            "eps": {"runs": [{"label": k, "score": (v.get("result") or {}).get("mean_relative_rmse")} for k, v in w.eps_runs.items()
                             if v.get("tool") == "eps_run"],
                    "series": list(eps.load_observations(str(__import__("plantagent.study", fromlist=["x"]).case_file(
                        w.case, c["eps"]["observations"]))).keys())} if "eps" in c else None,
            "doc_pages": {k: len(__import__("plantagent.docs", fromlist=["x"])._pages(
                __import__("plantagent.docs", fromlist=["x"]).DATA / d["pdf"])) for k, d in w.project.docs.items()}}


def plant(case):
    from .plant import PlantWorkspace
    if case not in PLANTS:
        PLANTS[case] = PlantWorkspace(case, os.getenv("COPILOT_MODEL", "muse-spark-1.3-contributor"))
    return PLANTS[case]


def plant_job(case, fn):
    """Run a plant-workspace agent call in the background and stream its tool calls (same job protocol as ws_ask)."""
    w = plant(case)
    job = uuid.uuid4().hex[:10]
    JOBS[job] = {"events": [], "done": False, "answer": None, "error": None}

    def work():
        w.listener = lambda e: JOBS[job]["events"].append({
            "kind": e["kind"], "name": e.get("name"), "text": e.get("text"),
            "args": _short(e.get("args"), 140) if e.get("args") else None,
            "result": _short(e.get("result"), 160) if e.get("result") is not None else None})
        try:
            JOBS[job]["answer"] = fn(w)
        except Exception as ex:
            JOBS[job]["error"] = f"{type(ex).__name__}: {ex}"
        finally:
            w.listener, JOBS[job]["done"] = None, True
    threading.Thread(target=work, daemon=True).start()
    return {"job": job}


def plant_project(case):
    w = plant(case)
    st = w.state(float(w.cfg.get("target_scale", 1.0))) if w.built else None
    return {"case": case, "kind": "process", "title": w.cfg["title"], "source": w.cfg["source"], "question": w.cfg["question"],
            "data_note": w.cfg.get("data_note"), "throughput": w.cfg.get("throughput"), "drawing": "svg" if w.cfg.get("svg") else "pdf" if w.cfg.get("pid_pdf") else "none", "dexpi": bool(w.cfg.get("pid")),
            "target_scale": w.cfg.get("target_scale", 1.0), "pid": w.pid or {"equipment": [], "connections": [], "valves": [], "control": []}, "basis": w.basis, "model": w.model,
            "built": {k: v for k, v in w.built.items() if k != "result"} if w.built else None,
            "read_confirmed": bool((w.pid or {}).get("confirmed")), "read_corrections": len((w.pid or {}).get("corrections") or []),
            "answers": w.answers, "revisions": [{k: r.get(k) for k in ("rev", "kind", "title", "changes", "capacity_multiple", "at", "user", "reason")}
                                                for r in w.revisions],
            "audit": {"verify": __import__("plantagent.audit", fromlist=["x"]).verify(case),
                      "entries": __import__("plantagent.audit", fromlist=["x"]).entries(case)[-50:]},
            "capacity": w.capacity() if w.built else None, "at_target": st}


MAX_UPLOAD = 20 * 1024 * 1024
MAX_POST = 28 * 1024 * 1024


def new_project(b):
    """Start a process-plant project from the engineer's own drawing and data sheet. The drawing is a DEXPI XML P&ID or a
    PDF; it is checked before anything is written. Nothing is spent until the engineer presses Build."""
    import re as _re
    from . import pid as _pid
    title, question, sheet = (str(b.get(k) or "").strip() for k in ("title", "question", "data_sheet"))
    if not 4 <= len(title) <= 200 or not 10 <= len(question) <= 4000:
        raise ValueError("give a project title and the engineering question")
    if not 200 <= len(sheet) <= 1024 * 1024:
        raise ValueError("paste the operating data sheet (current flows, temperatures, pressures, ratings): the model is built and "
                         "calibrated from it")
    base_slug = _re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "project"
    name = str(b.get("drawing_name") or "")
    ext = Path(name).suffix.lower()
    if ext not in (".xml", ".pdf"):
        raise ValueError("the drawing must be a DEXPI P&ID (.xml) or a PDF")
    encoded = b.get("drawing_b64")
    if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_UPLOAD + 2) // 3):
        raise ValueError("the drawing is empty or over 20 MB")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("invalid base64 drawing") from e
    if not data or len(data) > MAX_UPLOAD:
        raise ValueError("the drawing is empty or over 20 MB")
    try:
        if ext == ".xml":
            def reject_doctype(*_):
                raise ValueError("XML DTD and entities are not allowed")
            parser = expat.ParserCreate()
            parser.StartDoctypeDeclHandler = reject_doctype
            parser.Parse(data, True)
            ov = _pid.overview(io.BytesIO(data))
            if not ov["equipment"]:
                raise ValueError("no equipment found in this DEXPI file")
        else:
            if not data.startswith(b"%PDF-"):
                raise ValueError("the drawing is not a PDF")
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                if len(pdf) < 1:
                    raise ValueError("the PDF has no pages")
    except ValueError:
        raise
    except Exception as e:  # noqa: BLE001 - any parse failure means the file is not usable
        raise ValueError(f"the drawing could not be read: {type(e).__name__}") from e
    target = float(b.get("target_scale") or 1.2)
    if not math.isfinite(target) or target <= 0:
        raise ValueError("target_scale must be positive and finite")
    for n in range(1, 10000):
        slug = base_slug if n == 1 else f"{base_slug}_{n}"
        d = ROOT / "cases" / slug
        try:
            d.mkdir(parents=True)
            break
        except FileExistsError:
            continue
    else:
        raise ValueError("too many projects with this title")
    up = DATA_ROOT / "uploads" / slug
    up.mkdir(parents=True, exist_ok=True)
    f = up / ("drawing" + ext)
    f.write_bytes(data)
    cfg = {"kind": "process", "title": title, "source": "Uploaded by the engineer", "basis": "basis.md", "task_type": "capacity study",
           "question": question, "target_scale": target, "benchmark": False, "uploaded": True,
           ("pid" if ext == ".xml" else "pid_pdf"): f"uploads/{slug}/drawing{ext}"}
    (d / "basis.md").write_text(sheet + "\n")
    (d / "case.json").write_text(json.dumps(cfg, indent=2))
    from . import audit
    audit.append(slug, "create", None, "project created from uploaded drawing and data sheet", {"drawing": f.name, "bytes": len(data)})
    return {"case": slug, "url": f"plant.html?case={slug}"}


def ws_ask(case, text, context):
    w = workspace(case)
    job = uuid.uuid4().hex[:10]
    JOBS[job] = {"events": [], "done": False, "answer": None, "error": None}

    def listen(e):
        r = e.get("result")
        JOBS[job]["events"].append({"kind": e["kind"], "name": e.get("name"), "text": e.get("text"),
                                    "args": _short(e.get("args"), 140) if e.get("args") else None,
                                    "result": _short(r, 160) if r is not None else None})

    def work():
        w.listener = listen
        try:
            JOBS[job]["answer"] = w.ask(text, context)
        except Exception as ex:
            JOBS[job]["error"] = f"{type(ex).__name__}: {ex}"
        finally:
            w.listener, JOBS[job]["done"] = None, True
    threading.Thread(target=work, daemon=True).start()
    return {"job": job}


def ws_task(case, task_id):
    """Launch a long agent task (a full study with its own question) and stream its progress like ws_ask."""
    from .copilot import tasks
    from .study import Study
    w = workspace(case)
    t = next(x for x in tasks(w.case) if x["id"] == task_id)
    job = uuid.uuid4().hex[:10]
    JOBS[job] = {"events": [], "done": False, "answer": None, "error": None, "task": t["title"]}

    def work():
        try:
            st = Study(case, w.model, t.get("question"), t.get("task_type"), t.get("simulators"))
            st.emit = lambda e: JOBS[job]["events"].append({
                "kind": e["kind"], "name": e.get("name"), "text": e.get("text"),
                "args": _short(e.get("args"), 140) if e.get("args") else None,
                "result": _short(e.get("result"), 160) if e.get("result") is not None else None})
            run_dir = st.run()
            w.base = w._preload()  # the workspace now works from the new study's models
            summ = _json(Path(run_dir) / "summary.json") or {}
            JOBS[job]["answer"] = {"run": Path(run_dir).name, "summary": summ,
                                   "files": [f for f in DELIVERABLES if (Path(run_dir) / f).exists()]}
        except Exception as ex:
            JOBS[job]["error"] = f"{type(ex).__name__}: {ex}"
        finally:
            JOBS[job]["done"] = True
    threading.Thread(target=work, daemon=True).start()
    return {"job": job, "title": t["title"]}


def ws_fix_all(case):
    """'Get me to target': one verified proposal per failing unit, streamed as they come; the engineer accepts each."""
    from .copilot import failing_units, problems, target_flow
    w = workspace(case)
    job = uuid.uuid4().hex[:10]
    JOBS[job] = {"events": [], "done": False, "answer": None, "error": None}

    def work():
        try:
            units = failing_units(w)
            JOBS[job]["events"].append({"kind": "plan", "units": [u["unit"] for u in units]})
            for u in units[:6]:
                iss = next((i for i in problems(w) if i.get("structure") and i["structure"] == u["structure"]), None)
                w.listener = lambda e, u=u: JOBS[job]["events"].append({"kind": e["kind"], "name": e.get("name"), "unit": u["unit"],
                                                                         "args": _short(e.get("args"), 120) if e.get("args") else None})
                a = w.ask(f"Bring the {u['full_unit']} to {target_flow(w)} mgd. Its documented limit: {u['limit']}. Propose the least-cost "
                          f"change, verify it with a simulator run, and return it as a proposal" + (f" resolving issue {iss['id']}" if iss else "") + ".",
                          {"unit": u["unit"], "structure": u["structure"]})
                JOBS[job]["events"].append({"kind": "answer", "unit": u["unit"], "answer": a})
        except Exception as ex:
            JOBS[job]["error"] = f"{type(ex).__name__}: {ex}"
        finally:
            w.listener, JOBS[job]["done"] = None, True
    threading.Thread(target=work, daemon=True).start()
    return {"job": job}


def ws_export(case, kind):
    from .copilot import export
    w = workspace(case)
    f = export(w, kind)
    return {"file": f.name, "url": f"/wsfiles/{case}/{w.dir.name}/{f.name}"}


def history_series(case, dataset, parameter):
    return workspace(case).project.history(dataset, parameter)


def profile_at(case, run, label, q):
    study = _json(RUNS / case / run / "study.json")
    p = study["profiles"][label]
    r = profile.run(p["spec"], q)
    drawing = study.get("drawing")
    for n in r["nodes"]:
        if drawing and "drawing_ws_ft" in n:
            a = _anchor(drawing, n["drawing_ws_ft"], n["id"])
            n["bbox"] = a["bbox"] if a else None
        n["margin_ft"] = min((c["margin_ft"] for c in r["checks"] if c["id"] == n["id"] and "limit_ft" in c), default=None)
        n["fails"] = any(c["id"] == n["id"] and c["margin"] < 0 for c in r["checks"])
    r["capacity"] = profile.capacity(p["spec"])
    return r


@lru_cache(maxsize=16)
def drawing_png(case):
    c = Case(case)
    page = pymupdf.open(c.pdf)[c.cfg["drawing_page"] - 1]
    return page.get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6)).tobytes("png")


def start_run(case):
    _require_runs()
    before = set(_runs(case))
    log = open(RUNS / f"web_{case}.log", "w")
    subprocess.Popen([sys.executable, "-u", "-m", "plantagent.study", "--case", case], cwd=ROOT, stdout=log, stderr=log)
    for _ in range(100):  # the study creates its run dir immediately
        new = set(_runs(case)) - before
        if new:
            return {"run": new.pop()}
        time.sleep(0.1)
    raise RuntimeError("study did not start; see " + log.name)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        a[0].settimeout(15)
        super().__init__(*a, directory=str(STATIC), **kw)

    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json", code=200):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def _body(self, limit=MAX_POST):
        length = self.headers.get("Content-Length")
        if self.headers.get("Transfer-Encoding") or length is None or not length.isdecimal():
            raise ValueError("a valid Content-Length is required")
        if int(length) > limit:
            raise OverflowError("request body too large")
        data = self.rfile.read(int(length))
        if len(data) != int(length):
            raise ValueError("incomplete request body")
        return data

    def _json_body(self):
        body = json.loads(self._body() or b"{}")
        if not isinstance(body, dict):
            raise ValueError("JSON body must be an object")
        return body

    def _route(self, method):
        u = urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        known = set(all_cases())
        if parts[:1] not in (["api"], ["files"], ["wsfiles"]):
            return None
        if parts[:1] == ["wsfiles"] and len(parts) == 4 and parts[1] in known:
            name = parts[3]
            allowed = name in {"calc_sheets.xlsx", "memo.md", "markup.dwg", "profile_sheet.dwg", "profile_sheet.dxf"} or name.endswith(("_editable.dxf", "_editable.dwg"))
            f = _safe_file(RUNS / "ws" / parts[1], parts[2], name) if allowed else None
            if f:
                return self._send(f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
            return self._send({"error": "not found"}, code=404)
        if parts[:2] == ["api", "job"] and len(parts) == 3:
            j = JOBS.get(parts[2])
            if not j:
                return self._send({"error": "unknown job"}, code=404)
            off = int(q.get("offset", 0))
            return self._send({**j, "events": j["events"][off:], "offset": len(j["events"])})
        if parts[:2] == ["api", "plant"] and len(parts) == 4 and parts[2] in set(all_cases("process")):
            case, what = parts[2], parts[3]
            if method == "POST" and what in ("build", "ask"):
                _require_runs()
            body = self._json_body() if method == "POST" else {}
            w = plant(case)
            if what == "project":
                return self._send(plant_project(case))
            if what == "svg":
                f = _safe_file(ROOT / "cases" / case, w.cfg["svg"])
                return self._send(f.read_bytes(), "image/svg+xml") if f else self._send({"error": "not found"}, code=404)
            if what == "sheet.png":
                from . import pidvision
                return self._send(pidvision.render(DATA_ROOT / w.cfg["pid_pdf"], w.cfg.get("pid_page", 1) - 1), "image/png")
            if what == "build" and method == "POST":
                return self._send(plant_job(case, lambda w: {k: v for k, v in w.build().items() if k != "result"}))
            if what == "ask" and method == "POST":
                from . import audit
                audit.append(case, "ask", self.headers.get("X-User"), "", {"request": body["text"][:500], "model": w.model})
                return self._send(plant_job(case, lambda w: w.ask(body["text"], body.get("context"))))
            if what == "state":
                return self._send(w.state(float(q.get("scale", 1.0))))
            if what == "capacity":
                return self._send(w.capacity())
            user = self.headers.get("X-User")
            if what == "accept" and method == "POST":
                try:
                    return self._send(w.accept(body["proposal"], user, body.get("reason")))
                except ValueError as e:
                    return self._send({"error": str(e)}, code=409)
            if what == "restore" and method == "POST":
                try:
                    return self._send(w.restore(int(body.get("rev", 0)), user, body.get("reason")))
                except ValueError as e:
                    return self._send({"error": str(e)}, code=409)
            if what == "pidread":  # Muse's read of a PDF schematic and the engineer's confirmed version
                orig = json.loads(w.pid_file.read_text()) if w.pid_file.exists() else None
                conf = json.loads(w.confirmed_file.read_text()) if w.confirmed_file.exists() else None
                return self._send({"original": (orig or {}).get("raw"), "model": (orig or {}).get("model"),
                                   "confirmed": (conf or {}).get("raw"), "corrections": (conf or {}).get("corrections") or []})
            if what == "confirmread" and method == "POST":
                try:
                    return self._send(w.confirm_read(body.get("read") or {}, user, body.get("reason")))
                except ValueError as e:
                    return self._send({"error": str(e)}, code=409)
            if what == "relief":
                from . import pid as _pid
                return self._send(_pid.relief_scan(DATA_ROOT / w.cfg["pid"]))
            if what == "audit":
                from . import audit
                return self._send({"verify": audit.verify(case), "entries": audit.entries(case)})
            if what == "model" and method == "POST":
                from .llm import PRICES
                if body["model"] not in PRICES and not __import__("plantagent.llm", fromlist=["x"])._host(str(body["model"])):
                    return self._send({"error": "unknown model"}, code=400)
                w.model = body["model"]
                return self._send({"model": w.model})
        if parts == ["api", "newproject"] and method == "POST":
            try:
                return self._send(new_project(self._json_body()))
            except ValueError as e:
                return self._send({"error": str(e)}, code=400)
        if parts[:2] == ["api", "projects"]:
            return self._send([{"case": n, "kind": "study", "title": Case(n).cfg["title"], "task_type": Case(n).cfg["task_type"],
                                "workspace": "workspace" in Case(n).cfg} for n in all_cases()] +
                              [{"case": n, "kind": "process", "built": (RUNS / "ws" / n / "model.json").exists(),
                                "title": json.loads((ROOT / "cases" / n / "case.json").read_text())["title"],
                                "task_type": json.loads((ROOT / "cases" / n / "case.json").read_text())["task_type"], "workspace": True}
                               for n in all_cases("process")])
        if parts[:2] == ["api", "ws"] and len(parts) == 4 and parts[2] in known:
            case, what = parts[2], parts[3]
            if method == "POST" and what in ("ask", "task", "fixall", "photo", "voice", "readsheet"):
                _require_runs()
            body = self._json_body() if method == "POST" and what not in ("readsheet", "voice", "photo", "import") else {}
            if what == "model" and method == "POST":
                from .llm import PRICES
                if body["model"] not in PRICES and not __import__("plantagent.llm", fromlist=["x"])._host(str(body["model"])):
                    return self._send({"error": "unknown model"}, code=400)
                workspace(case).model = body["model"]
                return self._send({"model": body["model"]})
            if what == "readsheet" and method == "POST":
                from . import cad
                import tempfile
                data = self._body(MAX_UPLOAD)
                if not data.startswith(b"%PDF-"):
                    raise ValueError("upload a PDF sheet")
                page = int(q.get("page", 1))
                if page < 1:
                    raise ValueError("page must be positive")
                with tempfile.TemporaryDirectory() as t:
                    pdf = Path(t) / "sheet.pdf"
                    pdf.write_bytes(data)
                    t0 = time.time()
                    from . import llm as _llm
                    calls0 = _llm.LEDGER.read_text().count("\n") if _llm.LEDGER.exists() else 0
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(2) as ex:  # the full-sheet read and the tiled read run at the same time
                        f1, f2 = ex.submit(cad.read_profile, pdf, page), ex.submit(cad.locate_labels, pdf, page)
                        (reading, png), located = f1.result(), f2.result()
                    els, extra = cad.reconcile(reading, located)
                return self._send({"png": "data:image/png;base64," + base64.b64encode(png).decode(), "title": reading.get("title"),
                                   "design_flow_note": reading.get("design_flow_note"), "flow_path": reading.get("flow_path"),
                                   "elevations": els, "seconds": round(time.time() - t0),
                                   "cached": (_llm.LEDGER.read_text().count("\n") if _llm.LEDGER.exists() else 0) == calls0})
            if what == "reveal":
                w = workspace(case)
                g = _json(w.study_dir / "grade.json") if w.study_dir else None
                if not g:
                    graded = sorted(p for p in (RUNS / case).glob("2*") if (p / "grade.json").exists())
                    g = _json(graded[-1] / "grade.json") if graded else None
                key = w.case.answer_key or {}
                v = {i["id"]: i for i in (g or {}).get("items", [])}
                summ = _json(w.study_dir / "summary.json") if w.study_dir else {}
                return self._send({"score": (g or {}).get("score"), "judge": (g or {}).get("judge"), "source": key.get("source"),
                                   "run": w.study_dir.name if w.study_dir else None, "agent_model": summ.get("model"),
                                   "scores_all_runs": [(_json(p / "grade.json") or {}).get("score") for p in sorted((RUNS / case).glob("2*"))
                                                       if (p / "grade.json").exists()],
                                   "items": [{"unit": i["unit"], "engineers": i["engineers"], "verdict": v.get(i["id"], {}).get("verdict"),
                                              "note": v.get(i["id"], {}).get("note")} for i in key.get("items", [])]})
            if what == "voice" and method == "POST":
                from . import llm
                data = self._body(MAX_UPLOAD)
                if not data.startswith(b"RIFF") or data[8:12] != b"WAVE":
                    raise ValueError("upload WAV audio")
                return self._send(llm.transcribe(data))
            if what == "photo" and method == "POST":
                from .copilot import read_photo
                data = self._body(MAX_UPLOAD)
                if not data:
                    raise ValueError("upload a photo")
                return self._send(read_photo(workspace(case), data))
            if what == "import" and method == "POST":
                from .copilot import import_cad
                w = workspace(case)
                name = Path(self.headers.get("X-Filename") or "upload.dxf").name
                if Path(name).suffix.lower() not in (".dxf", ".dwg"):
                    return self._send({"error": "upload a .dxf or .dwg"}, code=400)
                f = w.dir / ("in_" + name)
                f.write_bytes(self._body(MAX_UPLOAD))
                return self._send(import_cad(w, f))
            if what in ("accept", "restore", "edit", "photoapply", "import") and method == "POST":
                from . import audit
                audit.append(case, what, self.headers.get("X-User"), (body or {}).get("reason", "") if isinstance(body, dict) else "",
                             {k: v for k, v in (body or {}).items() if k in ("title", "unit", "element", "field", "value", "rev", "run", "pump")}
                             if isinstance(body, dict) else {})
            if what == "project":
                return self._send(ws_project(case))
            if what == "ask" and method == "POST":
                return self._send(ws_ask(case, body["text"], body.get("context")))
            if what == "export" and method == "POST":
                if body.get("kind") == "memo":
                    _require_runs()
                return self._send(ws_export(case, body["kind"]))
            if what == "elements":
                from .copilot import elements
                return self._send(elements(workspace(case), q["label"]))
            if what == "edit" and method == "POST":
                from .copilot import edit
                return self._send(edit(workspace(case), body["label"], body["element"], body["field"], body["value"]))
            if what == "editable" and method == "POST":
                from .copilot import export_editable
                w = workspace(case)
                f = export_editable(w, body["label"])
                base = f"/wsfiles/{case}/{w.dir.name}/"
                return self._send({"dxf": base + f.name, "dwg": base + f.with_suffix(".dwg").name if f.with_suffix(".dwg").exists() else None})
            if what == "problems":
                from .copilot import problems
                return self._send(problems(workspace(case), float(q["q"]) if q.get("q") else None))
            if what == "tasks":
                from .copilot import tasks
                return self._send(tasks(workspace(case).case))
            if what == "task" and method == "POST":
                return self._send(ws_task(case, body["id"]))
            if what == "page":
                n, dpi = int(q["n"]), int(q.get("dpi", 110))
                if n < 1 or not 36 <= dpi <= 300:
                    raise ValueError("invalid page or DPI")
                w = workspace(case)
                url = w.project.image(q["doc"], n, dpi=dpi)
                return self._send(base64.b64decode(url.split(",", 1)[1]), "image/png")
            if what == "photoapply" and method == "POST":
                from .copilot import apply_photo
                return self._send(apply_photo(workspace(case), body["run"], body["pump"], body["gpm"], body["head"], body.get("note", "")))
            if what == "fixall" and method == "POST":
                return self._send(ws_fix_all(case))
            if what == "restore" and method == "POST":
                from .copilot import problems, restore
                w = workspace(case)
                r = restore(w, body.get("rev", 0))
                return self._send({**r, "issues": problems(w)})
            if what == "accept" and method == "POST":
                from .copilot import accept, problems
                w = workspace(case)
                try:
                    r = accept(w, body)
                except ValueError as e:
                    return self._send({"error": str(e)}, code=409)
                return self._send({**r, "issues": problems(w)})
            if what == "units":
                from .copilot import unit_capacities
                return self._send(unit_capacities(workspace(case), q.get("view", "proposed")))
            if what == "capacity":
                return self._send(profile.capacity(workspace(case).profiles[q["label"]]["spec"]))
            if what == "revisions":
                return self._send(workspace(case).revisions)
            if what == "history":
                return self._send(history_series(case, q["dataset"], q["parameter"]))
            if what == "profile":
                w = workspace(case)
                p = w.profiles[q["label"]]
                r = profile.run(p["spec"], float(q["q"]))
                for n in r["nodes"]:
                    if w.drawing and "drawing_ws_ft" in n:
                        a = _anchor(w.drawing, n["drawing_ws_ft"], n["id"])
                        n["bbox"] = a["bbox"] if a else None
                    n["fails"] = any(c["id"] == n["id"] and c["margin"] < 0 for c in r["checks"])
                return self._send(r)
        if parts[:1] == ["files"] and len(parts) == 4 and parts[1] in known and parts[3] in DELIVERABLES:
            f = _safe_file(RUNS / parts[1], parts[2], parts[3]) if parts[2] in _runs(parts[1]) else None
            if f:
                return self._send(f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
            return self._send({"error": "not found"}, code=404)
        api = parts[1:]
        if api == ["cases"]:
            return self._send(cases())
        if len(api) >= 2 and api[1] not in known:
            return self._send({"error": "unknown case"}, code=404)
        if len(api) == 3 and api[0] == "drawing":
            return self._send(drawing_png(api[1]), "image/png")
        if method == "POST" and api[:1] == ["start"] and len(api) == 2:
            return self._send(start_run(api[1]))
        if len(api) == 4 and api[0] == "run":
            case, run, what = api[1], api[2], api[3]
            if run not in _runs(case) or not _safe_file(RUNS / case, run, "log.jsonl"):
                return self._send({"error": "unknown run"}, code=404)
            if what == "log":
                return self._send(log_events(case, run, int(q.get("offset", 0))))
            if what == "detail":
                return self._send(run_detail(case, run))
            if what == "eps":
                return self._send(eps_series(case, run, q["label"], q["series"]))
            if what == "profile":
                return self._send(profile_at(case, run, q["label"], float(q["q"])))
        return self._send({"error": "not found"}, code=404)

    def _handle(self, method):
        try:
            if self._route(method) is None:
                if method == "GET":
                    super().do_GET()
                else:
                    self._send({"error": "not found"}, code=404)
        except PermissionError as e:
            self._send({"error": str(e)}, code=403)
        except OverflowError as e:
            self._send({"error": str(e)}, code=413)
        except TimeoutError as e:
            self._send({"error": str(e)}, code=408)
        except (ValueError, UnicodeDecodeError, KeyError, TypeError) as e:
            self._send({"error": str(e)}, code=400)
        except Exception as e:  # show the error in the UI instead of dropping the connection
            self._send({"error": f"{type(e).__name__}: {e}"}, code=500)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--check", action="store_true", help="exercise the API on the latest Roseburg run and exit")
    a = ap.parse_args()
    if a.check:
        run = next(r for r in _runs("roseburg") if (RUNS / "roseburg" / r / "study.json").exists())
        d = run_detail("roseburg", run)
        assert d["comparison"] and d["files"], d
        if d["profiles"]:
            lo, hi = (profile_at("roseburg", run, d["profiles"][0]["label"], q) for q in (6.0, 30.0))
            assert any(h["ws_ft"] > l["ws_ft"] for h, l in zip(hi["nodes"], lo["nodes"])), "more flow must raise some water level"
        assert log_events("roseburg", run)["events"] and drawing_png("roseburg")[:4] == b"\x89PNG"
        print("ok", run)
        sys.exit()
    print(f"http://127.0.0.1:{a.port}")
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
