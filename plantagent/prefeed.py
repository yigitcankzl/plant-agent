"""Deterministic pre-FEED gate for a proposed process design.

Reuses the workspace simulator, verified proposal records, P&ID relief graph and
artifact store.  It does not invent vendor curves, dynamic constants or prices:
missing design inputs remain explicit actions for the engineer.

Usage: python -m plantagent.prefeed salt_mvr
"""
import copy
import json
import math
import re
import time
from pathlib import Path

from . import artifacts, pid
from .docs import DATA
from .proposed import datasheet_markdown, present_calculation

ROOT = Path(__file__).resolve().parent.parent
ROUTING = {"mixer", "splitter", "recycle"}
DISCIPLINE_STATUS = {"pass", "fail", "open", "not affected"}


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
            "energy": ("available" if enthalpy else "not checked: the solver does not report enthalpy on the boundary streams")}


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
                     "checks": [c for c in checks if c["utilisation"] >= .8], "all_checks": checks,
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


def _enrich(spec, calc):
    """Older calculation records lack the new unit's inlet flow, pressure ratio and efficiency: fill them from the
    record's own solved streams (no new solve)."""
    from .plant import _operating_point
    calc = copy.deepcopy(calc)
    streams = {r.get("id"): r for r in calc.get("streams") or [] if isinstance(r, dict)}
    for row in calc.get("new_equipment") or []:
        units = {row["id"]: row.get("operating_point") or {}}
        row["operating_point"] = _operating_point(spec, units, streams, row["id"])
    return calc


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
                     "pressure_ratio": row.get("pressure_ratio"), "head": row.get("head"),
                     "head_unit": row.get("head_unit"), "inlet": row.get("inlet") or {}, "outlet": row.get("outlet") or {},
                     "rating_source": row.get("rating_source") or equipment.get("rating_source") or "to confirm",
                     "vendor_gate": ["guaranteed curve over min/normal/max flow", "efficiency and driver rating",
                                     "surge/choke or BEP/minimum-flow margin", "materials and seals",
                                     "noise/vibration", "nozzle loads and mechanical design"]})
    return rows


def hazard_screen(spec, changes, relief, aliases=None):
    """Small deterministic HAZOP register for changed equipment. It is a prompt for a team HAZOP, not one by itself.
    Only real equipment: model routing nodes (splitters, mixers) are left out, and a heating-side change of a model unit
    is named by its P&ID tag (case.json model_aliases, e.g. E-201 for the heater folded into V-201)."""
    units = {u["id"]: u for u in spec.get("units") or []}
    heater_of = {uid: tag for tag, uid in (aliases or {}).items() if isinstance(uid, str)}
    changed = []
    for change in changes:
        if change.get("add_unit") and change["add_unit"].get("type") not in ROUTING:
            changed.append((change["add_unit"]["id"], change["add_unit"].get("type"), True))
        elif change.get("reroute"):
            uid = change["reroute"]["unit"]; changed.append((uid, (units.get(uid) or {}).get("type"), False))
        elif str(change.get("path") or "").startswith("units."):
            _, uid, field = (change["path"].split(".") + [""])[:3]
            if uid in heater_of and field in ("U_W_m2K", "area_m2"):
                changed.append((heater_of[uid], "hx", False))
            else:
                changed.append((uid, (units.get(uid) or {}).get("type"), False))
    changed = [c for c in changed if c[1] not in ROUTING]
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
            overpressure = deviation in ("High pressure", "Tube rupture")  # relief only safeguards an overpressure case
            if new:
                safeguard = "new equipment: relief and isolation to confirm" if overpressure else "new equipment: alarms and trips to define"
            elif overpressure:
                safeguard = "; ".join(f"relief {x['status']}" for x in existing) or "no relief shown on the P&ID scan"
            else:
                safeguard = "alarms, trips and operating response to confirm on the P&ID"
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


