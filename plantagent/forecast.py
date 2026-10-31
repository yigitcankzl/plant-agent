"""Fouling forecast for the morning check: when does a fouling exchanger take the plant over its first limit, what does it
cost after that, and by when to clean. Deterministic, no LLM.

1. Fit: least squares on daily-mean U from the historian since the last cleaning (a jump of reset_jump_pct), with the
   slope's standard error; the 95 % band pivots the line about the fit's mean point (slope ± 1.96 SE).
2. Critical U: bisection on the model's U field, re-solving the current model in the simulator at today's throughput,
   until the tightest limit check reaches 100 % (no hard-coded threshold).
3. Date: where the fitted line meets the critical U (band: where the band's lines meet it).
4. Loss: plant capacity re-solved at the U the trend gives `after_days` past the limit date (and at today's U if it is
   already past); lost production = (1 - capacity) x the case's base throughput, priced at an ILLUSTRATIVE salt price.
   The compressor energy the fouling already costs comes from the historian power tag (now vs just after cleaning).
5. Back-test: the same fit made `backtest_days` earlier, so the engineer can see what this check would have said then.

Configuration: cases/<case>/historian_map.json "forecast" -> {exchanger tag: {...}}. CLI: python -m plantagent.forecast <case>
"""
import hashlib
import json
import re
import math
import statistics
from datetime import datetime, timedelta

from . import health
from .plant import patch

Z95 = 1.96


def daily_u(rows, tag):
    days = {}
    for r in rows:
        if r.get(tag) is not None:
            days.setdefault(int(r["day"]), []).append(r[tag])
    return [(d, statistics.fmean(v)) for d, v in sorted(days.items())]


def fit(points, reset_jump_pct=None):
    """Line through daily means since the last cleaning: slope (per day), intercept, R², slope SE, mean point."""
    start = 0
    if reset_jump_pct:
        start = next((i for i in range(len(points) - 1, 0, -1) if points[i][1] > points[i - 1][1] * (1 + reset_jump_pct)), 0)
    xs, ys = [p[0] for p in points[start:]], [p[1] for p in points[start:]]
    if len(xs) < 4:
        raise ValueError("fewer than 4 days since the last cleaning: no trend to fit")
    slope, icpt, r2 = health.trend(xs, ys)
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sse = sum((y - icpt - slope * x) ** 2 for x, y in zip(xs, ys))
    se = math.sqrt(sse / (len(xs) - 2) / sum((x - mx) ** 2 for x in xs))
    return {"from_day": xs[0], "to_day": xs[-1], "n_days": len(xs), "slope_per_day": slope, "intercept": icpt, "r2": r2,
            "slope_se": se, "mean_day": mx, "mean_U": my, "points": list(zip(xs, ys))}


def crossing(f, u_crit, slope=None):
    """Day at which the line (through the fit's mean point, optional other slope) reaches u_crit; None if it never does."""
    s = f["slope_per_day"] if slope is None else slope
    return None if s >= 0 else f["mean_day"] + (u_crit - f["mean_U"]) / s


def _max_util(r):
    c = max((c for c in r.get("checks") or [] if isinstance(c.get("utilisation"), (int, float))), key=lambda c: c["utilisation"], default=None)
    return (c["utilisation"], c) if c else (0.0, None)


def critical_u(solve, spec, path, lo, hi, scale=1.0, steps=12):
    """U at which the tightest check reaches 100 % at `scale` (bisection on simulator solves). Returns (U, check) or
    (None, why) when the bracket does not contain a crossing."""
    at = lambda u: _max_util(solve(patch(spec, [{"path": path, "value": u}]), scale))  # noqa: E731
    u_hi, c_hi = at(hi)
    if u_hi > 1:
        return None, f"over a limit even at U = {hi:g} ({c_hi['id']} {c_hi['check']})"
    u_lo, _ = at(lo)
    if u_lo <= 1:
        return None, f"no limit reached down to U = {lo:g}"
    for _ in range(steps):
        mid = (lo + hi) / 2
        u, c = at(mid)
        lo, hi = (mid, hi) if u > 1 else (lo, mid)
    _, c = at(lo)
    return round((lo + hi) / 2, 1), c


