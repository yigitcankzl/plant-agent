"""Extended-period (time-series) EPANET runs on an existing .inp model, compared with measured SCADA-like series.

Observations are a CSV in canonical form: column `hours` (time since start) and one column per series named
`<kind>:<id>:<quantity>_<unit>`, kind in node|tank|link|pump, quantity/unit in pressure_m, head_m, level_m, flow_lps,
demand_lps. Changes to the model are explicit and logged, the way a calibration log is kept:
  {"target": "pipe:ID" | "pipes:*" | "pipes:PREFIX*" | "pump:ID" | "tank:ID" | "demand:*" | "pattern:ID",
   "attr": "roughness" | "diameter" | "speed" | "init_level" | "base_demand" | "multipliers", "op": "set" | "scale", "value": x}
"""
import csv
import fnmatch
import math
import os
import tempfile
from functools import lru_cache

import numpy as np
import wntr

UNIT = {"m": 1.0, "lps": 1000.0, "psi": 1 / 0.70307, "ft": 1 / 0.3048, "gpm": 15850.32, "m3h": 3600.0}


def load_observations(path):
    rows = list(csv.DictReader(open(path)))
    hours = np.array([float(r["hours"]) for r in rows])
    return {k: (hours, np.array([float(r[k]) if r[k] not in ("", "nan") else np.nan for r in rows]))
            for k in rows[0] if k != "hours"}


@lru_cache(maxsize=4)
def _base(inp):
    return open(inp).read()


def _model(inp):
    with tempfile.NamedTemporaryFile("w", suffix=".inp", delete=False) as f:
        f.write(_base(inp))
    try:
        return wntr.network.WaterNetworkModel(f.name)
    finally:
        os.unlink(f.name)


def _targets(wn, target):
    kind, _, name = target.partition(":")
    pools = {"pipe": wn.pipe_name_list, "pipes": wn.pipe_name_list, "pump": wn.pump_name_list, "tank": wn.tank_name_list,
             "demand": wn.junction_name_list, "pattern": wn.pattern_name_list, "junction": wn.junction_name_list}
    names = [n for n in pools[kind] if fnmatch.fnmatch(n, name)]
    if not names:
        raise KeyError(f"{target}: no match")
    return kind, names


def apply(wn, changes):
    for ch in changes or []:
        kind, names = _targets(wn, ch["target"])
        op, v = ch.get("op", "set"), ch["value"]
        f = (lambda old: old * v) if op == "scale" else (lambda old: v)
        for n in names:
            if kind in ("pipe", "pipes"):
                link = wn.get_link(n)
                setattr(link, ch["attr"], f(getattr(link, ch["attr"])))
            elif kind == "pump":
                wn.get_link(n).base_speed = f(wn.get_link(n).base_speed)
            elif kind == "tank":
                setattr(wn.get_node(n), ch["attr"], f(getattr(wn.get_node(n), ch["attr"])))
            elif kind in ("demand", "junction"):
                for d in wn.get_node(n).demand_timeseries_list:
                    d.base_value = f(d.base_value)
            elif kind == "pattern":
                pat = wn.get_pattern(n)
                pat.multipliers = np.array(v) if op == "set" and isinstance(v, list) else pat.multipliers * v
    return wn


def simulate(inp, changes=(), duration_h=24, step_min=None):
    wn = apply(_model(inp), changes)
    wn.options.time.duration = int(duration_h * 3600)
    if step_min:
        wn.options.time.hydraulic_timestep = wn.options.time.report_timestep = int(step_min * 60)
    with tempfile.TemporaryDirectory() as t:
        res = wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=os.path.join(t, "eps"))
    return wn, res


def series(wn, res, key):
    """Simulated values for an observation column, in the column's unit, indexed by hours."""
    kind, eid, qty = key.split(":")
    quantity, unit = qty.rsplit("_", 1)
    scale = UNIT[unit]
    hours = res.node["head"].index.values / 3600
    if kind in ("node", "tank"):
        if quantity == "level":
            v = res.node["pressure"][eid].values  # tank pressure = water depth above the tank bottom
        else:
            v = res.node[{"pressure": "pressure", "head": "head", "demand": "demand"}[quantity]][eid].values
    else:
        v = res.link["flowrate"][eid].values
    return hours, v * scale


def compare(wn, res, obs):
    out = []
    for key, (t_obs, y_obs) in obs.items():
        try:
            t_sim, y_sim = series(wn, res, key)
        except KeyError:
            out.append({"series": key, "error": "element not in model"}); continue
        m = (t_obs >= t_sim[0]) & (t_obs <= t_sim[-1]) & ~np.isnan(y_obs)
        if not m.any():
            continue
        y = np.interp(t_obs[m], t_sim, y_sim)
        err = y - y_obs[m]
        spread = np.nanstd(y_obs[m]) or 1.0
        out.append({"series": key, "n": int(m.sum()), "rmse": round(float(np.sqrt(np.mean(err ** 2))), 3),
                    "bias": round(float(np.mean(err)), 3), "obs_mean": round(float(np.mean(y_obs[m])), 3),
                    "nse": round(float(1 - np.mean(err ** 2) / spread ** 2), 3)})
    return out


