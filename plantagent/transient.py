"""K-202 start-up on the salt MVR plant: a lumped dynamic screen, not a rigorous plant dynamic simulation.

One vapour volume (evaporator vapour space + suction duct) at saturation temperature; its pressure follows the mass
balance  d(rho V)/dt = boil-up - K-201 flow - K-202 forward flow,  with density proportional to pressure (isothermal,
anchored at the DWSIM suction density). Discharge pressure is held at the documented 3.08 bar (the heater's condensing
side), so each machine sees the head of P_d/P_s. K-201 runs at fixed speed on its curve; K-202 soft-starts on a
variable-speed drive, then a PI controller on suction pressure sets its speed; an anti-surge recycle keeps K-202's
own flow at least 10 % above its surge line. Boil-up ramps from today's rated flow to the combined design's flow at the
target. Curves come from cases/<case>/curves.json (plantagent/curves.py); every parameter that is not documented is
ILLUSTRATIVE and listed in the result.
ponytail: explicit Euler on one pressure state with a first-order speed drive; a dynamic simulator (holdups, heater
dynamics, valve and check-valve behaviour, trip logic) replaces this for detailed design.
"""
from .curves import Curve, head_kJ_kg

DEFAULTS = {  # ILLUSTRATIVE unless stated
    "V_m3": 600.0,             # evaporator vapour space + suction duct
    "P_set_bar": 1.70,         # suction pressure set point = model's evaporator pressure (documented, Table I)
    "P_d_bar": 3.08,           # discharge (heater condensing) pressure, model value
    "rho_ref": 0.9697,         # kg/m3 at P_set, DWSIM suction density
    "T_in_C": 115.15,          # suction temperature, model value
    "P_low_bar": 1.55, "P_high_bar": 1.85,  # allowed suction band
    "t_start_s": 10.0,         # K-202 start command
    "n_min": 0.70,             # VSD minimum speed reached by the soft start
    "ramp_pct_s": 1.0,         # VSD speed ramp limit, % per second
    "t_load0_s": 120.0, "t_load1_s": 600.0,  # boil-up ramp from today's rate to the target
    "Kp": 2.0, "Ki": 0.02,     # PI: speed fraction per unit relative pressure error; integral per second
    "asc_max_q": 0.6,
    "load_margin": 1.03,       # loaded K-202 keeps its curve peak 3 % above the header head (minimum loaded speed)          # anti-surge valve capacity as a fraction of K-202's design flow
    "motor_kW": 2400.0,        # K-202 provisional motor rating (proposal)
    "t_end_s": 1200.0, "dt_s": 0.05,
}


