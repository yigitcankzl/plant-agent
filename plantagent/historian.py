"""Plant historian connector: tag time series from a CSV export or from an OSIsoft PI Web API compatible server
(GET {base}/streams/{webId}/recorded), aligned to hourly rows in the format the morning check and the fouling forecast read
(plantagent.health.load), and mapped to model inputs.

Configuration: cases/<case>/historian_map.json
  "file": CSV export (a time column, then one column per tag) - used when no PI server is configured
  "pi": {"web_ids": {tag: webId}, "start": "*-30d", "end": "*", "step_s": 3600}
  "model_inputs": [{"tag", "path", "factor"?, "offset"?, "window_h"?}]  e.g. FI-1001 t/h -> feeds.S1004mix.kg_h, factor 1000
PI connection from the environment only (never committed): PI_WEB_API_URL, and PI_WEB_API_TOKEN (bearer) or
PI_WEB_API_USER + PI_WEB_API_PASSWORD (basic).
"""
import base64
import csv
import json
import os
import statistics
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_csv(path, tags=None):
    """{tag: [(datetime, value)]} from a CSV export; blank or non-numeric cells are skipped."""
    out = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            t = datetime.fromisoformat(r["time"])
            for k, v in r.items():
                if k == "time" or (tags and k not in tags):
                    continue
                try:
                    out.setdefault(k, []).append((t, float(v)))
                except (TypeError, ValueError):
                    pass
    return out


def _auth():
    if os.getenv("PI_WEB_API_TOKEN"):
        return f"Bearer {os.environ['PI_WEB_API_TOKEN']}"
    if os.getenv("PI_WEB_API_USER"):
        raw = f"{os.environ['PI_WEB_API_USER']}:{os.getenv('PI_WEB_API_PASSWORD', '')}".encode()
        return "Basic " + base64.b64encode(raw).decode()
    return None


def read_pi(web_ids, start="*-30d", end="*", base=None, max_count=150000, timeout=30):
    """{tag: [(datetime, value)]} from PI Web API recorded values. Bad-quality and digital-state values are skipped."""
    base = (base or os.getenv("PI_WEB_API_URL") or "").rstrip("/")
    if not base:
        raise ValueError("PI_WEB_API_URL is not set")
    out = {}
    for tag, wid in web_ids.items():
        q = urllib.parse.urlencode({"startTime": start, "endTime": end, "maxCount": max_count})
        req = urllib.request.Request(f"{base}/streams/{urllib.parse.quote(wid)}/recorded?{q}", headers={"Accept": "application/json"})
        if _auth():
            req.add_header("Authorization", _auth())
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - the configured historian URL
            items = json.loads(r.read()).get("Items") or []
        pts = []
        for it in items:
            v = it.get("Value")
            if it.get("Good") is False or isinstance(v, (dict, bool)) or v is None:
                continue
            t = datetime.fromisoformat(str(it["Timestamp"]).replace("Z", "+00:00"))
            pts.append((t.astimezone(timezone.utc).replace(tzinfo=None), float(v)))
        out[tag] = sorted(pts)
    return out


def align(series, step_s=3600):
    """Hourly (step_s) rows in plantagent.health.load format: {day, time, tag: mean of the samples in that step or None}."""
    pts = [t for s in series.values() for t, _ in s]
    if not pts:
        return []
    t0 = min(pts)
    t0 = t0.replace(minute=0, second=0, microsecond=0) if step_s == 3600 else t0
    buckets = {}
    for tag, s in series.items():
        for t, v in s:
            buckets.setdefault(int((t - t0).total_seconds() // step_s), {}).setdefault(tag, []).append(v)
    rows = []
    for b in range(max(buckets) + 1):
        vals = buckets.get(b, {})
        t = t0 + timedelta(seconds=b * step_s)
        rows.append({"day": b * step_s / 86400, "time": t.isoformat(timespec="minutes"),
                     **{tag: (statistics.fmean(vals[tag]) if tag in vals else None) for tag in series}})
    return rows


def source(cfg):
    """'pi' when the case maps PI web ids and a PI server is configured, else 'csv'."""
    return "pi" if cfg.get("pi") and os.getenv("PI_WEB_API_URL") else "csv"


def label(cfg):
    """Where the rows came from, for the cards and documents."""
    return f"PI Web API ({len(cfg['pi']['web_ids'])} tags)" if source(cfg) == "pi" else cfg["file"]


def rows(case, cfg=None):
    """Historian rows for a case, from PI when configured, else the CSV export (same format either way)."""
    cfg = cfg or json.loads((ROOT / "cases" / case / "historian_map.json").read_text())
    if source(cfg) == "pi":
        p = cfg["pi"]
        return align(read_pi(p["web_ids"], p.get("start", "*-30d"), p.get("end", "*")), p.get("step_s", 3600))
    from .health import load
    return load(ROOT / "cases" / case / cfg["file"])


def model_inputs(rs, mapping):
    """Model changes from the latest window of each mapped tag: [{path, value, tag, mean_of, source}]."""
    out = []
    for m in mapping:
        last = max((r["day"] for r in rs), default=0)
        win = m.get("window_h", 24) / 24
        vals = [r[m["tag"]] for r in rs if r.get(m["tag"]) is not None and r["day"] > last - win]
        if not vals:
            continue
        v = statistics.fmean(vals) * m.get("factor", 1) + m.get("offset", 0)
        out.append({"path": m["path"], "value": round(v, 4), "tag": m["tag"], "mean_of": len(vals),
                    "source": f"historian mean of the last {m.get('window_h', 24)} h"})
    return out


def summary(case):
    """What the connector sees for a case: source, tags, span and the mapped model inputs."""
    cfg = json.loads((ROOT / "cases" / case / "historian_map.json").read_text())
    rs = rows(case, cfg)
    tags = sorted({k for r in rs for k in r if k not in ("day", "time")})
    return {"case": case, "source": source(cfg), "source_label": label(cfg), "note": cfg.get("note"), "tags": tags, "n_rows": len(rs),
            "first": rs[0]["time"] if rs else None, "last": rs[-1]["time"] if rs else None,
            "pi_configured": bool(cfg.get("pi")), "pi_server": bool(os.getenv("PI_WEB_API_URL")),
            "model_inputs": model_inputs(rs, cfg.get("model_inputs") or [])}


if __name__ == "__main__":
    import sys
    print(json.dumps(summary(sys.argv[1] if len(sys.argv) > 1 else "salt_mvr"), indent=1))
