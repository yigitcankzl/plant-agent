"""Deterministic pre-FEED gate for a proposed process design.

Reuses the workspace simulator, verified proposal records, P&ID relief graph and
artifact store.  It does not invent vendor curves, dynamic constants or prices:
missing design inputs remain explicit actions for the engineer.

Usage: python -m plantagent.prefeed salt_mvr
"""
import copy
import json
import math
import time
from pathlib import Path

from . import artifacts, pid
from .docs import DATA
from .proposed import datasheet_markdown, present_calculation

ROOT = Path(__file__).resolve().parent.parent
ROUTING = {"mixer", "splitter", "recycle"}


def _added_equipment(changes):
    return [{"id": c["add_unit"]["id"], "type": c["add_unit"].get("type"),
             "limits": c.get("limits") or {}, "rating_source": c.get("rating_source")}
            for c in changes or [] if isinstance(c.get("add_unit"), dict)
            and c["add_unit"].get("type") not in ROUTING]


def _ports(unit):
    ins = ([unit["in"]] if isinstance(unit.get("in"), str) else list(unit.get("in") or []))
    outs = ([unit["out"]] if isinstance(unit.get("out"), str) else list(unit.get("out") or []))
    for side in ("hot", "cold"):
        if unit.get(side):
            ins.append(unit[side][0]); outs.append(unit[side][1])
    for name in ("vapor", "liquid", "distillate", "bottoms"):
        if unit.get(name):
            outs.append(unit[name])
    return ins, outs


def _balance(spec, result):
    produced, consumed = set(), set()
    for unit in spec.get("units") or []:
        ins, outs = _ports(unit)
        consumed.update(ins); produced.update(outs)
    feeds = [s for s in (spec.get("feeds") or {}) if s not in produced]
    products = sorted(produced - consumed)
    streams = result.get("streams") or {}
    missing = [s for s in feeds + products if (streams.get(s) or {}).get("kg_h") is None]
    if missing:
        return {"status": "not available", "reason": "boundary mass flow missing", "streams": missing}
    mass_in = sum(streams[s]["kg_h"] for s in feeds)
    mass_out = sum(streams[s]["kg_h"] for s in products)
    error = abs(mass_in - mass_out) / mass_in * 100 if mass_in else None
    components = sorted({c for s in feeds + products for c in (streams.get(s, {}).get("components_kg_h") or {})})
    component_errors = {}
    for component in components:
        ci = sum((streams[s].get("components_kg_h") or {}).get(component, 0) for s in feeds)
        co = sum((streams[s].get("components_kg_h") or {}).get(component, 0) for s in products)
        component_errors[component] = round(abs(ci - co) / ci * 100, 3) if ci else None
    enthalpy = all((streams.get(s) or {}).get("enthalpy_kJ_kg") is not None for s in feeds + products)
    return {"status": "ok" if error is not None and error <= 1 else "warn", "feeds": feeds, "products": products,
            "mass_in_kg_h": round(mass_in, 3), "mass_out_kg_h": round(mass_out, 3),
            "mass_error_pct": round(error, 3) if error is not None else None,
            "component_error_pct": component_errors,
            "energy": ("available" if enthalpy else "not available: boundary streams do not carry enthalpy_kJ_kg")}


