"""Proposal changes for WaterTAP RO specs (plantagent.ro): the RO counterpart of plant.patch / plant.change_errors.

A change is {path, value} into the RO spec, list items addressed by id, or {add_unit: {type: "ro_train", ...}} for a
new parallel train. Fields are classed:
- limit definitions (flux limits, product targets, minimum recoveries) never change: a proposal cannot redefine the check;
- operating set points and scenarios change freely (feed condition, recovery set point, HP discharge set point,
  trains in service, second-pass fraction);
- everything else is physical equipment (membrane, area, vessels, elements, pressure class, pumps, energy recovery,
  second pass, installed trains) and needs physical_change and rating_source, like DWSIM performance fields.
"""
import copy

CHANGE_HELP = (
    "RO (WaterTAP) changes: {path, value} into the RO spec, list items by id: feed.T_C | feed.TDS_g_L | feed.flow_m3_h "
    "(scenario); trains.in_service (N or N-1 duty trains; trains.installed is physical); stages.<stage id>.<field> "
    "(recovery is an operating set point only on the first stage of a spec that solves the HP pressure for it, else a limit; area_m2, vessels, elements_per_vessel, membrane, A_m_per_Pa_s, B_m_per_s, "
    "max_feed_pressure_bar are physical); hp_pump.P_out_bar (set point) and hp_pump.max_bar | max_kW | efficiency "
    "(pump replacement, physical); energy_recovery.type | efficiency (physical); second_pass (a whole block to add, "
    "null to remove; physical) and second_pass.fraction (partial-pass fraction, operating). Physical changes need "
    "physical_change and rating_source. Never change a limit definition: max_flux_*, max_lead_flux_*, target_TDS_g_L, "
    "target_boron_g_L, min_overall_recovery, min_concentrate_m3_h_per_vessel. A new parallel train is "
    "{add_unit: {id, type: 'ro_train', count, stage: {fields merged into every copied stage, e.g. "
    "max_feed_pressure_bar}, hp_pump: {P_out_bar, max_bar, max_kW, efficiency}, energy_recovery: {...}, or stages: "
    "[full list]}, rating_source}: it copies the existing train, renames its stages <id>-s1.., and the plant feed is "
    "split equally over every train in service. No reroute and no splitter/mixer units in RO specs."
)
LIMIT_FIELDS = {"max_flux_lmh", "max_flux_gfd", "max_lead_flux_lmh", "max_lead_flux_gfd", "target_TDS_g_L",
                "target_boron_g_L", "min_overall_recovery", "min_concentrate_m3_h_per_vessel"}
OPERATING = {("feed", None), ("trains", "in_service"), ("stages", "recovery"), ("hp_pump", "P_out_bar"),
             ("second_pass", "fraction"), ("energy_recovery", "P_out_bar")}
BLOCKS = ("feed", "trains", "stages", "hp_pump", "energy_recovery", "second_pass")


def is_ro(spec):
    return isinstance(spec, dict) and "stages" in spec and "units" not in spec


def _walk(spec, path, create=False):
    """(parent container, key) for a dotted path; list items by their id. Raises ValueError."""
    parts = path.split(".")
    if parts[0] not in BLOCKS:
        raise ValueError(f"{path}: RO paths start with one of {', '.join(BLOCKS)}")
    node = spec
    for i, key in enumerate(parts[:-1]):
        if isinstance(node, list):
            hit = next((x for x in node if isinstance(x, dict) and x.get("id") == key), None)
            if hit is None:
                raise ValueError(f"{path}: no item with id {key!r}; ids: {[x.get('id') for x in node if isinstance(x, dict)]}")
            node = hit
        elif isinstance(node, dict):
            if key not in node or node[key] is None:
                if not create:
                    raise ValueError(f"{path}: {'.'.join(parts[:i + 1])} is not in the spec")
                node[key] = {}
            node = node[key]
        else:
            raise ValueError(f"{path}: cannot descend into {'.'.join(parts[:i + 1])}")
    if isinstance(node, list):
        raise ValueError(f"{path}: address a stage field (stages.<id>.<field>), not a whole stage")
    return node, parts[-1]


def _kind(path, spec):
    parts = path.split(".")
    leaf = parts[-1]
    if leaf in LIMIT_FIELDS or parts[0] == "limits":
        return "limit"
    if parts[0] == "stages" and leaf == "recovery":
        # a set point only where it sets the HP discharge (first stage, no fixed P_out_bar); elsewhere it is the
        # documented minimum design recovery, a limit check
        first = (spec.get("stages") or [{}])[0].get("id") == parts[1]
        return "operating" if first and (spec.get("hp_pump") or {}).get("P_out_bar") is None else "limit"
    block = parts[0]
    if block == "feed":
        return "operating"
    field = parts[2] if block == "stages" and len(parts) == 3 else (parts[1] if len(parts) == 2 else None)
    return "operating" if (block, field) in OPERATING else "physical"


