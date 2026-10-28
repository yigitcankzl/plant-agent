"""Process plants (chemical, food, pharma, utilities) in DWSIM: build a flowsheet from a JSON spec, solve it, and find
which equipment limits throughput.

DWSIM runs through pythonnet and must run with cwd = its install dir, so every call is a subprocess worker
(about 2 s start-up, then about 0.05 s per solve).
"""
import json
import os
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
             "hx: cold [in, out], hot [in, out], U_W_m2K, area_m2 (rating: outlets are computed); optional U_ref_flows_m3_h "
             "[hot, cold] (U then varies with flow, each film ~ Q^0.8) and dP_ref_bar [hot, cold] at those flows (dP ~ Q^1.8). "
             "heater|cooler: in, out, T_out_C or duty_kW (scales: true if that duty grows with throughput, e.g. an IT or process heat load). valve: in, out, dP_bar or kv or P_out_bar. "
             "tank: in, out, volume_m3 = WORKING volume (about 80 % of nominal unless the data says otherwise), P_bar = vessel "
             "pressure (an atmospheric tank is about 1.013; the outlet leaves at this pressure, which sets pump suction and NPSH), "
             "residence_basis = the product stream that leaves the tank for good (hold time = volume / that flow). "
             "mixer: in [..], out. splitter: in, out [..], fractions [..] or fixed_kg_h {out stream: kg/h} (the first outlet fixed, "
             "the other takes the rest: in a recirculation loop fix the recirculation branch and let the product take the rest). compressor: in, out, P_out_bar, eff_pct. "
             "recycle: in (the calculated return stream), out (the tear stream used upstream, e.g. into a mixer), guess "
             "{T_C, kg_h} (closes recirculation loops). Streams are created by name the first time they appear. Model EVERY "
             "connection on the P&ID that carries process flow (recirculation loops included) or say why it is excluded.",
    "limits": "{unit or stream id: {max_m3_h, min_m3_h (pump minimum continuous flow), max_kW (pump or compressor motor), max_discharge_C (compressor), max_head_m, npshr_m, "
              "psv_set_barg (relief valve on the pump discharge: discharge must stay below 90 % of set), area_m2 (installed HX "
              "area), out_T_C (outlet the process needs, side: cold|hot), max_dP_hot_bar, max_dP_cold_bar (available pressure "
              "drop), min_residence_min, max_area_m2 (HX frame limit), and for streams max_T_C, max_P_bar (design limit), "
              "max_m3_h (utility supply; checked against 90 % of it to keep a margin), must_be_liquid: true (e.g. condenser outlet)}}. Values come from the P&ID or datasheets; cite them.",
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
            h.CalcMode = self.HXM.CalcBothTemp_UA
            h.OverallCoefficient, h.Area = float(u.get("U_W_m2K", 1000)), float(u.get("area_m2", 10))
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
            v = self._add("Valve", uid)
            self._link(self.stream(u["in"]), v); self._link(v, self.stream(u["out"]))
            if u.get("kv") is not None:
                v.CalcMode, v.Kv = self.Valve.CalculationMode.Kv_Liquid, float(u["kv"])
            elif u.get("P_out_bar") is not None:
                v.CalcMode, v.OutletPressure = self.Valve.CalculationMode.OutletPressure, float(u["P_out_bar"]) * 1e5
            else:
                v.CalcMode, v.DeltaP = self.Valve.CalculationMode.DeltaP, float(u.get("dP_bar", 0.5)) * 1e5
            return v
        if t == "tank":
            k = self._add("Tank", uid)
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
        raise ValueError(f"unknown unit type {t}")

    def solve(self):
        errs = self.mgr.CalculateFlowsheet4(self.sim)
        errs = [str(e.Message)[:200] for e in errs] if errs is not None else []
        flowdep = [(u, o) for u, o in self.units.values() if u["type"] == "hx" and (u.get("U_ref_flows_m3_h") or u.get("dP_ref_bar"))]
        for _ in range(2 if flowdep and not errs else 0):  # exchanger U and dP follow the solved flows
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
            e2 = self.mgr.CalculateFlowsheet4(self.sim)
            errs = [str(e.Message)[:200] for e in e2] if e2 is not None else []
        return errs

    def results(self):
        st = {}
        for n, s in self.streams.items():
            try:
                st[n] = {"T_C": round(s.GetTemperature() - 273.15, 2), "P_bar": round(s.GetPressure() / 1e5, 3),
                         "kg_h": round(s.GetMassFlow() * 3600, 1), "m3_h": round(s.GetVolumetricFlow() * 3600, 2),
                         "vapour_frac": round(float(s.Phases[2].Properties.molarfraction or 0.0), 4)}
            except Exception as ex:  # noqa: BLE001 - an unsolved stream reports why
                st[n] = {"error": str(ex)[:120]}
        un = {}
        for uid, (u, o) in self.units.items():
            t, r = u["type"], {"type": u["type"]}
            if t == "pump":
                q = self.streams[u["in"]].GetVolumetricFlow() * 3600
                # ponytail: DWSIM leaves DeltaQ at 0 in curve mode, so shaft power is Q*dP/eta
                r.update(m3_h=round(q, 2), head_m=round(o.Head, 2), dP_bar=round(o.DeltaP / 1e5, 3), eff_pct=round(o.Eficiencia, 1),
                         kW=round(q / 3600 * o.DeltaP / (o.Eficiencia / 100) / 1000, 2), npsha_m=round(o.NPSH, 2),
                         discharge_barg=round(self.streams[u["out"]].GetPressure() / 1e5 - 1.013, 3),
                         kind=u.get("kind", "centrifugal"))
            elif t == "hx":
                r.update(duty_kW=round(o.Q, 1), lmtd_C=round(o.LMTD, 2), U_W_m2K=round(o.OverallCoefficient, 1), area_m2=round(o.Area, 2),
                         dP_hot_bar=round(o.HotSidePressureDrop / 1e5, 3), dP_cold_bar=round(o.ColdSidePressureDrop / 1e5, 3))
            elif t in ("heater", "cooler"):
                r.update(duty_kW=round(o.DeltaQ, 2))
            elif t == "compressor":
                r.update(duty_kW=round(o.DeltaQ, 2), kW=round(o.DeltaQ, 2),
                         discharge_C=round(self.streams[u["out"]].GetTemperature() - 273.15, 1))
            elif t == "valve":
                r.update(dP_bar=round(o.DeltaP / 1e5, 3))
            elif t == "tank":
                # hold time is volume over the NET throughput (the product leaving), not over a recirculation loop
                basis = u.get("residence_basis")
                q = self.streams[basis].GetVolumetricFlow() if basis in self.streams else None
                r.update(residence_min=round(o.Volume / q / 60 if q else o.ResidenceTime / 60, 2), volume_m3=o.Volume,
                         residence_basis=basis or "tank outlet")
            un[uid] = r
        return {"streams": st, "units": un}

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
        h.CalcMode, h.Area = self.HXM.CalcBothTemp_UA, float(u.get("area_m2", 10))
        self.solve()
        return (round(a, 2) if not errs and a > 0 else None), errs


