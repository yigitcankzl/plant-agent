"""Rev B: the proposed P&ID sheet, re-issued with the verified changes drawn in.

Generic over any case SVG whose equipment sits in `<g data-tag>` groups (DEXPI renders and the generated sheets alike):

- a new unit that runs in parallel with an existing one is drawn as a symbol at a free spot beside it, tied into the
  existing inlet and outlet lines with tees and routed orthogonal lines (the reroutes of that change are the tees);
- a changed design or operating value is written in a callout next to the equipment or line it acts on, with the
  new design data and a leader line;
- every revision gets a revision cloud and a numbered triangle; a revision block (Rev A existing / Rev B proposed,
  DRAFT - NOT APPROVED) is added under the title block by extending the sheet.

Free space is found on an occupancy grid built from the drawing's own geometry (transforms included), so nothing is
placed on top of existing linework or text when there is room. The case SVG file is only read.
"""
import math
import re
import time
import xml.etree.ElementTree as ET

from .plant import FIELD, KIND, ROUTING_UNITS
from .proposed import _index, _neighbor, _parallel, _path_points, esc, ports, topology_units

CELL = 1.5
CLOUD = "#c62828"
INK = "#17383d"
NOTE = "#0b4f66"
SVGNS = "http://www.w3.org/2000/svg"
SHORT = {"U_W_m2K": "U", "m3_h": "flow", "kg_h": "flow", "volume_m3": "working volume", "area_m2": "area",
         "P_out_bar": "discharge pressure", "T_out_C": "outlet temperature", "T_C": "temperature", "P_bar": "pressure",
         "duty_kW": "duty", "eff_pct": "efficiency", "dP_bar": "pressure rise/drop", "fractions": "split"}
HALF = {"compressor": 8, "pump": 6, "hx": 10, "cooler": 10, "heater": 10}


# ---------------------------------------------------------------- geometry of the existing sheet

def _mul(a, b):
    return (a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1], a[0] * b[2] + a[2] * b[3],
            a[1] * b[2] + a[3] * b[3], a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5])


