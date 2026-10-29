"""Morning check: what an engineer looks at first thing. The plant's historian export is compared with the model and with
its limits, and the result is a short ranked list of things to look at today. Deterministic, no LLM.

- Exchangers: overall heat-transfer coefficient U from every sample (cold-side duty / counter-current LMTD / area), its
  trend over the window, and how many days until the process outlet limit is reached at today's and at the target
  throughput (critical U found by re-solving the plant model in DWSIM).
- Measured limits: last-day maximum against the limit, and how often it was exceeded over the window.
- Data quality: tags that are missing or flat-lined (a stuck transmitter is the first thing to rule out).

Configuration per case: cases/<case>/historian_map.json. CLI: python -m plantagent.health <case>
"""
import csv
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

from . import process
from .plant import patch

ROOT = Path(__file__).resolve().parent.parent


def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    t0 = datetime.fromisoformat(rows[0]["time"])
    out = []
    for r in rows:
        d = {"day": (datetime.fromisoformat(r["time"]) - t0).total_seconds() / 86400, "time": r["time"]}
        for k, v in r.items():
            if k != "time":
                try:
                    d[k] = float(v)
                except (TypeError, ValueError):
                    d[k] = None
        out.append(d)
    return out


def lmtd(dt1, dt2):
    if dt1 <= 0 or dt2 <= 0:
        return None
    return (dt1 - dt2) / __import__("math").log(dt1 / dt2) if abs(dt1 - dt2) > 1e-6 else dt1


def trend(xs, ys):
    """Least-squares slope, intercept and R^2."""
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    icpt = my - slope * mx
    ss = sum((y - my) ** 2 for y in ys)
    r2 = 1 - sum((y - (icpt + slope * x)) ** 2 for x, y in zip(xs, ys)) / ss if ss else 0.0
    return slope, icpt, r2


def exchanger_u(rows, c):
    """U (W/m2K) per sample from the cold side's duty; the hot side is the process stream."""
    out = []
    for r in rows:
        vals = [r.get(c[k]) for k in ("hot_in", "hot_out", "cold_in", "cold_out", "cold_flow_m3h")]
        if None in vals:
            continue
        thi, tho, tci, tco, qc = vals
        duty_kw = qc / 3600 * c.get("rho_cold", 997.0) * c.get("cp_cold_kJ_kgK", 4.18) * (tco - tci)
        lm = lmtd(thi - tco, tho - tci)
        if lm and duty_kw > 0:
            out.append({"day": r["day"], "U": duty_kw * 1000 / (c["area_m2"] * lm), "duty_kW": duty_kw})
    return out


def critical_u(spec, unit, out_stream, limit_C, scale, lo=100.0, hi=3000.0):
    """The U at which the process outlet reaches its limit at a throughput multiple (bisection on DWSIM solves)."""
    def out_T(u):
        r = process.run(patch(spec, [{"path": f"units.{unit}.U_W_m2K", "value": u}]), scale)
        return r["streams"][out_stream]["T_C"]
    if out_T(hi) > limit_C:
        return None  # even a clean, oversized exchanger cannot hold the limit at this throughput
    for _ in range(14):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if out_T(mid) > limit_C else (lo, mid)
    return round(hi, 1)


