"""Blind benchmark on real factories: US DOE Industrial Assessment Center (IAC/ITAC) audits.

The agent sees only the plant profile the auditors had before the site visit (industry, products, hours, size, and a
year of utility use and cost). The auditors' recommendations are hidden. The agent proposes up to 10 measures, each
with an ARC code from the DOE catalogue and an annual savings estimate. Scoring is deterministic:
  - recall: share of the auditors' recommendations the agent named (exact ARC code, and ARC family = first 5 chars),
  - savings-weighted recall: share of the auditors' identified $ savings covered by the measures the agent named,
  - precision at 10, and the savings estimate error on matched measures,
against an honest baseline: the 10 measures most often recommended at other plants of the same 2-digit SIC group.

Usage: python -m plantagent.iac --n 20 [--model muse-spark-1.3-contributor]
"""
import argparse
import csv
import json
import math
import random
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import llm
from .docs import DATA

ROOT = Path(__file__).resolve().parent.parent
SRC = DATA / "raw/factory/iac"
OUT = ROOT / "runs" / "iac"
STREAMS = {"EC": ("electricity", "kWh"), "ED": ("electric demand", "kW-months"), "EF": ("other electric fees", ""),
           "E2": ("natural gas", "MMBtu"), "E3": ("LPG", "MMBtu"), "E4": ("#1 fuel oil", "MMBtu"), "E5": ("#2 fuel oil", "MMBtu"),
           "E6": ("#4 fuel oil", "MMBtu"), "E7": ("#6 fuel oil", "MMBtu"), "E8": ("coal", "MMBtu"), "E9": ("wood", "MMBtu"),
           "E10": ("paper", "MMBtu"), "E11": ("other gas", "MMBtu"), "E12": ("other energy", "MMBtu"),
           "W0": ("water", "thousand gal"), "W1": ("water disposal", "thousand gal"), "W2": ("other liquid (non-haz)", "thousand gal"),
           "W3": ("other liquid (haz)", "thousand gal"), "W4": ("solid waste (non-haz)", "lb"), "W5": ("solid waste (haz)", "lb"),
           "W6": ("gaseous waste", "lb")}
GROUPS = {"20": "food", "22": "textiles", "24": "wood products", "26": "paper", "27": "printing", "28": "chemicals and pharma",
          "29": "petroleum", "30": "rubber and plastics", "32": "stone, clay, glass", "33": "primary metals",
          "34": "fabricated metals", "35": "machinery", "36": "electronics", "37": "transportation equipment"}

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["measures"], "properties": {"measures": {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
                               "required": ["arc", "measure", "annual_savings_usd", "implementation_cost_usd", "basis"],
                               "properties": {"arc": {"type": "string"}, "measure": {"type": "string"},
                                              "annual_savings_usd": {"type": "number"}, "implementation_cost_usd": {"type": "number"},
                                              "basis": {"type": "string"}}}}}}


def _f(v):
    try:
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def _arc(v):
    x = _f(v)
    return f"{x:.4f}" if x is not None else None


def load():
    plants = {r["ID"]: r for r in csv.DictReader(open(SRC / "extracted/ASSESS.csv"))}
    recs = defaultdict(list)
    for r in csv.DictReader(open(SRC / "extracted/RECC.csv")):
        if _arc(r["ARC2"]):
            saved = sum(_f(r[k]) or 0 for k in ("PSAVED", "SSAVED", "TSAVED", "QSAVED"))
            recs[r["ID"]].append({"arc": _arc(r["ARC2"]), "saved": saved, "cost": _f(r["IMPCOST"]), "status": r["IMPSTATUS"]})
    arcs = {row["ARC"]: row["description"] for row in csv.DictReader(open(SRC / "arc_codes.csv"))}
    return plants, recs, arcs


