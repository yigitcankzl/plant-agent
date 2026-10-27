"""Copy the benchmark evidence (no source PDFs) into evidence/ so it can be published with the code.

Usage: python -m plantagent.evidence
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS, OUT = ROOT / "runs", ROOT / "evidence"
KEEP = ["grade.json", "summary.json", "report.md", "capacity.md", "alternatives.md", "qaqc.md", "rfi.md", "test_plan.md",
        "standards_check.md", "cost_estimate.md", "profile.md", "drawing_markup.png", "drawing_redline.dwg"]


def collect():
    rows = []
    for case in sorted(p for p in (ROOT / "cases").iterdir() if (p / "case.json").exists()):
        cfg = json.loads((case / "case.json").read_text())
        graded = sorted(p for p in (RUNS / case.name).glob("2*") if (p / "grade.json").exists()) if (RUNS / case.name).exists() else []
        for run in graded:
            dst = OUT / case.name / run.name
            dst.mkdir(parents=True, exist_ok=True)
            for f in KEEP:
                if (run / f).exists():
                    shutil.copy(run / f, dst / f)
            g, s = json.loads((run / "grade.json").read_text()), json.loads((run / "summary.json").read_text())
            rows.append({"case": case.name, "task": cfg["task_type"], "run": run.name, "score": g["score"], "judge": g.get("judge"),
                         "agent_model": s.get("model"), "steps": s.get("llm_steps"), "cost_usd": s.get("cost_usd"),
                         "benchmark": cfg.get("benchmark", True)})
    if Path("/tmp/contamination.json").exists():
        shutil.copy("/tmp/contamination.json", OUT / "contamination_check.json")
    (OUT / "results.json").write_text(json.dumps(rows, indent=1))
    latest = {}
    for r in rows:
        latest.setdefault(r["case"], []).append(r)
    lines = ["# Benchmark evidence", "", "Each folder holds the agent's deliverables and the independent judge's grade for one blind run.",
             "The engineers' conclusion pages were withheld from the agent; see cases/<case>/case.json and answer_key.json.", "",
             "| Case | Task | Runs | Scores | Judge | Agent model |", "|---|---|---|---|---|---|"]
    for case, rs in latest.items():
        if not rs[0]["benchmark"]:
            continue
        lines.append(f"| {case} | {rs[0]['task']} | {len(rs)} | {', '.join(f'{r['score']:.0%}' for r in rs)} | {rs[-1]['judge']} | {rs[-1]['agent_model']} |")
    (OUT / "README.md").write_text("\n".join(lines) + "\n")
    return rows


if __name__ == "__main__":
    rows = collect()
    assert rows and (OUT / "README.md").exists()
    print("ok", len(rows), "graded runs")
