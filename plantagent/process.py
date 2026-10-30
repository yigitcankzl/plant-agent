"""Process plants (chemical, food, pharma, utilities) in DWSIM: build a flowsheet from a JSON spec, solve it, and find
which equipment limits throughput.

DWSIM runs through pythonnet and must run with cwd = its install dir, so every call is a subprocess worker
(about 2 s start-up, then about 0.05 s per solve).
"""
import json
import math
import os
import select
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DW = Path(os.path.expanduser("~/opt/dwsim/usr/local/lib/dwsim"))
DOTNET = Path(os.path.expanduser("~/opt/dotnet"))

SPEC_HELP = {
    "compounds": "DWSIM compound names, e.g. ['Water','Ethanol'], ['Propylene','Propane'], ['Methane','Water','Hydrogen','Carbon monoxide','Carbon dioxide']",
    "package": "property package: 'NRTL' (polar liquids), 'Peng-Robinson (PR)' (hydrocarbons/gases), 'Steam Tables (IAPWS-IF97)' (water/steam only)",
    "feeds": "{stream: {T_C, P_bar, kg_h | m3_h (liquid at feed T), x: {compound: mole fraction}, utility: true for cooling "
             "water/steam/chilled water (not scaled with throughput)}}",
    "units": "list in flow order, each with id and type. "
             "pump: in, out, dP_bar or curve [[m3_h, head_m],...], eff_pct, kind: centrifugal|positive_displacement. "
             "hx: cold [in, out], hot [in, out], U_W_m2K, area_m2 (rating: outlets are computed; for a condensing hot side give "
             "hot_out_T_C, e.g. the saturated condensate temperature, and the cold outlet follows from the energy balance); optional U_ref_flows_m3_h "
             "[hot, cold] (U then varies with flow, each film ~ Q^0.8) and dP_ref_bar [hot, cold] at those flows (dP ~ Q^1.8). "
             "heater|cooler: in, out, T_out_C or duty_kW (scales: true if that duty grows with throughput, e.g. an IT or process heat load). "
             "valve: in, out, dP_bar or kv or P_out_bar; optional cv_rated (US Cv) or kv_rated (one only), "
             "characteristic: equal_percentage|linear (default equal_percentage), rangeability (default 50), "
             "min_travel_pct/max_travel_pct (defaults 10/90). Liquid turbulent Cv only: no choking/cavitation/viscosity correction. "
             "pipe: in, out, length_m, id_mm or dn_mm (DN treated as inside diameter), roughness_mm (default 0.045), "
             "elevation_m (positive = rise), fittings_K (default 0); liquid Darcy-Weisbach/Colebrook, solved as a DWSIM outlet-pressure valve. "
             "tank: in, out, volume_m3 = WORKING volume (about 80 % of nominal unless the data says otherwise), P_bar = vessel "
             "pressure (an atmospheric tank is about 1.013; the outlet leaves at this pressure, which sets pump suction and NPSH), "
             "residence_basis = the product stream that leaves the tank for good (hold time = volume / that flow). "
             "mixer: in [..], out. splitter: in, out [..], fractions [..] or fixed_kg_h {out stream: kg/h} (the first outlet fixed, "
             "the other takes the rest: in a recirculation loop fix the recirculation branch and let the product take the rest). compressor: in, out, P_out_bar, eff_pct. "
             "evaporator: in, vapor, liquid, P_bar (body pressure), evap_frac (fraction of the inlet boiled off), heating [in, out] "
             "(steam that condenses fully), U_W_m2K, area_m2, optional feed_x_NaCl (feed NaCl mass fraction; default saturated at feed T), "
             "x_NaCl (body concentration; omit for saturation). The Water stand-in inlet kg/h is TOTAL feed brine, not water alone. "
             "For a closed forced-circulation loop, net_feed and net_liquid name the fresh feed and net liquid product streams used "
             "for the salt and sensible-heat balance; in and liquid remain the full circulating streams. Optional "
             "heat_balance_tolerance_pct defaults to 2; raise it only to a documented model-closure tolerance, never as equipment headroom. "
             "Reports salt_in_kg_h, salt_kg_h (zero when non-crystallising), crystallising, water_evaporated_per_t_salt, "
             "bpe_K and sensible_correction_kW. With feed_x_NaCl and heating, evap_frac is a maximum: available steam heat "
             "can lower boil-up. The simple water stand-in uses Steam Tables (IAPWS-IF97); brine cp corrects feed sensible heat, "
             "but crystallisation heat and electrolyte phase equilibria are omitted. The stand-in liquid outlet includes "
             "crystals plus mother liquor; liquid_out_brine_kg_h excludes crystals. Applies NaCl BPE to the driving force and checks heater area "
             "and the heat balance (boil-up vs heat the heating steam gives; >1 means the steam cannot sustain the boil-up). "
             "flash: in, vapor, liquid (equilibrium phase split at inlet T and P; use a cooler or valve first). "
             "component_separator: in, product, reject, recover_pct {compound: percent of inlet moles sent to product; omitted compounds default to 100}; fixed-split approximation, not a TEG or PSA design model. "
             "column: in, distillate, bottoms, light_key, heavy_key (compound names), light_key_in_bottoms and "
             "heavy_key_in_distillate (mole fractions), reflux_ratio, P_bar (shortcut method: reports minimum and actual stages, "
             "minimum reflux, condenser and reboiler duty). "
             "reactor: kind conversion|equilibrium|cstr|pfr, in, vapor and liquid (conversion, equilibrium, cstr) or out (pfr), "
             "mode isothermal|adiabatic|outlet_temperature, T_out_C in Celsius, phase Vapor|Liquid|Mixture|Solid, "
             "reactions [{name, base, stoich {compound: coefficient, products positive}, conversion_pct (conversion), "
             "approach_K and lnKeq (equilibrium; empty lnKeq uses Gibbs), A, E_J_mol, orders, Tmin_K, Tmax_K, rate_expression (cstr/pfr; "
             "empty rate_expression is Arrhenius k=A*exp(-E/RT) with E in J/mol, basis 'Molar Concentration', amount mol/m3, rate mol/[m3.s])}]. "
             "cstr needs volume_m3 and headspace (vapor volume fraction, default 0.1, must be > 0) and a liquid holdup: a vapor-only feed does not react. "
             "pfr needs volume_m3, or length_m and diameter_m (volume is then pi*d^2/4*L, m). Optional dP_bar. "
             "Results: conversion_pct of each base compound, duty_kW (DWSIM DeltaQ, kW, negative = heat removed), cooling_kW, T_out_C. "
             "distillation: rigorous column. in, distillate, bottoms, optional vapor (partial condenser), stages, feed_stage "
             "(1 = condenser), condenser total|partial|full_reflux, P_bar, dP_bar, subcool_K. One condenser spec and one reboiler spec: "
             "reflux_ratio, boilup_ratio, distillate_mol_s, bottoms_mol_s, or condenser_spec/reboiler_spec {type, value, units, compound}. "
             "Spec types: Reflux Ratio, Boilup Ratio, Product Molar Flow Rate (units mol/s), Product Mass Flow Rate, Heat Duty, "
             "Component Molar Flow Rate, Component Mass Flow Rate, Component Fraction, Component Recovery, Stream Ratio, Temperature, Feed Recovery. "
             "Results: condenser_kW, reboiler_kW (absolute duties), signed condenser_duty_kW and reboiler_duty_kW, and profile "
             "[{stage, T_C, P_bar, vapour_kg_h, liquid_kg_h, rho_v_kg_m3, rho_l_kg_m3, sigma_N_m, flood_frac}]. "
             "dwsim: any allowlisted DWSIM object. class is the ObjectType name, in and out are stream lists mapped onto the first "
             "material ports in DWSIM's port order (unused ports stay open), energy is an optional energy-stream name or list. "
             "set {Property: value} in the SI unit documented for that property; enums by name. report lists properties to return. "
             "A wrong class or property raises an error that lists the valid names. No arbitrary reflection. "
             "Reactions, feed stage and column specs are not generic properties: use reactor and distillation for those. "
             "recycle: in (the calculated return stream), out (the tear stream used upstream, e.g. into a mixer), guess "
             "{T_C, P_bar, kg_h, x} (closes recirculation loops); guess_scales: true scales that initial tear value during "
             "capacity search. Streams are created by name the first time they appear. Model EVERY "
             "connection on the P&ID that carries process flow (recirculation loops included) or say why it is excluded.",
    "limits": "{unit or stream id: {max_m3_h, min_m3_h (pump minimum continuous flow), max_kW (pump or compressor motor), max_kg_h (compressor suction capacity), max_discharge_C (compressor), max_head_m, npshr_m, "
              "psv_set_barg (relief valve on the pump discharge: discharge must stay below 90 % of set), area_m2 (installed HX "
              "area), out_T_C (outlet the process needs, side: cold|hot), max_dP_hot_bar, max_dP_cold_bar (available pressure "
              "drop), min_residence_min, max_area_m2 (HX frame limit), and for streams max_T_C, max_P_bar (design limit), "
              "max_m3_h (utility supply; checked against 90 % of it to keep a margin), max_velocity_m_s and max_dP_bar (pipe; "
              "3 m/s is a typical liquid pump-discharge screen per Grundfos guidance, not a universal limit), "
              "must_be_liquid: true (e.g. condenser outlet), min_T_out_C (cooler or condenser: the lowest outlet its heat sink allows at "
              "design conditions, e.g. design wet bulb + approach for an evaporative condenser), "
              "max_duty_kW (reactor cooling capacity: compared with cooling_kW, the heat the jacket must remove), "
              "max_T_C on a reactor (outlet temperature), "
              "diameter_m, tray_spacing_m (default 0.5 m, DWSIM's tray spacing), flood_frac_max (default 0.8) for a distillation column: "
              "Fair sieve-tray flood fraction from DWSIM's per-stage traffic. DWSIM does not report flooding. "
              "A unit type with no limit check is reported as 'no limit check for this unit type' and is not treated as within limits. "
              "Allowlisted classes and SI units: docs/dwsim_units.md.}}. Values come from the P&ID or datasheets; cite them.",
}


# ---------------------------------------------------------------- worker side (runs inside the DWSIM process)
def _dwsim():
    from pythonnet import load
    load("coreclr", runtime_config=str(ROOT / "runtime" / "dwsim.runtimeconfig.json"), dotnet_root=str(DOTNET))
    import clr
    sys.path.append(str(DW))
    os.chdir(DW)  # DWSIM resolves its data files relative to cwd
    for d in ["DWSIM.Automation", "DWSIM.Interfaces", "DWSIM.Thermodynamics", "DWSIM.UnitOperations", "DWSIM.GlobalSettings"]:
        clr.AddReference(str(DW / f"{d}.dll"))
    from DWSIM.Automation import Automation3
    return Automation3()


