"""Combustion and fired-equipment screening with Cantera (GRI-Mech 3.0 thermochemistry).

burn(): one burner (or a gas-turbine combustor, or a duct burner in a vitiated oxidant): fuel heating values, stoichiometric
air, excess air / flue O2, adiabatic flame temperature (HP equilibrium), flue-gas composition and flow, efficiency by the
energy-balance (stack-loss) method of ASME PTC 4 simplified (dry-gas, moisture and radiation losses, air-heat credit,
25 C reference), and a NOx screening: equilibrium NO at the flame temperature (an upper bound of the tendency) and thermal
NO formed in a stated residence time at the flame temperature (GRI-Mech 3.0 kinetics, isothermal post-flame reactor).
The NOx numbers are SCREENING values for comparing cases, not an emission guarantee: real burners have hotter
stoichiometric zones and staging that only the vendor's data capture.

hrsg_case(): a gas turbine + heat-recovery steam generator from a case file (cases/<case>/combustion.json; the salt plant
of US 5,366,514): the gas-turbine exhaust is closed by an energy balance on its fuel and shaft power, the HRSG sections are
calibrated (UA) at the documented steam rate, and off-design steam and stack temperature follow from the calibrated UA
with gas-side UA scaled by (gas flow ratio)^0.6; supplementary (duct) firing is solved for a steam target.

Usage: python -m plantagent.combustion <case> [steam_scale] [firing_scale]
"""
import json
import math

from .plant import ROOT

P_ATM = 101325.0
T_REF = 298.15                       # ASME PTC 4 reference temperature 77 F
AIR = {"O2": 0.2095, "N2": 0.7809, "AR": 0.0093, "CO2": 0.0003}  # dry air, mole fractions
ABMA_HUMIDITY = 0.013                # kg water / kg dry air, ABMA standard air (used by ASME PTC 4 when not measured)
HFG_25 = 2441.7e3                    # J/kg, latent heat of water at 25 C (IAPWS-95)
NG_TYPICAL = {"CH4": 0.931, "C2H6": 0.032, "C3H8": 0.007, "CO2": 0.01, "N2": 0.02}
MMBTU_H = 293.0711                   # kW per MMBtu/h
THERMAL_NOX_K = 1800.0
_GAS = None


def gas():
    global _GAS
    if _GAS is None:
        import cantera as ct
        _GAS = ct.Solution("gri30.yaml")
    return _GAS


def _norm(x):
    s = sum(float(v) for v in x.values())
    if s <= 0:
        raise ValueError("composition is empty")
    return {k: float(v) / s for k, v in x.items() if float(v) > 0}


def _h_molar(X, T):
    """Molar enthalpy J/kmol of a mixture at T (ideal gas, absolute incl. formation)."""
    g = gas()
    g.TPX = T, P_ATM, X
    return g.enthalpy_mole


def _mw(X):
    g = gas()
    g.TPX = 300, P_ATM, X
    return g.mean_molecular_weight


def _atoms(X):
    g = gas()
    return {e: sum(x * g.n_atoms(s, e) for s, x in X.items()) for e in ("C", "H", "O", "N")}


def heating_values(fuel):
    """LHV and HHV, J/kg fuel, at 25 C from GRI-Mech 3.0 enthalpies of formation (complete combustion)."""
    X = _norm(fuel)
    a = _atoms(X)
    o2 = a["C"] + a["H"] / 4 - a["O"] / 2  # kmol O2 per kmol fuel
    prod = {"CO2": a["C"], "H2O": a["H"] / 2, "N2": a["N"] / 2}
    h_r = _h_molar(X, T_REF) + o2 * _h_molar({"O2": 1}, T_REF)
    h_p = sum(n * _h_molar({s: 1}, T_REF) for s, n in prod.items() if n > 0)
    mw = _mw(X)
    lhv = (h_r - h_p) / mw
    return {"LHV": lhv, "HHV": lhv + prod["H2O"] * 18.015 / mw * HFG_25, "O2_stoich": o2, "MW": mw,
            "H2O_per_kg": prod["H2O"] * 18.015 / mw}


def _wet_air(humidity):
    n_h2o = humidity * _mw(AIR) / 18.015
    X = {**AIR, "H2O": n_h2o}
    return _norm(X)


def _o2_dry(X):
    dry = 1 - X.get("H2O", 0)
    return X.get("O2", 0) / dry * 100


def _complete(X_mix, T):
    """Products of complete combustion (TP equilibrium at a low temperature, where lean products are CO2/H2O/O2/N2)."""
    g = gas()
    g.TPX = 700.0, P_ATM, X_mix
    g.equilibrate("TP")
    g.TP = T, P_ATM
    return {s: x for s, x in zip(g.species_names, g.X) if x > 1e-9}


def _mix(fuel, ox_X, n_ox_per_fuel):
    X = {k: v for k, v in fuel.items()}
    for k, v in ox_X.items():
        X[k] = X.get(k, 0) + v * n_ox_per_fuel
    return _norm(X), 1 + n_ox_per_fuel


def flame(fuel, ox_X, n_ox, T_fuel, T_ox, P=P_ATM):
    """HP equilibrium of fuel (1 kmol) + oxidant (n_ox kmol): adiabatic flame temperature and equilibrium state."""
    g = gas()
    H = _h_molar(fuel, T_fuel) + n_ox * _h_molar(ox_X, T_ox)
    X, n = _mix(fuel, ox_X, n_ox)
    g.TPX = 1000, P, X
    g.HP = H / n / g.mean_molecular_weight, P
    g.equilibrate("HP")
    return g.T, {s: x for s, x in zip(g.species_names, g.X) if x > 1e-12}


def thermal_no(X_eq, T, tau_s, P=P_ATM):
    """Thermal NO formed in tau_s at constant T, starting from the equilibrium products with all nitrogen oxides removed."""
    import cantera as ct
    g = ct.Solution("gri30.yaml")
    start = {s: x for s, x in X_eq.items() if s == "N2" or g.n_atoms(s, "N") == 0}
    g.TPX = T, P, _norm(start)
    r = ct.IdealGasConstPressureReactor(g, energy="off", clone=True)
    net = ct.ReactorNet([r])
    net.advance(tau_s)
    ph = r.phase
    return float(ph["NO"].X[0] + ph["NO2"].X[0])


def _ppm_ref(ppm_dry, o2_dry_pct, ref):
    return ppm_dry * (20.9 - ref) / max(0.1, 20.9 - o2_dry_pct)