def _expand_train(spec, u):
    """A complete added-train definition: copy of the existing train with the change's overrides."""
    tid = u["id"]
    if u.get("stages"):
        stages = copy.deepcopy(u["stages"])
    else:
        stages = []
        for i, s in enumerate(spec["stages"] if isinstance(spec["stages"], list) else [spec["stages"]]):
            s = {**copy.deepcopy(s), **copy.deepcopy(u.get("stage") or {})}
            s["id"] = f"{tid}-s{i + 1}"
            stages.append(s)
    hp = {**copy.deepcopy(spec.get("hp_pump") or {}), **copy.deepcopy(u.get("hp_pump") or {})}
    hp["id"] = (u.get("hp_pump") or {}).get("id") or f"{tid}-HP"
    out = {"id": tid, "count": int(u.get("count", 1)), "stages": stages, "hp_pump": hp,
           "energy_recovery": {**copy.deepcopy(spec.get("energy_recovery") or {}), **copy.deepcopy(u.get("energy_recovery") or {})}}
    if u.get("rating_source"):
        out["rating_source"] = u["rating_source"]
    return out


def ids(spec):
    out = [s.get("id") for s in spec.get("stages") or []] + [(spec.get("hp_pump") or {}).get("id")]
    for t in spec.get("added_trains") or []:
        out += [t["id"], t["hp_pump"].get("id")] + [s.get("id") for s in t["stages"]]
    return {x for x in out if x}


def change_errors(spec, changes, require_evidence=True):
    errors = []
    for i, c in enumerate(changes or []):
        n = i + 1
        if not isinstance(c, dict):
            errors.append(f"change {n} is not an object")
            continue
        if sum(k in c for k in ("path", "add_unit", "reroute")) != 1:
            errors.append(f"change {n} must contain exactly one of path or add_unit")
            continue
        if "reroute" in c:
            errors.append(f"change {n}: RO specs have no stream connections to reroute; use add_unit type ro_train for a parallel train")
            continue
        if "path" in c:
            path = c.get("path")
            if not isinstance(path, str) or "value" not in c:
                errors.append(f"change {n} needs a path and a value")
                continue
            if path == "second_pass":
                kind = "physical"
            else:
                try:
                    node, key = _walk(copy.deepcopy(spec), path, create=path.startswith(("second_pass.", "trains.")))
                except ValueError as e:
                    errors.append(f"change {n}: {e}")
                    continue
                if key in ("vessels", "elements_per_vessel", "area_m2_per_element") and node.get("area_m2") is not None:
                    errors.append(f"change {n} {path}: this stage is sized by area_m2 (an explicit area wins over a vessel "
                                  "count); change area_m2")
                    continue
                kind = _kind(path, spec)
            if kind == "limit":
                errors.append(f"change {n} {path} redefines a limit check; a proposal changes the plant, not the limit")
            elif kind == "physical" and require_evidence and not (str(c.get("physical_change") or "").strip()
                                                                  and str(c.get("rating_source") or "").strip()):
                errors.append(f"change {n} {path} is physical equipment and needs physical_change and rating_source")
            continue
        u = c["add_unit"]
        if not isinstance(u, dict) or u.get("type") != "ro_train" or not isinstance(u.get("id"), str) or not u["id"]:
            errors.append(f"change {n}: in an RO spec add_unit must be {{id, type: 'ro_train', ...}}")
            continue
        if u["id"] in ids(spec):
            errors.append(f"change {n} cannot add duplicate id {u['id']}")
        if not str(c.get("rating_source") or u.get("rating_source") or "").strip():
            errors.append(f"change {n} add_unit {u['id']} needs rating_source")
        t = _expand_train(spec, u)
        missing = [k for k in ("max_bar", "max_kW") if t["hp_pump"].get(k) is None] + \
                  [f"{s['id']}.max_feed_pressure_bar" for s in t["stages"] if s.get("max_feed_pressure_bar") is None]
        if missing:
            errors.append(f"change {n} add_unit {u['id']} needs its own rating: {', '.join(missing)}")
        if t["count"] < 1:
            errors.append(f"change {n} add_unit {u['id']} count must be at least 1")
    return errors