def discipline_register(envelope, equipment, dynamics, hazards, construction, supplied=None):
    """One change-impact register. Specialist adapters may replace an open row with sourced results."""
    physical = bool(construction["physical_units"])
    routed = bool(construction["reroutes"])
    incomplete = any(e["status"] != "provisional pass" for e in equipment)
    rows = {
        "process": {"status": "pass" if envelope["robust_pass"] else "fail",
                    "summary": "all stated operating scenarios pass" if envelope["robust_pass"] else "at least one operating scenario fails",
                    "source": "pre-FEED operating-envelope solves"},
        "mechanical": {"status": "open" if physical else "not affected",
                       "summary": ("provisional equipment selection; vendor/mechanical approval remains open" if physical else "no new physical equipment"),
                       "source": "proposal calculation and provisional ratings"},
        "electrical": {"status": "open" if physical else "not affected",
                       "summary": "new drivers need load, starting and protection checks" if physical else "no new driver identified",
                       "source": "constructability gate"},
        "piping_utilities": {"status": "open" if physical or routed else "not affected",
                             "summary": "tie-ins, line sizing, supports and utility capacity remain open" if physical or routed else "no piping change identified",
                             "source": "proposal topology and constructability gate"},
        "controls": {"status": "open" if physical or routed else "not affected",
                     "summary": "control narrative, cause/effect and permissives remain open" if physical or routed else "no control change identified",
                     "source": "proposal topology and dynamic screen"},
        "process_safety": {"status": "open" if hazards["rows"] else "not affected",
                           "summary": f"{len(hazards['rows'])} change-focused HAZOP action(s) remain open" if hazards["rows"] else "no changed equipment hazard row",
                           "source": "change-focused HAZOP/relief screen"},
        "civil_structural": {"status": "open" if physical else "not affected",
                             "summary": "plot, access, lifting and foundation checks remain open" if physical else "no new foundation identified",
                             "source": "constructability gate"},
    }
    if incomplete and physical:
        rows["mechanical"]["summary"] = "one or more provisional equipment ratings are incomplete or fail"
    if dynamics.get("status") == "fail":
        rows["controls"].update(status="fail", summary="critical-loop dynamic screen fails")
    for row in supplied or []:
        did = str(row.get("id") or "").strip()
        status = row.get("status")
        if not did or status not in DISCIPLINE_STATUS or not str(row.get("source") or "").strip():
            raise ValueError("each supplied discipline result needs id, pass/fail/open/not affected status, and source")
        if status in ("pass", "fail") and not row.get("checks"):
            raise ValueError(f"supplied {did} {status} result needs deterministic checks")
        rows[did] = {"status": status, "summary": str(row.get("summary") or ""),
                     "source": row["source"], "checks": list(row.get("checks") or [])}
    return [{"id": did, **row} for did, row in rows.items()]


def _gate(did, checks, source, summary, open_reason=None):
    """A sourced gate row. Only checks that name a non-illustrative source decide pass/fail; an illustrative rating
    over its limit leaves the gate open (the rating has to be confirmed before it can fail or pass the design)."""
    rated = [c for c in checks if isinstance(c.get("utilisation"), (int, float))]
    # model-consistency flags (model U vs correlation) describe the model, not the design
    firm = [c for c in rated if "ILLUSTRATIVE" not in str(c.get("source") or "").upper() and not str(c.get("check") or "").startswith("model U")]
    soft_over = sorted((c for c in rated if c not in firm and c["utilisation"] > 1), key=lambda c: -c["utilisation"])
    if open_reason:
        status = "open"
    elif any(c["utilisation"] > 1 for c in firm):
        status = "fail"
    elif soft_over or not firm:
        status = "open"
    else:
        status = "pass"
    if soft_over and status != "fail":
        summary += "; over an ILLUSTRATIVE rating (confirm): " + ", ".join(
            f"{c['id']} {c['check']} {c['utilisation'] * 100:.0f} %" for c in soft_over[:3])
    rows = [{"id": c.get("id"), "check": c.get("check"), "value": _fmt(c.get("value")), "limit": _fmt(c.get("limit")),
             "unit": c.get("unit") or "", "result": (f"{c['utilisation'] * 100:.0f} %" if isinstance(c.get("utilisation"), (int, float))
                                                     else "information"), "source": c.get("source")} for c in checks]
    return {"id": did, "status": status, "summary": summary + (f"; {open_reason}" if open_reason else ""),
            "source": source, "checks": rows}