def _transform(text):
    m = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", text or ""):
        v = [float(x) for x in re.findall(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?", args)]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            a = math.radians(v[0])
            c, s = math.cos(a), math.sin(a)
            t = (c, s, -s, c, 0, 0)
            if len(v) == 3:
                t = _mul(_mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "matrix" and len(v) == 6:
            t = tuple(v)
        else:
            continue
        m = _mul(m, t)
    return m


def _apply(m, p):
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def _local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else ""


def _f(el, k, d=0.0):
    try:
        return float(re.sub(r"[a-z%]+$", "", el.get(k) or "") or d)
    except ValueError:
        return d


def _segments(el):
    """Polyline pieces of a drawing primitive in its own coordinates (closed shapes as outlines)."""
    tag = _local(el.tag)
    if tag == "rect":
        x, y, w, h = _f(el, "x"), _f(el, "y"), _f(el, "width"), _f(el, "height")
        return [[(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]]
    if tag in ("circle", "ellipse"):
        cx, cy = _f(el, "cx"), _f(el, "cy")
        rx = _f(el, "r") if tag == "circle" else _f(el, "rx")
        ry = _f(el, "r") if tag == "circle" else _f(el, "ry")
        return [[(cx + rx * math.cos(a / 8 * math.pi), cy + ry * math.sin(a / 8 * math.pi)) for a in range(17)]]
    if tag == "line":
        return [[(_f(el, "x1"), _f(el, "y1")), (_f(el, "x2"), _f(el, "y2"))]]
    if tag in ("polyline", "polygon"):
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?", el.get("points") or "")]
        pts = list(zip(nums[0::2], nums[1::2]))
        return [pts + pts[:1] if tag == "polygon" else pts]
    if tag == "path":
        return [_path_points(el.get("d") or "")]
    return []


def _text_box(el, m):
    text = "".join(el.itertext()).strip()
    if not text:
        return None
    fs = _f(el, "font-size", 3.0) or 3.0
    x, y = _f(el, "x"), _f(el, "y")
    dy = el.get("dy") or ""
    if dy.endswith("em"):
        y += float(dy[:-2] or 0) * fs
    w = len(text) * fs * 0.55
    anchor = el.get("text-anchor") or "start"
    x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    corners = [_apply(m, p) for p in ((x0, y - fs * 0.8), (x0 + w, y - fs * 0.8), (x0, y + fs * 0.2), (x0 + w, y + fs * 0.2))]
    return (min(p[0] for p in corners), min(p[1] for p in corners), max(p[0] for p in corners), max(p[1] for p in corners))


class Sheet:
    """Equipment boxes, piping lines and an occupancy grid of an existing SVG sheet."""

    def __init__(self, svg):
        self.root = ET.fromstring(svg)
        vb = [float(v) for v in (self.root.get("viewBox") or "0 0 420 297").replace(",", " ").split()]
        self.vb = vb
        self.occ = set()
        self.boxes, self.lines, self.texts = {}, [], []
        self._walk(self.root, (1, 0, 0, 1, 0, 0), None, None)
        for box in self.boxes.values():  # nothing is routed or written through (or tight against) a symbol
            self.mark_box((box[0] - 2.5, box[1] - 2.5, box[2] + 2.5, box[3] + 2.5))

    def _mark_seg(self, a, b):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (CELL / 2)))
        for i in range(n + 1):
            t = i / n
            self.occ.add((int((a[0] + (b[0] - a[0]) * t) // CELL), int((a[1] + (b[1] - a[1]) * t) // CELL)))

    def mark_box(self, box):
        for i in range(int(box[0] // CELL), int(box[2] // CELL) + 1):
            for j in range(int(box[1] // CELL), int(box[3] // CELL) + 1):
                self.occ.add((i, j))

    def mark_path(self, pts):
        for a, b in zip(pts, pts[1:]):
            self._mark_seg(a, b)

    def count(self, box, pad=1.0):
        return sum((i, j) in self.occ for i in range(int((box[0] - pad) // CELL), int((box[2] + pad) // CELL) + 1)
                   for j in range(int((box[1] - pad) // CELL), int((box[3] + pad) // CELL) + 1))

    def _walk(self, el, m, tag, line):
        name = _local(el.tag)
        if name in ("defs", "marker", "metadata", "title", "style"):
            return
        m = _mul(m, _transform(el.get("transform"))) if el.get("transform") else m
        if name == "g":
            if el.get("data-tag"):
                tag = el.get("data-tag")
            elif "label" in (el.get("class") or ""):
                tag = None  # DEXPI tag/bar labels and data tables are not the symbol
            if el.get("data-line"):
                line = {"line": el.get("data-line"), "from": el.get("data-from") or "", "to": el.get("data-to") or "",
                        "points": [], "stroke": None, "width": None}
                self.lines.append(line)
        if name == "text":
            box = _text_box(el, m)
            if box:
                self.mark_box(box)
                self.texts.append(("".join(el.itertext()).strip(), box, line["line"] if line else None))
            return
        if name == "g" and line is not None and el.get("transform"):  # an inline valve/instrument symbol on a line
            p = _apply(m, (0, 0))
            items = line.setdefault("items", [])
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 0.5 for q in items):
                items.append(p)
        if name == "rect" and _f(el, "width") * _f(el, "height") > 0.5 * self.vb[2] * self.vb[3]:
            return  # the sheet background
        for seg in _segments(el):
            pts = [_apply(m, p) for p in seg]
            self.mark_path(pts)
            if name in ("rect", "circle", "ellipse") and _f(el, "width", 0) * _f(el, "height", 0) < 900:
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                self.mark_box((min(xs), min(ys), max(xs), max(ys)))
            if tag and pts:
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                b = self.boxes.get(tag)
                self.boxes[tag] = (min(xs + ([b[0]] if b else [])), min(ys + ([b[1]] if b else [])),
                                   max(xs + ([b[2]] if b else [])), max(ys + ([b[3]] if b else [])))
            if line is not None and name in ("polyline", "line") and _length(pts) > _length(line["points"]):
                line["points"], line["stroke"], line["width"] = pts, el.get("stroke"), el.get("stroke-width")
        for child in el:
            self._walk(child, m, tag, line)

    def center(self, tag):
        b = self.boxes.get(tag)
        return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else None

    def inside(self, box, margin=8):
        x, y, w, h = self.vb
        return box[0] >= x + margin and box[1] >= y + margin and box[2] <= x + w - margin and box[3] <= y + h - margin


# ---------------------------------------------------------------- small helpers

def _num(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        a = abs(v)
        if a >= 10000:
            return f"{v:,.0f}"
        if a >= 1000:
            return f"{v:.0f}"
        if a >= 100:
            return f"{v:.1f}".rstrip("0").rstrip(".")  # 4 significant digits
        if a >= 10:
            return f"{v:.1f}".rstrip("0").rstrip(".")
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def qty(v, unit):
    """Rounded quantity with its unit; kg/h and kW above 1000 are shown as t/h and MW."""
    unit = {"m2": "m²", "m3": "m³", "m3/h": "m³/h", "C": "°C"}.get(unit, unit)
    if isinstance(v, (int, float)) and unit == "kg/h" and abs(v) >= 1000:
        return f"{_num(v / 1000)} t/h"
    if isinstance(v, (int, float)) and unit == "kW" and abs(v) >= 1000:
        return f"{_num(v / 1000)} MW"
    return f"{_num(v)} {unit}".strip()


def value_text(change, names):
    """'U 2,000 → 2,500 W/m²K' for a path change."""
    kind, oid, field = change["path"].split(".", 2)
    unit = FIELD.get(field, ("", ""))[1]
    frm, to = change.get("from"), change.get("value")
    if field == "fractions" and isinstance(to, list):
        pct = lambda v: f"{v[0] * 100:.1f}" if isinstance(v, list) and v else "?"  # noqa: E731
        return f"share of flow to this line {pct(frm) + ' → ' if frm is not None else ''}{pct(to)} %"
    label = SHORT.get(field, field.replace("_", " "))
    if kind == "feeds":
        who = re.sub(r"\s+(to|from)\s+\S+$", "", names.get(oid, oid))
        label = f"{who} {label}" if who != oid else label
    return f"{label} {_num(frm) + ' → ' if frm is not None else ''}{_num(to)} {unit}".strip()


def _short(text, n=46):
    text = re.split(r"[;(]", str(text or ""))[0].strip()
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def _owner(spec, change):
    kind, oid, _ = change["path"].split(".", 2)
    if kind == "units":
        return oid
    for u in spec.get("units") or []:
        ins, _ = ports(u)
        if oid in ins:
            return u["id"]
    return oid


def _cloud_rect(box, step=6.0):
    """Revision cloud along a rectangle: outward arcs of about `step` units."""
    x0, y0, x1, y1 = box
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    d = [f"M{x0:.1f},{y0:.1f}"]
    for (ax, ay), (bx, by) in zip(corners, corners[1:]):
        n = max(1, round(math.hypot(bx - ax, by - ay) / step))
        for i in range(n):
            px, py = ax + (bx - ax) * (i + 1) / n, ay + (by - ay) * (i + 1) / n
            r = math.hypot(bx - ax, by - ay) / n / 2
            d.append(f"A{r:.2f},{r:.2f} 0 0,1 {px:.1f},{py:.1f}")
    return " ".join(d)


def _triangle(x, y, n, k=1.0):
    """Revision triangle centred on (x, y) with the revision number; k scales it."""
    return (f'<g data-rev-triangle="{n}"><polygon points="{x:.1f},{y - 4.2 * k:.1f} {x + 4.6 * k:.1f},{y + 3 * k:.1f} '
            f'{x - 4.6 * k:.1f},{y + 3 * k:.1f}" fill="#fff" stroke="{CLOUD}" stroke-width="0.6"/><text x="{x:.1f}" y="{y + 2 * k:.1f}" '
            f'text-anchor="middle" font-size="{3.4 * k:.2f}" font-weight="700" fill="{CLOUD}" font-family="Arial,sans-serif">{n}</text></g>')


def _symbol(kind, flip=False):
    """New equipment in the sheet's own line style, drawn around a local origin (flow left to right)."""
    s = {"compressor": '<path d="M-8,-7 L8,-4 V4 L-8,7 Z"/><circle cx="-1" r="2" fill="none" stroke-width="0.45"/>'
                       '<path d="M-1,-2 L4,-4 M-1,2 L4,4" fill="none" stroke-width="0.45"/>',
         "pump": '<circle r="6"/><path d="M-3,-3 L4,0 L-3,3 Z" fill="#dbe9e7"/>',
         "hx": '<rect x="-10" y="-6" width="20" height="12" rx="5"/><path d="M-9,-2 H9 M-9,2 H9" fill="none" stroke-width="0.4"/>'}
    body = s.get(kind) or s.get({"cooler": "hx", "heater": "hx"}.get(kind, ""), '<rect x="-8" y="-6" width="16" height="12" rx="1"/>')
    return f'<g transform="scale(-1,1)">{body}</g>' if flip else body


def _along(points, dist, from_end):
    """Point at arc distance `dist` along a polyline (from its end or its start), with the segment direction."""
    pts = list(reversed(points)) if from_end else list(points)
    left = dist
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L and left <= L:
            t = left / L
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        left -= L
    return None


def _length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def _routes(a, b):
    if abs(a[0] - b[0]) < 0.5 or abs(a[1] - b[1]) < 0.5:
        return [[a, b]]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return [[a, (b[0], a[1]), b], [a, (a[0], b[1]), b], [a, (mx, a[1]), (mx, b[1]), b], [a, (a[0], my), (b[0], my), b]]


def _route_cost(sheet, pts, ends):
    cost = 0
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (CELL / 2)))
        seen = set()
        for i in range(n + 1):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            if any(math.hypot(p[0] - e[0], p[1] - e[1]) < 2.5 for e in ends):
                continue
            c = (int(p[0] // CELL), int(p[1] // CELL))
            if c not in seen:
                seen.add(c)
                cost += c in sheet.occ
    return cost * 4 + _length(pts) * 0.05 + (len(pts) - 2) * 1.5


def _best_route(sheet, a, b, ends=None):
    return min(_routes(a, b), key=lambda pts: _route_cost(sheet, pts, ends or [a, b]))


def _union(boxes):
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _clusters(boxes, gap=14):
    """Merge boxes that lie within `gap` of each other; returns the merged boxes."""
    out = [b for b in boxes if b]
    merged = True
    while merged:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                if _overlap(out[i], out[j], gap):
                    out[i] = _union([out[i], out.pop(j)])
                    merged = True
                    break
            if merged:
                break
    return out


def _grow(box, d):
    return (box[0] - d, box[1] - d, box[2] + d, box[3] + d)


# ---------------------------------------------------------------- placing the changes

def _place_callout(sheet, anchor_boxes, lines, taken, avoid=(), fs=2.5):
    """A free spot for a text callout near one of the anchor boxes; returns (anchor box, callout box)."""
    w = max(len(t) for t in lines) * fs * 0.56 + 3
    h = len(lines) * fs * 1.3 + 2
    best = None
    for anchor_box in anchor_boxes:
        cx, cy = (anchor_box[0] + anchor_box[2]) / 2, (anchor_box[1] + anchor_box[3]) / 2
        for dx in range(-96, 97, 4):
            for dy in range(-72, 73, 4):
                x0, y0 = cx + dx - w / 2, cy + dy - h / 2
                box = (x0, y0, x0 + w, y0 + h)
                if not sheet.inside(box, 10) or any(_overlap(box, t, 2) for t in taken) or _overlap(box, anchor_box, 1) \
                        or any(_overlap(box, t, 1) for t in avoid):
                    continue
                score = sheet.count(box, 1.5) * 30 + math.hypot(dx, dy) * 0.2
                if best is None or score < best[0]:
                    best = (score, anchor_box, box)
    return best[1:] if best else (None, None)


def _overlap(a, b, pad=0):
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])


def _leader(box, target):
    """Leader from the callout edge to the nearest point of the anchor box."""
    tx = min(max((box[0] + box[2]) / 2, target[0]), target[2])
    ty = min(max((box[1] + box[3]) / 2, target[1]), target[3])
    sx = min(max(tx, box[0]), box[2])
    sy = min(max(ty, box[1]), box[3])
    return (sx, sy), (tx, ty)


def _callout_svg(box, lines, rev, fs=2.5):
    x0, y0, x1, y1 = box
    out = [f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="#fff" stroke="{NOTE}" stroke-width="0.35"/>']
    for i, t in enumerate(lines):
        weight = ' font-weight="700"' if i == 0 else ""
        out.append(f'<text x="{x0 + 1.5:.1f}" y="{y0 + 1 + fs * (i + 1) * 1.3 - fs * 0.3:.1f}" font-size="{fs}"{weight} '
                   f'fill="{INK if i == 0 else NOTE}" font-family="Arial,sans-serif">{esc(t)}</text>')
    return "".join(out)


def _line_of(sheet, stream_ids):
    """Drawing line whose number is part of a model stream id (S3101 -> line 3101)."""
    for sid in stream_ids:
        for ln in sheet.lines:
            if ln["line"] and ln["points"] and re.search(rf"(?<!\d){re.escape(ln['line'])}(?!\d)", str(sid)):
                return ln
    return None


def _anchor(sheet, spec, change, proposal, names):
    """Where a value change is written: the drawn tag named in its physical description, the unit it acts on, the line
    of the stream it changes, then the equipment the proposal fixes."""
    drawn = set(sheet.boxes)
    text = str(change.get("physical_change") or "")
    for tag in sorted(drawn, key=lambda t: (text.find(t) if t in text else 1e9)):
        if tag and re.search(rf"(?<![\w-]){re.escape(tag)}(?![\w-])", text):
            return tag, [sheet.boxes[tag]]
    owner = _owner(spec, change)
    if owner in drawn:
        return owner, [sheet.boxes[owner]]
    kind, oid, field = change["path"].split(".", 2)
    unit = next((u for u in spec.get("units") or [] if u.get("id") == oid), None)
    streams = ports(unit)[1] if unit and field == "fractions" else [oid]
    ln = _line_of(sheet, streams)
    if ln:
        xs, ys = [p[0] for p in ln["points"]], [p[1] for p in ln["points"]]
        mid = _along(ln["points"], _length(ln["points"]) / 2, False) or (xs[0], ys[0])
        L = _length(ln["points"])
        pts = [p for p in (_along(ln["points"], L * f, False) for f in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9)) if p]
        return f"line {ln['line']}", [(p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2) for p in pts]
    for t in (proposal.get("fixes"), proposal.get("tag")):
        if t in drawn:
            return t, [sheet.boxes[t]]
    by_id, prod, cons = _index(spec.get("units") or [])
    for fwd in (True, False):
        hit = _neighbor(owner, fwd, by_id, prod, cons, {t: sheet.center(t) for t in drawn})
        if hit:
            return hit, [sheet.boxes[hit]]
    return None, None


def _parallel_plan(sheet, item, uid, kind):
    """Symbol spot, tees on the existing inlet/outlet lines and routed branch lines for a parallel unit."""
    partner = item["partner"]
    pbox = sheet.boxes[partner]
    pc = sheet.center(partner)
    up, down = item.get("upstream"), item.get("downstream")
    ins = [ln for ln in sheet.lines if ln["to"] == partner and ln["points"]]
    outs = [ln for ln in sheet.lines if ln["from"] == partner and ln["points"]]
    lin = next((ln for ln in ins if ln["from"] == up), ins[0] if ins else None)
    lout = next((ln for ln in outs if ln["to"] == down), outs[0] if outs else None)
    if lin and lout:
        axis = _flow_axis(lin["points"][-1], lout["points"][0])
    else:
        target = sheet.center(down) if down in sheet.boxes else None
        axis = _flow_axis(pc, target) if target else (1.0, 0.0)
    perp = [(-axis[1], axis[0]), (axis[1], -axis[0])]
    hw = HALF.get(kind, 8)
    best = None
    for px, py in perp:
        for off in (26, 30, 34, 38, 44, 50, 58):
            c = (pc[0] + px * off, pc[1] + py * off)
            sym = (c[0] - hw - 2, c[1] - 8, c[0] + hw + 2, c[1] + 8)
            label = (c[0] - 12, c[1] - 26, c[0] + 40, c[1] - 9) if py <= 0 else (c[0] - 12, c[1] + 9, c[0] + 40, c[1] + 26)
            if not sheet.inside(_union([sym, label]), 14):
                continue
            score = sheet.count(sym, 3) * 10 + sheet.count(label, 1) * 3 + off * 0.3
            if best is None or score < best[0]:
                best = (score, c)
    if not best:
        return None
    c = best[1]
    n_in, n_out = (c[0] - axis[0] * hw, c[1] - axis[1] * hw), (c[0] + axis[0] * hw, c[1] + axis[1] * hw)
    keep_out = _grow(pbox, 4)

    def tee(line, from_end, nozzle):
        if not line:
            p = (pc[0] - axis[0] * (hw + 10), pc[1] - axis[1] * (hw + 10)) if from_end else \
                (pc[0] + axis[0] * (hw + 10), pc[1] + axis[1] * (hw + 10))
            return p, _best_route(sheet, p, nozzle) if from_end else _best_route(sheet, nozzle, p), None
        L = _length(line["points"])
        options = []
        for d in range(6, int(min(L - 3, 70)) + 1, 2):
            p = _along(line["points"], d, from_end)
            if not p or (keep_out[0] <= p[0] <= keep_out[2] and keep_out[1] <= p[1] <= keep_out[3]):
                continue
            route = _best_route(sheet, p, nozzle) if from_end else _best_route(sheet, nozzle, p)
            options.append((_route_cost(sheet, route, [p, nozzle]) + d * 0.05, p, route))
        if not options:
            return None
        _, p, route = min(options, key=lambda o: o[0])
        return p, route, line
    t_in, t_out = tee(lin, True, n_in), tee(lout, False, n_out)
    if not t_in or not t_out:
        return None
    return {"at": c, "axis": axis, "tee_in": t_in, "tee_out": t_out, "flip": axis[0] < 0}


def _line_label(sheet, pts, label, fs):
    """Horizontal line-number label beside the freest stretch of a new line."""
    w, h = len(label) * fs * 0.56 + 1, fs * 1.3
    best = None
    for a, b in zip(pts, pts[1:]):
        for t in (0.25, 0.5, 0.75):
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            vertical = abs(a[0] - b[0]) < 0.5
            spots = [(px + 1.2, py - h / 2), (px - w - 1.2, py - h / 2)] if vertical else [(px - w / 2, py - h - 0.6), (px - w / 2, py + 0.6)]
            for x0, y0 in spots:
                box = (x0, y0, x0 + w, y0 + h)
                score = sheet.count(box, 0.3)
                if best is None or score < best[0]:
                    best = (score, box)
    box = best[1]
    return box[0] + 0.5, box[3] - fs * 0.35, box


def _parallel_any(uid, by_id, prod, cons, existing_ids):
    """A new unit fed by a splitter and discharging into a mixer (new or existing) that an existing unit also feeds from
    the same splitter: drawn parallel to that unit."""
    unit = by_id.get(uid)
    if not unit:
        return None
    ins, outs = ports(unit)
    if len(ins) != 1 or len(outs) != 1:
        return None
    splitter, mixer = prod.get(ins[0]), (cons.get(outs[0]) or [None])[0]
    if by_id.get(splitter, {}).get("type") != "splitter" or by_id.get(mixer, {}).get("type") != "mixer":
        return None
    for stream in ports(by_id[splitter])[1]:
        for partner in cons.get(stream) or []:
            if partner == uid or partner not in existing_ids:
                continue
            p_out = next((s for s in ports(by_id[partner])[1] if mixer in (cons.get(s) or [])), None)
            if p_out:
                return {"splitter": splitter, "mixer": mixer, "partner": partner, "in_stream": ins[0], "out_stream": outs[0],
                        "mixer_out": (ports(by_id[mixer])[1] or [None])[0], "partner_out": p_out,
                        "split_in": (ports(by_id[splitter])[0] or [None])[0]}
    return None


def _note_anchors(sheet, where):
    """Anchor boxes for a free note at a tag, an inline item ('3003/C1', 'PSV-202', 'FV-301') or a line number; falls back
    to the nearest match by token. Returns (anchors, resolved label)."""
    w = re.sub(r"^line\s*", "", where.strip(), flags=re.I)
    if not w:
        return [], where
    box = lambda p, d=2: (p[0] - d, p[1] - d, p[0] + d, p[1] + d)  # noqa: E731
    if w in sheet.boxes:
        return [sheet.boxes[w]], w
    exact = [t for t in sheet.texts if t[0].lower() == w.lower()]
    if exact:
        return [exact[0][1]], w

    def line_of(num):
        return next((ln for ln in sheet.lines if ln["points"] and ln["line"] and
                     (ln["line"] == num or ln["line"].split("-")[0] == num)), None)

    head, _, item = w.partition("/")
    ln = line_of(head) or line_of(re.split(r"[-\s]", head)[0])
    if ln:
        if item and ln.get("items"):  # the inline item on that line (valve 'C1' on line 3003)
            named = [t for t in sheet.texts if t[2] == ln["line"] and t[0].lower() == item.lower()]
            return ([named[0][1]] if named else [box(p) for p in ln["items"]]), f"{ln['line']}/{item}"
        L = _length(ln["points"])
        return [box(p) for p in (_along(ln["points"], L * f, False) for f in (0.2, 0.4, 0.6, 0.8)) if p], f"line {ln['line']}"
    for tok in re.findall(r"[A-Za-z]+-?\d+[A-Za-z0-9.]*|\d{3,}", w):  # nearest: any token that is on the sheet
        if tok in sheet.boxes:
            return [sheet.boxes[tok]], tok
        hit = next((t for t in sheet.texts if t[0].lower() == tok.lower() or t[0].lower().startswith(tok.lower() + "-")), None)
        if hit:
            return [hit[1]], tok
        ln = line_of(tok)
        if ln:
            return [box(_along(ln["points"], _length(ln["points"]) / 2, False))], f"line {ln['line']}"
    tag = next((t for t in sheet.boxes if t and (t in w or w in t)), None)
    if tag:
        return [sheet.boxes[tag]], tag
    return [], where


def _flow_axis(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) >= abs(dy):
        return (1.0 if dx >= 0 else -1.0, 0.0)
    return (0.0, 1.0 if dy >= 0 else -1.0)


def _duty(calculation, uid):
    rows = [r for r in (calculation or {}).get("checks") or [] if r.get("id") == uid and r.get("value") is not None]
    return ", ".join(qty(r["value"], r.get("unit") or "") for r in rows[:2])


def _rating(limits):
    bits = []
    if limits.get("max_kg_h") is not None:
        bits.append(qty(limits["max_kg_h"], "kg/h") + " suction")
    if limits.get("max_m3_h") is not None:
        bits.append(qty(limits["max_m3_h"], "m³/h"))
    if limits.get("max_kW") is not None:
        bits.append(qty(limits["max_kW"], "kW") + " shaft")
    if limits.get("area_m2") is not None:
        bits.append(qty(limits["area_m2"], "m²"))
    return " / ".join(bits) or "to confirm"


def _source(text):
    t = re.split(r"\s+/\s+|\s+-\s+", str(text or "to confirm"))[0].strip()
    return t if len(t) <= 52 else t[:51] + "…"


# ---------------------------------------------------------------- the sheet

def generate(svg, spec, revisions, names=None, meta=None):
    """Return {'svg', 'revisions': [{rev, title, where, drawn}], 'unplaced': [...], 'clouds': n}.

    revisions: [{'rev': n, 'title', 'changes': [...], 'calculation': {...} | None, 'fixes'/'tag': drawn tag | None}]
    spec: the model the changes apply to (existing plant). names: display names. meta: {'title', 'date', 'drawing'}.
    """
    names = names or {}
    meta = meta or {}
    sheet = Sheet(svg)
    parts, clouds, unplaced, report = [], [], [], []
    markers = {}
    taken, cloud_boxes = [], []

    def marker(colour):
        key = re.sub(r"[^0-9a-zA-Z]", "", colour or "k")
        markers[key] = colour or "#000"
        return f"url(#revb-arr-{key})"

    for rev in revisions:
        n = rev["rev"]
        changes = rev.get("changes") or []
        boxes, drawn = [], []
        try:
            units, existing_ids, added_ids = topology_units(spec, changes)
        except ValueError:
            units, existing_ids, added_ids = list(spec.get("units") or []), set(), set()
        by_id, prod, cons = _index(units)
        centers = {t: sheet.center(t) for t in sheet.boxes}
        rerouted = {c["reroute"]["unit"] for c in changes if isinstance(c.get("reroute"), dict)}
        handled_reroutes = set()
        for c in changes:
            add = c.get("add_unit")
            if not isinstance(add, dict) or add.get("type") in ROUTING_UNITS:
                continue
            uid, kind = add["id"], add.get("type")
            info = _parallel(uid, by_id, prod, cons, existing_ids, added_ids) or _parallel_any(uid, by_id, prod, cons, existing_ids)
            plan = None
            if info and info["partner"] in sheet.boxes:
                info["upstream"] = _neighbor(info["splitter"], False, by_id, prod, cons, centers)
                info["downstream"] = _neighbor(info["mixer"], True, by_id, prod, cons, centers)
                plan = _parallel_plan(sheet, info, uid, kind)
            if not plan:
                unplaced.append(uid)
                continue
            (tin, rin, lin), (tout, rout, lout) = plan["tee_in"], plan["tee_out"]
            x, y = plan["at"]
            g = [f'<g data-rev="{n}" class="revb-new">']
            limits = c.get("limits") or {}
            title = f"{uid} (NEW)"
            sub = f"Parallel {KIND.get(kind, kind)} to {info['partner']}"
            lines = [f"Rating {_rating(limits)}", f"Rating source: {_source(c.get('rating_source'))}"]
            duty = _duty(rev.get("calculation"), uid)
            if duty:
                lines.insert(1, f"Duty at target: {duty} (DWSIM)")
            above = plan["at"][1] <= sheet.center(info["partner"])[1]
            ty = y - 11 - 3.2 * (len(lines) + 1) if above else y + 12
            label_box = (x - 10, ty - 3.2, x - 10 + max(len(t) for t in [title, sub] + lines) * 1.35, ty + 6.4 + 3 * (len(lines) - 1) + 0.8)
            sym_box = (x - 10, y - 8, x + 10, y + 8)
            sheet.boxes[uid] = sym_box
            sheet.mark_box(sym_box)
            sheet.mark_box(label_box)
            taken.append(label_box)
            for pts, line, stream in ((rin, lin, info["in_stream"]), (rout, lout, info["out_stream"])):
                colour = (line or {}).get("stroke") or INK
                width = (line or {}).get("width") or "0.9"
                g.append(f'<g data-line="{esc(stream)}" data-from="{esc(info["splitter"] if pts is rin else uid)}" '
                         f'data-to="{esc(uid if pts is rin else info["mixer"])}" data-new="true">'
                         f'<polyline points="{" ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)}" fill="none" stroke="{colour}" '
                         f'stroke-width="{width}" stroke-linejoin="round" marker-end="{marker(colour)}"/>')
                label = f"{stream} (new)"
                lx, ly, lbox = _line_label(sheet, pts, label, 2.2)
                g.append(f'<rect x="{lbox[0]:.1f}" y="{lbox[1]:.1f}" width="{lbox[2] - lbox[0]:.1f}" height="{lbox[3] - lbox[1]:.1f}" fill="#fff" '
                         f'fill-opacity="0.85" stroke="none"/><text x="{lx:.1f}" y="{ly:.1f}" font-size="2.2" font-weight="700" fill="{colour}" '
                         f'font-family="Arial,sans-serif">{esc(label)}</text></g>')
                sheet.mark_box(lbox)
                sheet.mark_path(pts)
            for p, tee_id in ((tin, info["splitter"]), (tout, info["mixer"])):
                g.append(f'<g data-tag="{esc(tee_id)}" data-new="true" data-name="tie-in tee ({esc(KIND.get(by_id.get(tee_id, {}).get("type"), "tee"))})">'
                         f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="1.1" fill="{INK}" stroke="none"/></g>')
            g.append(f'<g data-tag="{esc(uid)}" data-pid="{esc(uid)}" data-new="true" data-name="{esc(sub)}" fill="#fff" stroke="{INK}" stroke-width="0.7">'
                     f'<g transform="translate({x:.1f},{y:.1f})">{_symbol(kind, plan["flip"])}</g>'
                     f'<text x="{x - 10:.1f}" y="{ty:.1f}" font-size="3.2" font-weight="700" stroke="none" fill="{INK}" font-family="Arial,sans-serif">{esc(title)}</text>'
                     f'<text x="{x - 10:.1f}" y="{ty + 3.3:.1f}" font-size="2.4" stroke="none" fill="#526b6c" font-family="Arial,sans-serif">{esc(sub)}</text>'
                     + "".join(f'<text x="{x - 10:.1f}" y="{ty + 6.4 + 3 * i:.1f}" font-size="2.3" stroke="none" fill="{NOTE}" '
                               f'font-family="Arial,sans-serif">{esc(t)}</text>' for i, t in enumerate(lines)) + "</g>")
            g.append("</g>")
            boxes += [sym_box, label_box, (tin[0] - 2, tin[1] - 2, tin[0] + 2, tin[1] + 2),
                      (tout[0] - 2, tout[1] - 2, tout[0] + 2, tout[1] + 2)]
            boxes += [(min(p[0] for p in r), min(p[1] for p in r), max(p[0] for p in r), max(p[1] for p in r)) for r in (rin, rout)]
            parts.append("".join(g))
            handled_reroutes |= rerouted  # the tie-in tees are the reroutes of a parallel addition
            drawn.append(f"{uid} drawn parallel to {info['partner']} with tie-ins on the existing lines")
        for c in changes:
            if not c.get("path"):
                continue
            tag, anchors = _anchor(sheet, spec, c, rev, names)
            if not anchors:
                unplaced.append(c["path"])
                continue
            lines = [f"{tag}: Rev B design data" if not tag.startswith("line") else f"{tag[0].upper()}{tag[1:]}: Rev B",
                     value_text(c, names)]
            what = c.get("physical_change")
            if what:
                lines.append(_short(what))
            abox, box = _place_callout(sheet, anchors, lines, taken, cloud_boxes)
            if not box:
                unplaced.append(c["path"])
                continue
            a, b = _leader(box, abox)
            parts.append(f'<g data-rev="{n}" class="revb-note" pointer-events="none">'
                         f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{NOTE}" stroke-width="0.35"/>'
                         f'<circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="0.6" fill="{NOTE}"/>{_callout_svg(box, lines, n)}</g>')
            sheet.mark_box(box)
            taken.append(box)
            boxes.append(_union([box, abox]))  # callout, leader and anchor stay in one cloud
            drawn.append(f"{tag}: {value_text(c, names)}")
        for c in changes:
            r = c.get("reroute")
            if isinstance(r, dict) and r["unit"] not in handled_reroutes:
                ln = next((ln for ln in sheet.lines if r["unit"] in (ln["from"], ln["to"]) and ln["points"]), None)
                if ln:
                    xs, ys = [p[0] for p in ln["points"]], [p[1] for p in ln["points"]]
                    boxes.append((min(xs), min(ys), max(xs), max(ys)))
                    drawn.append(f"line {ln['line']} rerouted ({r['field']} of {r['unit']})")
                else:
                    unplaced.append(f"reroute of {r['unit']}")
        for note in rev.get("notes") or []:  # free notes an engineer asked for, e.g. "bypass to be added here"
            where = str(note.get("tag") or note.get("line") or "").strip()
            text = str(note.get("text") or "").strip()
            anchors, label = _note_anchors(sheet, where)
            if not anchors and text:  # nothing on the sheet matches: the note goes in free space and says so
                x, y, w_, h_ = sheet.vb
                anchors, label = [(x + w_ / 2 - 2, y + h_ / 2 - 2, x + w_ / 2 + 2, y + h_ / 2 + 2)], f"{where}: not found on the sheet"
            if not text:
                continue
            words, lines, cur = text.split(), [f"NOTE ({label})"], ""
            for wd in words:
                if len(cur) + len(wd) + 1 > 46 and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = f"{cur} {wd}".strip()
            lines.append(cur)
            abox, box = _place_callout(sheet, anchors, lines[:5], taken, cloud_boxes)
            if not box:
                unplaced.append(f"note at {where}")
                continue
            a, b = _leader(box, abox)
            parts.append(f'<g data-rev="{n}" data-note="{esc(where)}" class="revb-note" pointer-events="none">'
                         f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{NOTE}" stroke-width="0.35"/>'
                         f'<circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="0.6" fill="{NOTE}"/>{_callout_svg(box, lines[:5], n)}</g>')
            sheet.mark_box(box)
            taken.append(box)
            boxes.append(_union([box, abox]))  # callout, leader and anchor stay in one cloud
            drawn.append(f"note at {where}: {_short(text, 60)}")
        for cb in _clusters(boxes):  # one cloud per changed area; a revision acting in two places gets two clouds
            cb = _grow(cb, 3)
            clouds.append(cb)
            cloud_boxes.append(cb)
            parts.append(f'<g data-rev-cloud="{n}" pointer-events="none"><path d="{_cloud_rect(cb)}" fill="none" stroke="{CLOUD}" '
                         f'stroke-width="0.55"/>{_triangle(cb[2] + 1, cb[1] - 1, n)}</g>')
        report.append({"rev": n, "title": rev.get("title"), "drawn": drawn})

    svg_out = _issue(svg, sheet, parts, markers, revisions, report, unplaced, meta)
    return {"svg": svg_out, "revisions": report, "unplaced": unplaced, "clouds": len(clouds)}


def _issue(svg, sheet, parts, markers, revisions, report, unplaced, meta):
    """Insert the Rev B content, extend the sheet with a revision block and mark the title block Rev B."""
    x, y, w, h = sheet.vb
    rows = len(revisions)
    strip = 33 + 4.2 * rows + (4 if unplaced else 0)
    top = y + h  # the strip starts under the original sheet
    date = meta.get("date") or time.strftime("%Y-%m-%d")
    defs = "<defs>" + "".join(f'<marker id="revb-arr-{k}" markerWidth="5" markerHeight="5" refX="4.5" refY="2.5" orient="auto" '
                              f'markerUnits="userSpaceOnUse"><path d="M0,0 L5,2.5 0,5 Z" fill="{v}"/></marker>' for k, v in markers.items()) + "</defs>"
    L, R = x + 6, x + w - 6
    blk = [f'<g id="revision-block" data-revision="B" font-family="Arial,sans-serif" pointer-events="none">',
           f'<rect x="{x}" y="{top}" width="{w}" height="{strip}" fill="#fff"/>',
           f'<rect x="{L}" y="{top + 2}" width="{R - L}" height="{strip - 5}" fill="none" stroke="{INK}" stroke-width="0.6"/>',
           f'<text x="{L + 3}" y="{top + 7}" font-size="3.4" font-weight="700" fill="{INK}">REVISIONS</text>',
           f'<text x="{L + 40}" y="{top + 7}" font-size="3.4" font-weight="700" fill="{CLOUD}">REV B - DRAFT - NOT APPROVED</text>',
           f'<text x="{R - 3}" y="{top + 7}" font-size="2.5" text-anchor="end" fill="{INK}">{esc(meta.get("drawing") or "")}</text>']
    # revision table: Rev | Date | Description | By | Chk | Appr
    cols = [L + 3, L + 13, L + 33, R - 63, R - 41, R - 20]
    ty = top + 12
    blk.append(f'<path d="M{L},{top + 9} H{R} M{L},{ty + 1.2} H{R}" stroke="{INK}" stroke-width="0.3"/>')
    for cx, t in zip(cols, ("REV", "DATE", "DESCRIPTION", "BY", "CHECKED", "APPROVED")):
        blk.append(f'<text x="{cx}" y="{ty}" font-size="2.3" font-weight="700" fill="{INK}">{t}</text>')
    for i, (rev, cells) in enumerate((("A", ("as received", "Existing plant as drawn (issued for reference)", "-", "-", "-")),
                                      ("B", (date, f"Proposed: {len(revisions)} change(s) marked by clouds 1-{len(revisions)}; "
                                                   + ("verified in DWSIM at the target" if meta.get("verified", True)
                                                      else "NOT verified in DWSIM: drawing request only"), "PlantAgent", "", "")))):
        yy = ty + 3.6 * (i + 1)
        colour = CLOUD if rev == "B" else INK
        blk.append(f'<text x="{cols[0]}" y="{yy}" font-size="2.5" font-weight="700" fill="{colour}">{rev}</text>')
        for cx, t in zip(cols[1:], cells):
            blk.append(f'<text x="{cx}" y="{yy}" font-size="2.3" fill="{colour}">{esc(t)}</text>')
    yy = ty + 3.6 * 3 + 1
    blk.append(f'<path d="M{L},{yy - 2.6} H{R}" stroke="{INK}" stroke-width="0.3"/>')
    blk.append(f'<text x="{L + 3}" y="{yy + 0.8}" font-size="2.4" font-weight="700" fill="{INK}">REV B CHANGES (clouded on the sheet)</text>')
    for i, (rev, rep) in enumerate(zip(revisions, report)):
        ry = yy + 5.4 + 4.2 * i
        blk.append(_triangle(L + 6, ry - 0.9, rev["rev"], 0.62))
        detail = "; ".join(rep["drawn"])
        detail = detail if len(detail) <= 120 else detail[:119] + "…"
        blk.append(f'<text x="{L + 11}" y="{ry:.1f}" font-size="2.3" fill="{INK}"><tspan font-weight="700">{esc(_short(rev.get("title"), 70))}</tspan>'
                   f'<tspan fill="#526b6c">  {esc(detail)}</tspan></text>')
    if unplaced:
        blk.append(f'<text x="{L + 3}" y="{yy + 5.4 + 4.2 * rows}" font-size="2.3" fill="{CLOUD}">Not drawn (no free position '
                   f'found; see the decision file): {esc(", ".join(unplaced))}</text>')
    checked = "verified in DWSIM" if meta.get("verified", True) else "NOT verified in DWSIM"
    blk.append(f'<text x="{R - 3}" y="{top + strip - 5}" font-size="2.2" text-anchor="end" fill="#526b6c">Generated by PlantAgent, '
               f'{checked}, to be checked by a licensed engineer. New equipment ratings: vendor quote to confirm.</text>')
    blk.append("</g>")
    body = defs + '<g id="rev-b" data-revision="B">' + "".join(parts) + "</g>" + "".join(blk)
    out = re.sub(r"\bRev A\b", "Rev B", svg)
    nh = h + strip
    out = re.sub(r'viewBox="[^"]*"', f'viewBox="{x:g} {y:g} {w:g} {nh:g}"', out, count=1)
    m = re.search(r"<svg\b[^>]*>", out)
    tag = m.group(0)
    hm = re.search(r'\sheight="([\d.]+)"', tag)
    if hm:
        tag2 = tag.replace(hm.group(0), f' height="{float(hm.group(1)) * nh / h:g}"')
        out = out[:m.start()] + tag2 + out[m.end():]
    idx = out.rfind("</svg>")
    return out[:idx] + body + out[idx:]


# ---------------------------------------------------------------- from a workspace

def case_svg(w):
    """Path of the case's SVG P&ID, or None."""
    from pathlib import Path
    if not w.cfg.get("svg"):
        return None
    p = Path(w.cfg["svg"])
    return p if p.is_absolute() else Path(__file__).resolve().parent.parent / "cases" / w.name / w.cfg["svg"]


def sheet_for(w, base, items, verified=True):
    """Rev B of the case drawing for revision items [{rev, title, changes, calculation, fixes, tag, notes}] on `base`."""
    from .plant import display_names, patch
    path = case_svg(w)
    if not path or not path.exists():
        return None
    try:
        after = patch(base, [c for r in items for c in r.get("changes") or []])
    except ValueError:
        after = base
    names = {**display_names(after), **w.names()}
    meta = {"title": w.cfg.get("title"), "verified": verified,
            "drawing": f"{w.name} P&ID · Rev B ({'proposed' if verified else 'draft'}) · {time.strftime('%Y-%m-%d')}"}
    return generate(path.read_text(), base, items, names, meta)


def design_answer(answers):
    """The answer whose verified proposals stand for the proposed design: the latest one whose changes together reach
    the target, else the latest one with any verified proposal. Later questions and commands without proposals
    (a chart, a document) do not replace it."""
    has = [a for a in answers if any(p.get("verified") for p in a.get("proposals") or [])]
    reach = [a for a in has if (a.get("combined") or {}).get("reaches_target")]
    return (reach or has or [None])[-1]


def workspace_items(w, answer=None):
    """(base spec, revision items) for the applied change revisions or, if none, an answer's verified proposals."""
    revs = [r for r in w.revisions if r.get("kind") == "change"]
    if revs:
        return revs[0]["spec_before"], [{"rev": i + 1, "title": r.get("title"), "changes": r["changes"],
                                         "calculation": r.get("calculation")} for i, r in enumerate(revs)]
    ans = (w.answers[answer] if isinstance(answer, int) and 0 <= answer < len(w.answers) else
           design_answer(w.answers))
    props = [p for p in (ans or {}).get("proposals") or [] if p.get("verified")]
    return w.spec, [{"rev": i + 1, "title": p.get("title"), "changes": p["changes"], "calculation": p.get("calculation"),
                     "fixes": p.get("fixes"), "tag": p.get("tag")} for i, p in enumerate(props)]


def from_workspace(w, answer=None):
    """Rev B of the case drawing for the applied change revisions or, if none, an answer's verified proposals.
    Returns None when the case has no SVG drawing or nothing to draw."""
    if not w.cfg.get("svg") or not w.built:
        return None
    base, items = workspace_items(w, answer)
    return sheet_for(w, base, items) if items else None


# ---------------------------------------------------------------- agent tool: draw a revision on request

def svg_png(svg, zoom=4.0):
    """PNG bytes of an SVG sheet (pymupdf); None when it cannot be rendered."""
    try:
        import pymupdf
        doc = pymupdf.open(stream=svg.encode(), filetype="svg")
        return doc[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png")
    except Exception:  # noqa: BLE001 - the SVG is the artifact; the PNG is a convenience
        return None


def _signature(changes):
    """What a set of changes does, independent of the ids it invents for routing: changed paths and new physical units."""
    return ({c["path"] for c in changes or [] if c.get("path")} |
            {c["add_unit"]["id"] for c in changes or [] if isinstance(c.get("add_unit"), dict) and c["add_unit"].get("type") not in ROUTING_UNITS})


def select_proposals(w, changes=None, answer=None, proposals=None):
    """(verified proposals to draw, leftover changes). Proposals are picked by answer index and/or titles (or indices);
    agent-typed changes that match verified proposals are replaced by the verified ones (their topology and calculation)."""
    answers = list(getattr(w, "answers", None) or [])
    if isinstance(answer, int) and -len(answers) <= answer < len(answers):
        pool = [answers[answer]]
    else:
        pool = [a for a in [design_answer(answers)] if a]
    verified = [p for a in pool for p in a.get("proposals") or [] if p.get("verified")]
    chosen = []
    if proposals:
        for want in proposals:
            for i, p in enumerate(verified):
                hit = (isinstance(want, int) and want == i) or (isinstance(want, str) and want.strip().lower() in str(p.get("title", "")).lower())
                if hit and p not in chosen:
                    chosen.append(p)
    elif answer is not None and not changes:
        chosen = verified
    changes = list(changes or [])
    if changes and verified:
        mine = _signature(changes)
        chosen += [p for p in verified if _signature(p["changes"]) & mine and p not in chosen]
        covered = set().union(*(_signature(p["changes"]) for p in chosen)) if chosen else set()
        changes = [c for c in changes if not (c.get("path") and c["path"] in covered)]
        if covered & _signature([c for c in changes if c.get("add_unit")]):  # a verified addition replaces the re-typed topology
            changes = [c for c in changes if not (c.get("add_unit") or c.get("reroute"))]
    return chosen, changes


def render_revision(w, changes=None, annotations=None, title=None, verified=False, answer=None, proposals=None):
    """Rev B sheet on the current model: verified proposals (by answer index and/or titles; agent-typed changes that match
    them are replaced by the verified ones), any further changes (proposal format: path changes, add_unit, reroute), and
    free notes [{tag | line, text}] at a tag, a line number or an inline item such as '3003/C1' or 'PSV-202'.
    Returns {'svg', 'proposals', 'verified', ...}. Raises ValueError for a malformed change or a case without a drawing."""
    from .plant import change_errors
    if not w.cfg.get("svg") or not w.built:
        raise ValueError("this project has no SVG P&ID (or no model yet) to draw a revision on")
    chosen, changes = select_proposals(w, changes, answer, proposals)
    annotations = list(annotations or [])
    if not chosen and not changes and not annotations:
        raise ValueError("nothing to draw: give answer/proposals, changes and/or annotations")
    errors = change_errors(w.spec, changes, require_evidence=False) if changes else []
    if errors:
        raise ValueError("; ".join(errors))
    items = [{"rev": i + 1, "title": p.get("title"), "changes": p["changes"], "calculation": p.get("calculation"),
              "fixes": p.get("fixes"), "tag": p.get("tag")} for i, p in enumerate(chosen)]
    if changes:
        items.append({"rev": len(items) + 1, "title": title or "Engineer drawing request", "changes": changes})
    if annotations:
        items.append({"rev": len(items) + 1, "title": "Notes (engineer request)", "changes": [], "notes": annotations})
    all_verified = verified or (bool(chosen) and not changes)
    r = sheet_for(w, w.spec, items, verified=all_verified)
    return {**r, "proposals": [p.get("title") for p in chosen], "verified": all_verified}


def draw_revision_tool(w, a, by=None, request=None):
    """Agent tool draw_revision: render the sheet and save it as a drawing artifact; returns the artifact meta."""
    from . import artifacts
    title = a.get("title") or "Rev B drawing"
    answer = a.get("answer")
    r = render_revision(w, a.get("changes"), a.get("annotations"), title, answer=int(answer) if str(answer).lstrip("-").isdigit() else None,
                        proposals=a.get("proposals"))
    svg = r["svg"]
    files = {"rev_b.svg": svg}
    png = svg_png(svg)
    if png:
        files["rev_b.png"] = png
    return artifacts.save(w.name, "drawing", title, files, by=by or getattr(w, "model", None), request=request,
                          sources=[f"cases/{w.name}/{w.cfg.get('svg')}", "current model spec"],
                          summary=("Draft Rev B P&ID of the verified proposals: " + "; ".join(r["proposals"]) if r["verified"] else
                                   "Draft Rev B P&ID: changes clouded and annotated; the changes not taken from verified proposals are "
                                   "not verified in DWSIM by this tool.") + (f" Not drawn: {', '.join(r['unplaced'])}." if r["unplaced"] else ""))
