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


GAL = 7.48052  # gallons per cubic foot
TREATMENT_HELP = ("units: [{type: flocculation | sedimentation | filters, name, count, and dimensions in ft: length, width, "
                  "depth (basins); weir_length_ft (sedimentation, total outlet weir/launder length); area_sf_each (filters); "
                  "max_rate_gpm_sf (filters: the approved rate, default 4 per Ten States 4.3.1.2)}]")


def treatment_capacity(units):
    """Rated capacity of treatment units from their dimensions against Ten States Standards (Water 2022): the plant flow
    (mgd) at which each criterion binds. Deterministic; every limit cites its section."""
    out = []
    for u in units:
        n, t = int(u.get("count") or 1), u["type"].lower()
        L, W, D = (float(u.get(k) or 0) for k in ("length", "width", "depth"))
        lim = []
        if t.startswith("floc"):
            v = L * W * D * n * GAL
            lim.append(("W-FL-01", "detention >= 30 min", v / 30 * 1440 / 1e6))
        elif t.startswith("sed"):
            v = L * W * D * n * GAL
            lim.append(("W-SED-01", "detention >= 4 h", v * 24 / 4 / 1e6))
            if W and D:
                lim.append(("W-SED-02", "horizontal velocity <= 0.5 ft/min", 0.5 * W * D * n * 1440 * GAL / 1e6))
            if u.get("weir_length_ft"):
                lim.append(("W-SED-03", "weir loading <= 20,000 gpd/ft", 20000 * float(u["weir_length_ft"]) / 1e6))
        elif t.startswith("filt"):
            a, rate = float(u["area_sf_each"]), float(u.get("max_rate_gpm_sf") or 4)
            lim.append(("W-FIL-01", f"filtration rate <= {rate:g} gpm/sf, all {n} filters", rate * a * n * 1440 / 1e6))
            if n > 2:
                lim.append(("W-FIL-02", f"filtration rate <= {rate:g} gpm/sf with the largest filter out ({n - 1} filters)",
                            rate * a * (n - 1) * 1440 / 1e6))
        rows = [{"rule_id": r, "criterion": c, "capacity_mgd": round(q, 2),
                 "citation": f"{RULES[r]['edition']}, Sec. {RULES[r]['section']}"} for r, c, q in lim]
        out.append({"unit": u.get("name") or u["type"], "type": t, "limits": rows,
                    "capacity_mgd": min((x["capacity_mgd"] for x in rows), default=None),
                    "governing": min(rows, key=lambda x: x["capacity_mgd"])["criterion"] if rows else None})
    return out


if __name__ == "__main__":
    tc = treatment_capacity([{"type": "filters", "count": 4, "area_sf_each": 522}, {"type": "flocculation", "count": 2, "length": 50,
                                                                                         "width": 20, "depth": 12}])
    assert tc[0]["capacity_mgd"] == round(4 * 522 * 3 * 1440 / 1e6, 2) and tc[0]["governing"].endswith("(3 filters)"), tc
    print(tc)
    r = check([{"rule_id": "S-FM-01", "value": 1.5, "basis": "t"}, {"rule_id": "S-FM-02", "value": 6.3},
               {"rule_id": "HI-POR-01", "numerator": 1714, "denominator": 1600}])
    assert [x["status"] for x in r] == ["FAIL", "pass", "pass"], r
    print("ok", len(RULES), "rules")
