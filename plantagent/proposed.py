"""Draft P&ID overlay and calculation sheet for a verified physical proposal.

The as-built SVG is never written. A proposed drawing is a new document: the original
markup plus a marked overlay. Placement follows process topology. A new physical unit
is drawn only when it sits on the new branch between a new splitter and a new mixer,
parallel to one existing unit that already has a coordinate. Anything else is reported
as unplaced new equipment and is not given a symbol.
"""
import copy
import math
import re
import xml.etree.ElementTree as ET

from .plant import added_equipment, patch

ROUTING = {"mixer", "splitter", "recycle"}
OFFSET = 36
ALONG = 32
CLEAR = 14
STROKE = "#0b7ea8"

_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
_CMD = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


def num(v):
    """Format a stored number without inventing a rounded substitute."""
    if v is None or v == "":
        return "to confirm"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return format(v, ".8g")
    return str(v)


def esc(v):
    return (str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def ports(unit):
    """Inlet and outlet stream ids. cold/hot are [in, out] pairs; a bare list is several streams on that side."""
    ins, outs = [], []

    def add(bucket, value):
        if isinstance(value, str) and value:
            bucket.append(value)
        elif isinstance(value, list) and value and all(isinstance(x, str) for x in value):
            bucket.extend(x for x in value if x)

    add(ins, unit.get("in"))
    add(outs, unit.get("out"))
    for key in ("vapor", "liquid", "product", "reject", "distillate", "bottoms"):
        add(outs, unit.get(key))
    for key in ("cold", "hot"):
        pair = unit.get(key)
        if isinstance(pair, (list, tuple)) and len(pair) == 2 and all(isinstance(x, str) for x in pair):
            ins.append(pair[0])
            outs.append(pair[1])
    return ins, outs


def _index(units):
    by_id, prod, cons = {}, {}, {}
    for unit in units:
        by_id[unit.get("id")] = unit
        ins, outs = ports(unit)
        for stream in ins:
            cons.setdefault(stream, []).append(unit.get("id"))
        for stream in outs:
            prod[stream] = unit.get("id")
    return by_id, prod, cons


def topology_units(spec, changes):
    """Units after the proposal. If the working spec already contains the new ids, do not add them twice."""
    added = [c["add_unit"] for c in changes or [] if isinstance(c, dict) and isinstance(c.get("add_unit"), dict)]
    added_ids = {u.get("id") for u in added if u.get("id")}
    base = list(spec.get("units") or [])
    base_ids = {u.get("id") for u in base}
    if added_ids & base_ids:
        units = base
    else:
        units = patch(copy.deepcopy(spec), changes).get("units") or []
    return units, base_ids - added_ids, added_ids


def topology(spec, changes):
    """Canonical proposed connectivity for the decision file."""
    try:
        units, _, _ = topology_units(spec, changes or [])
    except ValueError:
        units = list(spec.get("units") or [])
    out = []
    for unit in units:
        ins, outs = ports(unit)
        out.append({"id": unit.get("id"), "type": unit.get("type"), "in": ins, "out": outs})
    return {"changes": changes or [], "units": out}


def _path_points(d):
    """Absolute coordinates visited by a path, enough for a symbol bounding box."""
    if not d:
        return []
    tokens = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", d)
    pts, i, cx, cy, sx, sy, cmd = [], 0, 0.0, 0.0, 0.0, 0.0, ""
    pair_count = {"C": 3, "c": 3, "S": 2, "s": 2, "Q": 2, "q": 2, "T": 1, "t": 1, "A": 1, "a": 1}

    def take():
        nonlocal i
        if i >= len(tokens) or _CMD.fullmatch(tokens[i]):
            return None
        i += 1
        return float(tokens[i - 1])

    while i < len(tokens):
        if _CMD.fullmatch(tokens[i]):
            cmd = tokens[i]
            i += 1
        if cmd in ("Z", "z"):
            cx, cy = sx, sy
            pts.append((cx, cy))
            cmd = ""
            continue
        if cmd in ("M", "L"):
            x, y = take(), take()
            if x is None or y is None:
                break
            cx, cy = x, y
            if cmd == "M":
                sx, sy = cx, cy
                cmd = "L"
            pts.append((cx, cy))
        elif cmd in ("m", "l"):
            x, y = take(), take()
            if x is None or y is None:
                break
            cx, cy = cx + x, cy + y
            if cmd == "m":
                sx, sy = cx, cy
                cmd = "l"
            pts.append((cx, cy))
        elif cmd == "H":
            x = take()
            if x is None:
                break
            cx = x
            pts.append((cx, cy))
        elif cmd == "h":
            x = take()
            if x is None:
                break
            cx += x
            pts.append((cx, cy))
        elif cmd == "V":
            y = take()
            if y is None:
                break
            cy = y
            pts.append((cx, cy))
        elif cmd == "v":
            y = take()
            if y is None:
                break
            cy += y
            pts.append((cx, cy))
        else:
            n = pair_count.get(cmd, 1)
            vals = [take() for _ in range(n * 2 if cmd not in ("A", "a") else 7)]
            if any(v is None for v in vals):
                break
            if cmd in ("A", "a"):
                x, y = vals[5], vals[6]
                cx, cy = (cx + x, cy + y) if cmd == "a" else (x, y)
            else:
                x, y = vals[-2], vals[-1]
                cx, cy = (cx + x, cy + y) if cmd.islower() else (x, y)
            pts.append((cx, cy))
    return pts


def _shape_points(el):
    tag = el.tag.split("}")[-1]
    if tag == "rect":
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        return [(x, y), (x + float(el.get("width", 0)), y + float(el.get("height", 0)))]
    if tag == "circle":
        cx, cy, r = float(el.get("cx", 0)), float(el.get("cy", 0)), float(el.get("r", 0))
        return [(cx - r, cy - r), (cx + r, cy + r)]
    if tag == "ellipse":
        cx, cy = float(el.get("cx", 0)), float(el.get("cy", 0))
        rx, ry = float(el.get("rx", 0)), float(el.get("ry", 0))
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    if tag == "line":
        return [(float(el.get("x1", 0)), float(el.get("y1", 0))), (float(el.get("x2", 0)), float(el.get("y2", 0)))]
    if tag in ("polyline", "polygon"):
        nums = [float(n) for n in _NUM.findall(el.get("points") or "")]
        return list(zip(nums[0::2], nums[1::2]))
    if tag == "path":
        return _path_points(el.get("d") or "")
    return []


def _local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else ""


def centers_from_svg(svg):
    """Symbol centre of each data-tag group. Text labels are not part of the symbol."""
    root = ET.fromstring(svg)
    centers = {}
    for group in root.iter():
        if _local(group.tag) != "g":
            continue
        tag = group.get("data-tag")
        if not tag:
            continue
        pts = []
        for el in group.iter():
            if el is group or _local(el.tag) == "g":
                continue
            pts.extend(_shape_points(el))
        if pts:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            centers[tag] = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    return centers


def _line_boxes(svg):
    root = ET.fromstring(svg)
    boxes = []
    for group in root.iter():
        if _local(group.tag) != "g" or not group.get("data-line"):
            continue
        pts = []
        for el in group.iter():
            pts.extend(_shape_points(el))
        if not pts:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        boxes.append({"line": group.get("data-line"), "from": group.get("data-from") or "",
                      "to": group.get("data-to") or "", "box": (min(xs), min(ys), max(xs), max(ys))})
    return boxes


def _walk(seed, forward, by_id, prod, cons, centers, seen):
    if not seed or seed in seen:
        return None
    unit = by_id.get(seed)
    if seed in centers and (not unit or unit.get("type") not in ROUTING):
        return seed
    seen = seen | {seed}
    if not unit:
        return None
    ins, outs = ports(unit)
    nxt = []
    if forward:
        for stream in outs:
            nxt.extend(cons.get(stream) or [])
    else:
        for stream in ins:
            if prod.get(stream):
                nxt.append(prod[stream])
    for uid in nxt:
        hit = _walk(uid, forward, by_id, prod, cons, centers, seen)
        if hit:
            return hit
    return None


def _neighbor(uid, forward, by_id, prod, cons, centers):
    unit = by_id.get(uid)
    if not unit:
        return None
    ins, outs = ports(unit)
    seeds = []
    if forward:
        for stream in outs:
            seeds.extend(cons.get(stream) or [])
    else:
        for stream in ins:
            if prod.get(stream):
                seeds.append(prod[stream])
    for seed in seeds:
        hit = _walk(seed, forward, by_id, prod, cons, centers, {uid})
        if hit:
            return hit
    return None


def _parallel(uid, by_id, prod, cons, existing_ids, added_ids):
    """A new physical unit between a new splitter and a new mixer, beside one existing unit."""
    unit = by_id.get(uid)
    if not unit:
        return None
    ins, outs = ports(unit)
    if len(ins) != 1 or len(outs) != 1:
        return None
    splitter, mixer = prod.get(ins[0]), (cons.get(outs[0]) or [None])[0]
    if splitter not in added_ids or mixer not in added_ids:
        return None
    if by_id.get(splitter, {}).get("type") != "splitter" or by_id.get(mixer, {}).get("type") != "mixer":
        return None
    partners = []
    for stream in ports(by_id[splitter])[1]:
        if stream == ins[0]:
            continue
        for cid in cons.get(stream) or []:
            if cid in existing_ids and cid not in partners:
                partners.append(cid)
    if len(partners) != 1:
        return None
    partner = partners[0]
    if not any(mixer in (cons.get(stream) or []) for stream in ports(by_id[partner])[1]):
        return None
    return {"splitter": splitter, "mixer": mixer, "partner": partner, "in_stream": ins[0], "out_stream": outs[0],
            "mixer_out": (ports(by_id[mixer])[1] or [None])[0],
            "partner_out": next((s for s in ports(by_id[partner])[1] if mixer in (cons.get(s) or [])), None),
            "split_in": (ports(by_id[splitter])[0] or [None])[0]}


def _flow_axis(origin, target):
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    if abs(dx) >= abs(dy):
        return (1.0 if dx >= 0 else -1.0, 0.0)
    return (0.0, 1.0 if dy >= 0 else -1.0)


def _clear(pt, centers, ignore, minimum):
    for tag, (x, y) in centers.items():
        if tag in ignore:
            continue
        if math.hypot(pt[0] - x, pt[1] - y) < minimum:
            return False
    return True


def _place_parallel(info, centers):
    partner = centers.get(info["partner"])
    if not partner:
        return None
    down_id = info.get("downstream")
    up_id = info.get("upstream")
    target = centers.get(down_id) or centers.get(up_id)
    axis = _flow_axis(partner, target) if target else (1.0, 0.0)
    perp = [(-axis[1], axis[0]), (axis[1], -axis[0])]
    # Prefer the lower side of the sheet when both sides are open (larger y in this drawing).
    perp.sort(key=lambda p: -(partner[1] + p[1] * OFFSET))
    spot = None
    for px, py in perp:
        cand = (partner[0] + px * OFFSET, partner[1] + py * OFFSET)
        if _clear(cand, centers, {info["partner"]}, CLEAR):
            spot = cand
            break
    if spot is None:
        return None
    splitter = (partner[0] - axis[0] * ALONG, partner[1] - axis[1] * ALONG)
    reach = ALONG
    if down_id in centers:
        room = abs((centers[down_id][0] - partner[0]) * axis[0] + (centers[down_id][1] - partner[1]) * axis[1])
        reach = min(ALONG, max(18, room - 18))
    mixer = (partner[0] + axis[0] * reach, partner[1] + axis[1] * reach)
    if not _clear(splitter, centers, {info["partner"]}, CLEAR) or not _clear(mixer, centers, {info["partner"], down_id}, CLEAR):
        return None
    return {"unit_at": spot, "splitter_at": splitter, "mixer_at": mixer, "axis": axis}


def _ortho(a, b, avoid):
    if abs(a[0] - b[0]) < 1 or abs(a[1] - b[1]) < 1:
        return [a, b]
    options = [[a, (b[0], a[1]), b], [a, (a[0], b[1]), b]]

    def penalty(pts):
        elbow = pts[1]
        dists = [math.hypot(elbow[0] - x, elbow[1] - y) for x, y in avoid]
        return min(dists) if dists else 1

    return max(options, key=penalty)


def _cloud(cx, cy, radius=9, bumps=8):
    """A small revision cloud marking a changed connection, not a box around the whole line."""
    parts = []
    for i in range(bumps):
        a0 = 2 * math.pi * i / bumps
        a1 = 2 * math.pi * (i + 1) / bumps
        am = (a0 + a1) / 2
        x0, y0 = cx + radius * math.cos(a0), cy + radius * math.sin(a0)
        x1, y1 = cx + radius * math.cos(a1), cy + radius * math.sin(a1)
        bulge = radius + 3.2
        mx, my = cx + bulge * math.cos(am), cy + bulge * math.sin(am)
        parts.append(f"{'M' if i == 0 else 'L'}{x0:.1f},{y0:.1f} Q{mx:.1f},{my:.1f} {x1:.1f},{y1:.1f}")
    parts.append("Z")
    return " ".join(parts)


def _symbol(kind):
    """Simple ISA-like marks, drawn around a local origin."""
    if kind == "compressor":
        return '<path d="M-8,-6 L8,-4 V4 L-8,6 Z"/><circle r="1.8" fill="none"/><path d="M0,-3.2 L4,-4.6 M0,3.2 L4,1.8" fill="none"/>'
    if kind == "pump":
        return '<circle r="6" fill="#f4fbff"/><path d="M-3,-3.5 L4,0 L-3,3.5 Z" fill="#d7f1f8"/>'
    if kind == "hx":
        return '<rect x="-10" y="-6" width="20" height="12" rx="5" fill="#f4fbff"/><path d="M-9,-2 H9 M-9,2 H9" fill="none"/>'
    if kind == "splitter":
        return '<circle r="4" fill="#f4fbff"/><path d="M-7,0 H-4 M4,0 H7 M0,-4 V-7" fill="none"/>'
    if kind == "mixer":
        return '<rect x="-4" y="-4" width="8" height="8" fill="#f4fbff"/><path d="M-7,0 H-4 M4,0 H7 M0,4 V7" fill="none"/>'
    if kind in ("tank", "evaporator", "vessel", "column"):
        return '<rect x="-6" y="-10" width="12" height="20" rx="6" fill="#f4fbff"/>'
    return '<rect x="-8" y="-6" width="16" height="12" fill="#f4fbff"/>'


def _qty(value, unit):
    """Readable quantity from a stored SI field. kg/h and kW become t/h and MW when large."""
    if value is None:
        return None, unit
    if unit == "kg/h" and abs(value) >= 1000:
        return value / 1000.0, "t/h"
    if unit == "kW" and abs(value) >= 1000:
        return value / 1000.0, "MW"
    return value, unit


def equipment_duty(row):
    """Operating point and provisional rating from a canonical new_equipment record."""
    row = row or {}
    op = row.get("operating_point") or row.get("operating") or {}
    limits = row.get("limits") or {}
    rating = row.get("rating") or {}
    flow_v, flow_u = _qty(op.get("kg_h") if op.get("kg_h") is not None else op.get("flow"),
                          "kg/h" if op.get("kg_h") is not None else (op.get("flow_unit") or "kg/h"))
    shaft_raw = op.get("kW") if op.get("kW") is not None else (op.get("shaft") if op.get("shaft") is not None else op.get("duty"))
    shaft_u0 = "kW" if op.get("kW") is not None else (op.get("shaft_unit") or op.get("duty_unit") or "kW")
    shaft_v, shaft_u = _qty(shaft_raw, shaft_u0)
    rate_flow, rate_fu = _qty(limits.get("max_kg_h") if limits.get("max_kg_h") is not None else rating.get("flow"),
                              "kg/h" if limits.get("max_kg_h") is not None else (rating.get("flow_unit") or "kg/h"))
    rate_shaft_raw = limits.get("max_kW") if limits.get("max_kW") is not None else (
        rating.get("shaft") if rating.get("shaft") is not None else rating.get("duty"))
    rate_shaft_u0 = "kW" if limits.get("max_kW") is not None else (rating.get("shaft_unit") or rating.get("duty_unit") or "kW")
    rate_shaft, rate_su = _qty(rate_shaft_raw, rate_shaft_u0)
    return {
        "flow": flow_v, "flow_unit": flow_u if flow_v is not None else None,
        "shaft": shaft_v, "shaft_unit": shaft_u if shaft_v is not None else None,
        "rating_flow": rate_flow, "rating_flow_unit": rate_fu if rate_flow is not None else None,
        "rating_shaft": rate_shaft, "rating_shaft_unit": rate_su if rate_shaft is not None else None,
        "rating_source": row.get("rating_source") or rating.get("source") or "to confirm",
        "status": row.get("status") or "new equipment, rating to confirm",
        "efficiency_pct": op.get("eff_pct") if op.get("eff_pct") is not None else op.get("efficiency_pct"),
        "pressure_ratio": op.get("pressure_ratio"), "head": op.get("head"), "head_unit": op.get("head_unit"),
    }


def _duty_lines(row):
    d = equipment_duty(row)
    lines = []
    lines.append(f"operating flow {num(d['flow'])} {d['flow_unit'] or 'to confirm'}" if d["flow"] is not None
                 else "operating flow to confirm")
    lines.append(f"calculated shaft {num(d['shaft'])} {d['shaft_unit'] or 'to confirm'}" if d["shaft"] is not None
                 else "calculated duty to confirm")
    bits = []
    if d["rating_flow"] is not None:
        bits.append(f"{num(d['rating_flow'])} {d['rating_flow_unit'] or ''}".strip())
    if d["rating_shaft"] is not None:
        bits.append(f"{num(d['rating_shaft'])} {d['rating_shaft_unit'] or ''}".strip())
    lines.append("preliminary rating " + (" / ".join(bits) if bits else "to confirm"))
    lines.append("vendor confirmation required")
    lines.append("vendor curve to confirm")
    return lines


def present_calculation(calculation):
    """UI/decision view of a verify() calculation record. Values stay stored SI; display converts where useful."""
    if not calculation:
        return None
    c = calculation
    if "capacity_multiple_after" in c or "checks" in c or "operating_point" in str(c.get("new_equipment") or []):
        scale = c.get("target_scale")
        cap_b = c.get("capacity_multiple_before")
        cap_a = c.get("capacity_multiple_after")
        fb, fa = c.get("limited_by_before") or {}, c.get("limited_by_after") or {}
        if not isinstance(fb, dict):
            fb = {}
        if not isinstance(fa, dict):
            fa = {}
        limits = []
        for row in c.get("checks") or []:
            value, unit = row.get("value"), row.get("unit") or ""
            limit = row.get("limit")
            if unit == "kg/h":
                value, limit, unit = (None if value is None else value / 1000.0), (None if limit is None else limit / 1000.0), "t/h"
            elif unit == "kW" and value is not None and abs(value) >= 1000:
                value, limit, unit = value / 1000.0, (None if limit is None else limit / 1000.0), "MW"
            limits.append({"id": row.get("id"), "check": row.get("check"),
                           "before_pct": None if row.get("before") is None else row["before"] * 100,
                           "after_pct": None if row.get("after") is None else row["after"] * 100,
                           "value": value, "limit": limit, "unit": unit})
        streams = []
        for row in c.get("streams") or []:
            flow, flow_u = _qty(row.get("kg_h") if row.get("kg_h") is not None else row.get("flow"),
                                "kg/h" if row.get("kg_h") is not None else (row.get("flow_unit") or "kg/h"))
            phase = row.get("phase")
            if phase is None and row.get("vapour_frac") is not None:
                phase = "vapour" if row["vapour_frac"] >= 0.5 else "liquid"
            streams.append({"id": row.get("id"), "T_C": row.get("T_C"), "P_bar": row.get("P_bar"),
                            "flow": flow, "flow_unit": flow_u if flow is not None else None, "phase": phase or "to confirm"})
        new_rows = []
        for row in c.get("new_equipment") or []:
            duty = equipment_duty(row)
            new_rows.append({**duty, "id": row.get("id"), "type": row.get("type"), "service": row.get("service") or row.get("type"),
                             "inlet": row.get("inlet") or {}, "outlet": row.get("outlet") or {},
                             "missing": row.get("missing") or ["vendor curve", "mechanical design", "materials"],
                             "assumptions": row.get("assumptions") or []})
        total = 0.0
        have = False
        for uid, u in (c.get("units") or {}).items():
            if isinstance(u, dict) and u.get("kg_h") is not None and str(uid).startswith("K-"):
                total += u["kg_h"]
                have = True
        if not have:
            for row in c.get("new_equipment") or []:
                op = row.get("operating_point") or {}
                if op.get("kg_h") is not None:
                    total += op["kg_h"]
                    have = True
            for uid, u in (c.get("units") or {}).items():
                if isinstance(u, dict) and u.get("kg_h") is not None and uid not in {r.get("id") for r in c.get("new_equipment") or []}:
                    if any(x.get("id") == uid for x in c.get("checks") or []):
                        total += u["kg_h"]
                        have = True
        thru = None
        if have:
            thru = {"label": "total compression", "scale_pct": None if scale is None else scale * 100,
                    "value": total / 1000.0, "unit": "t/h"}
        return {
            "capacity_before_pct": None if cap_b is None else cap_b * 100,
            "capacity_after_pct": None if cap_a is None else cap_a * 100,
            "first_limit_before": {"id": fb.get("id"), "check": fb.get("check"),
                                  "pct": None if fb.get("utilisation") is None else fb["utilisation"] * 100},
            "first_limit_after": {"id": fa.get("id"), "check": fa.get("check"),
                                 "pct": None if fa.get("utilisation") is None else fa["utilisation"] * 100},
            "throughput": thru, "limits": limits, "streams": streams, "new_equipment": new_rows,
            "provenance": {"simulator": c.get("simulator") or "to confirm", "kind": "simulator screening",
                           "note": "Screening solve of the stored model. Not a vendor or mechanical approval."},
            "assumptions": c.get("assumptions") or ["to confirm"],
            "warnings": c.get("warnings") or c.get("errors") or ["to confirm"],
        }
    return c


def _pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def plan_overlay(spec, changes, centers):
    """Placement plan. Unplaced physical units are listed and must not be drawn."""
    units, existing_ids, added_ids = topology_units(spec, changes)
    by_id, prod, cons = _index(units)
    placed, unplaced, lines, extras = [], [], [], {}
    occupied = dict(centers)
    for uid in sorted(added_ids):
        unit = by_id.get(uid)
        if not unit or unit.get("type") in ROUTING:
            continue
        if uid in centers:
            unplaced.append(uid)
            continue
        info = _parallel(uid, by_id, prod, cons, existing_ids, added_ids)
        if not info or info["partner"] not in centers:
            unplaced.append(uid)
            continue
        info["upstream"] = _neighbor(info["splitter"], False, by_id, prod, cons, centers)
        info["downstream"] = _neighbor(info["mixer"], True, by_id, prod, cons, centers)
        spot = _place_parallel(info, occupied)
        if not spot:
            unplaced.append(uid)
            continue
        occupied[uid] = spot["unit_at"]
        occupied[info["splitter"]] = spot["splitter_at"]
        occupied[info["mixer"]] = spot["mixer_at"]
        placed.append({**info, "id": uid, "type": unit.get("type"), **spot})
    for item in placed:
        avoid = list(occupied.values())
        up = centers.get(item.get("upstream"))
        down = centers.get(item.get("downstream"))
        partner_stream = next(s for s in ports(by_id[item["splitter"]])[1] if item["partner"] in (cons.get(s) or []))
        routes = []
        if up:
            routes.append((item.get("split_in") or "inlet", item["upstream"], item["splitter"], up, item["splitter_at"]))
        routes.append((partner_stream, item["splitter"], item["partner"], item["splitter_at"], centers[item["partner"]]))
        routes.append((item["in_stream"], item["splitter"], item["id"], item["splitter_at"], item["unit_at"]))
        if item.get("partner_out"):
            routes.append((item["partner_out"], item["partner"], item["mixer"], centers[item["partner"]], item["mixer_at"]))
        routes.append((item["out_stream"], item["id"], item["mixer"], item["unit_at"], item["mixer_at"]))
        if down and item.get("mixer_out"):
            routes.append((item["mixer_out"], item["mixer"], item["downstream"], item["mixer_at"], down))
        for stream, src, dst, a, b in routes:
            lines.append({"stream": stream or f"{src}-{dst}", "from": src, "to": dst, "points": _ortho(a, b, avoid)})
        extras[item["splitter"]] = {"type": "splitter", "at": item["splitter_at"]}
        extras[item["mixer"]] = {"type": "mixer", "at": item["mixer_at"]}
    symbols = [{"id": p["id"], "type": p["type"], "at": p["unit_at"], "new": True} for p in placed]
    symbols += [{"id": i, "type": m["type"], "at": m["at"], "new": True} for i, m in extras.items()]
    return {"placed": placed, "unplaced": unplaced, "lines": lines, "symbols": symbols, "rerouted": [
        c["reroute"]["unit"] for c in changes or [] if isinstance(c, dict) and isinstance(c.get("reroute"), dict)]}


def _legend():
    rows = [("Existing", "#294248", ""), ("Proposed new", STROKE, 'stroke-dasharray="3,1.4"'),
            ("Rerouted", "#b45309", ""), ("Rating to confirm", STROKE, "")]
    body = ['<g data-legend="proposed" pointer-events="none">']
    for i, (label, color, extra) in enumerate(rows):
        y = -268 + i * 5.2
        if label == "Rerouted":
            body.append(f'<path d="M8,{y - 1:.1f} Q12,{y - 3:.1f} 16,{y - 1:.1f} Q20,{y + 1:.1f} 24,{y - 1:.1f}" fill="none" stroke="{color}" stroke-width="0.7"/>')
        elif label == "Rating to confirm":
            body.append(f'<text x="8" y="{y:.1f}" font-size="2.6" fill="{color}" font-family="sans-serif">{label}</text>')
            continue
        else:
            body.append(f'<line x1="8" y1="{y - 1:.1f}" x2="24" y2="{y - 1:.1f}" stroke="{color}" stroke-width="0.9" {extra}/>')
        body.append(f'<text x="27" y="{y:.1f}" font-size="2.6" fill="#17383d" font-family="sans-serif">{label}</text>')
    body.append("</g>")
    return "".join(body)


def overlay(svg, spec, changes, calculation=None, *, verified=True):
    """Return a proposed SVG document. The caller's string and file are left unchanged.

    Unverified proposals return the original string and drawn=False.
    """
    if not verified:
        return {"svg": svg, "drawn": False, "unplaced": [], "placed": [],
                "reason": "unverified proposal: no proposed drawing"}
    physical = [e["id"] for e in added_equipment(changes)]
    if not physical:
        return {"svg": svg, "drawn": False, "unplaced": [], "placed": [], "reason": "no new physical equipment"}
    try:
        centers = centers_from_svg(svg)
        planned = plan_overlay(spec, changes, centers)
    except (ValueError, ET.ParseError) as exc:
        planned = {"placed": [], "unplaced": physical, "lines": [], "symbols": [], "rerouted": []}
        reason = f"unplaced new equipment: {exc}"
    else:
        reason = ""
    duties = {row.get("id"): row for row in (calculation or {}).get("new_equipment") or [] if isinstance(row, dict)}
    parts = ['<g id="proposed-draft" data-draft="true" font-family="sans-serif">',
             f'<defs><marker id="arr-draft" markerWidth="5" markerHeight="5" refX="4.5" refY="2.5" orient="auto" markerUnits="userSpaceOnUse">'
             f'<path d="M0,0 L5,2.5 0,5 Z" fill="{STROKE}"/></marker></defs>',
             f'<text x="188" y="-288" font-size="7" font-weight="700" fill="{STROKE}" pointer-events="none">DRAFT – NOT APPROVED</text>',
             _legend()]
    rerouted = set(planned.get("rerouted") or [])
    for box in _line_boxes(svg):
        if box["from"] in rerouted or box["to"] in rerouted:
            x0, y0, x1, y1 = box["box"]
            path = _cloud((x0 + x1) / 2, (y0 + y1) / 2)
            parts.append(f'<g data-rerouted="{esc(box["line"])}" data-from="{esc(box["from"])}" data-to="{esc(box["to"])}">'
                         f'<path d="{path}" fill="none" stroke="#b45309" stroke-width="0.6" pointer-events="none"/></g>')
    for line in planned["lines"]:
        parts.append(f'<g class="proposed-new" data-line="{esc(line["stream"])}" data-from="{esc(line["from"])}" data-to="{esc(line["to"])}">'
                     f'<polyline points="{_pts(line["points"])}" fill="none" stroke="{STROKE}" stroke-width="0.9" '
                     f'stroke-dasharray="3,1.4" stroke-linejoin="round" marker-end="url(#arr-draft)"/>')
        a, b = line["points"][0], line["points"][-1]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        parts.append(f'<text x="{mx + 1.5:.1f}" y="{my - 1.5:.1f}" font-size="2.2" fill="{STROKE}" pointer-events="none">{esc(line["stream"])}</text></g>')
    for sym in planned["symbols"]:
        x, y = sym["at"]
        kind = sym["type"] or "equipment"
        note = ""
        if kind not in ROUTING:
            rows = _duty_lines(duties.get(sym["id"]))
            note = "".join(
                f'<text x="{x - 11:.1f}" y="{y + 11 + i * 3.1:.1f}" text-anchor="end" font-size="2.3" fill="#0b4f66" pointer-events="none">{esc(row)}</text>'
                for i, row in enumerate(rows))
        label = kind if kind in ROUTING else (duties.get(sym["id"]) or {}).get("service") or kind
        parts.append(f'<g class="proposed-new" data-tag="{esc(sym["id"])}" data-new="true" data-name="{esc(label)}" fill="#f4fbff" stroke="{STROKE}" stroke-width="0.8">'
                     f'<g transform="translate({x:.1f},{y:.1f})">{_symbol(kind)}</g>'
                     f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" font-size="3.2" font-weight="700" stroke="none" fill="#0b4f66" pointer-events="none">{esc(sym["id"])}</text>'
                     f'{note}</g>')
    if planned["unplaced"]:
        listed = ", ".join(planned["unplaced"])
        parts.append(f'<text x="8" y="-248" font-size="3" fill="#b45309" pointer-events="none">unplaced new equipment: {esc(listed)}</text>')
        reason = (reason + "; " if reason else "") + "unplaced new equipment: " + listed
    parts.append("</g>")
    idx = svg.rfind("</svg>")
    if idx < 0:
        return {"svg": svg, "drawn": False, "unplaced": physical, "placed": [], "reason": "unplaced new equipment: drawing has no svg root"}
    return {"svg": svg[:idx] + "".join(parts) + svg[idx:], "drawn": True, "unplaced": planned["unplaced"],
            "placed": [p["id"] for p in planned["placed"]], "reason": reason}


def _pct(v):
    return "—" if v is None else f"{num(v)} %"


def calculation_markdown(calculation):
    """Before/proposed sheet from a stored calculation record. Missing fields stay 'to confirm'."""
    c = present_calculation(calculation)
    if not c:
        return ""
    cap_b, cap_a = c.get("capacity_before_pct"), c.get("capacity_after_pct")
    fb, fa = c.get("first_limit_before") or {}, c.get("first_limit_after") or {}
    thru = c.get("throughput") or {}
    lines = ["### Before / Proposed calculation", ""]
    if thru:
        lines.append(f"- {thru.get('label') or 'Throughput'} at {num(thru.get('scale_pct'))} %: {num(thru.get('value'))} {thru.get('unit') or ''}".rstrip())
    lines.append(f"- Capacity before: {_pct(cap_b)}")
    lines.append(f"- Capacity after: {_pct(cap_a)}")
    lines.append(f"- First limit before: {fb.get('id') or 'to confirm'} {fb.get('check') or ''} {_pct(fb.get('pct'))}".strip())
    lines.append(f"- First limit after: {fa.get('id') or 'to confirm'} {fa.get('check') or ''} {_pct(fa.get('pct'))}".strip())
    lines += ["", "| Equipment | Check | Before % | After % | Calculated value | Limit |", "|---|---|---|---|---|---|"]
    for row in c.get("limits") or []:
        lines.append(f"| {row.get('id')} | {row.get('check')} | {_pct(row.get('before_pct'))} | {_pct(row.get('after_pct'))} | "
                     f"{num(row.get('value'))} {row.get('unit') or ''} | {num(row.get('limit'))} {row.get('unit') or ''} |")
    lines += ["", "| Stream | T | P | Flow | Phase |", "|---|---|---|---|---|"]
    for row in c.get("streams") or []:
        lines.append(f"| {row.get('id')} | {num(row.get('T_C'))} °C | {num(row.get('P_bar'))} bar | "
                     f"{num(row.get('flow'))} {row.get('flow_unit') or ''} | {row.get('phase') or 'to confirm'} |")
    lines += ["", "#### New equipment duty versus provisional rating", ""]
    for row in c.get("new_equipment") or []:
        lines.append(f"- **{row.get('id')}** operating {num(row.get('flow'))} {row.get('flow_unit') or ''} / shaft {num(row.get('shaft'))} {row.get('shaft_unit') or ''}; "
                     f"provisional rating {num(row.get('rating_flow'))} {row.get('rating_flow_unit') or ''} / {num(row.get('rating_shaft'))} {row.get('rating_shaft_unit') or ''}; "
                     f"source: {row.get('rating_source') or 'to confirm'}")
    prov = c.get("provenance") or {}
    lines += ["", f"Simulator provenance: {prov.get('simulator') or 'to confirm'} — {prov.get('kind') or 'simulator screening'}. {prov.get('note') or ''}"]
    lines += ["", "Assumptions:"] + [f"- {a}" for a in c.get("assumptions") or ["to confirm"]]
    lines += ["", "Warnings:"] + [f"- {w}" for w in c.get("warnings") or ["to confirm"]]
    return "\n".join(lines)


def datasheet_markdown(changes, calculation=None):
    """Preliminary datasheet. Vendor data that was not stored is marked to confirm."""
    presented = present_calculation(calculation) or {}
    rows = {e.get("id"): e for e in presented.get("new_equipment") or [] if isinstance(e, dict)}
    by_raw = {e.get("id"): e for e in (calculation or {}).get("new_equipment") or [] if isinstance(e, dict)}
    streams = {s.get("id"): s for s in (calculation or {}).get("streams") or [] if isinstance(s, dict)}
    physical = added_equipment(changes)
    if not physical:
        return ""
    lines = ["### Preliminary equipment datasheet", "",
             "Provisional equipment selection only. This is not a vendor datasheet and not a mechanical design approval.", ""]
    for equip in physical:
        row = rows.get(equip["id"]) or {}
        raw = by_raw.get(equip["id"]) or {}
        add = next((c.get("add_unit") for c in changes or []
                    if isinstance(c, dict) and isinstance(c.get("add_unit"), dict) and c["add_unit"].get("id") == equip["id"]), {})
        ins, outs = ports(add) if add else ([], [])
        inlet_s = streams.get(ins[0]) if ins else {}
        outlet_s = streams.get(outs[0]) if outs else {}
        inlet = row.get("inlet") or {"stream": (ins or ["to confirm"])[0], "T_C": (inlet_s or {}).get("T_C"),
                                     "P_bar": (inlet_s or {}).get("P_bar"),
                                     "phase": "vapour" if (inlet_s or {}).get("vapour_frac", 1) >= 0.5 else "liquid"}
        outlet = row.get("outlet") or {"stream": (outs or ["to confirm"])[0], "T_C": (outlet_s or {}).get("T_C"),
                                       "P_bar": (outlet_s or {}).get("P_bar"),
                                       "phase": "vapour" if (outlet_s or {}).get("vapour_frac", 1) >= 0.5 else "liquid"}
        missing = row.get("missing") or ["vendor curve", "mechanical design", "materials"]
        lines += [f"#### {equip['id']} {equip['type']}", "",
                  f"- Service: {row.get('service') or equip['type'] or 'to confirm'}",
                  f"- Inlet: {inlet.get('stream') or 'to confirm'}, {num(inlet.get('T_C'))} °C, {num(inlet.get('P_bar'))} bar, phase {inlet.get('phase') or 'to confirm'}",
                  f"- Outlet: {outlet.get('stream') or 'to confirm'}, {num(outlet.get('T_C'))} °C, {num(outlet.get('P_bar'))} bar, phase {outlet.get('phase') or 'to confirm'}",
                  f"- Operating flow: {num(row.get('flow'))} {row.get('flow_unit') or ''}".rstrip(),
                  f"- Pressure ratio: {num(row.get('pressure_ratio'))}; head: {num(row.get('head'))} {row.get('head_unit') or ''}".rstrip(),
                  f"- Calculated duty: {num(row.get('shaft'))} {row.get('shaft_unit') or ''}".rstrip(),
                  f"- Assumed efficiency: {num(row.get('efficiency_pct'))} %",
                  f"- Provisional rating: {num(row.get('rating_flow'))} {row.get('rating_flow_unit') or ''} / {num(row.get('rating_shaft'))} {row.get('rating_shaft_unit') or ''}".rstrip(),
                  f"- Rating source: {row.get('rating_source') or equip.get('rating_source') or raw.get('rating_source') or 'to confirm'}",
                  f"- Missing vendor information: {', '.join(missing)} — to confirm",
                  f"- Status: {row.get('status') or equip.get('status') or 'new equipment, rating to confirm'}", ""]
    return "\n".join(lines)