def run(curve_201, curve_202, G0_kg_h, G1_kg_h, **params):
    p = {**DEFAULTS, **params}
    c1, c2 = Curve(curve_201), Curve(curve_202)
    V, Pset, Pd, rho_ref, dt = p["V_m3"], p["P_set_bar"], p["P_d_bar"], p["rho_ref"], p["dt_s"]
    rho = lambda P: rho_ref * P / Pset  # noqa: E731
    P = Pset
    inv0 = rho(P) * V
    n2, integ, pi_on, loaded = 0.0, 0.0, False, False
    peak = max(c2.h)
    sums = {"G": 0.0, "m1": 0.0, "m2": 0.0}
    rows, steps = [], int(p["t_end_s"] / dt)
    worst = {"P_min": P, "P_max": P, "surge_margin_min_pct": None, "recycle_max_q": 0.0, "kW_max": 0.0, "asc_short": False,
             "k201_surge": False}
    for i in range(steps + 1):
        t = i * dt
        f = min(1.0, max(0.0, (t - p["t_load0_s"]) / (p["t_load1_s"] - p["t_load0_s"])))
        G = (G0_kg_h + f * (G1_kg_h - G0_kg_h)) / 3600
        H = head_kJ_kg(Pd / P, p["T_in_C"], c1.k, c1.M)
        q1 = c1.flow_at_head(H) or 0.0
        if q1 == 0.0:
            worst["k201_surge"] = True
        m1 = rho(P) * q1 / 3600
        # K-202: soft start to n_min, then the PI sets speed (rate-limited)
        if t >= p["t_start_s"]:
            if not pi_on:
                n_cmd = p["n_min"]
                if n2 >= p["n_min"] - 1e-9:
                    pi_on = True
            if pi_on:
                e = (P - Pset) / Pset
                integ += e * dt
                n_raw = p["n_min"] + p["Kp"] * e + p["Ki"] * integ
                # once K-202 delivers forward flow its speed must keep the curve peak above the header head
                # (+ load margin), or it falls back onto recycle and hunts
                n_lo = max(p["n_min"], (p["load_margin"] * H / (c2.h_d * peak)) ** 0.5) if loaded else p["n_min"]
                n_cmd = min(1.0, max(n_lo, n_raw))
                if n_cmd != n_raw:  # anti-windup by back-calculation: the integral tracks the clamped command
                    integ = (n_cmd - p["n_min"] - p["Kp"] * e) / p["Ki"]
            step = p["ramp_pct_s"] / 100 * dt
            n2 = min(n2 + step, n_cmd) if n_cmd > n2 else max(n2 - step, n_cmd)
        q2f = (c2.flow_at_head(H, n2) or 0.0) if n2 > 0 else 0.0
        loaded = loaded or q2f > 0
        qs = c2.surge_m3_h(n2) or 0.0
        q2_total = max(q2f, 1.1 * qs) if n2 > 0 else 0.0
        recycle = q2_total - q2f
        if recycle > p["asc_max_q"] * c2.q_d:
            worst["asc_short"] = True
        m2 = rho(P) * q2f / 3600
        h2 = H if q2f > 0 else c2.head(1.1 * qs, n2) if n2 > 0 else 0.0  # on full recycle the machine runs at its own curve
        eff2 = c2.eff_pct(q2_total, n2) if n2 > 0 else 100.0
        kW2 = rho(P) * q2_total / 3600 * h2 / (eff2 / 100) if n2 > 0 else 0.0
        kW1 = m1 * H / (c1.eff_pct(q1) / 100) if q1 else 0.0
        if n2 > 0 and q2f > 0 and qs:
            sm = (1 - qs / q2f) * 100
            worst["surge_margin_min_pct"] = sm if worst["surge_margin_min_pct"] is None else min(worst["surge_margin_min_pct"], sm)
        worst["recycle_max_q"] = max(worst["recycle_max_q"], recycle)
        worst["kW_max"] = max(worst["kW_max"], kW2)
        if i % int(2 / dt) == 0:
            rows.append({"t_s": round(t, 1), "P_s_bar": round(P, 4), "boilup_t_h": round(G * 3.6, 2), "K201_t_h": round(m1 * 3.6, 2),
                         "K202_t_h": round(m2 * 3.6, 2), "K202_recycle_m3_h": round(recycle, 0), "K202_speed_pct": round(n2 * 100, 2),
                         "K202_kW": round(kW2, 0), "K201_kW": round(kW1, 0)})
        if i == steps:
            break
        sums["G"] += G * dt; sums["m1"] += m1 * dt; sums["m2"] += m2 * dt
        P += (G - m1 - m2) * dt / (V * rho_ref / Pset)
        worst["P_min"], worst["P_max"] = min(worst["P_min"], P), max(worst["P_max"], P)
    inv1 = rho(P) * V
    balance_err = abs((inv1 - inv0) - (sums["G"] - sums["m1"] - sums["m2"])) / max(sums["G"], 1e-9)
    band = 0.005 * Pset
    late = [r for r in rows if r["t_s"] >= p["t_end_s"] - 60]
    settled = all(abs(r["P_s_bar"] - Pset) <= band for r in late)
    out_of_band = [r["t_s"] for r in rows if abs(r["P_s_bar"] - Pset) > band]
    checks = [
        {"check": "suction pressure stays in the allowed band", "value": [round(worst["P_min"], 4), round(worst["P_max"], 4)],
         "limit": [p["P_low_bar"], p["P_high_bar"]], "unit": "bar",
         "pass": p["P_low_bar"] <= worst["P_min"] and worst["P_max"] <= p["P_high_bar"]},
        {"check": "no surge: K-202 recycle within anti-surge valve capacity, K-201 stays on its curve",
         "value": round(worst["recycle_max_q"], 0), "limit": round(p["asc_max_q"] * c2.q_d, 0), "unit": "m3/h recycle",
         "pass": not worst["asc_short"] and not worst["k201_surge"]},
        {"check": "K-202 motor power vs rating", "value": round(worst["kW_max"], 0), "limit": p["motor_kW"], "unit": "kW",
         "pass": worst["kW_max"] <= p["motor_kW"]},
        {"check": "suction pressure settles within ±0.5 % of set point in the last 60 s", "value": round(rows[-1]["P_s_bar"], 4),
         "limit": Pset, "unit": "bar", "pass": settled},
    ]
    return {"method": "lumped vapour-volume mass balance, curves from curves.json, PI on suction pressure, explicit Euler "
                      f"(dt {dt} s); a screening model, not a rigorous dynamic simulation",
            "params": p, "illustrative": [k for k in DEFAULTS if k not in ("P_set_bar", "P_d_bar", "rho_ref", "T_in_C")],
            "boilup_kg_h": [G0_kg_h, G1_kg_h], "checks": checks, "status": "pass" if all(c["pass"] for c in checks) else "fail",
            "settling_time_s": (out_of_band[-1] + 2) if out_of_band else 0.0,
            "forward_surge_margin_min_pct": round(worst["surge_margin_min_pct"], 1) if worst["surge_margin_min_pct"] is not None else None,
            "mass_balance_rel_error": balance_err, "series": rows}