def profile(p):
    """What the auditors knew before the visit: no recommendations."""
    use = []
    for code, (name, unit) in STREAMS.items():
        cost, amount = _f(p.get(f"{code}_plant_cost")), _f(p.get(f"{code}_plant_usage"))
        if cost or amount:
            use.append({"stream": name, "annual_use": f"{amount:,.0f} {unit}" if amount else None, "annual_cost_usd": round(cost) if cost else None})
    g = lambda k: p.get(k) if p.get(k) not in ("", "nan", None) else None  # noqa: E731
    return {"industry_sic": g("SIC"), "industry_naics": g("NAICS"), "industry_group": GROUPS.get(str(g("SIC") or "")[:2], "other"),
            "products": g("PRODUCTS"), "state": g("STATE"), "fiscal_year": g("FY"), "annual_sales_usd": _f(p.get("SALES")),
            "employees": _f(p.get("EMPLOYEES")), "plant_area_sqft": _f(p.get("PLANT_AREA")),
            "production": f"{g('PRODLEVEL')} {g('PRODUNITS')}" if g("PRODLEVEL") else None,
            "operating_hours_per_year": _f(p.get("PRODHOURS")), "utilities": use}


def sample(plants, recs, n, seed=7):
    """n plants, FY2016+, 6+ recommendations with savings, spread over industry groups (deterministic)."""
    rng = random.Random(seed)
    pool = defaultdict(list)
    for i, p in plants.items():
        fy, rs = _f(p["FY"]) or 0, recs.get(i, [])
        if fy >= 2016 and len(rs) >= 6 and sum(r["saved"] for r in rs) > 0 and str(p["SIC"])[:2] in GROUPS and p.get("PRODUCTS"):
            pool[str(p["SIC"])[:2]].append(i)
    out, groups = [], sorted(pool)
    while len(out) < n:
        for gname in groups:
            if pool[gname] and len(out) < n:
                out.append(pool[gname].pop(rng.randrange(len(pool[gname]))))
    return out


def baseline(plants, recs, test_ids, sic2, k=10, share=False):
    """The k ARC codes most often recommended at other audited plants (FY2010+) of the same 2-digit SIC group."""
    c, n = Counter(), 0
    for i, p in plants.items():
        if i not in test_ids and str(p["SIC"])[:2] == sic2 and (_f(p["FY"]) or 0) >= 2010:
            c.update({r["arc"] for r in recs.get(i, [])})
            n += 1
    return [(a, m / n) for a, m in c.most_common(k)] if share else [a for a, _ in c.most_common(k)]


def score(pred_arcs, truth):
    fam = lambda a: a[:5]  # noqa: E731 - e.g. 2.4231 and 2.4236 are both compressed-air pressure/leak family 2.423
    tot = sum(r["saved"] for r in truth) or 1
    exact = [r for r in truth if r["arc"] in pred_arcs]
    family = [r for r in truth if fam(r["arc"]) in {fam(a) for a in pred_arcs}]
    return {"recall_exact": len(exact) / len(truth), "recall_family": len(family) / len(truth),
            "savings_recall_family": sum(r["saved"] for r in family) / tot,
            "precision_family": len({fam(a) for a in pred_arcs} & {fam(r["arc"]) for r in truth}) / max(1, len({fam(a) for a in pred_arcs})),
            "implemented_found": sum(1 for r in family if r["status"] == "I"), "implemented_total": sum(1 for r in truth if r["status"] == "I")}


def ask(model, prof, arcs, prior=None):
    cat = "\n".join(f"{k} {v}" for k, v in arcs.items())
    pri = ("\n\nIndustry statistics (other audited plants of this industry group, this plant excluded): the measures most often "
           "recommended, with the share of plants that got them. Use them as a prior, then choose for THIS plant's processes and "
           "utility mix:\n" + "\n".join(f"{a} {arcs.get(a, '')}: {f:.0%}" for a, f in prior)) if prior else ""
    msg = [{"role": "system", "content": "You are a senior industrial energy engineer preparing a one-day plant energy assessment "
                                         "(US DOE Industrial Assessment Center method). From the plant profile and utility data only, "
                                         "name the 10 measures you expect to recommend after the walk-through, most valuable first. "
                                         "Use the ARC code from the catalogue for each. Estimate annual savings from the utility data "
                                         "(state the share of which stream you assume) and implementation cost. Be specific to this "
                                         "industry and its processes, not generic."},
           {"role": "user", "content": "ARC catalogue:\n" + cat + pri + "\n\nPlant profile:\n" + json.dumps(prof, indent=1)}]
    m = llm.complete(model, msg, response_format={"type": "json_schema", "json_schema": {"name": "audit", "schema": SCHEMA, "strict": True}})
    try:
        return json.loads(m["content"])["measures"][:10]
    except json.JSONDecodeError:  # long reasoning outputs sometimes break the JSON late: keep every measure object that parses
        import re
        out = []
        for chunk in re.findall(r'\{[^{}]*"arc"[^{}]*\}', m["content"]):
            try:
                out.append(json.loads(chunk))
            except json.JSONDecodeError:
                pass
        if out:
            return out[:10]
        # strict-schema decoding can degenerate (e.g. a run of whitespace): ask again without the schema
        m = llm.complete(model, msg + [{"role": "user", "content": "Return only a JSON object {\"measures\": [...]} with the "
                                        "fields arc, measure, annual_savings_usd, implementation_cost_usd, basis. No other text."}],
                         response_format={"type": "json_object"})
        txt = m["content"]
        return json.loads(txt[txt.index("{"):txt.rindex("}") + 1])["measures"][:10]


