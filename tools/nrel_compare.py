"""Score a rebuilt NREL area model against the report's withheld stream tables (cases/nrel_ethanol/outcome.json).

python tools/nrel_compare.py nrel_ethanol_a500 [model.json]
Compares every output stream the model names S<number>: total flow, ethanol, water and the non-volatile solids (kg/h,
relative error) and temperature (K difference), skipping report values below 1 % of the stream. Counts checks within
3 % / 5 % (3 K / 5 K). Writes runs/ws/<area>/comparison.json. No LLM."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.make_nrel_case import MAP  # noqa: E402

# report heat stream -> (model unit id, result field)
DUTIES = {"QRD501": ("D-501", "reboiler_kW"), "QCD501": ("D-501", "condenser_kW"), "QRD502": ("D-502", "reboiler_kW"),
          "QCD502": ("D-502", "condenser_kW"), "QH512": ("H-512", "duty_kW"), "QH503": ("H-503", "duty_kW"), "QH509": ("H-509", "duty_kW")}
SOLIDS = {MAP[k] for k in MAP if k.endswith(("(SS)", "(IS)")) or k in ("Sulfuric Acid", "Other Organics")}


def compare(area, model_file=None):
    oc = json.loads((ROOT / "cases" / "nrel_ethanol" / "outcome.json").read_text())
    model_file = Path(model_file or ROOT / "runs" / "ws" / area / "model.json")
    built = json.loads(model_file.read_text())
    revs = model_file.with_name("revisions.json")
    result = built.get("result") or {}
    if revs.exists() and json.loads(revs.read_text()):
        result = json.loads(revs.read_text())[-1].get("result_after") or result
    streams = result.get("streams") or {}
    area_code = json.loads((ROOT / "cases" / area / "case.json").read_text())["area"]
    rows, checks = [], []
    for num, ref in oc["stream_tables"].items():
        if ref["area"] != area_code or ref["role"] != "output":
            continue
        got = streams.get("S" + num)
        if not got or got.get("error"):
            rows.append({"stream": num, "what": ref["what"], "status": "not in model"})
            continue
        comp = got.get("components_kg_h") or {}
        ref_kg = ref["standin_kg_h"]
        items = [("total kg/h", ref["Total Flow"], got.get("kg_h")),
                 ("ethanol kg/h", ref_kg.get("Ethanol", 0), comp.get("Ethanol", 0)),
                 ("water kg/h", ref_kg.get("Water", 0), comp.get("Water", 0)),
                 ("solids kg/h", sum(v for c, v in ref_kg.items() if c in SOLIDS), sum(v or 0 for c, v in comp.items() if c in SOLIDS))]
        row = {"stream": num, "what": ref["what"], "checks": []}
        for name, r, g in items:
            if not r or r < 0.01 * ref["Total Flow"] or g is None:
                continue
            err = (g - r) / r
            c = {"check": name, "report": round(r, 1), "model": round(g, 1), "error_pct": round(100 * err, 1),
                 "within_3": abs(err) <= 0.03, "within_5": abs(err) <= 0.05}
            row["checks"].append(c)
            checks.append(c)
        if got.get("T_C") is not None:
            d = got["T_C"] - ref["Temperature"]
            c = {"check": "temperature C", "report": ref["Temperature"], "model": round(got["T_C"], 1), "error_K": round(d, 1),
                 "within_3": abs(d) <= 3, "within_5": abs(d) <= 5}
            row["checks"].append(c)
            checks.append(c)
        rows.append(row)
    duties = []
    units = result.get("units") or {}
    for key, (uid, field) in DUTIES.items():
        if key not in oc["energy"] or uid not in units:
            continue
        r = abs(oc["energy"][key]["Gcal_h"]) * 1163.0  # Gcal/h -> kW
        g = units[uid].get(field)
        if g is None and field == "duty_kW":
            g = units[uid].get("duty_kW")
        if g is None:
            continue
        err = (abs(g) - r) / r
        duties.append({"duty": key, "what": oc["energy"][key]["what"], "unit": uid, "report_kW": round(r), "model_kW": round(abs(g)),
                       "error_pct": round(100 * err, 1), "within_5": abs(err) <= 0.05, "within_10": abs(err) <= 0.10})
    summary = {"area": area_code, "streams_compared": sum(1 for r in rows if r.get("checks")),
               "duties_compared": len(duties), "duties_within_10": sum(d["within_10"] for d in duties),
               "streams_missing": [r["stream"] for r in rows if r.get("status")],
               "checks": len(checks), "within_3": sum(c["within_3"] for c in checks), "within_5": sum(c["within_5"] for c in checks)}
    out = {"summary": summary, "streams": rows, "duties": duties,
           "note": "Report values are NREL's Aspen Plus model (Humbird et al. 2011, Appendix E), mapped to the DWSIM stand-in compounds."}
    dest = ROOT / "runs" / "ws" / area / "comparison.json"
    dest.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    o = compare(*sys.argv[1:3])
    print(json.dumps(o["summary"]))
    for r in o["streams"]:
        print(r["stream"], r.get("status") or "  ".join(f'{c["check"]}: {c["model"]} vs {c["report"]}' for c in r["checks"]))
    for d in o["duties"]:
        print(d["duty"], d["unit"], d["model_kW"], "vs", d["report_kW"], f'{d["error_pct"]} %')