def burn(fuel=None, firing_kW=None, basis="HHV", excess_air_pct=None, o2_dry_pct=None, air_T_C=25.0, fuel_T_C=25.0,
         stack_T_C=None, humidity=ABMA_HUMIDITY, radiation_loss_pct=0.5, residence_s=0.02, oxidant=None, o2_ref_pct=3.0):
    """One fired burner. oxidant={'X': {...}, 'T_C': t} replaces air (a duct burner in turbine exhaust); then excess_air_pct /
    o2_dry_pct refer to the oxidant's O2."""
    X_f = _norm(fuel or NG_TYPICAL)
    hv = heating_values(X_f)
    if not firing_kW or firing_kW <= 0:
        raise ValueError("firing_kW must be positive")
    m_f = firing_kW * 1000 / hv[basis]
    n_f = m_f / hv["MW"]  # kmol/s
    ox_X = _norm(oxidant["X"]) if oxidant else _wet_air(humidity)
    T_ox = (oxidant["T_C"] if oxidant else air_T_C) + 273.15
    T_f = fuel_T_C + 273.15
    n_stoich = hv["O2_stoich"] / ox_X["O2"]  # kmol oxidant per kmol fuel

    def products(lam):
        X, _ = _mix(X_f, ox_X, lam * n_stoich)
        return _complete(X, 400)
    if o2_dry_pct is not None:
        lo, hi = 1.0, 50.0
        if _o2_dry(products(hi)) < o2_dry_pct:
            raise ValueError(f"flue O2 {o2_dry_pct} % dry is not reachable with this oxidant")
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if _o2_dry(products(mid)) < o2_dry_pct else (lo, mid)
        lam = (lo + hi) / 2
    else:
        lam = 1 + float(excess_air_pct if excess_air_pct is not None else 15.0) / 100
    if lam < 1:
        raise ValueError("sub-stoichiometric firing is outside this screening (air ratio below 1)")
    n_ox = lam * n_stoich
    T_ad, X_eq = flame(X_f, ox_X, n_ox, T_f, T_ox)
    X_mix, n_mix = _mix(X_f, ox_X, n_ox)
    X_fg = _complete(X_mix, 400)
    g = gas()
    g.TPX = 400, P_ATM, X_fg
    mw_fg = g.mean_molecular_weight
    # complete-combustion products keep the mole count of the mixture only for CH4-type fuels; use mass balance
    m_ox = n_f * n_ox * _mw(ox_X)
    m_fg = m_f + m_ox
    n_fg = m_fg / mw_fg
    o2d = _o2_dry(X_fg)
    out = {"fuel_X": X_f, "LHV_MJ_kg": hv["LHV"] / 1e6, "HHV_MJ_kg": hv["HHV"] / 1e6, "fuel_kg_s": m_f,
           "firing_kW_LHV": m_f * hv["LHV"] / 1000, "firing_kW_HHV": m_f * hv["HHV"] / 1000,
           "air_ratio": lam, "excess_air_pct": (lam - 1) * 100, "oxidant_kg_s": m_ox, "oxidant_O2_pct": ox_X["O2"] * 100,
           "T_ad_K": T_ad, "T_ad_C": T_ad - 273.15, "flue_X_wet": {k: round(v, 6) for k, v in X_fg.items() if v > 1e-6},
           "flue_kg_s": m_fg, "flue_Nm3_h_wet": n_fg * 22.414 * 3600, "flue_Nm3_h_dry": n_fg * (1 - X_fg.get("H2O", 0)) * 22.414 * 3600,
           "O2_dry_pct": o2d, "CO2_dry_pct": X_fg.get("CO2", 0) / (1 - X_fg.get("H2O", 0)) * 100, "H2O_wet_pct": X_fg.get("H2O", 0) * 100}
    # water dew point of the flue gas (partial pressure of H2O)
    from chemicals import iapws95_Tsat
    out["dew_point_C"] = iapws95_Tsat(X_fg.get("H2O", 0) * P_ATM) - 273.15
    # NOx screening
    no_eq = X_eq.get("NO", 0) + X_eq.get("NO2", 0)
    no_th = thermal_no(X_eq, T_ad, residence_s) if residence_s else None
    dry_eq = 1 - X_eq.get("H2O", 0)
    for key, x in (("NO_equilibrium", no_eq), ("NO_thermal", no_th)):
        if x is None:
            continue
        ppm = x / dry_eq * 1e6
        out[f"{key}_ppmvd"] = ppm
        out[f"{key}_ppmvd_ref"] = _ppm_ref(ppm, o2d, o2_ref_pct)
        out[f"{key}_lb_MMBtu_HHV"] = x * n_fg * 46.0055 / (m_f * hv["HHV"] / 1e6) * 2326.0
    out.update(o2_ref_pct=o2_ref_pct, residence_s=residence_s)
    if stack_T_C is not None:
        out.update(stack_losses(X_f, hv, m_f, X_fg, m_fg, ox_X, m_ox, T_ox, T_f, stack_T_C + 273.15, radiation_loss_pct))
    return out


def stack_losses(X_f, hv, m_f, X_fg, m_fg, ox_X, m_ox, T_ox, T_f, T_stack, radiation_loss_pct):
    """ASME PTC 4 energy-balance method, simplified: losses and credits as % of fuel input (HHV), reference 25 C."""
    g = gas()
    q_in = m_f * hv["HHV"]
    w = X_fg.get("H2O", 0)
    dry = _norm({k: v for k, v in X_fg.items() if k != "H2O"})
    n_fg = m_fg / _mw(X_fg)
    n_dry, n_w = n_fg * (1 - w), n_fg * w
    dry_loss = n_dry * (_h_molar(dry, T_stack) - _h_molar(dry, T_REF))
    h2o_fuel = m_f * hv["H2O_per_kg"] / 18.015  # kmol/s water from fuel hydrogen
    h2o_vap = _h_molar({"H2O": 1}, T_stack) - _h_molar({"H2O": 1}, T_REF)
    moist_fuel = h2o_fuel * (h2o_vap + HFG_25 * 18.015)
    moist_air = max(0.0, n_w - h2o_fuel) * h2o_vap
    credit_air = m_ox / _mw(ox_X) * (_h_molar(ox_X, T_ox) - _h_molar(ox_X, T_REF))
    credit_fuel = m_f / hv["MW"] * (_h_molar(X_f, T_f) - _h_molar(X_f, T_REF))
    L = {"dry_gas_loss_pct": dry_loss / q_in * 100, "moisture_from_fuel_loss_pct": moist_fuel / q_in * 100,
         "moisture_in_air_loss_pct": moist_air / q_in * 100, "radiation_loss_pct": radiation_loss_pct,
         "air_heat_credit_pct": credit_air / q_in * 100, "fuel_heat_credit_pct": credit_fuel / q_in * 100}
    eff = 100 - L["dry_gas_loss_pct"] - L["moisture_from_fuel_loss_pct"] - L["moisture_in_air_loss_pct"] - radiation_loss_pct \
        + L["air_heat_credit_pct"] + L["fuel_heat_credit_pct"]
    return {**L, "stack_T_C": T_stack - 273.15, "efficiency_HHV_pct": eff, "efficiency_LHV_pct": eff * hv["HHV"] / hv["LHV"]}


