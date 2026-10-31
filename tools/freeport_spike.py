"""Freeport LNG 2022 spike: trapped LNG in a blocked-in 18-inch segment, isochoric heating with DWSIM PR thermo.
python tools/freeport_spike.py  ->  fill fraction vs heat leak per metre that reaches 1,313 psig in the documented 4.78 days."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plantagent import process  # noqa: E402

SPEC = {"compounds": ["Methane", "Ethane", "Propane", "Nitrogen"],
        "x": {"Methane": 0.95, "Ethane": 0.035, "Propane": 0.01, "Nitrogen": 0.005}}
P0 = (37 + 14.696) / 14.5038          # bar abs at isolation (PHMSA NOPV)
PF = (1313 + 14.696) / 14.5038        # bar abs at rupture (PHMSA NOPV)
DAYS = 4 + (18 * 60 + 44) / 1440      # Jun 3 16:44 -> Jun 8 11:28 (PHMSA NOPV)
ID = 0.4572 - 2 * 0.00478             # NPS 18 Sch 10S inner pipe (ILLUSTRATIVE)
A = math.pi * ID ** 2 / 4
WALL_KG_M = math.pi * (0.4572 - 0.00478) * 0.00478 * 7900  # inner pipe steel per metre (ILLUSTRATIVE wall)


def props(pts):
    return process._call({"op": "props", "spec": SPEC, "points": pts})["points"]


def u(p):  # internal energy, kJ/kg
    return p["enthalpy_kJ_kg"] - p["P_bar"] * 100 / p["density_kg_m3"]


PGRID = [1.0 * 300 ** (i / 99) for i in range(100)]  # 1 to 300 bar, brackets the vapour side too


def state(T, rho):
    """Pressure (bar) and u (kJ/kg) where the PT-flash overall density equals the trapped density."""
    pts = props([{"T_C": T, "P_bar": p} for p in PGRID])
    for a, b in zip(pts, pts[1:]):
        if a["density_kg_m3"] <= rho <= b["density_kg_m3"]:
            w = (rho - a["density_kg_m3"]) / (b["density_kg_m3"] - a["density_kg_m3"])
            return a["P_bar"] + w * (b["P_bar"] - a["P_bar"]), u(a) + w * (u(b) - u(a))
    return None, None


T0 = next(T / 2 for T in range(-300, -260)
          if process._call({"op": "bubble", "spec": SPEC, "T_C": [T / 2]})["points"][0]["bubble_P_bar"] >= P0)
liq, vap = props([{"T_C": T0, "P_bar": P0 + 0.3}, {"T_C": T0 + 3, "P_bar": P0}])
print(f"T0 {T0} C at {P0:.2f} bar; rho_liq {liq['density_kg_m3']}, rho_vap {vap['density_kg_m3']}; "
      f"A {A:.4f} m2; target {PF:.1f} bar in {DAYS:.2f} d")
rows = []
for f in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
    rho = f * liq["density_kg_m3"] + (1 - f) * vap["density_kg_m3"]
    u0 = (f * liq["density_kg_m3"] * u(liq) + (1 - f) * vap["density_kg_m3"] * u(vap)) / rho
    curve, Tc = [], T0
    while Tc < 40:
        P, uu = state(Tc, rho)
        if P is None:
            break
        curve.append((Tc, round(P, 2), round(uu - u0, 2)))
        if P > PF * 1.05:
            break
        Tc += 4
    i = next((i for i, c in enumerate(curve) if c[1] >= PF), None)
    if i:
        (Ta, Pa, da), (Tb, Pb, db) = curve[i - 1], curve[i]
        w = (PF - Pa) / (Pb - Pa)
        dU = da + w * (db - da)
        Tr = Ta + w * (Tb - Ta)
        wall = WALL_KG_M * 0.35 * (Tr - T0)  # kJ/m: the stainless inner pipe warms with the LNG (cp ~0.35 kJ/kgK, cryogenic)
        q = (rho * A * dU + wall) * 1000 / (DAYS * 86400)
        rows.append({"fill": f, "rho": round(rho, 1), "T_at_rupture_C": round(Tr, 1), "dU_kJ_kg": round(dU, 1),
                     "heat_leak_W_per_m": round(q, 2), "curve": curve})
    else:
        rows.append({"fill": f, "rho": round(rho, 1), "max_P_bar": curve[-1][1] if curve else None, "curve": curve})
    print(json.dumps({k: v for k, v in rows[-1].items() if k != "curve"}))
Path("/tmp/freeport").mkdir(exist_ok=True)
Path("/tmp/freeport/spike.json").write_text(json.dumps({"T0": T0, "rows": rows}, indent=1))