def check(case):
    cfg = json.loads((ROOT / "cases" / case / "historian_map.json").read_text())
    rows = load(ROOT / "cases" / case / cfg["file"])
    model = ROOT / "runs" / "ws" / case / "model.json"
    spec = json.loads(model.read_text())["spec"] if model.exists() else None
    items, exch, meas, quality = [], [], [], []
    last = max(r["day"] for r in rows)

    for unit, c in cfg.get("exchangers", {}).items():
        us = ([{"day": r["day"], "U": r[c["u_tag"]]} for r in rows if r.get(c["u_tag"]) is not None]
              if c.get("u_tag") else exchanger_u(rows, c))
        if len(us) < 10:
            quality.append(f"{unit}: too few valid samples to compute U")
            continue
        days = {}
        for u in us:
            days.setdefault(int(u["day"]), []).append(u["U"])
        xs, ys = list(days), [statistics.fmean(v) for v in days.values()]
        reset = None
        if c.get("reset_jump_pct"):
            reset = next((i for i in range(len(xs) - 1, 0, -1) if ys[i] > ys[i - 1] * (1 + c["reset_jump_pct"])), None)
        if reset is not None:
            xs, ys = xs[reset:], ys[reset:]
        slope, icpt, r2 = trend(xs, ys)
        u_now = statistics.fmean(u["U"] for u in us if u["day"] > last - 3)
        e = {"unit": unit, "U_now": round(u_now, 1), "U_start": round(ys[0], 1), "slope_per_day": round(slope, 2),
             "r2": round(r2, 2), "change_pct": round((u_now / ys[0] - 1) * 100, 1), "U_clean": c.get("U_clean"),
             "trend_from_day": xs[0]}
        for label, scale in (("today", 1.0), ("target", cfg.get("target_scale"))):
            if not (spec and c.get("model_out_stream") and c.get("out_limit_C")):
                continue
            if not scale:
                continue
            uc = critical_u(spec, unit, c["model_out_stream"], c["out_limit_C"], scale)
            e[f"U_critical_{label}"] = uc
            if uc is None:
                e[f"days_to_limit_{label}"] = None
                e[f"status_{label}"] = "cannot hold the limit even when clean"
            elif u_now <= uc:
                e[f"days_to_limit_{label}"] = 0
                e[f"status_{label}"] = "already over the limit"
            else:
                e[f"days_to_limit_{label}"] = round((u_now - uc) / -slope) if slope < 0 else None
                e[f"status_{label}"] = "within the limit"
        exch.append(e)
        d_today, d_tgt = e.get("days_to_limit_today"), e.get("days_to_limit_target")
        if slope < 0 and r2 > 0.5:
            period = f"since day {xs[0]}" if reset is not None else f"in {last:.0f} days"
            text = (f"{unit} is fouling: U {e['U_start']:.0f} → {u_now:.0f} W/m²K "
                    f"{period} ({e['change_pct']}%). "
                    + (f"At today's throughput the {c['out_limit_C']} °C outlet limit is reached in about {d_today} days. "
                       if d_today else "At today's throughput it is already at the outlet limit. " if d_today == 0 else "")
                    + (f"At the target throughput it is already over the limit (needs U ≥ {e['U_critical_target']:.0f})."
                       if d_tgt == 0 else f"At the target throughput the limit is reached in about {d_tgt} days." if d_tgt else "")
                    + (f" Clean-reference U: {c['U_clean']} W/m²K." if c.get("U_clean") else ""))
            urgency = 100 - min(d_today if d_today is not None else 0, 99) + (30 if d_tgt == 0 else 0)
            items.append({"urgency": urgency, "unit": unit, "kind": "fouling", "text": text})

    for m in cfg.get("limits", []):
        vals = [(r["day"], r.get(m["tag"])) for r in rows if r.get(m["tag"]) is not None]
        if not vals:
            quality.append(f"{m['tag']}: no data")
            continue
        recent = [v for d, v in vals if d > last - 1]
        peak, exceed = max(recent), sum(1 for _, v in vals if v > m["max"])
        meas.append({"tag": m["tag"], "name": m["name"], "last_day_max": round(peak, 2), "limit": m["max"],
                     "margin": round(m["max"] - peak, 2), "exceedances": exceed, "samples": len(vals)})
        if peak > m["max"] - m.get("warn_margin", 1.0):
            items.append({"urgency": 80 if peak > m["max"] else 50, "unit": m["name"], "kind": "limit",
                          "text": f"{m['name']} peaked at {peak:.1f} against {m['max']} in the last day "
                                  f"({exceed} of {len(vals)} samples over the limit in this window)."})

    for tag in [k for k in rows[0] if k not in ("day", "time")]:
        vals = [r[tag] for r in rows[-24:] if r.get(tag) is not None]
        if len(vals) < len(rows[-24:]) * 0.8:
            quality.append(f"{tag}: {len(rows[-24:]) - len(vals)} of the last {len(rows[-24:])} samples missing")
        elif len(set(vals)) == 1:
            quality.append(f"{tag}: flat at {vals[0]} for the last {len(vals)} samples (stuck transmitter?)")
    for q in quality:
        items.append({"urgency": 60, "unit": q.split(":")[0], "kind": "data quality", "text": q})

    items.sort(key=lambda x: -x["urgency"])
    return {"case": case, "source": cfg["file"], "source_note": cfg.get("note", ""), "from": rows[0]["time"], "to": rows[-1]["time"],
            "samples": len(rows), "today": items[:3], "all": items, "exchangers": exch, "measured_limits": meas, "data_quality": quality}


if __name__ == "__main__":
    us = exchanger_u([{"day": 0, "a": 50, "b": 35, "c": 25, "d": 37.7, "q": 20}],
                     {"hot_in": "a", "hot_out": "b", "cold_in": "c", "cold_out": "d", "cold_flow_m3h": "q", "area_m2": 46.8})
    assert 550 < us[0]["U"] < 650, us  # the data sheet's operating point (34 C out, 37.7 C return) gives U ~ 600
    s, i, r2 = trend([0, 1, 2], [10, 8, 6])
    assert abs(s + 2) < 1e-9 and r2 > 0.999
    if len(sys.argv) > 1:
        res = check(sys.argv[1])
        out = ROOT / "runs" / "ws" / sys.argv[1] / "health.json"
        out.write_text(json.dumps(res, indent=1))
        print(json.dumps({k: res[k] for k in ("today", "exchangers", "data_quality")}, indent=1))
        print("wrote", out)
    print("ok")
