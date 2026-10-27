"""Web UI for studies: live or replayed agent log, the drawing with a flow slider, deliverables, agent vs. engineers, benchmark.

Usage: python -m plantagent.web [--port 8000]
Starting a new study from the UI spends Muse credit, so it is off unless WEB_ALLOW_RUNS=1 (cap: MUSE_BUDGET_USD).
"""
import argparse
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

from . import profile
from .deliver import _anchor
from .docs import Case, all_cases

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
STATIC = ROOT / "web"
PHASES = {"collect": "1-2 Scope, criteria, data & RFI", "analyse": "3-6 Calibrate, model, capacity, alternatives",
          "qaqc": "7 Independent QA/QC", "resolve": "7b Lead engineer resolves QA/QC", "deliver": "8 Deliverables"}
DELIVERABLES = ["report.md", "drawing_markup.png", "drawing_redline.dwg", "drawing_redline.dxf", "profile_chart.png",
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
            "files": [f for f in DELIVERABLES if (d / f).exists()]}


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
        if parts[:1] not in (["api"], ["files"]):
            return None
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
            assert [n["ws_ft"] for n in hi["nodes"]][-1] > [n["ws_ft"] for n in lo["nodes"]][-1], "more flow must raise the upstream level"
        assert log_events("roseburg", run)["events"] and drawing_png("roseburg")[:4] == b"\x89PNG"
        print("ok", run)
        sys.exit()
    print(f"http://127.0.0.1:{a.port}")
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
