"""Order-of-magnitude capital cost from published cost curves, escalated with ENR CCI, with AACE accuracy ranges.

Curves and their sources: plantagent/data/cost_curves.json (TWDB 2024, City of Phoenix 2024, US EPA WBS, EPA-600/2-79-162b).
"""
import json
import re
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "data" / "cost_curves.json").read_text())
CURVES = {c["id"]: c for c in DATA["items"]}
TARGET = "2023-09"  # latest ENR value confirmed from a document (TWDB 2024 guide); 2025 value is unverified


def catalogue():
    return [{"id": c["id"], "item": c["item"], "x": f"{c['x_name']} [{c['x_unit']}]", "valid_range": c["valid_range"],
             "basis": f"{c['base_year']} $", "per_foot": c["form"].startswith("cost_per_ft"), "notes": c["notes"][:160]}
            for c in DATA["items"]]


def _curve(c, x):
    a, b, form = c["a"], c["b"], c["form"]
    if "x^2" in form:
        cc = float(re.search(r"c = (-?[\d.eE-]+)", form).group(1))
        return a + b * x + cc * x * x
    if "x^b" in form:
        return a * x ** b
    return a + b * x


def estimate(lines, aace_class=5, target=TARGET):
    """lines: [{id, x, qty=1 (count, or length in ft for per-foot curves), note}]."""
    enr_t = DATA["enr"][target]
    rows, total = [], 0.0
    for ln in lines:
        c = CURVES[ln["id"]]
        x, qty = float(ln["x"]), float(ln.get("qty", 1))
        lo, hi = c["valid_range"]
        unit = _curve(c, x)
        esc = enr_t / c["enr_base"] if c.get("enr_base") else 1.0
        cost = unit * qty * esc
        total += cost
        rows.append({"id": c["id"], "item": c["item"], "x": x, "x_unit": c["x_unit"], "qty": qty,
                     "unit_cost_base": round(unit), "base_year": c["base_year"], "escalation": round(esc, 3),
                     "cost": round(cost, -3), "note": ln.get("note", ""),
                     "warnings": ([f"x outside curve range {lo}-{hi}"] if not lo <= x <= hi else []) +
                                 ([f"not escalated: source in {c['base_year']} $ indexed by PPI"] if not c.get("enr_base") else []),
                     "source": f"{c['source']}, {c['page']}"})
    k = DATA["aace"]["classes"][str(aace_class)]
    low, high = sum(k["low"]) / 2, sum(k["high"]) / 2  # middle of the AACE range for the class
    return {"lines": rows, "total": round(total, -3), "dollars": f"{target} (ENR CCI {enr_t})", "aace_class": aace_class,
            "range": [round(total * (1 + low), -3), round(total * (1 + high), -3)],
            "range_basis": f"AACE 18R-97 class {aace_class}: {k['low']} to {k['high']}; midpoint bounds used",
            "note": "Order-of-magnitude capital cost from published curves; excludes land, engineering and contingency unless the curve includes them."}


if __name__ == "__main__":
    r = estimate([{"id": "C-PS-04", "x": 7.2}, {"id": "C-PIPE-03", "x": 18, "qty": 5000}])
    print(json.dumps(r, indent=1)[:1500])
    assert r["range"][0] < r["total"] < r["range"][1] and r["lines"][1]["cost"] > 0
    assert estimate([{"id": "C-SED-01", "x": 5000}])["lines"][0]["escalation"] > 4  # 1978 $ escalated
    print("ok")