# ---------------------------------------------------------------- water / steam
def _steam_h(T_C, P_bar):
    from chemicals import iapws95_properties
    return iapws95_properties(T_C + 273.15, P_bar * 1e5)[3]


def _tsat(P_bar):
    from chemicals import iapws95_Tsat
    return iapws95_Tsat(P_bar * 1e5) - 273.15


def _gas_h(X, T_C):
    g = gas()
    g.TPX = T_C + 273.15, P_ATM, X
    return g.enthalpy_mass


def _gas_T(X, h):
    g = gas()
    g.TPX = 500, P_ATM, X
    g.HP = h, P_ATM
    return g.T - 273.15


def _lmtd(d1, d2):
    if d1 <= 0 or d2 <= 0:
        return None
    return d1 if abs(d1 - d2) < 1e-9 else (d1 - d2) / math.log(d1 / d2)


# ---------------------------------------------------------------- gas turbine + HRSG case
def _v(d, key):
    x = d[key]
    return x["value"] if isinstance(x, dict) else x


def gt_exhaust(cfg, shaft_kW):
    """Gas-turbine exhaust from an energy balance: fuel (LHV basis, at ambient) + air -> shaft + losses + exhaust at T_exh.
    The air flow is the unknown (bisection on the air ratio)."""
    gt, fuel = cfg["gas_turbine"], _norm(_v(cfg["fuel"], "composition_mol"))
    hv = heating_values(fuel)
    q_fuel = _v(gt, "fuel_MMBtu_h") * MMBTU_H * 1000  # W
    basis = cfg["fuel"].get("heating_value_basis", "LHV")
    m_f = q_fuel / hv[basis]
    T_amb = _v(gt, "ambient_T_C") + 273.15
    T_exh = _v(gt, "exhaust_T_C") + 273.15
    loss = _v(gt, "loss_pct") / 100 * q_fuel
    air = _wet_air(ABMA_HUMIDITY)
    n_f = m_f / hv["MW"]
    n_st = hv["O2_stoich"] / air["O2"]

    def surplus(lam):
        n_ox = lam * n_st
        X, n = _mix(fuel, air, n_ox)
        Xp = _complete(X, T_exh)
        h_in = n_f * (_h_molar(fuel, T_amb) + n_ox * _h_molar(air, T_amb))
        m = m_f + n_f * n_ox * _mw(air)
        h_out = m * _gas_h(Xp, T_exh - 273.15)
        return h_in - h_out - shaft_kW * 1000 - loss
    lo, hi = 1.05, 20.0
    if surplus(lo) < 0 or surplus(hi) > 0:
        raise ValueError("gas-turbine energy balance does not close for this exhaust temperature")
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if surplus(mid) > 0 else (lo, mid)
    lam = (lo + hi) / 2
    X, _ = _mix(fuel, air, lam * n_st)
    Xp = _complete(X, T_exh)
    m_air = n_f * lam * n_st * _mw(air)
    return {"fuel_X": fuel, "fuel_kg_s": m_f, "fuel_kW_LHV": m_f * hv["LHV"] / 1000, "fuel_kW_HHV": m_f * hv["HHV"] / 1000,
            "air_kg_s": m_air, "air_ratio": lam, "exhaust_kg_s": m_f + m_air, "exhaust_X": Xp, "exhaust_T_C": T_exh - 273.15,
            "exhaust_O2_wet_pct": Xp.get("O2", 0) * 100, "exhaust_O2_dry_pct": _o2_dry(Xp), "shaft_kW": shaft_kW,
            "efficiency_LHV_pct": shaft_kW / (m_f * hv["LHV"] / 1000) * 100}


def _steam_side(cfg):
    h = cfg["hrsg"]
    P = (_v(h, "steam_P_psig") + 14.696) * 0.0689476
    T_s = (_v(h, "steam_T_F") - 32) / 1.8
    Tsat = _tsat(P)
    T_fw = _v(h, "feedwater_T_C")
    T_eco = Tsat - _v(h, "economizer_approach_K")
    return {"P_bar": P, "T_C": T_s, "Tsat_C": Tsat, "T_fw_C": T_fw, "T_eco_out_C": T_eco, "h_s": _steam_h(T_s, P),
            "h_fw": _steam_h(T_fw, P), "h_eco": _steam_h(T_eco, P), "m_s": _v(h, "steam_lb_h") * 0.45359237 / 3600}


def hrsg_design(cfg, exh):
    """Calibrate the HRSG at the documented steam rate: high-pressure section (superheater + evaporator, lumped against the
    saturation temperature) and economiser; returns UA of each section, pinch and stack temperature."""
    st = _steam_side(cfg)
    keep = 1 - _v(cfg["hrsg"], "casing_loss_pct") / 100
    X, m_g, T_in = exh["exhaust_X"], exh["exhaust_kg_s"], exh["exhaust_T_C"]
    q_hp = st["m_s"] * (st["h_s"] - st["h_eco"])
    q_eco = st["m_s"] * (st["h_eco"] - st["h_fw"])
    h_in = _gas_h(X, T_in)
    T_p = _gas_T(X, h_in - q_hp / keep / m_g)
    T_stack = _gas_T(X, h_in - (q_hp + q_eco) / keep / m_g)
    l_hp = _lmtd(T_in - st["Tsat_C"], T_p - st["Tsat_C"])
    l_eco = _lmtd(T_p - st["T_eco_out_C"], T_stack - st["T_fw_C"])
    if not l_hp or not l_eco:
        raise ValueError("HRSG temperature cross at the documented steam rate: the exhaust temperature is too low")
    return {**st, "q_hp_kW": q_hp / 1000, "q_eco_kW": q_eco / 1000, "T_pinch_gas_C": T_p, "pinch_K": T_p - st["Tsat_C"],
            "stack_T_C": T_stack, "UA_hp": q_hp / l_hp, "UA_eco": q_eco / l_eco, "m_g": m_g, "keep": keep}