def _r(x, n=0):
    """round() that lets an unsolved (None) value through instead of crashing the whole result."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return round(v, n)


def _valve_sizing(q_m3_s, rho_kg_m3, dp_bar, rated_cv=None, characteristic="equal_percentage", rangeability=50):
    """Basic ISA/IEC liquid Cv equation; no choked-flow, cavitation or viscosity correction."""
    if rho_kg_m3 <= 0 or q_m3_s < 0:
        raise ValueError("valve liquid density and flow must be valid")
    if dp_bar <= 0 and q_m3_s:
        return {"cv_required": None, "opening_pct": 100.0 if rated_cv is not None else None,
                "sizing_error": "no positive liquid pressure drop"}
    cv = q_m3_s / 0.0000630901964 * math.sqrt((rho_kg_m3 / 999.016) / (dp_bar * 14.5037738)) if q_m3_s else 0.0
    result = {"cv_required": cv}
    if rated_cv is not None:
        if rated_cv <= 0 or rangeability <= 1 or characteristic not in ("equal_percentage", "linear"):
            raise ValueError("rated Cv must be positive, rangeability > 1, characteristic equal_percentage or linear")
        fraction = cv / rated_cv
        opening = (1 + math.log(max(fraction, 1e-300)) / math.log(rangeability)) * 100 if characteristic == "equal_percentage" else \
            (fraction - 1 / rangeability) / (1 - 1 / rangeability) * 100
        result["opening_pct"] = max(0.0, opening)
    return result


def _pipe_hydraulics(q_m3_s, rho_kg_m3, mu_pa_s, length_m, diameter_m, roughness_m=0.000045,
                     elevation_m=0, fittings_K=0):
    from fluids.friction import friction_factor
    if (q_m3_s < 0 or rho_kg_m3 <= 0 or mu_pa_s <= 0 or length_m < 0 or diameter_m <= 0 or
            roughness_m < 0 or fittings_K < 0):
        raise ValueError("pipe flow/properties/geometry must be nonnegative and diameter, density, viscosity positive")
    velocity = 4 * q_m3_s / (math.pi * diameter_m ** 2)
    reynolds = rho_kg_m3 * velocity * diameter_m / mu_pa_s
    f = friction_factor(Re=reynolds, eD=roughness_m / diameter_m, Method="Colebrook") if reynolds else 0.0
    dp_bar = (rho_kg_m3 * velocity ** 2 / 2 * (f * length_m / diameter_m + fittings_K) +
              rho_kg_m3 * 9.80665 * elevation_m) / 1e5
    return {"velocity_m_s": velocity, "Reynolds": reynolds, "friction_factor": f, "dP_bar": dp_bar}


def _prop(unit, kind, values=None):
    meta = {"unit": unit, "kind": kind}
    if values:
        meta["values"] = values
    return meta


_F = lambda u="1": _prop(u, "float")  # noqa: E731
_I = lambda u="1": _prop(u, "int")  # noqa: E731
_B = _prop("bool", "bool")
_S = _prop("text", "str")
_E = lambda values: _prop("enum", "enum", values)  # noqa: E731

# Settable properties only. Values are DWSIM's stored SI (Pa, K, kW, m, m2, m3) unless the unit says otherwise.
# Pump and compressor efficiencies are percent, matching the existing wrappers. Enums are set by name.
DWSIM_ALLOW = {
    "Pump": {"DeltaP": _F("Pa"), "POut": _F("Pa"), "Eficiencia": _F("percent"), "Efficiency": _F("percent"),
             "OutletTemperature": _F("K"), "CalcMode": _E(["Delta_P", "OutletPressure", "EnergyStream", "Curves", "Power"])},
    "Valve": {"DeltaP": _F("Pa"), "PressureDrop": _F("Pa"), "OutletPressure": _F("Pa"), "Kv": _F("Kv"),
              "CalcMode": _E(["DeltaP", "OutletPressure", "Kv_Liquid", "Kv_Gas", "Kv_Steam", "Kv_General"])},
    "Heater": {"DeltaQ": _F("kW"), "HeatDuty": _F("kW"), "OutletTemperature": _F("K"), "PressureDrop": _F("Pa"),
               "TemperatureChange": _F("K"), "Efficiency": _F("fraction"),
               "CalcMode": _E(["HeatAdded", "OutletTemperature", "EnergyStream", "OutletVaporFraction", "TemperatureChange", "HeatAddedRemoved"])},
    "Cooler": {"DeltaQ": _F("kW"), "HeatDuty": _F("kW"), "OutletTemperature": _F("K"), "PressureDrop": _F("Pa"),
               "TemperatureChange": _F("K"), "Efficiency": _F("fraction"),
               "CalcMode": _E(["HeatRemoved", "OutletTemperature", "OutletVaporFraction", "TemperatureChange", "EnergyStream"])},
    "HeatExchanger": {"Area": _F("m2"), "OverallCoefficient": _F("W/m2K"), "Q": _F("kW"),
                      "HotSidePressureDrop": _F("Pa"), "ColdSidePressureDrop": _F("Pa"),
                      "CalcMode": _E(["CalcTempHotOut", "CalcTempColdOut", "CalcBothTemp", "CalcBothTemp_UA", "CalcArea",
                                      "ShellandTube_Rating", "ShellandTube_CalcFoulingFactor", "PinchPoint", "ThermalEfficiency",
                                      "OutletVaporFraction1", "OutletVaporFraction2"])},
    "Compressor": {"POut": _F("Pa"), "DeltaP": _F("Pa"), "DeltaQ": _F("kW"), "AdiabaticEfficiency": _F("percent"),
                   "PolytropicEfficiency": _F("percent"), "PressureRatio": _F("1"),
                   "CalcMode": _E(["OutletPressure", "Delta_P", "EnergyStream", "PowerRequired", "Head", "Curves", "PressureRatio"]),
                   "ProcessPath": _E(["Adiabatic", "Polytropic"])},
    "Expander": {"POut": _F("Pa"), "DeltaP": _F("Pa"), "DeltaQ": _F("kW"), "AdiabaticEfficiency": _F("percent"),
                 "PolytropicEfficiency": _F("percent"), "PressureRatio": _F("1"),
                 "CalcMode": _E(["OutletPressure", "Delta_P", "PowerGenerated", "Head", "Curves", "PressureRatio"]),
                 "ProcessPath": _E(["Adiabatic", "Polytropic"])},
    "Tank": {"Volume": _F("m3")},
    "Vessel": {"FlashPressure": _F("Pa"), "FlashTemperature": _F("K"),
               "CalculationMode": _E(["Adiabatic", "Legacy", "HeatingCoolingIsothermic", "HeatingCoolingIsobaric"]),
               "PressureCalculation": _E(["Average", "Maximum", "Minimum"])},
    "Mixer": {"PressureCalculation": _E(["Average", "Maximum", "Minimum"])},
    "Splitter": {"StreamFlowSpec": _F("kg/s"), "Stream2FlowSpec": _F("kg/s"),
                 "OperationMode": _E(["SplitRatios", "StreamMassFlowSpec", "StreamMoleFlowSpec"])},
    "OrificePlate": {"OrificeDiameter": _F("m"), "InternalPipeDiameter": _F("m"), "Beta": _F("1"),
                     "OverallPressureDrop": _F("Pa"), "OrificePressureDrop": _F("Pa"),
                     "OrifType": _E(["CornerTaps", "FlangeTaps", "RadiusTaps"]),
                     "CalculationMethod": _E(["Homogeneous", "Slip"])},
    "SolidSeparator": {"SeparationEfficiency": _F("fraction"), "LiquidSeparationEfficiency": _F("fraction")},
    "Filter": {"PressureDrop": _F("Pa"), "TotalFilterArea": _F("m2"), "SubmergedAreaFraction": _F("fraction"),
               "FilterCycleTime": _F("s"), "CakeRelativeHumidity": _F("fraction"),
               "SpecificCakeResistance": _F("m/kg"), "FilterMediumResistance": _F("1/m"),
               "CalcMode": _E(["Design", "Simulation"])},
    "ShortcutColumn": {"StageHeight": _F("m")},
    "DistillationColumn": {"NumberOfStages": _I("1"), "RefluxRatio": _F("1"), "ColumnPressureDrop": _F("Pa"),
                           "CondenserDeltaP": _F("Pa"), "CondenserDuty": _F("kW"), "ReboilerDuty": _F("kW"),
                           "TraySpacing": _F("m"), "DistillateFlowRate": _F("mol/s"), "MaxIterations": _I("1"),
                           "CondenserType": _E(["Total_Condenser", "Partial_Condenser", "Full_Reflux"])},
    "AbsorptionColumn": {"NumberOfStages": _I("1"), "ColumnPressureDrop": _F("Pa"), "TraySpacing": _F("m"),
                         "MaxIterations": _I("1"), "OperationMode": _E(["Absorber", "Extractor"])},
    "RCT_Conversion": {"OutletTemperature": _F("K"), "ReactorOperationMode": _E(["Isothermic", "Adiabatic", "OutletTemperature", "NonIsothermalNonAdiabatic"])},
    "RCT_Equilibrium": {"OutletTemperature": _F("K"), "ReactorOperationMode": _E(["Isothermic", "Adiabatic", "OutletTemperature", "NonIsothermalNonAdiabatic"])},
    "RCT_Gibbs": {"OutletTemperature": _F("K"), "ReactorOperationMode": _E(["Isothermic", "Adiabatic", "OutletTemperature", "NonIsothermalNonAdiabatic"])},
    "RCT_CSTR": {"Volume": _F("m3"), "Headspace": _F("fraction"), "OutletTemperature": _F("K"), "CatalystAmount": _F("kg"),
                 "ReactorOperationMode": _E(["Isothermic", "Adiabatic", "OutletTemperature", "NonIsothermalNonAdiabatic"])},
    "RCT_PFR": {"Length": _F("m"), "Diameter": _F("m"), "Volume": _F("m3"), "CatalystLoading": _F("kg/m3"),
                "CatalystVoidFraction": _F("fraction"), "CatalystParticleDiameter": _F("m"),
                "UseUserDefinedPressureDrop": _B, "UserDefinedPressureDrop": _F("Pa"), "OutletTemperature": _F("K"),
                "ReactorOperationMode": _E(["Isothermic", "Adiabatic", "OutletTemperature", "NonIsothermalNonAdiabatic"])},
    "OT_Recycle": {"MaximumIterations": _I("1"), "SmoothingFactor": _F("1"),
                   "AccelerationMethod": _E(["None", "Wegstein", "Dominant_Eigenvalue", "GlobalBroyden"])},
    "Pipe": {"OutletPressure": _F("Pa"), "OutletTemperature": _F("K"),
             "Specification": _E(["Length", "OutletPressure", "OutletTemperature"])},
}

_COLUMN_SPEC_TYPES = (
    "Reflux Ratio", "Boilup Ratio", "Heat Duty", "Product Molar Flow Rate", "Component Molar Flow Rate",
    "Product Mass Flow Rate", "Component Mass Flow Rate", "Component Fraction", "Component Recovery",
    "Stream Ratio", "Temperature", "Feed Recovery",
)
_REACTOR_MODE = {"isothermal": "Isothermic", "adiabatic": "Adiabatic", "outlet_temperature": "OutletTemperature"}
_REACTOR_CLASS = {"conversion": "RCT_Conversion", "equilibrium": "RCT_Equilibrium", "cstr": "RCT_CSTR", "pfr": "RCT_PFR"}
# Types that compare a DWSIM result with a stated limit. Anything else is reported, not treated as fine.
_CHECKED_TYPES = {"pump", "valve", "pipe", "hx", "heater", "cooler", "evaporator", "compressor", "column", "tank",
                  "reactor", "distillation"}


def _prop_list(props):
    return ", ".join(f"{name} ({meta['unit']})" + (f" one of {', '.join(meta['values'])}" if meta["kind"] == "enum" else "")
                     for name, meta in sorted(props.items()))


def validate_dwsim_unit(u):
    """Reject a generic unit whose class or property is outside the allowlist."""
    uid, cls = u.get("id", "?"), u.get("class")
    if cls not in DWSIM_ALLOW:
        raise ValueError(f"{uid}: DWSIM class {cls!r} is not allowlisted. Valid classes: {', '.join(sorted(DWSIM_ALLOW))}")
    props = DWSIM_ALLOW[cls]
    for name, value in (u.get("set") or {}).items():
        if name not in props:
            raise ValueError(f"{uid}: property {name!r} is not settable on {cls}. Valid properties: {_prop_list(props)}")
        meta = props[name]
        kind = meta["kind"]
        if kind == "enum":
            if not isinstance(value, str) or value not in meta["values"]:
                raise ValueError(f"{uid}: {name}={value!r} is not valid. Valid {name}: {', '.join(meta['values'])}")
        elif kind == "bool":
            if not isinstance(value, bool):
                raise ValueError(f"{uid}: {name} must be true or false, not {value!r}")
        elif kind == "int":
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{uid}: {name} must be a positive integer")
        elif kind == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise ValueError(f"{uid}: {name} must be a finite number")
            number = float(value)
            unit = meta["unit"]
            if unit == "fraction" and not 0 <= number <= 1:
                raise ValueError(f"{uid}: {name} must be between 0 and 1")
            if unit == "percent" and not 0 <= number <= 100:
                raise ValueError(f"{uid}: {name} must be between 0 and 100 percent")
            if unit == "K" and "TemperatureChange" not in name and number <= 0:
                raise ValueError(f"{uid}: {name} must be above 0 K")
            if unit in ("m", "m2", "m3") and number <= 0:
                raise ValueError(f"{uid}: {name} must be positive")
            if name in ("POut", "OutletPressure", "FlashPressure") and number <= 0:
                raise ValueError(f"{uid}: {name} must be positive")
        elif kind == "str" and not isinstance(value, str):
            raise ValueError(f"{uid}: {name} must be text")
    for name in u.get("report") or []:
        if name not in props:
            raise ValueError(f"{uid}: property {name!r} cannot be reported on {cls}. Valid properties: {_prop_list(props)}")
    if not u.get("in") or not u.get("out"):
        raise ValueError(f"{uid}: a dwsim unit needs in and out stream lists")
    return props


def _fair_csb(tray_spacing_m, flow_parameter):
    """Souders-Brown C_sb at entrainment flood, m/s, at 0.020 N/m surface tension.

    Lygeros, A. I.; Magoulas, K. G. Hydrocarbon Process. 1986, 65, 43-44, fit of
    Fair, J. R. Petro/Chem. Eng. 1961, 33(10), 45-52. Parameters as compiled by
    Souza, Bagajewicz and Costa, Ind. Eng. Chem. Res. 2025, 64 (doi 10.1021/acs.iecr.4c03115):
    C_sb = 0.0105 + 0.1496 * lt^0.755 * exp(-1.463 * F_LV^0.842), lt in m.
    Clamped to the chart's practical range (about 0.15-1 m spacing and F_LV 0.001-1).
    """
    lt = min(max(float(tray_spacing_m), 0.15), 1.0)
    flv = min(max(float(flow_parameter), 1e-3), 1.0)
    return 0.0105 + 0.1496 * lt ** 0.755 * math.exp(-1.463 * flv ** 0.842)


def fair_flood_fraction(vapour_kg_s, liquid_kg_s, rho_v, rho_l, sigma_N_m, diameter_m, tray_spacing_m):
    """Vapour velocity on the net area divided by Fair's flooding velocity.

    Net area is 90% of the shell (one downcomer taken as 10% of the cross-section), the usual
    screening allowance in Fair's chart. Not a tray rating: no weir, hole area or downcomer backup.
    """
    if diameter_m <= 0 or rho_v <= 0 or rho_l <= rho_v or vapour_kg_s <= 0:
        raise ValueError("flooding screen needs a positive diameter, vapour flow and liquid density above the vapour")
    area_net = 0.9 * math.pi * diameter_m ** 2 / 4
    velocity = (vapour_kg_s / rho_v) / area_net
    flv = (liquid_kg_s / vapour_kg_s) * math.sqrt(rho_v / rho_l) if liquid_kg_s > 0 else 1e-3
    csb = _fair_csb(tray_spacing_m, flv) * (max(sigma_N_m, 1e-4) / 0.020) ** 0.2
    u_flood = csb * math.sqrt((rho_l - rho_v) / rho_v)
    return velocity / u_flood if u_flood else None


def _column_profile(text):
    """Parse DWSIM's ColumnPropertiesProfile (Pa, K, mol/s, kg/s, kg/m3, Pa.s, W/m.K, N/m)."""
    rows = []
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        try:
            stage = int(parts[0])
            nums = [float(x) for x in parts[1:14]]
        except ValueError:
            continue
        keys = ("P_Pa", "T_K", "vapour_mol_s", "vapour_kg_s", "rho_v", "mu_v", "k_v",
                "liquid_mol_s", "liquid_kg_s", "rho_l", "mu_l", "k_l", "sigma_N_m")
        rows.append({"stage": stage, **dict(zip(keys, nums))})
    return rows


