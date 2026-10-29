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
             "(steam that condenses fully), U_W_m2K, area_m2, x_NaCl (omit for a salt-crystallising body: saturated brine; then "
             "salt_kg_h is reported; model the brine as Water with the Steam Tables (IAPWS-IF97) package: DWSIM's NRTL has no NaCl electrolyte data and gives about a third of the real boiling point elevation). Applies the NaCl boiling point elevation to the driving force and checks the heater area "
             "and the heat balance (boil-up vs heat the heating steam gives; >1 means the steam cannot sustain the boil-up). "
             "flash: in, vapor, liquid (equilibrium phase split at inlet T and P; use a cooler or valve first). "
             "component_separator: in, product, reject, recover_pct {compound: percent of inlet moles sent to product; omitted compounds default to 100}; fixed-split approximation, not a TEG or PSA design model. "
             "column: in, distillate, bottoms, light_key, heavy_key (compound names), light_key_in_bottoms and "
             "heavy_key_in_distillate (mole fractions), reflux_ratio, P_bar (shortcut method: reports minimum and actual stages, "
             "minimum reflux, condenser and reboiler duty). "
             "recycle: in (the calculated return stream), out (the tear stream used upstream, e.g. into a mixer), guess "
             "{T_C, kg_h} (closes recirculation loops). Streams are created by name the first time they appear. Model EVERY "
             "connection on the P&ID that carries process flow (recirculation loops included) or say why it is excluded.",
    "limits": "{unit or stream id: {max_m3_h, min_m3_h (pump minimum continuous flow), max_kW (pump or compressor motor), max_kg_h (compressor suction capacity), max_discharge_C (compressor), max_head_m, npshr_m, "
              "psv_set_barg (relief valve on the pump discharge: discharge must stay below 90 % of set), area_m2 (installed HX "
              "area), out_T_C (outlet the process needs, side: cold|hot), max_dP_hot_bar, max_dP_cold_bar (available pressure "
              "drop), min_residence_min, max_area_m2 (HX frame limit), and for streams max_T_C, max_P_bar (design limit), "
              "max_m3_h (utility supply; checked against 90 % of it to keep a margin), max_velocity_m_s and max_dP_bar (pipe; "
              "3 m/s is a typical liquid pump-discharge screen per Grundfos guidance, not a universal limit), "
              "must_be_liquid: true (e.g. condenser outlet), min_T_out_C (cooler or condenser: the lowest outlet its heat sink allows at "
              "design conditions, e.g. design wet bulb + approach for an evaporative condenser)}}. Values come from the P&ID or datasheets; cite them.",
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
        return round(float(x), n)
    except (TypeError, ValueError):
        return None


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
                              "kg_h": g.get("kg_h", ref.get("kg_h") or float(ref.get("m3_h", 1)) * 1000), "x": g.get("x", ref.get("x", {}))}, 1.0)
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
            sp.Ratios[0], sp.Ratios[1] = f, 1 - f
            b = hs[0]
            self.__dict__.setdefault("aux_liq", {})[uid] = hs[1]
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
        raise ValueError(f"unknown unit type {t}")

    def solve(self):
        errs = self.mgr.CalculateFlowsheet4(self.sim)
        errs = [str(e.Message)[:200] for e in errs] if errs is not None else []
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
                    x = u.get("x_NaCl")
                    b = brine.bpe(float(u["P_bar"]), x)
                    boil = (o.DeltaQ or 0) + (getattr(self, "aux_liq", {})[uid].DeltaQ or 0)
                    if boil < 0 or (self.streams[u["in"]].GetPhase("Vapor").Properties.molarfraction or 0) > 0.99:
                        r["error"] = ("inlet is vapour in the water stand-in: brine above the water saturation temperature at its "
                                      "pressure only stays liquid through its BPE; give that feed at a pressure where water is liquid")
                    r.update(boil_kW=_r(boil, 1), vapour_kg_h=_r(vap, 0), brine_T_C=b["t_brine_C"], bpe_K=b["bpe_K"],
                             salt_kg_h=_r(vap * b["x_NaCl"] / (1 - b["x_NaCl"]), 0) if x is None else None)
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
    for key in dict.fromkeys((*limits, *sorted(rated_valves), *evaporators)):
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
            add("pressure drop vs available", u.get("dP_bar"), lim.get("max_dP_bar"), "bar")
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
                # ponytail: 2 % energy-closure tolerance (feed preheat, losses); a real shortfall is far larger
                add("boil-up duty vs heat from the heating steam (2 % closure tolerance)", u["boil_kW"], u["heating_kW"] * 1.02, "kW")
        if u and u["type"] == "compressor":
            add("suction flow vs capacity", (res["streams"].get(sheet.units[key][0]["in"]) or {}).get("kg_h"), lim.get("max_kg_h"), "kg/h")
            add("shaft power vs motor", u["kW"], lim.get("max_kW"), "kW")
            add("discharge temperature vs limit", u["discharge_C"], lim.get("max_discharge_C"), "C")
        if u and u["type"] == "column":
            add("stages needed vs installed", u["stages"], lim.get("installed_stages"), "stages")
            add("reboiler duty vs rated", u["reboiler_kW"], lim.get("max_reboiler_kW"), "kW")
            add("condenser duty vs rated", u["condenser_kW"], lim.get("max_condenser_kW"), "kW")
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
    return sorted(out, key=lambda c: -c.get("utilisation", 0))


UTILITY_MARGIN = 0.9  # never plan a utility at more than 90 % of its stated supply
_MGR = None


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
        base, base_checks, errs = worst(1.0)
        if base is None:
            return {"error": "no limits to check; add `limits` with values from the P&ID or datasheets", "errors": errs}
        lo, hi = (0.1, 1.0) if base["utilisation"] > 1 else (1.0, 1.0)
        over = lambda w, errs: w is None or bool(errs) or w["utilisation"] > 1  # a solve that fails counts as over the limit  # noqa: E731
        while base["utilisation"] <= 1 and hi < 5:
            hi *= 1.25
            w, _, e = worst(hi)
            if over(w, e):
                break
            lo = hi
        for _ in range(12):
            mid = (lo + hi) / 2
            w, _, e = worst(mid)
            lo, hi = (lo, mid) if over(w, e) else (mid, hi)
        w, at_cap, _ = worst(lo)
        return {"capacity_multiple": round(lo, 3), "limited_by": w, "checks_at_capacity": at_cap,
                "checks_at_base": base_checks, "errors": errs,
                "note": "multiple of the current feed flows at which the first stated limit reaches 100 %"}
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
                r = {"worker_error": f"{type(ex).__name__}: {ex}"[:400]}
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
        print("ok")