def hrsg_offdesign(cfg, design, X, m_g, T_in, exponent):
    """Steam rate and stack temperature for a gas flow/temperature with the calibrated UA (gas-side scaling)."""
    st = design
    f = (m_g / design["m_g"]) ** exponent
    UA_hp, UA_eco, keep = design["UA_hp"] * f, design["UA_eco"] * f, design["keep"]
    h_in = _gas_h(X, T_in)
    T_w = st["T_eco_out_C"]
    for _ in range(40):
        h_w = _steam_h(T_w, st["P_bar"])

        def gap(ms):
            T_p = _gas_T(X, h_in - ms * (st["h_s"] - h_w) / keep / m_g)
            l = _lmtd(T_in - st["Tsat_C"], T_p - st["Tsat_C"])
            return (ms * (st["h_s"] - h_w) / l - UA_hp) if l else 1e30
        lo, hi = 0.0, st["m_s"] * 5
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if gap(mid) < 0 else (lo, mid)
        ms = (lo + hi) / 2
        T_p = _gas_T(X, h_in - ms * (st["h_s"] - h_w) / keep / m_g)
        # economiser, counter-current, epsilon-NTU with mean specific heats
        cp_g = (_gas_h(X, T_p) - _gas_h(X, T_p - 50)) / 50
        cp_w = (_steam_h(min(T_w, st["Tsat_C"] - 1), st["P_bar"]) - st["h_fw"]) / max(1.0, min(T_w, st["Tsat_C"] - 1) - st["T_fw_C"])
        C_g, C_w = m_g * cp_g * keep, ms * cp_w
        Cmin, Cmax = min(C_g, C_w), max(C_g, C_w)
        ntu, cr = UA_eco / Cmin, Cmin / Cmax
        eps = (1 - math.exp(-ntu * (1 - cr))) / (1 - cr * math.exp(-ntu * (1 - cr))) if abs(1 - cr) > 1e-6 else ntu / (1 + ntu)
        q = eps * Cmin * (T_p - st["T_fw_C"])
        T_w_new = st["T_fw_C"] + q / C_w
        if abs(T_w_new - T_w) < 0.01:
            T_w = T_w_new
            break
        T_w = 0.5 * T_w + 0.5 * T_w_new
    T_stack = _gas_T(X, _gas_h(X, T_p) - q / keep / m_g)
    return {"steam_kg_s": ms, "steam_lb_h": ms * 3600 / 0.45359237, "T_pinch_gas_C": T_p, "pinch_K": T_p - st["Tsat_C"],
            "eco_water_out_C": T_w, "eco_approach_K": st["Tsat_C"] - T_w, "stack_T_C": T_stack, "UA_factor": f,
            "q_steam_kW": ms * (st["h_s"] - st["h_fw"]) / 1000}


def duct_fire(cfg, exh, fuel_kW_HHV, residence_s):
    """Supplementary firing of fuel_kW (HHV) in the turbine exhaust: mixed gas temperature and composition, plus the
    duct burner's NOx screening (stoichiometric flame zone in the vitiated exhaust)."""
    fuel = exh["fuel_X"]
    if fuel_kW_HHV <= 0:
        return {"T_C": exh["exhaust_T_C"], "X": exh["exhaust_X"], "m_g": exh["exhaust_kg_s"], "fuel_kW_HHV": 0.0,
                "fuel_MMBtu_h_HHV": 0.0, "O2_wet_pct": exh["exhaust_X"].get("O2", 0) * 100, "NOx_added_ppmvd_15O2": 0.0, "NOx_added_lb_MMBtu_HHV": 0.0}
    hv = heating_values(fuel)
    m_f = fuel_kW_HHV * 1000 / hv["HHV"]
    n_f = m_f / hv["MW"]
    X_ox, T_ox = exh["exhaust_X"], exh["exhaust_T_C"] + 273.15
    n_ox_total = exh["exhaust_kg_s"] / _mw(X_ox) / n_f  # kmol exhaust per kmol duct fuel
    T_mix, X_eq = flame(fuel, X_ox, n_ox_total, 298.15, T_ox)
    X_mix, _ = _mix(fuel, X_ox, n_ox_total)
    X_p = _complete(X_mix, T_mix)
    # local flame: stoichiometric mixture of duct fuel and exhaust
    n_st = hv["O2_stoich"] / X_ox["O2"]
    T_loc, X_loc = flame(fuel, X_ox, n_st, 298.15, T_ox)
    x_no = thermal_no(X_loc, T_loc, residence_s) if residence_s else 0.0
    x_no_eq = X_loc.get("NO", 0) + X_loc.get("NO2", 0)
    frac = (1 + n_st) / (1 + n_ox_total)  # share of the total gas that passed through the stoichiometric zone (moles)
    m_g = exh["exhaust_kg_s"] + m_f
    n_g = m_g / _mw(X_p)
    dry = 1 - X_p.get("H2O", 0)
    o2d = _o2_dry(X_p)
    add_ppm = x_no * frac / dry * 1e6
    return {"T_C": T_mix - 273.15, "X": X_p, "m_g": m_g, "fuel_kW_HHV": fuel_kW_HHV, "fuel_MMBtu_h_HHV": fuel_kW_HHV / MMBTU_H,
            "fuel_kg_s": m_f, "O2_wet_pct": X_p.get("O2", 0) * 100, "O2_dry_pct": o2d,
            "local_flame_T_K": T_loc, "local_NO_equilibrium_ppm": x_no_eq * 1e6, "local_NO_thermal_ppm": x_no * 1e6,
            "flame_zone_fraction": frac, "NOx_added_ppmvd": add_ppm, "NOx_added_ppmvd_15O2": _ppm_ref(add_ppm, o2d, 15.0),
            "NOx_added_lb_MMBtu_HHV": x_no * frac * n_g * 46.0055 / (fuel_kW_HHV / 1000) * 2326.0 if fuel_kW_HHV else 0.0}