def _set_dwsim_prop(obj, name, value, meta):
    if meta["kind"] == "enum":
        current = getattr(obj, name)
        setattr(obj, name, getattr(type(current), str(value)))
    elif meta["kind"] == "bool":
        setattr(obj, name, bool(value))
    elif meta["kind"] == "int":
        setattr(obj, name, int(value))
    elif meta["kind"] == "str":
        setattr(obj, name, str(value))
    else:
        setattr(obj, name, float(value))


def _read_dwsim_prop(obj, name):
    value = getattr(obj, name)
    if value is None:
        return None
    getter = getattr(value, "GetType", None)
    if getter is not None and getter().IsEnum:
        return str(value).split(".")[-1]
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    try:
        return _r(value, 6)
    except (TypeError, ValueError):
        return None


def _duty_fields(obj):
    out = {}
    for attr, key in (("DeltaQ", "duty_kW"), ("HeatDuty", "heat_duty_kW")):
        value = getattr(obj, attr, None)
        if isinstance(value, (int, float)) and value == value:
            out[key] = _r(value, 3)
    if "duty_kW" not in out and "heat_duty_kW" in out:
        out["duty_kW"] = out["heat_duty_kW"]
    return out


def _dwsim_ports(obj):
    """Material inlets, material outlets, and energy ports in DWSIM's listed order."""
    ins, outs, energies = [], [], []
    for raw in obj.GetConnectionPortsList():
        line = str(raw).split(", Connected")[0]
        if "Type:" not in line:
            continue
        typ = line.split("Type:")[1].strip()
        name = line.split("Name:")[1].split(",")[0].strip() if "Name:" in line else ""
        index = None
        if "#" in line:
            try:
                index = int(line.split("#")[1].split(",")[0])
            except ValueError:
                index = None
        if line.startswith("Inlet Port"):
            side = "in"
        elif line.startswith("Outlet Port"):
            side = "out"
        else:
            side = "energy"
        port = {"index": index, "name": name, "side": side}
        if typ == "ConEn":
            energies.append(port)
        elif typ == "ConIn":
            ins.append(port)
        elif typ == "ConOut":
            outs.append(port)
    return ins, outs, energies


