"""Step artifacts and deliverables written from the study record (no LLM here)."""
import json
import math

import matplotlib
import pymupdf
import wntr
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont

from . import cad, design, sim

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


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

    if study.get("profiles"):
        write_profile(d, study, an, summary)
    write_design(d, study, an, summary)

    wb = Workbook()
    sheets = {"Data register": col.get("data_register", []), "Calibration": an.get("calibration", []),
              "Capacity": an.get("capacity_table", []), "Alternatives": an.get("alternatives", []),
              "Simulation runs": [{"label": k, "purpose": v["purpose"], "result": json.dumps(v["result"]),
                                   "spec": json.dumps(v["spec"])} for k, v in runs.items()],
              "Profile runs": [{"label": k, "purpose": v["purpose"], "flow_mgd": r["flow_mgd"], "passes": r["passes"],
                                "nodes": json.dumps(r["nodes"]), "checks": json.dumps(r["checks"])}
                               for k, v in (study.get("profiles") or {}).items() for r in v["results"]],
              "Pump data sheets": summary.get("pump_datasheets", []),
                        "Surge runs": [{"label": k, "purpose": v["purpose"], "event": json.dumps(v["args"]), "nodes": json.dumps(v["result"].get("nodes")),
                              "spec": json.dumps(v["spec"])} for k, v in (study.get("surges") or {}).items()]}
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


def write_design(d, study, an, summary):
    """New profile sheet for the recommended design and data sheets for the pumps of recommended alternatives."""
    profiles = study.get("profiles") or {}
    label = an.get("design_profile_run")
    label = label if label in profiles else (list(profiles)[-1] if profiles else None)
    if label:
        p = profiles[label]
        flows = sorted({float(q) for q in p["flows"]})
        info = design.profile_sheet(p["spec"], flows, d / "design_profile.dxf", "Proposed hydraulic profile",
                                    f"{study['facility']} - run {label}")
        try:
            cad.oda_convert(d / "design_profile.dxf", "DWG")
        except Exception as e:
            (d / "design_profile.dwg.error").write_text(str(e))
        summary["design_profile_sheet"] = {"run": label, **info}
    sheets = []
    for alt in rows(an.get("alternatives")):
        run = study["runs"].get(alt.get("run_label") or "")
        if not (alt.get("recommended") and run):
            continue
        for pump in run["spec"].get("pumps", []):
            if pump.get("on", True):
                try:
                    sheets.append({"alternative": alt.get("option", ""), "run": alt["run_label"],
                                   **design.pump_datasheet(run["spec"], pump["id"], run["result"])})
                except Exception as e:  # a loosely specified run should not stop the deliverables
                    sheets.append({"run": alt["run_label"], "pump": pump["id"], "error": str(e)})
    if sheets:
        summary["pump_datasheets"] = sheets
        (d / "pump_datasheets.json").write_text(json.dumps(sheets, indent=2))


def _base_profile(study, an):
    profiles = study["profiles"]
    base = an.get("base_profile_run")
    return base if base in profiles else next(iter(profiles))


def write_profile(d, study, an, summary):
    """Profile table, a true-scale profile chart, and the drawing marked up with results and revision clouds."""
    base = _base_profile(study, an)
    p = study["profiles"][base]
    from . import profile as prof
    limits = prof.capacity(p["spec"])
    lines = [f"# Hydraulic profile - base run `{base}`\n", p["purpose"], "\n## Water surface by structure (ft)\n",
             "| structure | " + " | ".join(f"{r['flow_mgd']} mgd" for r in p["results"]) + " | drawing | residual |",
             "|---|" + "---|" * (len(p["results"]) + 2)]
    for i, n in enumerate(p["results"][0]["nodes"]):
        lines.append(f"| {n['id']} | " + " | ".join(str(r["nodes"][i]["ws_ft"]) for r in p["results"]) +
                     f" | {n.get('drawing_ws_ft', '')} | " + " / ".join(str(r["nodes"][i]["residual_ft"]) for r in p["results"]
                                                                     if "residual_ft" in r["nodes"][i])[:40] + " |")
    lines += ["\n## Flow at which each limit binds\n", _table(limits, ["id", "check", "binds_at_mgd"])]
    (d / "profile.md").write_text("\n".join(lines))
    summary["profile"] = {"base_run": base, "limits": limits}

    # True-scale profile chart.
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ids = [n["id"] for n in p["results"][0]["nodes"]]
    for r in p["results"]:
        ax.plot(range(len(ids)), [n["ws_ft"] for n in r["nodes"]], marker="o", label=f"{r['flow_mgd']} mgd",
                color="tab:red" if not r["passes"] else None)
    for c in p["results"][0]["checks"]:
        if "limit_ft" in c and c["id"] in ids:
            i = ids.index(c["id"])
            ax.hlines(c["limit_ft"], i - 0.35, i + 0.35, colors="k", linestyles="--")
            ax.annotate(c["check"][:28], (i, c["limit_ft"]), fontsize=7, xytext=(2, 3), textcoords="offset points")
    dw = [(i, n["drawing_ws_ft"]) for i, n in enumerate(p["results"][0]["nodes"]) if "drawing_ws_ft" in n]
    if dw:
        ax.scatter(*zip(*dw), marker="s", facecolors="none", edgecolors="k", s=60, label="drawing", zorder=5)
    ax.set_xticks(range(len(ids)), [i[:16] for i in ids], rotation=25, fontsize=7, ha="right")
    ax.set_ylabel("water surface (ft)")
    ax.set_title(f"{study['facility']} - hydraulic profile ({base})")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(d / "profile_chart.png", dpi=130)
    plt.close(fig)

    if study.get("drawing"):
        markup_drawing(d, study, an, p)


