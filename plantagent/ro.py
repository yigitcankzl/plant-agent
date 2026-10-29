"""Reverse osmosis through WaterTAP (IDAES/Pyomo).

The parent process never imports WaterTAP. It speaks JSON to one long-lived worker
started with ``.venv-watertap/bin/python``, the same arrangement process.py uses for
DWSIM, so the DWSIM virtualenv stays untouched.
"""
import json
import math
import select
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WT_PYTHON = ROOT / ".venv-watertap" / "bin" / "python"
SOLVE_TIMEOUT_S = 180

# A and B are the WaterTAP seawater_RO_desalination example, not a vendor projection.
MEMBRANES = {
    "watertap_seawater": {"A_m_per_Pa_s": 4.2e-12, "B_m_per_s": 3.5e-8},
}

SPEC_HELP = (
    "feed or intake {flow_m3_h, TDS_g_L or ions {name: g/L}, T_C, P_bar}; "
    "pretreatment [{id, type media_filter|cartridge_filter|chemical, dP_bar, recovery, notes}] "
    "(chemicals are notes; filters are a specified pressure drop and recovery); "
    "hp_pump {efficiency, P_out_bar or omit to solve the pressure that meets the first stage's recovery, max_bar, max_kW}; "
    "stages [{id, area_m2 or area_m2_per_element+elements_per_vessel+vessels, A_m_per_Pa_s and B_m_per_s or membrane, "
    "max_flux_lmh or max_flux_gfd, max_feed_pressure_bar, min_concentrate_m3_h_per_vessel, recovery, permeate_P_bar, "
    "resolution 0D|1D}]; energy_recovery {type PX|turbine|none, efficiency, booster_pump {efficiency, max_kW}, P_out_bar}; "
    "second_pass {fraction, hp_pump, stage}; posttreatment notes; target_TDS_g_L. "
    "Boron is reported only when the feed includes it and the stage sets B_boron_m_per_s."
)

# ASTM D4516 as applied by FilmTec technical manual Form 609-02004.
# TCF = exp(U * (1/298.15 - 1/T_K)), U = 3020 1/K for a polyamide reference at 25 C.
# NDP = P_feed - dP/2 - P_permeate - pi_fb + pi_permeate  (one pressure unit throughout).
# Q_n = Q_a * (NDP_s/NDP_a) * (TCF_s/TCF_a)
# SP_n = SP_a * (NDP_a/NDP_s) * (C_fb_s/C_fb_a) * (TCF_a/TCF_s)
# dP_n = dP_a * (Q_fb_s/Q_fb_a) ** 1.4   (spiral-wound exponent used with D4516)
NORM_U = 3020.0
NORM_DP_EXP = 1.4
GFD_TO_LMH = 1.697


def _tcf(T_C, U=NORM_U):
    return math.exp(U * (1.0 / 298.15 - 1.0 / (float(T_C) + 273.15)))


def _ndp(cond):
    if cond.get("NDP") is not None:
        return float(cond["NDP"])
    return (float(cond["P_feed"]) - float(cond["dP"]) / 2.0 - float(cond["P_permeate"])
            - float(cond["pi_fb"]) + float(cond["pi_permeate"]))


def normalize(actual, standard, U=NORM_U, dp_exponent=NORM_DP_EXP):
    """ASTM D4516 normalized permeate flow, salt passage and differential pressure.

    ``actual`` and ``standard`` carry Q_permeate, T_C, P_feed, dP, P_permeate, pi_fb,
    pi_permeate (or NDP), salt_passage, C_fb and Q_fb. Salt passage keeps the units you
    pass in (fraction or percent). Pressures share one unit. Osmotic pressures are inputs:
    this function does not estimate them.
    """
    tcf_a, tcf_s = _tcf(actual["T_C"], U), _tcf(standard["T_C"], U)
    ndp_a, ndp_s = _ndp(actual), _ndp(standard)
    if ndp_a <= 0 or ndp_s <= 0:
        raise ValueError("net driving pressure must be positive")
    q_fb_a, q_fb_s = float(actual["Q_fb"]), float(standard["Q_fb"])
    if q_fb_a <= 0:
        raise ValueError("actual feed-brine flow must be positive")
    return {
        "normalized_permeate_flow": float(actual["Q_permeate"]) * (ndp_s / ndp_a) * (tcf_s / tcf_a),
        "normalized_salt_passage": (float(actual["salt_passage"]) * (ndp_a / ndp_s)
                                    * (float(standard["C_fb"]) / float(actual["C_fb"])) * (tcf_a / tcf_s)),
        "normalized_differential_pressure": float(actual["dP"]) * (q_fb_s / q_fb_a) ** float(dp_exponent),
        "TCF_actual": tcf_a, "TCF_standard": tcf_s, "NDP_actual": ndp_a, "NDP_standard": ndp_s,
        "U": U, "dp_exponent": dp_exponent,
        "method": "ASTM D4516 (FilmTec Form 609-02004): Q_n = Q_a*(NDP_s/NDP_a)*(TCF_s/TCF_a); "
                  "SP_n = SP_a*(NDP_a/NDP_s)*(C_fb_s/C_fb_a)*(TCF_a/TCF_s); "
                  "dP_n = dP_a*(Q_fb_s/Q_fb_a)^1.4; TCF = exp(3020*(1/298.15 - 1/T))",
    }


def available():
    return WT_PYTHON.exists()


_PROC, _LOCK = None, __import__("threading").Lock()


def _call(payload, timeout_s=None):
    """One long-lived WaterTAP worker. Restarted if it dies. One lock, same as process.py."""
    global _PROC
    if not WT_PYTHON.exists():
        raise RuntimeError(f"WaterTAP venv is missing ({WT_PYTHON}). "
                           "python3 -m venv .venv-watertap && .venv-watertap/bin/pip install -r requirements-watertap.txt "
                           "&& .venv-watertap/bin/idaes get-extensions")
    limit = timeout_s or SOLVE_TIMEOUT_S
    with _LOCK:
        for _attempt in (0, 1):
            if _PROC is None or _PROC.poll() is not None:
                _PROC = subprocess.Popen([str(WT_PYTHON), "-m", "plantagent.ro", "--serve"],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                         text=True, cwd=ROOT)
            try:
                _PROC.stdin.write(json.dumps(payload) + "\n")
                _PROC.stdin.flush()
                if not select.select([_PROC.stdout], [], [], limit)[0]:
                    _PROC.kill()
                    _PROC = None
                    raise RuntimeError(f"WaterTAP did not finish within {limit} s")
                line = _PROC.stdout.readline()
                if line:
                    r = json.loads(line)
                    if "worker_error" in r:
                        raise RuntimeError(r["worker_error"])
                    return r
            except (BrokenPipeError, json.JSONDecodeError):
                pass
            _PROC.kill()
            _PROC = None
        raise RuntimeError("WaterTAP worker failed")