class _Sheet:
    def __init__(self, mgr, spec, scale=1.0):
        import System
        from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
        from DWSIM.UnitOperations.UnitOperations import Pump, HeatExchangerCalcMode, Valve, Heater, Cooler, Compressor
        self.mgr, self.spec, self.S, self.Double = mgr, spec, System, System.Double
        self.OT, self.Pump, self.HXM, self.Valve, self.Heater, self.Cooler, self.Comp = \
            ObjectType, Pump, HeatExchangerCalcMode, Valve, Heater, Cooler, Compressor
        self.sim = mgr.CreateFlowsheet()
        self.comps = spec["compounds"]
        for c in self.comps:
            self.sim.AddCompound(c)
        self.sim.CreateAndAddPropertyPackage(spec.get("package") or "NRTL")
        pp = list(self.sim.PropertyPackages.Values)[0].__implementation__
        mode = getattr(pp, "EnthalpyEntropyCpCvCalculationMode", None)
        if mode is not None and "NRTL" in (spec.get("package") or "NRTL"):
            # default Lee-Kesler liquid enthalpy gives cp(water) ~5.3 kJ/kgK; use liquid Cp data instead
            pp.EnthalpyEntropyCpCvCalculationMode = type(mode).LiqCp_Excess
        self.streams, self.units, self.scale = {}, {}, scale
        for name, f in spec.get("feeds", {}).items():
            self._feed(self.stream(name), f, 1.0 if f.get("utility") else scale)
        for u in spec["units"]:
            self.units[u["id"]] = (u, self._unit(u))

    def stream(self, name):
        if name not in self.streams:
            self.streams[name] = self.sim.AddObject(self.OT.MaterialStream, 0, 0, name).GetAsObject()
        return self.streams[name]

    def _add(self, kind, name):
        return self.sim.AddObject(getattr(self.OT, kind), 0, 0, name).GetAsObject()

    def _link(self, a, b, ia=-1, ib=-1):
        self.sim.ConnectObjects(a.GraphicObject, b.GraphicObject, ia, ib)

    def _feed(self, s, f, scale):
        x = [float((f.get("x") or {}).get(c, 0.0)) for c in self.comps]
        tot = sum(x) or 1.0
        s.SetTemperature(273.15 + float(f["T_C"]))
        s.SetPressure(float(f["P_bar"]) * 1e5)
        s.SetOverallComposition(self.S.Array[self.Double]([v / tot for v in x]))
        if f.get("kg_h") is not None:
            s.SetMassFlow(float(f["kg_h"]) * scale / 3600)
        else:
            s.SetVolumetricFlow(float(f["m3_h"]) * scale / 3600)

    def _energy(self, name):
        # not a material stream: results() only walks self.streams
        return self._add("EnergyStream", name)

    def _connect_listed(self, obj, streams, ports, into_unit):
        if len(streams) > len(ports):
            names = ", ".join(p["name"] for p in ports) or "none"
            raise ValueError(f"{obj.GraphicObject.Tag}: {len(ports)} material port(s) ({names}); got {len(streams)} stream(s)")
        for stream_name, port in zip(streams, ports):
            idx = -1 if port["index"] is None else port["index"]
            if into_unit:
                self._link(self.stream(stream_name), obj, -1, idx)
            else:
                self._link(obj, self.stream(stream_name), idx, -1)

    def _connect_energy(self, obj, names, ports):
        names = names if isinstance(names, list) else [names]
        if len(names) > len(ports):
            raise ValueError(f"{obj.GraphicObject.Tag}: {len(ports)} energy port(s); got {len(names)} energy stream(s)")
        for name, port in zip(names, ports):
            energy = self._energy(name)
            idx = -1 if port["index"] is None else port["index"]
            if port["side"] == "in":
                self._link(energy, obj, -1, idx)
            else:
                self._link(obj, energy, idx, -1)

    def _add_reactions(self, uid, kind, reactions, phase):
        from System.Collections.Generic import Dictionary
        rs = self.sim.CreateReactionSet(uid, uid)
        self.sim.AddReactionSet(rs)
        for i, rxn in enumerate(reactions or []):
            sto = Dictionary[str, float]()
            for compound, coeff in rxn["stoich"].items():
                sto[compound] = float(coeff)
            name, base = rxn.get("name") or f"{uid}-{i+1}", rxn["base"]
            phase_i = rxn.get("phase") or phase
            if kind == "conversion":
                obj = self.sim.CreateConversionReaction(name, name, sto, base, phase_i, str(rxn["conversion_pct"]))
            elif kind == "equilibrium":
                obj = self.sim.CreateEquilibriumReaction(
                    name, name, sto, base, phase_i, rxn.get("basis") or "Fugacity", rxn.get("basis_units") or "Pa",
                    float(rxn.get("approach_K") or 0), rxn.get("lnKeq") or "")
            else:
                orders, reverse = Dictionary[str, float](), Dictionary[str, float]()
                for compound, coeff in rxn["stoich"].items():
                    default = 1.0 if float(coeff) < 0 else 0.0
                    orders[compound] = float((rxn.get("orders") or {}).get(compound, default))
                    reverse[compound] = float((rxn.get("reverse_orders") or {}).get(compound, 0.0))
                obj = self.sim.CreateKineticReaction(
                    name, name, sto, orders, reverse, base, phase_i, rxn.get("basis") or "Molar Concentration",
                    rxn.get("amount_units") or "mol/m3", rxn.get("rate_units") or "mol/[m3.s]",
                    float(rxn.get("A") or 0), float(rxn.get("E_J_mol") or 0), float(rxn.get("A_reverse") or 0),
                    float(rxn.get("E_reverse_J_mol") or 0), rxn.get("rate_expression") or "", rxn.get("reverse_rate_expression") or "")
            obj.Tmin = float(rxn.get("Tmin_K", 200))
            obj.Tmax = float(rxn.get("Tmax_K", 5000))
            self.sim.AddReaction(obj)
            self.sim.AddReactionToSet(obj.ID, rs.ID, True, i)
        return rs.ID

    def _column_spec(self, u, which):
        """Resolve a condenser or reboiler specification. Shorthand fields win over the spec object."""
        if which == "condenser":
            if u.get("reflux_ratio") is not None:
                spec = {"type": "Reflux Ratio", "value": u["reflux_ratio"], "units": ""}
            elif u.get("distillate_mol_s") is not None:
                spec = {"type": "Product Molar Flow Rate", "value": u["distillate_mol_s"], "units": "mol/s"}
            else:
                spec = u.get("condenser_spec")
        else:
            if u.get("boilup_ratio") is not None:
                spec = {"type": "Boilup Ratio", "value": u["boilup_ratio"], "units": ""}
            elif u.get("bottoms_mol_s") is not None:
                spec = {"type": "Product Molar Flow Rate", "value": u["bottoms_mol_s"], "units": "mol/s"}
            else:
                spec = u.get("reboiler_spec")
        if not spec:
            raise ValueError(f"{u['id']}: distillation needs a {which} spec (reflux_ratio, boilup_ratio, "
                             "distillate_mol_s, bottoms_mol_s, or condenser_spec/reboiler_spec)")
        if spec["type"] not in _COLUMN_SPEC_TYPES:
            raise ValueError(f"{u['id']}: {which} spec {spec['type']!r} is not valid. Valid: {', '.join(_COLUMN_SPEC_TYPES)}")
        if "Component" in spec["type"] and not spec.get("compound"):
            raise ValueError(f"{u['id']}: {spec['type']} needs compound")
        return spec

    def _unit(self, u):
        t, uid = u["type"], u["id"]
        if t == "pump":
            p = self._add("Pump", uid)
            self._link(self.stream(u["in"]), p); self._link(p, self.stream(u["out"]))
            self._link(self._add("EnergyStream", f"E-{uid}"), p)
            p.Eficiencia = float(u.get("eff_pct", 70))
            if u.get("curve"):
                from System.Collections.Generic import List
                cs = p.PumpCurveSet
                xs, ys = List[self.Double](), List[self.Double]()
                for q, h in u["curve"]:
                    xs.Add(float(q)); ys.Add(float(h))
                cs.CurveHead.X, cs.CurveHead.Y = xs, ys
                cs.CurveHead.xunit, cs.CurveHead.yunit, cs.CurveHead.Enabled = "m3/h", "m", True
                p.CurveHead = True
                p.CalcMode = self.Pump.CalculationMode.Curves
            else:
                p.CalcMode = self.Pump.CalculationMode.Delta_P
                p.DeltaP = float(u.get("dP_bar", 1.0)) * 1e5
            return p
        if t == "hx":
            h = self._add("HeatExchanger", uid)
            (ci, co), (hi, ho) = u["cold"], u["hot"]
            self._link(self.stream(ci), h, 0, 0); self._link(self.stream(hi), h, 0, 1)
            self._link(h, self.stream(co), 0, 0); self._link(h, self.stream(ho), 1, 0)
            h.OverallCoefficient, h.Area = float(u.get("U_W_m2K", 1000)), float(u.get("area_m2", 10))
            self._hx_mode(u, h)
            return h
        if t in ("heater", "cooler"):
            cls = self.Heater if t == "heater" else self.Cooler
            h = self._add("Heater" if t == "heater" else "Cooler", uid)
            e = self._add("EnergyStream", f"E-{uid}")
            self._link(self.stream(u["in"]), h); self._link(h, self.stream(u["out"]))
            self._link(e, h) if t == "heater" else self._link(h, e)
            if u.get("T_out_C") is not None:
                h.CalcMode = cls.CalculationMode.OutletTemperature
                h.OutletTemperature = 273.15 + float(u["T_out_C"])
            else:
                h.CalcMode = cls.CalculationMode.HeatAdded if t == "heater" else cls.CalculationMode.HeatRemoved
                h.DeltaQ = float(u["duty_kW"]) * (self.scale if u.get("scales") else 1.0)
            return h
        if t == "valve":
            if u.get("cv_rated") is not None and u.get("kv_rated") is not None:
                raise ValueError(f"{uid}: specify cv_rated or kv_rated, not both")
            if u.get("cv_rated") is not None or u.get("kv_rated") is not None:
                rated = float(u.get("cv_rated", 0) or 0) or float(u.get("kv_rated", 0) or 0) * 1.156
                lo, hi = float(u.get("min_travel_pct", 10)), float(u.get("max_travel_pct", 90))
                if rated <= 0 or not 0 <= lo < hi <= 100:
                    raise ValueError(f"{uid}: positive rating and 0 <= min_travel_pct < max_travel_pct <= 100 required")
                _valve_sizing(0, 1000, 1, rated, u.get("characteristic", "equal_percentage"), float(u.get("rangeability", 50)))
            v = self._add("Valve", uid)
            self._link(self.stream(u["in"]), v); self._link(v, self.stream(u["out"]))
            if u.get("kv") is not None:
                v.CalcMode, v.Kv = self.Valve.CalculationMode.Kv_Liquid, float(u["kv"])
            elif u.get("P_out_bar") is not None:
                v.CalcMode, v.OutletPressure = self.Valve.CalculationMode.OutletPressure, float(u["P_out_bar"]) * 1e5
            else:
                v.CalcMode, v.DeltaP = self.Valve.CalculationMode.DeltaP, float(u.get("dP_bar", 0.5)) * 1e5
            return v
        if t == "pipe":
            if u.get("id_mm") is not None and u.get("dn_mm") is not None:
                raise ValueError(f"{uid}: specify id_mm or dn_mm, not both")
            diameter = u["id_mm"] if u.get("id_mm") is not None else u.get("dn_mm")
            if diameter is None:
                raise ValueError(f"{uid}: id_mm or dn_mm required")
            _pipe_hydraulics(0, 1000, 0.001, float(u["length_m"]), float(diameter) / 1000,
                             float(u.get("roughness_mm", 0.045)) / 1000, float(u.get("elevation_m", 0)),
                             float(u.get("fittings_K", 0)))
            p = self._add("Valve", uid)
            self._link(self.stream(u["in"]), p); self._link(p, self.stream(u["out"]))
            p.CalcMode, p.DeltaP = self.Valve.CalculationMode.DeltaP, 0.0
            return p
        if t == "tank":
            k = self._add("Tank", uid)
            if isinstance(u["in"], list):  # several inlets: mix them first
                m = self._add("Mixer", f"{uid}-mix")
                for i, s_ in enumerate(u["in"]):
                    self._link(self.stream(s_), m, -1, i)
                src = self.stream(f"{uid}-mixed")
                self._link(m, src)
            else:
                src = self.stream(u["in"])
            if u.get("P_bar") is not None:  # the liquid settles at vessel pressure: an inlet valve drops it there
                v = self._add("Valve", f"{uid}-inlet")
                mid = self.stream(f"{uid}-in")
                self._link(src, v); self._link(v, mid)
                v.CalcMode, v.OutletPressure = self.Valve.CalculationMode.OutletPressure, float(u["P_bar"]) * 1e5
                src = mid
            self._link(src, k); self._link(k, self.stream(u["out"]))
            k.Volume = float(u.get("volume_m3", 10))
            return k
        if t == "recycle":
            r = self._add("OT_Recycle", uid)
            tear = self.stream(u["out"])
            g = u.get("guess") or {}
            ref = next((f for f in self.spec.get("feeds", {}).values() if not f.get("utility")), {})
            self._feed(tear, {"T_C": g.get("T_C", ref.get("T_C", 25)), "P_bar": g.get("P_bar", ref.get("P_bar", 1.5)),
                              "kg_h": g.get("kg_h", ref.get("kg_h") or float(ref.get("m3_h", 1)) * 1000), "x": g.get("x", ref.get("x", {}))},
                       self.scale if u.get("guess_scales") else 1.0)
            self._link(self.stream(u["in"]), r); self._link(r, tear)
            r.MaximumIterations = 300
            return r
        if t == "mixer":
            m = self._add("Mixer", uid)
            for i, s in enumerate(u["in"]):
                self._link(self.stream(s), m, -1, i)
            self._link(m, self.stream(u["out"]))
            return m
        if t == "splitter":
            sp = self._add("Splitter", uid)
            self._link(self.stream(u["in"]), sp)
            for i, s in enumerate(u["out"]):
                self._link(sp, self.stream(s), i, -1)
            if u.get("fixed_kg_h"):
                # ponytail: DWSIM fixes the flow of the FIRST outlet in this mode, so the fixed branch must be listed first
                (name, kg_h), = u["fixed_kg_h"].items()
                if u["out"][0] != name:
                    raise ValueError(f"splitter {uid}: list the fixed stream {name} first in out")
                sp.OperationMode = type(sp.OperationMode).StreamMassFlowSpec
                sp.StreamFlowSpec = float(kg_h) * (self.scale if u.get("fixed_scales") else 1.0) / 3600
            else:
                for i, f in enumerate(u["fractions"]):
                    sp.Ratios[i] = float(f)
            return sp
        if t == "compressor":
            c = self._add("Compressor", uid)
            self._link(self.stream(u["in"]), c); self._link(c, self.stream(u["out"]))
            self._link(self._add("EnergyStream", f"E-{uid}"), c)
            c.CalcMode, c.POut = self.Comp.CalculationMode.OutletPressure, float(u["P_out_bar"]) * 1e5
            c.AdiabaticEfficiency = float(u.get("eff_pct", 75))  # DWSIM takes percent, like the pump
            return c
        if t == "evaporator":
            # brine boils at P_bar: inlet valve -> heater to the evaporated fraction -> vapour/liquid split; the heating
            # steam condenses fully on the other side. Water stands in for the brine; the salt's boiling point elevation is
            # applied to the temperature driving force from brine.py (Sparrow 2003), and the salt follows from the water boiled.
            # ponytail: a DWSIM Vessel cannot split single-compound steam-table water, so the inlet is split by the boiled
            # fraction and each part is brought to saturated vapour / saturated liquid at body pressure
            v = self._add("Valve", f"{uid}-inlet"); mid = self.stream(f"{uid}-in")
            self._link(self.stream(u["in"]), v); self._link(v, mid)
            v.CalcMode, v.OutletPressure = self.Valve.CalculationMode.OutletPressure, float(u["P_bar"]) * 1e5
            sp = self._add("Splitter", f"{uid}-split")
            self._link(mid, sp)
            hs = []
            for k, (out, vf) in enumerate(((u["vapor"], 1.0), (u["liquid"], 0.0))):
                part = self.stream(f"{uid}-part{k}")
                self._link(sp, part, k, -1)
                h = self._add("Heater", uid if k == 0 else f"{uid}-liq")
                self._link(part, h); self._link(h, self.stream(out)); self._link(self._add("EnergyStream", f"E-{uid}-{k}"), h)
                h.CalcMode, h.OutletVaporFraction = self.Heater.CalculationMode.OutletVaporFraction, vf
                hs.append(h)
            f = float(u["evap_frac"])
            if not 0 < f < 1:
                raise ValueError(f"{uid}: evap_frac must be between 0 and 1")
            if u.get("feed_x_NaCl") is not None and not 0 <= float(u["feed_x_NaCl"]) <= 0.32:
                raise ValueError(f"{uid}: feed_x_NaCl must be between 0 and 0.32")
            if u.get("x_NaCl") is not None and not 0 <= float(u["x_NaCl"]) <= 0.32:
                raise ValueError(f"{uid}: x_NaCl must be between 0 and 0.32")
            sp.Ratios[0], sp.Ratios[1] = f, 1 - f
            b = hs[0]
            self.__dict__.setdefault("aux_liq", {})[uid] = hs[1]
            self.__dict__.setdefault("aux_split", {})[uid] = sp
            if u.get("heating"):
                c = self._add("Cooler", f"{uid}-heating")
                self._link(self.stream(u["heating"][0]), c); self._link(c, self.stream(u["heating"][1]))
                self._link(c, self._add("EnergyStream", f"E-{uid}-heating"))
                c.CalcMode, c.OutletVaporFraction = self.Cooler.CalculationMode.OutletVaporFraction, 0.0
                self.__dict__.setdefault("aux", {})[uid] = c
            return b
        if t == "flash":
            v = self._add("Vessel", uid)
            self._link(self.stream(u["in"]), v)
            self._link(v, self.stream(u["vapor"]), 0, -1)
            self._link(v, self.stream(u["liquid"]), 1, -1)
            return v
        if t == "component_separator":
            from DWSIM.UnitOperations.UnitOperations.Auxiliary import ComponentSeparationSpec, SeparationSpec
            s = self._add("ComponentSeparator", uid)
            self._link(self.stream(u["in"]), s)
            self._link(s, self.stream(u["product"]), 0, -1)
            self._link(s, self.stream(u["reject"]), 1, -1)
            for c in self.comps:
                pct = float(u.get("recover_pct", {}).get(c, 100))
                if not 0 <= pct <= 100:
                    raise ValueError(f"{uid}: recovery for {c} must be 0-100 percent")
                s.ComponentSepSpecs.Add(c, ComponentSeparationSpec(c, SeparationSpec.PercentInletMolarFlow, pct, "%"))
            s.SpecifiedStreamIndex = 0
            return s
        if t == "column":
            # shortcut distillation (Fenske-Underwood-Gilliland): stages and duties for given key-component splits
            c = self._add("ShortcutColumn", uid)
            self._link(self.stream(u["in"]), c)
            self._link(c, self.stream(u["distillate"]), 0, -1); self._link(c, self.stream(u["bottoms"]), 1, -1)
            self._link(c, self._add("EnergyStream", f"QC-{uid}")); self._link(self._add("EnergyStream", f"QR-{uid}"), c)
            c.m_lightkey, c.m_heavykey = u["light_key"], u["heavy_key"]
            c.m_lightkeymolarfrac = float(u["light_key_in_bottoms"])
            c.m_heavykeymolarfrac = float(u["heavy_key_in_distillate"])
            c.m_refluxratio = float(u.get("reflux_ratio", 1.5))
            c.m_condenserpressure = float(u.get("P_bar", 1.013)) * 1e5
            c.m_boilerpressure = float(u.get("P_bottom_bar", u.get("P_bar", 1.013))) * 1e5
            return c
        if t == "dwsim":
            props = validate_dwsim_unit(u)
            obj = self._add(u["class"], uid)
            ins, outs, energies = _dwsim_ports(obj)
            self._connect_listed(obj, u["in"], ins, True)
            self._connect_listed(obj, u["out"], outs, False)
            if u.get("energy") is not None:
                if not energies:
                    raise ValueError(f"{uid}: {u['class']} has no energy port")
                self._connect_energy(obj, u["energy"], energies)
            for name, value in (u.get("set") or {}).items():
                _set_dwsim_prop(obj, name, value, props[name])
            return obj
        if t == "reactor":
            kind = u.get("kind")
            if kind not in _REACTOR_CLASS:
                raise ValueError(f"{uid}: reactor kind must be one of {', '.join(_REACTOR_CLASS)}")
            mode = u.get("mode", "isothermal")
            if mode not in _REACTOR_MODE:
                raise ValueError(f"{uid}: reactor mode must be isothermal, adiabatic or outlet_temperature")
            phase = u.get("phase") or ("Liquid" if kind == "cstr" else "Vapor")
            if phase not in ("Vapor", "Liquid", "Mixture", "Solid"):
                raise ValueError(f"{uid}: phase must be Vapor, Liquid, Mixture or Solid")
            obj = self._add(_REACTOR_CLASS[kind], uid)
            self._link(self.stream(u["in"]), obj, -1, 0)
            self._link(self._energy(f"E-{uid}"), obj, -1, 1)
            if kind == "pfr":
                if not u.get("out"):
                    raise ValueError(f"{uid}: pfr needs out")
                self._link(obj, self.stream(u["out"]), 0, -1)
            elif kind == "cstr":
                if not u.get("liquid"):
                    raise ValueError(f"{uid}: cstr needs liquid (the reacting holdup) and an optional vapor")
                self._link(obj, self.stream(u["liquid"]), 0, -1)
                self._link(obj, self.stream(u.get("vapor") or f"{uid}-vapor"), 1, -1)
            else:
                if not u.get("vapor") or not u.get("liquid"):
                    raise ValueError(f"{uid}: {kind} reactor needs vapor and liquid outlets")
                self._link(obj, self.stream(u["vapor"]), 0, -1)
                self._link(obj, self.stream(u["liquid"]), 1, -1)
            if kind == "cstr":
                if u.get("volume_m3") is None:
                    raise ValueError(f"{uid}: cstr needs volume_m3")
                obj.Volume = float(u["volume_m3"])
                obj.Headspace = float(u.get("headspace", 0.1))
                if obj.Headspace <= 0:
                    raise ValueError(f"{uid}: headspace must be > 0 (DWSIM rejects a CSTR with no vapor space)")
            if kind == "pfr":
                if u.get("volume_m3") is not None:
                    obj.Volume = float(u["volume_m3"])
                elif u.get("length_m") is not None and u.get("diameter_m") is not None:
                    obj.Volume = math.pi * (float(u["diameter_m"]) / 2) ** 2 * float(u["length_m"])
                else:
                    raise ValueError(f"{uid}: pfr needs volume_m3, or length_m and diameter_m")
                if u.get("length_m") is not None:
                    obj.Length = float(u["length_m"])
                if u.get("diameter_m") is not None:
                    obj.Diameter = float(u["diameter_m"])
                if u.get("dP_bar") is not None:
                    obj.UseUserDefinedPressureDrop = True
                    obj.UserDefinedPressureDrop = float(u["dP_bar"]) * 1e5
            obj.ReactionSetID = self._add_reactions(uid, kind, u.get("reactions"), phase)
            obj.ReactorOperationMode = getattr(type(obj.ReactorOperationMode), _REACTOR_MODE[mode])
            if mode == "outlet_temperature":
                if u.get("T_out_C") is None:
                    raise ValueError(f"{uid}: outlet_temperature mode needs T_out_C")
                obj.OutletTemperature = 273.15 + float(u["T_out_C"])
            return obj
        if t == "distillation":
            stages, feed_stage = int(u["stages"]), int(u["feed_stage"])
            if not 1 <= feed_stage <= stages:
                raise ValueError(f"{uid}: feed_stage must be from 1 (condenser) to {stages}")
            condenser = {"total": "Total_Condenser", "partial": "Partial_Condenser", "full_reflux": "Full_Reflux"}
            if u.get("condenser", "total") not in condenser:
                raise ValueError(f"{uid}: condenser must be total, partial or full_reflux")
            cspec, rspec = self._column_spec(u, "condenser"), self._column_spec(u, "reboiler")
            col = self._add("DistillationColumn", uid)
            col.SetNumberOfStages(stages)
            col.ConnectFeed(self.stream(u["in"]), feed_stage - 1)
            col.ConnectDistillate(self.stream(u["distillate"]))
            col.ConnectBottoms(self.stream(u["bottoms"]))
            if u.get("vapor"):
                col.ConnectVaporProduct(self.stream(u["vapor"]))
            col.ConnectCondenserDuty(self._energy(f"QC-{uid}"))
            col.ConnectReboilerDuty(self._energy(f"QR-{uid}"))
            col.SetCondenserSpec(cspec["type"], float(cspec["value"]), cspec.get("units") or "", cspec.get("compound") or "")
            col.SetReboilerSpec(rspec["type"], float(rspec["value"]), rspec.get("units") or "", rspec.get("compound") or "")
            col.SetTopPressure(float(u.get("P_bar", 1.01325)) * 1e5)
            col.ColumnPressureDrop = float(u.get("dP_bar", 0)) * 1e5
            col.CondenserType = getattr(type(col.CondenserType), condenser[u.get("condenser", "total")])
            if u.get("subcool_K") is not None:
                col.TotalCondenserSubcoolingDeltaT = float(u["subcool_K"])
            return col
        raise ValueError(f"unknown unit type {t}")

    def solve(self):
        errs = self.mgr.CalculateFlowsheet4(self.sim)
        errs = [str(e.Message)[:200] for e in errs] if errs is not None else []
        if not errs:
            for uid, (u, o) in self.units.items():
                if u["type"] != "evaporator" or u.get("feed_x_NaCl") is None or not u.get("heating"):
                    continue
                sp = self.aux_split[uid]
                for _ in range(4):
                    r = self.results()["units"][uid]
                    if r.get("error") or not r.get("heating_kW"):
                        break
                    f = float(sp.Ratios[0])
                    qprime = (o.DeltaQ or 0) / f - (self.aux_liq[uid].DeltaQ or 0) / (1 - f)
                    if qprime <= 0:
                        break
                    next_f = min(float(u["evap_frac"]), max(0.001, f + (r["heating_kW"] - r["boil_kW"]) / qprime))
                    if abs(next_f - f) < 0.00001:
                        break
                    sp.Ratios[0], sp.Ratios[1] = next_f, 1 - next_f
                    e2 = self.mgr.CalculateFlowsheet4(self.sim)
                    errs = [str(e.Message)[:200] for e in e2] if e2 is not None else []
                    if errs:
                        break
        flowdep = [(u, o) for u, o in self.units.values() if u["type"] == "hx" and (u.get("U_ref_flows_m3_h") or u.get("dP_ref_bar"))]
        pipes = [(u, o) for u, o in self.units.values() if u["type"] == "pipe"]
        self._pipe_values = {}
        for _ in range(2 if (flowdep or pipes) and not errs else 0):  # flow-dependent U, dP and pipe pressure follow solved flows
            for u, o in flowdep:
                qh = self.streams[u["hot"][0]].GetVolumetricFlow() * 3600
                qc = self.streams[u["cold"][0]].GetVolumetricFlow() * 3600
                if u.get("U_ref_flows_m3_h"):
                    rh, rc = u["U_ref_flows_m3_h"]
                    # equal film resistances at the reference flows; each film coefficient ~ Q^0.8 (fouling folded in)
                    U0 = float(u.get("U_W_m2K", 1000))
                    o.OverallCoefficient = 1 / (0.5 / U0 * (rh / qh) ** 0.8 + 0.5 / U0 * (rc / qc) ** 0.8)
                if u.get("dP_ref_bar"):
                    (dh, dc), (rh, rc) = u["dP_ref_bar"], u.get("U_ref_flows_m3_h") or u["dP_ref_flows_m3_h"]
                    o.HotSidePressureDrop, o.ColdSidePressureDrop = dh * 1e5 * (qh / rh) ** 1.8, dc * 1e5 * (qc / rc) ** 1.8
            for u, o in pipes:
                uid = u["id"]
                s = self.streams[u["in"]]
                if float(s.Phases[2].Properties.molarfraction or 0) > 0.001:
                    errs.append(f"{uid}: liquid-only pipe hydraulics; gas/two-phase flow is unsupported")
                    continue
                try:
                    q, rho = float(s.GetVolumetricFlow()), float(s.Phases[0].Properties.density)
                    mu = float(s.Phases[1].Properties.viscosity or 0)
                    diameter = u["id_mm"] if u.get("id_mm") is not None else u["dn_mm"]
                    data = _pipe_hydraulics(q, rho, mu, float(u["length_m"]), float(diameter) / 1000,
                                            float(u.get("roughness_mm", 0.045)) / 1000, float(u.get("elevation_m", 0)),
                                            float(u.get("fittings_K", 0)))
                except (TypeError, ValueError) as ex:
                    errs.append(f"{uid}: pipe liquid properties unavailable: {ex}")
                    continue
                pout = s.GetPressure() - data["dP_bar"] * 1e5
                if pout <= 0:
                    errs.append(f"{uid}: calculated outlet pressure is nonpositive")
                    continue
                self._pipe_values[uid] = data
                o.CalcMode, o.OutletPressure = self.Valve.CalculationMode.OutletPressure, pout
            if errs:
                break
            e2 = self.mgr.CalculateFlowsheet4(self.sim)
            errs = [str(e.Message)[:200] for e in e2] if e2 is not None else []
        return errs

    def results(self):
        st = {}
        for n, s in self.streams.items():
            try:
                st[n] = {"T_C": _r(s.GetTemperature() - 273.15, 2), "P_bar": _r(s.GetPressure() / 1e5, 3),
                         "kg_h": _r(s.GetMassFlow() * 3600, 1), "m3_h": _r(s.GetVolumetricFlow() * 3600, 2),
                         "vapour_frac": _r(float(s.Phases[2].Properties.molarfraction or 0.0), 4),
                         "components_kg_h": {c: _r(s.GetCompoundMassFlow(c) * 3600, 2) for c in self.comps}}
            except Exception as ex:  # noqa: BLE001 - an unsolved stream reports why
                st[n] = {"error": str(ex)[:120]}
        un = {}
        for uid, (u, o) in self.units.items():
            t, r = u["type"], {"type": u["type"]}
            try:
                if t == "pump":
                    q = (self.streams[u["in"]].GetVolumetricFlow() or 0) * 3600
                    # ponytail: DWSIM leaves DeltaQ at 0 in curve mode, so shaft power is Q*dP/eta
                    r.update(m3_h=_r(q, 2), head_m=_r(o.Head, 2), dP_bar=_r(o.DeltaP / 1e5, 3), eff_pct=_r(o.Eficiencia, 1),
                             kW=_r(q / 3600 * (o.DeltaP or 0) / ((o.Eficiencia or 100) / 100) / 1000, 2), npsha_m=_r(o.NPSH, 2),
                             discharge_barg=_r(self.streams[u["out"]].GetPressure() / 1e5 - 1.013, 3),
                             kind=u.get("kind", "centrifugal"))
                elif t == "hx":
                    r.update(duty_kW=_r(o.Q, 1), lmtd_C=_r(o.LMTD, 2), U_W_m2K=_r(o.OverallCoefficient, 1), area_m2=_r(o.Area, 2),
                             dP_hot_bar=_r(o.HotSidePressureDrop / 1e5, 3), dP_cold_bar=_r(o.ColdSidePressureDrop / 1e5, 3))
                elif t in ("heater", "cooler"):
                    r.update(duty_kW=_r(o.DeltaQ, 2))
                elif t == "evaporator":
                    from . import brine
                    vap = self.streams[u["vapor"]].GetMassFlow() * 3600
                    feed_name = u.get("net_feed") or u["in"]
                    liquid_name = u.get("net_liquid") or u["liquid"]
                    if feed_name not in self.streams or liquid_name not in self.streams:
                        missing = feed_name if feed_name not in self.streams else liquid_name
                        r["error"] = f"balance stream {missing} does not exist"
                        continue
                    feed = self.streams[feed_name]
                    feed_kg_h = feed.GetMassFlow() * 3600
                    feed_t = feed.GetTemperature() - 273.15
                    feed_x = float(u["feed_x_NaCl"]) if u.get("feed_x_NaCl") is not None else brine.x_sat(feed_t)
                    salt_in = feed_kg_h * feed_x
                    liquid_kg_h = self.streams[liquid_name].GetMassFlow() * 3600
                    b = brine.bpe(float(u["P_bar"]), float(u["x_NaCl"]) if u.get("x_NaCl") is not None else None)
                    body_x = min(b["x_NaCl"], salt_in / liquid_kg_h) if liquid_kg_h else b["x_NaCl"]
                    if body_x < b["x_NaCl"]:
                        b = brine.bpe(float(u["P_bar"]), body_x)
                    if vap > feed_kg_h - salt_in + 0.1:
                        r["error"] = "boil-up exceeds water in the feed; reduce evap_frac or increase feed"
                        salt = liquid_brine = None
                    else:
                        salt = max(0.0, (salt_in - liquid_kg_h * body_x) / (1 - body_x))
                        liquid_brine = liquid_kg_h - salt
                    feed_cp_t = max(0, min(150, feed_t))
                    body_cp_t = max(0, min(150, b["t_brine_C"]))
                    water_cp_t = max(0, min(150, b["t_water_C"]))
                    if feed_cp_t != feed_t or body_cp_t != b["t_brine_C"] or water_cp_t != b["t_water_C"]:
                        r["error"] = "brine cp correlation valid only from 0 to 150 C"
                    cp_avg = (brine.cp(feed_cp_t, feed_x) + brine.cp(body_cp_t, body_x)) / 2
                    water_cp_avg = (brine.cp(feed_cp_t, 0) + brine.cp(water_cp_t, 0)) / 2
                    brine_sensible = feed_kg_h / 3600 * cp_avg * (b["t_brine_C"] - feed_t)
                    water_sensible = feed_kg_h / 3600 * water_cp_avg * (b["t_water_C"] - feed_t)
                    # DWSIM's water stand-in ends at water saturation. Real vapour leaves saturated brine superheated by BPE.
                    vapor_superheat = vap / 3600 * 2.08 * b["bpe_K"]
                    correction = brine_sensible - water_sensible + vapor_superheat
                    boil = (o.DeltaQ or 0) + (getattr(self, "aux_liq", {})[uid].DeltaQ or 0) + correction
                    if boil < 0 or (self.streams[u["in"]].GetPhase("Vapor").Properties.molarfraction or 0) > 0.99:
                        r["error"] = ("inlet is vapour in the water stand-in: brine above the water saturation temperature at its "
                                      "pressure only stays liquid through its BPE; give that feed at a pressure where water is liquid")
                    r.update(boil_kW=_r(boil, 1), sensible_correction_kW=_r(correction, 1),
                             brine_sensible_kW=_r(brine_sensible, 1), water_sensible_kW=_r(water_sensible, 1),
                             vapor_superheat_kW=_r(vapor_superheat, 1), vapour_kg_h=_r(vap, 0),
                             brine_T_C=b["t_brine_C"], bpe_K=b["bpe_K"], body_x_NaCl=b["x_NaCl"],
                             salt_in_kg_h=_r(salt_in, 0), salt_kg_h=_r(salt, 0) if salt is not None else None,
                             crystallising=salt is not None and salt > 0,
                             liquid_out_brine_kg_h=_r(liquid_brine, 0) if liquid_brine is not None else None,
                             water_evaporated_per_t_salt=_r(vap / salt, 2) if salt else None)
                    if u.get("heating"):
                        hc = getattr(self, "aux", {}).get(uid)
                        hs = self.streams[u["heating"][1]]
                        heat, t_cond = (hc.DeltaQ if hc else None), hs.GetTemperature() - 273.15
                        dt = t_cond - b["t_brine_C"]
                        r.update(heating_kW=_r(abs(heat), 1) if heat is not None else None, condensing_C=_r(t_cond, 2), driving_dT_K=_r(dt, 2),
                                 heat_balance_kW=_r(abs(heat) - boil, 1) if heat is not None else None,
                                 area_needed_m2=_r(boil * 1e3 / (float(u["U_W_m2K"]) * dt), 0) if u.get("U_W_m2K") and dt > 0 else
                                 (None if not u.get("U_W_m2K") else 9.99e9),
                                 area_m2=u.get("area_m2"), U_W_m2K=u.get("U_W_m2K"))
                elif t == "compressor":
                    r.update(duty_kW=_r(o.DeltaQ, 2), kW=_r(o.DeltaQ, 2),
                             discharge_C=_r(self.streams[u["out"]].GetTemperature() - 273.15, 1))
                elif t == "valve":
                    r.update(dP_bar=_r(o.DeltaP / 1e5, 3))
                    s = self.streams[u["in"]]
                    rated = (float(u["cv_rated"]) if u.get("cv_rated") is not None else float(u["kv_rated"]) * 1.156) if \
                        (u.get("cv_rated") is not None or u.get("kv_rated") is not None) else None
                    if float(s.Phases[2].Properties.molarfraction or 0) <= 0.001:
                        dp = (s.GetPressure() - self.streams[u["out"]].GetPressure()) / 1e5
                        try:
                            sizing = _valve_sizing(float(s.GetVolumetricFlow()), float(s.Phases[0].Properties.density), dp,
                                                   rated, u.get("characteristic", "equal_percentage"), float(u.get("rangeability", 50)))
                            r["cv_required"] = _r(sizing["cv_required"], 3)
                            if rated is not None:
                                r["opening_pct"] = _r(sizing["opening_pct"], 2)
                                if sizing.get("sizing_error"):
                                    r["sizing_error"] = sizing["sizing_error"]
                        except (TypeError, ValueError) as ex:
                            if rated is not None:
                                r["sizing_error"] = f"liquid properties unavailable: {ex}"
                    if rated is not None:
                        if float(s.Phases[2].Properties.molarfraction or 0) > 0.001:
                            r.update(cv_required=None, opening_pct=None, sizing_error="liquid-only Cv sizing; gas/two-phase unsupported")
                        r.update(cv_rated=_r(rated, 3), characteristic=u.get("characteristic", "equal_percentage"))
                elif t == "pipe":
                    data = getattr(self, "_pipe_values", {}).get(uid)
                    if data:
                        r.update(dP_bar=_r((self.streams[u["in"]].GetPressure() - self.streams[u["out"]].GetPressure()) / 1e5, 4),
                                 velocity_m_s=_r(data["velocity_m_s"], 3), Reynolds=_r(data["Reynolds"], 0),
                                 friction_factor=_r(data["friction_factor"], 5))
                elif t == "column":
                    r.update(min_stages=_r(o.m_Nmin, 1), stages=_r(o.m_N, 1), min_reflux=_r(o.m_Rmin, 3), reflux=_r(o.m_refluxratio, 3),
                             condenser_kW=_r(abs(o.m_Qc or 0), 1), reboiler_kW=_r(abs(o.m_Qb or 0), 1))
                elif t == "tank":
                    # hold time is volume over the NET throughput (the product leaving), not over a recirculation loop
                    basis = u.get("residence_basis")
                    q = self.streams[basis].GetVolumetricFlow() if basis in self.streams else None
                    r.update(residence_min=_r(o.Volume / q / 60 if q else o.ResidenceTime / 60, 2), volume_m3=o.Volume,
                             residence_basis=basis or "tank outlet")
                elif t == "dwsim":
                    r["class"] = u["class"]
                    r["properties"] = {name: _read_dwsim_prop(o, name) for name in (u.get("report") or [])}
                    r.update(_duty_fields(o))
                elif t == "reactor":
                    products = [s for s in (u.get("vapor"), u.get("liquid"), u.get("out"), f"{uid}-vapor") if s in self.streams]
                    inlet = self.streams[u["in"]]
                    conv = []
                    for rxn in u.get("reactions") or []:
                        base = rxn["base"]
                        nin = float(inlet.GetCompoundMolarFlow(base) or 0)
                        nout = sum(float(self.streams[s].GetCompoundMolarFlow(base) or 0) for s in products)
                        conv.append({"reaction": rxn.get("name"), "base": base,
                                     "conversion_pct": _r((nin - nout) / nin * 100, 2) if nin else None})
                    temps = [self.streams[s].GetTemperature() - 273.15 for s in products
                             if (self.streams[s].GetMassFlow() or 0) > 1e-8]
                    duty = o.DeltaQ
                    r.update(kind=u["kind"], conversion=conv, conversion_pct=conv[0]["conversion_pct"] if len(conv) == 1 else None,
                             duty_kW=_r(duty, 3), cooling_kW=_r(max(0.0, -(duty or 0)), 3),
                             T_out_C=_r(max(temps), 2) if temps else None)
                elif t == "distillation":
                    profile = _column_profile(o.ColumnPropertiesProfile)
                    lim = (self.spec.get("limits") or {}).get(uid) or {}
                    spacing = float(lim.get("tray_spacing_m") or o.TraySpacing or 0.5)
                    diameter = lim.get("diameter_m")
                    flood_error = None if diameter else "flooding screen needs limits.diameter_m (tray_spacing_m defaults to 0.5, flood_frac_max to 0.8)"
                    fracs = []
                    shown = []
                    for row in profile:
                        item = {"stage": row["stage"], "T_C": _r(row["T_K"] - 273.15, 2), "P_bar": _r(row["P_Pa"] / 1e5, 4),
                                "vapour_kg_h": _r(row["vapour_kg_s"] * 3600, 2), "liquid_kg_h": _r(row["liquid_kg_s"] * 3600, 2),
                                "vapour_mol_s": _r(row["vapour_mol_s"], 4), "liquid_mol_s": _r(row["liquid_mol_s"], 4),
                                "rho_v_kg_m3": _r(row["rho_v"], 2), "rho_l_kg_m3": _r(row["rho_l"], 1),
                                "sigma_N_m": _r(row["sigma_N_m"], 5)}
                        if diameter and row["vapour_kg_s"] > 1e-6 and row["rho_l"] > row["rho_v"] > 0:
                            frac = fair_flood_fraction(row["vapour_kg_s"], row["liquid_kg_s"], row["rho_v"], row["rho_l"],
                                                       row["sigma_N_m"], float(diameter), spacing)
                            item["flood_frac"] = _r(frac, 3)
                            if frac is not None:
                                fracs.append(frac)
                        shown.append(item)
                    if diameter and not fracs:
                        flood_error = "DWSIM reported no stage with vapour traffic to screen for flooding"
                    r.update(stages=o.NumberOfStages, feed_stage=u["feed_stage"], reflux=_r(o.RefluxRatio, 3),
                             condenser_kW=_r(abs(o.CondenserDuty or 0), 2), reboiler_kW=_r(abs(o.ReboilerDuty or 0), 2),
                             condenser_duty_kW=_r(o.CondenserDuty, 2), reboiler_duty_kW=_r(o.ReboilerDuty, 2),
                             dwsim_estimated_diameter_m=_r(o.EstimatedDiameter, 3) if o.EstimatedDiameter == o.EstimatedDiameter else None,
                             profile=shown, flood_frac=_r(max(fracs), 3) if fracs else None, flood_error=flood_error,
                             tray_spacing_m=spacing)
            except (TypeError, ZeroDivisionError) as ex:  # an unsolved unit reports why instead of failing the run
                r["error"] = f"did not solve ({ex.__class__.__name__}): check the unit's inlet streams and specs"
            un[uid] = r
        return {"streams": st, "units": un}

    def _hx_mode(self, u, h):
        """Rating mode by default (U and area given, outlets computed). A condensing or boiling side does not converge in
        that mode, so hot_out_T_C fixes the hot outlet (e.g. saturated condensate) and the cold outlet follows from the
        energy balance; the area check then says whether the installed area can deliver it."""
        if u.get("hot_out_T_C") is not None:
            h.CalcMode, h.TempHotOut = self.HXM.CalcTempColdOut, 273.15 + float(u["hot_out_T_C"])
        else:
            h.CalcMode = self.HXM.CalcBothTemp_UA

    def required_area(self, uid, out_T_C, side="cold"):
        """Area this exchanger needs to reach out_T_C on `side` at the current flows (DWSIM design mode)."""
        u, h = self.units[uid]
        from DWSIM.UnitOperations.UnitOperations import SpecifiedTemperature
        h.CalcMode = self.HXM.CalcArea
        if side == "cold":
            h.DefinedTemperature, h.TempColdOut = SpecifiedTemperature.Cold_Fluid, 273.15 + float(out_T_C)
        else:
            h.DefinedTemperature, h.TempHotOut = SpecifiedTemperature.Hot_Fluid, 273.15 + float(out_T_C)
        errs = self.solve()
        a = float(h.Area)
        h.Area = float(u.get("area_m2", 10))
        self._hx_mode(u, h)
        self.solve()
        return (round(a, 2) if not errs and a > 0 else None), errs


