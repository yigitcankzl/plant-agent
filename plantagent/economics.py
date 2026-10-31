"""Economics of a design answer: an order-of-magnitude factored capex per verified proposal, the added margin per year from
the solved throughput gain and energy, simple payback and NPV. Deterministic, no model call.

Equipment factors: FACTORS below (one table, every entry ILLUSTRATIVE with a source note). Product, energy, utility prices,
operating days, outage, discount rate and life: cases/<case>/economics.json. Cached next to the model (economics.json),
keyed by the content of the design, the model, the case prices and this module's factor table.
CLI: python -m plantagent.economics <case>
"""
import copy
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTING = {"mixer", "splitter", "recycle"}
_SRC = ("ILLUSTRATIVE order-of-magnitude factor of the kind tabulated in Towler & Sinnott, Chemical Engineering Design "
        "(2nd ed., 2012), ch. 7; not a vendor quote")
FACTORS = {  # bare equipment cost per unit of size, then one installation factor; replace with quotes
    "compressor": {"usd_per": 900, "per": "kW", "size": "driver rating (limits.max_kW), else solved shaft power", "source": _SRC},
    "pump": {"usd_per": 600, "per": "kW", "size": "motor rating (limits.max_kW), else solved shaft power", "source": _SRC},
    "hx": {"usd_per": 450, "per": "m2", "size": "installed area", "source": _SRC},
    "tank": {"usd_per": 1500, "per": "m3", "size": "volume", "source": _SRC},
    "install_factor": {"value": 2.5, "source": "ILLUSTRATIVE Lang-type installed/bare factor for added fluid-processing "
                                               "equipment (piping, instruments, electrical, civil, erection)"},
    "tie_in": {"usd": 120000, "source": "ILLUSTRATIVE allowance per new tee/join tied into a live line (hot tap or shutdown tie-in)"},
    "cleaning": {"usd": 80000, "source": "ILLUSTRATIVE chemical/mechanical clean of one large exchanger incl. waste handling"},
    "setpoint": {"usd": 15000, "source": "ILLUSTRATIVE instrument, DCS and procedure change for a flow, level or set-point change"},
}
AACE5 = (-0.5, 1.0)  # AACE 18R-97 class 5 widest band (see plantagent/data/cost_curves.json)
CLASS_USD = {"no capex": (0, 25000), "<$100k": (0, 100000), "$100k-$1M": (100000, 1000000), ">$1M": (1000000, float("inf"))}


def _get(spec, path):
    kind, oid, field = path.split(".", 2)
    if kind == "units":
        return next((u.get(field) for u in spec.get("units") or [] if u.get("id") == oid), None)
    return ((spec.get(kind) or {}).get(oid) or {}).get(field)


def _short(v):
    return [_short(x) for x in v] if isinstance(v, list) else round(v, 3) if isinstance(v, float) else v


def _change_lines(change, design_units, spec, tag=lambda x: x):
    """Capex lines for one model change; tag maps a model unit id back to its P&ID tag (case model_aliases)."""
    f, inst = FACTORS, FACTORS["install_factor"]["value"]
    u = change.get("add_unit")
    if u:
        t = u.get("type")
        if t in ROUTING:
            return [{"item": f"tie-in {u['id']}", "basis": "new tee/join", "usd": f["tie_in"]["usd"], "source": f["tie_in"]["source"]}]
        if t not in FACTORS:
            return [{"item": f"{u['id']} ({t})", "basis": "no factor for this equipment type", "usd": None, "source": "to price"}]
        fac, lim = FACTORS[t], change.get("limits") or {}
        solved = (design_units.get(u["id"]) or {})
        size = {"kW": lim.get("max_kW") or solved.get("kW"), "m2": u.get("area_m2") or lim.get("area_m2"),
                "m3": u.get("volume_m3")}[fac["per"]]
        if not size:
            return [{"item": u["id"], "basis": f"no {fac['per']} size to price", "usd": None, "source": "to price"}]
        return [{"item": f"{u['id']} {t}", "basis": f"{size:,.0f} {fac['per']} × ${fac['usd_per']:,}/{fac['per']} × install {inst}",
                 "size": size, "size_unit": fac["per"], "usd": round(size * fac["usd_per"] * inst, -3), "source": fac["source"]}]
    if change.get("reroute"):
        return []  # the tee or join it connects to carries the tie-in
    path = str(change.get("path") or "")
    if path.endswith(".U_W_m2K") and float(change.get("value") or 0) > float(change.get("from") or _get(spec, path) or 0):
        return [{"item": f"clean {tag(path.split('.')[1])}", "basis": "restore clean U", "usd": f["cleaning"]["usd"], "source": f["cleaning"]["source"]}]
    if path:
        return [{"item": f"set-point {path}", "basis": f"{_short(change.get('from', _get(spec, path)))} → {_short(change.get('value'))}",
                 "usd": f["setpoint"]["usd"], "source": f["setpoint"]["source"]}]
    return []


def _kw(result, units):
    return sum(float((result.get("units") or {}).get(u, {}).get("kW") or 0) for u in units)