def run(spec, scale=1.0):
    return _call({"op": "run", "spec": spec, "scale": scale})


def capacity(spec):
    return _call({"op": "capacity", "spec": spec}, timeout_s=900)


def example():
    """Solve WaterTAP's seawater RO desalination flowsheet (pressure exchanger, 0D RO)."""
    return _call({"op": "example"}, timeout_s=300)


# ---------------------------------------------------------------- worker side


def _eff(value, default=0.8):
    if value is None:
        return default
    value = float(value)
    return value / 100.0 if value > 1.0 else value


def _composition(feed):
    """Return TDS g/L, optional boron g/L, and a note about ions that were lumped."""
    boron_keys = {"b", "boron", "boric"}
    note = None
    if feed.get("TDS_g_L") is not None:
        tds = float(feed["TDS_g_L"])
        boron = feed.get("boron_g_L")
        ions = feed.get("ions") or feed.get("ion_table")
        if ions and boron is None:
            for key, val in ions.items():
                if str(key).lower() in boron_keys:
                    boron = float(val)
        return tds, (None if boron is None else float(boron)), note
    ions = feed.get("ions") or feed.get("ion_table")
    if not ions:
        raise ValueError("feed needs TDS_g_L or an ion table (g/L)")
    tds, boron = 0.0, None
    for key, val in ions.items():
        if str(key).lower() in boron_keys:
            boron = float(val) if boron is None else boron + float(val)
        else:
            tds += float(val)
    return tds, boron, "ions other than boron are summed into TDS; the property package does not speciate them"


def _area(stage):
    if stage.get("area_m2") is not None:
        return float(stage["area_m2"])
    try:
        return float(stage["area_m2_per_element"]) * int(stage["elements_per_vessel"]) * int(stage["vessels"])
    except KeyError as e:
        raise ValueError(f"stage {stage.get('id', '')} needs area_m2 or area_m2_per_element, elements_per_vessel and vessels") from e


def _ab(stage):
    if stage.get("membrane"):
        try:
            mem = MEMBRANES[stage["membrane"]]
        except KeyError as e:
            raise ValueError(f"unknown membrane {stage['membrane']!r}; known: {', '.join(MEMBRANES)} "
                             "or give A_m_per_Pa_s and B_m_per_s") from e
        return mem["A_m_per_Pa_s"], mem["B_m_per_s"]
    A, B = stage.get("A_m_per_Pa_s"), stage.get("B_m_per_s")
    if A is None and stage.get("A_LMH_per_bar") is not None:
        A = float(stage["A_LMH_per_bar"]) / 3.6e11
    if A is None or B is None:
        raise ValueError(f"stage {stage.get('id', '')} needs a membrane name or A and B")
    return float(A), float(B)


def _width(stage, area, flow_m3_h):
    if stage.get("width_m"):
        return float(stage["width_m"])
    if stage.get("elements_per_vessel"):
        length = int(stage["elements_per_vessel"]) * float(stage.get("element_length_m", 1.016))
        return area / length
    # no vessel count: pick a width whose 1 mm channel is near 0.15 m/s, where the friction factor solves
    height = float(stage.get("channel_height_m", 1e-3))
    return max((max(float(flow_m3_h), 0.1) / 3600.0) / (0.15 * height), 1.0)


def _erd_kind(spec):
    erd = spec.get("energy_recovery") or {}
    kind = str(erd.get("type") or "none").lower().replace("-", "_").replace(" ", "_")
    if kind in ("px", "pressure_exchanger"):
        return "pressure_exchanger"
    if kind in ("turbine", "pump_as_turbine", "pat"):
        return "pump_as_turbine"
    if kind in ("none", "no", ""):
        return "none"
    raise ValueError(f"energy_recovery type {erd.get('type')!r} must be PX, turbine, or none")


def _flux_limit_lmh(stage):
    if stage.get("max_flux_lmh") is not None:
        return float(stage["max_flux_lmh"])
    if stage.get("max_flux_gfd") is not None:
        return float(stage["max_flux_gfd"]) * GFD_TO_LMH
    return None


def _prepare(spec, scale):
    feed = spec.get("feed") or spec.get("intake")
    if not feed:
        raise ValueError("spec needs feed or intake")
    tds, boron, ion_note = _composition(feed)
    T = float(feed.get("T_C", 25))
    pressure = float(feed.get("P_bar", 1.0))
    flow = float(feed["flow_m3_h"]) * float(scale)
    streams, chemicals = {}, []

    def snap(q, p, modelled):
        row = {"flow_m3_h": round(q, 4), "P_bar": round(p, 4), "T_C": T, "TDS_g_L": round(tds, 5), "modelled": modelled}
        if boron is not None:
            row["boron_g_L"] = round(boron, 6)
        return row

    streams["intake"] = snap(flow, pressure, "feed specification")
    for i, block in enumerate(spec.get("pretreatment") or []):
        kind = str(block.get("type") or "media_filter").lower()
        bid = block.get("id") or f"PT{i + 1}"
        if kind in ("chemical", "note", "notes"):
            chemicals.append({"id": bid, "notes": block.get("notes") or ""})
            streams[bid] = {**snap(flow, pressure, "note only; chemistry is not simulated"), "notes": block.get("notes") or ""}
            continue
        flow *= float(block.get("recovery", 1.0))
        pressure -= float(block.get("dP_bar", 0.0))
        if pressure <= 0.05:
            raise ValueError(f"{bid} drops the feed below 0.05 bar")
        streams[bid] = snap(flow, pressure, "specified pressure drop and recovery; concentration unchanged")
    stages = spec.get("stages") or spec.get("stage")
    if isinstance(stages, dict):
        stages = [stages]
    if not stages:
        raise ValueError("spec needs at least one RO stage")
    hp = dict(spec.get("hp_pump") or spec.get("pump") or {})
    if hp.get("P_out_bar") is None and stages[0].get("recovery") is None:
        raise ValueError("set hp_pump.P_out_bar, or a recovery on the first stage so the feed pressure can be solved")
    if hp.get("P_out_bar") is None and len(stages) > 1:
        raise ValueError("set hp_pump.P_out_bar when there is more than one stage")
    boron_note = None
    if boron is not None:
        needing = list(stages)
        second = spec.get("second_pass") or {}
        if second.get("stage"):
            needing.append(second["stage"])
        if any(s.get("B_boron_m_per_s") is None for s in needing):
            boron_note = "boron is in the feed but B_boron_m_per_s is not set on every stage, so boron passage is not modelled"
            boron = None
    return {"flow_m3_h": flow, "P_bar": pressure, "T_C": T, "TDS_g_L": tds, "boron_g_L": boron,
            "boron_note": boron_note,
            "ion_note": ion_note, "streams": streams, "chemicals": chemicals, "stages": stages, "hp": hp,
            "solve_pressure": hp.get("P_out_bar") is None, "erd": _erd_kind(spec),
            "erd_spec": spec.get("energy_recovery") or {}, "second": spec.get("second_pass"),
            "target_TDS_g_L": spec.get("target_TDS_g_L"), "post": spec.get("posttreatment")}


