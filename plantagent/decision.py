"""Decision file (management-of-change pack) and a one-page management memo from the plant workspace.

Read top-down: 1 summary, 2 basis, 3 existing vs proposed, 4 one subsection per change, 5 drawings (Rev A and the
Rev B sheet from plantagent/revb.py, embedded as high-resolution pages), 6 risks and safety, 7 approvals; appendices for
reproducibility, capability gaps, model review and assumptions.

Everything in the file is recomputed when it is made: before/after limits are re-solved in DWSIM at the target, the
pre-startup safety review (PSSR) checklist is generated deterministically from the changes, and the audit-chain head and
model ids make it reproducible. It is a DRAFT for engineering review: nothing in it is an approval.

Usage: python -m plantagent.decision <case>
"""
import json
import re
import subprocess
import time
import zipfile
from pathlib import Path

from . import audit, pid, process
from .docs import DATA
from .plant import FIELD, KIND, PlantWorkspace, added_equipment, describe_change, display_names
from .proposed import ports, topology
from .revb import _num, qty, value_text

ROOT = Path(__file__).resolve().parent.parent


def _git_head():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:  # noqa: BLE001
        return None


def _owner(spec, change):
    """The equipment a change acts on: the unit itself, or the unit a utility feed serves."""
    if change.get("add_unit"):
        return change["add_unit"]["id"]
    if change.get("reroute"):
        return change["reroute"]["unit"]
    path = change["path"]
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
        if c.get("add_unit"):
            u, source = c["add_unit"], c.get("rating_source") or "to confirm"
            if u["type"] in ("mixer", "splitter", "recycle"):
                items.append(f"Confirm the new {u['id']} routing/manifold in the field, including branch isolation, drains, vents and flow direction.")
                items.append(f"Isolation: confirm valves so the new {u['id']} manifold can be separated from the existing line.")
            else:
                items.append(f"Isolation: confirm block valves on each nozzle of new {u['id']} before the line is opened to process fluid.")
                items.append(f"Check valves and backflow: confirm a non-return device so parallel {u['id']} cannot be driven backwards. To confirm.")
                items.append(f"Controls and parallel load sharing: confirm how {u['id']} shares load with the existing machine, including a manual fallback. To confirm.")
                items.append(f"Alarms and trips: confirm process and machine alarms and trips for new {u['id']} before start-up. To confirm.")
                items.append(f"Relief review: confirm relief protection for new {u['id']} and the changed piping. This file does not size a relief device.")
                items.append(f"Commissioning: confirm line-up, rotation and a no-load check of new {u['id']} before process fluid.")
                items.append(f"Materials and wet-service suitability of new {u['id']}: to confirm. No materials certificate is on file.")
                items.append(f"Vendor curve for new {u['id']}: to confirm against {source}. The rating in this file is provisional.")
                if u["type"] == "compressor":
                    items.append(f"Turndown and surge: confirm the surge line, anti-surge control and minimum flow for new compressor {u['id']}. To confirm; no vendor curve is on file.")
            continue
        if c.get("reroute"):
            r = c["reroute"]
            to = ", ".join(r["value"]) if isinstance(r["value"], list) else r["value"]
            items.append(f"Walk down the reroute of {r['unit']} {r['field']} to {to}; confirm valves, drains, vents and flow direction match the Rev B drawing.")
            continue
        kind, oid, field = c["path"].split(".", 2)
        who, v = names.get(oid, oid), c.get("value")
        own = _owner(spec, c)
        if kind == "feeds" and field in ("m3_h", "kg_h"):
            items.append(f"Verify the {who.lower()} can deliver {v:g} {FIELD[field][1]} at header pressure, and that the branch control valve can pass it.")
            u = (at.get("units") or {}).get(own) or {}
            if u.get("dP_cold_bar") or u.get("dP_hot_bar"):
                items.append(f"Measure the pressure drop across {own} at the new flow (model: cold side {u.get('dP_cold_bar')} bar, hot side {u.get('dP_hot_bar')} bar) "
                             "and compare with the available differential.")
            items.append(f"Confirm the {who.lower()} return temperature stays within the utility system's limit at the new duty.")
        elif field == "fractions":
            items.append(f"Set the new split at {who}: {value_text(c, names)}; confirm the flow control can hold it at the new rate and "
                         "update the operating procedure.")
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


def _stored_calculations(revs, ans):
    found = [r["calculation"] for r in revs or [] if isinstance(r.get("calculation"), dict)]
    if found:
        return found
    return [p["calculation"] for p in (ans or {}).get("proposals") or []
            if p.get("verified") and isinstance(p.get("calculation"), dict)]