def discipline_gates(w, answer=None, refresh=False):
    """Discipline gates of the design answer from the deterministic engines already on this project: DWSIM (process),
    pandapower (electrical), ht/fluids (heat transfer), Cantera (combustion). No model call. Cached in gates.json
    keyed by the design answer, so the page can show the strip without re-solving."""
    from . import revb
    from .plant import patch
    ans = (w.answers[int(answer)] if answer is not None and -len(w.answers) <= int(answer) < len(w.answers)
           else revb.design_answer(w.answers))
    proposals = [p for p in (ans or {}).get("proposals") or [] if p.get("verified")]
    if not proposals:
        return {"error": "no verified design answer to assess"}
    key = {"headline": ans.get("headline"), "request": ans.get("request"), "titles": [p.get("title") for p in proposals],
           "revisions": len(w.revisions)}
    cache = w.model_file.with_name("gates.json")
    if not refresh and cache.exists():
        old = json.loads(cache.read_text())
        if old.get("key") == key:
            return old
    changes = [c for p in proposals for c in p.get("changes") or []]
    target = float(w.cfg.get("target_scale") or 1.0)
    comb = ans.get("combined") if len(proposals) > 1 and not (ans.get("combined") or {}).get("error") else None
    reach = (comb or {}).get("reaches_target") if comb else proposals[-1].get("reaches_target")
    cap = (comb or {}).get("capacity_multiple") if comb else proposals[-1].get("capacity_multiple")
    sim = "WaterTAP" if w.cfg.get("engine") == "watertap" else "DWSIM"
    proc = [{"id": "plant", "check": "maximum throughput with all verified changes vs target", "value": (cap or 0) * 100,
             "limit": target * 100, "unit": "%", "utilisation": target / cap if cap else 2.0,
             "source": f"{sim} re-solve of the combined changes on the server"}]
    proc += [{**c, "source": f"{sim} limit check"} for c in (comb or {}).get("over_limits_at_target") or []]
    summary = f"design {'reaches' if reach else 'does not reach'} {target * 100:.0f} % (max {(cap or 0) * 100:.0f} %)"
    cfg_path = ROOT / "cases" / w.name / "prefeed.json"
    scen = (json.loads(cfg_path.read_text()) if cfg_path.exists() else {}).get("scenarios")
    robust, rsum = [], ""
    if scen:  # the engineer's operating envelope: the design must hold in every stated scenario, not just at the target
        env = run_envelope(patch(copy.deepcopy(w.spec), changes), scen, w._solve, patch)
        for r in env["scenarios"]:
            wst = r.get("worst") or {}
            robust.append({"id": wst.get("id") or "scenario", "check": f"scenario '{r['name']}': {wst.get('check') or 'solve'}",
                         "value": wst.get("value"), "limit": wst.get("limit"), "unit": wst.get("unit"),
                         "utilisation": wst.get("utilisation") if not r["errors"] else 2.0,
                         "source": f"{sim} solve; scenario basis: {r['basis']}"})
        failed = [r["name"] for r in env["scenarios"] if not r["pass"]]
        rsum = f"operating envelope {len(env['scenarios']) - len(failed)}/{len(env['scenarios'])} scenarios pass" + \
               (f" (fails: {', '.join(failed)})" if failed else "")
    # the target itself and the envelope around it are separate gates: reaching 120 % and holding it when fouled are different questions
    rows = [_gate("process", proc, f"{sim} re-solve of the design (server verify)", summary)]
    if robust:
        rows.append(_gate("robustness", robust, f"{sim} solves of the pre-FEED operating envelope", rsum))
    # mechanical: provisional ratings of new machines vs the solved duty; a vendor curve is still needed
    eq = equipment_screen(changes, [_enrich(patch(copy.deepcopy(w.spec), changes), p["calculation"]) for p in proposals if p.get("calculation")])
    if eq:
        mech = []
        for e in eq:
            if e.get("flow_margin"):
                mech.append({"id": e["id"], "check": "solved flow vs provisional rating", "value": e["operating_flow"],
                             "limit": e["rating_flow"], "unit": e.get("flow_unit") or "", "utilisation": 1 / e["flow_margin"],
                             "source": e["rating_source"]})
            if e.get("power_margin"):
                mech.append({"id": e["id"], "check": "solved shaft power vs provisional driver rating", "value": e["calculated_shaft"],
                             "limit": e["rating_shaft"], "unit": e.get("shaft_unit") or "", "utilisation": 1 / e["power_margin"],
                             "source": e["rating_source"]})
        rows.append(_gate("mechanical", mech, "proposal calculation vs provisional rating",
                          f"{len(eq)} new machine(s) within provisional ratings" if mech else "no solved rating",
                          open_reason="guaranteed vendor curve, materials and mechanical design still needed"))
    try:
        from . import electrical
        cfg = electrical.config(w.name)
        if cfg and electrical.available():
            if electrical.motor_changes(cfg, changes):
                e = electrical.for_workspace(w, changes, target, save=False)
                src = "pandapower load flow of cases/%s/electrical.json%s" % (w.name, " (ILLUSTRATIVE network values)" if "ILLUSTRATIVE" in str(cfg.get("note")) else "")
                g = _gate("electrical", e["checks"], src, e["summary"])
                # the network is illustrative as a whole, but a transformer overload on it is the finding to act on
                if any(c["utilisation"] > 1 for c in e["checks"]):
                    g["status"] = "fail"
                rows.append(g)
            else:
                rows.append({"id": "electrical", "status": "not affected", "summary": "no new or re-rated motor on the one-line diagram",
                             "source": f"cases/{w.name}/electrical.json motor list", "checks": []})
    except Exception as ex:  # noqa: BLE001 - a broken adapter leaves the gate open, never green
        rows.append({"id": "electrical", "status": "open", "summary": f"electrical check could not run: {type(ex).__name__}: {ex}"[:200],
                     "source": "pandapower adapter", "checks": []})
    try:
        from . import hxdetail
        geo = ROOT / "cases" / w.name / "hx_geometry.json"
        hx_checks, notes = [], []
        for tag, entry in (json.loads(geo.read_text()).items() if geo.exists() else []):
            if not isinstance(entry, dict) or tag.startswith("_"):
                continue
            uid = entry.get("model_unit", tag)
            clean = any(str(c.get("path") or "") == f"units.{uid}.U_W_m2K" for c in changes)
            r = hxdetail.hx_detail(w, tag, target, condition="clean" if clean else "fouled", save=False, changes=changes)
            if r.get("illustrative_geometry"):  # the rating can only be as firm as the geometry it rates
                r["checks"] = [{**c, "source": f"{c.get('source')} (ILLUSTRATIVE geometry)"} for c in r["checks"]]
            hx_checks += r["checks"]
            notes.append(f"{tag} ({r['condition']}): area needed {r['results']['A_req']:.0f} of {r['results']['A_inst']:.0f} m²")
        if hx_checks:
            rows.append(_gate("heat_transfer", hx_checks, "ht/fluids exchanger rating at the design point (cases/%s/hx_geometry.json)" % w.name,
                              "; ".join(notes)))
    except Exception as ex:  # noqa: BLE001
        rows.append({"id": "heat_transfer", "status": "open", "summary": f"exchanger rating could not run: {type(ex).__name__}: {ex}"[:200],
                     "source": "ht/fluids adapter", "checks": []})
    try:
        from . import combustion
        if combustion.load_case(w.name):
            r = combustion.combustion_check(w, steam_scale=target, scale=target, save=False)
            d = r["scenario"].get("duct_burner") or {}
            fired = (d.get("fuel_MMBtu_h_HHV") or 0) > 0
            rows.append(_gate("combustion", r["checks"], "Cantera gas turbine + HRSG model (cases/%s/combustion.json)" % w.name,
                              r["summary"], open_reason=("if HRSG steam rises with throughput (x%.2f), it needs supplementary (duct) firing "
                                                         "the unfired HRSG does not have: a modification to decide" % target) if fired else None))
    except Exception as ex:  # noqa: BLE001
        rows.append({"id": "combustion", "status": "open", "summary": f"combustion check could not run: {type(ex).__name__}: {ex}"[:200],
                     "source": "Cantera adapter", "checks": []})
    physical = [c["add_unit"]["id"] for c in changes if c.get("add_unit") and c["add_unit"].get("type") not in ROUTING]
    routed = physical or any(c.get("reroute") or c.get("bypass") or c.get("remove_unit") for c in changes)
    supply = [str(c["path"]).split(".")[1] for c in changes if str(c.get("path") or "").startswith("feeds.")]
    for did, what, needed in (("piping_utilities", "tie-ins, line sizing, supports and utility headers"
                               + (f" (supply change on {', '.join(dict.fromkeys(supply))}: header capacity to confirm)" if supply else ""),
                               routed or supply),
                              ("controls", "control narrative, split/load-sharing control, cause & effect and permissives", routed),
                              ("process_safety", "change-focused HAZOP, relief case and isolation for the changed equipment", routed),
                              ("civil_structural", "plot, access, lifting and foundations", physical)):
        rows.append({"id": did, "status": "open" if needed else "not affected",
                     "summary": (f"no calculation adapter: {what} remain open" + (f" for {', '.join(physical)}" if physical else "")) if needed
                     else "no physical or routing change", "source": "proposal topology (no engine for this discipline)", "checks": []})
    out = {"key": key, "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "disciplines": rows}
    cache.write_text(json.dumps(out, indent=1))
    return out


def decision_inputs(changes, field_checks=None):
    """Rank explicit field checks, or make only the minimum evidence requests implied by the physical changes."""
    rows = []
    for n, raw in enumerate(field_checks or [], 1):
        if not all(str(raw.get(k) or "").strip() for k in ("item", "where", "changes")):
            raise ValueError("field checks need item, where and changes")
        priority = int(raw.get("priority") or n)
        if priority < 1:
            raise ValueError("field-check priority must be a positive integer")
        rows.append({"priority": priority, "item": raw["item"], "where": raw["where"],
                     "changes": raw["changes"], "source": raw.get("source") or "design answer"})
    if not rows:
        for change in changes:
            path = str(change.get("path") or "")
            if path.endswith(".U_W_m2K"):
                tag = path.split(".")[1]
                rows.append({"item": f"Post-work heat-transfer coefficient for {tag}",
                             "where": "fixed-flow temperature and duty survey after cleaning",
                             "changes": f"If measured U is below {change.get('value')} W/m2K, re-run the envelope; cleaning alone may not clear the limit",
                             "source": "verified proposal", "priority": len(rows) + 1})
            unit = change.get("add_unit") or {}
            if unit.get("type") not in (None, *ROUTING):
                rows.append({"item": f"Guaranteed duty and driver curve for {unit['id']}",
                             "where": "vendor curve at minimum, normal and maximum suction/discharge conditions",
                             "changes": "If the guaranteed curve misses the calculated duty or provisional rating, resize or reject the proposal",
                             "source": change.get("rating_source") or "proposal rating to confirm", "priority": len(rows) + 1})
        if any(c.get("reroute") for c in changes):
            rows.append({"item": "Tie-in and isolation survey", "where": "proposed Rev B connection points in the field",
                         "changes": "If isolation, access or line class differs, revise the routing, outage and installed cost",
                         "source": "proposal topology", "priority": len(rows) + 1})
    return sorted(rows, key=lambda row: row["priority"])


def option_comparison(proposals, envelope):
    """Compare what is actually on record; do not manufacture numeric Pareto rankings from cost-class labels."""
    rows = []
    for p in proposals:
        cap = p.get("capacity_multiple")
        reaches = p.get("reaches_target")
        rows.append({"title": p.get("title") or "untitled change", "verified": bool(p.get("verified")),
                     "role": "standalone target" if reaches else "partial change" if reaches is False else "not independently solved",
                     "capacity_multiple": cap, "cost_class": p.get("cost_class") or "not stated",
                     "physical_units": [c["add_unit"]["id"] for c in p.get("changes") or []
                                        if c.get("add_unit") and c["add_unit"].get("type") not in ROUTING]})
    rows.append({"title": "Combined proposed design", "verified": envelope["robust_pass"],
                 "role": "combined envelope", "capacity_multiple": max(
                     (r["scale"] for r in envelope["scenarios"] if r["pass"]), default=None),
                 "cost_class": " + ".join(dict.fromkeys(r["cost_class"] for r in rows)) or "not stated",
                 "physical_units": [u for r in rows for u in r["physical_units"]]})
    return {"options": rows, "pareto": "not ranked: sourced numeric cost, outage and energy values are required"}


def _direction(check):
    value, limit, util = check.get("value"), check.get("limit"), check.get("utilisation")
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (value, limit, util)) or not value or not limit:
        return None
    high_error, low_error = abs(util - value / limit), abs(util - limit / value)
    if abs(high_error - low_error) < 1e-9:
        words = str(check.get("check") or "").lower()
        return "min" if any(x in words for x in ("minimum", "npsh", "residence", "min travel")) else "max"
    return "max" if high_error < low_error else "min"


