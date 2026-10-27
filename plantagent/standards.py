"""Design-standard checks with citations: Ten States Standards (Water Works 2022, Wastewater Facilities 2014) and an
HI-derived operating-region rule. Rules: plantagent/data/standards.json (section and page for each)."""
import json
import re
from pathlib import Path

RULES = {r["id"]: r for r in json.loads((Path(__file__).parent / "data" / "standards.json").read_text())}


def list_rules(standard=None):
    return [{k: r[k] for k in ("id", "standard", "section", "rule", "quantity", "op", "value", "unit")}
            for r in RULES.values() if standard in (None, r["standard"], "all")]


def _ok(op, v, lim):
    if op == "between":
        return lim[0] <= v <= lim[1]
    if op == "required":
        return bool(v) == bool(lim)
    return {">=": v >= lim, "<=": v <= lim, ">": v > lim, "<": v < lim, "==": v == lim}[op]


# Which kind of evidence each quantity needs: a firm-capacity ratio from a gravity profile is not evidence.
NEEDS = [(re.compile(r"firm_capacity|pump|N-1|npsh|suction", re.I), "pumps"), (re.compile(r"freeboard|weir_loading|water_depth", re.I), "profile")]


def check(items, runs=None):
    """items: [{rule_id, value | numerator+denominator, basis (run label or page)}] -> pass/fail with citation.
    runs: {label: run} lets the check refuse a basis of the wrong kind (e.g. a pump rule backed by a gravity profile)."""
    out = []
    for it in items:
        r = RULES[it["rule_id"]]
        need = next((k for rx, k in NEEDS if rx.search(r["quantity"])), None)
        run = (runs or {}).get(str(it.get("basis", "")).split()[0]) if runs else None
        if need and run is not None:
            kind = "pumps" if run.get("spec", {}).get("pumps") else "profile" if "elements" in run.get("spec", {}) else "other"
            if kind != need:
                out.append({"rule_id": r["id"], "status": "not checked", "rule": r["rule"],
                            "reason": f"basis {it.get('basis')} is a {kind} run; this rule needs a {need} run",
                            "citation": f"{r['edition']}, Sec. {r['section']}"}); continue
        v = it.get("value")
        if v is None and it.get("denominator"):
            v = float(it["numerator"]) / float(it["denominator"])
        if v is None:
            out.append({"rule_id": r["id"], "status": "not checked", "reason": it.get("basis", "no value")}); continue
        v = v if isinstance(v, bool) else float(v)
        out.append({"rule_id": r["id"], "status": "pass" if _ok(r["op"], v, r["value"]) else "FAIL",
                    "value": round(v, 4) if not isinstance(v, bool) else v, "limit": f"{r['op']} {r['value']} {r['unit']}",
                    "rule": r["rule"], "citation": f"{r['edition']}, Sec. {r['section']} ({r['source_page']})",
                    "basis": it.get("basis", "")})
    return out


if __name__ == "__main__":
    r = check([{"rule_id": "S-FM-01", "value": 1.5, "basis": "t"}, {"rule_id": "S-FM-02", "value": 6.3},
               {"rule_id": "HI-POR-01", "numerator": 1714, "denominator": 1600}])
    assert [x["status"] for x in r] == ["FAIL", "pass", "pass"], r
    print("ok", len(RULES), "rules")