def _checks(sheet, res):
    """Utilisation (value / limit) of every stated limit; >1 means the equipment cannot do it."""
    out = []
    limits = sheet.spec.get("limits") or {}
    rated_valves = {uid for uid, (spec_u, _) in sheet.units.items() if spec_u["type"] == "valve" and
                    (spec_u.get("cv_rated") is not None or spec_u.get("kv_rated") is not None)}
    evaporators = sorted(uid for uid, (spec_u, _) in sheet.units.items() if spec_u["type"] == "evaporator")
    reactors = sorted(uid for uid, (spec_u, _) in sheet.units.items() if spec_u["type"] == "reactor")
    columns = sorted(uid for uid, (spec_u, _) in sheet.units.items() if spec_u["type"] == "distillation")
    for key in dict.fromkeys((*limits, *sorted(rated_valves), *evaporators, *reactors, *columns)):
        lim = limits.get(key, {})
        u, s = res["units"].get(key), res["streams"].get(key)
        def add(what, value, limit, unit, higher_is_worse=True):
            if value is None or not limit:
                return
            util = value / limit if higher_is_worse else (limit / value if value else 9.99)
            out.append({"id": key, "check": what, "value": value, "limit": limit, "unit": unit, "utilisation": round(util, 3)})
        if u and u["type"] == "pump":
            add("flow vs rated", u["m3_h"], lim.get("max_m3_h"), "m3/h")
            add("shaft power vs motor", u["kW"], lim.get("max_kW"), "kW")
            if u.get("kind") != "positive_displacement":  # a PD pump delivers whatever head the system needs, up to its relief
                add("head vs rated", u["head_m"], lim.get("max_head_m"), "m")
            add("flow vs minimum continuous", u["m3_h"], lim.get("min_m3_h"), "m3/h", higher_is_worse=False)
            add("NPSH available vs 1.3 x required", u["npsha_m"], 1.3 * lim["npshr_m"] if lim.get("npshr_m") else None, "m",
                higher_is_worse=False)
            add("discharge vs 90 % of relief set", u["discharge_barg"], 0.9 * lim["psv_set_barg"] if lim.get("psv_set_barg") else None, "barg")
        if u and u["type"] == "valve" and key in rated_valves:
            spec_u = sheet.units[key][0]
            if u.get("sizing_error"):
                out.append({"id": key, "check": "valve liquid sizing", "error": u["sizing_error"], "utilisation": 1.001})
            else:
                add("valve opening vs max travel", u.get("opening_pct"), float(spec_u.get("max_travel_pct", 90)), "%")
                add("valve opening vs min travel", u.get("opening_pct"), float(spec_u.get("min_travel_pct", 10)), "%",
                    higher_is_worse=False)
        if u and u["type"] == "pipe":
            add("velocity vs limit", u.get("velocity_m_s"), lim.get("max_velocity_m_s"), "m/s")
            # A downhill line can gain pressure. Only the positive loss consumes the available pressure-drop budget.
            add("pressure drop vs available", max(0.0, u.get("dP_bar") or 0.0), lim.get("max_dP_bar"), "bar")
        if u and u["type"] in ("hx", "heater", "cooler") and lim.get("out_T_C") is not None:
            side = lim.get("side", "cold")
            if u["type"] == "hx" and lim.get("area_m2"):
                need, errs = sheet.required_area(key, lim["out_T_C"], side)
                if need is not None:
                    add(f"area needed for {side} outlet {lim['out_T_C']} C", need, lim["area_m2"], "m2")
                else:
                    out.append({"id": key, "check": "required area", "error": "; ".join(errs)[:200] or "no solution"})
        if u and u["type"] == "evaporator":
            if u.get("error"):
                out.append({"id": key, "check": "evaporator inlet", "error": u["error"]})
            elif (u.get("boil_kW") or 0) > 0:
                add("heater area needed (BPE included) vs installed", u.get("area_needed_m2"), u.get("area_m2"), "m2")
            if u.get("heat_balance_kW") is not None and (u["boil_kW"] or 0) > 0 and not u.get("error"):
                tolerance = float(sheet.units[key][0].get("heat_balance_tolerance_pct", 2))
                add(f"boil-up duty vs heat from the heating steam ({tolerance:g} % closure tolerance)",
                    u["boil_kW"], u["heating_kW"] * (1 + tolerance / 100), "kW")
        if u and u["type"] == "compressor":
            add("suction flow vs capacity", (res["streams"].get(sheet.units[key][0]["in"]) or {}).get("kg_h"), lim.get("max_kg_h"), "kg/h")
            add("shaft power vs motor", u["kW"], lim.get("max_kW"), "kW")
            add("discharge temperature vs limit", u["discharge_C"], lim.get("max_discharge_C"), "C")
        if u and u["type"] == "column":
            add("stages needed vs installed", u["stages"], lim.get("installed_stages"), "stages")
            add("reboiler duty vs rated", u["reboiler_kW"], lim.get("max_reboiler_kW"), "kW")
            add("condenser duty vs rated", u["condenser_kW"], lim.get("max_condenser_kW"), "kW")
        if u and u["type"] == "reactor":
            if (u.get("cooling_kW") or 0) > 0:
                add("cooling duty vs cooling capacity", u.get("cooling_kW"), lim.get("max_duty_kW"), "kW")
            add("outlet temperature vs limit", u.get("T_out_C"), lim.get("max_T_C"), "C")
        if u and u["type"] == "distillation":
            add("reboiler duty vs rated", u.get("reboiler_kW"), lim.get("max_reboiler_kW"), "kW")
            add("condenser duty vs rated", u.get("condenser_kW"), lim.get("max_condenser_kW"), "kW")
            if u.get("flood_frac") is not None:
                add("Fair flood fraction vs limit", u["flood_frac"], lim.get("flood_frac_max", 0.8), "fraction of flood")
            elif u.get("flood_error"):
                out.append({"id": key, "check": "Fair flooding screen", "error": u["flood_error"]})
        if u and u["type"] == "hx":
            add("installed area vs frame", u["area_m2"], lim.get("max_area_m2"), "m2")
            add("hot-side pressure drop vs available", u["dP_hot_bar"], lim.get("max_dP_hot_bar"), "bar")
            add("cold-side pressure drop vs available", u["dP_cold_bar"], lim.get("max_dP_cold_bar"), "bar")
        if u and u["type"] in ("heater", "cooler") and lim.get("min_T_out_C") is not None:
            # a cooler/condenser cannot cool below what its heat sink allows (ambient or wet bulb + approach); in kelvin,
            # so the ratio stays meaningful near 0 C
            spec_u = sheet.units[key][0]
            t_out = (res["streams"].get(spec_u["out"]) or {}).get("T_C")
            if t_out is not None:
                out.append({"id": key, "check": "outlet temperature vs heat-sink minimum (ambient + approach)", "value": t_out,
                            "limit": lim["min_T_out_C"], "unit": "C",
                            "utilisation": round((lim["min_T_out_C"] + 273.15) / (t_out + 273.15), 3)})
        if u and lim.get("max_kW") and u["type"] in ("heater", "cooler"):  # an exchanger's datasheet duty is a design point, not a limit
            add("duty vs design", abs(u.get("duty_kW") or 0), lim["max_kW"], "kW")
        if u and u["type"] == "tank":
            add("residence time", u["residence_min"], lim.get("min_residence_min"), "min", higher_is_worse=False)
        if s and "T_C" in s:
            add("temperature vs design", s["T_C"], lim.get("max_T_C"), "C")
            add("pressure vs design", s["P_bar"], lim.get("max_P_bar"), "bar")
            if lim.get("must_be_liquid") and s.get("vapour_frac", 0) > 0:  # e.g. a condenser that cannot condense at this pressure
                out.append({"id": key, "check": "must leave as liquid", "value": s["vapour_frac"], "limit": 0, "unit": "vapour fraction",
                            "utilisation": round(1 + s["vapour_frac"], 3)})
            add("flow vs 90 % of available supply", s["m3_h"], UTILITY_MARGIN * lim["max_m3_h"] if lim.get("max_m3_h") else None, "m3/h")
    for uid, (spec_u, _) in sheet.units.items():
        if spec_u["type"] not in _CHECKED_TYPES:
            out.append({"id": uid, "check": "no limit check for this unit type", "type": spec_u["type"]})
    return sorted(out, key=lambda c: -c.get("utilisation", 0))


