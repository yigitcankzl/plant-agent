"""EPANET hydraulics (via WNTR) for a plant section described as a small JSON network.

The spec uses the source document's units: "units": "US" (ft, in, gpm, hp, psi) or "SI" (m, mm, l/s, kW, bar).
The agent never computes hydraulics itself; it builds a network and reads these results.
"""
import math
import os
import tempfile

import numpy as np
import wntr

US = {"len": 0.3048, "dia": 0.0254, "flow": 6.30902e-5, "power": 745.7, "press": 6894.76,
      "len_u": "ft", "dia_u": "in", "flow_u": "gpm", "power_u": "hp", "press_u": "psi"}
SI = {"len": 1.0, "dia": 0.001, "flow": 0.001, "power": 1000.0, "press": 1e5,
      "len_u": "m", "dia_u": "mm", "flow_u": "lps", "power_u": "kw", "press_u": "bar"}
RHO_G = 1000 * 9.81

SPEC_HELP = {
    "units": "'US' (default) or 'SI'. Field suffixes below use US names; for SI use _m, _mm, _lps, _kw instead of _ft, _in, _gpm, _hp.",
    "reservoirs": "[{id, head_ft}] fixed water levels (river, wet well, basin, clearwell, terminal reservoir)",
    "junctions": "[{id, elev_ft}] connection points; pressure is reported at each",
    "pipes": "[{id, from, to, length_ft, diameter_in, c_factor=120, minor_k=0, closed=false}]",
    "pumps": "[{id, from, to, rated_gpm, rated_head_ft | curve:[[gpm, ft], ...], motor_hp, speed=1.0, on=true, "
             "efficiency=0.80 | eff_curve:[[gpm, fraction], ...], motor_eff=0.95, centerline_ft (for NPSH available)}]. A single rated point lets EPANET "
             "derive the curve (shutoff 133% head, max 200% flow); give `curve` when the document has curve data. "
             "speed scales the curve by the affinity laws.",
}


def _u(spec):
    return SI if spec.get("units", "US").upper() == "SI" else US


def _f(d, key, u, default=None):
    """Read a field by its US or SI name."""
    names = {"head": ("head_ft", "head_m"), "elev": ("elev_ft", "elev_m"), "length": ("length_ft", "length_m"),
             "diameter": ("diameter_in", "diameter_mm"), "rated_flow": ("rated_gpm", "rated_lps"),
             "rated_head": ("rated_head_ft", "rated_head_m"), "motor": ("motor_hp", "motor_kw")}[key]
    for n in names:
        if n in d:
            return d[n]
    if default is not None:
        return default
    raise KeyError(f"missing {names[0 if u is US else 1]} in {d.get('id', d)}")


def build(spec):
    if not spec.get("junctions"):
        raise ValueError("EPANET needs at least one junction. Typical layout: reservoir -> pump -> junction -> pipe -> reservoir.")
    u = _u(spec)
    wn = wntr.network.WaterNetworkModel()
    for r in spec.get("reservoirs", []):
        wn.add_reservoir(r["id"], base_head=_f(r, "head", u) * u["len"])
    for j in spec.get("junctions", []):
        wn.add_junction(j["id"], elevation=_f(j, "elev", u, 0) * u["len"])
    for p in spec.get("pipes", []):
        wn.add_pipe(p["id"], p["from"], p["to"], length=_f(p, "length", u) * u["len"],
                    diameter=_f(p, "diameter", u) * u["dia"], roughness=p.get("c_factor", 120),
                    minor_loss=p.get("minor_k", 0),
                    initial_status="CLOSED" if p.get("closed") else "OPEN")
    for p in spec.get("pumps", []):
        pts = p.get("curve") or [[_f(p, "rated_flow", u), _f(p, "rated_head", u)]]
        wn.add_curve(p["id"] + "_curve", "HEAD", [(q * u["flow"], h * u["len"]) for q, h in pts])
        wn.add_pump(p["id"], p["from"], p["to"], "HEAD", p["id"] + "_curve", speed=p.get("speed", 1.0))
        if not p.get("on", True):
            wn.get_link(p["id"]).initial_status = wntr.network.LinkStatus.Closed
    wn.options.time.duration = 0
    return wn