def k202_startup(w, save=True):
    """The salt case's K-202 start-up: boil-up from K-201's documented rated suction to the combined design's compressor
    suction at the target (from curves.evaluate, DWSIM). Saved as an analysis artifact with a chart."""
    import json
    from . import artifacts, charts, curves
    ev = curves.evaluate(w)
    if ev.get("error"):
        return ev
    ov = curves.overlay(w.name)["units"]
    if not {"K-201", "K-202"} <= set(ov):
        return {"error": "the start-up screen needs curves for K-201 and K-202 (salt_mvr)"}
    tgt = ev["scales"][f"{ev['target_scale']:.2f}"]
    G1 = sum(c["value"] for c in tgt["checks"] if c["id"] == "K-201" and "capacity" in c["check"])  # group volumetric total
    G1_kg_h = G1 * DEFAULTS["rho_ref"]
    G0_kg_h = 226800.0  # K-201 rated suction, US 5,366,514 Table I
    r = run(ov["K-201"], ov["K-202"], G0_kg_h, G1_kg_h)
    r["boilup_source"] = ("start: K-201 documented rated suction 226.8 t/h (Table I); end: combined design's compressor "
                          "suction at the target, DWSIM (curves.evaluate)")
    if not save:
        return r
    t = [x["t_s"] for x in r["series"]]
    p = r["params"]
    svg = charts.panels_svg("K-202 start-up and ramp to 120 % (lumped screen, ILLUSTRATIVE parameters)", t, [
        {"title": "Suction pressure", "unit": "bar", "series": {"P suction": [x["P_s_bar"] for x in r["series"]]},
         "lines": {"low limit": p["P_low_bar"], "high limit": p["P_high_bar"], "set point": p["P_set_bar"]}},
        {"title": "Flows", "unit": "t/h", "series": {"boil-up": [x["boilup_t_h"] for x in r["series"]],
                                                     "K-201": [x["K201_t_h"] for x in r["series"]],
                                                     "K-202 forward": [x["K202_t_h"] for x in r["series"]]}},
        {"title": "K-202 drive", "unit": "% speed / MW", "series": {"speed %": [x["K202_speed_pct"] for x in r["series"]],
                                                                   "power MW x10": [x["K202_kW"] / 100 for x in r["series"]]},
         "lines": {"motor rating x10": p["motor_kW"] / 100}},
    ])
    meta = artifacts.save(w.name, "analysis", "K-202 start-up transient", {"transient.json": json.dumps(r, indent=1), "transient.svg": svg},
                          by="plantagent.transient", sources=["cases/salt_mvr/curves.json (ILLUSTRATIVE)", "US 5,366,514 Table I"],
                          summary=f"{r['status'].upper()}: " + "; ".join(f"{c['check']}: {'ok' if c['pass'] else 'FAIL'}" for c in r["checks"]))
    r["artifact"] = meta["id"]
    return r