UTILITY_MARGIN = 0.9  # never plan a utility at more than 90 % of its stated supply
_MGR = None


def _capacity_search(worst, max_scale=5.0):
    """Bracket a stated physical limit; a failed solve is uncertainty, never a capacity result."""
    base, base_checks, errors = worst(1.0)
    common = {"checks_at_base": base_checks}
    if errors:
        return {"capacity_multiple": None, "limited_by": base, "errors": errors, **common,
                "note": "the base case did not solve, so no capacity was calculated"}
    if base is None:
        return {"error": "no limits to check; add `limits` with values from the P&ID or datasheets", "errors": errors}
    if base["utilisation"] > 1:
        feasible = []
        for scale in (0.1, 0.2, 0.4, 0.6, 0.8):
            check, checks, solve_errors = worst(scale)
            if not solve_errors and check is not None and check["utilisation"] <= 1:
                feasible.append((scale, check, checks))
        if not feasible:
            return {"capacity_multiple": None, "limited_by": base, "errors": [], **common,
                    "note": "the base case is already over a limit and no feasible lower throughput was found down to 10 %"}
        lo, _, _ = feasible[-1]
        hi = 1.0
    else:
        lo = hi = 1.0
        while hi < max_scale:
            trial = min(max_scale, hi * 1.25)
            check, _, solve_errors = worst(trial)
            if solve_errors:
                return {"capacity_multiple": None, "capacity_lower_bound": round(lo, 3), "limited_by": None,
                        "errors": solve_errors, **common,
                        "note": "the solver failed before a physical limit was bracketed; the last feasible scale is a lower bound"}
            if check is None:
                return {"capacity_multiple": None, "capacity_lower_bound": round(lo, 3), "limited_by": None,
                        "errors": [], **common, "note": "no limit check remained while searching for capacity"}
            hi = trial
            if check["utilisation"] > 1:
                break
            lo = hi
        if hi >= max_scale and check["utilisation"] <= 1:
            return {"capacity_multiple": None, "capacity_lower_bound": round(lo, 3), "limited_by": base,
                    "errors": [], **common,
                    "note": "no stated limit was reached through the maximum searched throughput"}
    for _ in range(12):
        mid = (lo + hi) / 2
        check, _, solve_errors = worst(mid)
        if solve_errors or check is None:
            return {"capacity_multiple": None, "capacity_lower_bound": round(lo, 3), "limited_by": None,
                    "errors": solve_errors, **common,
                    "note": "the solver failed inside the capacity bracket; no physical capacity is claimed"}
        lo, hi = (lo, mid) if check["utilisation"] > 1 else (mid, hi)
    check, at_capacity, solve_errors = worst(lo)
    if solve_errors or check is None:
        return {"capacity_multiple": None, "capacity_lower_bound": round(lo, 3), "limited_by": None,
                "errors": solve_errors, **common,
                "note": "the final capacity point did not solve; no physical capacity is claimed"}
    return {"capacity_multiple": round(lo, 3), "limited_by": check, "checks_at_capacity": at_capacity,
            "errors": [], **common,
            "note": "multiple of the current feed flows at which the first stated limit reaches 100 %"}


