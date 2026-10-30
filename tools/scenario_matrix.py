"""Run a matrix of typical engineer commands against copies of process cases and report what works.
python tools/scenario_matrix.py [model] [case ...]  ->  runs/scenario_matrix/<case>.md + .json
Each case is copied to a throw-away case `_mx_<case>` (cases/ and runs/ws/), so the real case history is untouched.
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from plantagent.plant import PlantWorkspace  # noqa: E402

COMMON = [
    ("capacity", "Can the plant reach the target throughput? What limits it first and what is the cheapest way there?"),
    ("whatif_sweep", "Show how the limits change if the main feed temperature varies from 10 C below to 10 C above today's value, with a chart."),
    ("datasheet", "Prepare a data sheet for the most heavily loaded equipment item at the target throughput."),
    ("summary", "Write a one-page summary of the last verified answer for my manager."),
    ("work_order", "Prepare a maintenance work order for the cheapest no-capex fix in the last verified answer."),
    ("drawing", "Draw the proposed design from the last verified proposals as a Rev B P&ID and add a note at the most loaded item."),
    ("relief", "Is every equipment item protected by a relief device? List the sides that are not and what you would do."),
    ("unknown", "Calculate the noise level at the compressor or pump nearest the control room."),
]
SPECIFIC = {
    "chem_c01": [
        ("add_parallel", "Add a second pump in parallel with P4711, same model, and tell me what it does at 120%."),
        ("add_series", "Add a booster pump in series on the line between P4711 and H1007 (2 bar rise) and check it at 120%."),
        ("bypass", "What happens if we bypass the control valve 47123/C1 (remove it and fit a spool piece)?"),
        ("remove", "Take H1008 out of service: what does the unit then manage, and what fails first?"),
        ("upsize", "Put a larger motor on P4712, next standard size, and check it."),
        ("utility", "Cooling water may only supply 22 m3/h in summer. Does the 120% case still work?"),
    ],
    "salt_mvr": [
        ("add_parallel", "Add a parallel vapour compressor K-202 sized for the 120% case and verify it."),
        ("add_series", "Add a second desuperheater in series after D-201 and tell me if it changes anything."),
        ("bypass", "What happens if the purge evaporator V-301 is bypassed for a week (purge liquor straight to disposal)?"),
        ("fouling", "The main heater is fouling. Below which heat-transfer coefficient must production drop? Chart it."),
        ("feed_conc", "If the feed brine arrives at 22 wt% NaCl instead of saturated, what happens to salt production?"),
        ("upsize", "Replace the main heater E-201 with a 10,000 m2 unit and check the 120% case."),
    ],
}


def copy_case(case):
    tmp = f"_mx_{case}"
    for base in (ROOT / "cases", ROOT / "runs" / "ws"):
        shutil.rmtree(base / tmp, ignore_errors=True)
    shutil.copytree(ROOT / "cases" / case, ROOT / "cases" / tmp)
    ws = ROOT / "runs" / "ws" / tmp
    ws.mkdir(parents=True)
    for f in ("model.json", "revisions.json", "health.json", "forecast.json", "states.json"):
        if (ROOT / "runs" / "ws" / case / f).exists():
            shutil.copy(ROOT / "runs" / "ws" / case / f, ws / f)
    # earlier verified answers so document/drawing commands have something to point at
    answers = sorted((ROOT / "runs" / "ws" / case).glob("*/answers.json"))
    if answers:
        (ws / "20000101-000000").mkdir()  # loads as the earlier answers of the copy
        shutil.copy(answers[-1], ws / "20000101-000000" / "answers.json")
    return tmp


def run(model, case):
    tmp = copy_case(case)
    out, t0 = [], time.time()
    try:
        only = [k for k in (__import__("os").environ.get("MX_ONLY") or "").split(",") if k]
        for key, text in COMMON + SPECIFIC.get(case, []):
            if only and key not in only:
                continue
            w = PlantWorkspace(tmp, model)
            s0 = time.time()
            try:
                a = w.ask(text)
                ps = [p for p in a.get("proposals") or [] if isinstance(p, dict)]
                tools = []
                log = w.dir / "log.jsonl"
                if log.exists():
                    tools = [json.loads(l).get("tool") for l in log.read_text().splitlines() if '"tool"' in l]
                gaps_f = ROOT / "runs" / "ws" / tmp / "gaps.json"
                row = {"key": key, "request": text, "headline": a.get("headline"), "seconds": round(time.time() - s0),
                       "cost_usd": a.get("cost_usd"), "tools": sorted(set(t for t in tools if t)),
                       "proposals": [{"title": p.get("title"), "verified": p.get("verified"),
                                      "why_not": p.get("unverified_reason") or p.get("error") or
                                      ("still over: " + ", ".join(c["id"] for c in p.get("still_over") or []) if p.get("still_over") else None)}
                                     for p in ps],
                       "artifacts": [(x["kind"], x["title"]) for x in a.get("artifacts") or []],
                       "reaches_target": (a.get("combined") or {}).get("reaches_target"),
                       "gaps": json.loads(gaps_f.read_text())[-2:] if gaps_f.exists() else []}
            except Exception as e:  # noqa: BLE001 - one failing command must not stop the matrix
                row = {"key": key, "request": text, "error": f"{type(e).__name__}: {e}"[:400], "seconds": round(time.time() - s0)}
            out.append(row)
            print(json.dumps(row)[:300], flush=True)
    finally:
        for base in (ROOT / "cases", ROOT / "runs" / "ws"):
            shutil.rmtree(base / tmp, ignore_errors=True)
    d = ROOT / "runs" / "scenario_matrix"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{case}.json").write_text(json.dumps(out, indent=1))
    md = [f"# Scenario matrix: {case} ({model}, {round(time.time() - t0)} s, ${sum(r.get('cost_usd') or 0 for r in out):.3f})", "",
          "| Scenario | Result | Tools | Proposals | Files |", "|---|---|---|---|---|"]
    for r in out:
        props = "; ".join(f"{p['title']}: {'verified' if p['verified'] else 'NOT verified (' + str(p['why_not'] or '')[:80] + ')'}"
                          for p in r.get("proposals") or [])
        md.append(f"| {r['key']} | {r.get('error') or r.get('headline')} | {', '.join(r.get('tools') or [])} | {props} | "
                  f"{'; '.join(f'{k}: {t}' for k, t in r.get('artifacts') or [])} |")
    (d / f"{case}.md").write_text("\n".join(md) + "\n")
    return out


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "muse-spark-1.3-contributor"
    for case in sys.argv[2:] or ["chem_c01", "salt_mvr"]:
        run(model, case)
