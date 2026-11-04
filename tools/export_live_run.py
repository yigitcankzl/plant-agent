"""Export one recorded engineering run to web/img/live_run.json for the landing page replay (no model call).

The page replays exactly these rows: Muse's proposal per round, the engine checks with their status, and the tool
calls Muse made, all from the stored worklog and session log. usage: python tools/export_live_run.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE, RUN, SESSION = "basf_process_column_k_2750_dexpi_c02_uns", "20261103-214753", "20261103-214738"
NAMES = {"process": "Process target", "robustness": "Operating envelope (±10 % feed)", "confidence": "Uncertainty (48 samples)"}


def check_name(c):
    c = c or ""
    if c.startswith("separation."):
        return {"flooding": "Column flooding", "purity_distillate": "Distillate purity", "purity_bottoms": "Bottoms purity",
                "min_reflux": "Minimum reflux"}.get(c.rsplit(".", 1)[-1], c)
    return NAMES.get(c, c.replace("_", " ").capitalize())


def main():
    base = ROOT / "runs" / "ws" / CASE
    w = json.loads((base / "work" / RUN / "worklog.json").read_text())
    tools, rnd = [[]], 0
    for line in (base / SESSION / "log.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "tool" in r:
            label = (r.get("args") or {}).get("label") or ""
            tools[-1].append(r["tool"] + (f" '{label}'" if label else ""))
        if "submit" in r:
            tools.append([])
    rounds = []
    for i, r in enumerate(w["rounds"]):
        muse = next(s for s in r["steps"] if s["actor"] == "muse")
        checks = [{"name": check_name(s.get("check")), "status": s["status"], "detail": s.get("title", "")[:140]}
                  for s in r["steps"] if s.get("kind") == "check" and s["status"] in ("pass", "fail")]
        rounds.append({"n": r["n"], "proposal": " + ".join(t.split(" – ")[0].split(" - ")[0] for t in muse["title"].split("; "))[:120],
                       "seconds": muse.get("seconds"), "usd": muse.get("usd"),
                       "tools": tools[i] if i < len(tools) else [], "checks": checks})
    out = {"case": CASE, "run": RUN, "goal": w["goal"], "model": w["model"], "started": w["started"],
           "seconds": w["seconds_total"], "usd": w["usd_total"], "status": w["status"],
           "open": [s.get("check") for r in w["rounds"][-1:] for s in r["steps"] if s.get("status") == "open"],
           "rounds": rounds}
    (ROOT / "web" / "img" / "live_run.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(len(rounds), "rounds,", sum(len(r["tools"]) for r in rounds), "tool calls")


if __name__ == "__main__":
    main()