def patch(spec, changes):
    errors = change_errors(spec, changes, require_evidence=False)
    if errors:
        raise ValueError("; ".join(errors))
    s = copy.deepcopy(spec)
    for c in changes:
        if c.get("add_unit"):
            t = _expand_train(s, c["add_unit"])
            if c.get("rating_source"):
                t["rating_source"] = c["rating_source"]
            s.setdefault("added_trains", []).append(t)
            continue
        if c["path"] == "second_pass":
            if c["value"] is None:
                s.pop("second_pass", None)
            else:
                s["second_pass"] = copy.deepcopy(c["value"])
            continue
        node, key = _walk(s, c["path"], create=c["path"].startswith(("second_pass.", "trains.")))
        node[key] = copy.deepcopy(c["value"])
    return s


def affected(spec, changes):
    """Ids whose checks a proposal targets: stage ids, the pump id, train ids, 'trains', 'permeate'/'plant' for scenarios."""
    out = set()
    for c in changes or []:
        if c.get("add_unit"):
            t = _expand_train(spec, c["add_unit"])
            out |= {t["id"], t["hp_pump"]["id"], *(s["id"] for s in t["stages"])}
            continue
        parts = str(c.get("path") or "").split(".")
        if parts[0] == "stages" and len(parts) > 1:
            out.add(parts[1])
        elif parts[0] == "hp_pump":
            out.add((spec.get("hp_pump") or {}).get("id") or "HP")
        elif parts[0] == "trains":
            out.add("trains")
        elif parts[0] == "second_pass":
            out |= {"second_pass", ((spec.get("second_pass") or {}).get("stage") or {}).get("id") or "RO-2P"}
        elif parts[0] == "energy_recovery":
            out |= {(spec.get("hp_pump") or {}).get("id") or "HP", "booster"}
    return out


def removed(spec, changes):
    """Check ids a proposal legitimately removes (switching the second pass off)."""
    if any(c.get("path") == "second_pass" and c.get("value") is None for c in changes or []):
        sp = spec.get("second_pass") or {}
        return {"second_pass", (sp.get("stage") or {}).get("id") or "RO-2P"}
    return set()


def added_trains(changes, spec):
    """New equipment records for plant.added_equipment: each added train with its ratings."""
    out = []
    for c in changes or []:
        u = c.get("add_unit") if isinstance(c, dict) else None
        if isinstance(u, dict) and u.get("type") == "ro_train":
            t = _expand_train(spec, u)
            out.append({"id": t["id"], "type": "ro_train", "count": t["count"],
                        "limits": {"hp_max_bar": t["hp_pump"].get("max_bar"), "hp_max_kW": t["hp_pump"].get("max_kW"),
                                   "max_feed_pressure_bar": max((s.get("max_feed_pressure_bar") or 0) for s in t["stages"])},
                        "rating_source": c.get("rating_source") or u.get("rating_source"), "status": "new equipment, rating to confirm"})
    return out


if __name__ == "__main__":
    spec = {"feed": {"flow_m3_h": 100, "TDS_g_L": 35, "T_C": 20}, "trains": {"installed": 3, "in_service": 2},
            "hp_pump": {"id": "P1", "max_bar": 70, "max_kW": 500, "P_out_bar": 60},
            "stages": [{"id": "S1", "area_m2": 1000, "max_feed_pressure_bar": 70, "max_flux_lmh": 15}]}
    assert patch(spec, [{"path": "trains.in_service", "value": 3}])["trains"]["in_service"] == 3
    assert change_errors(spec, [{"path": "stages.S1.max_flux_lmh", "value": 20}])
    assert change_errors(spec, [{"path": "hp_pump.max_kW", "value": 900}])  # physical without evidence
    assert not change_errors(spec, [{"path": "hp_pump.max_kW", "value": 900, "physical_change": "new motor", "rating_source": "quote"}])
    assert not change_errors(spec, [{"path": "feed.T_C", "value": 10}])
    t = patch(spec, [{"add_unit": {"id": "T9", "type": "ro_train", "stage": {"max_feed_pressure_bar": 95},
                                   "hp_pump": {"max_bar": 95, "P_out_bar": 90}}, "rating_source": "quote"}])["added_trains"][0]
    assert t["stages"][0]["id"] == "T9-s1" and t["stages"][0]["max_feed_pressure_bar"] == 95 and t["hp_pump"]["id"] == "T9-HP"
    assert affected(spec, [{"path": "stages.S1.area_m2", "value": 2}, {"path": "hp_pump.max_kW", "value": 1}]) == {"S1", "P1"}
    assert change_errors(spec, [{"reroute": {}}]) and change_errors(spec, [{"path": "stages.S9.area_m2", "value": 1}])
    print("ok")
