"""NaCl brine thermodynamics for evaporator and crystalliser studies: vapour pressure, solubility, BPE and liquid cp.
BPE: Sparrow (2003), Desalination 159:161-170, valid 0-150 C and up to saturation. Liquid cp: WaterTAP
cryst_prop_pack.py, Laliberte (2009) eqs. 10-12 and Sharqawy et al. (2010) eq. 9; local source at
case-data/raw/nacl_mvr/data_watertap/cryst_prop_pack.py.txt. DWSIM's NRTL without electrolyte parameters gives about
a third of the real BPE, so the BPE is applied explicitly.
"""
import math

# p [MPa] = A + B t + C t^2 + D t^3 + E t^4, each of A..E = k1 + k2 x + k3 x^2 + k4 x^3 + k5 x^4 (x = NaCl mass fraction, t in C)
_K = {"A": (0.9083e-3, -0.569e-3, 0.1945e-3, -3.736e-3, 2.82e-3),
      "B": (-0.0669e-3, 0.0582e-3, -0.1668e-3, 0.6761e-3, -2.091e-3),
      "C": (7.541e-6, -5.143e-6, 6.482e-6, -52.62e-6, 115.7e-6),
      "D": (-0.0922e-6, 0.0649e-6, -0.1313e-6, 0.8024e-6, -1.986e-6),
      "E": (1.237e-9, -0.753e-9, 0.1448e-9, -6.964e-9, 14.61e-9)}


def p_solution_bar(t, x):
    """Vapour pressure (bar) of an NaCl solution of mass fraction x at t C."""
    co = {k: sum(c * x ** i for i, c in enumerate(v)) for k, v in _K.items()}
    return 10 * (co["A"] + co["B"] * t + co["C"] * t ** 2 + co["D"] * t ** 3 + co["E"] * t ** 4)


def x_sat(t):
    """NaCl solubility (mass fraction) at t C."""
    return 0.2628 + 62.75e-6 * t + 1.084e-6 * t ** 2


def cp(t, x):
    """Liquid NaCl brine heat capacity, kJ/(kg K), from WaterTAP's Laliberte (2009) mixture correlation."""
    if not (0 <= x <= 0.32 and 0 <= t <= 150):
        raise ValueError("brine cp requires 0-150 C and 0-0.32 NaCl mass fraction")
    tk = t + 273.15
    t68 = (tk - 0.00025 * 273.15) / (1 - 0.00025)
    cp_water = 5.328 - 0.006913 * t68 + 9.6e-6 * t68 ** 2 + 2.5e-9 * t68 ** 3
    cp_nacl = -0.06936 * math.exp(-0.07821 * t - 11.2762 * x + 3.848 * math.exp(0.01 * t)) + 8.7319 * x ** 1.8125
    return (1 - x) * cp_water + x * cp_nacl


def boiling_t(p_bar, x):
    """Temperature at which the solution boils at p_bar (bisection on the vapour pressure)."""
    if not isinstance(p_bar, (int, float)) or not math.isfinite(float(p_bar)) or p_bar <= 0:
        raise ValueError("brine boiling point requires a positive finite pressure")
    if not isinstance(x, (int, float)) or not math.isfinite(float(x)) or not 0 <= x <= 0.32:
        raise ValueError("brine boiling point requires 0-0.32 NaCl mass fraction")
    lo, hi = 0.0, 150.0
    if not p_solution_bar(lo, x) <= p_bar <= p_solution_bar(hi, x):
        raise ValueError("brine boiling point is outside the Sparrow correlation range of 0-150 C")
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if p_solution_bar(mid, x) < p_bar else (lo, mid)
    return (lo + hi) / 2


def bpe(p_bar, x=None):
    """Boiling point elevation (K) at p_bar for mass fraction x (saturated brine when x is None)."""
    t_water = boiling_t(p_bar, 0.0)
    if x is not None and (not isinstance(x, (int, float)) or not math.isfinite(float(x)) or not 0 <= x <= 0.32):
        raise ValueError("brine BPE requires 0-0.32 NaCl mass fraction")
    if x is None:  # saturated: iterate because solubility depends on temperature
        t = t_water
        for _ in range(20):
            t = boiling_t(p_bar, min(x_sat(t), 0.32))
        x = x_sat(t)
    t = boiling_t(p_bar, x)
    return {"p_bar": p_bar, "x_NaCl": round(x, 4), "t_water_C": round(t_water, 2), "t_brine_C": round(t, 2), "bpe_K": round(t - t_water, 2),
            "note": "Sparrow 2003 NaCl-water vapour pressure; vapour leaves the brine superheated by the BPE, and the condensing side "
                    "must be hotter than the brine by the BPE plus the heater temperature difference."}


if __name__ == "__main__":
    # Sparrow-derived saturated BPE at 100 C is about 8.2 K; at 50 C about 5.8 K (numbers.md table)
    r100 = bpe(p_solution_bar(100.0, x_sat(100.0)))
    assert abs(r100["t_brine_C"] - 100.0) < 0.1 and 7.9 < r100["bpe_K"] < 8.6, r100
    r10 = bpe(1.0, 0.10)
    assert 1.6 < r10["bpe_K"] < 2.2, r10
    assert 4.1 < cp(100, 0) < 4.3 and 3.2 < cp(100, 0.26) < 3.4
    assert cp(100, 0.26) < cp(100, 0.20) < cp(100, 0)
    print(r100, bpe(1.70), sep="\n")
    print("ok")