def forecast(w, tag=None, as_of_day=None, refresh=False):
    """The forecast for one exchanger of a workspace (PlantWorkspace). Cached per model spec and as-of day."""
    cfg = json.loads((health.ROOT / "cases" / w.name / "historian_map.json").read_text())
    fc_all = cfg.get("forecast") or {}
    tag = tag or next(iter(fc_all), None)
    if tag not in fc_all:
        raise ValueError(f"no fouling forecast configured for {tag!r}; configured: {list(fc_all)}")
    fc, ex = fc_all[tag], cfg["exchangers"][tag]
    from . import historian
    rows = historian.rows(w.name, cfg)  # PI Web API when configured, else the CSV export
    last_day = int(rows[-1]["day"]) if as_of_day is None else int(as_of_day)
    key = hashlib.sha1(json.dumps([w.spec, tag, last_day, fc], sort_keys=True).encode()).hexdigest()[:16]
    cache = w.model_file.with_name("forecast.json")
    cached = json.loads(cache.read_text()) if cache.exists() else {}
    if not refresh and cached.get("key") == key:
        return cached
    t0 = datetime.fromisoformat(rows[0]["time"])
    date = lambda d: None if d is None else (t0 + timedelta(days=d)).date().isoformat()  # noqa: E731
    pts = [p for p in daily_u(rows, ex["u_tag"]) if p[0] <= last_day]
    f = fit(pts, ex.get("reset_jump_pct"))
    u_now = f["intercept"] + f["slope_per_day"] * last_day
    path, scale = fc["model_path"], 1.0
    u_crit, first = critical_u(w._solve, w.spec, path, fc.get("U_low", 800.0), fc.get("U_high", ex.get("U_clean") or 3000), scale)
    out = {"key": key, "case": w.name, "tag": tag, "model_path": path, "as_of": rows[min(last_day * 24 + 23, len(rows) - 1)]["time"],
           "as_of_day": last_day, "simulator": "DWSIM" if not w.cfg.get("engine") else w.cfg["engine"],
           "model": f"{(w.built or {}).get('label')} rev {len(w.revisions)}", "source": historian.label(cfg), "source_note": cfg.get("note"),
           "fit": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in f.items() if k != "points"},
           "fit_text": f"U = {f['intercept']:.0f} {f['slope_per_day']:+.1f}·day (days {f['from_day']}–{f['to_day']} since cleaning, "
                       f"R² {f['r2']:.3f}, slope ± {Z95 * f['slope_se']:.1f}/day at 95 %)",
           "points": [[d, round(u, 1)] for d, u in daily_u(rows, ex["u_tag"])], "points_start": t0.date().isoformat(), "U_now": round(u_now, 1), "U_clean": ex.get("U_clean")}
    if u_crit is None:
        return {**out, "status": "no limit", "why": first}
    d_c = crossing(f, u_crit)
    band = sorted(x for x in (crossing(f, u_crit, f["slope_per_day"] - Z95 * f["slope_se"]),
                              crossing(f, u_crit, f["slope_per_day"] + Z95 * f["slope_se"])) if x is not None)
    out.update({"U_critical": u_crit, "first_limit": {k: first.get(k) for k in ("id", "check", "value", "limit", "unit", "utilisation")},
                "limit_day": None if d_c is None else round(d_c, 1), "limit_date": date(d_c),
                "limit_band_dates": [date(b) for b in band], "days_to_limit": None if d_c is None else round(d_c - last_day, 1)})
    if d_c is None:
        return {**out, "status": "not fouling"}
    out["status"] = "past the limit" if d_c <= last_day else "within the limit"
    base, unit = (w.cfg.get("throughput") or {}).get("base"), (w.cfg.get("throughput") or {}).get("unit", "")
    price = fc["product_price"]

    def loss(day):
        u = f["intercept"] + f["slope_per_day"] * day
        cap = w._capacity_of(patch(w.spec, [{"path": path, "value": u}])).get("capacity_multiple")
        lost = base * max(0.0, 1 - min(cap, 1.0)) if (base and cap) else None
        return {"day": round(day, 1), "date": date(day), "U": round(u, 1), "capacity_multiple": cap,
                "lost_per_day": None if lost is None else round(lost, 1), "unit": unit,
                "usd_per_day": None if lost is None else round(lost * price["value"])}
    after = loss(max(d_c, last_day) + fc.get("after_days", 7))
    out.update({"after": after, "after_days": fc.get("after_days", 7), "product_price": price, "now": loss(last_day) if d_c <= last_day else None})
    margin = max(fc.get("margin_days", 3), (d_c - band[0]) if band else 0)
    clean_by = max(d_c - margin, last_day)
    out.update({"margin_days": round(margin, 1), "clean_by": date(clean_by), "clean_now": clean_by <= last_day})
    if fc.get("power_tag"):
        pw = [(r["day"], r[fc["power_tag"]]) for r in rows if r.get(fc["power_tag"]) is not None and r["day"] <= last_day + 1]
        early = [v for d, v in pw if f["from_day"] + 1 <= d < f["from_day"] + 3]  # the first two whole days after cleaning
        late = [v for d, v in pw if last_day - 2 <= d < last_day + 1]
        if early and late:
            kw = statistics.fmean(late) - statistics.fmean(early)
            e = fc["energy_price"]
            out["energy"] = {"tag": fc["power_tag"], "extra_kW": round(kw), "usd_per_day": round(kw * 24 * e["value"]), "price": e,
                             "basis": "historian mean of the last 3 days minus the first 2 whole days after cleaning"}
    if fc.get("backtest_days") and as_of_day is None and last_day - fc["backtest_days"] > f["from_day"] + 4:
        b_day = last_day - fc["backtest_days"]
        bf = fit([p for p in pts if p[0] <= b_day], ex.get("reset_jump_pct"))
        bd = crossing(bf, u_crit)
        out["backtest"] = {"as_of": date(b_day), "said_limit_date": date(bd), "said_days_ahead": None if bd is None else round(bd - b_day, 1),
                           "fit_text": f"slope {bf['slope_per_day']:+.1f}/day from {bf['n_days']} days"}
    if as_of_day is None:  # a back-dated forecast is a what-if; the card keeps today's
        cache.write_text(json.dumps(out, indent=1))
    return out


