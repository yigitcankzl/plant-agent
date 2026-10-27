"""Step artifacts and deliverables written from the study record (no LLM here)."""
import json

import wntr
from openpyxl import Workbook

from . import sim


def rows(x):
    """Model output is loosely typed: accept a list of dicts, a dict, a list of strings or a string."""
    if not x:
        return []
    if isinstance(x, dict):
        return [x]
    if isinstance(x, str):
        return [{"value": x}]
    return [r if isinstance(r, dict) else {"value": r} for r in x]


def _table(rows_, cols):
    rows_ = rows(rows_)
    if rows_ and not any(c in r for r in rows_ for c in cols):
        cols = list(dict.fromkeys(k for r in rows_ for k in r))
    if not rows_:
        return "_none_\n"
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows_:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/").replace("\n", " ") for c in cols) + " |")
    return "\n".join(out) + "\n"


def write_deliverables(d, study, memo, summary):
    col, an, rev, res, runs = (study["collection"], study["analysis"], study["review"], study["resolution"], study["runs"])
    crit = col.get("criteria", {})
    if not isinstance(crit, dict):
        crit = {"criteria": crit}

    (d / "criteria.md").write_text(
        f"# Step 1 - Scope and design criteria\n\n**Question:** {crit.get('question', study['question'])}\n\n"
        "## Definitions\n" + _table(crit.get("definitions", []), ["term", "definition", "source"]) +
        "\n## Criteria\n" + _table(crit.get("criteria", []), ["name", "value", "source"]) +
        "\n## Standards\n" + _table(crit.get("standards", []), ["name", "use"]) +
        "\n## Units on the flow path\n" + "".join(f"- {r.get('value', r)}\n" for r in rows(col.get("units_on_path"))))
    (d / "data_register.json").write_text(json.dumps(col.get("data_register", []), indent=2))
    (d / "rfi.md").write_text("# Step 2 - Requests for information and assumptions\n\n" +
                              _table(col.get("rfi", []), ["item", "issue", "resolution", "reason"]))
    (d / "calibration.md").write_text("# Step 3 - Calibration against field data\n\n" +
                                      _table(an.get("calibration", []), ["test", "source", "measured", "simulated", "residual_pct", "run_label", "note"]))

    base = an.get("base_model_run")
    base = base if base in runs else (next(iter(runs)) if runs else None)
    if base:
        sim.write_inp(runs[base]["spec"], d / "model.inp")
        wn = wntr.network.WaterNetworkModel(str(d / "model.inp"))  # open-check: the file reloads and runs
        wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=str(d / "model_check"))
        for f in d.glob("model_check.*"):
            f.unlink()
        summary["model_inp"] = {"base_run": base, "pumps": wn.num_pumps, "pipes": wn.num_pipes, "reloads": True}

    (d / "capacity.md").write_text("# Step 5 - Capacity evaluation\n\n" +
                                   _table(an.get("capacity_table", []), ["unit", "limit", "binds_at", "limits_target", "evidence"]))
    (d / "alternatives.md").write_text("# Step 6 - Alternatives\n\n" +
                                       _table(an.get("alternatives", []), ["unit", "option", "run_label", "result", "meets_target", "cost_class", "cost_basis", "recommended"]))
    (d / "qaqc.md").write_text(
        "# Step 7 - QA/QC\n\nChecked runs: " + ", ".join(map(str, rev.get("checked_runs") or [])) +
        "\n\nChecked citations: " + ", ".join(map(str, rev.get("checked_citations") or [])) + "\n\n## Issues\n" +
        _table(rev.get("issues", []), ["severity", "item", "issue", "evidence"]) +
        "\n## Lead engineer responses\n" + _table(res.get("responses", []), ["issue", "action", "explanation"]))
    (d / "report.md").write_text(memo)
    (d / "findings.json").write_text(json.dumps(an.get("findings", []), indent=2))
    (d / "study.json").write_text(json.dumps(study, indent=2))

    wb = Workbook()
    sheets = {"Data register": col.get("data_register", []), "Calibration": an.get("calibration", []),
              "Capacity": an.get("capacity_table", []), "Alternatives": an.get("alternatives", []),
              "Simulation runs": [{"label": k, "purpose": v["purpose"], "result": json.dumps(v["result"]),
                                   "spec": json.dumps(v["spec"])} for k, v in runs.items()]}
    wb.remove(wb.active)
    for name, data in sheets.items():
        ws = wb.create_sheet(name)
        data = rows(data)
        cols = list(dict.fromkeys(k for r in data for k in r))
        ws.append(cols)
        for r in data:
            ws.append([json.dumps(r[c]) if isinstance(r.get(c), (dict, list)) else r.get(c) for c in cols])
    wb.save(d / "calc_appendix.xlsx")
    (d / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import tempfile
    from pathlib import Path
    spec = {"reservoirs": [{"id": "a", "head_ft": 0}, {"id": "b", "head_ft": 20}], "junctions": [{"id": "j"}],
            "pipes": [{"id": "p", "from": "j", "to": "b", "length_ft": 100, "diameter_in": 12}],
            "pumps": [{"id": "P", "from": "a", "to": "j", "rated_gpm": 1000, "rated_head_ft": 30}]}
    study = {"question": "q", "collection": {"criteria": {}}, "analysis": {"base_model_run": "r1", "findings": [{"unit": "u"}]},
             "review": {}, "resolution": {}, "runs": {"r1": {"purpose": "x", "spec": spec, "result": sim.run(spec)}}}
    with tempfile.TemporaryDirectory() as t:
        s = {}
        write_deliverables(Path(t), study, "memo", s)
        assert s["model_inp"]["reloads"] and (Path(t) / "calc_appendix.xlsx").exists()
    print("ok")
