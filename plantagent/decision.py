"""Decision file (management-of-change pack) and a one-page management memo from the plant workspace.

Everything in the file is recomputed when it is made: before/after limits are re-solved in DWSIM at the target, the
pre-startup safety review (PSSR) checklist is generated deterministically from the changes, and the audit-chain head and
model ids make it reproducible. It is a DRAFT for engineering review: nothing in it is an approval.

Usage: python -m plantagent.decision <case>
"""
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from . import audit, pid, process
from .docs import DATA
from .plant import FIELD, PlantWorkspace, describe_change, display_names

ROOT = Path(__file__).resolve().parent.parent


def _git_head():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:  # noqa: BLE001
        return None


def _owner(spec, path):
    """The equipment a change acts on: the unit itself, or the unit a utility feed serves."""
    kind, oid, _ = path.split(".", 2)
    if kind == "units":
        return oid
    for u in spec.get("units") or []:
        ins = [u.get("in")] if isinstance(u.get("in"), str) else list(u.get("in") or [])
        ins += [u[k][0] for k in ("cold", "hot") if u.get(k)]
        if oid in ins:
            return u["id"]
    return oid


def pssr(spec, changes, names, at):
    """Pre-startup safety review items generated from the kind of each change (deterministic rules)."""
    items = []
    units = {u["id"]: u for u in spec.get("units") or []}
    for c in changes:
        kind, oid, field = c["path"].split(".", 2)
        who, v = names.get(oid, oid), c.get("value")
        own = _owner(spec, c["path"])
        if kind == "feeds" and field in ("m3_h", "kg_h"):
            items.append(f"Verify the {who.lower()} can deliver {v:g} {FIELD[field][1]} at header pressure, and that the branch control valve can pass it.")
            u = (at.get("units") or {}).get(own) or {}
            if u.get("dP_cold_bar") or u.get("dP_hot_bar"):
                items.append(f"Measure the pressure drop across {own} at the new flow (model: cold side {u.get('dP_cold_bar')} bar, hot side {u.get('dP_hot_bar')} bar) "
                             "and compare with the available differential.")
            items.append(f"Confirm the {who.lower()} return temperature stays within the utility system's limit at the new duty.")
        elif field == "volume_m3":
            items.append(f"Confirm the high-level alarm and trip on {oid} leave margin above the new working volume of {v:g} m³; update the level setpoint "
                         "in the operating procedure.")
        elif field == "U_W_m2K":
            items.append(f"Plan and record the cleaning of {oid}; run a performance test after cleaning to confirm U of about {v:g} W/m²K.")
        elif field == "area_m2":
            items.append(f"Mechanical: confirm {oid}'s frame accepts {v:g} m² of plates; pressure-test after re-plating; update the datasheet.")
        elif field in ("P_out_bar", "T_out_C", "dP_bar"):
            items.append(f"Change the {FIELD.get(field, (field,))[0]} setpoint of {oid} to {v:g}; check the alarms and trips around it and the relief "
                         "set pressures downstream.")
        else:
            items.append(f"Review the change to {who} ({c['path']} = {v}) for alarms, trips and procedures.")
        if units.get(own, {}).get("type") in ("hx", "cooler", "heater"):
            items.append(f"Confirm {own}'s relief protection is unchanged by the new duty (see the relief scan section).")
    if not changes:
        return ["No plant change: confirm the operating limits in this file before running at the higher load, and record the first 24 h against the model."]
    items += ["Update the P&ID, equipment datasheets and the operating procedure for every change above.",
              "Brief the operators on the new setpoints before start-up.",
              "Record the first 24 h of operation at the new throughput and compare with the model's predicted values in this file."]
    return list(dict.fromkeys(items))


def redline_svg(w, owners, revs):
    """The DEXPI P&ID with a revision cloud and note at each changed equipment item."""
    if not w.cfg.get("svg") or not w.cfg.get("pid"):
        return None
    svg = (ROOT / "cases" / w.name / w.cfg["svg"]).read_text()
    g = pid.parse(DATA / w.cfg["pid"])
    tag_to_id = {n["tag"]: i for i, n in g["nodes"].items() if n["kind"] == "equipment" and n.get("tag")}
    root = ET.parse(DATA / w.cfg["pid"]).getroot()
    pos = {}
    for e in root.findall("Equipment"):
        loc = e.find("Position/Location")
        if loc is not None:
            pos[e.get("ID")] = (float(loc.get("X")), float(loc.get("Y")))
    marks = []
    for tag, rev in owners.items():
        p = pos.get(tag_to_id.get(tag))
        if not p:
            continue
        x, y = p[0], -p[1]  # the pyDEXPI rendering flips Y
        marks.append(f'<ellipse cx="{x}" cy="{y}" rx="16" ry="12" fill="none" stroke="#d00" stroke-width="0.9" stroke-dasharray="2,1.2"/>'
                     f'<polygon points="{x + 14},{y - 20} {x + 22},{y - 20} {x + 18},{y - 13}" fill="none" stroke="#d00" stroke-width="0.6"/>'
                     f'<text x="{x + 15.6}" y="{y - 16.5}" font-size="3.4" fill="#d00" font-family="sans-serif">{rev}</text>')
    note = "; ".join(f"{r['rev_label']}: {r['title']}" for r in revs)[:300]
    marks.append(f'<text x="8" y="-288" font-size="4" fill="#d00" font-family="sans-serif">DRAFT REVISION (not approved) - {re.sub("[<>&]", "", note)}</text>')
    return svg.replace("</svg>", "".join(marks) + "</svg>")