def _boot():
    import logging
    logging.getLogger("idaes").setLevel(logging.ERROR)
    logging.getLogger("pyomo").setLevel(logging.ERROR)
    from pyomo.environ import ConcreteModel, TransformationFactory, value
    from pyomo.network import Arc
    from pyomo.opt import TerminationCondition
    from idaes.core import FlowsheetBlock
    from idaes.core.util.initialization import propagate_state
    from idaes.core.util.model_statistics import degrees_of_freedom
    from idaes.models.unit_models import Feed, Mixer, Product, Separator
    from idaes.models.unit_models.mixer import MomentumMixingType
    import idaes.core.util.scaling as iscale
    from watertap.core.solvers import get_solver
    from watertap.property_models.multicomp_aq_sol_prop_pack import (
        DensityCalculation, MaterialFlowBasis, MCASParameterBlock)
    from watertap.unit_models.pressure_changer import EnergyRecoveryDevice, Pump
    from watertap.unit_models.pressure_exchanger import PressureExchanger
    from watertap.unit_models.reverse_osmosis_0D import (
        ConcentrationPolarizationType, MassTransferCoefficient, PressureChangeType, ReverseOsmosis0D)
    from watertap.unit_models.reverse_osmosis_1D import ReverseOsmosis1D
    solver = get_solver()
    solver.options["max_cpu_time"] = 60
    solver.options["print_level"] = 0
    return locals()


_LIBS = None


def _L():
    global _LIBS
    if _LIBS is None:
        try:
            _LIBS = _boot()
        except Exception as ex:  # noqa: BLE001
            raise RuntimeError(f"WaterTAP failed to load ({ex}). In .venv-watertap run: idaes get-extensions") from ex
    return _LIBS


def _add_ro(fs, name, prop, stage, boron, flow_m3_h):
    L = _L()
    resolution = str(stage.get("resolution") or "0D").upper()
    cls = L["ReverseOsmosis1D"] if resolution == "1D" else L["ReverseOsmosis0D"]
    kw = dict(property_package=prop, has_pressure_change=True,
              pressure_change_type=L["PressureChangeType"].calculated,
              mass_transfer_coefficient=L["MassTransferCoefficient"].calculated,
              concentration_polarization_type=L["ConcentrationPolarizationType"].calculated)
    if resolution == "1D":
        kw["finite_elements"] = int(stage.get("finite_elements", 6))
    unit = cls(**kw)
    setattr(fs, name, unit)
    area = _area(stage)
    A, B = _ab(stage)
    unit.A_comp.fix(A)
    unit.B_comp.fix(B)
    if boron is not None:
        unit.B_comp[0, "boron"].fix(float(stage["B_boron_m_per_s"]))
    unit.feed_side.channel_height.fix(float(stage.get("channel_height_m", 1e-3)))
    unit.feed_side.spacer_porosity.fix(float(stage.get("spacer_porosity", 0.9)))
    unit.permeate.pressure[0].fix(float(stage.get("permeate_P_bar", 1.01325)) * 1e5)
    unit.width.fix(_width(stage, area, flow_m3_h))
    unit.area.fix(area)
    unit.recovery_mass_phase_comp.setlb(None)
    unit.flux_mass_phase_comp.setlb(None)
    L["iscale"].set_scaling_factor(unit.area, 1.0 / area)
    return unit, area


def _fix_pump(pump, efficiency, p_bar, p_bounds=(1.5e5, 150e5)):
    pump.efficiency_pump.fix(_eff(efficiency))
    pump.control_volume.properties_out[0].pressure.setlb(p_bounds[0])
    pump.control_volume.properties_out[0].pressure.setub(p_bounds[1])
    if p_bar is not None:
        pump.control_volume.properties_out[0].pressure.fix(float(p_bar) * 1e5)
    _L()["iscale"].set_scaling_factor(pump.control_volume.work, 1e-5)


def _state_mass(prop):
    value = _L()["value"]
    return sum(float(value(var)) for var in prop.flow_mass_phase_comp.values())


def _set_vol(prop, dens):
    """flow_vol is not a port variable, so a propagated state leaves it at its initial value."""
    vol = _state_mass(prop) / dens
    if hasattr(prop, "flow_vol_phase"):
        prop.flow_vol_phase["Liq"].set_value(vol)
    else:
        prop.flow_vol.set_value(vol)


