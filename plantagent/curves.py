"""Equipment performance curves: centrifugal pumps (head and efficiency vs flow) and compressors (polytropic head and
efficiency vs actual suction flow, surge and stonewall), scaled to other speeds by the affinity laws.

A unit may carry `curve` in its spec. Points are normalised to a design point so a vendor curve and a generic shape use
the same form:
  {"kind": "compressor" | "pump",
   "design": {"q_m3_h": actual suction (compressor) or delivered (pump) flow at the design point,
              "pr": pressure ratio at the design point (compressor), "T_in_C": suction temperature for that ratio,
              "head_m": design head (pump), "eff_pct": efficiency at the design point},
   "points": [[q/q_design, head/head_design, eff/eff_design], ...],   # at 100 % speed, flow ascending
   "surge_q": q/q_design of the surge line at 100 % speed (compressor), "stonewall_q": choke (compressor),
   "min_flow_q": minimum continuous flow (pump), "speed_pct": running speed, "variable_speed": bool,
   "max_speed_pct": drive limit, "k": isentropic exponent (default 1.3, steam), "M": molar mass (default 18.015),
   "basis": where the curve comes from (ILLUSTRATIVE unless a vendor curve)}

With a curve, a unit's capacity is the flow the curve delivers at the head the process needs (descending branch, right
of the peak), not a fixed rated flow. Compressors that draw from the same splitter and discharge to the same pressure
share load the way their curves do at that common head.
ponytail: piecewise-linear curves and an ideal-gas head with a constant exponent; a vendor map with Z and speed lines
replaces this when one exists.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R_U = 8314.462618  # J/(kmol K)


def head_kJ_kg(pr, T_in_C, k=1.3, M=18.015):
    """Isentropic head of an ideal gas over a pressure ratio (kJ/kg)."""
    e = (k - 1) / k
    return k / (k - 1) * R_U / M * (T_in_C + 273.15) * (pr ** e - 1) / 1000


def _interp(xs, ys, x):
    x = min(max(x, xs[0]), xs[-1])  # flat outside the published points: never extrapolate a curve
    if x <= xs[0]:
        i = 0
    elif x >= xs[-1]:
        i = len(xs) - 2
    else:
        i = next(j for j in range(len(xs) - 1) if xs[j] <= x <= xs[j + 1])
    x0, x1, y0, y1 = xs[i], xs[i + 1], ys[i], ys[i + 1]
    return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)


class Curve:
    def __init__(self, c):
        pts = sorted(c["points"])
        self.c, self.q, self.h, self.e = c, [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
        d = c["design"]
        self.kind = c.get("kind", "compressor")
        self.q_d = float(d["q_m3_h"])
        self.eff_d = float(d.get("eff_pct", 75))
        self.k, self.M = float(c.get("k", 1.3)), float(c.get("M", 18.015))
        self.h_d = float(d["head_m"]) if self.kind == "pump" else head_kJ_kg(float(d["pr"]), float(d["T_in_C"]), self.k, self.M)
        self.peak = max(range(len(self.h)), key=lambda i: self.h[i])  # descending branch starts here

    # at speed fraction n (affinity: Q ~ n, H ~ n^2, efficiency moves with Q/n)
    def head(self, q_m3_h, n=1.0):
        return self.h_d * n * n * _interp(self.q, self.h, q_m3_h / (self.q_d * n))

    def eff_pct(self, q_m3_h, n=1.0):
        return self.eff_d * _interp(self.q, self.e, q_m3_h / (self.q_d * n))

    def flow_at_head(self, head, n=1.0):
        """Flow on the descending branch where the curve gives `head`; None if the head is above the curve's peak."""
        target = head / (self.h_d * n * n)
        qs, hs = self.q[self.peak:], self.h[self.peak:]
        if target > hs[0]:
            return None
        if target <= hs[-1]:
            return qs[-1] * self.q_d * n  # at or past the last point: choke
        for j in range(len(qs) - 1):
            if hs[j] >= target >= hs[j + 1]:
                f = (hs[j] - target) / ((hs[j] - hs[j + 1]) or 1)
                return (qs[j] + f * (qs[j + 1] - qs[j])) * self.q_d * n

    def speed_for(self, q_m3_h, head, lo=0.3, hi=1.3):
        """Speed fraction at which the curve passes through (q, head), on the stable side; None if not in [lo, hi]."""
        def gap(n):
            q_max = self.flow_at_head(head, n)
            return -1.0 if q_max is None else q_max - q_m3_h
        if gap(hi) < 0 or gap(lo) > 0:
            return None if gap(hi) < 0 else lo
        for _ in range(60):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if gap(m) < 0 else (lo, m)
        return hi

    def surge_m3_h(self, n=1.0):
        return float(self.c["surge_q"]) * self.q_d * n if self.c.get("surge_q") else None

    def stonewall_m3_h(self, n=1.0):
        return float(self.c["stonewall_q"]) * self.q_d * n if self.c.get("stonewall_q") else None