def _flow(spec, sid, field, scale):
    f = (spec.get("feeds") or {}).get(sid) or {}
    v = f.get(field)
    return None if v is None else float(v) * (1.0 if f.get("utility") else scale)


def key(w, ans):
    from .prefeed import gates_key
    cfg = ROOT / "cases" / w.name / "economics.json"
    blob = json.dumps({"design": gates_key(w, ans)["content"], "prices": cfg.read_text() if cfg.exists() else None,
                       "factors": FACTORS, "combined": (ans or {}).get("combined")}, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()


def assess(w, answer=None, refresh=False):
    """Economics of the design answer (or answers[answer]); cached in economics.json next to the model."""
    from . import revb
    from .plant import patch
    cfg_path = ROOT / "cases" / w.name / "economics.json"
    if not cfg_path.exists():
        return {"error": f"no economics.json for {w.name}"}
    ans = (w.answers[int(answer)] if answer is not None and -len(w.answers) <= int(answer) < len(w.answers)
           else revb.design_answer(w.answers))
    props = [p for p in (ans or {}).get("proposals") or [] if p.get("verified")]
    if not props:
        return {"error": "no verified design answer to price"}
    k = key(w, ans)
    cache = w.model_file.with_name("economics.json")
    if not refresh and cache.exists():
        old = json.loads(cache.read_text())
        if old.get("key") == k:
            return old
    cfg = json.loads(cfg_path.read_text())
    target = float(w.cfg.get("target_scale") or 1.0)
    changes = [c for p in props for c in p.get("changes") or []]
    spec_d = patch(copy.deepcopy(w.spec), changes)
    design, existing = w._solve(spec_d, target), w._solve(w.spec, 1.0)
    du = design.get("units") or {}

    back = {v: k for k, v in (w.cfg.get("model_aliases") or {}).items()}
    rows, total = [], 0.0
    for p in props:
        lines = [ln for c in p.get("changes") or [] for ln in _change_lines(c, du, w.spec, lambda x: back.get(x, x))]
        usd = sum(ln["usd"] or 0 for ln in lines)
        lo, hi = CLASS_USD.get(p.get("cost_class"), (None, None))
        rows.append({"title": p.get("title"), "cost_class": p.get("cost_class"), "capex_usd": usd, "lines": lines,
                     "unpriced": [ln["item"] for ln in lines if ln["usd"] is None],
                     "cost_class_check": None if lo is None else ("consistent" if lo <= usd <= hi else
                                                                 f"factored ${usd:,.0f} is outside the stated class {p.get('cost_class')}")})
        total += usd

    tp = {**(w.cfg.get("throughput") or {}), **(cfg.get("throughput") or {})}
    cap = (ans.get("combined") or {}).get("capacity_multiple")
    sold = min(cap, target) if cap else target
    days = float(cfg["operating_days"]["value"])
    price, var = cfg["product"]["price"], cfg["product"].get("variable_cost") or {"value": 0}
    unit_margin = float(price["value"]) - float(var["value"])
    gain_day = float(tp["base"]) * max(0.0, sold - 1.0)
    revenue = gain_day * days * float(price["value"])
    product_margin = gain_day * days * unit_margin

    energy = []
    for d in cfg.get("drivers") or []:  # who pays for shaft power: electric motor, gas turbine fuel, steam ...
        dkw = _kw(design, d["units"]) - _kw(existing, d["units"])
        energy.append({"name": d["name"], "units": d["units"], "delta_kW": round(dkw, 1), "price": d["price"],
                       "usd_per_year": round(dkw * 24 * days * float(d["price"]["value"]), -2)})
    utilities = []
    for u in cfg.get("utilities") or []:
        before, after = _flow(w.spec, u["stream"], u["field"], 1.0), _flow(spec_d, u["stream"], u["field"], target)
        if before is None or after is None:
            continue
        utilities.append({"name": u["name"], "stream": u["stream"], "delta": round(after - before, 3), "unit": u["field"].replace("_", "/"),
                          "price": u["price"], "usd_per_year": round((after - before) * 24 * days * float(u["price"]["value"]), -2)})
    margin = product_margin - sum(e["usd_per_year"] for e in energy) - sum(u["usd_per_year"] for u in utilities)
    physical = any(c.get("add_unit") or c.get("reroute") for c in changes)
    out_cfg = cfg.get("outage") or {}
    outage_days = float(out_cfg.get("days", 0)) if physical or any(str(c.get("path", "")).endswith(".U_W_m2K") for c in changes) else 0.0
    outage = float(tp["base"]) * outage_days * unit_margin
    rate, years = float(cfg["discount_rate"]["value"]), int(cfg["years"]["value"])
    annuity = sum(1 / (1 + rate) ** t for t in range(1, years + 1))

    def npv(capex):
        return round(-(capex + outage) + margin * annuity, -3)
    payback = (total + outage) / margin if margin > 0 else None
    band = [round(total * (1 + AACE5[0]), -3), round(total * (1 + AACE5[1]), -3)]
    cur = cfg.get("currency", "USD")
    def money(v):
        return f"${v / 1e6:.1f}M" if abs(v) >= 1e6 else f"${v / 1e3:.0f}k"
    pb = ("none" if payback is None else f"{payback * 52:.0f} weeks" if payback < 0.25 else
          f"{payback * 12:.0f} months" if payback < 2 else f"{payback:.1f} years")
    summary = (f"Capex ≈ {money(total)} (class 5: {money(band[0])}–{money(band[1])}); +{gain_day:,.0f} {tp.get('unit', '')} "
               f"→ {money(margin)}/yr margin after energy and utilities; payback {pb}; NPV {years} y @ {rate:.0%} "
               f"{money(npv(total))}. All prices ILLUSTRATIVE.")
    out = {"key": k, "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "case": w.name, "answer_headline": ans.get("headline"),
           "currency": cur, "illustrative": True, "summary": summary,
           "capex": {"total_usd": round(total, -3), "range_usd": band, "range_basis": "AACE 18R-97 class 5, -50 % / +100 %",
                     "proposals": rows},
           "annual": {"throughput_name": tp.get("name"), "unit": tp.get("unit"), "base": tp["base"], "sold_multiple": round(sold, 4),
                      "gain_per_day": round(gain_day, 1), "operating_days": days, "revenue_usd": round(revenue, -2),
                      "product_margin_usd": round(product_margin, -2), "energy": energy, "utilities": utilities,
                      "margin_usd": round(margin, -2), "basis": f"solved {ans.get('combined', {}).get('capacity_multiple') or target:.3f} × base, "
                                                              f"capped at the {target:.0%} target; energy from {('DWSIM' if not w.cfg.get('engine') else w.cfg['engine'])} "
                                                              f"solves (design at {target:.0%} vs today at 100 %)"},
           "outage": {"days": outage_days, "usd": round(outage, -3), "source": out_cfg.get("source")},
           "payback_years": None if payback is None else round(payback, 2),
           "npv_usd": npv(total), "npv_range_usd": [npv(band[1]), npv(band[0])], "discount_rate": rate, "years": years,
           "prices": {"product": price, "variable_cost": var, "operating_days": cfg["operating_days"],
                      "discount_rate": cfg["discount_rate"], "years": cfg["years"], "factors": FACTORS}}
    cache.write_text(json.dumps(out, indent=1))
    return out


def cached(w, ans):
    """The cached economics for this answer, or None if missing or stale (no solve)."""
    f = w.model_file.with_name("economics.json")
    if not (ans and f.exists() and (ROOT / "cases" / w.name / "economics.json").exists()):
        return None
    e = json.loads(f.read_text())
    return e if e.get("key") == key(w, ans) else None


def for_prefeed(e):
    """The pre-FEED constructability input (prefeed.constructability economics) from an assessment."""
    if not e or e.get("error"):
        return None
    lo, hi = e["capex"]["range_usd"]
    per_day = e["annual"]["base"] * (float(e["prices"]["product"]["value"]) - float(e["prices"]["variable_cost"]["value"]))
    return {"capex_low": lo, "capex_high": hi, "outage_days": e["outage"]["days"], "production_value_per_day": per_day,
            "currency": e["currency"], "source": "plantagent.economics factored estimate (ILLUSTRATIVE prices, cases/<case>/economics.json)"}


def markdown(e):
    if not e or e.get("error"):
        return []
    a = e["annual"]
    md = ["", "### Economics (ILLUSTRATIVE prices; order of magnitude)", "", f"- {e['summary']}", "",
          "| Proposal | Stated class | Factored capex | Check |", "|---|---|---|---|"]
    md += [f"| {p['title']} | {p['cost_class'] or ''} | ${p['capex_usd']:,.0f} | {p['cost_class_check'] or ''} |" for p in e["capex"]["proposals"]]
    md += ["", f"- Added {a['throughput_name'] or 'throughput'}: {a['gain_per_day']:,.0f} {a['unit'] or ''} × {a['operating_days']:.0f} d; "
               f"product margin ${a['product_margin_usd']:,.0f}/yr ({a['basis']})."]
    md += [f"- {x['name']}: {x['delta_kW']:+,.0f} kW → ${x['usd_per_year']:,.0f}/yr at {x['price']['value']} {x['price']['unit']} ({x['price']['source']})."
           for x in a["energy"]]
    md += [f"- {x['name']}: {x['delta']:+,.2f} {x['unit']} → ${x['usd_per_year']:,.0f}/yr ({x['price']['source']})." for x in a["utilities"]]
    md += [f"- Outage for tie-ins/cleaning: {e['outage']['days']:g} d → ${e['outage']['usd']:,.0f} ({e['outage']['source'] or 'to confirm'}).",
           f"- Payback {e['payback_years']} years; NPV ${e['npv_usd']:,.0f} (capex band: ${e['npv_range_usd'][0]:,.0f} to ${e['npv_range_usd'][1]:,.0f})."]
    return md


if __name__ == "__main__":
    import sys
    from .plant import PlantWorkspace
    r = assess(PlantWorkspace(sys.argv[1]), refresh="--refresh" in sys.argv)
    print(json.dumps({k: v for k, v in r.items() if k != "prices"}, indent=1)[:4000])