def commissioning_plan(changes, envelope, equipment, observations=None):
    """Acceptance plan from solved checks; supplied observations close tests against the same documented limit."""
    tags = {c["add_unit"]["id"] for c in changes if c.get("add_unit") and c["add_unit"].get("type") not in ROUTING}
    tags |= {c["path"].split(".")[1] for c in changes if str(c.get("path") or "").startswith("units.")}
    passed = [row for row in envelope["scenarios"] if row["pass"]]
    target = max(passed or envelope["scenarios"], key=lambda r: r["scale"])
    tests = []
    for check in target.get("all_checks") or []:
        if check.get("id") not in tags or _direction(check) is None:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", f"{check['id']}-{check['check']}".lower()).strip("-")
        tests.append({"id": slug, "tag": check["id"], "measurement": check["check"],
                      "predicted": check["value"], "limit": check["limit"], "unit": check.get("unit") or "",
                      "direction": _direction(check), "status": "open", "source": f"scenario {target['name']}"})
    for row in equipment:
        if row["id"] not in {t["tag"] for t in tests}:
            tests.append({"id": re.sub(r"[^a-z0-9]+", "-", f"{row['id']}-vendor-duty".lower()), "tag": row["id"],
                          "measurement": "vendor guaranteed operating point", "predicted": row.get("operating_flow"),
                          "limit": row.get("rating_flow"), "unit": row.get("flow_unit") or "", "direction": "max",
                          "status": "open", "source": row.get("rating_source") or "rating to confirm"})
    by_id = {t["id"]: t for t in tests}
    for observed in observations or []:
        test = by_id.get(observed.get("test_id"))
        if not test:
            raise ValueError(f"unknown commissioning test {observed.get('test_id')}")
        if not str(observed.get("source") or "").strip():
            raise ValueError(f"commissioning observation {test['id']} needs a source")
        value = float(observed["value"])
        if not math.isfinite(value):
            raise ValueError(f"commissioning observation {test['id']} must be finite")
        test["observed"] = value
        test["observation_source"] = observed["source"]
        if test.get("limit") is None:
            test["status"] = "review"
        else:
            test["status"] = "pass" if ((value <= test["limit"]) if test["direction"] == "max" else (value >= test["limit"])) else "fail"
    status = "fail" if any(t["status"] == "fail" for t in tests) else "pass" if tests and all(t["status"] == "pass" for t in tests) else "open"
    return {"status": status, "scenario": target["name"], "tests": tests,
            "note": "Open tests are commissioning requirements, not evidence that the installed change passed."}