def _stream(res, sid):
    return (res.get("streams") or {}).get(sid) or {}


def _op(u, res, by_id):
    """Operating need of one curved unit from the solved state: actual flow, required head, suction density."""
    cv = Curve(u["curve"])
    if cv.kind == "pump":
        r = (res.get("units") or {}).get(u["id"]) or {}
        return cv, r.get("m3_h"), r.get("head_m"), None
    s_in, s_out = _stream(res, u["in"]), _stream(res, u["out"])
    if not s_in.get("m3_h") or not s_in.get("P_bar") or not s_out.get("P_bar"):
        return cv, None, None, None
    pr = s_out["P_bar"] / s_in["P_bar"]
    return cv, s_in["m3_h"], head_kJ_kg(pr, s_in["T_C"], cv.k, cv.M), s_in["kg_h"] / s_in["m3_h"]


def _groups(spec):
    """Compressors with curves fed by one splitter and discharging at one pressure run in parallel on a common head."""
    comps = [u for u in spec.get("units") or [] if u.get("type") == "compressor" and u.get("curve")]
    out, seen = [], set()
    for sp in spec.get("units") or []:
        if sp.get("type") != "splitter":
            continue
        members = [u for u in comps if u["in"] in (sp.get("out") or [])]
        if len(members) > 1 and len({u.get("P_out_bar") for u in members}) == 1:
            out.append(members)
            seen |= {u["id"] for u in members}
    return out + [[u] for u in comps if u["id"] not in seen]


def _row(uid, check, value, limit, unit, util, **extra):
    return {"id": uid, "check": check, "value": round(value, 1) if value is not None else None, "limit": round(limit, 1) if limit else limit,
            "unit": unit, "utilisation": round(util, 3), "source": "performance curve (curves.py)", **extra}


def checks(spec, res):
    """Check rows for every unit with a curve (same shape as process._checks rows), plus the operating point of each."""
    by_id = {u["id"]: u for u in spec.get("units") or []}
    out = []
    for group in _groups(spec):
        ops = {u["id"]: _op(u, res, by_id) for u in group}
        if any(q is None for _, q, _, _ in ops.values()):
            out += [{"id": u["id"], "check": "performance curve", "error": "operating point not in the solved state"} for u in group]
            continue
        head = max(h for _, _, h, _ in ops.values())  # common discharge, common suction: the same head
        total = sum(q for _, q, _, _ in ops.values())
        caps = {}
        for u in group:
            cv = ops[u["id"]][0]
            n = float(u["curve"].get("speed_pct", 100)) / 100
            if u["curve"].get("variable_speed"):
                n = float(u["curve"].get("max_speed_pct", 100)) / 100
            caps[u["id"]] = (cv.flow_at_head(head, n) or 0.0, n)
        cap_total = sum(c for c, _ in caps.values())
        # in a parallel group the curves, not the model's fixed split, decide each machine's share: a fixed-speed machine
        # runs where its curve meets the common head; variable-speed machines take the rest, in proportion to capacity
        vsd = [u["id"] for u in group if u["curve"].get("variable_speed")]
        fixed = [u["id"] for u in group if u["id"] not in vsd]
        share = {}
        if len(group) > 1 and cap_total > 0:
            f_cap, v_cap = sum(caps[i][0] for i in fixed), sum(caps[i][0] for i in vsd)
            if not vsd or not fixed:
                share = {i: total * caps[i][0] / cap_total for i in caps}
            else:
                cut = min(1.0, total / f_cap) if f_cap else 0.0
                share = {i: caps[i][0] * cut for i in fixed}
                rem = max(0.0, total - sum(share.values()))
                share.update({i: rem * caps[i][0] / v_cap if v_cap else 0.0 for i in vsd})
        for u in group:
            cv, q_fixed, h_u, rho = ops[u["id"]]
            cap, n = caps[u["id"]]
            q = share.get(u["id"], q_fixed)
            unit = "m3/h" if cv.kind == "pump" else "m3/h actual"
            shared = len(group) > 1
            label = (f"flow vs curve capacity at the required head ({'parallel group ' + '+'.join(x['id'] for x in group) if shared else 'this unit'})")
            util = (total / cap_total if shared else q / cap) if (cap_total if shared else cap) else 9.99
            n_need = cv.speed_for(max(q, 1e-6), h_u) if u["curve"].get("variable_speed") else None
            op = {"q_m3_h": round(q, 1), "q_model_m3_h": round(q_fixed, 1), "head": round(h_u, 2),
                  "head_unit": "m" if cv.kind == "pump" else "kJ/kg", "q_over_design": round(q / cv.q_d, 3),
                  "speed_needed_pct": round(n_need * 100, 1) if n_need else None,
                  "speed_pct": round((n_need or n) * 100, 1), "drive": "variable speed" if n_need else "fixed speed",
                  "eff_pct": round(cv.eff_pct(q, n_need or n), 1), "kg_h": round(q * rho, 0) if rho else None,
                  "basis": u["curve"].get("basis", "")}
            if cv.kind == "compressor" and rho:
                op["shaft_kW"] = round(q * rho / 3600 * h_u / (op["eff_pct"] / 100), 0)
            out.append(_row(u["id"], label, total if shared else q, cap_total if shared else cap, unit, util, operating_point=op))
            if cv.kind == "compressor":
                n_op = n_need or n
                qs, qc = cv.surge_m3_h(n_op), cv.stonewall_m3_h(n_op)
                if qs:  # surge margin = 1 - Q_surge/Q at the running speed; below 10 % is a warning band
                    op["surge_margin_pct"] = round((1 - qs / q) * 100, 1) if q > 0 else None
                    out.append(_row(u["id"], "surge flow (+10 % margin) vs operating flow; above 100 % the machine needs recycle",
                                    qs * 1.1, q, unit, qs * 1.1 / q if q > 0 else 9.99))
                if qc:
                    op["stonewall_margin_pct"] = round((1 - q / qc) * 100, 1)
                    out.append(_row(u["id"], "operating flow vs stonewall (choke)", q, qc, unit, q / qc))
            elif u["curve"].get("min_flow_q"):
                q_min = float(u["curve"]["min_flow_q"]) * cv.q_d * (n_need or n)
                out.append(_row(u["id"], "flow vs minimum continuous (curve)", q, q_min, unit, q_min / q if q else 9.99))
    return out