def _anchor(drawing, value, structure=""):
    """The drawing label a result belongs to: same value, and among equal values the one whose structure name matches."""
    words = set(structure.lower().replace("/", " ").split())
    overlap = lambda e: len(words & set(e.get("structure", "").lower().replace("/", " ").split()))  # noqa: E731
    hits = [e for e in drawing["elevations"] if abs(float(e["value"]) - float(value)) < 0.006]
    if hits:
        return max(hits, key=overlap)
    named = [e for e in drawing["elevations"] if overlap(e)]
    return max(named, key=overlap) if named else None


def markup_drawing(d, study, an, p, zoom=1.6):
    """Results and revision clouds on the real sheet: PNG for the report and UI, redlined DXF + DWG for CAD."""
    from .docs import Case
    case = Case(study["case"])
    drawing = study["drawing"]
    page = pymupdf.open(case.pdf)[drawing["page"] - 1]
    im = Image.open(__import__("io").BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png"))).convert("RGB")
    W, H = im.size
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
    except OSError:
        font = ImageFont.load_default()

    labels, changes = [], []
    top = max(p["results"], key=lambda r: r["flow_mgd"])
    for n in top["nodes"]:
        a = _anchor(drawing, n["drawing_ws_ft"]) if "drawing_ws_ft" in n else None
        if not a:
            continue
        fail = any(c["id"] == n["id"] and c["margin_ft"] < 0 for c in top["checks"])
        text = f"{top['flow_mgd']:g} MGD: WS {n['ws_ft']:.2f}" + (" OVER LIMIT" if fail else "")
        x0, y0, x1, y1 = a["bbox"]
        xy = (x0 * W, y1 * H + 3)
        draw.rectangle(draw.textbbox(xy, text, font=font), fill=(255, 255, 255))
        draw.text(xy, text, fill=(200, 0, 0) if fail else (0, 90, 200), font=font)
        labels.append({"bbox": a["bbox"], "text": text})
    for ch in rows(an.get("drawing_changes")):
        a = _anchor(drawing, ch.get("anchor_value") or -1, ch.get("structure", ""))
        if not a:
            continue
        x0, y0, x1, y1 = a["bbox"]
        pad = 0.012
        box = [(x0 - pad) * W, (y0 - pad) * H, (x1 + pad) * W, (y1 + pad) * H]
        _png_cloud(draw, box)
        changes.append({"bbox": [x0 - pad, y0 - pad, x1 + pad, y1 + pad], "note": ch.get("note", "")[:120]})
    try:
        small = ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        small = font
    notes = [f"A{i}  {ch['note']}" for i, ch in enumerate(changes, 1)]
    if notes:  # revision notes in a boxed panel at the top left, clear of the drawing content
        lh = 17
        box = [0.06 * W, 0.035 * H, 0.06 * W + max(draw.textlength(n, font=small) for n in notes) + 16, 0.035 * H + lh * len(notes) + 30]
        draw.rectangle(box, fill=(255, 255, 255), outline=(200, 0, 0), width=2)
        draw.text((box[0] + 8, box[1] + 5), "PROPOSED REVISIONS (AGENT, FOR ENGINEER REVIEW)", fill=(200, 0, 0), font=small)
        for i, n in enumerate(notes):
            draw.text((box[0] + 8, box[1] + 22 + lh * i), n, fill=(200, 0, 0), font=small)
    for i, ch in enumerate(changes, 1):
        x0, y0, x1, y1 = ch["bbox"]
        draw.text((x1 * W + 6, y0 * H - 16), f"A{i}", fill=(200, 0, 0), font=font)
    im.save(d / "drawing_markup.png")

    sheet = d / "drawing.dxf"
    cad.pdf_page_to_dxf(case.pdf, drawing["page"], sheet)
    rev = {"number": "A", "date": __import__("time").strftime("%Y-%m-%d"), "by": "AGENT",
           "description": "PROPOSED - AGENT STUDY, FOR ENGINEER REVIEW, NOT FOR CONSTRUCTION"}
    red = cad.redline(sheet, d / "drawing_redline.dxf", changes, rev, [0, 0, page.rect.width, page.rect.height], labels=labels)
    try:
        cad.oda_convert(red, "DWG")
    except Exception as e:  # DWG is a convenience copy; the DXF is the deliverable
        (d / "drawing_redline.dwg.error").write_text(str(e))
    sheet.unlink()


def _png_cloud(draw, box, r=9):
    x0, y0, x1, y1 = box
    for (ax, ay), (bx, by) in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
        n = max(int(math.hypot(bx - ax, by - ay) / (2 * r)), 1)
        for i in range(n):
            cx, cy = ax + (bx - ax) * (i + 0.5) / n, ay + (by - ay) * (i + 0.5) / n
            draw.arc([cx - r, cy - r, cx + r, cy + r], 0, 360, fill=(200, 0, 0), width=3)


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