def _worker(a):
    global _MGR
    mgr = _MGR = _MGR or _dwsim()
    spec, op = a["spec"], a["op"]
    if op == "run":
        sh = _Sheet(mgr, spec, float(a.get("scale", 1.0)))
        errs = sh.solve()
        res = sh.results()
        return {"scale": a.get("scale", 1.0), "errors": errs, **res, "checks": _checks(sh, res)}
    if op == "capacity":
        # throughput multiple at which the first stated limit reaches 100 % (bisection on all feed flows)
        def worst(scale):
            sh = _Sheet(mgr, spec, scale)
            errs = sh.solve()
            res = sh.results()
            ch = [c for c in _checks(sh, res) if "utilisation" in c]
            return (max(ch, key=lambda c: c["utilisation"]) if ch else None), ch, errs
        return _capacity_search(worst)
    if op == "bubble":
        # pressure a blocked-in liquid reaches when heated to T (bubble point): a trapped-liquid overpressure check
        import System
        from DWSIM.Interfaces.Enums import StreamSpec
        sim = mgr.CreateFlowsheet()
        for c in spec["compounds"]:
            sim.AddCompound(c)
        sim.CreateAndAddPropertyPackage(spec.get("package") or "Peng-Robinson (PR)")
        s = sim.AddObject(__import__("DWSIM.Interfaces.Enums.GraphicObjects", fromlist=["ObjectType"]).ObjectType.MaterialStream,
                          0, 0, "S").GetAsObject()
        x = [float(spec["x"].get(c, 0)) for c in spec["compounds"]]
        s.SetOverallComposition(System.Array[System.Double]([v / sum(x) for v in x]))
        s.SetMassFlow(1.0)
        out = []
        for T in a["T_C"]:
            s.SpecType = StreamSpec.Temperature_and_VaporFraction
            s.SetTemperature(273.15 + float(T))
            s.Phases[2].Properties.molarfraction = 0.0
            errs = mgr.CalculateFlowsheet4(sim)
            out.append({"T_C": T, "bubble_P_bar": round(s.GetPressure() / 1e5, 2),
                        "errors": [str(e.Message)[:120] for e in errs] if errs is not None else []})
        return {"compounds": spec["compounds"], "x": spec["x"], "points": out,
                "note": "bubble-point pressure: a liquid-full, blocked-in vessel heated to T rises to at least this pressure "
                        "(thermal expansion of the liquid drives it higher still)"}
    if op == "blocked_in":
        # liquid-full, blocked-in vessel heated from T1 to T2 (API 521 hydraulic expansion): dP = beta * dT / kappa for a rigid
        # vessel, with the cubic expansion beta and compressibility kappa of the liquid taken from DWSIM at a pressure that keeps
        # it liquid. ponytail: linear form, as in API 521 and the CSB analysis; it overstates for large dT (kappa falls with P).
        T1, T2, P1 = float(a["T1_C"]), float(a["T2_C"]), float(a["P1_bar"])
        bub = _worker({"op": "bubble", "spec": spec, "T_C": [T2]})["points"][0]["bubble_P_bar"]
        Pr = max(P1, bub * 1.2)
        pts = _worker({"op": "props", "spec": spec, "points": [{"T_C": T1, "P_bar": Pr}, {"T_C": T2, "P_bar": Pr},
                                                                {"T_C": (T1 + T2) / 2, "P_bar": Pr}, {"T_C": (T1 + T2) / 2, "P_bar": Pr + 50}]})["points"]
        r1, r2, rm, rm50 = (p["density_kg_m3"] for p in pts)
        beta = (r1 / r2 - 1) / (T2 - T1)          # 1/K
        kappa = (rm50 - rm) / rm / 50             # 1/bar
        dp = beta * (T2 - T1) / kappa
        # a vapour or gas pocket absorbs the expansion: below this liquid fill fraction at T1 the vessel only reaches the
        # vapour pressure at T2; above it the liquid fills the vessel and hydraulic expansion governs
        rho_bub = _worker({"op": "props", "spec": spec, "points": [{"T_C": T2, "P_bar": bub * 1.001 + 0.01}]})["points"][0]
        crit = round(rho_bub["density_kg_m3"] / r1, 3) if rho_bub["vapour_frac"] == 0 else None
        return {"T1_C": T1, "T2_C": T2, "P1_bar": P1, "bubble_P_bar_at_T2": bub,
                "bubble_psig_at_T2": round((bub - 1.013) * 14.5038, -1),
                "critical_liquid_fill_at_T1": crit,
                "regimes": f"If the vessel held less than {crit:.0%} liquid by volume at T1, the liquid stays below liquid-full "
                           f"and the pressure stays at the vapour pressure ({bub:.1f} bar). Above that fill, hydraulic expansion "
                           f"governs (the pressure below)." if crit else "",
                "beta_per_K": round(beta, 5),
                "kappa_per_bar": round(kappa, 6), "pressure_rise_bar_per_K": round(beta / kappa, 1),
                "pressure_bar": round(P1 + dp, 0), "pressure_psig": round((P1 + dp - 1.013) * 14.5038, -1),
                "note": "API 521 hydraulic-expansion screening for a liquid-full rigid vessel (linear beta/kappa). Wall stretch "
                        "lowers it; the fill fraction decides which regime applies."}
    if op == "props":
        # density and phase of a mixture at given T and P (liquid expansion, vessel fill checks)
        import System
        from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
        sim = mgr.CreateFlowsheet()
        for c in spec["compounds"]:
            sim.AddCompound(c)
        sim.CreateAndAddPropertyPackage(spec.get("package") or "Peng-Robinson (PR)")
        s = sim.AddObject(ObjectType.MaterialStream, 0, 0, "S").GetAsObject()
        x = [float(spec["x"].get(c, 0)) for c in spec["compounds"]]
        s.SetOverallComposition(System.Array[System.Double]([v / sum(x) for v in x]))
        s.SetMassFlow(1.0)
        out = []
        for pt in a["points"]:
            s.SetTemperature(273.15 + float(pt["T_C"]))
            s.SetPressure(float(pt["P_bar"]) * 1e5)
            errs = mgr.CalculateFlowsheet4(sim)
            out.append({**pt, "density_kg_m3": round(s.GetMassFlow() / s.GetVolumetricFlow(), 2),
                        "vapour_frac": round(float(s.Phases[2].Properties.molarfraction or 0.0), 4),
                        "errors": [str(e.Message)[:120] for e in errs] if errs is not None else []})
        return {"compounds": spec["compounds"], "x": spec["x"], "points": out}
    raise ValueError(op)


