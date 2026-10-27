"""Web UI for studies: live or replayed agent log, the drawing with a flow slider, deliverables, agent vs. engineers, benchmark.

Usage: python -m plantagent.web [--port 8000]
Starting a new study from the UI spends Muse credit, so it is off unless WEB_ALLOW_RUNS=1 (cap: MUSE_BUDGET_USD).
"""
import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
import time
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pymupdf

from . import eps, profile
from .deliver import _anchor
from .docs import Case, all_cases

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
    return sorted((p.name for p in d.iterdir() if (p / "log.jsonl").exists()), reverse=True) if d.exists() else []


def _json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


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
                    "summary": _json(RUNS / name / done[0] / "summary.json") if done else None})
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

WORKSPACES, JOBS = {}, {}


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
            "rated_mgd": c.get("workspace", {}).get("rated_mgd"), "model": w.model,
            "current_profile": __import__("plantagent.copilot", fromlist=["x"]).current_label(w),
            "task_type": c["task_type"], "study_run": w.study_dir.name if w.study_dir else None,
            "eps": {"runs": [{"label": k, "score": (v.get("result") or {}).get("mean_relative_rmse")} for k, v in w.eps_runs.items()
                             if v.get("tool") == "eps_run"],
                    "series": list(eps.load_observations(str(__import__("plantagent.study", fromlist=["x"]).case_file(
                        w.case, c["eps"]["observations"]))).keys())} if "eps" in c else None,
            "doc_pages": {k: len(__import__("plantagent.docs", fromlist=["x"])._pages(
                __import__("plantagent.docs", fromlist=["x"]).DATA / d["pdf"])) for k, d in w.project.docs.items()}}


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
        n["fails"] = any(c["id"] == n["id"] and c["margin_ft"] < 0 for c in r["checks"])
    r["capacity"] = profile.capacity(p["spec"])
    return r


@lru_cache(maxsize=16)
def drawing_png(case):
    c = Case(case)
    page = pymupdf.open(c.pdf)[c.cfg["drawing_page"] - 1]
    return page.get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6)).tobytes("png")


def start_run(case):
    if os.getenv("WEB_ALLOW_RUNS") != "1":
        raise PermissionError("starting studies from the UI is disabled (set WEB_ALLOW_RUNS=1)")
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

    def _route(self, method):
        u = urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        known = set(all_cases())
        if parts[:1] not in (["api"], ["files"], ["wsfiles"]):
            return None
        if parts[:1] == ["wsfiles"] and len(parts) == 4 and parts[1] in known:
            f = RUNS / "ws" / parts[1] / Path(parts[2]).name / Path(parts[3]).name
            if f.exists():
                return self._send(f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
            return self._send({"error": "not found"}, code=404)
        if parts[:2] == ["api", "job"] and len(parts) == 3:
            j = JOBS.get(parts[2])
            if not j:
                return self._send({"error": "unknown job"}, code=404)
            off = int(q.get("offset", 0))
            return self._send({**j, "events": j["events"][off:], "offset": len(j["events"])})
        if parts[:2] == ["api", "ws"] and len(parts) == 4 and parts[2] in known:
            case, what = parts[2], parts[3]
            if what == "photo" and method == "POST":
                from .copilot import read_photo
                data = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                return self._send(read_photo(workspace(case), data))
            if what == "import" and method == "POST":
                from .copilot import import_cad
                w = workspace(case)
                name = Path(self.headers.get("X-Filename") or "upload.dxf").name
                if Path(name).suffix.lower() not in (".dxf", ".dwg"):
                    return self._send({"error": "upload a .dxf or .dwg"}, code=400)
                f = w.dir / ("in_" + name)
                f.write_bytes(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
                return self._send(import_cad(w, f))
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}") if method == "POST" else {}
            if what == "project":
                return self._send(ws_project(case))
            if what == "ask" and method == "POST":
                return self._send(ws_ask(case, body["text"], body.get("context")))
            if what == "export" and method == "POST":
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
                w = workspace(case)
                url = w.project.image(q["doc"], int(q["n"]), dpi=int(q.get("dpi", 110)))
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
                r = accept(w, body)
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
                    n["fails"] = any(c["id"] == n["id"] and c["margin_ft"] < 0 for c in r["checks"])
                return self._send(r)
        if parts[:1] == ["files"] and len(parts) == 4 and parts[1] in known and parts[3] in DELIVERABLES:
            f = RUNS / parts[1] / Path(parts[2]).name / parts[3]
            if f.exists():
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
            case, run, what = api[1], Path(api[2]).name, api[3]
            if not (RUNS / case / run / "log.jsonl").exists():
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
                super().do_GET()
        except PermissionError as e:
            self._send({"error": str(e)}, code=403)
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