def run(n, model, prior=False):
    plants, recs, arcs = load()
    ids = sample(plants, recs, n)
    llm.set_tag("iac")
    usd0, t0 = llm.spent(), time.time()

    def one(i):
        prof = profile(plants[i])
        truth = recs[i]
        try:
            ms = ask(model, prof, arcs, baseline(plants, recs, set(ids), str(plants[i]["SIC"])[:2], 25, True) if prior else None)
        except Exception as e:  # noqa: BLE001 - a failed plant counts as zero, it is not dropped
            ms = []
            print(i, "failed:", e)
        pred = [str(m["arc"]).strip()[:6] for m in ms]
        base = baseline(plants, recs, set(ids), str(plants[i]["SIC"])[:2])
        sav = {r["arc"][:5]: r["saved"] for r in truth}
        errs = [abs(math.log(m["annual_savings_usd"] / sav[str(m["arc"])[:5]])) for m in ms
                if str(m["arc"])[:5] in sav and m["annual_savings_usd"] > 0 and sav[str(m["arc"])[:5]] > 0]
        return {"id": i, "group": prof["industry_group"], "products": prof["products"], "profile": prof,
                "engineers": [{**r, "desc": arcs.get(r["arc"], "")} for r in truth], "agent": ms,
                "agent_score": score(pred, truth), "baseline": base, "baseline_score": score(base, truth),
                "savings_log_errors": errs}

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(llm.inherit_tag(one), ids))
    keys = ["recall_exact", "recall_family", "savings_recall_family", "precision_family"]
    summary = {"model": model, "industry_prior": prior, "plants": len(rows), "seconds": round(time.time() - t0), "cost_usd": round(llm.spent() - usd0, 4),
               "agent": {k: round(statistics.mean(r["agent_score"][k] for r in rows), 3) for k in keys},
               "baseline": {k: round(statistics.mean(r["baseline_score"][k] for r in rows), 3) for k in keys},
               "agent_beats_baseline_on_plants": sum(r["agent_score"]["savings_recall_family"] > r["baseline_score"]["savings_recall_family"] for r in rows),
               "median_savings_error_factor": round(math.exp(statistics.median(e for r in rows for e in r["savings_log_errors"])), 2)
               if any(r["savings_log_errors"] for r in rows) else None,
               "implemented_found": f"{sum(r['agent_score']['implemented_found'] for r in rows)} of {sum(r['agent_score']['implemented_total'] for r in rows)}"}
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{time.strftime('%Y%m%d-%H%M%S')}-{model.replace(':', '_').replace('/', '_')}{'-prior' if prior else ''}.json"
    f.write_text(json.dumps({"summary": summary, "plants": rows}, indent=1))
    print(json.dumps(summary, indent=1), "\n", f)
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--model", default="muse-spark-1.3-contributor")
    ap.add_argument("--prior", action="store_true", help="give the agent the industry statistics (other plants) as a prior")
    a = ap.parse_args()
    t = [{"arc": "2.4231", "saved": 100, "status": "I"}, {"arc": "2.7142", "saved": 300, "status": "N"}]
    s = score(["2.4236", "2.2511"], t)
    assert s["recall_exact"] == 0 and s["recall_family"] == 0.5 and s["savings_recall_family"] == 0.25 and s["implemented_found"] == 1
    run(a.n, a.model, a.prior)