def run_envelope(spec, scenarios, solve, patch):
    """Run a bounded scenario matrix; a robust pass requires every scenario to solve and stay within every stated limit."""
    if not scenarios or len(scenarios) > 24:
        raise ValueError("prefeed needs 1 to 24 operating-envelope scenarios")
    names, rows = set(), []
    for raw in scenarios:
        name = str(raw.get("name") or "").strip()
        scale = float(raw.get("scale") or 1.0)
        if not name or name in names:
            raise ValueError("scenario names must be present and unique")
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError(f"scenario {name}: scale must be positive and finite")
        names.add(name)
        changes = raw.get("changes") or []
        if any(c.get("add_unit") or c.get("reroute") or str(c.get("path") or "").startswith("limits.") for c in changes):
            raise ValueError(f"scenario {name}: vary operating inputs, not topology or documented limits")
        scenario_spec = patch(copy.deepcopy(spec), changes)
        try:
            result = solve(scenario_spec, scale)
        except Exception as error:  # a failed solve is a failed scenario, never a robust pass
            result = {"errors": [f"{type(error).__name__}: {error}"], "checks": [], "streams": {}}
        checks = [c for c in result.get("checks") or [] if isinstance(c.get("utilisation"), (int, float))]
        worst = max(checks, key=lambda c: c["utilisation"], default=None)
        over = [c for c in checks if c["utilisation"] > 1]
        errors = list(result.get("errors") or [])
        if not checks and not errors:
            errors.append("no stated engineering limit checks in this scenario")
        balance = _balance(scenario_spec, result) if result.get("streams") else {
            "status": "not available", "reason": "scenario did not solve", "energy": "not available"}
        rows.append({"name": name, "scale": scale, "basis": raw.get("basis") or "engineer-defined scenario",
                     "pass": not errors and not over, "worst": worst, "over": over, "errors": errors,
                     "checks": [c for c in checks if c["utilisation"] >= .8],
                     "balance": balance})
    governing = max(rows, key=lambda r: (r["worst"] or {}).get("utilisation", 0))
    return {"robust_pass": all(r["pass"] for r in rows), "scenarios": rows,
            "governing": {"scenario": governing["name"], **(governing["worst"] or {})}}


def dynamic_screen(items):
    """First-order-plus-dead-time loop screen using measured/approved constants supplied by the engineer."""
    if not items:
        return {"status": "not run", "reason": "no measured dynamic model",
                "needed": ["equipment liquid/vapour holdup", "controller action and tuning",
                           "valve/drive response", "step-test time constant and dead time", "trip and permissive logic"]}
    if len(items) > 20:
        raise ValueError("at most 20 critical dynamic loops")
    rows = []
    for item in items:
        required = ("name", "variable", "initial", "final", "time_constant_s", "duration_s", "source")
        missing = [k for k in required if item.get(k) in (None, "")]
        if missing:
            raise ValueError(f"dynamic screen missing {', '.join(missing)}")
        y0, yf, tau, dead, duration = (float(item["initial"]), float(item["final"]),
                                      float(item["time_constant_s"]), float(item.get("dead_time_s") or 0),
                                      float(item["duration_s"]))
        if not all(math.isfinite(x) for x in (y0, yf, tau, dead, duration)):
            raise ValueError(f"dynamic screen {item['name']}: values must be finite")
        values = [y0 if t <= dead else yf + (y0 - yf) * math.exp(-(t - dead) / tau)
                  for t in [duration * i / 40 for i in range(41)]] if tau > 0 and duration > 0 and dead >= 0 else []
        if not values:
            raise ValueError(f"dynamic screen {item['name']}: time constant and duration must be positive; dead time non-negative")
        low, high = item.get("low_limit"), item.get("high_limit")
        if any(v is not None and not math.isfinite(float(v)) for v in (low, high)):
            raise ValueError(f"dynamic screen {item['name']}: limits must be finite")
        passed = (low is None or min(values) >= float(low)) and (high is None or max(values) <= float(high))
        rows.append({"name": item["name"], "variable": item["variable"], "unit": item.get("unit") or "",
                     "initial": y0, "final": yf, "minimum": round(min(values), 5), "maximum": round(max(values), 5),
                     "low_limit": low, "high_limit": high, "settling_time_s": round(dead + 4 * tau, 1),
                     "pass": passed, "source": item["source"],
                     "method": "first-order-plus-dead-time screening; not a rigorous plant dynamic simulation"})
    return {"status": "pass" if all(r["pass"] for r in rows) else "fail", "loops": rows}


