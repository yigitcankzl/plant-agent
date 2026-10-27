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


SCOPE = {"C-PS": "complete pump station", "C-PMP": "pump equipment", "C-VFD": "drive", "C-PIPE": "pipeline", "C-FM": "force main",
         "C-TANK": "pressure vessel", "C-FIL": "filter", "C-FLOC": "flocculation basin", "C-SED": "clarifier", "C-WTP": "treatment plant",
         "C-GST": "ground storage"}
UNIT_WORDS = {"filter": "C-FIL", "basin": "C-SED|C-FLOC|C-WTP", "clarifier": "C-SED", "floc": "C-FLOC", "sediment": "C-SED",
              "surge": "C-TANK", "tank": "C-TANK|C-GST", "clearwell": "C-GST", "pipe": "C-PIPE|C-FM", "main": "C-PIPE|C-FM", "vfd": "C-VFD"}


def estimate(lines, aace_class=5, target=TARGET, label=""):
    """lines: [{id, x, qty=1 (count, or length in ft for per-foot curves), note}]. A line whose curve does not fit the
    item it prices (e.g. a filter priced with a pump-station curve) is rejected, not summed."""
    enr_t = DATA["enr"][target]
    rows, total = [], 0.0
    for ln in lines:
        c = CURVES[ln["id"]]
        x, qty = float(ln["x"]), float(ln.get("qty", 1))
        what = (str(ln.get("note", "")) + " " + label).lower()
        want = next((v for k, v in UNIT_WORDS.items() if k in what), None)
        prefix = ln["id"].rsplit("-", 1)[0]
        if want and not re.match(want, prefix) and prefix in ("C-PS", "C-PIPE", "C-PMP"):
            rows.append({"id": c["id"], "item": c["item"], "x": x, "qty": qty, "cost": 0, "rejected": True,
                         "warnings": [f"rejected: a {SCOPE.get(prefix, prefix)} curve cannot price '{what.strip()[:60]}'"],
                         "source": f"{c['source']}, {c['page']}"})
            continue
        lo, hi = c["valid_range"]
        unit = _curve(c, x)
        esc = enr_t / c["enr_base"] if c.get("enr_base") else 1.0
        cost = unit * qty * esc
        total += cost
        rows.append({"id": c["id"], "item": c["item"], "x": x, "x_unit": c["x_unit"], "qty": qty,
                     "unit_cost_base": round(unit), "base_year": c["base_year"], "escalation": round(esc, 3),
                     "cost": round(cost, -3), "note": ln.get("note", ""),
                     "warnings": ([f"x outside curve range {lo}-{hi}"] if not lo <= x <= hi else []) +
                                 (["fixed term is most of this cost: the curve prices a complete facility, not added equipment"]
                                  if "a + b*x" in c["form"] and not c["form"].startswith("cost_per_ft") and c["a"] > 0.5 * unit else []) +
                                 ([f"not escalated: source in {c['base_year']} $ indexed by PPI"] if not c.get("enr_base") else []) +
                                 ([f"low confidence: {c['base_year']} cost basis escalated x{esc:.1f} by ENR"] if esc > 2 else []),
                     "source": f"{c['source']}, {c['page']}"})
    k = DATA["aace"]["classes"][str(aace_class)]
    low, high = min(k["low"]), max(k["high"])  # the full AACE band, not its midpoint
    return {"lines": rows, "total": round(total, -3), "dollars": f"{target} (ENR CCI {enr_t})", "aace_class": aace_class,
            "range": [round(total * (1 + low), -3), round(total * (1 + high), -3)],
            "range_basis": f"AACE 18R-97 class {aace_class}: low {k['low'][0]:.0%} to {k['low'][1]:.0%}, high +{k['high'][0]:.0%} to +{k['high'][1]:.0%}; widest band shown",
            "note": "Order-of-magnitude capital cost from published curves at a national-average location (no location factor); "
                    "excludes land, engineering (typically 15-25%) and contingency (typically 25-40% at Class 5) unless the curve includes them."}


if __name__ == "__main__":
    r = estimate([{"id": "C-PS-04", "x": 7.2}, {"id": "C-PIPE-03", "x": 18, "qty": 5000}])
    print(json.dumps(r, indent=1)[:1500])
    assert r["range"][0] < r["total"] < r["range"][1] and r["lines"][1]["cost"] > 0
    assert estimate([{"id": "C-SED-01", "x": 5000}])["lines"][0]["escalation"] > 4  # 1978 $ escalated
    print("ok")