def _md_to_html(md):
    """Enough markdown (headings, bullets, tables, bold) for the PDF rendering."""
    out, table = [], []

    def flush():
        if table:
            rows = [r for r in table if not re.fullmatch(r"\|[-\s|:]+\|", r)]
            out.append("<table>" + "".join("<tr>" + "".join(f"<td>{c.strip()}</td>" for c in r.strip("|").split("|")) + "</tr>" for r in rows) + "</table>")
            table.clear()
    for line in md.splitlines():
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        if line.startswith("|"):
            table.append(line)
            continue
        flush()
        if line.startswith("#"):
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{n}>{line[n:].strip()}</h{n}>")
        elif line.startswith(("- ", "* ")):
            out.append(f"<p>&#8226; {line[2:]}</p>")
        elif line.strip():
            out.append(f"<p>{line}</p>")
    flush()
    return "".join(out)


def _pdf(md, path):
    import pymupdf
    css = "body{font-family:sans-serif;font-size:9pt} h1{font-size:14pt} h2{font-size:11pt;margin-top:8pt} td{border:0.5pt solid #999;padding:2pt;font-size:8pt} table{border-collapse:collapse}"
    story = pymupdf.Story(html=_md_to_html(md), user_css=css)
    writer = pymupdf.DocumentWriter(str(path))
    more = True
    while more:
        dev = writer.begin_page(pymupdf.paper_rect("a4"))
        more, _ = story.place(pymupdf.paper_rect("a4") + (36, 40, -36, -40))
        story.draw(dev)
        writer.end_page()
    writer.close()


