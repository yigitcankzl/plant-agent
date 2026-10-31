"""Heat-exchanger detail rating (thermal-hydraulic screening) for one shell-and-tube or plate exchanger of a case.

Duty, flows, temperatures and pressures come from a DWSIM solve of the workspace model at a throughput multiple (with an
answer's proposal applied when asked). Geometry comes from cases/<case>/hx_geometry.json, where every field names its
source and ILLUSTRATIVE marks what the P&ID / data sheet do not give. Correlations are Caleb Bell's `ht` and `fluids`:

  tube side    Gnielinski (1976) via ht.conv_internal.turbulent_Gnielinski (Dittus-Boelter shown as a cross-check);
               Darcy friction factor fluids.friction_factor (Clamond solution of Colebrook)
  shell side   liquid: Bell-Delaware (Taborek, HEDH 3.3.11): Zukauskas ideal tube bank (ht.Nu_Zukauskas_Bejan) times
               ht's Bell correction factors Jc, Jl, Jb, Js, Jr; Kern (1950) h shown as a cross-check; dP by ht.dP_Kern
               condensing (horizontal bundle): Nusselt (1916) film on a horizontal tube with Kern's N^-1/6 row
               correction; dP = 50 % of the vapour-only Kern value (Kern 1950)
  plate        Martin (1996) Nu (ht.Nu_plate_Martin) and Darcy friction (fluids.friction_plate_Martin_1999), geometry
               from fluids.PlateExchanger, port loss 1.4 velocity heads (Shah & Focke 1988)
  overall      1/U_o = 1/h_o + R_fo + d_o ln(d_o/d_i)/(2 k_w) + (d_o/d_i)(R_fi + 1/h_i); F from ht.F_LMTD_Fakheri

Properties: water and steam IAPWS-95 / IAPWS 2008 viscosity / IAPWS 2011 conductivity (`chemicals`); NaCl brine
Laliberte & Cooper (2004) density and Laliberte (2009) cp (WaterTAP parameters, plantagent/brine.py), Laliberte (2007)
viscosity, Sharqawy et al. (2010) conductivity (extrapolated above 160 g/kg); other liquids DWSIM liquid properties.
Screening only: not a vendor thermal design (HTRI/Aspen EDR) and not a mechanical design.

Usage: python -m plantagent.hxdetail <case> <tag> [scale] [answer]
"""
import copy
import json
import math

from . import artifacts, brine, process
from .plant import ROOT, patch

G = 9.80665
FT2 = 0.17611  # m2K/W per h ft2 F/Btu
RANGES = {"gnielinski": (2300, 5e6), "zukauskas": (1, 2e6), "martin": (1, 1e5)}