def _md_to_html(md):
    """Enough markdown (headings, bullets, tables with a header row, bold, code, page breaks) for the PDF rendering."""
    out, table = [], []

    def flush():
        if table:
            rows = [r for r in table if not re.fullmatch(r"\|[-\s|:]+\|", r)]
            cell = lambda c: "&#160;" * 30 if c.strip() == "_" else c.strip()  # noqa: E731 - "_" is an empty signature field
            html = "".join("<tr>" + "".join((f"<th>{cell(c)}</th>" if i == 0 else f"<td>{cell(c)}</td>") for c in r.strip("|").split("|")) + "</tr>"
                           for i, r in enumerate(rows))
            out.append(f"<table>{html}</table>")
            table.clear()
    for line in md.splitlines():
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        if line.startswith("|"):
            table.append(line)
            continue
        flush()
        if line.startswith("#"):
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{n}>{line[n:].strip()}</h{n}>")
        elif line.startswith(("- ", "* ")):
            out.append(f"<p class='li'>&#8226; {line[2:]}</p>")
        elif line.strip():
            out.append(f"<p>{line}</p>")
    flush()
    return "".join(out)


CSS = ("body{font-family:sans-serif;font-size:9pt;color:#17383d} h1{font-size:16pt;margin-bottom:2pt} h2{font-size:12pt;margin-top:10pt;"
       "border-bottom:0.6pt solid #17383d} h3{font-size:10pt;margin-top:8pt} h4{font-size:9pt;margin-top:6pt} p{margin:2pt 0}"
       " p.li{margin-left:8pt} th{text-align:left;border:0.5pt solid #9aa;padding:2pt;font-size:8pt}"
       " td{border:0.5pt solid #9aa;padding:2pt;font-size:8pt;vertical-align:top} table{border-collapse:collapse;width:100%;margin:3pt 0}"
       " code{font-family:monospace;font-size:7.5pt}")


def _story_pdf(md):
    import io
    import pymupdf
    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    story = pymupdf.Story(html=_md_to_html(md), user_css=CSS)
    more = True
    while more:
        dev = writer.begin_page(pymupdf.paper_rect("a4"))
        more, _ = story.place(pymupdf.paper_rect("a4") + (40, 40, -40, -48))
        story.draw(dev)
        writer.end_page()
    writer.close()
    return pymupdf.open("pdf", buf.getvalue())


def _pdf(parts, path, drawings=(), footer=""):
    """PDF from markdown parts, each starting on a new page; the drawings (title, svg) are inserted as A4-landscape
    pages before the last part."""
    import pymupdf
    doc = pymupdf.open()
    for md in parts[:-1]:
        doc.insert_pdf(_story_pdf(md))
    for title, svg in drawings:
        # raster at ~300 dpi: MuPDF's SVG-to-PDF conversion drops parts of DEXPI sheets, its raster renderer does not
        png = pymupdf.open(stream=svg.encode(), filetype="svg")[0].get_pixmap(matrix=pymupdf.Matrix(6, 6)).tobytes("png")
        page = doc.new_page(width=842, height=595)
        page.insert_text((40, 32), title, fontsize=11, fontname="hebo", color=(0.09, 0.22, 0.24))
        page.insert_image(pymupdf.Rect(30, 42, 812, 562), stream=png, keep_proportion=True)
    if parts:
        doc.insert_pdf(_story_pdf(parts[-1]))
    for i, page in enumerate(doc):
        w, h = page.rect.width, page.rect.height
        page.insert_text((40, h - 22), f"{footer} · DRAFT - NOT APPROVED · page {i + 1} of {len(doc)}", fontsize=7, fontname="helv",
                         color=(0.4, 0.45, 0.45))
    doc.save(str(path), garbage=3, deflate=True, deflate_images=True)
    return len(doc)


def _pct(v):
    return "-" if v is None else f"{v * 100:.0f} %"


def _cap(v):
    return "-" if v is None else f"{v * 100:.1f} %"


def _tags_in(text, tags):
    return {t for t in tags if t and re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text or "")}


def _illustrative(w):
    """Data-sheet lines marked ILLUSTRATIVE (and the case's data note)."""
    basis = ROOT / "cases" / w.name / w.cfg["basis"] if w.cfg.get("basis") else None
    lines = []
    if basis and basis.exists():
        for line in basis.read_text().splitlines():
            if "illustrative" in line.lower() and line.lstrip().startswith(("-", "|", "*")):
                lines.append(re.sub(r"\s+", " ", line.strip(" -*|")).strip())
    return lines


