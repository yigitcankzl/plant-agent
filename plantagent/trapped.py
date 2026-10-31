"""Blocked-in liquefied-gas segment heated by ambient heat leak: pressure against time (incident reconstruction).

The segment is a rigid volume holding a fixed mass of LNG (or any liquefied gas) between closed valves. Heat leaks in at a
steady rate per metre; the contents follow an isochore: while a vapour space remains the pressure stays near the vapour
pressure, once the liquid has expanded to fill the pipe the pressure climbs steeply (hydraulic expansion). Thermodynamics
are DWSIM Peng-Robinson PT flashes (plantagent/process.py 'props'): at each temperature the pressure whose overall density
equals the trapped density, and the internal energy there. Length cancels: mass and heat both scale with it.

`scale` multiplies the documented time blocked in (spec['hours']), so the workspace slider moves time and 'capacity' is the
time multiple at which the first limit is reached. Spec: see SPEC_HELP.
"""
import hashlib
import json
import math
from pathlib import Path

from . import process

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "runs" / "cache" / "trapped"
PSI = 14.5038           # psi per bar
ATM_PSI = 14.696
WALL_CP = 0.35          # kJ/kgK, austenitic stainless at cryogenic temperature (screening value)
STEEL_KG_M3 = 7900

SPEC_HELP = (
    "Blocked-in segment spec: {fluid: {compounds: [DWSIM names], x: {name: mole fraction}}, "
    "feeds: {<id>: {P_psig: initial pressure, fill_fraction: liquid volume fraction at the start}}, "
    "units: [{id, type: 'pipe_segment', in: <feed id>, od_m, wall_m, length_m, heat_leak_W_m: heat ingress per metre}, "
    "{id, type: 'relief_valve', protects: <segment id>, set_psig, isolated: true|false}, "
    "{id, type: 'valve', isolates: <segment id>, closed: true|false}], hours: documented time blocked in, "
    "limits: {<segment id>: {design_psig, burst_psig}}}. scale multiplies hours. Checks: segment pressure vs design and vs "
    "burst. A relief valve that is not isolated holds the pressure at its set point; an open isolating valve vents the "
    "segment to the rest of the system (pressure stays at the start).")


def available():
    return process.available()


def _props(fluid, points):
    return process._call({"op": "props", "spec": fluid, "points": points})["points"]


def _bubble(fluid, T_C):
    return process._call({"op": "bubble", "spec": fluid, "T_C": [T_C]})["points"][0]["bubble_P_bar"]


def _u(p):  # internal energy, kJ/kg
    return p["enthalpy_kJ_kg"] - p["P_bar"] * 100 / p["density_kg_m3"]


PGRID = [400 ** (i / 119) for i in range(120)]  # 1 to 400 bar


def isochore(fluid, P0_bar, fill):
    """[(T_C, P_bar, du_kJ_kg)] along the isochore of a segment filled to `fill` (liquid volume fraction) at its bubble
    point P0. Cached on disk: about a hundred DWSIM flashes per point."""
    key = hashlib.sha1(json.dumps([fluid, round(P0_bar, 3), round(fill, 4), PGRID[-1]], sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text())
    lo, hi = -200.0, 0.0  # bubble temperature at P0
    for _ in range(18):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _bubble(fluid, mid) < P0_bar else (lo, mid)
    T0 = round(hi, 2)
    liq, vap = _props(fluid, [{"T_C": T0, "P_bar": P0_bar + 0.3}, {"T_C": T0 + 3, "P_bar": P0_bar}])
    rho = fill * liq["density_kg_m3"] + (1 - fill) * vap["density_kg_m3"]
    u0 = None
    curve, T, prev = [], T0, 0.0
    while T < 80:
        pts = _props(fluid, [{"T_C": T, "P_bar": p} for p in PGRID])
        hit = None
        for a, b in zip(pts, pts[1:]):  # the first bracket at or above the last pressure: the isochore only rises
            if a["density_kg_m3"] <= rho <= b["density_kg_m3"] and b["P_bar"] >= prev:
                w = (rho - a["density_kg_m3"]) / ((b["density_kg_m3"] - a["density_kg_m3"]) or 1)
                hit = (a["P_bar"] + w * (b["P_bar"] - a["P_bar"]), _u(a) + w * (_u(b) - _u(a)))
                break
        if hit is None:
            break
        prev = hit[0]
        u0 = hit[1] if not curve else u0  # energy reference: the first point of the same interpolation
        curve.append([round(T, 2), round(hit[0], 3), round(hit[1] - u0, 3)])
        if hit[0] > PGRID[-1] * 0.9:
            break
        T += 2.0
    out = {"T0_C": T0, "rho_kg_m3": round(rho, 2), "rho_liquid_kg_m3": liq["density_kg_m3"], "curve": curve}
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out))
    return out


def _segment(spec):
    seg = next((u for u in spec.get("units") or [] if u.get("type") == "pipe_segment"), None)
    if not seg:
        raise ValueError("spec needs one unit of type pipe_segment")
    return seg