def _checks(sheet, res):
    """Utilisation (value / limit) of every stated limit; >1 means the equipment cannot do it."""
    out = []
    for key, lim in (sheet.spec.get("limits") or {}).items():
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
        if u and u["type"] in ("hx", "heater", "cooler") and lim.get("out_T_C") is not None:
            side = lim.get("side", "cold")
            if u["type"] == "hx" and lim.get("area_m2"):
                need, errs = sheet.required_area(key, lim["out_T_C"], side)
                if need is not None:
                    add(f"area needed for {side} outlet {lim['out_T_C']} C", need, lim["area_m2"], "m2")
                else:
                    out.append({"id": key, "check": "required area", "error": "; ".join(errs)[:200] or "no solution"})
        if u and u["type"] == "compressor":
            add("shaft power vs motor", u["kW"], lim.get("max_kW"), "kW")
            add("discharge temperature vs limit", u["discharge_C"], lim.get("max_discharge_C"), "C")
        if u and u["type"] == "hx":
            add("installed area vs frame", u["area_m2"], lim.get("max_area_m2"), "m2")
            add("hot-side pressure drop vs available", u["dP_hot_bar"], lim.get("max_dP_hot_bar"), "bar")
            add("cold-side pressure drop vs available", u["dP_cold_bar"], lim.get("max_dP_cold_bar"), "bar")
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


def _call(payload):
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
    return _call({"op": "capacity", "spec": spec})


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
        assert bi["pressure_psig"] > 2000, "heating liquid-full propane by 60 K must reach thousands of psi"
        assert b["points"][2]["bubble_P_bar"] > b["points"][0]["bubble_P_bar"] > 5
        print("ok")
