"""Troubleshooting from a symptom, the way an engineer does it: list every plausible cause, make the model reproduce the
symptom under each one, and keep the cause that also agrees with the OTHER measurements. Deterministic, no LLM.

Each hypothesis moves one model parameter (fouling = lower U, cooling water short = lower utility flow, ...). The
parameter is fitted so the model reproduces the symptom; the hypothesis is then scored by how well that fitted model
matches every other observation. A cause that needs an implausible parameter, or that contradicts the other readings,
ranks low. Only the readings a hypothesis explicitly doubts are left out of its score (a short-flow hypothesis says the
flow meter is wrong; thermometers still count).

CLI demo: python -m plantagent.diagnose
"""
import json
import math
from pathlib import Path

from . import process
from .plant import patch

ROOT = Path(__file__).resolve().parent.parent


def value(res, path):
    """'streams.<id>.<q>' or 'units.<id>.<q>' from a process.run result."""
    kind, oid, q = path.split(".", 2)
    return (res.get(kind) or {}).get(oid, {}).get(q)


def hypotheses_for(spec, hx, side="hot", names=None):
    """The usual causes when an exchanger's process outlet runs out of spec. names: {stream or unit id: readable name}
    (PlantWorkspace.names()) so hypotheses read "Cooling water to H1007 short of flow" instead of a stream id."""
    out = _hypotheses(spec, hx, side)
    for h in out:
        for k, v in sorted((names or {}).items(), key=lambda kv: -len(kv[0])):
            h["name"] = h["name"].replace(k, v)
    return out


def _hypotheses(spec, hx, side):
    u = next(x for x in spec["units"] if x["id"] == hx)
    util_side = "cold" if side == "hot" else "hot"
    util_in, proc_in = u[util_side][0], u[side][0]
    feeds = spec["feeds"]
    out = [{"name": f"{hx} fouled (lower heat-transfer coefficient)", "path": f"units.{hx}.U_W_m2K",
            "lo": 0.2 * u["U_W_m2K"], "hi": 1.5 * u["U_W_m2K"], "action": f"check {hx} approach temperatures; plan a clean"}]
    if util_in in feeds:
        f = feeds[util_in]
        out += [{"name": f"{util_in} short of flow (blocked strainer, throttled valve, weak pump)", "path": f"feeds.{util_in}.m3_h",
                 "lo": 0.2 * f["m3_h"], "hi": 1.5 * f["m3_h"], "doubts": [f"streams.{util_in}.m3_h"],
                 "action": "check the utility strainer, valve position and pump discharge pressure"},
                {"name": f"{util_in} supply too warm (cooling tower or chiller)", "path": f"feeds.{util_in}.T_C",
                 "lo": f["T_C"] - 10, "hi": f["T_C"] + 20, "action": "check the utility header temperature at its source"}]
    if proc_in in feeds:  # only when the process inlet is itself a feed of the model
        f = feeds[proc_in]
        out += [{"name": "process flow higher than metered", "path": f"feeds.{proc_in}.m3_h", "lo": 0.5 * f["m3_h"], "hi": 2.0 * f["m3_h"],
                 "doubts": [f"streams.{proc_in}.m3_h"], "action": "cross-check the process flow meter against a tank level change"}]
    else:  # trace the process inlet back to the model feed it comes from
        prod = next((k for k, f in feeds.items() if not f.get("utility")), None)
        if prod:
            f = feeds[prod]
            out += [{"name": "process flow higher than metered", "path": f"feeds.{prod}.m3_h", "lo": 0.5 * f["m3_h"], "hi": 2.0 * f["m3_h"],
                     "doubts": [f"streams.{prod}.m3_h"], "action": "cross-check the process flow meter against a tank level change"},
                    {"name": "process arriving hotter", "path": f"feeds.{prod}.T_C", "lo": f["T_C"] - 15, "hi": f["T_C"] + 25,
                     "action": "check the upstream unit's outlet temperature"}]
    return out


def fit(spec, scale, h, symptom):
    """Parameter value at which the model reproduces the symptom (bisection; None if it cannot within the range)."""
    def g(x):
        r = process.run(patch(spec, [{"path": h["path"], "value": x}]), scale)
        v = value(r, symptom["path"])
        return (v - symptom["value"]) if v is not None and not r["errors"] else None, r
    glo, _ = g(h["lo"])
    ghi, _ = g(h["hi"])
    if glo is None or ghi is None or glo * ghi > 0:
        return None, None
    lo, hi = h["lo"], h["hi"]
    for _ in range(16):
        mid = (lo + hi) / 2
        gm, _ = g(mid)
        if gm is None:
            return None, None
        lo, hi = (mid, hi) if (gm > 0) == (glo > 0) else (lo, mid)
    x = (lo + hi) / 2
    return x, g(x)[1]


