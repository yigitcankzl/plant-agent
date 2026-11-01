"""Onboard an unseen DEXPI P&ID end to end with no hand-written case files.

The data sheet is generated from the DEXPI file itself (every design attribute it carries, nothing typed by a person);
whatever the drawing does not say, Muse has to assume, and those values come out tagged `assumed`.

  PYTHONPATH=. .venv/bin/python tools/onboard_unseen.py <dexpi.xml> --step create|build|ask|loop|all
"""
import argparse
import base64
import json
import sys
from pathlib import Path

from plantagent import llm, pid

MODEL = "baseten:meta-models/muse-spark-open-1026"
TITLE = "BASF process column K 2750 (DEXPI C02, unseen)"
QUESTION = "+20 % feed: what limits it first and what does it cost?"


def data_sheet(xml):
    """Everything the DEXPI file states, as text. No number in it is typed by a person."""
    o = pid.overview(xml)
    out = ["Operating data sheet generated automatically from the DEXPI P&ID (no engineer input beyond the drawing).",
           "Only what the drawing states is listed; process conditions not on the drawing are unknown and must be assumed.", ""]
    for e in o["equipment"]:
        out.append(f"Equipment {e['tag']} ({e['class']}): " + ", ".join(f"{k} {v}" for k, v in (e.get("design") or {}).items()))
        for lim in e.get("design_limits") or []:
            out.append("  design limits: " + ", ".join(f"{k} {v}" for k, v in lim.items()))
    for ln in o["lines"]:
        out.append(f"Line {ln['line']}: fluid code {ln.get('fluid_code')}, piping class {ln.get('piping_class')}, DN {ln.get('dn')}")
    for c in o["connections"]:
        out.append(f"Connection {c['from']} -> {c['to']} via {', '.join(c['inline']) or 'direct'}")
    for v in o["valves"]:
        out.append(f"Valve {v['tag']} ({v['class']})")
    out += [f"Instrumentation: {c}" for c in o["control"]]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml")
    ap.add_argument("--step", default="all")
    ap.add_argument("--case")
    a = ap.parse_args()
    from plantagent import web
    from plantagent.plant import PlantWorkspace as Workspace
    case = a.case
    if a.step in ("create", "all"):
        r = web.new_project({"title": TITLE, "question": QUESTION, "data_sheet": data_sheet(a.xml), "task_type": "capacity",
                             "drawing_name": Path(a.xml).name, "drawing_b64": base64.b64encode(Path(a.xml).read_bytes()).decode()})
        case = r["case"]
        print("created", case, flush=True)
    w = Workspace(case, MODEL)
    usd0 = llm.spent()
    if a.step in ("build", "all"):
        b = w.build()
        print("build", json.dumps({k: v for k, v in b.items() if k != "result"}, default=str)[:1500], flush=True)
    if a.step in ("ask", "all"):
        ans = w.ask(QUESTION)
        print("ask", ans.get("headline"), ans.get("cost_usd"), flush=True)
    if a.step in ("loop", "all"):
        from plantagent import loop
        log = loop.run(w, QUESTION + " Make the design pass every engineering check that has data.", 3, 8)
        print("loop", log["status"], log.get("usd_total"), (log.get("result") or {}).get("headline"), flush=True)
    print("spent this step", round(llm.spent() - usd0, 4), "case", case)


if __name__ == "__main__":
    sys.exit(main())