def rfq_markdown(equipment):
    lines = ["# Vendor RFQ duty sheet", "", "**DRAFT — bidder data and guarantees remain to be supplied.**", ""]
    if not equipment:
        return "\n".join(lines + ["No new physical equipment in this design.", ""])
    for row in equipment:
        lines += [f"## {row['id']} — {row['type']}", "",
                  f"- Calculated operating flow: {_fmt(row.get('operating_flow'))} {row.get('flow_unit') or ''}",
                  f"- Provisional rated flow: {_fmt(row.get('rating_flow'))} {row.get('flow_unit') or ''}",
                  f"- Calculated shaft load: {_fmt(row.get('calculated_shaft'))} {row.get('shaft_unit') or ''}",
                  f"- Provisional driver rating: {_fmt(row.get('rating_shaft'))} {row.get('shaft_unit') or ''}",
                  f"- Rating basis: {row.get('rating_source') or 'to confirm'}"]
        if row.get("pressure_ratio") is not None:
            lines.append(f"- Calculated pressure ratio: {_fmt(row['pressure_ratio'])}")
        if row.get("head") is not None:
            lines.append(f"- Calculated head: {_fmt(row['head'])} {row.get('head_unit') or ''}")
        lines += ["", "Bidder shall return:", ""]
        lines += [f"- {item}" for item in row["vendor_gate"]]
        lines += ["- guaranteed performance at minimum, normal and maximum duty", "- exceptions and required auxiliaries", ""]
    return "\n".join(lines)