def hrsg_case(cfg, shaft_kW, steam_scale=None, firing_scale=None, exhaust_T_C=None, residence_s=None):
    """Base point (documented) and one scenario: a steam target (duct firing solved) or a firing multiple of the GT fuel."""
    cfg = json.loads(json.dumps(cfg))
    if exhaust_T_C:
        cfg["gas_turbine"]["exhaust_T_C"] = {"value": float(exhaust_T_C), "source": "engineer's input", "illustrative": True}
    tau = residence_s or _v(cfg["duct_burner"], "residence_s")
    exp = _v(cfg["hrsg"], "ua_gas_exponent")
    exh = gt_exhaust(cfg, shaft_kW)
    des = hrsg_design(cfg, exh)
    base_fuel_hhv = exh["fuel_kW_HHV"]
    if firing_scale and steam_scale:
        raise ValueError("give steam_scale or firing_scale, not both")

    def run(q_db):
        d = duct_fire(cfg, exh, q_db, tau)
        o = hrsg_offdesign(cfg, des, d["X"], d["m_g"], d["T_C"], exp)
        return d, o
    target = None
    if steam_scale and steam_scale > 1:
        target = des["m_s"] * steam_scale
        lo, hi = 0.0, base_fuel_hhv
        if run(hi)[1]["steam_kg_s"] < target:
            raise ValueError("more than the turbine's own fuel would be needed as duct firing; outside this screening")
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if run(mid)[1]["steam_kg_s"] < target else (lo, mid)
        q_db = hi
    elif firing_scale and firing_scale > 1:
        q_db = (firing_scale - 1) * base_fuel_hhv
    else:
        q_db = 0.0
    d, o = run(q_db)
    total_hhv = base_fuel_hhv + q_db
    X = d["X"]
    # stack-loss breakdown of the whole train (GT + duct burner + HRSG) on total fuel HHV (ASME PTC 4 style)
    hv = heating_values(exh["fuel_X"])
    m_f_tot = total_hhv * 1000 / hv["HHV"]
    gt_loss = _v(cfg["gas_turbine"], "loss_pct") / 100 * _v(cfg["gas_turbine"], "fuel_MMBtu_h") * MMBTU_H
    casing = o["q_steam_kW"] / des["keep"] * (1 - des["keep"])
    loss = stack_losses(exh["fuel_X"], hv, m_f_tot, X, d["m_g"], _wet_air(ABMA_HUMIDITY), exh["air_kg_s"],
                        _v(cfg["gas_turbine"], "ambient_T_C") + 273.15, 298.15, o["stack_T_C"] + 273.15,
                        (gt_loss + casing) / total_hhv * 100)
    from chemicals import iapws95_Tsat
    dew = iapws95_Tsat(X.get("H2O", 0) * P_ATM) - 273.15
    useful = shaft_kW + o["q_steam_kW"]
    return {"gas_turbine": exh, "hrsg_design": des, "duct_burner": d, "hrsg": o, "steam_target_kg_s": target,
            "steam_scale": (o["steam_kg_s"] / des["m_s"]), "total_fuel_kW_HHV": total_hhv,
            "fuel_utilisation_HHV_pct": useful / total_hhv * 100, "losses": loss, "dew_point_C": dew,
            "stack_O2_dry_pct": _o2_dry(X)}


def checks_hrsg(cfg, r, tag):
    lim = cfg["hrsg"]
    out = []

    def add(uid, check, value, limit, unit, util, source):
        out.append({"id": uid, "check": check, "value": round(value, 4), "limit": round(limit, 4), "unit": unit,
                    "utilisation": None if util is None else round(util, 3), "source": source})
    o, d, des = r["hrsg"], r["duct_burner"], r["hrsg_design"]
    mp = _v(lim, "min_pinch_K")
    add(tag, "evaporator pinch vs minimum", o["pinch_K"], mp, "K", mp / max(o["pinch_K"], 1e-6), lim["min_pinch_K"]["source"])
    ma = _v(lim, "min_economizer_approach_K")
    add(tag, "economiser approach to saturation vs minimum (steaming)", o["eco_approach_K"], ma, "K", ma / max(o["eco_approach_K"], 1e-6),
        lim["min_economizer_approach_K"]["source"])
    margin = _v(lim, "stack_dew_margin_K")
    ms = r["dew_point_C"] + margin
    add(tag, f"stack temperature vs water dew point {r['dew_point_C']:.0f} C + {margin:g} K", o["stack_T_C"], ms, "C",
        ms / o["stack_T_C"], lim["stack_dew_margin_K"]["source"])
    if d["fuel_kW_HHV"] > 0:
        add(tag, "gas temperature into the superheater vs unfired design inlet", d["T_C"], des and r["gas_turbine"]["exhaust_T_C"], "C",
            d["T_C"] / r["gas_turbine"]["exhaust_T_C"], "the documented HRSG is unfired: above that inlet the superheater sees hotter gas "
            "than its design point (tube metal and attemperation to confirm with the HRSG vendor)")
        exists = bool(_v(cfg["duct_burner"], "installed"))
        add("duct burner", f"supplementary firing needed ({d['fuel_MMBtu_h_HHV']:.1f} MMBtu/h)" + ("" if exists else ", no duct burner on record"),
            d["fuel_kW_HHV"] / 1000, 0.0, "MW HHV", None, cfg["duct_burner"]["installed"]["source"])
        mo = _v(cfg["duct_burner"], "min_O2_wet_pct")
        add("duct burner", "O2 after duct firing vs minimum for stable firing", d["O2_wet_pct"], mo, "% wet", mo / d["O2_wet_pct"],
            cfg["duct_burner"]["min_O2_wet_pct"]["source"])
        add("duct burner", "local flame temperature vs thermal-NOx onset (screening)", d["local_flame_T_K"], THERMAL_NOX_K, "K",
            d["local_flame_T_K"] / THERMAL_NOX_K, "thermal (Zeldovich) NO formation becomes significant above about 1,800 K "
            "(e.g. Turns, An Introduction to Combustion, ch. 5)")
    return out


def check_burner(r, min_stack_margin_K=20.0):
    out = [{"id": "burner", "check": "adiabatic flame temperature vs thermal-NOx onset (screening)", "value": round(r["T_ad_K"], 1),
            "limit": THERMAL_NOX_K, "unit": "K", "utilisation": round(r["T_ad_K"] / THERMAL_NOX_K, 3),
            "source": "thermal (Zeldovich) NO formation becomes significant above about 1,800 K (e.g. Turns, An Introduction to Combustion, ch. 5)"}]
    if r.get("stack_T_C") is not None:
        lim = r["dew_point_C"] + min_stack_margin_K
        out.append({"id": "burner", "check": f"stack temperature vs water dew point {r['dew_point_C']:.0f} C + {min_stack_margin_K:g} K",
                    "value": round(r["stack_T_C"], 1), "limit": round(lim, 1), "unit": "C", "utilisation": round(lim / r["stack_T_C"], 3),
                    "source": "typical practice: keep a non-condensing stack above the water dew point with a margin"})
    return out


def load_case(case):
    f = ROOT / "cases" / case / "combustion.json"
    return json.loads(f.read_text()) if f.exists() else None


# ---------------------------------------------------------------- workspace tool + calculation sheet
def _n(v):
    from .hxdetail import _n as n
    return n(float(v)) if isinstance(v, (int, float)) else n(v)


def _t(head, rows):
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + \
        ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]


def _get(spec_res, path):
    cur = spec_res
    for p in path.split("."):
        cur = (cur or {}).get(p)
    return cur