def _n(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return "to confirm" if v in (None, "") else str(v)
    r = float(f"{v:.4g}")
    return str(int(r)) if r == int(r) and abs(r) < 1e15 else str(r)


# ---------------------------------------------------------------- properties
def water(T_C, P_bar):
    from chemicals import iapws95_properties, iapws95_rho, k_IAPWS, mu_IAPWS
    T, P = T_C + 273.15, P_bar * 1e5
    rho = iapws95_rho(T, P)
    mu = mu_IAPWS(T, rho)
    return {"rho": rho, "mu": mu, "k": k_IAPWS(T, rho), "cp": iapws95_properties(T, P)[5],
            "source": "IAPWS-95 (density, cp), IAPWS 2008 viscosity, IAPWS 2011 conductivity (chemicals)"}


def saturated_steam(P_bar):
    """Saturation state for a condensing side: liquid film and vapour properties, latent heat."""
    from chemicals import iapws95_Tsat, iapws95_properties, iapws95_rhog_sat, iapws95_rhol_sat, k_IAPWS, mu_IAPWS
    P = P_bar * 1e5
    T = iapws95_Tsat(P)
    rl, rg = iapws95_rhol_sat(T), iapws95_rhog_sat(T)
    liq, vap = iapws95_properties(T - 0.01, P), iapws95_properties(T + 0.01, P)
    return {"T_C": T - 273.15, "rho_l": rl, "rho_g": rg, "mu_l": mu_IAPWS(T, rl), "mu_g": mu_IAPWS(T, rg),
            "k_l": k_IAPWS(T, rl), "cp_l": liq[5], "hfg": vap[3] - liq[3],
            "source": "IAPWS-95 saturation (chemicals), IAPWS 2008/2011 transport properties"}


def nacl_brine(T_C, x):
    """Saturated or sub-saturated NaCl brine (no crystals): density, viscosity, conductivity, cp."""
    t = T_C
    rho_w = 999.9 + 2.034e-2 * t - 6.162e-3 * t ** 2 + 2.261e-5 * t ** 3 - 4.657e-8 * t ** 4  # Sharqawy 2010 eq. 8
    c0, c1, c2, c3, c4 = -0.00433, 0.06471, 1.01660, 0.014624, 3315.6  # Laliberte & Cooper 2004 NaCl (WaterTAP params)
    v_app = (x + c2 + c3 * t) / ((x * c0 + c1) * math.exp(1e-6 * (t + c4) ** 2))
    rho = 1 / (x * v_app + (1 - x) / rho_w)
    mu_w = (t + 246) / ((0.05594 * t + 5.2842) * t + 137.37)  # mPa s, Laliberte 2007 eq. for water
    v1, v2, v3, v4, v5, v6 = 16.221788633396, 1.32293086770011, 1.48485985010431, 0.00746912559657377, 30.7802007540575, 2.05826852322558
    mu_i = math.exp((v1 * x ** v2 + v3) / (v4 * t + 1)) / (v5 * x ** v6 + 1)
    mu = math.exp((1 - x) * math.log(mu_w) + x * math.log(mu_i)) * 1e-3
    S = 1000 * x  # g/kg; Sharqawy et al. 2010 eq. 13 (Jamieson & Tudhope), valid to 160 g/kg
    k = 1e-3 * 10 ** (math.log10(240 + 0.0002 * S) + 0.434 * (2.3 - (343.5 + 0.037 * S) / (t + 273.15))
                      * (1 - (t + 273.15) / (647 + 0.03 * S)) ** (1 / 3))
    return {"rho": rho, "mu": mu, "k": k, "cp": brine.cp(t, x) * 1000,
            "source": f"NaCl brine x={x:.4f}: Laliberte & Cooper 2004 density, Laliberte 2007 viscosity, Laliberte 2009 cp "
                      f"(WaterTAP parameters), Sharqawy 2010 conductivity" + (" (extrapolated above 160 g/kg)" if S > 160 else "")}


def dwsim_liquid(spec, feed, T_C, P_bar):
    f = spec["feeds"][feed]
    pk = spec.get("package") or "NRTL"
    pt = process.props(spec["compounds"], f["x"], [{"T_C": T_C, "P_bar": P_bar}], pk)["points"][0]["liquid"]
    return {"rho": pt["density_kg_m3"], "mu": pt["viscosity_Pa_s"], "k": pt["k_W_mK"], "cp": pt["cp_kJ_kgK"] * 1000,
            "source": f"DWSIM {pk} liquid properties of feed {feed} composition"}


def _props(fluid, spec, T_C, P_bar, T_in_C):
    m = fluid["model"]
    if m == "iapws_water":
        return water(T_C, P_bar)
    if m == "nacl_brine":
        x = brine.x_sat(T_in_C) if fluid.get("x_NaCl", "saturated") == "saturated" else float(fluid["x_NaCl"])
        return nacl_brine(T_C, x)
    if m == "dwsim":
        return dwsim_liquid(spec, fluid["feed"], T_C, P_bar)
    raise ValueError(f"unknown fluid model {m!r}")


# ---------------------------------------------------------------- correlations
def tube_side(m_kg_s, p, g, n_tubes):
    """Velocity, Re, h and pressure drop inside the tubes."""
    import fluids
    from ht.conv_internal import turbulent_Dittus_Boelter, turbulent_Gnielinski
    do, di, L, Np = g["tube_od_m"], g["tube_od_m"] - 2 * g["tube_wall_m"], g["tube_length_m"], int(g["tube_passes"])
    a = n_tubes / Np * math.pi * di ** 2 / 4
    v = m_kg_s / (p["rho"] * a)
    Re = p["rho"] * v * di / p["mu"]
    Pr = p["cp"] * p["mu"] / p["k"]
    fd = fluids.friction_factor(Re, eD=g.get("tube_roughness_m", 1.5e-6) / di)
    if Re >= 2300:
        Nu, method = turbulent_Gnielinski(Re, Pr, fd), "Gnielinski (ht.turbulent_Gnielinski)"
    else:
        Nu, method = 3.66, "laminar fully developed, constant wall temperature (Nu 3.66)"
    h = Nu * p["k"] / di
    dP = (fd * L * Np / di + 2.5 * Np) * p["rho"] * v ** 2 / 2
    return {"di": di, "flow_area": a, "v": v, "Re": Re, "Pr": Pr, "fd": fd, "Nu": Nu, "h": h, "method": method,
            "h_dittus_boelter": turbulent_Dittus_Boelter(Re, Pr, heating=True) * p["k"] / di if Re > 1e4 else None,
            "dP": dP}


def bundle(g, n_tubes):
    """Outer tube limit and shell diameters; given shell ID wins, otherwise HEDH bundle + clearance."""
    from ht.hx import DBundle_for_Ntubes_HEDH, shell_clearance
    Dotl = DBundle_for_Ntubes_HEDH(n_tubes, g["tube_od_m"], g["tube_pitch_m"], int(g.get("layout_angle_deg", 30)))
    if g.get("shell_id_m"):
        return Dotl, g["shell_id_m"], "given"
    return Dotl, Dotl + shell_clearance(DBundle=Dotl), "derived"


def shell_liquid(m_kg_s, p, g, n_tubes, Ds, Dotl):
    """Bell-Delaware shell-side h with ht's correction factors, Kern h as a cross-check, Kern dP."""
    from ht.conv_tube_bank import (Nu_Zukauskas_Bejan, baffle_correction_Bell, baffle_leakage_Bell, bundle_bypassing_Bell,
                                   dP_Kern, laminar_correction_Bell, unequal_baffle_spacing_Bell)
    do, pt, B, Bc, L = g["tube_od_m"], g["tube_pitch_m"], g["baffle_spacing_m"], g["baffle_cut"], g["tube_length_m"]
    ang = int(g.get("layout_angle_deg", 30))
    p_par = pt * (0.866 if ang == 30 else 0.707 if ang == 45 else 1.0)  # pitch parallel to flow
    p_eff = pt * (0.707 if ang == 45 else 1.0)
    Dctl = Dotl - do
    th_ctl = 2 * math.acos(max(-1.0, min(1.0, Ds * (1 - 2 * Bc) / Dctl)))
    Fw = th_ctl / (2 * math.pi) - math.sin(th_ctl) / (2 * math.pi)
    Fc = 1 - 2 * Fw
    th_ds = 2 * math.acos(1 - 2 * Bc)
    Sm = B * ((Ds - Dotl) + Dctl / p_eff * (pt - do))
    Ssb = math.pi * Ds * g.get("shell_baffle_clearance_m", 0.0048) / 2 * (1 - th_ds / (2 * math.pi))
    Ltb = g.get("tube_baffle_clearance_m", 0.0008)
    Stb = math.pi / 4 * ((do + Ltb) ** 2 - do ** 2) * n_tubes * (1 - Fw)
    Sb = B * (Ds - Dotl)
    Nc = Ds * (1 - 2 * Bc) / p_par
    Ncw = 0.8 / p_par * (Ds * Bc - (Ds - Dctl) / 2)
    Nb = max(1, int(round(L / B)) - 1)
    Re = do * m_kg_s / (p["mu"] * Sm)
    Pr = p["cp"] * p["mu"] / p["k"]
    Nu = Nu_Zukauskas_Bejan(Re, Pr, tube_rows=max(1, int(round(Nc))), pitch_parallel=p_par, pitch_normal=pt)
    h_ideal = Nu * p["k"] / do
    J = {"Jc": baffle_correction_Bell(Fc), "Jl": baffle_leakage_Bell(Ssb, Stb, Sm),
         "Jb": bundle_bypassing_Bell(Sb / Sm, int(g.get("sealing_strip_pairs", 0)), max(1, int(round(Nc))), laminar=Re < 100),
         "Js": unequal_baffle_spacing_Bell(Nb, B), "Jr": laminar_correction_Bell(Re, int(round(Nc + Ncw))) if Re < 100 else 1.0}
    h = h_ideal * J["Jc"] * J["Jl"] * J["Jb"] * J["Js"] * J["Jr"]
    # Kern (1950): equivalent diameter (triangular), crossflow area at the shell centre line
    De = 1.10 / do * (pt ** 2 - 0.917 * do ** 2) if ang == 30 else 1.27 / do * (pt ** 2 - 0.785 * do ** 2)
    As = (pt - do) * Ds * B / pt
    Re_k = m_kg_s / As * De / p["mu"]
    h_kern = 0.36 * p["k"] / De * Re_k ** 0.55 * Pr ** (1 / 3)
    dP = dP_Kern(m_kg_s, p["rho"], p["mu"], Ds, B, pt, do, Nb)
    return {"Re": Re, "Pr": Pr, "Nu_ideal": Nu, "h_ideal": h_ideal, **J, "h": h, "h_kern": h_kern, "Re_kern": Re_k,
            "v_cross": m_kg_s / (p["rho"] * Sm), "Sm": Sm, "Nc": Nc, "Nb": Nb, "Fc": Fc, "dP": dP,
            "method": "Bell-Delaware: Zukauskas ideal bank (ht.Nu_Zukauskas_Bejan) x Jc Jl Jb Js Jr (ht.*_Bell); dP ht.dP_Kern"}


def shell_condensing(m_kg_s, sat, g, n_tubes, Ds, Dotl, T_wall_C):
    """Nusselt film condensation on a horizontal bundle with Kern's row correction; dP 50 % of vapour-only Kern."""
    from ht.conv_tube_bank import dP_Kern
    do, pt = g["tube_od_m"], g["tube_pitch_m"]
    dT = max(0.05, sat["T_C"] - T_wall_C)
    hfg = sat["hfg"] + 0.68 * sat["cp_l"] * dT  # Rohsenow (1956) modified latent heat
    h1 = 0.725 * (sat["rho_l"] * (sat["rho_l"] - sat["rho_g"]) * G * hfg * sat["k_l"] ** 3 / (sat["mu_l"] * do * dT)) ** 0.25
    Nr = max(1.0, 2 / 3 * Dotl / pt)
    h = h1 * Nr ** (-1 / 6)
    Nb = max(1, int(round(g["tube_length_m"] / g["baffle_spacing_m"])) - 1)
    dP = 0.5 * dP_Kern(m_kg_s, sat["rho_g"], sat["mu_g"], Ds, g["baffle_spacing_m"], pt, do, Nb)
    return {"h": h, "h_single_tube": h1, "Nr": Nr, "dT_film": dT, "dP": dP, "Nb": Nb,
            "method": "Nusselt (1916) horizontal tube, Kern N^-1/6 row correction; dP 0.5 x vapour-only ht.dP_Kern"}


def lmtd(Th_in, Th_out, Tc_in, Tc_out):
    d1, d2 = Th_in - Tc_out, Th_out - Tc_in
    if d1 <= 0 or d2 <= 0:
        raise ValueError(f"temperature cross: hot {Th_in}->{Th_out} C, cold {Tc_in}->{Tc_out} C")
    return d1 if abs(d1 - d2) < 1e-9 else (d1 - d2) / math.log(d1 / d2)


# ---------------------------------------------------------------- rating
def _vals(entry):
    g = {k: v["value"] if isinstance(v, dict) else v for k, v in (entry.get("geometry") or {}).items()}
    src = {k: v.get("source", "") if isinstance(v, dict) else "" for k, v in (entry.get("geometry") or {}).items()}
    return g, src


def rate(entry, sides, Q_kW, spec, condition="fouled"):
    """Pure rating: entry = hx_geometry.json item, sides = {'hot': {'in': stream, 'out': stream, 'kg_h'}, 'cold': ...}
    with stream dicts {T_C, P_bar, kg_h, vapour_frac}. Returns rows [(quantity, value, unit, source)], numbers, notes."""
    g, gsrc = _vals(entry)
    rows, notes, num = [], [], {"Q_kW": Q_kW}
    row = lambda q, v, u, s: rows.append((q, v, u, s))  # noqa: E731
    fouling = entry.get("fouling_m2K_W") or {}
    Rf = {k: (v["value"] if condition == "fouled" else 0.0) for k, v in fouling.items()}
    rf_src = {k: (v["source"] if condition == "fouled" else "clean condition: no fouling allowance") for k, v in fouling.items()}
    hot, cold = sides["hot"], sides["cold"]
    for k, s in (("hot", hot), ("cold", cold)):
        row(f"{k} side in / out", f"{_n(s['in']['T_C'])} / {_n(s['out']['T_C'])}", "°C", s["in"].get("source", "DWSIM solve"))
        row(f"{k} side flow", _n(s["in"]["kg_h"]), "kg/h", s["in"].get("source", "DWSIM solve"))
    if entry["type"] == "plate":
        return _rate_plate(entry, g, gsrc, sides, Q_kW, spec, Rf, rf_src, rows, num, notes, condition)
    tube_k = entry.get("tube_side", "cold")
    shell_k = "hot" if tube_k == "cold" else "cold"
    tube, shell = sides[tube_k], sides[shell_k]
    do, L = g["tube_od_m"], g["tube_length_m"]
    n_tubes = g.get("n_tubes") or round(g["area_m2"] / (math.pi * do * L))
    A_inst = n_tubes * math.pi * do * L
    row("tubes", _n(n_tubes), "", gsrc.get("n_tubes") or f"area / (π d_o L) = {_n(g['area_m2'])} / (π × {_n(do)} × {_n(L)})")
    for k in ("tube_od_m", "tube_wall_m", "tube_length_m", "tube_passes", "tube_pitch_m", "baffle_spacing_m", "baffle_cut", "tube_k_W_mK"):
        if k in g:
            row(k, _n(g[k]), "", gsrc[k])
    Dotl, Ds, how = bundle(g, n_tubes)
    row("bundle diameter (outer tube limit)", _n(Dotl), "m", "ht.hx.DBundle_for_Ntubes_HEDH")
    row("shell inside diameter", _n(Ds), "m", gsrc.get("shell_id_m") if how == "given" else "bundle + ht.hx.shell_clearance (derived)")
    if how == "given" and Dotl > Ds:
        notes.append(f"the tube count from the area needs a {Dotl:.3f} m bundle, larger than the {Ds:.3f} m shell: geometry to confirm")
    # tube side
    t_mean = (tube["in"]["T_C"] + tube["out"]["T_C"]) / 2
    pt_ = _props(entry["fluids"][tube_k], spec, t_mean, tube["in"]["P_bar"], tube["in"]["T_C"])
    if entry["fluids"][tube_k]["model"] == "dwsim" and abs(tube["out"]["T_C"] - tube["in"]["T_C"]) > 1:
        pt_["cp"] = Q_kW * 1000 / (tube["in"]["kg_h"] / 3600 * abs(tube["out"]["T_C"] - tube["in"]["T_C"]))
    ts = tube_side(tube["in"]["kg_h"] / 3600, pt_, g, n_tubes)
    row(f"tube-side properties at {_n(t_mean)} °C", f"ρ {_n(pt_['rho'])} kg/m³, μ {_n(pt_['mu'] * 1e3)} mPa·s, k {_n(pt_['k'])} W/m·K, "
        f"cp {_n(pt_['cp'] / 1e3)} kJ/kg·K", "", pt_["source"])
    row("tube-side velocity", _n(ts["v"]), "m/s", f"m / (ρ × {_n(n_tubes)}/{g['tube_passes']} tubes × π d_i²/4)")
    row("tube-side Re / Pr", f"{_n(ts['Re'])} / {_n(ts['Pr'])}", "", "ρ v d_i / μ; cp μ / k")
    row("tube-side h", _n(ts["h"]), "W/m²K", ts["method"] + f", Darcy f {_n(ts['fd'])} (fluids.friction_factor)")
    if ts["h_dittus_boelter"]:
        row("tube-side h, Dittus-Boelter cross-check", _n(ts["h_dittus_boelter"]), "W/m²K", "ht.turbulent_Dittus_Boelter")
    row("tube-side pressure drop", _n(ts["dP"] / 1e5), "bar", "(f L N_p / d_i + 2.5 N_p) ρ v²/2 (Sinnott, C&R Vol. 6 eq. 12.20)")
    if entry["fluids"][tube_k]["model"] == "nacl_brine":
        notes.append("crystal slurry in the circulating brine is not included in the tube-side properties (clear-liquor basis)")
        if not tube["in"].get("source"):  # a solved brine stream (water stand-in): the rise with brine cp differs
            rise = Q_kW * 1000 / (tube["in"]["kg_h"] / 3600 * pt_["cp"])
            num["brine_rise_K"] = rise
            row("brine temperature rise at the solved duty with brine cp", _n(rise), "K",
                f"Q / (m cp_brine); the DWSIM water stand-in gives {_n(tube['out']['T_C'] - tube['in']['T_C'])} K")
    # shell side
    kw = g["tube_k_W_mK"]
    Rw = do * math.log(do / ts["di"]) / (2 * kw)
    ratio = do / ts["di"]
    cond = entry["fluids"][shell_k]["model"] == "steam_condensing"
    if cond:
        sat = saturated_steam(shell["in"]["P_bar"])
        row("shell-side saturation temperature", _n(sat["T_C"]), "°C", f"{sat['source']} at {_n(shell['in']['P_bar'])} bar(a)")
        Tw = (sat["T_C"] + t_mean) / 2
        for _ in range(30):  # wall temperature from the series resistances
            ss = shell_condensing(shell["in"]["kg_h"] / 3600, sat, g, n_tubes, Ds, Dotl, Tw)
            q = (sat["T_C"] - t_mean) / (1 / ss["h"] + Rw + ratio / ts["h"])
            Tw = sat["T_C"] - q / ss["h"]
        if shell["in"].get("T_C", 0) > sat["T_C"] + 1:
            notes.append(f"the heating steam arrives superheated ({_n(shell['in']['T_C'])} °C); the desuperheating duty is rated "
                         "at the condensing coefficient (wet-wall condensation), a common screening simplification")
        row("shell-side condensing h", _n(ss["h"]), "W/m²K", ss["method"].split("; ")[0] + f", film ΔT {_n(ss['dT_film'])} K, N_r {_n(ss['Nr'])}")
        Th_in, Th_out = sat["T_C"], shell["out"]["T_C"]
    else:
        s_mean = (shell["in"]["T_C"] + shell["out"]["T_C"]) / 2
        ps = _props(entry["fluids"][shell_k], spec, s_mean, shell["in"]["P_bar"], shell["in"]["T_C"])
        if entry["fluids"][shell_k]["model"] == "dwsim" and abs(shell["out"]["T_C"] - shell["in"]["T_C"]) > 1:
            ps["cp"] = Q_kW * 1000 / (shell["in"]["kg_h"] / 3600 * abs(shell["out"]["T_C"] - shell["in"]["T_C"]))
            ps["source"] += "; cp = Q / (m ΔT) of the DWSIM solve"
        ss = shell_liquid(shell["in"]["kg_h"] / 3600, ps, g, n_tubes, Ds, Dotl)
        row(f"shell-side properties at {_n(s_mean)} °C", f"ρ {_n(ps['rho'])} kg/m³, μ {_n(ps['mu'] * 1e3)} mPa·s, k {_n(ps['k'])} W/m·K, "
            f"cp {_n(ps['cp'] / 1e3)} kJ/kg·K", "", ps["source"])
        row("shell-side crossflow velocity", _n(ss["v_cross"]), "m/s", f"m / (ρ S_m), S_m {_n(ss['Sm'])} m² (Bell-Delaware)")
        row("shell-side Re", _n(ss["Re"]), "", "d_o m / (μ S_m)")
        row("Bell correction factors Jc / Jl / Jb / Js / Jr", " / ".join(_n(ss[k]) for k in ("Jc", "Jl", "Jb", "Js", "Jr")), "",
            "ht.baffle_correction_Bell, baffle_leakage_Bell, bundle_bypassing_Bell, unequal_baffle_spacing_Bell, laminar_correction_Bell")
        row("shell-side h (Bell-Delaware)", _n(ss["h"]), "W/m²K", ss["method"])
        row("shell-side h, Kern cross-check", _n(ss["h_kern"]), "W/m²K", "Kern (1950): 0.36 (k/D_e) Re^0.55 Pr^1/3")
        Th_in, Th_out = (shell if shell_k == "hot" else tube)["in"]["T_C"], (shell if shell_k == "hot" else tube)["out"]["T_C"]
    row("shell-side pressure drop", _n(ss["dP"] / 1e5), "bar", ss["method"].split("; ")[-1])
    Rfo, Rfi = Rf.get("shell", 0.0), Rf.get("tube", 0.0)
    row("fouling, shell / tube", f"{_n(Rfo)} / {_n(Rfi)}", "m²K/W", f"shell: {rf_src.get('shell')}; tube: {rf_src.get('tube')}")
    row("tube wall resistance", _n(Rw), "m²K/W", f"d_o ln(d_o/d_i) / (2 k_w), k_w {_n(kw)} W/m·K")
    U_clean = 1 / (1 / ss["h"] + Rw + ratio / ts["h"])
    U = 1 / (1 / U_clean + Rfo + ratio * Rfi)
    Tc_in, Tc_out = sides["cold"]["in"]["T_C"], sides["cold"]["out"]["T_C"]
    if not cond:
        Th_in, Th_out = sides["hot"]["in"]["T_C"], sides["hot"]["out"]["T_C"]
    dTlm = lmtd(Th_in, Th_out, Tc_in, Tc_out)
    F = 1.0
    if not cond and int(g["tube_passes"]) > 1:
        from ht.hx import F_LMTD_Fakheri
        F = F_LMTD_Fakheri(Th_in, Th_out, Tc_in, Tc_out, shells=1)
    num.update(v_tube=ts["v"], h_tube=ts["h"], h_shell=ss["h"], U_clean=U_clean, U=U, A_inst=A_inst, dP_tube_bar=ts["dP"] / 1e5,
               dP_shell_bar=ss["dP"] / 1e5, LMTD=dTlm, F=F, n_tubes=n_tubes, Re_tube=ts["Re"], tube_k=tube_k)
    return _overall(rows, num, notes, U_clean, U, F, dTlm, Q_kW, A_inst, condition, "outside tube area")


def _overall(rows, num, notes, U_clean, U, F, dTlm, Q_kW, A_inst, condition, basis):
    rows.append(("U clean (correlation)", _n(U_clean), "W/m²K", f"1/U = Σ resistances, {basis}"))
    rows.append((f"U {'in service (with fouling)' if condition == 'fouled' else 'clean condition'}", _n(U), "W/m²K",
                 "1/U = 1/U_clean + fouling" if condition == "fouled" else "clean: no fouling allowance"))
    rows.append(("LMTD / F", f"{_n(dTlm)} / {_n(F)}", "K / -", "counter-current LMTD of the solved temperatures; F ht.F_LMTD_Fakheri (1 for a condensing side or one pass)"))
    A_req = Q_kW * 1000 / (U * F * dTlm)
    A_req_clean = Q_kW * 1000 / (U_clean * F * dTlm)
    rows.append(("duty", _n(Q_kW), "kW", "DWSIM solve"))
    rows.append(("area required (correlation U)", _n(A_req), "m²", "Q / (U F LMTD)"))
    rows.append(("area required, clean", _n(A_req_clean), "m²", "Q / (U_clean F LMTD)"))
    rows.append(("area installed", _n(A_inst), "m²", "geometry"))
    num.update(A_req=A_req, A_req_clean=A_req_clean, U_needed=Q_kW * 1000 / (A_inst * F * dTlm))
    rows.append(("U needed for the solved duty on the installed area", _n(num["U_needed"]), "W/m²K", "Q / (A_installed F LMTD)"))
    return rows, num, notes


def _rate_plate(entry, g, gsrc, sides, Q_kW, spec, Rf, rf_src, rows, num, notes, condition):
    import fluids
    from ht.conv_plate import Nu_plate_Martin
    row = lambda q, v, u, s: rows.append((q, v, u, s))  # noqa: E731
    phi = fluids.plate_enlargement_factor(g["amplitude_m"], g["wavelength_m"])
    plates = int(round(g["area_m2"] / (g["plate_width_m"] * g["plate_length_m"] * phi))) + 2
    pe = fluids.PlateExchanger(g["amplitude_m"], g["wavelength_m"], chevron_angle=g["chevron_angle_deg"], width=g["plate_width_m"],
                               length=g["plate_length_m"], thickness=g["plate_thickness_m"], d_port=g["port_diameter_m"], plates=plates)
    for k in ("plate_width_m", "plate_length_m", "amplitude_m", "wavelength_m", "chevron_angle_deg", "plate_thickness_m", "port_diameter_m", "plate_k_W_mK"):
        row(k, _n(g[k]), "", gsrc[k])
    row("plates (incl. 2 end plates)", plates, "", f"area / (W L φ) + 2, enlargement φ {_n(phi)} (fluids.plate_enlargement_factor)")
    row("hydraulic diameter / channels per side", f"{_n(pe.D_hydraulic)} m / {_n(pe.channels_per_fluid)}", "", "fluids.PlateExchanger")
    res = {}
    for k in ("hot", "cold"):
        s = sides[k]
        T = (s["in"]["T_C"] + s["out"]["T_C"]) / 2
        p = _props(entry["fluids"][k], spec, T, s["in"]["P_bar"], s["in"]["T_C"])
        if entry["fluids"][k]["model"] == "dwsim" and abs(s["out"]["T_C"] - s["in"]["T_C"]) > 1:
            p["cp"] = Q_kW * 1000 / (s["in"]["kg_h"] / 3600 * abs(s["out"]["T_C"] - s["in"]["T_C"]))
            p["source"] += "; cp = Q / (m ΔT) of the DWSIM solve"
        m = s["in"]["kg_h"] / 3600
        v = m / (p["rho"] * pe.channels_per_fluid * pe.A_channel_flow)
        Re = p["rho"] * v * pe.D_hydraulic / p["mu"]
        Pr = p["cp"] * p["mu"] / p["k"]
        Nu = Nu_plate_Martin(Re, Pr, g["chevron_angle_deg"])
        h = Nu * p["k"] / pe.D_hydraulic
        f = fluids.friction_plate_Martin_1999(Re, g["chevron_angle_deg"])
        v_port = m / (p["rho"] * math.pi / 4 * g["port_diameter_m"] ** 2)
        dP = f * pe.length / pe.D_hydraulic * p["rho"] * v ** 2 / 2 + 1.4 * p["rho"] * v_port ** 2 / 2
        res[k] = {"v": v, "Re": Re, "h": h, "dP": dP}
        row(f"{k} properties at {_n(T)} °C", f"ρ {_n(p['rho'])} kg/m³, μ {_n(p['mu'] * 1e3)} mPa·s, k {_n(p['k'])} W/m·K, cp {_n(p['cp'] / 1e3)} kJ/kg·K",
            "", p["source"])
        row(f"{k} channel velocity / Re", f"{_n(v)} m/s / {_n(Re)}", "", "m / (ρ N_ch W b); ρ v D_h / μ")
        row(f"{k} h", _n(h), "W/m²K", "Martin (1996), ht.Nu_plate_Martin")
        row(f"{k} pressure drop", _n(dP / 1e5), "bar", f"Darcy f {_n(f)} (fluids.friction_plate_Martin_1999) x L/D_h + port 1.4 ρ v_port²/2 (v_port {_n(v_port)} m/s)")
    Rw = g["plate_thickness_m"] / g["plate_k_W_mK"]
    row("fouling hot / cold", f"{_n(Rf.get('hot', 0))} / {_n(Rf.get('cold', 0))}", "m²K/W", f"hot: {rf_src.get('hot')}; cold: {rf_src.get('cold')}")
    U_clean = 1 / (1 / res["hot"]["h"] + Rw + 1 / res["cold"]["h"])
    U = 1 / (1 / U_clean + Rf.get("hot", 0) + Rf.get("cold", 0))
    hot, cold = sides["hot"], sides["cold"]
    dTlm = lmtd(hot["in"]["T_C"], hot["out"]["T_C"], cold["in"]["T_C"], cold["out"]["T_C"])
    num.update(v_hot=res["hot"]["v"], v_cold=res["cold"]["v"], h_hot=res["hot"]["h"], h_cold=res["cold"]["h"], U_clean=U_clean, U=U,
               dP_hot_bar=res["hot"]["dP"] / 1e5, dP_cold_bar=res["cold"]["dP"] / 1e5, LMTD=dTlm, F=1.0, plates=plates, A_inst=pe.A_heat_transfer)
    return _overall(rows, num, notes, U_clean, U, 1.0, dTlm, Q_kW, pe.A_heat_transfer, condition, "plate heat-transfer area")


def checks(tag, entry, num, model_U, condition):
    """Screening checks in the process-check format (id, check, value, limit, unit, utilisation, source)."""
    lim = {k: v for k, v in (entry.get("limits") or {}).items()}
    out = []

    def add(check, value, limit, unit, util, source):
        out.append({"id": tag, "check": check, "value": round(value, 4), "limit": round(limit, 4), "unit": unit,
                    "utilisation": round(util, 3), "source": source})
    plate = entry["type"] == "plate"
    vels = [("hot", num["v_hot"]), ("cold", num["v_cold"])] if plate else [(num["tube_k"], num["v_tube"])]
    lo_k, hi_k = ("channel_velocity_min_m_s", "channel_velocity_max_m_s") if plate else ("tube_velocity_min_m_s", "tube_velocity_max_m_s")
    for side, v in vels:
        where = f"{side} channel" if plate else "tube"
        if lo_k in lim:
            add(f"{where} velocity vs minimum", v, lim[lo_k]["value"], "m/s", lim[lo_k]["value"] / max(v, 1e-9), lim[lo_k]["source"])
        if hi_k in lim:
            add(f"{where} velocity vs maximum", v, lim[hi_k]["value"], "m/s", v / lim[hi_k]["value"], lim[hi_k]["source"])
    if num.get("F", 1.0) < 0.999:
        add("LMTD correction factor F vs minimum", num["F"], 0.75, "-", 0.75 / max(num["F"], 1e-6),
            "typical practice: F not below 0.75 for a multi-pass shell (Sinnott, C&R Vol. 6 sec. 12.6); lower means a "
            "temperature cross that needs counter-current flow or shells in series")
    add(f"area required ({condition} correlation U) vs installed", num["A_req"], num["A_inst"], "m2", num["A_req"] / num["A_inst"],
        "Q / (U F LMTD), U from the correlations")
    dps = [("hot", num["dP_hot_bar"], "dP_hot_max_bar"), ("cold", num["dP_cold_bar"], "dP_cold_max_bar")] if plate else \
          [("tube", num["dP_tube_bar"], "dP_tube_max_bar"), ("shell", num["dP_shell_bar"], "dP_shell_max_bar")]
    for side, dp, k in dps:
        if k in lim:
            add(f"{side}-side pressure drop vs allowable", dp, lim[k]["value"], "bar", dp / lim[k]["value"], lim[k]["source"])
    rated = (entry.get("circulation") or {}).get("rated_m3_h")
    if num.get("circulation_m3_h") and rated:
        add("brine circulation needed for the rise limit vs pump rating", num["circulation_m3_h"], rated["value"], "m3/h",
            num["circulation_m3_h"] / rated["value"], rated["source"])
    if "brine_rise_K" in num and "brine_rise_max_K" in lim and not num.get("circulation_m3_h"):
        add("brine temperature rise vs maximum", num["brine_rise_K"], lim["brine_rise_max_K"]["value"], "K",
            num["brine_rise_K"] / lim["brine_rise_max_K"]["value"], lim["brine_rise_max_K"]["source"])
    if model_U:
        dev = abs(model_U / num["U"] - 1) * 100
        add(f"model U {model_U:g} vs correlation U {num['U']:.0f} W/m2K ({condition})", dev, 20.0, "% difference", dev / 20,
            "flag when the model's U differs by more than 20 % from the correlation")
    return out


# ---------------------------------------------------------------- workspace entry point
def geometry(case, tag):
    f = ROOT / "cases" / case / "hx_geometry.json"
    if not f.exists():
        raise ValueError(f"no exchanger geometry for {case} (cases/{case}/hx_geometry.json)")
    data = {k: v for k, v in json.loads(f.read_text()).items() if not k.startswith("_")}
    for k, v in data.items():
        if k == tag or tag in (v.get("aliases") or []):
            return k, v
    raise ValueError(f"no geometry for {tag!r}; exchangers with geometry in this case: {sorted(data)}")


def _get(spec, path):
    cur = spec
    for part in path.split("."):
        if isinstance(cur, list):
            cur = next((u for u in cur if u.get("id") == part), None)
        elif isinstance(cur, dict):
            cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _solve(w, tag, entry, scale, answer, changes=None):
    from . import documents
    if changes is not None:  # a whole design (all verified changes of an answer), solved together
        spec = patch(copy.deepcopy(w.spec), changes)
        scale = float(scale or 1.0)
        return w._solve(spec, scale), scale, f"DWSIM solve of the design at {scale * 100:.0f} %", spec, None
    if answer is not None:
        i, ans = documents._answer(w, answer)
        p = documents._proposal(ans, tag) or documents._proposal(ans, entry.get("model_unit"))
        if not p:
            raise ValueError(f"answer {answer} has no proposal on {tag}; rate the current model (omit answer) instead")
        res, scale, src = documents._proposed(w, i, p, scale)
        return res, scale, src, patch(copy.deepcopy(w.spec), p["changes"]), p
    scale = float(scale or 1.0)
    res, src = documents._current(w, scale)
    return res, scale, src, w.spec, None


def hx_detail(w, tag, scale=None, answer=None, condition=None, save=True, by=None, request=None, changes=None):
    tag, entry = geometry(w.name, tag)
    if not w.built:
        raise ValueError("no model built yet")
    res, scale, src, spec, prop = _solve(w, tag, entry, scale, answer, changes)
    uid = entry.get("model_unit", tag)
    u = next((x for x in spec["units"] if x["id"] == uid), None)
    st, ures = res.get("streams") or {}, ((res.get("units") or {}).get(uid) or {})
    extra, circ_m3_h = [], None
    if u and u.get("type") == "evaporator" and entry.get("circulation"):
        # the model folds the heater into the evaporator body: steam side from the solve, brine circulation from the
        # brine-rise design rule (the flow the heater must carry), compared with the circulation pump's rating
        Q = abs(ures.get("heating_kW") or 0)
        Tb, x = ures["brine_T_C"], ures.get("body_x_NaCl") or brine.x_sat(ures["brine_T_C"])
        entry = copy.deepcopy(entry)
        entry["fluids"]["cold"]["x_NaCl"] = x
        circ = entry["circulation"]
        rise = circ["rise_K"]["value"]
        cp = nacl_brine(Tb + rise / 2, x)["cp"]
        m = Q * 1000 / (cp * rise)
        rho = nacl_brine(Tb, x)["rho"]
        sides = {"hot": {"in": st[u["heating"][0]], "out": st[u["heating"][1]]},
                 "cold": {"in": {"T_C": Tb, "P_bar": 3.0, "kg_h": m * 3600, "source": "V-201 body temperature (solve) + brine-rise limit"},
                          "out": {"T_C": Tb + rise, "P_bar": 3.0, "kg_h": m * 3600}}}
        circ_m3_h = m * 3600 / rho
        extra = [("brine circulation for the rise limit", _n(circ_m3_h), "m³/h",
                  f"Q {_n(Q)} kW / (cp {_n(cp / 1e3)} kJ/kg·K × {_n(rise)} K) / ρ {_n(rho)} kg/m³; rise limit: {circ['rise_K']['source']}"),
                 ("brine inlet (body) temperature / NaCl mass fraction", f"{_n(Tb)} °C / {_n(x)}", "", f"DWSIM solve, {uid} (boiling point elevation included)")]
    elif u and u.get("type") == "hx":
        sides = {k: {"in": st[u[k][0]], "out": st[u[k][1]]} for k in ("hot", "cold")}
        Q = abs(ures.get("duty_kW") or 0)
    else:
        raise ValueError(f"model unit {uid} is not a heat exchanger (or an evaporator heater with circulation data) in the current model")
    if not Q:
        raise ValueError(f"the solve has no duty for {uid}")
    condition = condition or ("clean" if prop and "clean" in (prop.get("title") or "").lower() else "fouled")
    rows, num, notes = rate(entry, sides, Q, spec, condition)
    rows[4:4] = extra
    if any(f.get("model") == "dwsim" for f in entry["fluids"].values()):
        notes.append("DWSIM liquid viscosity and conductivity of a non-ideal aqueous mixture come from mixing rules; "
                     "confirm against laboratory data before relying on h for that side")
    for side, meas in (entry.get("measured") or {}).items():  # geometry consistency: calculated vs measured pressure drop
        calc = num.get(f"dP_{side}_bar") if entry["type"] == "plate" else \
            num.get("dP_tube_bar" if side == num.get("tube_k") else "dP_shell_bar")
        if calc is not None and meas.get("value"):
            ratio = calc / meas["value"]
            num[f"dP_{side}_calc_over_measured"] = ratio
            rows.append((f"{side}-side pressure drop, measured", _n(meas["value"]), "bar", meas["source"]))
            if not 0.5 <= ratio <= 2:
                notes.append(f"the calculated {side}-side pressure drop is {ratio * 100:.0f} % of the measured "
                             f"{meas['value']:g} bar: the ILLUSTRATIVE geometry does not reproduce the real exchanger "
                             "(fewer or narrower channels, or the measurement includes nozzles/piping); velocities and h "
                             "here are likely off by the same cause")
    if circ_m3_h:
        num["circulation_m3_h"] = circ_m3_h
        if ures.get("driving_dT_K"):
            notes.append(f"the model rates {uid} on condensing minus body temperature ({_n(ures['driving_dT_K'])} K); with the "
                         f"{_n(entry['circulation']['rise_K']['value'])} K brine rise in the tubes the LMTD is {_n(num['LMTD'])} K")
    mu_path = (entry.get("model_U") or {}).get("path")
    model_U = _get(spec, mu_path) if mu_path else None
    solved_U = ((res.get("units") or {}).get(uid) or {}).get("U_W_m2K")
    chk = checks(tag, entry, num, model_U, condition)
    illustrative = [k for k, v in (entry.get("geometry") or {}).items() if isinstance(v, dict) and v.get("illustrative")]
    worst = max(chk, key=lambda c: c["utilisation"])
    summary = (f"{tag} at {_n(scale * 100)} % ({condition}): U {num['U']:.0f} W/m2K vs model {model_U}; area needed "
               f"{num['A_req']:.0f} of {num['A_inst']:.0f} m2; tightest check {worst['check']} {worst['utilisation'] * 100:.0f} %")
    out = {"tag": tag, "scale": scale, "condition": condition, "basis": src, "model_U": model_U, "solved_U": solved_U,
           "results": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in num.items()}, "checks": chk,
           "illustrative_geometry": illustrative, "notes": notes, "summary": summary}
    if save:
        md = sheet(w, tag, entry, out, rows, prop)
        meta = _save(w.name, f"HX detail {tag}", f"hx-{tag}", md, summary, by, request)
        return {**meta, **out}
    return out