def _efficiency(p, q, speed):
    if "eff_curve" in p:
        xs, ys = zip(*sorted(p["eff_curve"]))
        return float(np.interp(q / speed, xs, ys))  # affinity: efficiency follows Q/N
    return p.get("efficiency", 0.80)


def run(spec):
    u = _u(spec)
    wn = build(spec)
    with tempfile.TemporaryDirectory() as tmp:  # keep EPANET scratch files out of the repo
        res = wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=os.path.join(tmp, "run"))
    flow = res.link["flowrate"].iloc[0]
    head = res.node["head"].iloc[0]
    pressure = res.node["pressure"].iloc[0]
    F, P, L = u["flow_u"], u["power_u"], u["len_u"]

    out = {"units": "SI" if u is SI else "US", "pumps": [], "pipes": [], "junctions": [], "warnings": []}
    single = [p["id"] for p in spec.get("pumps", []) if "curve" not in p]
    if single:  # EPANET derives the whole curve from one point: fine for screening, not for firm capacity sign-off
        out["curve_basis"] = f"single rated point (EPANET 3-point curve: shutoff 133%, runout 200%) for {', '.join(single)}: screening only"
    if any("eff_curve" not in p and "efficiency" not in p for p in spec.get("pumps", [])):
        out["efficiency_basis"] = "assumed 0.80 where no efficiency was given: power and energy are indicative"
    total_kw = 0.0
    for p in spec.get("pumps", []):
        on = p.get("on", True)
        q_m3s = abs(float(flow[p["id"]]))
        tdh_m = float(head[p["to"]]) - float(head[p["from"]])
        q = q_m3s / u["flow"]
        speed = p.get("speed", 1.0)
        rated = p.get("curve", [[_f(p, "rated_flow", u, 1)]])[-1][0] if "curve" in p else _f(p, "rated_flow", u)
        eff = _efficiency(p, q, speed) if on else 0
        shaft_w = RHO_G * q_m3s * tdh_m / eff if on and eff else 0.0
        elec_kw = shaft_w / p.get("motor_eff", 0.95) / 1000
        total_kw += elec_kw
        row = {"id": p["id"], "on": on, f"flow_{F}": round(q, 1), f"tdh_{L}": round(tdh_m / u["len"], 2),
               "speed": speed, "efficiency": round(eff, 3), f"shaft_{P}": round(shaft_w / u["power"], 1),
               f"motor_{P}": p.get("motor_hp", p.get("motor_kw")), "electric_kw": round(elec_kw, 1)}
        if "curve" not in p:
            row["pct_of_rated_flow"] = round(100 * q / rated) if on else 0
            if on and q > 1.2 * rated:
                out["warnings"].append(f"{p['id']}: {100*q/rated:.0f}% of rated flow (far right on curve)")
        motor = p.get("motor_hp", p.get("motor_kw"))
        if on and motor and shaft_w / u["power"] > motor:
            out["warnings"].append(f"{p['id']}: shaft power {shaft_w/u['power']:.0f} {P} exceeds {motor} {P} motor")
        out["pumps"].append(row)
    for p in spec.get("pipes", []):
        q_m3s = abs(float(flow[p["id"]]))
        d_m = _f(p, "diameter", u) * u["dia"]
        v = q_m3s / (math.pi / 4 * d_m ** 2)
        out["pipes"].append({"id": p["id"], f"flow_{F}": round(q_m3s / u["flow"], 1),
                             f"velocity_{'fps' if u is US else 'mps'}": round(v / u["len"], 2)})
    for j in spec.get("junctions", []):
        out["junctions"].append({"id": j["id"], f"pressure_{u['press_u']}": round(float(pressure[j["id"]]) * RHO_G / u["press"], 2)})
    q_total = sum(abs(float(flow[p["id"]])) for p in spec.get("pumps", []))
    out[f"total_pumped_{F}"] = round(q_total / u["flow"], 1)
    if u is US:
        out["total_pumped_mgd"] = round(q_total / u["flow"] / 694.444, 3)
    out["total_electric_kw"] = round(total_kw, 1)
    if q_total > 0:
        out["specific_energy_kwh_per_ml"] = round(total_kw / (q_total * 3.6), 1)  # kW / (ML/h)
    return out