# ---------------------------------------------------------------- caller side
_PROC, _LOCK = None, __import__("threading").Lock()


SOLVE_TIMEOUT_S = 150


def _call(payload, timeout_s=None):
    """One long-lived DWSIM worker (start-up once, then ~0.05 s per solve); restarted if it dies.
    ponytail: one global lock serialises solves; a worker pool if several users solve at once."""
    global _PROC
    with _LOCK:
        for attempt in (0, 1):
            if _PROC is None or _PROC.poll() is not None:
                _PROC = subprocess.Popen([sys.executable, "-m", "plantagent.process", "--serve"], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=ROOT)
            try:
                _PROC.stdin.write(json.dumps(payload) + "\n")
                _PROC.stdin.flush()
                # a flowsheet that never converges (e.g. nested recycles) would hang the caller: give up after SOLVE_TIMEOUT_S
                if not select.select([_PROC.stdout], [], [], timeout_s or SOLVE_TIMEOUT_S)[0]:
                    _PROC.kill()
                    _PROC = None
                    raise RuntimeError(f"DWSIM did not finish within {timeout_s or SOLVE_TIMEOUT_S} s (the flowsheet does not converge); "
                                       "simplify it: fewer recycle loops, or the evaporator unit for boiling brine bodies")
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
        raise RuntimeError("DWSIM worker failed")


def available():
    return (DW / "DWSIM.Automation.dll").exists() and DOTNET.exists()


def run(spec, scale=1.0):
    return _call({"op": "run", "spec": spec, "scale": scale})


def capacity(spec):
    return _call({"op": "capacity", "spec": spec}, timeout_s=900)  # many solves (bisection)


def bubble(compounds, x, T_C, package="Peng-Robinson (PR)"):
    return _call({"op": "bubble", "spec": {"compounds": compounds, "x": x, "package": package}, "T_C": list(T_C)})


def blocked_in(compounds, x, T1_C, P1_bar, T2_C, package="Peng-Robinson (PR)"):
    return _call({"op": "blocked_in", "spec": {"compounds": compounds, "x": x, "package": package},
                  "T1_C": T1_C, "P1_bar": P1_bar, "T2_C": T2_C})


def props(compounds, x, points, package="Peng-Robinson (PR)"):
    return _call({"op": "props", "spec": {"compounds": compounds, "x": x, "package": package}, "points": list(points)})


DEMO = {
    "compounds": ["Water", "Ethanol"], "package": "NRTL",
    "feeds": {"FEED": {"T_C": 25, "P_bar": 1.2, "kg_h": 18000, "x": {"Water": 0.9, "Ethanol": 0.1}},
              "HOT_IN": {"T_C": 90, "P_bar": 3, "kg_h": 21600, "x": {"Water": 1}, "utility": True}},
    "units": [{"id": "P-101", "type": "pump", "in": "FEED", "out": "S1", "dP_bar": 4, "eff_pct": 70},
              {"id": "E-101", "type": "hx", "cold": ["S1", "S2"], "hot": ["HOT_IN", "HOT_OUT"], "U_W_m2K": 1500, "area_m2": 10},
              {"id": "V-101", "type": "valve", "in": "S2", "out": "S3", "dP_bar": 2},
              {"id": "T-101", "type": "tank", "in": "S3", "out": "PROD", "volume_m3": 10}],
    "limits": {"E-101": {"area_m2": 10, "out_T_C": 52, "side": "cold"}, "P-101": {"max_m3_h": 30, "max_kW": 4},
               "T-101": {"min_residence_min": 25}},
}

if __name__ == "__main__":
    if "--serve" in sys.argv:
        out = sys.stdout
        sys.stdout = sys.stderr  # DWSIM may print; keep the protocol channel clean
        for line in sys.stdin:
            try:
                r = _worker(json.loads(line))
            except Exception as ex:  # noqa: BLE001 - report to the caller, keep serving
                r = {"worker_error": f"{type(ex).__name__}: {ex}"[:2000]}
            out.write(json.dumps(r) + "\n")
            out.flush()
    else:
        r = run(DEMO)
        assert not r["errors"], r["errors"]
        print(r["units"], r["checks"][:3], sep="\n")
        c = capacity(DEMO)
        print("capacity", c["capacity_multiple"], c["limited_by"])
        assert 1.0 < c["capacity_multiple"] < 2.0
        b = bubble(["Propylene", "Propane"], {"Propylene": 0.9, "Propane": 0.1}, [20, 60, 90])
        print(b["points"])
        d = props(["Propane"], {"Propane": 1}, [{"T_C": 25, "P_bar": 20}, {"T_C": 85, "P_bar": 60}])["points"]
        print(d)
        assert 450 < d[0]["density_kg_m3"] < 520 and d[1]["density_kg_m3"] < d[0]["density_kg_m3"]
        bi = blocked_in(["Propane", "Propylene"], {"Propane": 0.95, "Propylene": 0.05}, 25, 15, 86)  # Williams: 77 F -> 187 F
        print("blocked-in 25->86 C:", bi)
        # a condenser cannot cool below wet bulb + approach: a lower outlet must show as over its limit
        cyc = {"compounds": ["Ammonia"], "package": "Peng-Robinson (PR)",
               "feeds": {"SUC": {"T_C": -8, "P_bar": 2.9, "kg_h": 3600, "x": {"Ammonia": 1}}},
               "units": [{"id": "K", "type": "compressor", "in": "SUC", "out": "DIS", "P_out_bar": 8.6, "eff_pct": 75},
                         {"id": "COND", "type": "cooler", "in": "DIS", "out": "LIQ", "T_out_C": 18}],
               "limits": {"COND": {"min_T_out_C": 28}}}
        ch = [c for c in run(cyc)["checks"] if c["id"] == "COND" and "heat-sink" in c["check"]]
        assert ch and ch[0]["utilisation"] > 1, ch
        assert bi["pressure_psig"] > 2000, "heating liquid-full propane by 60 K must reach thousands of psi"
        assert b["points"][2]["bubble_P_bar"] > b["points"][0]["bubble_P_bar"] > 5
        section = {"compounds": ["Carbon dioxide", "Water"], "package": "Peng-Robinson (PR)",
                   "feeds": {"IN": {"T_C": 29, "P_bar": 32, "kg_h": 1000,
                                    "x": {"Carbon dioxide": 0.97, "Water": 0.03}}},
                   "units": [{"id": "V", "type": "flash", "in": "IN", "vapor": "VAP", "liquid": "LIQ"},
                             {"id": "DRY", "type": "component_separator", "in": "VAP", "product": "DRY_CO2",
                              "reject": "WET", "recover_pct": {"Water": 10}}]}
        sr = run(section)
        assert not sr["errors"], sr["errors"]
        ss = sr["streams"]
        assert abs(ss["VAP"]["kg_h"] + ss["LIQ"]["kg_h"] - 1000) < 1
        assert ss["LIQ"]["kg_h"] > 0 and ss["VAP"]["kg_h"] > 0
        assert abs(ss["DRY_CO2"]["kg_h"] + ss["WET"]["kg_h"] - ss["VAP"]["kg_h"]) < 1
        assert abs(ss["DRY_CO2"]["components_kg_h"]["Water"] / ss["VAP"]["components_kg_h"]["Water"] - 0.1) < 0.02
        assert any(c["id"] == "V" and c["check"] == "no limit check for this unit type" for c in sr["checks"])
        conv = {"compounds": ["Ethylene", "Hydrogen", "Ethane"], "package": "Peng-Robinson (PR)",
                "feeds": {"F": {"T_C": 77, "P_bar": 5, "kg_h": 3600, "x": {"Ethylene": 0.5, "Hydrogen": 0.5}}},
                "units": [{"id": "R", "type": "reactor", "kind": "conversion", "in": "F", "vapor": "V", "liquid": "L",
                           "mode": "isothermal", "phase": "Vapor",
                           "reactions": [{"name": "HYD", "base": "Ethylene", "conversion_pct": 90,
                                          "stoich": {"Ethylene": -1, "Hydrogen": -1, "Ethane": 1}}]}],
                "limits": {"R": {"max_duty_kW": 1e6, "max_T_C": 200}}}
        cr = run(conv)
        assert not cr["errors"], cr["errors"]
        ru = cr["units"]["R"]
        assert 85 < ru["conversion_pct"] < 95 and ru["duty_kW"] < 0 and 70 < ru["T_out_C"] < 85, ru
        col = {"compounds": ["Benzene", "Toluene"], "package": "Peng-Robinson (PR)",
               "feeds": {"F": {"T_C": 92, "P_bar": 1.013, "kg_h": 3064, "x": {"Benzene": 0.5, "Toluene": 0.5}}},
               "units": [{"id": "C", "type": "distillation", "in": "F", "distillate": "D", "bottoms": "B",
                          "stages": 12, "feed_stage": 7, "condenser": "total", "P_bar": 1.01325,
                          "reflux_ratio": 2.0, "bottoms_mol_s": 5.0}],
               "limits": {"C": {"diameter_m": 0.9, "tray_spacing_m": 0.5, "flood_frac_max": 0.8}}}
        c1, c2 = run(col), run(col, 2.0)
        assert not c1["errors"], c1["errors"]
        assert not c2["errors"], c2["errors"]
        assert c1["streams"]["D"]["components_kg_h"]["Benzene"] > c1["streams"]["B"]["components_kg_h"]["Benzene"]
        f1, f2 = c1["units"]["C"]["flood_frac"], c2["units"]["C"]["flood_frac"]
        assert f1 and f2 and f2 > f1, (f1, f2, c1["units"]["C"].get("flood_error"), c2["errors"])
        assert c1["units"]["C"]["condenser_kW"] and len(c1["units"]["C"]["profile"]) == 12
        # evaporator: US 5,366,514 Table I boil-up (247.7 t/h) and salt; +20 % feed with a fixed compressor flow runs short of heat
        ev = {"compounds": ["Water"], "package": "Steam Tables (IAPWS-IF97)",
              "feeds": {"B": {"T_C": 125.6, "P_bar": 3, "kg_h": 362900, "x": {"Water": 1}}},
              "units": [{"id": "V", "type": "evaporator", "in": "B", "vapor": "VAP", "liquid": "L", "P_bar": 1.7, "evap_frac": 0.68,
                         "heating": ["ST", "C"], "U_W_m2K": 2000, "area_m2": 8800},
                        {"id": "SP", "type": "splitter", "in": "VAP", "out": ["SUC", "X"], "fixed_kg_h": {"SUC": 226800}},
                        {"id": "K", "type": "compressor", "in": "SUC", "out": "ST", "P_out_bar": 3.08, "eff_pct": 78}]}
        e1, e2 = run(ev), run(ev, 1.2)
        v1 = e1["units"]["V"]
        assert not e1["errors"] and 240000 < v1["vapour_kg_h"] < 255000 and 9 < v1["bpe_K"] < 10.5 and v1["driving_dT_K"] > 5, v1
        assert any(c["check"].startswith("boil-up") and c["utilisation"] > 1 for c in e2["checks"]), e2["checks"]
        # Same compressor-limited boil-up, with feed adjusted for each water fraction and a small mother-liquor purge.
        import copy
        balance = copy.deepcopy(ev)
        balance["units"][0].pop("heating")
        balance["units"][0].update(feed_x_NaCl=0.26, evap_frac=0.73)
        balance["feeds"]["B"]["kg_h"] = 247700 / 0.73
        rich = run(balance)["units"]["V"]
        balance["units"][0].update(feed_x_NaCl=0.20, evap_frac=0.79)
        balance["feeds"]["B"]["kg_h"] = 247700 / 0.79
        lean = run(balance)["units"]["V"]
        ratio = (0.20 / 0.80) / (0.26 / 0.74)
        assert abs(rich["vapour_kg_h"] - lean["vapour_kg_h"]) < 1 and abs(lean["salt_kg_h"] / rich["salt_kg_h"] - ratio) < 0.02
        heated = copy.deepcopy(ev)
        heated["units"][0]["feed_x_NaCl"] = 0.26
        warm = run(heated)["units"]["V"]
        heated["feeds"]["B"]["T_C"] = 120
        cold = run(heated)["units"]["V"]
        assert cold["vapour_kg_h"] < warm["vapour_kg_h"] and cold["sensible_correction_kW"] < warm["sensible_correction_kW"]
        print("ok")