def _build(job):
    L = _L()
    m = L["ConcreteModel"]()
    m.fs = L["FlowsheetBlock"](dynamic=False)
    solutes = ["tds"] + (["boron"] if job["boron_g_L"] is not None else [])
    diff = {("Liq", "tds"): 1.47e-9}
    mw = {"tds": 31.4e-3}
    if "boron" in solutes:
        diff[("Liq", "boron")] = 1.63e-9
        mw["boron"] = 10.81e-3
    m.fs.properties = L["MCASParameterBlock"](
        solute_list=solutes, diffusivity_data=diff, mw_data=mw,
        material_flow_basis=L["MaterialFlowBasis"].mass, ignore_neutral_charge=True,
        density_calculation=L["DensityCalculation"].seawater)
    prop = m.fs.properties
    m.fs.feed = L["Feed"](property_package=prop)
    flow_vol = job["flow_m3_h"] / 3600.0
    tds = job["TDS_g_L"]
    m.fs.feed.temperature[0].fix(job["T_C"] + 273.15)
    m.fs.feed.pressure[0].fix(job["P_bar"] * 1e5)
    var_args = {("flow_vol_phase", "Liq"): flow_vol, ("conc_mass_phase_comp", ("Liq", "tds")): tds}
    if job["boron_g_L"] is not None:
        var_args[("conc_mass_phase_comp", ("Liq", "boron"))] = job["boron_g_L"]
    m.fs.feed.properties.calculate_state(var_args=var_args, hold_state=True)
    iscale = L["iscale"]
    iscale.set_scaling_factor(m.fs.feed.properties[0].flow_vol_phase["Liq"], 10.0 / flow_vol)
    iscale.set_scaling_factor(m.fs.feed.properties[0].conc_mass_phase_comp["Liq", "tds"], 10.0 / max(tds, 1e-6))
    m.fs.hp = L["Pump"](property_package=prop)
    p_init = job["hp"].get("P_out_bar")
    if p_init is None:
        p_init = float(job["hp"].get("P_guess_bar", 60))
    _fix_pump(m.fs.hp, job["hp"].get("efficiency"), p_init)
    ros = []
    for i, stage in enumerate(job["stages"]):
        unit, _area_m2 = _add_ro(m.fs, f"ro{i}", prop, stage, job["boron_g_L"], job["flow_m3_h"])
        ros.append(unit)
    arcs = []
    if job["erd"] == "pressure_exchanger":
        m.fs.split = L["Separator"](property_package=prop, outlet_list=["HP", "PXR"])
        m.fs.mix = L["Mixer"](property_package=prop, momentum_mixing_type=L["MomentumMixingType"].equality,
                              inlet_list=["HP", "PX"])
        m.fs.px = L["PressureExchanger"](property_package=prop)
        m.fs.booster = L["Pump"](property_package=prop)
        erd = job["erd_spec"]
        m.fs.px.efficiency_pressure_exchanger.fix(_eff(erd.get("efficiency"), 0.95))
        _fix_pump(m.fs.booster, (erd.get("booster_pump") or {}).get("efficiency"), None)
        m.fs.booster.control_volume.properties_out[0].pressure.unfix()
        iscale.set_scaling_factor(m.fs.px.feed_side.work, 1e-5)
        iscale.set_scaling_factor(m.fs.px.brine_side.work, 1e-5)
        arcs += [("a_feed", m.fs.feed.outlet, m.fs.split.inlet),
                 ("a_hp_in", m.fs.split.HP, m.fs.hp.inlet),
                 ("a_hp_out", m.fs.hp.outlet, m.fs.mix.HP),
                 ("a_px_feed", m.fs.split.PXR, m.fs.px.feed_inlet),
                 ("a_px_brine", ros[-1].retentate, m.fs.px.brine_inlet),
                 ("a_boost_in", m.fs.px.feed_outlet, m.fs.booster.inlet),
                 ("a_boost_out", m.fs.booster.outlet, m.fs.mix.PX),
                 ("a_ro0", m.fs.mix.outlet, ros[0].inlet)]
    elif job["erd"] == "pump_as_turbine":
        m.fs.erd = L["EnergyRecoveryDevice"](property_package=prop)
        erd = job["erd_spec"]
        _fix_pump(m.fs.erd, erd.get("efficiency"), erd.get("P_out_bar", 1.01325), p_bounds=(5e4, 150e5))
        arcs += [("a_feed", m.fs.feed.outlet, m.fs.hp.inlet),
                 ("a_hp_out", m.fs.hp.outlet, ros[0].inlet),
                 ("a_erd", ros[-1].retentate, m.fs.erd.inlet)]
    else:
        arcs += [("a_feed", m.fs.feed.outlet, m.fs.hp.inlet),
                 ("a_hp_out", m.fs.hp.outlet, ros[0].inlet)]
    for i in range(len(ros) - 1):
        arcs.append((f"a_between{i + 1}", ros[i].retentate, ros[i + 1].inlet))
    if len(ros) == 1:
        perm_src = ros[0].permeate
    else:
        m.fs.pmix = L["Mixer"](property_package=prop, momentum_mixing_type=L["MomentumMixingType"].minimize,
                               inlet_list=[f"p{i}" for i in range(len(ros))])
        for i, ro in enumerate(ros):
            arcs.append((f"a_perm{i}", ro.permeate, getattr(m.fs.pmix, f"p{i}")))
        perm_src = m.fs.pmix.outlet
    m.fs.product = L["Product"](property_package=prop)
    m.fs.brine = L["Product"](property_package=prop)
    second = job["second"]
    if second:
        fraction = float(second.get("fraction", 1.0))
        if not 0 < fraction <= 1:
            raise ValueError("second_pass.fraction must be between 0 and 1")
        sp_stage = second.get("stage") or {}
        sp_hp = second.get("hp_pump") or {}
        if sp_hp.get("P_out_bar") is None:
            raise ValueError("second_pass.hp_pump.P_out_bar is required")
        m.fs.sp = L["Pump"](property_package=prop)
        _fix_pump(m.fs.sp, sp_hp.get("efficiency"), sp_hp.get("P_out_bar"))
        m.fs.spro, _sp_area = _add_ro(m.fs, "spro", prop, sp_stage, job["boron_g_L"], job["flow_m3_h"])
        m.fs.sp_brine = L["Product"](property_package=prop)
        arcs.append(("a_sp_brine", m.fs.spro.retentate, m.fs.sp_brine.inlet))
        if fraction < 1:
            m.fs.spsplit = L["Separator"](property_package=prop, outlet_list=["pass2", "bypass"])
            m.fs.spmix = L["Mixer"](property_package=prop, momentum_mixing_type=L["MomentumMixingType"].minimize,
                                    inlet_list=["pass2", "bypass"])
            m.fs.spsplit.split_fraction[0, "pass2"].fix(fraction)
            arcs += [("a_to_split", perm_src, m.fs.spsplit.inlet),
                     ("a_sp_in", m.fs.spsplit.pass2, m.fs.sp.inlet),
                     ("a_sp_ro", m.fs.sp.outlet, m.fs.spro.inlet),
                     ("a_sp_perm", m.fs.spro.permeate, m.fs.spmix.pass2),
                     ("a_bypass", m.fs.spsplit.bypass, m.fs.spmix.bypass),
                     ("a_product", m.fs.spmix.outlet, m.fs.product.inlet)]
        else:
            arcs += [("a_sp_in", perm_src, m.fs.sp.inlet),
                     ("a_sp_ro", m.fs.sp.outlet, m.fs.spro.inlet),
                     ("a_product", m.fs.spro.permeate, m.fs.product.inlet)]
    else:
        arcs.append(("a_product", perm_src, m.fs.product.inlet))
    if job["erd"] == "pressure_exchanger":
        arcs.append(("a_brine", m.fs.px.brine_outlet, m.fs.brine.inlet))
    elif job["erd"] == "pump_as_turbine":
        arcs.append(("a_brine", m.fs.erd.outlet, m.fs.brine.inlet))
    else:
        arcs.append(("a_brine", ros[-1].retentate, m.fs.brine.inlet))
    for name, src, dest in arcs:
        setattr(m.fs, name, L["Arc"](source=src, destination=dest))
    L["TransformationFactory"]("network.expand_arcs").apply_to(m)
    iscale.calculate_scaling_factors(m)
    m._ros = ros  # noqa: SLF001 - worker-only handle, not a Pyomo component
    return m