DRAFT = ("**Status: DRAFT for engineering review, not approved.** Combustion screening by PlantAgent with Cantera "
         "(GRI-Mech 3.0); every number carries its source. NOx values are screening tendencies, not emission guarantees.")


def combustion_check(w, steam_scale=None, firing_scale=None, exhaust_T_C=None, residence_s=None, scale=None, fuel=None,
                     firing_kW=None, excess_air_pct=None, o2_dry_pct=None, air_T_C=None, stack_T_C=None, basis="HHV",
                     save=True, by=None, request=None, changes=None):
    """The agent tool. With a case file (gas turbine + HRSG) and no firing_kW: base point and the asked scenario.
    Otherwise one burner from the given fuel, firing rate, air ratio / O2, air preheat and stack temperature."""
    cfg = load_case(w.name)
    if firing_kW is not None or cfg is None:
        if firing_kW is None:
            raise ValueError("this case has no fired equipment on record: give firing_kW (and fuel, excess_air_pct or "
                             "o2_dry_pct, air_T_C, stack_T_C) to screen a burner")
        r = burn(fuel, float(firing_kW), basis, excess_air_pct, o2_dry_pct, float(air_T_C if air_T_C is not None else 25.0),
                 25.0, stack_T_C, residence_s=residence_s if residence_s is not None else 0.02)
        chk = check_burner(r)
        md = _burner_sheet(r, fuel is None, chk)
        summary = (f"burner {r['firing_kW_HHV']:.0f} kW HHV, air ratio {r['air_ratio']:.2f} (O2 {r['O2_dry_pct']:.1f} % dry): flame "
                   f"{r['T_ad_C']:.0f} C" + (f", efficiency {r['efficiency_HHV_pct']:.1f} % HHV" if 'efficiency_HHV_pct' in r else "") +
                   f", thermal NO screening {r['NO_thermal_ppmvd_ref']:.0f} ppmvd @3 % O2")
        title, stem, out = "Combustion check: burner", "combustion-burner", {"mode": "burner", "result": r}
    else:
        path = cfg["gas_turbine"]["shaft_kW"]["from_model"]
        if changes:  # the proposed design: its own solve sets the turbine load (mirrors the electrical adapter)
            import copy
            from .plant import patch
            st = w._solve(patch(copy.deepcopy(w.spec), changes), float(scale or 1.0))
        else:
            st = w.state(float(scale or 1.0))
        shaft = _get(st, path)
        if not shaft:
            raise ValueError(f"the solve has no {path} for the turbine shaft power")
        base = hrsg_case(cfg, shaft, exhaust_T_C=exhaust_T_C, residence_s=residence_s)
        r = hrsg_case(cfg, shaft, steam_scale, firing_scale, exhaust_T_C, residence_s) if (steam_scale or firing_scale) else base
        tag = cfg["hrsg"]["tag"]
        chk = checks_hrsg(cfg, r, tag)
        md = _hrsg_sheet(cfg, base, r, chk, shaft, path, steam_scale, firing_scale, exhaust_T_C, w, scale)
        d, o = r["duct_burner"], r["hrsg"]
        # SI first, the plant's US units in brackets
        summary = (f"{cfg['gas_turbine']['tag']} + {tag}: steam {o['steam_lb_h'] * 0.45359237 / 1000:,.1f} t/h "
                   f"({o['steam_lb_h']:,.0f} lb/h, ×{r['steam_scale']:.2f}), stack {base['hrsg']['stack_T_C']:.0f} → {o['stack_T_C']:.0f} °C, "
                   f"duct firing {d.get('fuel_kW_HHV', 0) / 1000:,.2f} MW HHV ({d.get('fuel_MMBtu_h_HHV', 0):.1f} MMBtu/h), "
                   f"NOx added {d.get('NOx_added_ppmvd_15O2', 0):.1f} ppmvd at 15 % O2 (screening)")
        title, stem = f"Combustion check: {cfg['gas_turbine']['tag']} + {tag}", "combustion-hrsg"
        out = {"mode": "gas turbine + HRSG", "base": _slim(base), "scenario": _slim(r)}
    out.update(checks=chk, summary=summary)
    if not save:
        return out
    from .hxdetail import _save
    return {**_save(w.name, title, stem, md, summary, by, request), **out}


def _slim(r):
    keep = {"gas_turbine": ("air_kg_s", "air_ratio", "exhaust_kg_s", "exhaust_T_C", "exhaust_O2_dry_pct", "efficiency_LHV_pct", "fuel_kW_LHV", "shaft_kW"),
            "duct_burner": ("T_C", "fuel_MMBtu_h_HHV", "O2_wet_pct", "local_flame_T_K", "NOx_added_ppmvd_15O2", "NOx_added_lb_MMBtu_HHV"),
            "hrsg": ("steam_lb_h", "stack_T_C", "pinch_K", "eco_approach_K", "q_steam_kW")}
    out = {k: {f: round(float(r[k][f]), 3) for f in fs if f in r[k]} for k, fs in keep.items()}
    out.update({k: round(float(r[k]), 3) for k in ("steam_scale", "total_fuel_kW_HHV", "fuel_utilisation_HHV_pct", "dew_point_C", "stack_O2_dry_pct")})
    return out