def make(w, answer=None):
    """Build the decision file and memo for the workspace's current revisions (or, with no revisions, a selected answer's
    verified proposals applied together as the proposed case)."""
    target = float(w.cfg.get("target_scale", 1.0))
    built = w._built_spec()
    revs = [r for r in w.revisions if r.get("kind") == "change"]
    ans = w.answers[answer] if isinstance(answer, int) and 0 <= answer < len(w.answers) else (w.answers[-1] if w.answers else None)
    if revs:
        changes = [c for r in revs for c in r["changes"]]
        proposed = w.spec
    elif ans and any(p.get("verified") for p in ans.get("proposals") or []):
        revs = [{"rev": i + 1, "title": p.get("title"), "changes": p["changes"], "reason": "proposed in the answer, not yet applied",
                 "user": None, "at": None, "proposed_by": ans.get("model")} for i, p in enumerate(p for p in ans["proposals"] if p.get("verified"))]
        changes = [c for r in revs for c in r["changes"]]
        from .plant import patch
        proposed = patch(built, changes)
    elif ans:  # the answer needs no change to the plant (e.g. the load already fits): a no-change decision on the record
        revs, changes, proposed = [], [], built
    else:
        raise ValueError("nothing to decide yet: ask a question, or apply a verified fix as a draft revision")
    names = w.names()
    before, after = process.run(built, target), process.run(proposed, target)
    bc = {(c["id"], c["check"]): c for c in before["checks"] if "utilisation" in c}
    ac = {(c["id"], c["check"]): c for c in after["checks"] if "utilisation" in c}
    rows = sorted(({"id": k[0], "check": k[1], "before": bc[k]["utilisation"] if k in bc else None, "after": ac[k]["utilisation"],
                    "value_before": bc[k]["value"] if k in bc else None, "value_after": ac[k]["value"], "limit": ac[k]["limit"], "unit": ac[k]["unit"]}
                   for k in ac), key=lambda r: -(r["before"] or 0))
    for r in revs:
        r["rev_label"] = f"Rev {r['rev']}"
    owners = {}
    for r in revs:
        for c in r["changes"]:
            owners.setdefault(_owner(proposed, c["path"]), r["rev_label"])
    relief = pid.relief_scan(DATA / w.cfg["pid"]) if w.cfg.get("pid") else []
    relief_hit = [x for x in relief if x["tag"] in owners and x["status"] != "protected"]
    checklist = pssr(proposed, changes, names, after)
    head = (audit.entries(w.name)[-1:] or [{}])[0].get("hash")
    so = (ans or {}).get("second_opinion") or {}
    over_after = [r for r in rows if r["after"] > 1]
    cost = sorted({p.get("cost_class") for p in (ans or {}).get("proposals") or [] if p.get("cost_class")}) or ["not stated"]
    stamp = time.strftime("%Y-%m-%d %H:%M %Z")
    pct = lambda v: "—" if v is None else f"{v * 100:.0f} %"  # noqa: E731

    md = [f"# Decision file: {w.cfg['title']}", "",
          f"**Status: DRAFT for engineering review, not approved.** Prepared {stamp} by PlantAgent from the working model.", "",
          f"**Question:** {w.cfg.get('question')}", "",
          *([f"**Answer on record:** {ans.get('headline')}. {ans.get('summary')}", ""] if ans and not changes else []),
          f"**Result at {target * 100:.0f} % of today's throughput (re-solved in DWSIM for this file):** "
          + ("all stated limits within 100 %." if not over_after else f"{len(over_after)} limits still over 100 %: "
             + ", ".join(f"{names.get(r['id'], r['id'])} ({r['check']})" for r in over_after[:5]) + "."), "",
          "## 1. What changes and why", "", "| Rev | Change | Reason | Proposed by | Applied |", "|---|---|---|---|---|"]
    if not revs:
        md += ["| - | No change to the plant: the answer on record needs none | | | |"]
    md += [f"| {r['rev_label']} | {'; '.join(re.sub('<[^>]+>', '', describe_change(built, c, names)) for c in r['changes'])} | {r.get('reason') or ''} | "
           f"{r.get('proposed_by') or r.get('user') or ''} | {r.get('at') or 'not applied'} |" for r in revs]
    md += ["", f"## 2. Limits before and after, at {target * 100:.0f} % (DWSIM, re-solved now)", "",
           "| Equipment or stream | Check | Before | After | Value after | Limit |", "|---|---|---|---|---|---|"]
    md += [f"| {names.get(r['id'], r['id'])} | {r['check']} | {pct(r['before'])} | {pct(r['after'])} | {r['value_after']} {r['unit']} | {r['limit']} {r['unit']} |"
           for r in rows if (r["before"] or 0) > 0.8 or r["after"] > 0.8 or r["id"] in owners]
    md += ["", "## 3. Drawing", "", "Redlined P&ID: `redline.svg` (revision clouds at " + ", ".join(owners) + ")." if w.cfg.get("svg") else
           "This project has no smart P&ID; the changed equipment is: " + ", ".join(owners) + "."]
    md += ["", "## 4. Relief protection (P&ID relief scan)", ""]
    md += ([f"- {x['tag']} {', '.join(x['side_fluids'])} side: {x['status']}. {x['detail']}" + (" Heated side that can be blocked in." if x["thermal_expansion_risk"] else "")
            for x in relief_hit] or ["- No changed equipment side lacks relief on this drawing." if relief else "- No smart P&ID: relief scan not available; review relief manually."])
    md += ["", "- The changes are operating changes; the relief scan reads the drawing, so its findings above are unchanged by them and still need closing."]
    md += ["", "## 5. Field checks and assumptions", ""]
    md += [f"- Field check: {f.get('item')}. Where: {f.get('where')}. Changes: {f.get('changes')}" for f in (ans or {}).get("field_checks") or []] or ["- No field checks were raised in the answer."]
    md += [f"- Assumption (model): {a}" for a in (w.built.get("assumptions") or [])[:12]]
    reviewed = (w.built or {}).get("review") or {"status": "ok", "findings": [], "blocking": 0, "energy": {}}
    gaps = list(getattr(w, "gaps", None) or [])
    md += ["", "## Model review", "", f"**Status:** {reviewed.get('status', 'ok')}."]
    md += [f"- **{f.get('severity')}** — {f.get('check')}: {f.get('evidence')}" for f in reviewed.get("findings") or []] or ["- No findings."]
    if (reviewed.get("energy") or {}).get("note"):
        md += ["", reviewed["energy"]["note"]]
    md += ["", "## Capability gaps", ""]
    md += [f"- {g.get('what')}: {g.get('why')} Needed: {g.get('needed')}." for g in gaps] or ["- None recorded."]
    if so.get("comparison"):
        c = so["comparison"]
        md += ["", "## 6. Second opinion (Muse Spark Open, answered independently)", "", f"Status: **{c['status']}**."]
        md += [f"- Differs: {d}" for d in c["disagree"]] + [f"- Agrees: {a}" for a in c["agree"]]
    md += ["", "## 7. Pre-startup safety review (PSSR) checklist (generated from the changes)", ""]
    md += [f"- [ ] {i}" for i in checklist]
    md += ["", "## 8. Sign-off (DRAFT: not approved)", "", "| Role | Name | Signature | Date |", "|---|---|---|---|",
           "| Process engineer |  |  |  |", "| Operations |  |  |  |", "| Process safety (MOC) |  |  |  |", "| Approver |  |  |  |",
           "", "## 9. Reproducibility", "",
           f"- Model: {w.built.get('label')} built by {w.built.get('model')} on {w.built.get('at')}; P&ID coverage missing connections: "
           f"{len((w.built.get('coverage') or {}).get('missing_connections') or [])}",
           f"- Audit-chain head hash: `{head}` (chain intact: {audit.verify(w.name)['ok']})",
           f"- Code version: {_git_head()}; simulator: DWSIM (headless) via plantagent.process",
           "- Values in sections 2 and 7 were recomputed when this file was made; re-run `python -m plantagent.decision "
           f"{w.name}` on the same revisions to reproduce them."]
    decision_md = "\n".join(md) + "\n"

    diffs = sorted((so.get("comparison") or {}).get("disagree") or [], key=lambda d: d.startswith(("units.", "feeds.", "limits.")))  # outcomes first
    risk = ("the open-weights second opinion disagreed on: " + "; ".join(diffs[:3])) if diffs else \
        "no second-opinion disagreement recorded"
    if reviewed.get("status") == "model needs review":
        risk = f"the model needs review ({reviewed.get('blocking', 0)} blocking finding(s)). " + risk
    memo = [f"# Memo: {w.cfg['title']}", "", f"{stamp} · DRAFT, not approved", "",
            f"**Decision asked for:** {w.cfg.get('question')}", "",
            (f"**Recommendation:** no change to the plant is needed. {(ans or {}).get('headline', '')}. " if not changes else
             f"**Recommendation:** {'apply' if not over_after else 'do not yet apply'} the {len(revs)} change(s) below; ")
            + f"At {target * 100:.0f} % throughput "
            + ("every stated limit is within 100 % in the simulation." if not over_after else f"{len(over_after)} limit(s) remain over 100 %."), ""]
    memo += [f"- {re.sub('<[^>]+>', '', describe_change(built, c, names))}" for c in changes]
    memo += ["", f"**Cost class:** {', '.join(cost)}.", "",
             f"**Risk:** {risk}. Relief findings on changed equipment: {len(relief_hit)}.", "",
             "**Measure next:** " + ("; ".join(f.get("item", "") for f in (ans or {}).get("field_checks") or []) or
                                     "the first 24 h at the new throughput against the model's predicted values") + ".", "",
             f"Full decision file and PSSR checklist ({len(checklist)} items) attached. Audit head `{(head or '')[:12]}`."]
    memo_md = "\n".join(memo) + "\n"

    out = w.model_file.with_name("decision-" + time.strftime("%Y%m%d-%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "decision.md").write_text(decision_md)
    (out / "memo.md").write_text(memo_md)
    svg = redline_svg(w, owners, revs)
    if svg:
        (out / "redline.svg").write_text(svg)
    data = {"case": w.name, "made": stamp, "target_scale": target, "revisions": revs, "limits": rows, "pssr": checklist,
            "relief": relief_hit, "second_opinion": so.get("comparison"), "audit_head": head, "code": _git_head(),
            "model_review": reviewed, "gaps": gaps,
            "model": {k: w.built.get(k) for k in ("label", "model", "at", "review_status")}}
    (out / "decision.json").write_text(json.dumps(data, indent=1, default=str))
    files = ["decision.md", "memo.md", "decision.json"] + (["redline.svg"] if svg else [])
    for name, md_ in (("decision.pdf", decision_md), ("memo.pdf", memo_md)):
        try:
            _pdf(md_, out / name)
            files.append(name)
        except Exception as e:  # noqa: BLE001 - the markdown and JSON stand without the PDF
            data.setdefault("pdf_errors", []).append(f"{name}: {type(e).__name__}: {e}")
    with zipfile.ZipFile(out / "decision.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(out / f, f)
    files.append("decision.zip")
    audit.append(w.name, "decision_file", None, "decision file generated (draft)", {"folder": out.name, "revisions": len(revs),
                                                                                       "limits_over_after": len(over_after),
                                                                                       "model_review": reviewed.get("status"),
                                                                                       "blocking_findings": reviewed.get("blocking")})
    return {"folder": out.name, "files": files, "over_after": len(over_after), "pssr_items": len(checklist), "audit_head": head}


if __name__ == "__main__":
    import sys
    # python -m plantagent.decision <case> [--answer-file job.json]   (an answer saved from the workspace, e.g. a second-opinion run)
    w = PlantWorkspace(sys.argv[1])
    if "--answer-file" in sys.argv:
        j = json.loads(Path(sys.argv[sys.argv.index("--answer-file") + 1]).read_text())
        w.answers = [j.get("answer") or j]
    print(json.dumps(make(w), indent=1))