def equipment_screen(changes, calculations):
    """Screen the provisional ratings already on verified proposals; never substitutes a made-up vendor curve."""
    presented = [present_calculation(c) or {} for c in calculations if isinstance(c, dict)]
    calc_rows = {r.get("id"): r for c in presented for r in c.get("new_equipment") or []}
    rows = []
    for equipment in _added_equipment(changes):
        row = calc_rows.get(equipment["id"]) or {}
        flow, rating_flow = row.get("flow"), row.get("rating_flow")
        shaft, rating_shaft = row.get("shaft"), row.get("rating_shaft")
        flow_margin = rating_flow / flow if flow and rating_flow else None
        power_margin = rating_shaft / shaft if shaft and rating_shaft else None
        margins = [x for x in (flow_margin, power_margin) if x is not None]
        status = "fail" if any(x < 1 for x in margins) else "provisional pass" if margins else "incomplete"
        rows.append({"id": equipment["id"], "type": equipment["type"], "status": status,
                     "operating_flow": flow, "flow_unit": row.get("flow_unit"), "rating_flow": rating_flow,
                     "flow_margin": round(flow_margin, 3) if flow_margin else None,
                     "calculated_shaft": shaft, "shaft_unit": row.get("shaft_unit"), "rating_shaft": rating_shaft,
                     "power_margin": round(power_margin, 3) if power_margin else None,
                     "rating_source": row.get("rating_source") or equipment.get("rating_source") or "to confirm",
                     "vendor_gate": ["guaranteed curve over min/normal/max flow", "efficiency and driver rating",
                                     "surge/choke or BEP/minimum-flow margin", "materials and seals",
                                     "noise/vibration", "nozzle loads and mechanical design"]})
    return rows


def hazard_screen(spec, changes, relief):
    """Small deterministic HAZOP register for changed equipment. It is a prompt for a team HAZOP, not one by itself."""
    units = {u["id"]: u for u in spec.get("units") or []}
    changed = []
    for change in changes:
        if change.get("add_unit") and change["add_unit"].get("type") not in ROUTING:
            changed.append((change["add_unit"]["id"], change["add_unit"].get("type"), True))
        elif change.get("reroute"):
            uid = change["reroute"]["unit"]; changed.append((uid, (units.get(uid) or {}).get("type"), False))
        elif str(change.get("path") or "").startswith("units."):
            uid = change["path"].split(".")[1]; changed.append((uid, (units.get(uid) or {}).get("type"), False))
    patterns = {
        "compressor": [("No flow / trip", "trip, isolation or surge", "loss of production; recycle heating", "confirm anti-surge, trip and restart logic"),
                       ("High pressure", "blocked discharge or control failure", "overpressure upstream/downstream", "size relief/depressuring case; check discharge system")],
        "pump": [("No flow", "trip or low suction", "loss of circulation; heating or cavitation", "confirm low-flow trip, standby start and minimum-flow path"),
                 ("High pressure", "deadhead", "line or seal overpressure", "check shutoff head against line/relief rating")],
        "hx": [("No utility", "utility trip or fouling", "process outlet off specification", "alarm on approach/outlet; define response"),
               ("Tube rupture", "pressure boundary failure", "cross-contamination and low-side overpressure", "compare design pressures and size credible relief case")],
        "evaporator": [("High pressure", "vapour outlet blocked", "vessel overpressure", "verify relief load and discharge destination"),
                       ("High level", "outlet restriction/control failure", "carryover to compressor", "confirm independent high-high trip")],
        "valve": [("More flow", "fail open", "downstream overload or overpressure", "solve fail-open flow and relief case"),
                  ("No flow", "fail closed", "loss of duty or blocked-in liquid", "check trip and thermal relief")],
    }
    rows = []
    for uid, typ, new in dict.fromkeys(changed):
        for deviation, cause, consequence, action in patterns.get(typ, [("No flow", "isolation or failure", "loss of process function", "confirm alarms, trips and operating response")]):
            existing = [x for x in relief if x.get("tag") == uid]
            safeguard = "new equipment: relief and isolation to confirm" if new else "; ".join(x["status"] for x in existing) or "not shown on relief scan"
            rows.append({"tag": uid, "type": typ, "deviation": deviation, "cause": cause, "consequence": consequence,
                         "existing_safeguard": safeguard, "action": action, "status": "open"})
    return {"method": "automated change-focused HAZOP/relief screening; team HAZOP and API/ISO sizing remain required",
            "rows": rows, "relief_findings": [x for x in relief if x.get("status") != "protected"]}