def _init_unit(unit):
    """Unit initialization sometimes holds the inlet fixed when it gives up. Release it and continue."""
    try:
        unit.initialize()
    except Exception:
        from pyomo.environ import Var
        feed_side = getattr(unit, "feed_side", None)
        inlet = getattr(feed_side, "properties_in", None) if feed_side is not None else None
        if inlet is not None:
            for var in inlet[0].component_data_objects(Var):
                if var.fixed:
                    var.unfix()


def _initialize(m, job):
    L = _L()
    value, propagate = L["value"], L["propagate_state"]
    ros = m._ros
    m.fs.feed.initialize()
    if job["erd"] == "pressure_exchanger":
        propagate(m.fs.a_feed)
        comps = list(m.fs.properties.component_list)
        m.fs.split.split_fraction[0, "PXR"].fix(0.55)
        m.fs.split.initialize()
        m.fs.split.split_fraction[0, "PXR"].unfix()
        propagate(m.fs.a_hp_in)
        m.fs.hp.initialize()
        propagate(m.fs.a_hp_out)
        p_out = m.fs.hp.control_volume.properties_out[0]
        for j in comps:
            m.fs.mix.PX_state[0].flow_mass_phase_comp["Liq", j].set_value(
                value(m.fs.split.PXR_state[0].flow_mass_phase_comp["Liq", j]))
        m.fs.mix.PX_state[0].temperature.set_value(value(p_out.temperature))
        m.fs.mix.PX_state[0].pressure.set_value(value(p_out.pressure))
        m.fs.mix.initialize()
        propagate(m.fs.a_ro0)
        for i, ro in enumerate(ros):
            if i:
                propagate(getattr(m.fs, f"a_between{i}"))
            ro.initialize()
        brine_src = ros[-1].feed_side.properties_out[0]
        # flow_vol_phase on the splitter stays at its initial value, so the split is taken from mass
        frac = _state_mass(brine_src) / _state_mass(m.fs.split.mixed_state[0])
        m.fs.split.split_fraction[0, "PXR"].fix(min(0.9, max(0.05, frac)))
        m.fs.split.initialize()
        m.fs.split.split_fraction[0, "PXR"].unfix()
        propagate(m.fs.a_hp_in)
        m.fs.hp.initialize()
        propagate(m.fs.a_hp_out)
        propagate(m.fs.a_px_feed)
        propagate(m.fs.a_px_brine)
        # The unit initializer demands inlet volumes within 0.1 percent and gives up when
        # concentrate is denser than seawater. Seed the same pressures it would have and let the NLP finish.
        px = m.fs.px
        feed_in = px.feed_side.properties_in[0]
        brine_in = px.brine_side.properties_in[0]
        feed_out = px.feed_side.properties_out[0]
        brine_out = px.brine_side.properties_out[0]
        for src, dst in ((feed_in, feed_out), (brine_in, brine_out)):
            for j in comps:
                dst.flow_mass_phase_comp["Liq", j].set_value(value(src.flow_mass_phase_comp["Liq", j]))
            dst.temperature.set_value(value(src.temperature))
            dst.flow_vol_phase["Liq"].set_value(value(src.flow_vol_phase["Liq"]))
        p_feed = float(value(feed_in.pressure))
        p_brine = float(value(brine_in.pressure))
        eff = float(value(px.efficiency_pressure_exchanger[0]))
        p_feed_out = p_feed + eff * (p_brine - p_feed)
        feed_out.pressure.set_value(p_feed_out)
        brine_out.pressure.set_value(p_feed)
        px.feed_side.deltaP[0].set_value(p_feed_out - p_feed)
        px.brine_side.deltaP[0].set_value(p_feed - p_brine)
        propagate(m.fs.a_boost_in)
        m.fs.booster.control_volume.properties_out[0].pressure.fix(value(p_out.pressure))
        m.fs.booster.initialize()
        m.fs.booster.control_volume.properties_out[0].pressure.unfix()
        propagate(m.fs.a_boost_out)
    else:
        propagate(m.fs.a_feed)
        m.fs.hp.initialize()
        propagate(m.fs.a_hp_out)
        for i, ro in enumerate(ros):
            if i:
                propagate(getattr(m.fs, f"a_between{i}"))
            ro.initialize()
        if job["erd"] == "pump_as_turbine":
            propagate(m.fs.a_erd)
            m.fs.erd.initialize()
    if job["second"]:
        propagate(m.fs.a_sp_in)
        m.fs.sp.initialize()
        propagate(m.fs.a_sp_ro)
        src = ros[0].mixed_permeate[0]
        dens = _state_mass(src) / value(src.flow_vol_phase["Liq"])
        _set_vol(m.fs.sp.control_volume.properties_in[0], dens)
        _set_vol(m.fs.sp.control_volume.properties_out[0], dens)
        _set_vol(m.fs.spro.feed_side.properties_in[0], dens)
        _init_unit(m.fs.spro)