def sheet(w, tag, entry, out, rows, prop):
    t = lambda head, rs: ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + \
        ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rs]  # noqa: E731
    md = [f"# Heat-exchanger detail rating: {tag}", "",
          "**Status: DRAFT for engineering review, not approved.** Thermal-hydraulic screening by PlantAgent; every number "
          "carries its source. Not a vendor thermal design or a mechanical design.", "",
          f"**Service:** {entry.get('service')}", "", f"**Basis solve:** {out['basis']}.", "",
          f"**Condition:** {out['condition']}" + (f" (proposal '{prop.get('title')}')" if prop else ""), ""]
    if out["illustrative_geometry"]:
        md += [f"**ILLUSTRATIVE geometry** (not in the P&ID or data sheet, to be replaced by the vendor data sheet): "
               f"{', '.join(out['illustrative_geometry'])}. Results depend on these values.", ""]
    md += ["## Calculation", ""] + t(("Quantity", "Value", "Unit", "Source / method"), rows)
    md += ["", "## Model U", ""] + t(("Item", "Value", "Source"), [
        ("U in the model", f"{_n(out['model_U'])} W/m²K", f"model {(entry.get('model_U') or {}).get('path')}: {(entry.get('model_U') or {}).get('why')}"),
        ("U solved on the exchanger unit", f"{_n(out['solved_U'])} W/m²K", "DWSIM solve (duty / (A LMTD) of the rating unit)"),
        ("U from the correlations", f"{_n(out['results']['U'])} W/m²K", f"this sheet ({out['condition']})")])
    md += ["", "## Screening checks", ""] + t(("Check", "Value", "Limit", "Utilisation", "Source"),
                                              [(c["check"], f"{_n(c['value'])} {c['unit']}", f"{_n(c['limit'])} {c['unit']}",
                                                f"{_n(c['utilisation'] * 100)} %", c["source"]) for c in out["checks"]])
    if out["notes"]:
        md += ["", "## Notes", ""] + [f"- {n}" for n in out["notes"]]
    md += ["", "## Software", "", f"ht {_ver('ht')}, fluids {_ver('fluids')}, chemicals {_ver('chemicals')} (Caleb Bell, MIT licence); "
           "DWSIM for the process solve."]
    return md