def commissioning_markdown(plan):
    lines = ["# Commissioning acceptance plan", "", "**DRAFT — acceptance readings require traceable field sources.**", "",
             f"Scenario basis: {plan['scenario']}. Overall status: **{plan['status'].upper()}**.", "",
             "| Test | Tag | Measurement | Predicted | Acceptance limit | Observed | Status | Source |",
             "|---|---|---|---:|---:|---:|---|---|"]
    for row in plan["tests"]:
        op = "≤" if row["direction"] == "max" else "≥"
        lines.append(f"| {row['id']} | {row['tag']} | {row['measurement']} | {_fmt(row.get('predicted'))} {row['unit']} | "
                     f"{op} {_fmt(row.get('limit'))} {row['unit']} | {_fmt(row.get('observed'))} | {row['status']} | "
                     f"{row.get('observation_source') or row['source']} |")
    lines += ["", plan["note"], ""]
    return "\n".join(lines)


def _fmt(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


def _pct(fraction):
    return f"{fraction * 100:.0f}%" if isinstance(fraction, (int, float)) else "—"


def markdown(data, datasheets=""):
    env = data["envelope"]
    lines = ["# Pre-FEED design gate", "", "**DRAFT — simulator screening, not approved for construction.**", "",
             f"**Verdict:** {'ROBUST PASS' if env['robust_pass'] else 'NOT ROBUST'} across {len(env['scenarios'])} stated operating scenarios.", "",
             "## Operating envelope", "", "| Scenario | Load | Result | Governing check | Utilisation | Mass closure | Basis |",
             "|---|---:|---|---|---:|---:|---|"]
    for row in env["scenarios"]:
        worst, bal = row.get("worst") or {}, row["balance"]
        lines.append(f"| {row['name']} | {row['scale'] * 100:.0f}% | {'PASS' if row['pass'] else 'FAIL'} | "
                     f"{worst.get('id', '—')} {worst.get('check', '')} | {_pct(worst.get('utilisation'))} | "
                     f"{_fmt(bal.get('mass_error_pct'))}% | {row['basis']} |")
    lines += ["", "Energy closure: " + "; ".join(sorted({r["balance"].get("energy", "not available") for r in env["scenarios"]})), "",
              "## Discipline impact register", "", "| Discipline | Status | Impact | Evidence |", "|---|---|---|---|"]
    lines += [f"| {r['id'].replace('_', ' ').title()} | {r['status']} | {r['summary']} | {r['source']} |" for r in data["disciplines"]]
    lines += ["", "## Decision-changing evidence", ""]
    if data["decision_inputs"]:
        lines += ["| Priority | Evidence needed | Where / how | Decision changed | Source |", "|---:|---|---|---|---|"]
        lines += [f"| {r['priority']} | {r['item']} | {r['where']} | {r['changes']} | {r['source']} |" for r in data["decision_inputs"]]
    else:
        lines += ["No decision-changing field input was identified from the recorded changes."]
    lines += ["", "## Change portfolio", "", "| Change | Role | Verified | Capacity | Cost class | New equipment |",
              "|---|---|---|---:|---|---|"]
    for row in data["options"]["options"]:
        capacity = f"{row['capacity_multiple'] * 100:.1f}%" if isinstance(row.get("capacity_multiple"), (int, float)) else "—"
        lines.append(f"| {row['title']} | {row['role']} | {'yes' if row['verified'] else 'no'} | {capacity} | "
                     f"{row['cost_class']} | {', '.join(row['physical_units']) or '—'} |")
    lines += ["", data["options"]["pareto"], "", "## Preliminary equipment selection", ""]
    if data["equipment"]:
        lines += ["| Tag | Type | Status | Rating / solved flow | Rating / solved power | Rating source |", "|---|---|---|---:|---:|---|"]
        for row in data["equipment"]:
            lines.append(f"| {row['id']} | {row['type']} | {row['status']} | {_pct(row['flow_margin'])} | {_pct(row['power_margin'])} | {row['rating_source']} |")
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
    com = data["commissioning"]
    lines += ["", "## Commissioning acceptance", "", f"Status: **{com['status'].upper()}** against scenario {com['scenario']}.", ""]
    if com["tests"]:
        lines += ["| Test | Tag | Measurement | Limit | Status |", "|---|---|---|---:|---|"]
        for row in com["tests"]:
            op = "≤" if row["direction"] == "max" else "≥"
            lines.append(f"| {row['id']} | {row['tag']} | {row['measurement']} | {op} {_fmt(row.get('limit'))} {row['unit']} | {row['status']} |")
    else:
        lines += ["No solved acceptance check maps to the changed equipment; define the acceptance measurements before issue."]
    lines += ["", "## Gate and limitations", "", "- A pass means all stated simulator checks passed in all stated scenarios; it is not mechanical or vendor approval.",
              "- New equipment remains provisional until guaranteed curves and materials are checked.",
              "- The automated hazard register does not replace a multidisciplinary HAZOP or relief-system design.",
              "- Missing inputs stay open; PlantAgent does not invent curves, dynamic constants or costs.", ""]
    return "\n".join(lines)


def make(w, answer=None, scenarios=None, dynamics=None, economics=None, commissioning=None, disciplines=None):
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
    calculations = [_enrich(spec, p.get("calculation")) for p in proposals if p.get("calculation")]
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
    dynamic = dynamic_screen(dynamics)
    hazards = hazard_screen(spec, changes, relief, w.cfg.get("model_aliases"))
    construction = constructability(changes, equipment, [p.get("cost_class") or "not stated" for p in proposals], economics)
    if disciplines is None and cfg.get("disciplines") is None and selected in w.answers:
        try:  # sourced engine results (DWSIM, pandapower, ht/fluids, Cantera) replace the open placeholder rows
            disciplines = discipline_gates(w, w.answers.index(selected)).get("disciplines")
        except Exception:  # noqa: BLE001 - the placeholder register stays, open
            disciplines = None
    discipline_rows = discipline_register(envelope, equipment, dynamic, hazards, construction,
                                          disciplines if disciplines is not None else cfg.get("disciplines"))
    inputs = decision_inputs(changes, cfg.get("field_checks") or (selected or {}).get("field_checks"))
    options = option_comparison(proposals, envelope)
    commission = commissioning_plan(changes, envelope, equipment,
                                     commissioning if commissioning is not None else cfg.get("commissioning"))
    data = {"case": w.name, "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "design_answer": (selected or {}).get("headline"), "proposal_titles": [p.get("title") for p in proposals],
            "envelope": envelope, "equipment": equipment, "dynamics": dynamic, "hazards": hazards,
            "constructability": construction, "disciplines": discipline_rows, "decision_inputs": inputs,
            "options": options, "commissioning": commission}
    sheets = "\n\n".join(datasheet_markdown(p.get("changes"), _enrich(spec, p["calculation"]) if p.get("calculation") else
                                             (calculations[0] if calculations else None))
                            for p in proposals if p.get("changes"))
    text = markdown(data, sheets)
    files = {"prefeed.md": text, "prefeed.json": json.dumps(data, indent=2),
             "impact-register.json": json.dumps(discipline_rows, indent=2),
             "vendor-rfq.md": rfq_markdown(equipment), "commissioning.md": commissioning_markdown(commission)}
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
    open_disciplines = sum(r["status"] in ("open", "fail") for r in discipline_rows)
    summary = ("Robust pass" if envelope["robust_pass"] else "Not robust") + \
              f" across {len(envelope['scenarios'])} operating scenarios; {len(equipment)} provisional equipment item(s); " \
              f"{open_disciplines} discipline gate(s) open or failed; commissioning {commission['status']}."
    meta = artifacts.save(w.name, "analysis", "Pre-FEED design gate", files, by="PlantAgent (deterministic)",
                          sources=[f"cases/{w.name}/case.json", f"runs/ws/{w.name}/model.json"] +
                                  ([f"cases/{w.name}/prefeed.json"] if cfg_path.exists() else []), summary=summary)
    return {**meta, "assessment": data}


if __name__ == "__main__":
    import sys
    from .plant import PlantWorkspace
    result = make(PlantWorkspace(sys.argv[1]))
    print(json.dumps({k: result[k] for k in ("id", "title", "files", "summary")}, indent=2))