def overlay(case):
    """cases/<case>/curves.json: {"basis": ..., "units": {tag: curve}}; None without one."""
    f = ROOT / "cases" / case / "curves.json"
    return json.loads(f.read_text()) if f.exists() else None


def apply(spec, ov):
    """A copy of the spec with each overlay curve on its unit (the stored model is not changed)."""
    spec = copy.deepcopy(spec)
    for u in spec.get("units") or []:
        if u["id"] in (ov or {}).get("units", {}):
            u["curve"] = ov["units"][u["id"]]
    return spec


def evaluate(w, refresh=False):
    """The case's curves on the combined design (or the model when there is none) at 100 % and at the target.
    Cached in runs/ws/<case>/curves.json by content hash. No model call."""
    from . import process
    from .plant import patch
    from .revb import design_answer
    ov = overlay(w.name)
    if not ov:
        return {"error": "no performance curves for this case (cases/<case>/curves.json)"}
    ans = design_answer(w.answers)
    changes = [c for p in (ans or {}).get("proposals") or [] if p.get("verified") for c in p.get("changes") or []]
    spec = apply(patch(copy.deepcopy(w.spec), changes), ov)
    target = float(w.cfg.get("target_scale", 1.0))
    key = hashlib.sha256(json.dumps([spec, target, 1], sort_keys=True, default=str).encode()).hexdigest()[:16]
    cache = w.model_file.with_name("curves.json")
    if cache.exists() and not refresh:
        old = json.loads(cache.read_text())
        if old.get("key") == key:
            return old
    rows = {}
    for sc in sorted({1.0, target}):
        r = process.run(spec, sc)
        if r.get("errors"):
            rows[f"{sc:.2f}"] = {"error": "; ".join(map(str, r["errors"]))[:300]}
            continue
        cks = checks(spec, r)
        rows[f"{sc:.2f}"] = {"scale": sc, "checks": cks,
                             "operating_points": {c["id"]: c["operating_point"] for c in cks if c.get("operating_point")},
                             "worst": max((c.get("utilisation", 0) for c in cks), default=0)}
    tgt = rows.get(f"{target:.2f}", {})
    holds = bool(tgt.get("checks")) and all(c.get("utilisation", 0) <= 1.0 for c in tgt["checks"] if "error" not in c)
    out = {"key": key, "basis": ov.get("basis"), "applied_to": "combined design" if changes else "model",
           "target_scale": target, "scales": rows, "target_holds_on_curves": holds,
           "note": "Curves are ILLUSTRATIVE unless a vendor curve is supplied; the stored model is unchanged."}
    cache.write_text(json.dumps(out, indent=1))
    return out