def firm_capacity(spec):
    """Firm capacity: the station output with the largest pump out of service, solved in EPANET for every
    single-pump outage (the worst one governs)."""
    pumps = [p for p in spec.get("pumps", []) if p.get("on", True)]
    if len(pumps) < 2:
        raise ValueError("firm capacity needs at least two pumps in service")
    cases = []
    for p in pumps:
        variant = {**spec, "pumps": [{**x, "on": False} if x["id"] == p["id"] else x for x in spec["pumps"]]}
        r = run(variant)
        cases.append({"out_of_service": p["id"], "total_pumped_mgd" if _u(spec) is US else "total_pumped_lps":
                      r.get("total_pumped_mgd", r.get("total_pumped_lps")), "warnings": r["warnings"]})
    key = "total_pumped_mgd" if _u(spec) is US else "total_pumped_lps"
    worst = min(cases, key=lambda c: c[key])
    return {"firm": worst[key], "unit": key.split("_")[-1], "governing_outage": worst["out_of_service"], "cases": cases,
            "all_pumps": run(spec).get(key)}


def write_inp(spec, path):
    wntr.network.write_inpfile(build(spec), str(path), units="GPM" if _u(spec) is US else "LPS")


def velocity(flow, diameter=None, area=None, openings=1, units="US"):
    """Mean velocity. US: flow in mgd, diameter in inches or area in ft2 -> fps. SI: l/s, mm or m2 -> m/s."""
    if units.upper() == "SI":
        a = area if area is not None else math.pi / 4 * (diameter / 1000) ** 2
        return round(flow / 1000 / (a * openings), 3)
    a = area if area is not None else math.pi / 4 * (diameter / 12) ** 2
    return round(flow * 1.5472 / (a * openings), 3)


if __name__ == "__main__":
    # 18 mgd in a 29.5" ID pipe is ~5.9 fps, as Roseburg Table 4-1 states.
    assert abs(velocity(18, diameter=29.5) - 5.87) < 0.05
    spec = {"reservoirs": [{"id": "river", "head_ft": 0}, {"id": "basin", "head_ft": 40}],
            "junctions": [{"id": "j"}],
            "pipes": [{"id": "main", "from": "j", "to": "basin", "length_ft": 500, "diameter_in": 29.5}],
            "pumps": [{"id": "P2", "from": "river", "to": "j", "rated_gpm": 4200, "rated_head_ft": 49, "motor_hp": 75}]}
    r = run(spec)
    print(r)
    assert 4000 < r["pumps"][0]["flow_gpm"] < 6000
    # SI spec with a multipoint curve and an efficiency curve; slowing a pump whose BEP is right of duty lowers efficiency.
    si = {"units": "SI", "reservoirs": [{"id": "low", "head_m": 0}, {"id": "high", "head_m": 40}],
          "junctions": [{"id": "d", "elev_m": 0}],
          "pipes": [{"id": "rm", "from": "d", "to": "high", "length_m": 2650, "diameter_mm": 900}],
          "pumps": [{"id": "A", "from": "low", "to": "d", "curve": [[0, 60], [600, 48], [1000, 30]],
                     "eff_curve": [[200, 0.5], [600, 0.8], [900, 0.86]], "motor_kw": 400}]}
    full, slow = run(si), run({**si, "pumps": [{**si["pumps"][0], "speed": 0.9}]})
    assert slow["pumps"][0]["efficiency"] < full["pumps"][0]["efficiency"]
    with tempfile.TemporaryDirectory() as d:
        write_inp(spec, f"{d}/m.inp")
        assert wntr.network.WaterNetworkModel(f"{d}/m.inp").num_pumps == 1
    print("ok", full["specific_energy_kwh_per_ml"], slow["specific_energy_kwh_per_ml"])