def _describe(spec, c, names):
    """One readable line per change: fractions as percentages, reroutes with stream names joined."""
    if c.get("reroute"):
        r, j = c["reroute"], lambda v: ", ".join(v) if isinstance(v, list) else str(v)  # noqa: E731
        return f"Reroutes {names.get(r['unit'], r['unit'])} {r['field']}: " + (f"{j(c['from'])} → " if c.get("from") is not None else "") + j(r["value"])
    if c.get("path") and isinstance(c.get("value"), list):
        return f"{names.get(c['path'].split('.')[1], c['path'].split('.')[1])}: {value_text(c, names)}"
    return re.sub("<[^>]+>", "", describe_change(spec, c, names))


def _datasheet(changes, calc):
    """Preliminary equipment datasheet of the new units (rounded, units shown; missing vendor data marked to confirm)."""
    out = ["#### Preliminary equipment datasheet", "",
           "Provisional equipment selection only: not a vendor datasheet and not a mechanical design approval.", "",
           "| Tag | Service | Inlet | Outlet | Operating point | Pressure ratio / head | Rating | Rating source |", "|---|---|---|---|---|---|---|---|"]
    streams = {s.get("id"): s for s in (calc or {}).get("streams") or []}
    checks = (calc or {}).get("checks") or []
    for c in changes:
        u = c.get("add_unit")
        if not u or u.get("type") in ("mixer", "splitter", "recycle"):
            continue
        ins, outs = ports(u)
        si, so_ = streams.get(ins[0]) if ins else None, streams.get(outs[0]) if outs else None
        side = lambda sid, st: f"{sid}, {_num(st['T_C'])} °C, {_num(st['P_bar'])} bar" if st else f"{sid}, to confirm"  # noqa: E731
        op = [qty(x["value"], x.get("unit") or "") for x in checks if x.get("id") == u["id"] and x.get("value") is not None]
        if u.get("eff_pct"):
            op.append(f"efficiency {u['eff_pct']} % (assumed)")
        ratio = f"{_num(so_['P_bar'] / si['P_bar'])}" if si and so_ and si.get("P_bar") else "to confirm"
        lim = c.get("limits") or {}
        rating = " / ".join(x for x in (qty(lim["max_kg_h"], "kg/h") if lim.get("max_kg_h") else "",
                                        qty(lim["max_kW"], "kW") if lim.get("max_kW") else "") if x) or "to confirm"
        out.append(f"| {u['id']} | {KIND.get(u.get('type'), u.get('type'))} | {side(ins[0], si) if ins else '-'} | "
                   f"{side(outs[0], so_) if outs else '-'} | {', '.join(op) or 'to confirm'} | {ratio}; head to confirm | {rating} | "
                   f"{c.get('rating_source') or 'to confirm'} |")
    return out + ["", "Missing vendor information (to confirm): vendor curve, mechanical design, materials.", ""]


def _change_calc(calc, tags=()):
    """Before/after table of one change from its stored DWSIM calculation record: only the rows this change moves or
    the items it acts on (values with units, rounded)."""
    rows = ["| Item | Check | Limit | Before | After |", "|---|---|---|---|---|"]
    for c in calc.get("checks") or []:
        if c.get("before") is None and c.get("after") is None and c.get("value") is None:
            continue  # a unit type without a limit check
        moved = c.get("before") is None or c.get("after") is None or abs(c["after"] - c["before"]) > 0.005
        if not moved and c.get("id") not in tags:
            continue
        unit, limit = c.get("unit") or "", c.get("limit")
        before = (f"{qty(c['before'] * limit, unit)} ({_pct(c['before'])})" if c.get("before") is not None and limit
                  else _pct(c.get("before")))
        after = qty(c["value"], unit) if c.get("value") is not None else "-"
        if c.get("after") is not None:
            after += f" ({_pct(c['after'])})"
        rows.append(f"| {c['id']} | {c['check']} | {qty(limit, unit) if limit is not None else '-'} | {before} | {after} |")
    return rows if len(rows) > 2 else []


