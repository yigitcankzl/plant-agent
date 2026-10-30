"""Grade a study's findings against the engineers' withheld answer key.

Usage: python -m plantagent.grade [run_dir ...]   (default: latest run of every case)
"""
import json
import os
import re
import sys
from pathlib import Path

from . import llm
from .docs import Case

# The judge is a stronger model than the agent's study model, so the score is not self-graded. ~$0.05 per case.
JUDGE = os.getenv("JUDGE_MODEL", "muse-wonder-1.0")
SCORE = {"found": 1.0, "partially": 0.5, "missed": 0.0, "contradicted": 0.0}

PROMPT = """You grade an AI engineering study against the answer key written by the professional engineers.
For each answer-key item decide: "found" (same conclusion and essentially the same remedy), "partially" (right problem
but different/incomplete remedy or value), "missed" (not addressed), or "contradicted" (agent concludes the opposite).
Judge substance, not wording. Return JSON only: {"items": [{"id": ..., "verdict": ..., "note": "one short sentence"}]}"""


def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def grade(run_dir, judge=None, write=True):
    run_dir, judge = Path(run_dir), judge or JUDGE
    study = json.loads((run_dir / "study.json").read_text())
    key = Case(study["case"]).answer_key
    findings = study["analysis"].get("findings", [])
    alternatives = study["analysis"].get("alternatives", [])
    llm.set_tag("grade:" + study["case"])
    out = _json(llm.chat(judge, [{"role": "system", "content": PROMPT}, {"role": "user", "content": json.dumps(
        {"answer_key": [{k: i[k] for k in ("id", "unit", "engineers")} for i in key["items"]],
         "agent_findings": findings, "agent_alternatives": alternatives})}], temperature=0))
    verdicts = {v["id"]: v for v in out["items"]}
    rows = []
    for item in key["items"]:
        v = verdicts.get(item["id"], {"verdict": "missed", "note": "not graded"})
        rows.append({"id": item["id"], "unit": item["unit"], "verdict": v["verdict"], "note": v.get("note", "")})
    score = sum(SCORE.get(r["verdict"], 0) for r in rows) / len(rows)
    result = {"case": study["case"], "judge": judge, "agent_model": study.get("model"), "score": round(score, 3), "items": rows}
    if write:
        (run_dir / "grade.json").write_text(json.dumps(result, indent=2))
    return result


def agreement(second="muse-spark-1.3"):
    """Re-grade every graded run with a second judge model (not saved as the grade) and report verdict agreement."""
    rows = []
    for g in sorted(Path("runs").glob("*/2*/grade.json")):
        first = json.loads(g.read_text())
        if not Case(first["case"]).cfg.get("benchmark", True):
            continue
        other = grade(g.parent, second, write=False)
        pairs = [(a["verdict"], b["verdict"]) for a, b in zip(first["items"], other["items"])]
        rows.append({"case": first["case"], "run": g.parent.name, "judge": first.get("judge"), "score": first["score"],
                     "second_judge": second, "second_score": other["score"],
                     "same_verdict": sum(a == b for a, b in pairs), "items": len(pairs)})
    same, n = sum(r["same_verdict"] for r in rows), sum(r["items"] for r in rows)
    out = {"second_judge": second, "verdict_agreement": round(same / n, 3), "items": n, "runs": rows,
           "mean_score_first": round(sum(r["score"] for r in rows) / len(rows), 3),
           "mean_score_second": round(sum(r["second_score"] for r in rows) / len(rows), 3)}
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/judge_agreement.json").write_text(json.dumps(out, indent=1))
    return out


def latest_runs():
    root = Path("runs")
    return [sorted(p for p in (root / c).iterdir() if (p / "study.json").exists())[-1]
            for c in sorted(x.name for x in root.iterdir() if x.is_dir() and x.name not in ("llm_cache", "pages"))
            if any((p / "study.json").exists() for p in (root / c).iterdir())]


def print_table(results):
    for r in results:
        summary = json.loads((r["dir"] / "summary.json").read_text())
        print(f"\n== {r['case']}: score {r['score']:.0%} | {summary['llm_steps']} LLM steps, {summary['simulations']} sims, "
              f"{summary['wall_time_s']} s, ${summary['cost_usd']:.3f}")
        for i in r["items"]:
            print(f"  {i['verdict']:<13} {i['unit'][:42]:<42} {i['note'][:90]}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--agreement"]:
        print(json.dumps({k: v for k, v in agreement().items() if k != "runs"}, indent=1))
        sys.exit()
    dirs = [Path(p) for p in sys.argv[1:]] or latest_runs()
    results = [{**grade(d), "dir": d} for d in dirs]
    print_table(results)
    print(f"\nspent ${llm.spent():.4f} of ${llm.BUDGET_USD}")