def _prop_stream(prop, boron):
    L = _L()
    value = L["value"]
    row = {"flow_m3_h": round(float(value(prop.flow_vol_phase["Liq"])) * 3600, 4),
           "P_bar": round(float(value(prop.pressure)) / 1e5, 4),
           "T_C": round(float(value(prop.temperature)) - 273.15, 3),
           "TDS_g_L": round(float(value(prop.conc_mass_phase_comp["Liq", "tds"])), 5)}
    if boron:
        row["boron_g_L"] = round(float(value(prop.conc_mass_phase_comp["Liq", "boron"])), 6)
    return row


def _blend(rows):
    q = sum(r["flow_m3_h"] for r in rows)
    out = {"flow_m3_h": round(q, 4),
           "P_bar": round(min(r["P_bar"] for r in rows), 4),
           "T_C": round(sum(r["T_C"] * r["flow_m3_h"] for r in rows) / q, 3),
           "TDS_g_L": round(sum(r["TDS_g_L"] * r["flow_m3_h"] for r in rows) / q, 5)}
    if rows and "boron_g_L" in rows[0]:
        out["boron_g_L"] = round(sum(r["boron_g_L"] * r["flow_m3_h"] for r in rows) / q, 6)
    return out


def _lmh(ro, mass_flux):
    dens = float(_L()["value"](ro.dens_solvent))
    return float(mass_flux) / dens * 3.6e6


def _add_check(out, uid, what, observed, limit, unit, higher_is_worse=True):
    if observed is None or limit is None or float(limit) == 0:
        return
    util = float(observed) / float(limit) if higher_is_worse else float(limit) / float(observed)
    out.append({"id": uid, "check": what, "value": round(float(observed), 4), "limit": round(float(limit), 4),
                "unit": unit, "utilisation": round(util, 3)})


