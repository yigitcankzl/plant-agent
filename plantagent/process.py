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
    "feeds": "{stream: {T_C, P_bar, kg_h | m3_h (liquid at feed T), x: {compound: mole fraction}}}",
    "units": "list, each with id and type. pump: in, out, dP_bar or curve [[m3_h, head_m],...], eff_pct. "
             "hx: cold [in, out], hot [in, out], U_W_m2K, area_m2 (rating: outlets are computed). "
             "heater|cooler: in, out, T_out_C or duty_kW. valve: in, out, dP_bar or kv. tank: in, out, volume_m3. "
             "mixer: in [..], out. splitter: in, out [..], fractions [..]. compressor: in, out, P_out_bar, eff_pct. "
             "Streams are created by name the first time they appear.",
    "limits": "{unit or stream id: {max_m3_h, max_kW, max_head_m, area_m2 (installed HX area), out_T_C (HX/heater outlet the process "
              "needs, on the side given by side: cold|hot), min_residence_min, max_T_C, max_P_bar (design limit)}}. Values come from "
              "the P&ID or datasheets; cite them.",
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
        self.streams, self.units = {}, {}
        for name, f in spec.get("feeds", {}).items():
            self._feed(self.stream(name), f, scale)
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
                h.DeltaQ = float(u["duty_kW"])
            return h
        if t == "valve":
            v = self._add("Valve", uid)
            self._link(self.stream(u["in"]), v); self._link(v, self.stream(u["out"]))
            if u.get("kv") is not None:
                v.CalcMode, v.Kv = self.Valve.CalculationMode.Kv_Liquid, float(u["kv"])
            else:
                v.CalcMode, v.DeltaP = self.Valve.CalculationMode.DeltaP, float(u.get("dP_bar", 0.5)) * 1e5
            return v
        if t == "tank":
            k = self._add("Tank", uid)
            self._link(self.stream(u["in"]), k); self._link(k, self.stream(u["out"]))
            k.Volume = float(u.get("volume_m3", 10))
            return k
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
            for i, f in enumerate(u["fractions"]):
                sp.Ratios[i] = float(f)
            return sp
        if t == "compressor":
            c = self._add("Compressor", uid)
            self._link(self.stream(u["in"]), c); self._link(c, self.stream(u["out"]))
            self._link(self._add("EnergyStream", f"E-{uid}"), c)
            c.CalcMode, c.POut = self.Comp.CalculationMode.OutletPressure, float(u["P_out_bar"]) * 1e5
            c.AdiabaticEfficiency = float(u.get("eff_pct", 75)) / 100
            return c
        raise ValueError(f"unknown unit type {t}")

    def solve(self):
        errs = self.mgr.CalculateFlowsheet4(self.sim)
        return [str(e.Message)[:200] for e in errs] if errs is not None else []

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
                         kW=round(q / 3600 * o.DeltaP / (o.Eficiencia / 100) / 1000, 2), npsha_m=round(o.NPSH, 2))
            elif t == "hx":
                r.update(duty_kW=round(o.Q, 1), lmtd_C=round(o.LMTD, 2), U_W_m2K=o.OverallCoefficient, area_m2=round(o.Area, 2))
            elif t in ("heater", "cooler", "compressor"):
                r.update(duty_kW=round(o.DeltaQ, 2))
            elif t == "valve":
                r.update(dP_bar=round(o.DeltaP / 1e5, 3))
            elif t == "tank":
                r.update(residence_min=round(o.ResidenceTime / 60, 2), volume_m3=o.Volume)
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
            add("head vs rated", u["head_m"], lim.get("max_head_m"), "m")
        if u and u["type"] in ("hx", "heater", "cooler") and lim.get("out_T_C") is not None:
            side = lim.get("side", "cold")
            if u["type"] == "hx" and lim.get("area_m2"):
                need, errs = sheet.required_area(key, lim["out_T_C"], side)
                if need is not None:
                    add(f"area needed for {side} outlet {lim['out_T_C']} C", need, lim["area_m2"], "m2")
                else:
                    out.append({"id": key, "check": "required area", "error": "; ".join(errs)[:200] or "no solution"})
        if u and lim.get("max_kW") and u["type"] in ("hx", "heater", "cooler"):
            add("duty vs design", abs(u.get("duty_kW") or 0), lim["max_kW"], "kW")
        if u and u["type"] == "tank":
            add("residence time", u["residence_min"], lim.get("min_residence_min"), "min", higher_is_worse=False)
        if s and "T_C" in s:
            add("temperature vs design", s["T_C"], lim.get("max_T_C"), "C")
            add("pressure vs design", s["P_bar"], lim.get("max_P_bar"), "bar")
    return sorted(out, key=lambda c: -c.get("utilisation", 0))


