"""Every engineering input of a plant, with where it came from, and the engineer's confirmations (contract: docs/assumptions.md).

Inputs live in three places: the case files (cases/<case>/*.json), drafts made for a new plant (runs/ws/<case>/drafts/*.json)
and files the engineer uploaded (runs/ws/<case>/inputs/*.json). Each numeric value is one assumption. Confirming or editing
one appends to runs/ws/<case>/assumptions_log.jsonl; the latest log line wins and marks it engineer_confirmed."""
import csv
import io
import json
import math
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ("documented", "datasheet", "muse_default", "assumed", "engineer_confirmed")
SKIP_FILES = {"case", "historian_map", "outcome", "prefeed"}  # config, tag maps and recorded outcomes are not inputs
SKIP_KEYS = {"source", "note", "unit", "currency", "notes"}


def ws_dir(case):
    return ROOT / "runs" / "ws" / case


def classify(text, default):
    """Map a free-text source note ("basis.md: 18 m3/h", "ILLUSTRATIVE", "vendor datasheet") to one of SOURCES."""
    t = str(text or "").strip()
    if t in SOURCES:
        return t
    low = t.lower()
    if not low:
        return default
    if "engineer" in low and "confirm" in low:
        return "engineer_confirmed"
    if re.search(r"illustrative|assum|placeholder|typical|estimate", low):
        return "assumed"
    if re.search(r"\bmuse\b|draft|default", low):
        return "muse_default"
    if re.search(r"datasheet|data sheet|vendor|nameplate|manufacturer", low):
        return "datasheet"
    return "documented"


def _files(case):
    """(file id, path, default source, writable) for every input file of the case."""
    out = []
    for p in sorted((ROOT / "cases" / case).glob("*.json")):
        if p.stem not in SKIP_FILES:
            out.append((p.stem, p, "assumed", False))
    for sub, default in (("drafts", "muse_default"), ("inputs", "datasheet")):
        for p in sorted((ws_dir(case) / sub).glob("*.json")):
            out.append((f"{sub}/{p.stem}", p, default, True))
    return out


def _walk(node, loc, label, source, out, note=None):
    if isinstance(node, dict):
        if isinstance(node.get("source"), str):
            source, note = classify(node["source"], source), node["source"]
        if "value" in node and isinstance(node["value"], (int, float)) and not isinstance(node["value"], bool):
            out.append({"loc": loc + ["value"], "label": label, "value": node["value"], "unit": node.get("unit"),
                        "source": source, "note": note})
            return
        for k, v in node.items():
            if k not in SKIP_KEYS:
                _walk(v, loc + [k], f"{label}.{k}" if label else k, source, out, note)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            name = next((v[k] for k in ("id", "tag", "name") if isinstance(v, dict) and isinstance(v.get(k), str)), str(i))
            _walk(v, loc + [i], f"{label}.{name}" if label else name, source, out, note)
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        out.append({"loc": loc, "label": label, "value": node, "unit": None, "source": source, "note": note})


def log(case):
    f = ws_dir(case) / "assumptions_log.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def collect(case):
    """All assumptions of the case, each {id, file, label, value, unit, source, note, confirmed_at?}."""
    last = {e["id"]: e for e in log(case)}
    items = []
    for fid, path, default, writable in _files(case):
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        rows = []
        _walk(data, [], "", default, rows, data.get("note") if isinstance(data, dict) else None)
        for r in rows:
            r.update(id=f"{fid}:{r['label']}", file=fid, writable=writable)
            if r["id"] in last:
                e = last[r["id"]]
                r.update(source="engineer_confirmed", confirmed_at=e["at"], confirmed_by=e.get("user"))
                if not writable:  # shipped case data is not rewritten; the log carries the engineer's value
                    r["value"] = e["value"]
            items.append(r)
    return items


def summary(items):
    return {s: sum(1 for i in items if i["source"] == s) for s in SOURCES}


def confirm(case, item_id, value=None, user=None, note=None, uploaded=False):
    """Confirm an assumption (value None keeps it) or set a new value. Writes the value back to drafts/inputs files and to
    the case files of an uploaded project; shipped demo cases keep their files and take the value from the log."""
    match = next((i for i in collect(case) if i["id"] == item_id), None)
    if not match:
        raise ValueError(f"unknown assumption {item_id!r}")
    new = match["value"] if value is None else value
    if isinstance(new, bool) or not isinstance(new, (int, float)) or not math.isfinite(new):
        raise ValueError("value must be a finite number")
    path = next(p for fid, p, _, _ in _files(case) if fid == match["file"])
    written = match["writable"] or uploaded
    if written and new != match["value"]:
        data = json.loads(path.read_text())
        node = data
        for k in match["loc"][:-1]:
            node = node[k]
        node[match["loc"][-1]] = new
        if match["loc"][-1] == "value":
            node["source"] = "engineer_confirmed"
        path.write_text(json.dumps(data, indent=2))
    entry = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "id": item_id, "old": match["value"], "value": new,
             "source": "engineer_confirmed", "user": user, "note": (str(note)[:500] if note else None), "written": written}
    f = ws_dir(case) / "assumptions_log.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