def constructability(changes, equipment, cost_classes, economics=None):
    physical = [c for c in changes if c.get("add_unit") and c["add_unit"].get("type") not in ROUTING]
    reroutes = [c for c in changes if c.get("reroute")]
    cleaning = [c for c in changes if str(c.get("path") or "").endswith(".U_W_m2K")]
    checks = []
    if physical:
        checks += ["Plot space, access and lifting study", "Foundation and nozzle-load design", "Electrical load, starter and cable study",
                   "Vendor lead time and spares", "Materials/corrosion review"]
    if physical or reroutes:
        checks += ["Tie-in list, isolation plan and shutdown window", "Line sizing, supports, stress and hydrotest", "Control narrative and cause/effect update"]
    if cleaning:
        checks += ["Cleaning method, waste handling, inspection and post-clean performance test"]
    e = economics or {}
    numeric = all(e.get(k) is not None for k in ("capex_low", "capex_high", "outage_days", "production_value_per_day"))
    values = ({k: float(e[k]) for k in ("capex_low", "capex_high", "outage_days", "production_value_per_day")}
              if numeric else {})
    if numeric and not str(e.get("source") or "").strip():
        raise ValueError("quantified economics needs a source")
    if numeric and (not all(math.isfinite(v) and v >= 0 for v in values.values()) or values["capex_low"] > values["capex_high"]):
        raise ValueError("economics must be finite, non-negative and capex_low must not exceed capex_high")
    quantified = ({"capex_low": values["capex_low"], "capex_high": values["capex_high"],
                   "outage_loss": values["outage_days"] * values["production_value_per_day"],
                   "first_year_low": values["capex_low"] + values["outage_days"] * values["production_value_per_day"],
                   "first_year_high": values["capex_high"] + values["outage_days"] * values["production_value_per_day"],
                   "currency": e.get("currency") or "USD", "source": e.get("source") or "to confirm"} if numeric else None)
    return {"physical_units": [c["add_unit"]["id"] for c in physical], "reroutes": len(reroutes),
            "tie_ins": "to confirm on the Rev B line list" if physical or reroutes else 0,
            "outage_required": bool(physical or reroutes or cleaning), "cost_classes": cost_classes,
            "quantified": quantified, "checks": list(dict.fromkeys(checks)),
            "unpriced": [] if quantified else ["installed equipment", "piping/tie-ins", "electrical and controls", "civil/structural", "outage production loss"]}