def headline(r):
    """One line for the morning-check card."""
    t, sim = r["tag"], r["simulator"]
    if r.get("status") in ("no limit", "not fouling"):
        return f"{t}: {r.get('why') or 'U is not falling'}; no fouling limit date to forecast ({sim})."
    tag = " at an illustrative price" if re.search("ILLUSTRATIVE|ASSUMED", str((r.get("product_price") or {}).get("source", ""))) else ""
    a, now, usd = r["after"], r.get("now"), lambda v: f"${v:,.0f}/d{tag}"  # noqa: E731
    if r["status"] == "past the limit":
        return (f"{t} passed its limit on {r['limit_date']} ({-r['days_to_limit']:g} days ago) → about {now['lost_per_day']:.0f} {now['unit']} "
                f"({usd(now['usd_per_day'])}) lost now, {a['lost_per_day']:.0f} {a['unit']} by {a['date']} → clean now; verified in {sim}.")
    return (f"{t} reaches its limit in {r['days_to_limit']:.0f} days ({r['limit_date']}) → about {a['lost_per_day']:.0f} {a['unit']} "
            f"and {usd(a['usd_per_day'])} lost {r['after_days']} days after that → clean by {r['clean_by']}; verified in {sim}.")


if __name__ == "__main__":
    import sys
    pts = [(d, 2400 - 30 * d + (5 if d % 2 else -5)) for d in range(20)]
    f = fit([(-1, 1500)] + pts, 0.15)
    assert f["from_day"] == 0 and abs(f["slope_per_day"] + 30) < 0.5 and f["slope_se"] > 0, f
    assert abs(crossing(f, 1800) - 20) < 0.5
    if len(sys.argv) > 1:
        from .plant import PlantWorkspace
        r = forecast(PlantWorkspace(sys.argv[1]), *(sys.argv[2:3] or [None]), refresh=True)
        print(json.dumps({k: v for k, v in r.items() if k != "points"}, indent=1))
    print("ok")