def make(w, answer=None):
    """Build the MOC decision pack and memo for the workspace's applied change revisions (or, with none, a selected answer's
    verified proposals applied together as the proposed case)."""
    if (w.built.get("review") or {}).get("blocking"):
        raise ValueError("the current model has blocking review findings; correct it before creating a decision pack")
    from .plant import patch
    target = float(w.cfg.get("target_scale", 1.0))
    change_revs = [r for r in w.revisions if r.get("kind") == "change"]
    corrections = [r for r in w.revisions if r.get("kind") == "correction"]
    ans = w.answers[answer] if isinstance(answer, int) and 0 <= answer < len(w.answers) else (w.answers[-1] if w.answers else None)
    props = {}
    if change_revs:  # applied revisions: the existing plant is the model before the first design change
        built = change_revs[0]["spec_before"]
        revs = [{"rev": i + 1, "title": r.get("title"), "changes": r["changes"], "reason": r.get("reason"), "user": r.get("user"),
                 "at": r.get("at"), "proposed_by": r.get("proposed_by"), "new_equipment": r.get("new_equipment") or added_equipment(r["changes"]),
                 "calculation": r.get("calculation"), "capacity_multiple": r.get("capacity_multiple")} for i, r in enumerate(change_revs)]
        proposed = w.spec
    elif ans and any(p.get("verified") for p in ans.get("proposals") or []):
        built = getattr(w, "spec", None) or w._built_spec()  # the current (corrected) model the proposals were verified on
        verified = [p for p in ans["proposals"] if p.get("verified")]
        revs = [{"rev": i + 1, "title": p.get("title"), "changes": p["changes"], "reason": p.get("why"), "user": None, "at": None,
                 "proposed_by": ans.get("model"), "new_equipment": p.get("new_equipment") or added_equipment(p["changes"]),
                 "calculation": p.get("calculation"), "capacity_multiple": p.get("capacity_multiple")} for i, p in enumerate(verified)]
        props = {r["rev"]: p for r, p in zip(revs, verified)}
        proposed = patch(built, [c for r in revs for c in r["changes"]])
    elif ans:  # the answer needs no change to the plant (e.g. the load already fits): a no-change decision on the record
        built = getattr(w, "spec", None) or w._built_spec()
        revs, proposed = [], built
    else:
        raise ValueError("nothing to decide yet: ask a question, or apply a verified fix as a draft revision")
    changes = [c for r in revs for c in r["changes"]]
    names = {**display_names(proposed), **w.names()}
    nm = lambda i: names.get(i, i)  # noqa: E731
    before, after = process.run(built, target), process.run(proposed, target)
    bc = {(c["id"], c["check"]): c for c in before["checks"] if "utilisation" in c}
    ac = {(c["id"], c["check"]): c for c in after["checks"] if "utilisation" in c}
    rows = sorted(({"id": k[0], "check": k[1], "before": bc[k]["utilisation"] if k in bc else None, "after": ac[k]["utilisation"],
                    "value_before": bc[k]["value"] if k in bc else None, "value_after": ac[k]["value"], "limit": ac[k]["limit"], "unit": ac[k]["unit"]}
                   for k in ac), key=lambda r: -max(r["before"] or 0, r["after"] or 0))
    owners = {}
    for r in revs:
        r["rev_label"] = f"Rev B.{r['rev']}"
        for c in r["changes"]:
            owners.setdefault(_owner(proposed, c), r["rev"])
    new_equipment = [e for r in revs for e in (r.get("new_equipment") or added_equipment(r["changes"]))]
    relief = pid.relief_scan(DATA / w.cfg["pid"]) if w.cfg.get("pid") else []
    relief_hit = [x for x in relief if x["tag"] in owners and x["status"] != "protected"]
    checklist = pssr(proposed, changes, names, after)
    head = (audit.entries(w.name)[-1:] or [{}])[0].get("hash")
    so = (ans or {}).get("second_opinion") or {}
    over_before = [r for r in rows if (r["before"] or 0) > 1]
    over_after = [r for r in rows if r["after"] > 1]
    stamp = time.strftime("%Y-%m-%d %H:%M %Z")
    reviewed = (w.built or {}).get("review") or {"status": "ok", "findings": [], "blocking": 0, "energy": {}}
    gaps = list(getattr(w, "gaps", None) or [])
    calculations = _stored_calculations(revs, ans)

    # the drawings: Rev A as received, Rev B with the changes drawn in (plantagent/revb.py)
    from . import revb
    rev_a = rev_b = None
    path = revb.case_svg(w)
    if path and path.exists():
        rev_a = path.read_text()
        if revs:
            try:
                rev_b = revb.sheet_for(w, built, [{"rev": r["rev"], "title": r["title"], "changes": r["changes"],
                                                    "calculation": r.get("calculation"),
                                                    "fixes": props.get(r["rev"], {}).get("fixes"), "tag": props.get(r["rev"], {}).get("tag")}
                                                   for r in revs])
            except Exception as e:  # noqa: BLE001 - the pack stands without the drawing; the failure is stated in it
                rev_b = {"svg": None, "error": f"{type(e).__name__}: {e}", "revisions": [], "unplaced": []}

    # capacities: before = the existing model; after = the combined proposal
    cap_before = next((c.get("capacity_multiple_before") for c in calculations if c.get("capacity_multiple_before") is not None), None)
    if cap_before is None and hasattr(w, "capacity") and not change_revs:
        try:
            cap_before = (w.capacity() or {}).get("capacity_multiple")
        except Exception:  # noqa: BLE001
            cap_before = None
    combined = (ans or {}).get("combined") or {}
    cap_after = combined.get("capacity_multiple") if not change_revs else (revs[-1].get("capacity_multiple") if revs else None)
    costs = {r["rev"]: (props.get(r["rev"]) or {}).get("cost_class") for r in revs}
    tp = w.cfg.get("throughput") or {}
    target_text = f"{target * 100:.0f} % of today's throughput"
    if tp.get("base"):
        target_text += f" ({tp.get('name', 'throughput')} {_num(tp['base'])} → {_num(tp['base'] * target)} {tp.get('unit', '')})"
    worst = lambda rs, k: max(rs, key=lambda r: r[k] or 0) if rs else None  # noqa: E731
    wb, wa = worst(rows, "before"), worst(rows, "after")
    result = (f"At {target * 100:.0f} %, existing plant: {len(over_before)} limit(s) over 100 %"
              + (f" (highest {nm(wb['id'])} {wb['check']} {_pct(wb['before'])})" if wb and wb["before"] else "")
              + f"; with the changes: " + ("all stated limits within 100 %" if not over_after else f"{len(over_after)} limit(s) still over 100 %")
              + (f" (highest {nm(wa['id'])} {wa['check']} {_pct(wa['after'])})" if wa else "") + ".")
    if cap_after is not None:
        result += f" Simulated maximum throughput: {_cap(cap_before)} → {_cap(cap_after)} of today."
    if not revs:
        decision_line = f"No change to the plant is needed: {(ans or {}).get('headline', '')}."
    else:
        verb = "Approve for detailed engineering" if not over_after else "Do not approve yet"
        decision_line = (f"{verb}: {len(revs)} change(s) to reach {target * 100:.0f} % of today's throughput - "
                         + "; ".join(f"({r['rev']}) {r['title']}" for r in revs) + ".")
    approvals = []
    for r in revs:
        bits = [f"cost class {costs.get(r['rev']) or 'not stated'}"]
        if any(c.get("add_unit") and c["add_unit"].get("type") not in ("mixer", "splitter", "recycle") for c in r["changes"]):
            bits.append("purchase of new equipment (vendor quote to confirm)")
        if any(c.get("add_unit") or c.get("reroute") for c in r["changes"]):
            bits.append("piping tie-ins (outage)")
        approvals.append(f"({r['rev']}) {r['title']}: " + ", ".join(bits))
    approvals.append(f"Pre-startup safety review: {len(checklist)} items (section 6.2).")

    md = [f"# Management of Change: {w.cfg['title']}", "",
          f"**DRAFT - NOT APPROVED.** Prepared {stamp} by PlantAgent from the working model. Nothing in this file is an approval.", "",
          "## 1. Summary", "",
          "| | |", "|---|---|",
          f"| **Decision requested** | {decision_line} |",
          f"| **Target** | {target_text} |",
          f"| **Result (DWSIM, re-solved for this file)** | {result} |",
          f"| **Cost class** | " + ("; ".join(f"({k}) {v or 'not stated'}" for k, v in costs.items()) or "no change") + " |",
          f"| **Needs approval** | " + "<br/>".join(approvals).replace("<br/>", "; ") + " |",
          f"| **Status** | DRAFT for engineering review; to be checked by a licensed engineer. Sign-off in section 7. |", ""]
    if ans and ans.get("summary"):
        md += [f"**Answer on record:** {ans.get('headline', '')}. {ans['summary']}", ""]

    cover = "\n".join(md) + "\n"
    md = ["## 2. Basis", "", f"**Question.** {w.cfg.get('question')}", "",
           f"**Plant and data sources.** {w.cfg.get('source') or w.cfg['title']}." + (f" {w.cfg['url']}" if w.cfg.get("url") else ""), ""]
    if w.cfg.get("data_note"):
        md += [f"**Data status.** {w.cfg['data_note']}", ""]
    ill = _illustrative(w)
    if ill:
        md += ["Values marked **ILLUSTRATIVE** in the data sheet (confirm before approval):", ""] + [f"- {x}" for x in ill[:8]] + [""]
    md += [f"**Model.** {w.built.get('label')} built by {w.built.get('model')} on {w.built.get('at')}; simulator DWSIM (headless). "
           f"Review status: **{reviewed.get('status', 'ok')}** ({len(reviewed.get('findings') or [])} finding(s), "
           f"{reviewed.get('blocking', 0) or 0} blocking; details in appendix C).", ""]
    if corrections:
        md += ["Model corrections applied before this study (not plant changes):", ""] + [f"- {r.get('title')}" for r in corrections] + [""]

    md += [f"## 3. Existing vs proposed at {target * 100:.0f} % (DWSIM, re-solved for this file)", "",
           "| Item | Check | Limit | Existing | Proposed | Proposed value |", "|---|---|---|---|---|---|"]
    shown = [r for r in rows if (r["before"] or 0) > 0.8 or r["after"] > 0.8 or r["id"] in owners]
    md += [f"| {nm(r['id'])} | {r['check']} | {qty(r['limit'], r['unit'])} | {_pct(r['before'])} | **{_pct(r['after'])}** | "
           f"{qty(r['value_after'], r['unit'])} |" for r in shown[:16]] or ["| - | no limit near 80 % | | | | |"]
    md += ["", "Existing and Proposed are utilisation (value / limit) of each limiting item at the target; over 100 % fails.", ""]

    md += ["## 4. Changes", ""]
    if not revs:
        md += ["No change to the plant: the answer on record needs none.", ""]
    field = list((ans or {}).get("field_checks") or [])
    used = set()
    drawn = {d["rev"]: d["drawn"] for d in (rev_b or {}).get("revisions") or []}
    for r in revs:
        p = props.get(r["rev"]) or {}
        tags = {_owner(proposed, c) for c in r["changes"]} | {p.get("fixes"), p.get("tag")}
        tags |= {c["add_unit"]["id"] for c in r["changes"] if c.get("add_unit")}
        tags |= set().union(*[_tags_in(c.get("physical_change"), set(names) | {t for t in (p.get("fixes"), p.get("tag")) if t}) for c in r["changes"]])
        md += [f"### 4.{r['rev']} {r['title']}", "",
               f"Cloud {r['rev']} on the Rev B drawing. Cost class: {costs.get(r['rev']) or 'not stated'}.", ""]
        phys = [c.get("physical_change") for c in r["changes"] if c.get("physical_change")]
        md += ["**What physically changes.**", ""]
        md += [f"- {x}" for x in phys] or []
        md += [f"- {_describe(built, c, names)}" for c in r["changes"]
               if not (c.get("add_unit") and c["add_unit"].get("type") in ("mixer", "splitter"))]
        if drawn.get(r["rev"]):
            md += [f"- On the drawing: {'; '.join(drawn[r['rev']])}."]
        md += ["", f"**Why.** {r.get('reason') or 'not stated'}", ""]
        rated = [c for c in r["changes"] if c.get("rating_source")]
        md += ["**Rating and rating source.**", ""]
        md += [f"- {c['add_unit']['id'] if c.get('add_unit') else nm(c['path'].split('.')[1])}: {c['rating_source']}" for c in rated] or \
              ["- Existing equipment; no rating is changed."]
        calc = r.get("calculation")
        md += ["", "**Before / Proposed calculation** (this change alone, DWSIM at the target).", ""]
        if calc:
            md += [f"- Simulated maximum: {_cap(calc.get('capacity_multiple_before'))} → {_cap(calc.get('capacity_multiple_after'))} of today; "
                   f"first limit {((calc.get('limited_by_before') or {}).get('id'))} → {((calc.get('limited_by_after') or {}).get('id'))}.", ""]
            md += _change_calc(calc, tags)
        else:
            lim = p.get("limited_by") or {}
            md += [f"- Fixes {p.get('fixes') or 'the limit above'}; alone this change gives a simulated maximum of {_cap(r.get('capacity_multiple'))}"
                   + (f" (next limit {nm(lim.get('id'))}, {lim.get('check')})" if lim else "") + "."]
        if r["new_equipment"]:
            md += ["", *_datasheet(r["changes"], calc),
                   "**Simulator screening.** The figures above are a simulator screening solve, not a mechanical design. "
                   "**Provisional equipment selection.** Ratings of new equipment are preliminary and marked to confirm. "
                   "**Vendor and mechanical design approval.** Not granted: vendor curve, materials, relief sizing and shop design remain to confirm.", ""]
        mine = [f for f in field if _tags_in(" ".join(str(f.get(k, "")) for k in ("item", "where", "changes")), tags)]
        used |= {id(f) for f in mine}
        md += ["", "**Field checks that could change this.**", ""]
        md += [f"- {f.get('item')}. Where: {f.get('where')}. If it differs: {f.get('changes')}" for f in mine] or ["- None raised for this change."]
        md += [""]
    rest = [f for f in field if id(f) not in used]
    if rest:
        md += [f"### 4.{len(revs) + 1} Other field checks", ""] + [f"- {f.get('item')}. Where: {f.get('where')}. If it differs: {f.get('changes')}" for f in rest] + [""]

    md += ["## 5. Drawings", ""]
    if rev_a:
        md += ["The next pages show the P&ID **Rev A** (existing, as received) and **Rev B** (proposed): each change is drawn in, "
               "clouded and numbered as in section 4, with the new design values written next to the equipment or line and a "
               "revision block (DRAFT - NOT APPROVED). Files in the pack: `rev_a.svg`, `rev_b.svg`, `rev_b.png`."]
        if rev_b and rev_b.get("unplaced"):
            md += ["", f"Not drawn on Rev B (no free position found; described in section 4): {', '.join(rev_b['unplaced'])}."]
        if rev_b and rev_b.get("error"):
            md += ["", f"Rev B could not be generated: {rev_b['error']}. Section 4 describes every change."]
    else:
        md += ["This project has no SVG P&ID; the changed equipment is: " + (", ".join(owners) or "none") + "."]
    part1 = "\n".join(md) + "\n"

    md = ["## 6. Risks and safety", "", "### 6.1 Relief protection (P&ID relief scan)", ""]
    md += ([f"- {x['tag']} {', '.join(x['side_fluids'])} side: {x['status']}. {x['detail']}" + (" Heated side that can be blocked in." if x["thermal_expansion_risk"] else "")
            for x in relief_hit] or ["- No changed existing equipment side lacks relief on this drawing." if relief else "- No smart P&ID: relief scan not available; review relief manually."])
    if new_equipment:
        md += ["- New equipment is not on the as-built P&ID: its relief, isolation and control design need engineering review before approval."]
    md += ["", "### 6.2 Pre-startup safety review (PSSR), generated from the changes", ""]
    md += [f"- [ ] {i}" for i in checklist]
    md += ["", "### 6.3 Second opinion", ""]
    if so.get("comparison"):
        c = so["comparison"]
        md += [f"An open-weights model answered the same question independently: **{c['status']}**."]
        md += [f"- Differs: {d}" for d in c["disagree"]] + [f"- Agrees: {a}" for a in c["agree"]]
    else:
        md += ["No second opinion was requested for this answer."]
    risks = []
    if reviewed.get("status") == "model needs review":
        risks.append(f"The model needs review ({reviewed.get('blocking', 0)} blocking finding(s)).")
    if over_after:
        risks.append("Limits still over 100 % with the changes: " + ", ".join(f"{nm(r['id'])} {r['check']} {_pct(r['after'])}" for r in over_after[:5]) + ".")
    if ill:
        risks.append("The result depends on ILLUSTRATIVE data-sheet values (section 2).")
    if risks:
        md += ["", "### 6.4 Open risks", ""] + [f"- {x}" for x in risks]
    md += ["", "## 7. Approvals (DRAFT: not approved)", "",
           "| Role | Name | Signature | Date |", "|---|---|---|---|",
           *[f"| {role} | _ | _ | _ |" for role in ("Process engineer", "Operations", "Process safety (MOC)", "Manager (approver)")],
           "", "## Appendix A. Reproducibility", "",
           f"- Code version (git): {_git_head()}; simulator: DWSIM (headless) via plantagent.process.",
           f"- Audit-chain head hash: `{head}` (chain intact: {audit.verify(w.name)['ok']}).",
           f"- Model: {w.built.get('label')} by {w.built.get('model')} on {w.built.get('at')}; answer by {(ans or {}).get('model') or '-'}.",
           f"- Run labels and calculation records: " + (", ".join(sorted({c.get('model_label') for c in calculations if c.get('model_label')})) or "re-solved in this file") + ".",
           f"- Sections 1, 3 and 6.2 were recomputed when this file was made; re-run `python -m plantagent.decision {w.name}` on the same "
           "revisions to reproduce them.",
           "", "## Appendix B. Capability gaps", ""]
    md += [f"- {g.get('what')}: {g.get('why')} Needed: {g.get('needed')}." for g in gaps] or ["- None recorded."]
    md += ["", "## Appendix C. Model review", "", f"Status: **{reviewed.get('status', 'ok')}**."]
    md += [f"- **{f.get('severity')}** - {f.get('check')}: {f.get('evidence')}" for f in reviewed.get("findings") or []] or ["- No findings."]
    if (reviewed.get("energy") or {}).get("note"):
        md += ["", reviewed["energy"]["note"]]
    md += ["", "## Appendix D. Model assumptions", ""] + ([f"- {a}" for a in (w.built.get("assumptions") or [])[:12]] or ["- None recorded."])
    part2 = "\n".join(md) + "\n"
    decision_md = cover + "\n" + part1 + "\n" + part2

    diffs = sorted((so.get("comparison") or {}).get("disagree") or [], key=lambda d: d.startswith(("units.", "feeds.", "limits.")))
    risk = ("the open-weights second opinion disagreed on: " + "; ".join(diffs[:3])) if diffs else "no second-opinion disagreement recorded"
    if reviewed.get("status") == "model needs review":
        risk = f"the model needs review ({reviewed.get('blocking', 0)} blocking finding(s)). " + risk
    memo = [f"# Memo: {w.cfg['title']}", "", f"{stamp} · DRAFT, not approved", "",
            f"**Decision asked for:** {w.cfg.get('question')}", "", f"**Recommendation:** {decision_line}", "", f"**Result:** {result}", ""]
    memo += [f"- ({r['rev']}) {r['title']} - cost class {costs.get(r['rev']) or 'not stated'}" for r in revs]
    memo += ["", f"**Risk:** {risk}. Relief findings on changed equipment: {len(relief_hit)}.", "",
             "**Measure next:** " + ("; ".join(f.get("item", "") for f in field) or
                                     "the first 24 h at the new throughput against the model's predicted values") + ".", "",
             f"Full MOC file with Rev A/Rev B drawings and PSSR checklist ({len(checklist)} items) attached. Audit head `{(head or '')[:12]}`."]
    memo_md = "\n".join(memo) + "\n"

    out = w.model_file.with_name("decision-" + time.strftime("%Y%m%d-%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "decision.md").write_text(decision_md)
    (out / "memo.md").write_text(memo_md)
    files = ["decision.md", "memo.md", "decision.json"]
    drawings = []
    if rev_a:
        (out / "rev_a.svg").write_text(rev_a)
        files.append("rev_a.svg")
        drawings.append(("5.1 P&ID Rev A - existing (as received)", rev_a))
    if rev_b and rev_b.get("svg"):
        for name in ("rev_b.svg", "redline.svg"):  # redline.svg: the name earlier packs and the web UI use
            (out / name).write_text(rev_b["svg"])
        files += ["rev_b.svg", "redline.svg"]
        png = revb.svg_png(rev_b["svg"])
        if png:
            (out / "rev_b.png").write_bytes(png)
            files.append("rev_b.png")
        drawings.append(("5.2 P&ID Rev B - proposed (DRAFT - NOT APPROVED)", rev_b["svg"]))
    data = {"case": w.name, "made": stamp, "target_scale": target, "revisions": revs, "new_equipment": new_equipment,
            "topology": topology(built, changes), "calculation": calculations, "capacity": {"before": cap_before, "after": cap_after},
            "limits": rows, "pssr": checklist, "drawing": {k: v for k, v in (rev_b or {}).items() if k != "svg"},
            "relief": relief_hit, "second_opinion": so.get("comparison"), "audit_head": head, "code": _git_head(),
            "model_review": reviewed, "gaps": gaps,
            "model": {k: w.built.get(k) for k in ("label", "model", "at", "review_status")}}
    footer = f"MOC {w.name} · {time.strftime('%Y-%m-%d')}"
    for name, parts, dr in (("decision.pdf", [cover, part1, part2], drawings), ("memo.pdf", [memo_md], ())):
        try:
            data.setdefault("pages", {})[name] = _pdf(parts, out / name, dr, footer)
            files.append(name)
        except Exception as e:  # noqa: BLE001 - the markdown and JSON stand without the PDF
            data.setdefault("pdf_errors", []).append(f"{name}: {type(e).__name__}: {e}")
    (out / "decision.json").write_text(json.dumps(data, indent=1, default=str))
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