def _pack(m, job, solve_s):
    L = _L()
    value = L["value"]
    boron = job["boron_g_L"] is not None
    streams = dict(job["streams"])
    streams["hp_suction"] = _prop_stream(m.fs.feed.properties[0], boron)
    streams["hp_discharge"] = _prop_stream(m.fs.hp.control_volume.properties_out[0], boron)
    stage_rows, checks, first_perms = [], [], []
    for i, (ro, stage) in enumerate(zip(m._ros, job["stages"])):
        xs = sorted({key[1] for key in ro.flux_mass_phase_comp.keys()})
        lead = _lmh(ro, value(ro.flux_mass_phase_comp[0, xs[0], "Liq", "H2O"]))
        avg = _lmh(ro, value(ro.flux_mass_phase_comp_avg[0, "Liq", "H2O"]))
        recovery = float(value(ro.recovery_vol_phase[0, "Liq"]))
        pin = float(value(ro.inlet.pressure[0])) / 1e5
        perm = _prop_stream(ro.mixed_permeate[0], boron)
        conc = _prop_stream(ro.feed_side.properties_out[0], boron)
        sid = stage.get("id") or f"RO-{i + 1}"
        streams[f"{sid}_permeate"] = perm
        streams[f"{sid}_concentrate"] = conc
        first_perms.append(perm)
        stage_rows.append({"id": sid, "area_m2": round(float(value(ro.area)), 2), "recovery": round(recovery, 5),
                           "feed_pressure_bar": round(pin, 4), "flux_lmh_avg": round(avg, 4),
                           "flux_gfd_avg": round(avg / GFD_TO_LMH, 4), "flux_lmh_lead": round(lead, 4),
                           "flux_gfd_lead": round(lead / GFD_TO_LMH, 4),
                           "resolution": str(stage.get("resolution") or "0D").upper(),
                           "permeate_TDS_g_L": perm["TDS_g_L"], "concentrate_m3_h": conc["flow_m3_h"]})
        flux_lim = _flux_limit_lmh(stage)
        _add_check(checks, sid, "feed pressure vs max", pin, stage.get("max_feed_pressure_bar"), "bar")
        _add_check(checks, sid, "average flux vs max", avg, flux_lim, "LMH")
        _add_check(checks, sid, "lead-element flux vs max", lead, flux_lim, "LMH")
        if stage.get("vessels") and stage.get("min_concentrate_m3_h_per_vessel") is not None:
            _add_check(checks, sid, "concentrate flow vs minimum per vessel",
                       conc["flow_m3_h"] / float(stage["vessels"]), stage["min_concentrate_m3_h_per_vessel"],
                       "m3/h", higher_is_worse=False)
        _add_check(checks, sid, "recovery vs design", recovery, stage.get("recovery"), "fraction")
    # Product/brine blocks close the network, but their intensive properties stay at the initial
    # state. Report the unit states, which the solve actually updated.
    train = first_perms[0] if len(first_perms) == 1 else _blend(first_perms)
    if job["erd"] == "pressure_exchanger":
        brine = _prop_stream(m.fs.px.brine_side.properties_out[0], boron)
    elif job["erd"] == "pump_as_turbine":
        brine = _prop_stream(m.fs.erd.control_volume.properties_out[0], boron)
    else:
        brine = dict(streams[f"{stage_rows[-1]['id']}_concentrate"])
    streams["brine"] = brine
    pumps = {"HP": round(float(value(m.fs.hp.work_mechanical[0])) / 1000.0, 4)}
    _add_check(checks, job["hp"].get("id") or "HP", "discharge pressure vs max",
               streams["hp_discharge"]["P_bar"], job["hp"].get("max_bar"), "bar")
    _add_check(checks, job["hp"].get("id") or "HP", "shaft power vs motor", pumps["HP"], job["hp"].get("max_kW"), "kW")
    if job["erd"] == "pressure_exchanger":
        pumps["booster"] = round(float(value(m.fs.booster.work_mechanical[0])) / 1000.0, 4)
        boost = job["erd_spec"].get("booster_pump") or {}
        _add_check(checks, "booster", "shaft power vs motor", pumps["booster"], boost.get("max_kW"), "kW")
    elif job["erd"] == "pump_as_turbine":
        pumps["turbine"] = round(float(value(m.fs.erd.work_mechanical[0])) / 1000.0, 4)
    if job["second"]:
        pumps["second_pass"] = round(float(value(m.fs.sp.work_mechanical[0])) / 1000.0, 4)
        sp_hp = job["second"].get("hp_pump") or {}
        _add_check(checks, "second_pass", "shaft power vs motor", pumps["second_pass"], sp_hp.get("max_kW"), "kW")
        _add_check(checks, "second_pass", "discharge pressure vs max",
                   float(value(m.fs.sp.control_volume.properties_out[0].pressure)) / 1e5, sp_hp.get("max_bar"), "bar")
        sp_stage = job["second"].get("stage") or {}
        sp_avg = _lmh(m.fs.spro, value(m.fs.spro.flux_mass_phase_comp_avg[0, "Liq", "H2O"]))
        sp_xs = sorted({key[1] for key in m.fs.spro.flux_mass_phase_comp.keys()})
        sp_lead = _lmh(m.fs.spro, value(m.fs.spro.flux_mass_phase_comp[0, sp_xs[0], "Liq", "H2O"]))
        sp_pin = float(value(m.fs.spro.inlet.pressure[0])) / 1e5
        sp_rec = float(value(m.fs.spro.recovery_vol_phase[0, "Liq"]))
        _add_check(checks, sp_stage.get("id") or "RO-2P", "feed pressure vs max", sp_pin, sp_stage.get("max_feed_pressure_bar"), "bar")
        _add_check(checks, sp_stage.get("id") or "RO-2P", "average flux vs max", sp_avg, _flux_limit_lmh(sp_stage), "LMH")
        _add_check(checks, sp_stage.get("id") or "RO-2P", "lead-element flux vs max", sp_lead, _flux_limit_lmh(sp_stage), "LMH")
        _add_check(checks, sp_stage.get("id") or "RO-2P", "recovery vs design", sp_rec, sp_stage.get("recovery"), "fraction")
        sp_perm = _prop_stream(m.fs.spro.mixed_permeate[0], boron)
        streams["second_pass_permeate"] = sp_perm
        streams["second_pass_concentrate"] = _prop_stream(m.fs.spro.feed_side.properties_out[0], boron)
        fraction = float(job["second"].get("fraction", 1.0))
        if fraction >= 1:
            product = sp_perm
        else:
            bypass = dict(train)
            bypass["flow_m3_h"] = round(train["flow_m3_h"] * (1.0 - fraction), 4)
            product = _blend([bypass, sp_perm])
        stage_rows.append({"id": sp_stage.get("id") or "RO-2P", "recovery": round(sp_rec, 5),
                           "feed_pressure_bar": round(sp_pin, 4), "flux_lmh_avg": round(sp_avg, 4),
                           "flux_lmh_lead": round(sp_lead, 4), "permeate_TDS_g_L": sp_perm["TDS_g_L"]})
    else:
        product = train
    streams["permeate"] = product
    net_kW = sum(pumps.values())
    sec = net_kW / product["flow_m3_h"] if product["flow_m3_h"] else None
    intake_q = job["streams"]["intake"]["flow_m3_h"]
    not_modelled = []
    if job.get("boron_note"):
        not_modelled.append(job["boron_note"])
    elif not boron:
        not_modelled.append("boron (pass boron in the feed and B_boron_m_per_s on each stage to track it)")
    if any(str(s.get("resolution") or "0D").upper() != "1D" for s in job["stages"]):
        not_modelled.append("per-element flux profile (0D reports feed-end flux as the lead value and the length-averaged flux; set resolution to 1D to discretize the vessel)")
    not_modelled.append("pretreatment chemistry (filters are a specified pressure drop and recovery; chemical steps are notes)")
    not_modelled.append("post-treatment reactions (stored as notes)")
    if job["ion_note"]:
        not_modelled.append(job["ion_note"])
    if job["second"]:
        not_modelled.append("second-pass concentrate recycle to the first-pass feed (the concentrate is an outlet)")
    post = job["post"]
    post_note = post if isinstance(post, str) else (post or {}).get("notes") if isinstance(post, dict) else None
    _add_check(checks, "permeate", "permeate TDS vs target", product["TDS_g_L"], job["target_TDS_g_L"], "g/L")
    checks.sort(key=lambda c: -c["utilisation"])
    return {"scale": None, "errors": [], "solve_s": round(solve_s, 3),
            "recovery": round(product["flow_m3_h"] / intake_q, 5) if intake_q else None,
            "ro_recovery": round(sum(p["flow_m3_h"] for p in first_perms) / job["flow_m3_h"], 5) if job["flow_m3_h"] else None,
            "feed_pressure_bar": stage_rows[0]["feed_pressure_bar"],
            "permeate_TDS_g_L": product["TDS_g_L"],
            "boron": product.get("boron_g_L", "not modelled"),
            "sec_kWh_m3": round(sec, 4) if sec is not None else None,
            "flux_lmh_avg": stage_rows[0]["flux_lmh_avg"], "flux_lmh_lead": stage_rows[0]["flux_lmh_lead"],
            "flux_gfd_avg": stage_rows[0].get("flux_gfd_avg"), "pumps_kW": pumps,
            "streams": streams, "stages": stage_rows, "checks": checks, "not_modelled": not_modelled,
            "notes": {"chemicals": job["chemicals"], "posttreatment": post_note,
                      "pretreatment": "specified pressure drop and recovery at constant concentration",
                      "flux_lead": "feed-end flux of the membrane channel"}}


def _solve(spec, scale=1.0):
    t0 = time.perf_counter()
    try:
        job = _prepare(spec, scale)
        m = _build(job)
        init_fail = None
        try:
            _initialize(m, job)
        except Exception as ex:  # noqa: BLE001 - a bad initial point can still solve
            init_fail = str(ex)
        if job["solve_pressure"]:
            m.fs.hp.control_volume.properties_out[0].pressure.unfix()
            m._ros[0].recovery_vol_phase[0, "Liq"].fix(float(job["stages"][0]["recovery"]))
        dof = _L()["degrees_of_freedom"](m)
        if dof != 0:
            extra = f"; initialization: {init_fail}" if init_fail else ""
            raise RuntimeError(f"RO flowsheet has {dof} degrees of freedom; the spec does not close{extra}")
        results = _L()["solver"].solve(m, tee=False)
        tc = results.solver.termination_condition
        ok = tc in (_L()["TerminationCondition"].optimal, _L()["TerminationCondition"].locallyOptimal,
                    _L()["TerminationCondition"].feasible)
        if not ok:
            extra = f"; initialization: {init_fail}" if init_fail else ""
            return {"scale": scale, "errors": [f"solver finished {tc}{extra}"], "checks": [],
                    "solve_s": round(time.perf_counter() - t0, 3)}
        out = _pack(m, job, time.perf_counter() - t0)
        out["scale"] = scale
        return out
    except (RuntimeError, ValueError) as ex:
        return {"scale": scale, "errors": [str(ex)], "checks": [], "solve_s": round(time.perf_counter() - t0, 3)}