def diagnose(spec, symptom, observations, hypotheses, scale=1.0):
    """symptom: {path, value, name}; observations: [{path, value, name, sigma}] (sigma = measurement uncertainty)."""
    base = process.run(spec, scale)
    rows = []
    for h in hypotheses:
        x, res = fit(spec, scale, h, symptom)
        if x is None:
            rows.append({**h, "fitted": None, "score": None, "verdict": "cannot reproduce the symptom within a plausible range"})
            continue
        used, sq = [], 0.0
        for o in observations:
            if o["path"] in (h.get("doubts") or []):
                continue  # this hypothesis says that very reading is off (e.g. a flow meter); all other readings count
            m = value(res, o["path"])
            if m is None:
                continue
            z = (m - o["value"]) / o.get("sigma", 0.5)
            sq += z * z
            used.append({"name": o.get("name", o["path"]), "measured": o["value"], "model": round(m, 2), "z": round(z, 1)})
        cur = (spec_value(spec, h["path"]))
        rows.append({**h, "fitted": round(x, 2), "current": cur, "change_pct": round((x / cur - 1) * 100, 1) if cur else None,
                     "score": round(math.sqrt(sq / max(1, len(used))), 2), "checks": used})
    ok = sorted([r for r in rows if r["score"] is not None], key=lambda r: r["score"])
    for i, r in enumerate(ok):
        r["verdict"] = ("most likely: agrees with the other readings" if i == 0 and r["score"] < 2 else
                        "consistent" if r["score"] < 2 else "contradicted by the other readings")
    consistent = [r for r in ok if r["score"] < 2]
    # more than one cause fits: name the field checks that tell them apart, cheapest first, before anything is changed
    nxt = [f"{r['name']}: {r['action']}" for r in consistent] if len(consistent) > 1 else []
    return {"symptom": symptom, "baseline_model_value": value(base, symptom["path"]), "ranked": ok + [r for r in rows if r["score"] is None],
            "consistent": len(consistent), "field_checks_to_separate": nxt}


def spec_value(spec, path):
    kind, oid, f = path.split(".", 2)
    obj = next((u for u in spec["units"] if u["id"] == oid), None) if kind == "units" else spec.get(kind, {}).get(oid)
    return (obj or {}).get(f)


def demo():
    """H1007's product outlet runs hot. Fouling or short cooling water? The cooling-water return temperature tells:
    fouling moves less heat (return cools), a short flow heats the little water there is (return warms)."""
    spec = json.loads((ROOT / "runs" / "ws" / "chem_c01" / "model.json").read_text())["spec"]
    truth = patch(spec, [{"path": "feeds.s47130.m3_h", "value": 13.0}])  # the hidden cause: cooling water at 13 instead of 20
    t = process.run(truth, 1.0)
    obs = lambda sid, q, name, sig: {"path": f"streams.{sid}.{q}", "value": round(t["streams"][sid][q], 2), "name": name, "sigma": sig}  # noqa: E731
    symptom = obs("s47123a", "T_C", "H1007 product out", 0.2)
    observations = [obs("s47131", "T_C", "cooling water return", 0.3), obs("s47130", "T_C", "cooling water supply", 0.3),
                    obs("s47122", "T_C", "H1007 product in", 0.3),
                    obs("s47121", "m3_h", "product flow (meter)", 0.2), obs("s47130", "m3_h", "cooling water flow (meter, reads high)", 0.3)]
    observations[-1]["value"] = 20.0  # the cooling-water meter still says 20: the reading the short-flow hypothesis doubts
    return diagnose(spec, symptom, observations, hypotheses_for(spec, "H1007"))


if __name__ == "__main__":
    r = demo()
    for h in r["ranked"]:
        print(f"{h.get('score')!s:>6}  {h['name']}: fitted {h.get('fitted')} (now {h.get('current')})  -> {h.get('verdict')}")
    print("to separate:", r["field_checks_to_separate"])
    assert "short of flow" in r["ranked"][0]["name"], "the cooling-water return must point to the short flow, not to fouling"
    assert any("fouled" in h["name"] and "contradicted" in h["verdict"] for h in r["ranked"])
    out = ROOT / "runs" / "ws" / "chem_c01" / "diagnose_demo.json"
    out.write_text(json.dumps(r, indent=1))
    print("ok")