def _worker(a):
    mgr = _dwsim()
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
        while base["utilisation"] <= 1 and hi < 5:
            hi *= 1.25
            w, _, _ = worst(hi)
            if w["utilisation"] > 1:
                break
            lo = hi
        for _ in range(12):
            mid = (lo + hi) / 2
            w, _, _ = worst(mid)
            lo, hi = (mid, hi) if w["utilisation"] <= 1 else (lo, mid)
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
    raise ValueError(op)


# ---------------------------------------------------------------- caller side
def _call(payload):
    out = subprocess.run([sys.executable, "-m", "plantagent.process", "--worker"], input=json.dumps(payload),
                         capture_output=True, text=True, cwd=ROOT, timeout=300)
    lines = out.stdout.strip().splitlines()
    if out.returncode or not lines:
        raise RuntimeError((out.stderr.strip().splitlines() or ["DWSIM worker failed"])[-1])
    return json.loads(lines[-1])


def run(spec, scale=1.0):
    return _call({"op": "run", "spec": spec, "scale": scale})


def capacity(spec):
    return _call({"op": "capacity", "spec": spec})


def bubble(compounds, x, T_C, package="Peng-Robinson (PR)"):
    return _call({"op": "bubble", "spec": {"compounds": compounds, "x": x, "package": package}, "T_C": list(T_C)})


DEMO = {
    "compounds": ["Water", "Ethanol"], "package": "NRTL",
    "feeds": {"FEED": {"T_C": 25, "P_bar": 1.2, "kg_h": 18000, "x": {"Water": 0.9, "Ethanol": 0.1}},
              "HOT_IN": {"T_C": 90, "P_bar": 3, "kg_h": 21600, "x": {"Water": 1}}},
    "units": [{"id": "P-101", "type": "pump", "in": "FEED", "out": "S1", "dP_bar": 4, "eff_pct": 70},
              {"id": "E-101", "type": "hx", "cold": ["S1", "S2"], "hot": ["HOT_IN", "HOT_OUT"], "U_W_m2K": 1500, "area_m2": 10},
              {"id": "V-101", "type": "valve", "in": "S2", "out": "S3", "dP_bar": 2},
              {"id": "T-101", "type": "tank", "in": "S3", "out": "PROD", "volume_m3": 10}],
    "limits": {"E-101": {"area_m2": 10, "out_T_C": 52, "side": "cold"}, "P-101": {"max_m3_h": 30, "max_kW": 4},
               "T-101": {"min_residence_min": 25}},
}

if __name__ == "__main__":
    if "--worker" in sys.argv:
        print(json.dumps(_worker(json.loads(sys.stdin.read()))))
    else:
        r = run(DEMO)
        assert not r["errors"], r["errors"]
        print(r["units"], r["checks"][:3], sep="\n")
        c = capacity(DEMO)
        print("capacity", c["capacity_multiple"], c["limited_by"])
        assert 1.0 < c["capacity_multiple"] < 2.0
        b = bubble(["Propylene", "Propane"], {"Propylene": 0.9, "Propane": 0.1}, [20, 60, 90])
        print(b["points"])
        assert b["points"][2]["bubble_P_bar"] > b["points"][0]["bubble_P_bar"] > 5
        print("ok")