def _capacity(spec):
    def worst(scale):
        r = _solve(spec, scale)
        checks = [c for c in r.get("checks") or [] if "utilisation" in c]
        top = max(checks, key=lambda c: c["utilisation"]) if checks else None
        return top, checks, r.get("errors") or []

    base, base_checks, errs = worst(1.0)
    if base is None:
        return {"error": "no limits to check; set a max pressure, flux, pump power, permeate TDS, recovery or minimum concentrate flow",
                "errors": errs}
    lo, hi = (0.1, 1.0) if base["utilisation"] > 1 else (1.0, 1.0)

    def over(top, errors):
        return top is None or bool(errors) or top["utilisation"] > 1

    while base["utilisation"] <= 1 and hi < 5:
        hi *= 1.25
        top, _, errors = worst(hi)
        if over(top, errors):
            break
        lo = hi
    for _ in range(12):
        mid = (lo + hi) / 2
        top, _, errors = worst(mid)
        lo, hi = (lo, mid) if over(top, errors) else (mid, hi)
    top, at_cap, _ = worst(lo)
    return {"capacity_multiple": round(lo, 3), "limited_by": top, "checks_at_capacity": at_cap,
            "checks_at_base": base_checks, "errors": errs,
            "note": "multiple of the feed flow at which the first stated limit reaches 100 %"}


def _example():
    from pyomo.environ import value
    from watertap.flowsheets.seawater_RO_desalination.seawater_RO_desalination import (
        add_costing, build, initialize_system, set_operating_conditions, solve)
    t0 = time.perf_counter()
    m = build(erd_type="pressure_exchanger", RO_1D=False)
    set_operating_conditions(m)
    initialize_system(m)
    t1 = time.perf_counter()
    solve(m, tee=False)
    add_costing(m)
    m.fs.costing.initialize()
    solve(m, tee=False)
    t2 = time.perf_counter()
    ro = m.fs.desalination.RO
    perm = ro.mixed_permeate[0]
    return {"source": "watertap.flowsheets.seawater_RO_desalination main() defaults: pressure_exchanger, RO 0D",
            "recovery": float(value(ro.recovery_vol_phase[0, "Liq"])),
            "feed_pressure_bar": float(value(ro.inlet.pressure[0])) / 1e5,
            "permeate_TDS_g_L": float(value(perm.conc_mass_phase_comp["Liq", "tds"])),
            "permeate_m3_h": float(value(perm.flow_vol_phase["Liq"])) * 3600,
            "sec_kWh_m3": float(value(m.fs.costing.specific_energy_consumption)),
            "hp_kW": float(value(m.fs.desalination.P1.work_mechanical[0])) / 1000,
            "booster_kW": float(value(m.fs.desalination.P2.work_mechanical[0])) / 1000,
            "init_s": round(t1 - t0, 3), "solve_s": round(t2 - t1, 3),
            "boron": "not modelled",
            "notes": "SEC is WaterTAP's specific_energy_consumption (kWh/m3 of product), including zero-order "
                     "pretreatment and post-treatment electricity. The example property list is tds and tss; boron is absent. "
                     "The module's __main__ sets RO_1D=True; the packaged test and this check use the function default, 0D."}


def _worker(a):
    op = a.get("op")
    if op == "run":
        return _solve(a["spec"], float(a.get("scale", 1.0)))
    if op == "capacity":
        return _capacity(a["spec"])
    if op == "example":
        return _example()
    if op == "normalize":
        return normalize(a["actual"], a["standard"], a.get("U", NORM_U), a.get("dp_exponent", NORM_DP_EXP))
    raise ValueError(f"unknown op {op}")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        out = sys.stdout
        sys.stdout = sys.stderr
        for line in sys.stdin:
            try:
                result = _worker(json.loads(line))
            except Exception as ex:  # noqa: BLE001 - report to the caller, keep serving
                result = {"worker_error": f"{type(ex).__name__}: {ex}"[:2000]}
            out.write(json.dumps(result) + "\n")
            out.flush()
    else:
        ex = example()
        assert abs(ex["recovery"] - 0.420696) / 0.420696 < 1e-3, ex
        assert abs(ex["feed_pressure_bar"] - 70.0) < 0.05, ex
        assert abs(ex["permeate_TDS_g_L"] - 0.2126) < 0.002, ex
        assert abs(ex["sec_kWh_m3"] - 3.3917) / 3.3917 < 0.01, ex
        assert ex["boron"] == "not modelled"
        sample = {"Q_permeate": 80, "T_C": 20, "P_feed": 40, "dP": 2, "P_permeate": 1,
                  "pi_fb": 20, "pi_permeate": 0.5, "salt_passage": 1.5, "C_fb": 55, "Q_fb": 120}
        ref = {"Q_permeate": 100, "T_C": 25, "P_feed": 50, "dP": 2, "P_permeate": 1,
               "pi_fb": 22, "pi_permeate": 0.4, "salt_passage": 1.0, "C_fb": 45, "Q_fb": 100}
        n = normalize(sample, ref)
        assert abs(n["normalized_permeate_flow"] - 135.6914432840) < 1e-6, n
        assert abs(n["normalized_salt_passage"] - 0.7235667615) < 1e-6, n
        assert abs(n["normalized_differential_pressure"] - 1.5494453080) < 1e-6, n
        print("example", round(ex["recovery"], 6), round(ex["feed_pressure_bar"], 3),
              round(ex["sec_kWh_m3"], 4), round(ex["permeate_TDS_g_L"], 4),
              "init_s", ex["init_s"], "solve_s", ex["solve_s"])
        print("normalize ok")