def _burner_sheet(r, default_fuel, chk):
    fsrc = "ILLUSTRATIVE typical pipeline natural gas (no fuel analysis given)" if default_fuel else "engineer's input"
    rows = [("fuel (mole fractions)", ", ".join(f"{k} {v:.3f}" for k, v in r["fuel_X"].items()), "", fsrc),
            ("LHV / HHV", f"{_n(r['LHV_MJ_kg'])} / {_n(r['HHV_MJ_kg'])}", "MJ/kg", "Cantera GRI-Mech 3.0 enthalpies of formation at 25 C; HHV adds water latent heat 2,441.7 kJ/kg (IAPWS-95)"),
            ("firing rate HHV / LHV", f"{_n(r['firing_kW_HHV'])} / {_n(r['firing_kW_LHV'])}", "kW", "input / heating values"),
            ("fuel flow", _n(r["fuel_kg_s"]), "kg/s", "firing / heating value"),
            ("air ratio / excess air", f"{_n(r['air_ratio'])} / {_n(r['excess_air_pct'])} %", "", "input (or solved for the flue O2)"),
            ("air flow (ABMA standard humidity 0.013 kg/kg)", _n(r["oxidant_kg_s"]), "kg/s", "stoichiometric O2 x air ratio"),
            ("adiabatic flame temperature", f"{_n(r['T_ad_K'])} K ({_n(r['T_ad_C'])} °C)", "", "Cantera HP equilibrium (GRI-Mech 3.0)"),
            ("flue gas O2 dry / CO2 dry / H2O wet", f"{_n(r['O2_dry_pct'])} / {_n(r['CO2_dry_pct'])} / {_n(r['H2O_wet_pct'])}", "%", "complete-combustion products (Cantera)"),
            ("flue gas flow", f"{_n(r['flue_kg_s'])} kg/s; {_n(r['flue_Nm3_h_wet'])} Nm³/h wet; {_n(r['flue_Nm3_h_dry'])} Nm³/h dry", "", "mass balance; Nm³ at 0 °C, 1 atm"),
            ("water dew point of the flue gas", _n(r["dew_point_C"]), "°C", "H2O partial pressure, IAPWS-95 saturation"),
            ("NO at equilibrium at the flame temperature", f"{_n(r['NO_equilibrium_ppmvd_ref'])} ppmvd @{r['o2_ref_pct']:g} % O2", "", "Cantera equilibrium: upper bound of the thermal tendency (SCREENING)"),
            ("thermal NO formed in the residence time", f"{_n(r['NO_thermal_ppmvd_ref'])} ppmvd @{r['o2_ref_pct']:g} % O2; {_n(r['NO_thermal_lb_MMBtu_HHV'])} lb/MMBtu HHV", "",
             f"GRI-Mech 3.0 kinetics, isothermal at the flame temperature for {r['residence_s']:g} s (ILLUSTRATIVE residence; SCREENING)")]
    if "efficiency_HHV_pct" in r:
        rows += [("stack temperature", _n(r["stack_T_C"]), "°C", "input"),
                 ("dry flue gas loss", _n(r["dry_gas_loss_pct"]), "% HHV", "ASME PTC 4 energy balance, simplified, 25 °C reference"),
                 ("moisture from fuel hydrogen loss", _n(r["moisture_from_fuel_loss_pct"]), "% HHV", "ASME PTC 4 (incl. latent heat)"),
                 ("moisture in air loss", _n(r["moisture_in_air_loss_pct"]), "% HHV", "ASME PTC 4"),
                 ("radiation and convection loss", _n(r["radiation_loss_pct"]), "% HHV", "ILLUSTRATIVE (ABMA chart value for the unit size to confirm)"),
                 ("air heat credit", _n(r["air_heat_credit_pct"]), "% HHV", "ASME PTC 4 (air entering above 25 °C); counts only preheat supplied from outside the "
                  "boiler envelope (a flue-gas air heater inside it: give ambient air and the stack after the air heater)"),
                 ("efficiency HHV / LHV", f"{_n(r['efficiency_HHV_pct'])} / {_n(r['efficiency_LHV_pct'])}", "%", "100 − losses + credits")]
    md = ["# Combustion check: burner", "", DRAFT, "", "## Calculation", ""] + _t(("Quantity", "Value", "Unit", "Source / method"), rows)
    return md + _checks_md(chk) + _soft()


def _checks_md(chk):
    return ["", "## Screening checks", ""] + _t(("Equipment", "Check", "Value", "Limit", "Utilisation", "Source"),
                                                [(c["id"], c["check"], f"{_n(c['value'])} {c['unit']}", f"{_n(c['limit'])} {c['unit']}",
                                                  "information" if c["utilisation"] is None else f"{_n(c['utilisation'] * 100)} %", c["source"]) for c in chk])


def _soft():
    import cantera
    from .hxdetail import _ver
    return ["", "## Software", "", f"Cantera {cantera.__version__} with GRI-Mech 3.0 (gri30.yaml); chemicals {_ver('chemicals')} (IAPWS-95)."]