def run(inp, obs_path=None, changes=(), duration_h=24, samples=6):
    """One extended-period run; returns fit statistics per observed series and a few sampled values."""
    wn, res = simulate(inp, changes, duration_h)
    out = {"duration_h": duration_h, "changes": list(changes)}
    obs = load_observations(obs_path) if obs_path else {}
    if obs:
        out["fit"] = compare(wn, res, obs)
        rel = [abs(f["rmse"]) / (abs(f["obs_mean"]) or 1) for f in out["fit"] if "rmse" in f]
        out["mean_relative_rmse"] = round(float(np.mean(rel)), 4) if rel else None
    hours = res.node["head"].index.values / 3600
    idx = np.linspace(0, len(hours) - 1, min(samples, len(hours))).astype(int)
    out["tanks"] = {t: [round(float(res.node["pressure"][t].values[i]), 2) for i in idx] for t in wn.tank_name_list[:6]}
    out["pumps"] = {p: [round(float(res.link["flowrate"][p].values[i]) * 1000, 1) for i in idx] for p in wn.pump_name_list[:6]}
    out["sample_hours"] = [round(float(hours[i]), 2) for i in idx]
    out["units"] = "tanks: water depth m; pumps: flow l/s"
    return out


def fit(inp, obs_path, params, duration_h=24, base_changes=(), max_evals=120):
    """Calibrate scale factors on chosen parameter groups to minimise mean relative RMSE (bounded Nelder-Mead)."""
    from scipy.optimize import minimize
    obs = load_observations(obs_path)

    def score(x):
        ch = list(base_changes) + [{**p, "op": "scale", "value": float(np.clip(v, p["min"], p["max"]))} for p, v in zip(params, x)]
        try:
            wn, res = simulate(inp, ch, duration_h)
        except Exception:
            return 1e6
        f = [r for r in compare(wn, res, obs) if "rmse" in r]
        return float(np.mean([r["rmse"] / (abs(r["obs_mean"]) or 1) for r in f])) if f else 1e6

    x0 = [1.0 for _ in params]
    before = score(x0)
    r = minimize(score, x0, method="Nelder-Mead", options={"maxfev": max_evals, "xatol": 1e-3, "fatol": 1e-5})
    best = [{**p, "op": "scale", "value": round(float(np.clip(v, p["min"], p["max"])), 4)} for p, v in zip(params, r.x)]
    return {"before_mean_relative_rmse": round(before, 4), "after_mean_relative_rmse": round(float(r.fun), 4),
            "evaluations": int(r.nfev), "fitted_changes": best,
            "note": "Scale factors fitted by Nelder-Mead on mean relative RMSE over all observed series."}


if __name__ == "__main__":
    # Self-check on EPANET's Net1 (shipped with WNTR): synthetic "measurements" from a model with rougher pipes,
    # then the fit must recover a roughness scale close to the truth.
    net1 = os.path.join(os.path.dirname(wntr.__file__), "..", "examples", "networks", "Net1.inp")
    if not os.path.exists(net1):
        import glob
        net1 = (glob.glob(os.path.join(os.path.dirname(wntr.__file__), "**", "Net1.inp"), recursive=True) or [None])[0]
    assert net1, "Net1.inp not found"
    truth = [{"target": "pipes:*", "attr": "roughness", "op": "scale", "value": 0.8}]
    wn, res = simulate(net1, truth, 24)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        keys = ["tank:2:level_m", "node:22:pressure_m", "pump:9:flow_lps"]
        cols = {k: series(wn, res, k.replace("pump:", "link:")) for k in keys}
        f.write("hours," + ",".join(k.replace("pump:", "link:") for k in keys) + "\n")
        for i, h in enumerate(cols[keys[0]][0]):
            f.write(f"{h}," + ",".join(f"{cols[k][1][i]:.4f}" for k in keys) + "\n")
    r0 = run(net1, f.name)
    fr = fit(net1, f.name, [{"target": "pipes:*", "attr": "roughness", "min": 0.5, "max": 1.5}], max_evals=40)
    os.unlink(f.name)
    print(r0["mean_relative_rmse"], fr)
    assert fr["after_mean_relative_rmse"] < fr["before_mean_relative_rmse"]
    assert abs(fr["fitted_changes"][0]["value"] - 0.8) < 0.08, fr
    print("ok")