# Uploads: the engineer's own data, with the expected columns shown before upload
TEMPLATES = {
    "motors": {"title": "Motor list", "format": "CSV", "required": ["tag", "kw"], "optional": ["voltage_kv", "start", "cable_m"],
               "example": "tag,kw,voltage_kv,start,cable_m\nP-101,75,0.4,dol,120\nK-201,2400,6.6,vfd,300\n",
               "use": "electrical load flow and motor starting: one row per motor; start is dol, soft or vfd"},
    "curves": {"title": "Pump or compressor curve", "format": "CSV", "required": ["tag", "flow_m3h", "head_m"],
               "optional": ["efficiency_pct", "speed_rpm"],
               "example": "tag,flow_m3h,head_m,efficiency_pct\nP-101,0,62,0\nP-101,60,58,71\nP-101,120,47,78\nP-101,160,35,70\n",
               "use": "vendor curve: at least three points per tag, flow rising; the lowest flow row is the minimum-flow point"},
    "datasheet": {"title": "Equipment data sheet", "format": "PDF", "required": [], "optional": [],
                  "example": None, "use": "stored with the project as a documented source"},
}


def _rows(data, kind):
    t = TEMPLATES[kind]
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    if not rows:
        raise ValueError(f"the {t['title'].lower()} has no rows")
    cols = {c.strip() for c in rows[0].keys() if c}
    missing = [c for c in t["required"] if c not in cols]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}; expected {', '.join(t['required'] + t['optional'])}")
    out = []
    for n, r in enumerate(rows, 2):
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("tag"):
            raise ValueError(f"row {n}: tag is empty")
        row = {"id": r["tag"]}
        for c in t["required"][1:] + [c for c in t["optional"] if c != "start"]:
            if r.get(c):
                try:
                    x = float(r[c])
                except ValueError:
                    raise ValueError(f"row {n}: {c} is not a number: {r[c]!r}") from None
                if not math.isfinite(x) or x < 0:
                    raise ValueError(f"row {n}: {c} must be a finite, non-negative number")
                row[c] = x
            elif c in t["required"]:
                raise ValueError(f"row {n}: {c} is empty")
        if kind == "motors" and r.get("start"):
            if r["start"].lower() not in ("dol", "soft", "vfd"):
                raise ValueError(f"row {n}: start must be dol, soft or vfd")
            row["start"] = r["start"].lower()
        out.append(row)
    return out


def upload(case, kind, data, filename=None):
    if kind not in TEMPLATES:
        raise ValueError(f"kind must be one of {', '.join(TEMPLATES)}")
    d = ws_dir(case) / "inputs"
    d.mkdir(parents=True, exist_ok=True)
    if kind == "datasheet":
        if not data.startswith(b"%PDF-"):
            raise ValueError("upload a PDF data sheet")
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename or "datasheet.pdf").name)[:80] or "datasheet.pdf"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        (d / "datasheets").mkdir(exist_ok=True)
        (d / "datasheets" / name).write_bytes(data)
        return {"kind": kind, "file": f"inputs/datasheets/{name}", "source": "documented", "bytes": len(data)}
    # leading "# ..." lines are the file's own note (e.g. "ILLUSTRATIVE vendor curve"); it travels with every value
    text = data.decode("utf-8-sig")
    note = " ".join(ln.lstrip("#").strip() for ln in text.splitlines() if ln.startswith("#"))
    rows = _rows("\n".join(ln for ln in text.splitlines() if not ln.startswith("#")).encode(), kind)
    if kind == "motors":
        doc = {"source": "datasheet", "note": note or "motor list uploaded by the engineer", "motors": rows}
    else:
        curves = {}
        for r in rows:
            curves.setdefault(r.pop("id"), []).append(r)
        for tag, pts in curves.items():
            if len(pts) < 3:
                raise ValueError(f"{tag}: a curve needs at least three points")
            if any(b["flow_m3h"] <= a["flow_m3h"] for a, b in zip(pts, pts[1:])):
                raise ValueError(f"{tag}: flow must rise from row to row")
        doc = {"source": "datasheet", "note": note or "vendor curves uploaded by the engineer",
               "curves": [{"id": tag, "points": pts} for tag, pts in curves.items()]}
    (d / f"{kind}.csv").write_bytes(data)  # the raw file, kept as uploaded
    (d / f"{kind}.json").write_text(json.dumps(doc, indent=2))
    from . import drafts
    used = drafts.resolve_uploads(case, ROOT)  # into the discipline files the checks read (inputs > case > draft)
    return {"kind": kind, "file": f"inputs/{kind}.json", "source": "datasheet", "rows": len(rows),
            "applied_to": {k: v for k, v in used.items() if v}}


def inputs(case):
    d = ws_dir(case) / "inputs"
    files = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()) if d.exists() else []
    return {"templates": TEMPLATES, "files": files}


if __name__ == "__main__":
    items = collect("salt_mvr")
    print(len(items), summary(items))
    for i in items[:8]:
        print(i["id"], i["value"], i["source"])