def history(spec, iso=None):
    """Hours -> (P_bar, T_C) for the blocked-in segment with no relief: [(h, P_bar, T_C)], plus the inputs used."""
    seg = _segment(spec)
    feed = (spec.get("feeds") or {}).get(seg.get("in")) or {}
    P0 = (float(feed.get("P_psig", 0)) + ATM_PSI) / PSI
    fill = float(feed["fill_fraction"])
    iso = iso or isochore(spec["fluid"], P0, fill)
    od, wall = float(seg["od_m"]), float(seg["wall_m"])
    area = math.pi * (od - 2 * wall) ** 2 / 4
    wall_kg_m = math.pi * (od - wall) * wall * STEEL_KG_M3
    q = float(seg["heat_leak_W_m"])
    rows = []
    for T, P, du in iso["curve"]:  # energy per metre into fluid and pipe wall -> hours at the heat leak
        e = iso["rho_kg_m3"] * area * du + wall_kg_m * WALL_CP * (T - iso["T0_C"])
        h = e * 1000 / q / 3600
        if rows and h < rows[-1][0]:  # flash noise near the critical point: time only moves forward
            continue
        rows.append((h, P, T))
    return rows, {"P0_bar": P0, "fill": fill, "area_m2": area, "mass_kg_m": iso["rho_kg_m3"] * area, "T0_C": iso["T0_C"],
                  "rho_kg_m3": iso["rho_kg_m3"], "heat_leak_W_m": q}


def _at(rows, h):
    if h <= rows[0][0]:
        return rows[0][1], rows[0][2]
    for (h1, P1, T1), (h2, P2, T2) in zip(rows, rows[1:]):
        if h1 <= h <= h2:
            w = (h - h1) / ((h2 - h1) or 1)
            return P1 + w * (P2 - P1), T1 + w * (T2 - T1)
    return None, None  # beyond the computed isochore (past 400 bar): treat as off the curve


def _liquid_full_h(rows):
    """The knee: first step where the pressure rise per hour jumps (the vapour space is gone)."""
    slopes = [((P2 - P1) / ((h2 - h1) or 1e-9), h1, (P2 - P1) / max(P1, 1e-6)) for (h1, P1, _), (h2, P2, _) in zip(rows, rows[1:])]
    for i in range(3, len(slopes)):
        before = max(s for s, _, _ in slopes[i - 3:i])  # vapour-pressure rise speeds up gently; liquid-full is a jump
        if slopes[i][0] > 5 * max(before, 1e-6) and slopes[i][2] > 0.2:
            return round(slopes[i][1], 1)
    return None


def run(spec, scale=1.0):
    seg = _segment(spec)
    sid = seg["id"]
    hours = float(spec.get("hours") or 0) * float(scale)
    lim = (spec.get("limits") or {}).get(sid) or {}
    psv = next((u for u in spec["units"] if u.get("type") == "relief_valve" and u.get("protects") == sid), None)
    valves = [u for u in spec["units"] if u.get("type") == "valve" and u.get("isolates") == sid]
    blocked = bool(valves) and all(v.get("closed") for v in valves)
    rows, basis = history(spec)
    errors, notes = [], []
    if not blocked:
        P, T = basis["P0_bar"], basis["T0_C"]
        notes.append("an isolating valve is open: the segment vents to the connected system and stays at its start pressure")
    else:
        P, T = _at(rows, hours)
        if P is None:  # past the top of the computed isochore: at least that pressure, already far over any rating
            P, T = rows[-1][1], rows[-1][2]
            notes.append(f"after {hours:.1f} h the pressure is above the computed range: at least {P * PSI - ATM_PSI:,.0f} psig")
    lifted = False
    if psv and not psv.get("isolated") and P is not None:
        set_bar = (float(psv["set_psig"]) + ATM_PSI) / PSI
        if P > set_bar:
            P, lifted = set_bar, True
            notes.append(f"{psv['id']} lifts at {psv['set_psig']} psig and holds the segment there (LNG vented)")
    psig = P * PSI - ATM_PSI
    checks = []
    for k, label in (("design_psig", "pressure vs design pressure"), ("burst_psig", "pressure vs estimated burst pressure")):
        if lim.get(k):
            checks.append({"id": sid, "check": label, "value": round(psig, 1), "limit": float(lim[k]), "unit": "psig",
                           "utilisation": round(psig / float(lim[k]), 4)})
    full = _liquid_full_h(rows)
    exceed = {}
    for k in ("design_psig", "burst_psig"):
        if lim.get(k) and blocked and not (psv and not psv.get("isolated")):
            target = (float(lim[k]) + ATM_PSI) / PSI
            exceed[k.replace("_psig", "_reached_h")] = next((round(h, 1) for h, p, _ in rows if p >= target), None)
    units = {sid: {"type": "pipe_segment", "hours": round(hours, 1), "P_bar": round(P, 2), "P_psig": round(psig, 1),
                   "T_C": round(T, 1), "liquid_full_h": full, "blocked_in": blocked,
                   "mass_kg_per_m": round(basis["mass_kg_m"], 1), "start_T_C": basis["T0_C"], **exceed}}
    if psv:
        units[psv["id"]] = {"type": "relief_valve", "isolated": bool(psv.get("isolated")), "lifted": lifted,
                            "set_psig": psv.get("set_psig")}
    for v in valves:
        units[v["id"]] = {"type": "valve", "closed": bool(v.get("closed"))}
    series = [[round(h, 2), round(p * PSI - ATM_PSI, 1)] for h, p, _ in rows]
    return {"scale": scale, "errors": errors, "notes": notes, "units": units,
            "streams": {seg.get("in") or "LNG": {"T_C": round(T, 1), "P_bar": round(P, 2), "kg_h": 0.0}},
            "checks": checks, "series_h_psig": series, "basis": {k: (round(v, 4) if isinstance(v, float) else v)
                                                                  for k, v in basis.items()}}


def capacity(spec):
    """Time multiple (of spec['hours']) at which the first limit reaches 100 %."""
    def worst(scale):
        r = run(spec, scale)
        ch = [c for c in r["checks"] if "utilisation" in c]
        return (max(ch, key=lambda c: c["utilisation"]) if ch else None), ch, r["errors"]
    out = process._capacity_search(worst)
    if out.get("note", "").startswith("multiple of the current feed flows"):
        out["note"] = "multiple of the documented time blocked in at which the first stated limit reaches 100 %"
    return out