def _hrsg_sheet(cfg, base, r, chk, shaft, path, steam_scale, firing_scale, exhaust_T_C, w, scale):
    gt, h, db = cfg["gas_turbine"], cfg["hrsg"], cfg["duct_burner"]
    src = lambda d, k: d[k].get("source", "") if isinstance(d[k], dict) else ""  # noqa: E731
    illus = [f"{sec}.{k}" for sec in ("fuel", "gas_turbine", "hrsg", "duct_burner") for k, v in cfg[sec].items()
             if isinstance(v, dict) and v.get("illustrative")] + (["gas_turbine.exhaust_T_C (engineer's input)"] if exhaust_T_C else [])
    g0, des = base["gas_turbine"], base["hrsg_design"]
    scen = (f"steam target x{steam_scale:g} (duct firing solved)" if steam_scale else
            f"total firing x{firing_scale:g} (the extra fuel fired in a duct burner)" if firing_scale else "documented operation")
    md = [f"# Combustion check: {gt['tag']} gas turbine + {h['tag']} heat-recovery steam generator", "", DRAFT, "",
          "**Plant:** salt plant of US 5,366,514 FIG. I: the gas turbine drives the vapour compressor K-201; its exhaust raises "
          "600 psig / 820 °F steam in an unfired HRSG for a back-pressure turbine whose exhaust joins the K-201 discharge (D-201).", "",
          f"**Scenario:** {scen}.", "",
          f"**ILLUSTRATIVE inputs** (not in the patent): {', '.join(illus)}. Results depend on them, the exhaust temperature most.", "",
          "## Inputs", ""]
    md += _t(("Input", "Value", "Unit", "Source"), [
        ("turbine fuel", f"{_n(_v(gt, 'fuel_MMBtu_h'))} MMBtu/h ({_n(g0['fuel_kW_LHV'])} kW)", cfg["fuel"]["heating_value_basis"], src(gt, "fuel_MMBtu_h") + "; basis: " + cfg["fuel"]["heating_value_basis_source"]),
        ("fuel composition", ", ".join(f"{k} {v:.3f}" for k, v in _v(cfg["fuel"], "composition_mol").items()), "mol", src(cfg["fuel"], "composition_mol")),
        ("ambient", _n(_v(gt, "ambient_T_C")), "°C", src(gt, "ambient_T_C")),
        ("turbine shaft power", _n(shaft), "kW", f"{gt['shaft_kW']['source']} ({path}, {_n((scale or 1.0) * 100)} % throughput)"),
        ("turbine exhaust temperature", _n(g0["exhaust_T_C"]), "°C", "engineer's input" if exhaust_T_C else src(gt, "exhaust_T_C")),
        ("turbine losses", _n(_v(gt, "loss_pct")), "% of fuel", src(gt, "loss_pct")),
        ("steam", f"{_n(_v(h, 'steam_lb_h'))} lb/h at {_n(_v(h, 'steam_P_psig'))} psig, {_n(_v(h, 'steam_T_F'))} °F", "", src(h, "steam_lb_h")),
        ("feedwater", _n(_v(h, "feedwater_T_C")), "°C", src(h, "feedwater_T_C")),
        ("economiser design approach", _n(_v(h, "economizer_approach_K")), "K", src(h, "economizer_approach_K")),
        ("HRSG casing loss", _n(_v(h, "casing_loss_pct")), "%", src(h, "casing_loss_pct")),
        ("off-design UA exponent", _n(_v(h, "ua_gas_exponent")), "", src(h, "ua_gas_exponent")),
        ("duct burner", "installed" if _v(db, "installed") else "none on record", "", src(db, "installed")),
        ("NO screening residence time", _n(_v(db, "residence_s")), "s", src(db, "residence_s"))])
    md += ["", "## Gas turbine exhaust (energy balance)", ""]
    md += _t(("Quantity", "Value", "Unit", "Method"), [
        ("air flow", _n(g0["air_kg_s"]), "kg/s", "bisection on the air ratio: fuel + air (ABMA humidity) at ambient = shaft + losses + exhaust enthalpy (Cantera)"),
        ("overall air ratio", _n(g0["air_ratio"]), "", "air / stoichiometric air"),
        ("exhaust flow / O2", f"{_n(g0['exhaust_kg_s'])} kg/s / {_n(g0['exhaust_O2_dry_pct'])} % dry", "", "complete combustion (Cantera)"),
        ("turbine shaft efficiency", _n(g0["efficiency_LHV_pct"]), "% LHV", "shaft / fuel LHV")])
    md += ["", "## HRSG calibration at the documented steam rate", ""]
    md += _t(("Quantity", "Value", "Unit", "Method"), [
        ("saturation at drum pressure", f"{_n(des['Tsat_C'])} °C at {_n(des['P_bar'])} bar(a)", "", "IAPWS-95"),
        ("superheater + evaporator duty / economiser duty", f"{_n(des['q_hp_kW'])} / {_n(des['q_eco_kW'])}", "kW", "steam x enthalpy rise (IAPWS-95)"),
        ("gas leaving the evaporator / pinch", f"{_n(des['T_pinch_gas_C'])} °C / {_n(des['pinch_K'])} K", "", "gas enthalpy balance (Cantera)"),
        ("stack temperature (documented operation)", _n(des["stack_T_C"]), "°C", "gas enthalpy balance"),
        ("UA superheater + evaporator / economiser", f"{_n(des['UA_hp'] / 1000)} / {_n(des['UA_eco'] / 1000)}", "kW/K",
         "duty / LMTD (superheater lumped with the evaporator against saturation: screening simplification)")])
    rows = []
    for label, k1, k2, unit in (("steam", "hrsg", "steam_lb_h", "lb/h"), ("stack temperature", "hrsg", "stack_T_C", "°C"),
                                ("evaporator pinch", "hrsg", "pinch_K", "K"), ("economiser approach", "hrsg", "eco_approach_K", "K"),
                                ("gas into the superheater", "duct_burner", "T_C", "°C"), ("duct firing", "duct_burner", "fuel_MMBtu_h_HHV", "MMBtu/h HHV"),
                                ("O2 after duct firing", "duct_burner", "O2_wet_pct", "% wet"),
                                ("NOx added by the duct burner", "duct_burner", "NOx_added_ppmvd_15O2", "ppmvd @15 % O2"),
                                ("duct-burner NOx (screening)", "duct_burner", "NOx_added_lb_MMBtu_HHV", "lb/MMBtu HHV")):
        a, b = base[k1].get(k2), r[k1].get(k2)
        if a is None and k1 == "duct_burner" and k2 == "O2_wet_pct":
            a = base["gas_turbine"]["exhaust_X"].get("O2", 0) * 100
        rows.append((label, _n(a) if a is not None else "—", _n(b) if b is not None else "—", unit,
                     "calibrated UA with gas-side scaling (gas flow ratio)^exponent; steam temperature held by attemperation"
                     if k1 == "hrsg" else "Cantera: duct fuel burnt in the exhaust (HP equilibrium); NOx from a stoichiometric "
                     "flame zone at its adiabatic temperature for the residence time, diluted into the total gas (SCREENING)"))
    rows += [("total fuel", _n(base["total_fuel_kW_HHV"]), _n(r["total_fuel_kW_HHV"]), "kW HHV", "turbine + duct burner"),
             ("water dew point of the stack gas", _n(base["dew_point_C"]), _n(r["dew_point_C"]), "°C", "IAPWS-95 saturation at the H2O partial pressure"),
             ("fuel utilisation (shaft + steam)", _n(base["fuel_utilisation_HHV_pct"]), _n(r["fuel_utilisation_HHV_pct"]), "% HHV", "energy balance"),
             ("dry-gas loss", _n(base["losses"]["dry_gas_loss_pct"]), _n(r["losses"]["dry_gas_loss_pct"]), "% HHV", "ASME PTC 4 energy balance, simplified, 25 °C reference"),
             ("moisture losses (fuel H + air)", _n(base["losses"]["moisture_from_fuel_loss_pct"] + base["losses"]["moisture_in_air_loss_pct"]),
              _n(r["losses"]["moisture_from_fuel_loss_pct"] + r["losses"]["moisture_in_air_loss_pct"]), "% HHV", "ASME PTC 4"),
             ("turbine + casing losses", _n(base["losses"]["radiation_loss_pct"]), _n(r["losses"]["radiation_loss_pct"]), "% HHV", "inputs above"),
             ("efficiency by losses (check = utilisation)", _n(base["losses"]["efficiency_HHV_pct"]), _n(r["losses"]["efficiency_HHV_pct"]), "% HHV",
              "100 − losses + credits (ASME PTC 4 stack-loss method)")]
    md += ["", "## Documented operation vs scenario", ""] + _t(("Quantity", "Documented", "Scenario", "Unit", "Method"), rows)
    md += _checks_md(chk)
    md += ["", "## What this does not cover", "",
           "- The turbine's own NOx and its part-load behaviour need the vendor performance data (not in the patent).",
           "- Extra steam reaches the plant as more turbine exhaust into D-201; re-solve the process model with TURBINE_EXH "
           "raised to see what it does to the evaporator (run_process / sweep)."]
    return md + _soft()


if __name__ == "__main__":
    import sys
    case = sys.argv[1]
    cfg = load_case(case)
    r = hrsg_case(cfg, 9399.0, float(sys.argv[2]) if len(sys.argv) > 2 else None, float(sys.argv[3]) if len(sys.argv) > 3 else None)
    print(json.dumps({k: v for k, v in r.items() if k not in ("gas_turbine",)}, indent=1, default=str)[:4000])