def _ver(mod):
    try:
        return __import__(mod).__version__
    except Exception:  # noqa: BLE001
        return "?"


def _save(case, title, stem, md, summary, by=None, request=None):
    """Markdown + PDF calculation artifact."""
    import tempfile
    from pathlib import Path
    from .decision import _pdf
    text = "\n".join(md) + "\n"
    files = {f"{stem}.md": text}
    try:
        with tempfile.TemporaryDirectory() as d:
            _pdf([text], Path(d) / "x.pdf", footer=title)
            files[f"{stem}.pdf"] = (Path(d) / "x.pdf").read_bytes()
    except Exception as e:  # noqa: BLE001 - the markdown stands without the PDF
        summary += f" (PDF failed: {type(e).__name__}: {e})"
    sources = sorted({r.split("|")[-2].strip() for r in md if r.startswith("|") and not r.startswith("|---") and r.count("|") > 3})
    return artifacts.save(case, "calculation", title, files, by=by or "PlantAgent (deterministic)", request=request,
                          sources=[s for s in sources if s and s not in ("Source", "Source / method")][:40], summary=summary)


if __name__ == "__main__":
    import sys
    from .plant import PlantWorkspace
    case, tag = sys.argv[1:3]
    w = PlantWorkspace(case)
    r = hx_detail(w, tag, float(sys.argv[3]) if len(sys.argv) > 3 else None, int(sys.argv[4]) if len(sys.argv) > 4 else None)
    print(json.dumps({k: r[k] for k in ("summary", "results", "checks", "notes", "files", "id") if k in r}, indent=1))