def _fmt(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


def markdown(data, datasheets=""):
    env = data["envelope"]
    lines = ["# Pre-FEED design gate", "", "**DRAFT — simulator screening, not approved for construction.**", "",
             f"**Verdict:** {'ROBUST PASS' if env['robust_pass'] else 'NOT ROBUST'} across {len(env['scenarios'])} stated operating scenarios.", "",
             "## Operating envelope", "", "| Scenario | Load | Result | Governing check | Utilisation | Mass closure | Basis |",
             "|---|---:|---|---|---:|---:|---|"]
    for row in env["scenarios"]:
        worst, bal = row.get("worst") or {}, row["balance"]
        lines.append(f"| {row['name']} | {row['scale'] * 100:.0f}% | {'PASS' if row['pass'] else 'FAIL'} | "
                     f"{worst.get('id', '—')} {worst.get('check', '')} | {_fmt(worst.get('utilisation'))} | "
                     f"{_fmt(bal.get('mass_error_pct'))}% | {row['basis']} |")
    lines += ["", "Energy closure: " + "; ".join(sorted({r["balance"].get("energy", "not available") for r in env["scenarios"]})), "",
              "## Preliminary equipment selection", ""]
    if data["equipment"]:
        lines += ["| Tag | Type | Status | Flow margin | Driver margin | Rating source |", "|---|---|---|---:|---:|---|"]
        for row in data["equipment"]:
            lines.append(f"| {row['id']} | {row['type']} | {row['status']} | {_fmt(row['flow_margin'])} | {_fmt(row['power_margin'])} | {row['rating_source']} |")
        lines += ["", "Vendor gate still open: guaranteed curve; efficiency/driver; surge/choke or BEP/minimum flow; materials; vibration/noise; mechanical design.", ""]
    else:
        lines += ["No new physical equipment in the selected design.", ""]
    if datasheets:
        lines += [datasheets, ""]
    dyn = data["dynamics"]
    lines += ["## Critical-loop dynamics", ""]
    if dyn.get("loops"):
        lines += ["| Loop | Variable | Result | Min | Max | Limits | 2% settling screen | Source |", "|---|---|---|---:|---:|---|---:|---|"]
        for row in dyn["loops"]:
            lines.append(f"| {row['name']} | {row['variable']} | {'PASS' if row['pass'] else 'FAIL'} | {row['minimum']} | {row['maximum']} | "
                         f"{_fmt(row['low_limit'])} … {_fmt(row['high_limit'])} {row['unit']} | {row['settling_time_s']} s | {row['source']} |")
        lines += ["", "Method: first-order-plus-dead-time screening. A rigorous dynamic simulation still needs equipment holdup and control/drive models.", ""]
    else:
        lines += [f"Not run: {dyn['reason']}.", "", "Needed: " + "; ".join(dyn["needed"]) + ".", ""]
    haz = data["hazards"]
    lines += ["## Change-focused HAZOP and relief screen", "", "| Tag | Deviation | Cause | Consequence | Existing safeguard | Action |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {r['tag']} | {r['deviation']} | {r['cause']} | {r['consequence']} | {r['existing_safeguard']} | {r['action']} |" for r in haz["rows"]]
    con = data["constructability"]
    lines += ["", "## Cost and constructability gate", "", f"Cost classes on the proposals: {', '.join(con['cost_classes']) or 'not stated'}.",
              f"Outage required: {'yes' if con['outage_required'] else 'no identified outage work'}. Exact tie-ins: {con['tie_ins']}.", ""]
    if con["quantified"]:
        q = con["quantified"]
        lines += [f"First-year installed plus outage screen: {q['currency']} {q['first_year_low']:,.0f}–{q['first_year_high']:,.0f} ({q['source']}).", ""]
    else:
        lines += ["No sourced numerical estimate supplied; these items remain unpriced: " + "; ".join(con["unpriced"]) + ".", ""]
    lines += [f"- {x}" for x in con["checks"]]
    lines += ["", "## Gate and limitations", "", "- A pass means all stated simulator checks passed in all stated scenarios; it is not mechanical or vendor approval.",
              "- New equipment remains provisional until guaranteed curves and materials are checked.",
              "- The automated hazard register does not replace a multidisciplinary HAZOP or relief-system design.",
              "- Missing inputs stay open; PlantAgent does not invent curves, dynamic constants or costs.", ""]
    return "\n".join(lines)


def make(w, answer=None, scenarios=None, dynamics=None, economics=None):
    """Build and save the deterministic pre-FEED gate for the selected verified design (or current model)."""
    if not w.built:
        raise ValueError("no model built yet")
    from . import revb
    from .plant import patch
    selected = (w.answers[int(answer)] if answer is not None and str(answer).lstrip("-").isdigit()
                and -len(w.answers) <= int(answer) < len(w.answers) else revb.design_answer(w.answers))
    proposals = [p for p in (selected or {}).get("proposals") or [] if p.get("verified")]
    cfg_path = ROOT / "cases" / w.name / "prefeed.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    if not proposals and cfg.get("design"):
        selected = {"headline": cfg["design"].get("title")}
        proposals = cfg["design"].get("proposals") or []
    changes = [c for p in proposals for c in p.get("changes") or []]
    spec = patch(copy.deepcopy(w.spec), changes)
    scenarios = scenarios or cfg.get("scenarios") or [
        {"name": "today", "scale": 1.0, "basis": "current throughput"},
        {"name": "target", "scale": float(w.cfg.get("target_scale") or 1.0), "basis": "case target"}]
    dynamics = dynamics if dynamics is not None else cfg.get("dynamics")
    economics = economics or cfg.get("economics")
    envelope = run_envelope(spec, scenarios, w._solve, patch)
    calculations = [p.get("calculation") for p in proposals if p.get("calculation")]
    if changes and not calculations:
        target = float(w.cfg.get("target_scale") or 1.0)
        solved = w._solve(spec, target)
        records = []
        for change in changes:
            unit = change.get("add_unit")
            if not unit or unit.get("type") in ROUTING:
                continue
            op = copy.deepcopy((solved.get("units") or {}).get(unit["id"]) or {})
            inlet = unit.get("in") if isinstance(unit.get("in"), str) else None
            outlet = unit.get("out") if isinstance(unit.get("out"), str) else None
            if inlet and (solved.get("streams") or {}).get(inlet, {}).get("kg_h") is not None:
                op["kg_h"] = solved["streams"][inlet]["kg_h"]
            if unit.get("eff_pct") is not None:
                op.setdefault("eff_pct", unit["eff_pct"])
            pin = (solved.get("streams") or {}).get(inlet or "", {}).get("P_bar")
            pout = (solved.get("streams") or {}).get(outlet or "", {}).get("P_bar")
            if pin and pout:
                op.setdefault("pressure_ratio", pout / pin)
            records.append({"id": unit["id"], "type": unit.get("type"), "operating_point": op,
                            "limits": change.get("limits") or {}, "rating_source": change.get("rating_source"),
                            "status": "new equipment, rating to confirm"})
        calculations = [{"target_scale": target, "units": solved.get("units") or {},
                         "streams": [{"id": sid, **row} for sid, row in (solved.get("streams") or {}).items()],
                         "new_equipment": records, "simulator": "watertap" if w.cfg.get("engine") == "watertap" else "dwsim"}]
        for proposal in proposals:
            if any(c.get("add_unit") and c["add_unit"].get("type") not in ROUTING for c in proposal.get("changes") or []):
                proposal = {**proposal, "calculation": calculations[0]}
    equipment = equipment_screen(changes, calculations)
    relief = pid.relief_scan(DATA / w.cfg["pid"]) if w.cfg.get("pid") else []
    data = {"case": w.name, "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "design_answer": (selected or {}).get("headline"), "proposal_titles": [p.get("title") for p in proposals],
            "envelope": envelope, "equipment": equipment, "dynamics": dynamic_screen(dynamics),
            "hazards": hazard_screen(spec, changes, relief),
            "constructability": constructability(changes, equipment, [p.get("cost_class") or "not stated" for p in proposals], economics)}
    sheets = "\n\n".join(datasheet_markdown(p.get("changes"), p.get("calculation") or (calculations[0] if calculations else None))
                            for p in proposals if p.get("changes"))
    text = markdown(data, sheets)
    files = {"prefeed.md": text, "prefeed.json": json.dumps(data, indent=2)}
    try:
        import tempfile
        from .decision import _pdf
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prefeed.pdf"
            _pdf([text], path, footer=f"Pre-FEED {w.name}")
            files["prefeed.pdf"] = path.read_bytes()
    except Exception as error:  # markdown and JSON remain the authoritative artifacts
        data["pdf_error"] = f"{type(error).__name__}: {error}"
        files["prefeed.json"] = json.dumps(data, indent=2)
    summary = ("Robust pass" if envelope["robust_pass"] else "Not robust") + \
              f" across {len(envelope['scenarios'])} operating scenarios; {len(equipment)} provisional equipment item(s)."
    meta = artifacts.save(w.name, "analysis", "Pre-FEED design gate", files, by="PlantAgent (deterministic)",
                          sources=[f"cases/{w.name}/case.json", f"runs/ws/{w.name}/model.json"] +
                                  ([f"cases/{w.name}/prefeed.json"] if cfg_path.exists() else []), summary=summary)
    return {**meta, "assessment": data}


if __name__ == "__main__":
    import sys
    from .plant import PlantWorkspace
    result = make(PlantWorkspace(sys.argv[1]))
    print(json.dumps({k: result[k] for k in ("id", "title", "files", "summary")}, indent=2))
