"""Process-plant workspace: the agent reads a smart P&ID (DEXPI) and the operating data sheet, builds the DWSIM model
itself, then answers the engineer's questions with simulator-verified proposals the engineer accepts or rejects.
"""
import copy
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path

from . import audit, brine, grid, llm, pid, process, ro, ro_changes, trapped
from .docs import DATA
from .study import ARR, Study, compact, submit, text_tool_calls, unstring

ROOT = Path(__file__).resolve().parent.parent
S, N, B = {"type": "string"}, {"type": "number"}, {"type": "boolean"}


def _write_json(path, value):
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=1))
    os.replace(tmp, path)

RULES = ("Rules: every number comes from the P&ID (cite the tag and attribute), the operating data sheet (cite the row), or a "
         "logged simulator run (cite its label). Never invent equipment ratings. State each assumption. Use the simulator, not "
         "your own arithmetic, for temperatures, duties, areas and capacity. Never raise an existing limits.* rating to make a "
         "proposal pass. If the spec cannot express the physics or change, call report_gap instead of approximating or changing a "
         "documented limit. For physical "
         "new equipment use add_unit with a complete unit spec, its own limits and a rating_source; "
         "use routing-only splitter/mixer units and reroute changes when needed so flow actually passes through parallel equipment. "
         "Make data sheets, calculation sheets, summaries and work orders with make_document, never by writing them yourself.")

CHANGE_HELP = ("One change is either {path, value} for an existing operating/model field; "
               "{add_unit: {complete unit spec}, limits: {that new unit's ratings}, rating_source: 'vendor quote to confirm / "
               "standard size ...'}; or {reroute: {unit, field, value}} for a process connection. Do not edit limits.* for "
               "existing equipment. A physical change to an existing performance field (for example clean U, efficiency or "
               "installed area) also needs physical_change and rating_source; equipment type/kind cannot be edited in place. "
               "A parallel train normally needs a splitter, the new rated unit, a mixer, and reroutes of "
               "the existing unit's inlet/outlet. Routing-only splitter/mixer units do not need ratings or a rating_source. "
               "A unit IN SERIES on a line (e.g. a booster pump or preheater on stream S1): add_unit with in=S1 and a new "
               "out stream, then reroute the unit that consumed S1 to the new stream. Taking equipment out: "
               "{remove_unit: id, physical_change} (then reroute what used its streams) or {bypass: {unit: id}, physical_change} "
               "for a one-in/one-out unit whose flow then skips it.")

CHANGE = {"path": {"type": "string", "description": "feeds.<stream>.<field> | units.<id>.<field>; never limits.* for existing equipment"},
          "value": {"description": "new value for path"},
          "physical_change": {"type": "string", "description": "physical work that changes an existing performance field"},
          "rating_source": {"type": "string", "description": "source for a changed performance value or a new unit rating"},
          "add_unit": {"type": "object", "description": "complete process unit spec, including id, type and connections"},
          "limits": {"type": "object", "description": "ratings for add_unit only; stored under limits.<new id>"},
          "remove_unit": {"type": "string", "description": "id of an existing unit taken out (needs physical_change)"},
          "bypass": {"type": "object", "description": "{unit: id} of a one-in/one-out unit the flow now skips (needs physical_change)"},
          "reroute": {"type": "object", "description": "change a unit connection so the added equipment is in the flow",
                      "properties": {"unit": S, "field": S, "value": {"description": "stream id or list of stream ids"}}}}

SUBMIT_MODEL = submit("submit_model", "The process model you built and calibrated.", {
    "label": {"type": "string", "description": "label of the calibrated run_process run (the model)"},
    "mapping": ARR({"tag": S, "modelled_as": S, "source": S}),
    "calibration": ARR({"item": S, "measured": S, "simulated": S, "source": S}),
    "assumptions": {"type": "array", "items": S},
}, ["label", "mapping", "calibration"])

SUBMIT_MODEL_RO = submit("submit_model", "The WaterTAP reverse-osmosis model you built and calibrated.", {
    "label": {"type": "string", "description": "label of the calibrated run_ro run (the model)"},
    "mapping": ARR({"tag": S, "modelled_as": S, "source": S}),
    "calibration": ARR({"item": S, "measured": S, "simulated": S, "source": S}),
    "assumptions": {"type": "array", "items": S},
}, ["label", "mapping", "calibration"])

# DWSIM build user prompt: keep byte-stable for non-WaterTAP cases.
BUILD_DWSIM = (
    "Read the P&ID and the operating data sheet. Build the DWSIM flowsheet "
    "with run_process, following the P&ID topology exactly: every process equipment item as a unit with its "
    "P&ID tag as id, recirculation loops closed with a recycle unit only where the loop temperature is set by "
    "mixing (e.g. a tank fed by fresh product and a recirculation); a closed circulating loop held at a "
    "known supply temperature (chilled water, a coolant loop) is modelled once-through instead: a feed at "
    "its supply temperature and flow, through its heat loads, to the exchanger or chiller that returns it "
    "to supply temperature. Control valves that carry flow as valves "
    "with their tags, utilities as feeds with utility: true. Where the site datasheets contradict P&ID "
    "attributes, use the site data and list the conflict as an assumption; also act on the P&ID data_quality "
    "warnings. Put in `limits` EVERY rating and requirement you can cite: pump rated and minimum flow, motor "
    "power, NPSHr and relief set pressure; exchanger installed area with the outlet temperature the process "
    "needs, frame limit and available pressure drop; tank hold time; product temperature limits; utility "
    "supply limits on the utility feed streams. Calibrate against EVERY measured value in the data sheet "
    "(temperatures, flows, pressure drops) and report measured vs simulated. Run check_coverage on your final "
    "model and fix every missing connection that carries normal flow. Then call submit_model. A deterministic review "
    "checks that submit: if it returns blocking findings, fix the flowsheet and call submit_model once more. "
    "If the spec cannot express the fix, call report_gap instead of approximating or changing a documented limit. "
    "If there are project documents, search them and read only the pages with the equipment data you need "
    "(datasheets), at most 6. The model you submit is the as-built plant; later alternatives must express physical "
    "additions explicitly with add_unit/reroute changes, not by raising an existing rating."
)

BUILD_WATERTAP = (
    "You are constructing a seawater reverse-osmosis (SWRO) model with WaterTAP. Do not use run_process or "
    "process_capacity. Build and solve with run_ro; search capacity with ro_capacity. Model the full available process "
    "boundary: intake/feed condition; pretreatment pressure losses and recoveries; high-pressure pumps; membrane "
    "stages/trains; one-train-out availability; PX or turbine energy recovery and booster pumps; partial or full second "
    "pass where documented; post-treatment as documented notes where chemistry is not simulated; permeate and "
    "concentrate outlets. Every documented rating or requirement must become a WaterTAP check (feed pressure, membrane "
    "flux, recovery, minimum concentrate flow per vessel, pump power, product TDS, train/vessel/element count and "
    "availability). Report every unsupported physics through report_gap — especially boron when no boron coefficient is "
    "available. Before submit_model run at least one design-condition solve, one cold/high-salinity solve, and a "
    "ro_capacity search. Run check_coverage on the final model. State second-pass and one-train-out assumptions "
    "explicitly. Then call submit_model. A deterministic WaterTAP review checks that submit: if it returns blocking "
    "findings, fix the RO spec and call submit_model once more. If the spec cannot express the fix, call report_gap. "
    "If there are project documents, search them and read only the pages with the equipment data you need, at most 6."
)

SUBMIT_MODEL_TRAPPED = submit("submit_model", "The blocked-in segment model you built.", {
    "label": {"type": "string", "description": "label of the run_trapped run (the model)"},
    "mapping": ARR({"tag": S, "modelled_as": S, "source": S}),
    "calibration": ARR({"item": S, "measured": S, "simulated": S, "source": S}),
    "assumptions": {"type": "array", "items": S},
}, ["label", "mapping", "calibration"])

BUILD_TRAPPED = (
    "Build a model of the blocked-in pipe segment with run_trapped (DWSIM Peng-Robinson thermodynamics along a constant-"
    "volume path; the slider and `scale` multiply the documented time blocked in). Do not use run_process. From the data "
    "sheet and drawing: the fluid composition, the start pressure and liquid fill, the pipe size and wall, the heat leak per "
    "metre, every valve that isolates the segment (closed or open as documented) and every relief valve that protects it "
    "(isolated or in service as documented), and `limits` with the design pressure and an estimated burst pressure with their "
    "sources. Where the data sheet gives a range or marks a value ILLUSTRATIVE, pick a stated value, say why in assumptions, "
    "and use trapped_capacity and run_trapped at other values to show how the answer depends on it. Report measured vs "
    "simulated for every measured value you have (at least the start pressure). Then call submit_model. Spec: " + trapped.SPEC_HELP
)

SUBMIT_MODEL_GRID = submit("submit_model", "The transmission-grid model you built and calibrated.", {
    "label": {"type": "string", "description": "label of the calibrated run_grid run (the model)"},
    "mapping": ARR({"tag": S, "modelled_as": S, "source": S}),
    "calibration": ARR({"item": S, "measured": S, "simulated": S, "source": S}),
    "assumptions": {"type": "array", "items": S},
}, ["label", "mapping", "calibration"])

BUILD_GRID = (
    "You are building an AC load-flow model of a transmission grid area with pandapower. Do not use run_process. Read the "
    "one-line diagram and the data sheet. Build the network with run_grid: every substation busbar named on the drawing as "
    "a bus (a substation operated with split busbars is two buses joined by a bus coupler switch in its documented state), "
    "every line and transformer with the drawing's name as id, line lengths and per-km parameters from the data sheet, "
    "documented injections as gens, and the wider grid as the documented grid equivalents. Put every protection setting "
    "the data sheet cites (trip, alarm or maximum accepted current) in `limits` with where it acts and its source. "
    "Calibrate against EVERY flow the data sheet gives for the documented moment and report measured vs simulated; the "
    "only quantity you may tune is the one the data sheet names as unknown. Then call submit_model. A deterministic review "
    "checks that submit: if it returns blocking findings, fix the model and call submit_model once more. If the spec "
    "cannot express something, call report_gap instead of approximating. The model you submit is the system as operated "
    "at the documented moment; later switching actions must be expressed as path changes, not by editing the model."
)

RO_MASS_TOL = 0.02  # feed vs product + concentrate + pretreatment losses
RO_PRESSURE_TOL_BAR = 0.05

ANSWER = submit("answer", "Final answer, shown on the P&ID and as calc cards (not as chat).", {
    "headline": {"type": "string", "description": "the answer in at most 8 plain words, e.g. 'No - cooler H1007 limits at +17%'"},
    "summary": {"type": "string", "description": "at most 2 plain sentences with the key numbers and their sources"},
    "cards": ARR({"title": S, "result": {"type": "string", "description": "headline value(s) with units, at most 14 words"},
                  "inputs": ARR({"name": S, "value": S, "source": S,
                                 "basis": {"type": "string", "enum": ["documented", "measured", "computed", "assumed"],
                                           "description": "documented = drawing/datasheet/report value; measured = operating or field data; "
                                                          "computed = a logged simulator run; assumed = engineering judgement"}}),
                  "runs": {"type": "array", "items": S},
                  "assumptions": {"type": "array", "items": S},
                  "status": {"type": "string", "enum": ["ok", "warn", "fail", "info"]}}),
    "field_checks": ARR({"item": {"type": "string", "description": "the missing or assumed value"},
                         "where": {"type": "string", "description": "where and how to measure or confirm it"},
                         "changes": {"type": "string", "description": "which conclusion would change, and at what value"}}),
    "highlights": ARR({"tag": {"type": "string", "description": "equipment tag on the P&ID, e.g. H1007"}, "text": S,
                       "severity": {"type": "string", "enum": ["ok", "warn", "fail", "info"]}}),
    "proposals": {"type": "array", "description": "fixes, each a change to the model; the workspace re-solves it in DWSIM before "
                  "the engineer can accept it. " + CHANGE_HELP, "items": {"type": "object", "properties": {
                      "title": S, "tag": S,
                      "changes": ARR(CHANGE),
                      "cost_class": {"type": "string", "enum": ["no capex", "<$100k", "$100k-$1M", ">$1M"]},
                      "why": S}}},
}, ["headline", "summary", "cards"])


def limit_changes(p):
    """Paths in a proposal that edit the limits themselves rather than the plant. Installed exchanger area is physical
    (patch moves its area limit with it), so only explicit limits.* edits count."""
    return [c["path"] for c in p.get("changes") or [] if isinstance(c, dict) and str(c.get("path", "")).startswith("limits.")]


CONNECTION_FIELDS = {"in", "out", "cold", "hot", "heating", "vapor", "liquid", "product", "reject", "distillate", "bottoms"}
ROUTING_UNITS = {"mixer", "splitter", "recycle"}
_STRUCTURAL_UNIT_FIELDS = {"id", "type", "kind", *CONNECTION_FIELDS}
_PHYSICAL_UNIT_FIELDS = {"U_W_m2K", "area_m2", "eff_pct", "efficiency", "cv_rated", "kv_rated", "rangeability",
                         "diameter_m", "id_mm", "dn_mm", "length_m", "roughness_mm", "stages", "feed_stage"}


def added_equipment(changes):
    """Physical units introduced by a proposal, retained as evidence instead of being hidden in a dotted diff."""
    return [{"id": c["add_unit"].get("id"), "type": c["add_unit"].get("type"), "limits": c.get("limits") or {},
             "rating_source": c.get("rating_source"), "status": "new equipment, rating to confirm"}
            for c in changes or [] if isinstance(c, dict) and isinstance(c.get("add_unit"), dict) and
            c["add_unit"].get("type") not in ROUTING_UNITS]


def change_errors(spec, changes, require_evidence=True):
    """Validate the structural proposal boundary before it reaches the simulator."""
    if ro_changes.is_ro(spec):
        return ro_changes.change_errors(spec, changes, require_evidence)
    if grid.is_grid(spec):
        return grid.change_errors(spec, changes, require_evidence)
    existing = {u.get("id") for u in spec.get("units") or []}
    additions = [c.get("add_unit") for c in changes or [] if isinstance(c, dict) and c.get("add_unit") is not None]
    new_ids = [u.get("id") for u in additions if isinstance(u, dict) and isinstance(u.get("id"), str)]
    known, errors = existing | set(new_ids), []
    for i, c in enumerate(changes or []):
        if not isinstance(c, dict):
            errors.append(f"change {i + 1} is not an object")
            continue
        forms = sum(k in c for k in ("path", "add_unit", "reroute", "remove_unit", "bypass"))
        if forms != 1:
            errors.append(f"change {i + 1} must contain exactly one of path, add_unit, reroute, remove_unit or bypass")
            continue
        if "remove_unit" in c or "bypass" in c:  # taking equipment out is a physical change: it needs a stated reason
            uid = c.get("remove_unit") if "remove_unit" in c else (c["bypass"] or {}).get("unit") if isinstance(c["bypass"], dict) else c["bypass"]
            if uid not in existing:
                errors.append(f"change {i + 1} removes or bypasses unknown unit {uid}")
            elif require_evidence and not str(c.get("physical_change") or "").strip():
                errors.append(f"change {i + 1} removing or bypassing {uid} needs physical_change (what is done on site)")
            continue
        if "path" in c:
            try:
                kind, oid, field = c["path"].split(".", 2)
            except (AttributeError, ValueError):
                errors.append(f"change {i + 1} has a bad path")
                continue
            if kind not in ("units", "feeds", "limits") or "value" not in c:
                errors.append(f"change {i + 1} has a bad path or no value")
            elif kind == "units" and oid not in known:
                errors.append(f"change {i + 1} names unknown unit {oid}")
            elif kind == "feeds" and oid not in (spec.get("feeds") or {}):
                errors.append(f"change {i + 1} names unknown feed {oid}")
            elif kind == "units" and field in _STRUCTURAL_UNIT_FIELDS:
                errors.append(f"change {i + 1} cannot edit existing unit structure {oid}.{field}; use reroute or add_unit")
            elif require_evidence and kind == "units" and (field in _PHYSICAL_UNIT_FIELDS or
                                      field.startswith(("max_", "min_", "rated_")) or "curve" in field.casefold()):
                if not str(c.get("physical_change") or "").strip() or not str(c.get("rating_source") or "").strip():
                    errors.append(f"change {i + 1} {oid}.{field} needs physical_change and rating_source")
        elif "add_unit" in c:
            u = c["add_unit"]
            if not isinstance(u, dict) or not isinstance(u.get("id"), str) or not u["id"] or not isinstance(u.get("type"), str) or not u["type"]:
                errors.append(f"change {i + 1} add_unit needs id and type")
                continue
            if u["id"] in existing or new_ids.count(u["id"]) > 1:
                old = (spec.get("limits") or {}).get(u["id"]) or {}
                newer = c.get("limits") if isinstance(c.get("limits"), dict) else {}
                raised = [k for k, val in newer.items()
                          if isinstance(old.get(k), (int, float)) and isinstance(val, (int, float)) and float(val) > float(old[k])]
                if u["id"] in existing and raised:
                    errors.append(f"change {i + 1} cannot raise existing limit {u['id']}.{raised[0]}")
                else:
                    errors.append(f"change {i + 1} cannot add duplicate unit {u['id']}")
            if u["type"] not in ROUTING_UNITS and not c.get("limits"):
                errors.append(f"change {i + 1} add_unit {u['id']} needs its own limits")
            if (u["type"] not in ROUTING_UNITS or c.get("limits")) and not str(c.get("rating_source") or "").strip():
                errors.append(f"change {i + 1} add_unit {u['id']} needs rating_source")
            if not isinstance(c.get("limits", {}), dict):
                errors.append(f"change {i + 1} limits must be an object")
        else:
            r = c["reroute"]
            value = r.get("value") if isinstance(r, dict) else None
            streams = isinstance(value, str) or (isinstance(value, list) and value and all(isinstance(x, str) for x in value))
            if (not isinstance(r, dict) or r.get("unit") not in known or r.get("field") not in CONNECTION_FIELDS or
                    "value" not in r or not streams):
                errors.append(f"change {i + 1} reroute needs a known unit, connection field and value")
    return errors


# Splitter outlet fractions must sum to 1 within this absolute tolerance (0.8333 + 0.1667 is accepted).
FRACTION_SUM_TOL = 1e-3
_PATH_FIELDS = {"path", "value"}
_ADD_FIELDS = {"add_unit", "limits", "rating_source"}
_REROUTE_FIELDS = {"reroute"}
_INLET_PORTS = ("in",)
_OUTLET_PORTS = ("out", "vapor", "liquid", "distillate", "bottoms", "product", "reject")
_PAIR_PORTS = ("cold", "hot", "heating")  # [inlet, outlet]
_STREAM_KEEP = ("T_C", "P_bar", "kg_h", "vapour_frac", "components_kg_h")


def cited_run_labels(proposal, answer=None):
    """Run labels the proposal or the answer cards explicitly cite, in first-seen order."""
    labels = []

    def add(value):
        if isinstance(value, str):
            if value and value not in labels:
                labels.append(value)
        elif isinstance(value, list):
            for item in value:
                add(item)

    if isinstance(proposal, dict):
        add(proposal.get("runs"))
        add(proposal.get("cited_runs"))
        for change in proposal.get("changes") or []:
            if isinstance(change, dict):
                add(change.get("runs"))
    if isinstance(answer, dict):
        for card in answer.get("cards") or []:
            if isinstance(card, dict):
                add(card.get("runs"))
    return labels


def _split_change(change, index):
    """One canonical object per path, add_unit or reroute. add_unit plus reroute splits; anything else combined is an error."""
    forms = [key for key in ("path", "add_unit", "reroute") if key in change]
    number = index + 1
    if len(forms) <= 1:
        return [change], [], []
    if set(forms) != {"add_unit", "reroute"}:
        joined = " and ".join(forms)
        return [], [], [f"change {number} combines {joined}; only add_unit plus reroute can be split"]
    add, route, notes = {}, {}, []
    for key, value in change.items():
        if key in _ADD_FIELDS:
            add[key] = copy.deepcopy(value)
        elif key in _REROUTE_FIELDS or key == "from":
            route[key] = copy.deepcopy(value)
        elif key in _PATH_FIELDS:
            return [], [], [f"change {number} field {key} belongs on a path change and cannot be placed on add_unit plus reroute"]
        else:
            add[key] = copy.deepcopy(value)
            notes.append(f"kept extra field {key} on the add_unit change")
    unit = add.get("add_unit") if isinstance(add.get("add_unit"), dict) else {}
    reroute = route.get("reroute") if isinstance(route.get("reroute"), dict) else {}
    notes.insert(0, f"split change {number} into add_unit {unit.get('id')} then reroute {reroute.get('unit')}.{reroute.get('field')}")
    return [add, route], notes, []


def _fractions_close(a, b):
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)) or len(a) != len(b):
        return False
    try:
        return all(abs(float(x) - float(y)) <= FRACTION_SUM_TOL for x, y in zip(a, b))
    except (TypeError, ValueError):
        return False


def _fraction_problem(unit):
    """None when fractions are present and valid, 'missing' when they can be recovered, otherwise an error."""
    sid = unit.get("id")
    fractions = unit.get("fractions")
    outlets = unit.get("out")
    n_out = len(outlets) if isinstance(outlets, list) else None
    if fractions is None:
        return "missing"
    if not isinstance(fractions, (list, tuple)) or n_out is None or len(fractions) != n_out:
        return f"splitter {sid} fractions length must match out ({n_out})"
    try:
        numbers = [float(x) for x in fractions]
    except (TypeError, ValueError):
        return f"splitter {sid} fractions must be numbers"
    if any(x < 0 for x in numbers):
        return f"splitter {sid} fractions must be non-negative"
    if abs(sum(numbers) - 1.0) > FRACTION_SUM_TOL:
        return f"splitter {sid} fractions must sum to 1 within {FRACTION_SUM_TOL:g}"
    return None


def _recover_fractions(unit_id, runs, cited):
    """Fractions from cited logged runs, only when every cited occurrence of this id agrees."""
    found = []
    for label in cited:
        run = runs.get(label) if isinstance(runs, dict) else None
        if not isinstance(run, dict):
            continue
        for unit in (run.get("spec") or {}).get("units") or []:
            if isinstance(unit, dict) and unit.get("id") == unit_id and isinstance(unit.get("fractions"), list):
                found.append((label, unit["fractions"]))
    if not found:
        return None, None, f"splitter {unit_id} is missing fractions and no cited run supplies them"
    first = found[0][1]
    labels = []
    for label, fractions in found:
        if not _fractions_close(fractions, first):
            return None, None, f"splitter {unit_id} fractions are ambiguous across cited runs ({label} disagrees)"
        if label not in labels:
            labels.append(label)
    return [float(x) for x in first], ", ".join(labels), None


def _apply_splitter_fractions(changes, runs, cited):
    notes, errors = [], []
    for change in changes:
        unit = change.get("add_unit") if isinstance(change, dict) else None
        if not isinstance(unit, dict) or unit.get("type") != "splitter":
            continue
        problem = _fraction_problem(unit)
        if problem is None:
            continue
        if problem != "missing":
            errors.append(problem)
            continue
        recovered, label, err = _recover_fractions(unit.get("id"), runs, cited)
        if err:
            errors.append(err)
            continue
        problem = _fraction_problem({**unit, "fractions": recovered})
        if problem:
            errors.append(problem)
            continue
        unit["fractions"] = recovered
        change["fractions_source"] = label
        notes.append(f"recovered fractions for {unit.get('id')} from run {label}")
    return notes, errors


def normalize_proposal(proposal, spec, runs=None, cited=None):
    """Canonical changes before verify(): one of path, add_unit, reroute per object. Mutates the proposal only when complete.

    Returns errors and leaves `changes` untouched when a field cannot be placed, fractions are missing, or cited runs disagree.
    `normalized_changes` is a deterministic audit list (empty when nothing was rewritten)."""
    if not isinstance(proposal, dict):
        return ["proposal is not an object"]
    original = proposal.get("changes") or []
    if not isinstance(original, list):
        return ["changes must be a list"]
    labels = cited_run_labels(proposal) if cited is None else list(cited)
    built, notes, errors = [], [], []
    for index, change in enumerate(original):
        if not isinstance(change, dict):
            built.append(change)
            continue
        parts, part_notes, part_errors = _split_change(change, index)
        built.extend(parts)
        notes.extend(part_notes)
        errors.extend(part_errors)
    if errors:
        return errors
    mutable = []
    for change in built:
        unit = change.get("add_unit") if isinstance(change, dict) else None
        if isinstance(unit, dict) and unit.get("type") == "splitter" and unit.get("fractions") is None:
            mutable.append(copy.deepcopy(change))
        else:
            mutable.append(change)
    frac_notes, frac_errors = _apply_splitter_fractions(mutable, runs or {}, labels)
    if frac_errors:
        return frac_errors
    notes.extend(frac_notes)
    prior = proposal.get("normalized_changes")
    kept = list(prior) if isinstance(prior, list) else []
    if mutable == original and not notes:
        proposal["normalized_changes"] = kept
        return []
    proposal["changes"] = mutable
    proposal["normalized_changes"] = kept + notes
    return []


def _assumptions(proposal):
    found = proposal.get("assumptions") if isinstance(proposal, dict) else None
    return list(found) if isinstance(found, list) else []


def _simulator_name(cfg):
    engine = (cfg or {}).get("engine")
    return engine if engine in ("watertap", "pandapower") else "dwsim"


def _is_grid(cfg):
    return _simulator_name(cfg) == "pandapower"


def _is_watertap(cfg):
    return _simulator_name(cfg) == "watertap"


def _is_trapped(cfg):
    """A blocked-in liquefied-gas segment (plantagent/trapped.py): DWSIM thermo along an isochore, time on the slider."""
    return (cfg or {}).get("engine") == "trapped"


def _trapped_spec(cfg, spec):
    """The case's time base (throughput.base hours) is the one the slider shows: scale x that, whatever hours the model set."""
    base = ((cfg or {}).get("throughput") or {}).get("base")
    return {**spec, "hours": float(base)} if base else spec


def _ro_stages(spec):
    stages = (spec or {}).get("stages") or (spec or {}).get("stage") or []
    return [stages] if isinstance(stages, dict) else list(stages)


def _ro_feed(spec):
    return (spec or {}).get("feed") or (spec or {}).get("intake") or {}


def _ro_assumptions_text(assumptions):
    return " ".join(str(a) for a in (assumptions or [])).casefold()


def _finite(x):
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def _fraction_warnings(proposal):
    return [note for note in (proposal.get("normalized_changes") or [])
            if isinstance(note, str) and note.startswith("recovered fractions")]


def _stream_names(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _inlets_outlets(unit):
    inlets, outlets = [], []
    for key in _INLET_PORTS:
        inlets += _stream_names(unit.get(key))
    for key in _OUTLET_PORTS:
        outlets += _stream_names(unit.get(key))
    for key in _PAIR_PORTS:
        pair = unit.get(key)
        if isinstance(pair, list) and len(pair) >= 2:
            if isinstance(pair[0], str):
                inlets.append(pair[0])
            if isinstance(pair[1], str):
                outlets.append(pair[1])
    return inlets, outlets


def _downstream_units(spec, seeds):
    """Unit ids reachable downstream of seeds, seeds included. Pair ports are [inlet, outlet]."""
    consumes, produces = {}, {}
    for unit in spec.get("units") or []:
        if not isinstance(unit, dict) or not unit.get("id"):
            continue
        inlets, outlets = _inlets_outlets(unit)
        for stream in inlets:
            consumes.setdefault(stream, []).append(unit["id"])
        for stream in outlets:
            produces.setdefault(stream, []).append(unit["id"])
    graph = {}
    for stream, sources in produces.items():
        for source in sources:
            for dest in consumes.get(stream, []):
                if dest != source:
                    graph.setdefault(source, set()).add(dest)
    seen, stack = set(), [seed for seed in seeds if seed]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, ()))
    return seen


def _compact_stream(sid, raw):
    row = {"id": sid}
    if isinstance(raw, dict):
        for key in _STREAM_KEEP:
            if key in raw:
                row[key] = raw[key]
        for key, value in raw.items():
            if key not in row and "component" in key:
                row[key] = value
    return row


def _blank_calculation(proposal, target, simulator, errors):
    return {"target_scale": target, "capacity_multiple_before": None, "capacity_multiple_after": None,
            "limited_by_before": None, "limited_by_after": None, "checks": [], "units": {}, "streams": [],
            "new_equipment": [], "assumptions": _assumptions(proposal), "simulator": simulator,
            "errors": list(errors or []), "warnings": _fraction_warnings(proposal)}


def _reject_proposal(proposal, target, why, new, simulator, errors=None):
    return {"verified": False, "fixes": proposal.get("tag") if isinstance(proposal, dict) else None, "still_over": [],
            "breaks": [], "capacity_multiple": None, "limited_by": None, "reaches_target": False,
            "over_limits_at_target": [], "target_scale": target, "new_equipment": new, "unverified_reason": why,
            "calculation": _blank_calculation(proposal, target, simulator, errors if errors is not None else [why])}


def _direct_units(proposal):
    direct = set()
    tag = proposal.get("tag") if isinstance(proposal, dict) else None
    if isinstance(tag, str) and tag:
        direct.add(tag)
    for change in (proposal.get("changes") or []) if isinstance(proposal, dict) else []:
        if not isinstance(change, dict):
            continue
        if change.get("path"):
            parts = str(change["path"]).split(".", 2)
            if len(parts) >= 2 and parts[0] == "units":
                direct.add(parts[1])
        elif isinstance(change.get("add_unit"), dict) and change["add_unit"].get("id"):
            direct.add(change["add_unit"]["id"])
        elif isinstance(change.get("reroute"), dict) and change["reroute"].get("unit"):
            direct.add(change["reroute"]["unit"])
    return direct


def _calculation(proposal, target, before_cap, after_cap, before_map, solved, spec, new, simulator):
    """Compact record of the solve that verify() actually ran. Capacity fields stay None when the solver omitted them."""
    downstream = _downstream_units(spec, _direct_units(proposal))
    units_res = solved.get("units") or {}
    streams_res = solved.get("streams") or {}
    checks = []
    for check in solved.get("checks") or []:
        if not isinstance(check, dict):
            continue
        cid, name = check.get("id"), check.get("check")
        key = (cid, name)
        before_u = before_map.get(key)
        changed = "utilisation" in check and (key not in before_map or before_map[key] != check.get("utilisation"))
        if cid not in downstream and not changed:
            continue
        checks.append({"id": cid, "check": name, "before": before_u, "after": check.get("utilisation"),
                       "value": check.get("value"), "limit": check.get("limit"), "unit": check.get("unit")})
    interest = set(downstream)
    for check in checks:
        if check.get("id"):
            interest.add(check["id"])
    stream_ids, seen = [], set()
    for unit in spec.get("units") or []:
        if not isinstance(unit, dict) or unit.get("id") not in interest:
            continue
        inlets, outlets = _inlets_outlets(unit)
        for sid in inlets + outlets:
            if sid not in seen:
                seen.add(sid)
                stream_ids.append(sid)
    return {"target_scale": target,
            "capacity_multiple_before": before_cap.get("capacity_multiple") if isinstance(before_cap, dict) else None,
            "capacity_multiple_after": after_cap.get("capacity_multiple") if isinstance(after_cap, dict) else None,
            "limited_by_before": before_cap.get("limited_by") if isinstance(before_cap, dict) else None,
            "limited_by_after": after_cap.get("limited_by") if isinstance(after_cap, dict) else None,
            "checks": checks,
            "units": {uid: copy.deepcopy(units_res[uid]) for uid in sorted(interest) if uid in units_res},
            "streams": [_compact_stream(sid, streams_res.get(sid)) for sid in stream_ids if sid in streams_res],
            "new_equipment": [{"id": item.get("id"), "type": item.get("type"),
                               "operating_point": _operating_point(spec, units_res, streams_res, item.get("id")),
                               "limits": item.get("limits") or {}, "rating_source": item.get("rating_source"),
                               "status": item.get("status")} for item in new],
            "assumptions": _assumptions(proposal), "simulator": simulator,
            "errors": list(solved.get("errors") or []), "warnings": _fraction_warnings(proposal)}


class _LazyLog:
    """A log file opened on first write, so a workspace that only reads (web views, tests) leaves no empty session dir."""
    def __init__(self, path):
        self.path, self.f = path, None

    def write(self, text):
        if self.f is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.f = self.path.open("w")
        self.f.write(text)

    def flush(self):
        if self.f:
            self.f.flush()


def _operating_point(spec, units_res, streams_res, uid):
    """Solved result of a new unit plus what the solve knows but the unit row lacks: inlet mass flow, pressure ratio and
    the efficiency the solve used, so data sheets and the pre-FEED gate never print 'to confirm' for a solved value."""
    op = copy.deepcopy(units_res.get(uid)) or {}
    unit = next((u for u in spec.get("units") or [] if isinstance(u, dict) and u.get("id") == uid), {})
    ins, outs = _inlets_outlets(unit) if unit else ([], [])
    s_in = streams_res.get(ins[0]) if len(ins) == 1 else None
    s_out = streams_res.get(outs[0]) if len(outs) == 1 else None
    if s_in and s_in.get("kg_h") is not None:
        op.setdefault("kg_h", s_in["kg_h"])
    if s_in and s_out and s_in.get("P_bar") and s_out.get("P_bar") and unit.get("type") in ("compressor", "pump"):
        op.setdefault("pressure_ratio", s_out["P_bar"] / s_in["P_bar"])
    if unit.get("eff_pct") is not None or unit.get("type") in ("compressor", "pump"):
        op.setdefault("eff_pct", unit.get("eff_pct", 75 if unit.get("type") == "compressor" else 70))  # process.py defaults
    return op


_NUM = re.compile(r"(?<![\w.-])(-?\d[\d,]*\.?\d*)\s*(t/h|MW)?")


def _numbers(obj, out=None):
    """Every number in a solved result or spec, flattened."""
    out = [] if out is None else out
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _numbers(v, out)
    return out


# measurement unit in the text -> the solver fields it can refer to (values in the solver's units: kg/h, kW, °C, bar)
_CAL_FIELDS = [(r"t/h|kg/h", ("kg_h", "vapour_kg_h", "salt_kg_h", "liquid_kg_h")), (r"m3/h|m³/h", ("m3_h",)),
               (r"W/m", ("U_W_m2K",)), (r"\bk?W\b|\bMW\b", ("kW", "duty_kW", "boil_kW", "heating_kW")),
               (r"°C|\bC\b|degC", ("T_C", "brine_T_C", "T_out_C", "condensing_C", "discharge_C")),
               (r"\bbar", ("P_bar", "P_out_bar", "dP_bar")), (r"%", ("eff_pct",)), (r"m2|m²", ("area_m2",))]


def _cal_refs(text, result):
    """(id, field, value) the text points at: a stream or unit id named in it as a whole token, and the field it names
    explicitly (e.g. 'brine_T_C') or, failing that, the fields its measurement unit can mean."""
    text = str(text or "")
    objs = {**(result.get("streams") or {}), **(result.get("units") or {})}
    ids = [i for i in objs if re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", text)]
    refs = []
    for i in ids:
        o = objs[i] if isinstance(objs[i], dict) else {}
        named = [k for k in o if isinstance(o[k], (int, float)) and not isinstance(o[k], bool) and re.search(rf"\b{re.escape(k)}\b", text)]
        fields = named or [f for pat, fs in _CAL_FIELDS if re.search(pat, text) for f in fs if isinstance(o.get(f), (int, float))]
        refs += [(i, f, float(o[f])) for f in dict.fromkeys(fields)]
    return refs


def _made_after(session, built_at, answers_file, model_file):
    """True when a session (dir name YYYYMMDD-HHMMSS) started after the model was built ('at' YYYY-MM-DD HH:MM). Compares
    the recorded times, not file mtimes: a git checkout gives every file the same arbitrary mtime order."""
    import re as _re
    stamp = _re.sub(r"\D", "", str(built_at or ""))[:12]
    if _re.fullmatch(r"\d{8}-\d{6}", session) and len(stamp) == 12:
        return session.replace("-", "")[:12] >= stamp
    return answers_file.stat().st_mtime > model_file.stat().st_mtime  # older records without 'at'


def calibration_check(spec, result, rows):
    """Check the agent's calibration table against the solve instead of trusting its prose. Each row is compared only
    with the exact stream/unit field its simulated text names (no pool of every number in the result): the claimed
    number must be that field's solved value, a value the model was given (feed or unit setting) is an input, not a
    reproduced measurement, and a reproduced output must be within 3 % of the measured value."""
    def first(text):  # the leading number, in the solver's units (t/h and MW are kg/h and kW there)
        m = _NUM.search(str(text or ""))
        if not m:
            return None
        v = float(m.group(1).replace(",", ""))
        return v * 1000 if m.group(2) else v  # only a unit written right after the number converts it
    feeds = spec.get("feeds") or {}
    units = {u.get("id"): u for u in spec.get("units") or []}
    close = lambda a, b, rel: abs(a - b) <= max(abs(b) * rel, 0.051)  # noqa: E731
    out, counts = [], {"reproduced": 0, "input": 0, "differs": 0, "not_in_solve": 0, "no_reference": 0, "no_measurement": 0}
    for row in rows or []:
        m, sv = first(row.get("measured")), first(row.get("simulated"))
        refs = _cal_refs(row.get("simulated"), result)
        hit = min((r for r in refs if sv is not None and close(sv, r[2], 0.005)), key=lambda r: abs(r[2] - sv), default=None)
        ref, value = (f"{hit[0]}.{hit[1]}", hit[2]) if hit else (None, None)
        if not refs:
            check = "no_reference"
        elif hit is None:
            check = "not_in_solve"
        elif any(isinstance(src.get(hit[1]), (int, float)) and close(float(src[hit[1]]), value, 0.002)
                 for src in ((feeds.get(hit[0]) or {}), (units.get(hit[0]) or {}))):
            check = "input"
        elif m is None or not re.match(r"\s*-?\d", str(row.get("measured") or "")):
            check = "no_measurement"
        elif abs(value - m) <= abs(m) * 0.03:
            check = "reproduced"
        else:
            check = "differs"
        counts[check] += 1
        out.append({**row, "check": check, "reference": ref,
                    "deviation_pct": round((value - m) / m * 100, 1) if check in ("reproduced", "differs") and m else None})
    return {"rows": out, "counts": counts}


OPEN_MODEL = "baseten:meta-models/muse-spark-open-1026"
FIELD = {"m3_h": ("flow", "m³/h"), "kg_h": ("flow", "kg/h"), "T_C": ("temperature", "°C"), "P_bar": ("pressure", "bar(a)"),
         "volume_m3": ("working volume", "m³"), "area_m2": ("installed area", "m²"), "U_W_m2K": ("heat-transfer coefficient", "W/m²K"),
         "P_out_bar": ("discharge pressure", "bar(a)"), "T_out_C": ("outlet temperature", "°C"), "duty_kW": ("duty", "kW"),
         "dP_bar": ("pressure rise/drop", "bar"), "eff_pct": ("efficiency", "%"), "kv": ("valve Kv", "")}
KIND = {"pump": "pump", "hx": "heat exchanger", "tank": "tank", "valve": "valve", "heater": "heat load", "cooler": "cooler",
        "compressor": "compressor", "mixer": "junction", "splitter": "branch", "recycle": "loop closure", "column": "column"}


def display_names(spec):
    """Readable names for every unit and stream id, from the flowsheet topology (no model call): a unit keeps its P&ID tag
    with its kind; a stream is named by what produces and consumes it, e.g. 'Utility supply to H1007', 'H1007 to T4750'."""
    units = spec.get("units") or []
    names = {u["id"]: f"{u['id']} {KIND.get(u['type'], u['type'])}" for u in units}
    prod, cons = {}, {}
    for u in units:
        ins = [u["in"]] if isinstance(u.get("in"), str) else list(u.get("in") or [])
        outs = [u["out"]] if isinstance(u.get("out"), str) else list(u.get("out") or [])
        for k in ("cold", "hot"):
            if u.get(k):
                ins.append(u[k][0]); outs.append(u[k][1])
        for k in ("distillate", "bottoms"):
            if u.get(k):
                outs.append(u[k])
        for x in ins:
            cons.setdefault(x, u["id"])
        for x in outs:
            prod.setdefault(x, u["id"])
    feeds = spec.get("feeds") or {}
    hidden = {u["id"]: u for u in units if u["type"] in ("mixer", "splitter", "recycle", "valve")}

    def io(uid, side):
        u = next(x for x in units if x["id"] == uid)
        v = u.get(side)
        return [v] if isinstance(v, str) else list(v or [])

    def up(sid, seen=()):  # nearest real equipment upstream, through junctions, branches and valves
        p = prod.get(sid)
        if p is None or sid in seen:
            return None
        return p if p not in hidden else next((x for x in (up(i, seen + (sid,)) for i in io(p, "in")) if x), None)

    def down(sid, seen=()):
        c = cons.get(sid)
        if c is None or sid in seen:
            return None
        return c if c not in hidden else next((x for x in (down(o, seen + (sid,)) for o in io(c, "out")) if x), None)

    def leaves(sid, seen=()):  # does this stream (or what it becomes) leave the unit for good?
        c = cons.get(sid)
        if c is None:
            return True
        return c in hidden and hidden[c]["type"] != "recycle" and any(leaves(o, seen + (sid,)) for o in io(c, "out") if o not in seen)
    utility = {k for k, f in feeds.items() if f.get("utility")}
    for _ in range(len(units)):  # a utility stays a utility through its own side of exchangers and through valves
        for u in units:
            pairs = [tuple(u[k]) for k in ("cold", "hot") if u.get(k)] + \
                [(i, o) for i in ([u["in"]] if isinstance(u.get("in"), str) else []) for o in ([u["out"]] if isinstance(u.get("out"), str) else [])]
            utility |= {o for i, o in pairs if i in utility}
    for sid in set(prod) | set(cons) | set(feeds):
        a, b = up(sid), down(sid)
        if sid in utility and sid not in feeds and cons.get(sid) is None:
            names[sid] = f"Utility return from {a or 'the unit'}"
            continue
        if sid in feeds:
            names[sid] = f"{'Utility supply' if feeds[sid].get('utility') else 'Feed'} to {b or 'the unit'}"
        elif a and b and a != b:
            names[sid] = f"{a} outlet to {b}"
        elif a and cons.get(sid) is None:
            names[sid] = f"{a} outlet (product leaving the unit)"
        elif a:
            names[sid] = f"{a} outlet"
        elif b:
            names[sid] = f"Stream into {b}"
        else:
            names[sid] = sid
    return names


def model_only_change(spec, c, changes=()):
    """True for model bookkeeping with no field work of its own: an added junction/branch, or a reroute of one."""
    if isinstance(c.get("add_unit"), dict):
        return c["add_unit"].get("type") in ROUTING_UNITS
    if c.get("reroute"):
        uid = c["reroute"].get("unit")
        types = {u.get("id"): u.get("type") for u in spec.get("units") or []}
        types.update({x["add_unit"].get("id"): x["add_unit"].get("type") for x in changes if isinstance(x.get("add_unit"), dict)})
        return types.get(uid) in ROUTING_UNITS
    return False


def describe_change(spec, c, names=None, aliases=None):
    """'H1007 cooling water flow: 20 → 27 m³/h' for a change path; the raw path stays available for traceability.
    `aliases` (case.json model_aliases, P&ID tag → model unit): a heating-side field of a model unit is named by its P&ID tag."""
    names = names or display_names(spec)
    if c.get("add_unit"):
        u, limits = c["add_unit"], c.get("limits") or {}
        if u.get("type") in ROUTING_UNITS:
            return f"Model-only {KIND.get(u.get('type'), u.get('type'))} {u.get('id')} (connects the new tie-in in the model; no item of its own)"
        rating = c.get("rating_source") or "rating not stated"
        if limits.get("max_kg_h") is not None:
            size = f", {limits['max_kg_h'] / 1000:g} t/h suction"
        elif limits.get("max_kW") is not None:
            size = f", {limits['max_kW']:,.0f} kW"
        else:
            size = ""
        return f"Adds {u.get('id')} {KIND.get(u.get('type'), u.get('type'))}{size} (provisional rating: {rating})"
    if c.get("reroute"):
        r, j = c["reroute"], lambda v: " + ".join(map(str, v)) if isinstance(v, list) else str(v)  # noqa: E731
        old = f"{j(c['from'])} → " if c.get("from") is not None else ""
        return f"Re-pipes {names.get(r.get('unit'), r.get('unit'))} {'inlet' if r.get('field') == 'in' else 'outlet' if r.get('field') == 'out' else r.get('field')}" \
               f" to the new tie-in (model streams {old}{j(r.get('value'))})"
    if c.get("remove_unit") is not None or c.get("bypass") is not None:
        uid = c.get("remove_unit") or (c["bypass"].get("unit") if isinstance(c["bypass"], dict) else c["bypass"])
        return f"{'Removes' if c.get('remove_unit') is not None else 'Bypasses'} {names.get(uid, uid)} ({c.get('physical_change') or 'reason not stated'})"
    try:
        kind, oid, field = c["path"].split(".", 2)
    except (KeyError, ValueError):
        return c.get("path", "")
    label, unit = FIELD.get(field, (field.replace("_", " "), ""))
    who = names.get(oid, oid)
    tag = next((t for t, m in (aliases or {}).items() if m == oid), None) if field in ("U_W_m2K", "area_m2") else None
    if tag:
        who = f"{tag} (heating side of {oid} in the model)"
    frm = c.get("from")
    if field == "fractions":
        label, unit = "split (share of flow per outlet)", ""
        fmt = lambda v: " / ".join(f"{float(x) * 100:.1f} %" for x in v) if isinstance(v, list) else str(v)  # noqa: E731
    else:
        fmt = lambda v: f"{v:,.4g}" if isinstance(v, (int, float)) else str(v)  # noqa: E731
    return f"{who} {label}: {fmt(frm) + ' → ' if frm is not None else ''}{fmt(c.get('value'))} {unit}".strip()


def compare_answers(a, b):
    """Where two independent answers agree, deterministically: limiting equipment, proposed changes (same path, values
    within 10 %), DWSIM verification and the verdict. Nothing is chosen; disagreements are for the engineer."""
    agree, disagree = [], []
    lim = lambda x: {h["tag"] for h in x.get("highlights") or [] if h.get("severity") in ("fail", "warn")} | \
        {p.get("tag") for p in x.get("proposals") or [] if p.get("tag")}  # noqa: E731
    la, lb = lim(a), lim(b)
    if la or lb:
        (agree if la == lb else disagree).append(f"limiting equipment: {', '.join(sorted(la)) or 'none'} vs {', '.join(sorted(lb)) or 'none'}")
    def ch(x):
        out = {}
        for p in x.get("proposals") or []:
            for c in p.get("changes") or []:
                if c.get("path"):
                    out[c["path"]] = c.get("value")
                elif c.get("add_unit"):
                    out[f"add_unit.{c['add_unit'].get('id')}"] = json.dumps(
                        {"unit": c["add_unit"], "limits": c.get("limits") or {}, "rating_source": c.get("rating_source")}, sort_keys=True)
                elif c.get("reroute"):
                    r = c["reroute"]
                    out[f"reroute.{r.get('unit')}.{r.get('field')}"] = r.get("value")
        return out
    ca, cb = ch(a), ch(b)
    for path in sorted(ca.keys() | cb.keys()):
        va, vb = ca.get(path), cb.get(path)
        if va is None or vb is None:
            disagree.append(f"{path}: only {'the main model' if vb is None else 'the open model'} changes it")
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)) and abs(va - vb) <= 0.1 * max(abs(va), abs(vb), 1e-9):
            agree.append(f"{path}: {va} vs {vb}")
        else:
            disagree.append(f"{path}: {va} vs {vb}")
    ver = lambda x: {p.get("tag") for p in x.get("proposals") or [] if p.get("verified")}  # noqa: E731
    va, vb = ver(a), ver(b)
    if va or vb:
        (agree if va == vb else disagree).append(f"verified in DWSIM: {', '.join(sorted(va)) or 'none'} vs {', '.join(sorted(vb)) or 'none'}")
    import re as _re

    def energy(x):  # the annual energy saving stated in the answer (MWh), if any
        for txt in [x.get("headline") or "", x.get("summary") or ""] + [c.get("result") or "" for c in x.get("cards") or []]:
            m = _re.search(r"sav\w*[^.;]*?([\d][\d,]*\.?\d*)\s*(MWh|GWh)", txt, _re.I)
            if m:
                return float(m.group(1).replace(",", "")) * (1000 if m.group(2) == "GWh" else 1)
        return None
    ea, eb = energy(a), energy(b)
    if ea and eb:
        (agree if abs(ea - eb) <= 0.1 * max(ea, eb) else disagree).append(f"annual energy saving: {ea:,.0f} vs {eb:,.0f} MWh")

    def reach(x):  # None when the answer proposes no change: the verdict is then in its prose, not compared here
        if (x.get("combined") or {}).get("reaches_target") is not None:
            return bool(x["combined"]["reaches_target"])
        ps = x.get("proposals") or []
        return any(p.get("reaches_target") for p in ps) if ps else None
    ra, rb = reach(a), reach(b)
    if ra is not None and rb is not None:
        (agree if ra == rb else disagree).append(f"reaches the target: {'yes' if ra else 'no'} vs {'yes' if rb else 'no'}")
    return {"agree": agree, "disagree": disagree, "status": "agree" if not disagree else "disagree" if not agree else "partly"}


def read_corrections(orig, conf):
    """What the engineer changed in Muse's read: loops, equipment and connections added, removed or edited."""
    out = []
    lo, lc = {x["name"]: x for x in orig.get("loops", [])}, {x["name"]: x for x in conf.get("loops", [])}
    out += [f"loop added: {n}" for n in lc.keys() - lo.keys()] + [f"loop removed: {n}" for n in lo.keys() - lc.keys()]
    out += [f"loop {n}: {k} {lo[n].get(k)} -> {lc[n].get(k)}" for n in lo.keys() & lc.keys() for k in ("fluid", "supply_C", "return_C")
            if lo[n].get(k) != lc[n].get(k)]
    eo, ec = {x["tag"]: x for x in orig.get("equipment", [])}, {x["tag"]: x for x in conf.get("equipment", [])}
    out += [f"equipment added: {t} ({ec[t]['class']})" for t in ec.keys() - eo.keys()] + [f"equipment removed: {t}" for t in eo.keys() - ec.keys()]
    for t in eo.keys() & ec.keys():
        for k in ("class", "count", "capacity_kW", "flow_gpm"):
            a, b = eo[t].get(k), ec[t].get(k)
            if (a or None) != (b or None) and not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and float(a) == float(b)):
                out.append(f"{t}: {k} {a} -> {b}")
        if sorted(eo[t].get("loops") or []) != sorted(ec[t].get("loops") or []):
            out.append(f"{t}: loops {eo[t].get('loops')} -> {ec[t].get('loops')}")
    key = lambda c: (c["from"], c["to"], c.get("loop") or "")  # noqa: E731
    co, cc = {key(c) for c in orig.get("connections", [])}, {key(c) for c in conf.get("connections", [])}
    out += [f"connection added: {a} -> {b} ({lp})" for a, b, lp in sorted(cc - co)]
    out += [f"connection removed: {a} -> {b} ({lp})" for a, b, lp in sorted(co - cc)]
    return out


def patch(spec, changes):
    """Apply operating changes, added units and connection reroutes to a copy of the process spec."""
    # Proposal evidence is checked by verify(); internal sensitivity and rendering patches use the same mechanics.
    if ro_changes.is_ro(spec):  # WaterTAP RO spec: paths into its blocks, added trains
        return ro_changes.patch(spec, changes)
    if grid.is_grid(spec):  # transmission grid: switching and dispatch paths into its elements
        return grid.patch(spec, changes)
    errors = change_errors(spec, changes, require_evidence=False)
    if errors:
        raise ValueError("; ".join(errors))
    s = copy.deepcopy(spec)
    units = {u["id"]: u for u in s["units"]}
    for c in changes:
        if "remove_unit" in c or "bypass" in c:
            uid = c.get("remove_unit") if "remove_unit" in c else (c["bypass"] or {}).get("unit") if isinstance(c["bypass"], dict) else c["bypass"]
            gone = units.pop(uid)
            s["units"] = [u for u in s["units"] if u["id"] != uid]
            (s.get("limits") or {}).pop(uid, None)
            if "bypass" in c:  # the flow skips the unit: its inlet stream is renamed to its outlet, so checks on both stay
                src, out = gone.get("in"), gone.get("out")
                if not isinstance(src, str) or not isinstance(out, str):
                    raise ValueError(f"bypass {uid}: only a unit with one inlet and one outlet can be bypassed; use remove_unit and reroute")
                for u in s["units"]:
                    for f in CONNECTION_FIELDS:
                        v = u.get(f)
                        if v == src:
                            u[f] = out
                        elif isinstance(v, list):
                            u[f] = [out if x == src else x for x in v]
                if src in (s.get("feeds") or {}):
                    s["feeds"][out] = s["feeds"].pop(src)
                if src in (s.get("limits") or {}):
                    s["limits"].setdefault(out, {}).update(s["limits"].pop(src))
            continue
        if c.get("add_unit"):
            u = copy.deepcopy(c["add_unit"])
            s["units"].append(u)
            units[u["id"]] = u
            if c.get("limits"):
                s.setdefault("limits", {})[u["id"]] = copy.deepcopy(c["limits"])
            continue
        if c.get("reroute"):
            r = c["reroute"]
            units[r["unit"]][r["field"]] = copy.deepcopy(r["value"])
            continue
        kind, oid, field = c["path"].split(".", 2)
        if kind == "units":
            units[oid][field] = c["value"]
            if field == "area_m2" and oid in (s.get("limits") or {}):
                s["limits"][oid]["area_m2"] = c["value"]
        elif kind == "feeds":
            s["feeds"][oid][field] = c["value"]
        elif kind == "limits":
            s.setdefault("limits", {}).setdefault(oid, {})[field] = c["value"]
        else:
            raise ValueError(f"bad path {c['path']}")
    return s


def coverage(pid_ov, spec):
    """Which P&ID equipment-to-equipment connections the model reproduces, and which equipment it leaves out."""
    tags = {e["tag"] for e in pid_ov["equipment"] if e["tag"]}
    units = {u["id"]: u for u in spec.get("units", [])}
    outs, ins = {}, {}
    for u in units.values():
        for k, d in (("in", ins), ("out", outs), ("cold", None), ("hot", None)):
            v = u.get(k)
            if k in ("cold", "hot") and v:
                ins.setdefault(v[0], []).append(u["id"]); outs.setdefault(v[1], []).append(u["id"])
            elif v and d is not None:
                for name in (v if isinstance(v, list) else [v]):
                    d.setdefault(name, []).append(u["id"])
    nxt = {}
    for st, srcs in outs.items():
        for a in srcs:
            nxt.setdefault(a, set()).update(ins.get(st, []))
    for u in units.values():  # a recycle hands its stream on to whoever reads the tear stream
        if u["type"] == "recycle":
            nxt.setdefault(u["id"], set()).update(ins.get(u["out"], []))

    def reaches(a, b):
        seen, todo = set(), [a]
        while todo:
            x = todo.pop()
            for y in nxt.get(x, ()):
                if y == b:
                    return True
                if y not in seen and y not in tags:  # pass through valves, mixers, splitters, recycles only
                    seen.add(y); todo.append(y)
        return False

    tag_of = lambda s: s.split("(")[0]  # noqa: E731
    rows = []
    for c in pid_ov["connections"]:
        a, b = tag_of(c["from"]), tag_of(c["to"])
        if a in tags and b in tags and a != b:
            relief = any("SafetyValve" in v for v in c["inline"])  # a relief path carries no normal flow
            rows.append({"from": a, "to": b, "lines": c["lines"], "relief_path": relief,
                         "modelled": a in units and b in units and reaches(a, b)})
    return {"connections": rows, "missing_connections": [r for r in rows if not r["modelled"] and not r["relief_path"]],
            "missing_equipment": sorted(tags - set(units))}


def _ro_block_items(spec):
    """Documented WaterTAP blocks that coverage understands (not a DWSIM units[] list)."""
    spec = spec or {}
    items, notes, unsupported = [], [], []
    feed = _ro_feed(spec)
    if feed:
        items.append({"id": "feed", "kind": "feed/intake", "modelled": True,
                      "how": "feed specification"})
    for i, block in enumerate(spec.get("pretreatment") or []):
        bid = block.get("id") or f"PT{i + 1}"
        kind = str(block.get("type") or "media_filter").lower()
        if kind in ("chemical", "note", "notes"):
            notes.append({"id": bid, "kind": "pretreatment chemical", "modelled": False,
                          "how": "note only; chemistry is not simulated", "notes": block.get("notes") or ""})
        else:
            items.append({"id": bid, "kind": "pretreatment", "modelled": True,
                          "how": "specified pressure drop and recovery; concentration unchanged"})
    hp = spec.get("hp_pump") or spec.get("pump")
    if hp is not None:
        items.append({"id": (hp or {}).get("id") or "HP", "kind": "HP pump", "modelled": True, "how": "WaterTAP pump"})
    for i, stage in enumerate(_ro_stages(spec)):
        sid = stage.get("id") or f"RO-{i + 1}"
        items.append({"id": sid, "kind": "first-pass stage/train", "modelled": True, "how": "WaterTAP RO stage"})
    erd = spec.get("energy_recovery")
    if erd is not None:
        kind = str((erd or {}).get("type") or "none").lower()
        if kind not in ("", "none", "no"):
            items.append({"id": (erd or {}).get("id") or "ERD", "kind": "energy recovery", "modelled": True,
                          "how": f"WaterTAP {kind}"})
        boost = (erd or {}).get("booster_pump")
        if boost is not None:
            items.append({"id": (boost or {}).get("id") or "booster", "kind": "booster pump", "modelled": True,
                          "how": "WaterTAP booster"})
    second = spec.get("second_pass")
    if second:
        items.append({"id": "second_pass", "kind": "second-pass pump/stage", "modelled": True,
                      "how": "WaterTAP second pass; concentrate recycle to first-pass feed is not closed"})
        unsupported.append("second-pass concentrate recycle to the first-pass feed (concentrate is an outlet)")
    items.append({"id": "permeate", "kind": "product path", "modelled": True, "how": "permeate outlet"})
    items.append({"id": "brine", "kind": "concentrate path", "modelled": True, "how": "concentrate outlet"})
    post = spec.get("posttreatment")
    if post is not None:
        post_note = post if isinstance(post, str) else (post or {}).get("notes") if isinstance(post, dict) else ""
        post_id = (post.get("id") if isinstance(post, dict) else None) or "posttreatment"
        notes.append({"id": post_id, "kind": "post-treatment", "modelled": False,
                      "how": "documented note only; chemistry is not simulated", "notes": post_note or ""})
    if (feed.get("boron_g_L") is not None or any(str(k).lower() in ("b", "boron", "boric")
                                                 for k in (feed.get("ions") or feed.get("ion_table") or {}))):
        needing = list(_ro_stages(spec))
        if second and second.get("stage"):
            needing.append(second["stage"])
        if any(s.get("B_boron_m_per_s") is None for s in needing):
            unsupported.append("boron passage (feed has boron but B_boron_m_per_s is missing on a stage)")
    return items, notes, unsupported


def ro_coverage(pid_ov, spec, mapping=None):
    """Deterministic coverage for a WaterTAP RO spec (not spec['units'])."""
    items, notes, unsupported = _ro_block_items(spec)
    modelled_ids = {row["id"] for row in items}
    mapped = []
    covered_tags = set()
    for row in mapping or []:
        if not isinstance(row, dict):
            continue
        tag, as_ = row.get("tag"), row.get("modelled_as")
        if not tag:
            continue
        covered_tags.add(tag)
        mapped.append({"tag": tag, "modelled_as": as_, "source": row.get("source"),
                       "grouped": as_ in modelled_ids or any(as_ == n["id"] for n in notes),
                       "note_only": any(as_ == n["id"] for n in notes)})
    tags = {e["tag"] for e in (pid_ov or {}).get("equipment") or [] if e.get("tag")}
    missing_equipment = sorted(tags - covered_tags - modelled_ids)
    missing_connections = []
    if pid_ov:
        tag_of = lambda s: str(s).split("(")[0]  # noqa: E731
        known = covered_tags | modelled_ids
        for c in pid_ov.get("connections") or []:
            a, b = tag_of(c.get("from")), tag_of(c.get("to"))
            if a in tags and b in tags and a != b and not (a in known and b in known):
                missing_connections.append({"from": a, "to": b, "lines": c.get("lines") or [],
                                            "relief_path": False, "modelled": False})
    return {"engine": "watertap",
            "modelled": items,
            "mappings": mapped,
            "notes": notes,
            "intentionally_not_simulated": notes,
            "unsupported_physics": unsupported,
            "missing_equipment": missing_equipment,
            "missing_connections": missing_connections,
            "connections": []}


def review_ro(spec, result, pid_ov=None, basis="", mapping=None, assumptions=None):
    """Deterministic WaterTAP model review. Same high-level shape as review_model for the UI."""
    spec, result = spec or {}, result or {}
    findings = []
    assumptions = list(assumptions or [])
    assum_text = _ro_assumptions_text(assumptions)
    failing = bool(spec.get("failing_baseline") or result.get("failing_baseline")
                   or "failing baseline" in assum_text)
    errs = [e for e in result.get("errors") or [] if e]
    if errs:
        findings.append(_finding("block", "solver error", "WaterTAP errors: " + "; ".join(str(e) for e in errs[:6])))
    feed = _ro_feed(spec)
    feed_q = feed.get("flow_m3_h")
    if not _finite(feed_q) or float(feed_q) <= 0:
        findings.append(_finding("block", "feed flow", "Feed flow_m3_h must be a positive number."))
    streams = result.get("streams") or {}
    permeate = streams.get("permeate") or {}
    brine = streams.get("brine") or {}
    scale = float(result.get("scale") or 1.0)
    raw = float(feed_q) * scale if _finite(feed_q) else None
    if raw is None and _finite((streams.get("intake") or {}).get("flow_m3_h")):
        raw = float(streams["intake"]["flow_m3_h"])
    # Flow into the RO after pretreatment: HP suction, else raw reduced by declared recoveries.
    q_ro = (streams.get("hp_suction") or {}).get("flow_m3_h")
    if not _finite(q_ro) and _finite(raw):
        q_ro = raw
        for block in spec.get("pretreatment") or []:
            kind = str(block.get("type") or "").lower()
            if kind in ("chemical", "note", "notes"):
                continue
            if block.get("recovery") is not None:
                q_ro *= float(block["recovery"])
    pret_loss = (float(raw) - float(q_ro)) if _finite(raw) and _finite(q_ro) else 0.0
    q_p, q_b = permeate.get("flow_m3_h"), brine.get("flow_m3_h")
    q_sp = (streams.get("second_pass_concentrate") or {}).get("flow_m3_h") or 0.0
    if _finite(raw) and _finite(q_p) and _finite(q_b):
        out = float(q_p) + float(q_b) + (float(q_sp) if _finite(q_sp) else 0.0) + float(pret_loss)
        gap = float(raw) - out
        frac = abs(gap) / max(float(raw), 1e-9)
        if frac > RO_MASS_TOL:
            findings.append(_finding(
                "block", "mass balance",
                f"Feed {raw:g} m3/h vs permeate {q_p:g} + concentrate {q_b:g}"
                f" + second-pass concentrate {(q_sp if _finite(q_sp) else 0):g} + pretreatment loss {pret_loss:g} "
                f"(imbalance {gap:g} m3/h, {frac:.1%}; tolerance {RO_MASS_TOL:.0%})."))
    recovery = result.get("recovery")
    if _finite(recovery) and _finite(q_p) and _finite(raw) and float(raw) > 0:
        expected = float(q_p) / float(raw)
        if abs(float(recovery) - expected) > max(1e-3, RO_MASS_TOL):
            findings.append(_finding(
                "block", "recovery inconsistent",
                f"Reported recovery {float(recovery):.5f} vs permeate/feed {expected:.5f}."))
    # Pressures: HP discharge at or above stage feed; within documented maxima.
    hp_out = (streams.get("hp_discharge") or {}).get("P_bar")
    for stage in result.get("stages") or []:
        pin = stage.get("feed_pressure_bar")
        if _finite(hp_out) and _finite(pin) and float(pin) > float(hp_out) + RO_PRESSURE_TOL_BAR:
            findings.append(_finding(
                "block", "pressure order",
                f"Stage {stage.get('id')} feed {pin} bar exceeds HP discharge {hp_out} bar.",
                [stage.get("id")]))
    for stage in _ro_stages(spec):
        lim = stage.get("max_feed_pressure_bar")
        got = next((s.get("feed_pressure_bar") for s in result.get("stages") or []
                    if s.get("id") == stage.get("id")), None)
        if lim is not None and _finite(got) and float(got) > float(lim) + RO_PRESSURE_TOL_BAR and not failing:
            findings.append(_finding(
                "block", "pressure above maximum",
                f"{stage.get('id')} feed {got} bar above max {lim} bar.", [stage.get("id")]))
    sec = result.get("sec_kWh_m3")
    if result and not errs:
        if not _finite(sec) or float(sec) <= 0:
            findings.append(_finding("block", "SEC", f"Specific energy must be finite and positive; got {sec!r}."))
        pumps = result.get("pumps_kW") or {}
        if pumps and not any(_finite(v) and float(v) > 0 for v in pumps.values()):
            findings.append(_finding("block", "pump power", f"Pump powers must be finite and positive; got {pumps!r}."))
        tds = result.get("permeate_TDS_g_L")
        if tds is None:
            tds = permeate.get("TDS_g_L")
        if not _finite(tds):
            findings.append(_finding("block", "product TDS", f"Product TDS must be finite; got {tds!r}."))
    configured = [s.get("id") or f"RO-{i + 1}" for i, s in enumerate(_ro_stages(spec))]
    got_stages = {s.get("id") for s in result.get("stages") or [] if isinstance(s, dict)}
    for sid in configured:
        if result and not errs and sid not in got_stages:
            findings.append(_finding("block", "stage missing", f"Configured stage {sid} produced no result.", [sid]))
    for c in result.get("checks") or []:
        if not isinstance(c, dict):
            continue
        if not _finite(c.get("value")) or not _finite(c.get("limit")) or not _finite(c.get("utilisation")):
            findings.append(_finding(
                "block", "check not finite",
                f"{c.get('id')} {c.get('check')} has non-finite value/limit/utilisation.",
                [c.get("id")] if c.get("id") else None))
        elif float(c["utilisation"]) > 1.0:
            findings.append(_finding(
                "warn" if failing else "block", "failing-baseline limit" if failing else "check over 100%",
                f"{c.get('id')} {c.get('check')} utilisation is {c['utilisation']} at the design condition."
                + (" This is retained as a documented failing baseline, not a passing design." if failing else ""),
                [c.get("id")] if c.get("id") else None))
    boron = result.get("boron")
    not_mod = " ".join(str(x) for x in result.get("not_modelled") or []).casefold()
    feed_boron = feed.get("boron_g_L") is not None or any(
        str(k).lower() in ("b", "boron", "boric") for k in (feed.get("ions") or feed.get("ion_table") or {}))
    if (spec.get("target_boron_g_L") is not None or feed_boron) and (boron == "not modelled" or "boron" in not_mod):
        findings.append(_finding(
            "warn", "boron not modelled",
            "Boron is not modelled (missing B_boron_m_per_s or boron is absent from the solve). "
            "Do not invent a boron value; report_gap if a boron limit is required."))
    if "second pass" not in assum_text and "second-pass" not in assum_text and "2nd pass" not in assum_text:
        findings.append(_finding(
            "warn", "second-pass assumption",
            "State explicitly whether a second pass is modelled, partial/full, and that concentrate recycle is or is not closed."))
    if not any(k in assum_text for k in ("one train", "one-train", "train out", "trains online", "n+1", "availability")):
        findings.append(_finding(
            "warn", "train availability",
            "State the one-train-out / trains-online availability assumption explicitly."))
    findings.sort(key=lambda f: (0 if f["severity"] == "block" else 1, f["check"], f["evidence"]))
    status = "model needs review" if any(f["severity"] == "block" for f in findings) else "ok"
    return {"status": status, "findings": findings,
            "blocking": sum(f["severity"] == "block" for f in findings),
            "energy": {"method": "watertap", "tolerance": RO_MASS_TOL, "note": "RO mass/volume balance on m3/h streams."}}


# process.run does not return stream enthalpy. The smallest addition that closes the flowsheet is one number per stream:
# enthalpy_kJ_kg (specific enthalpy, kJ/kg) inside each stream of the result. Until that field exists, review_model checks
# evaporator heating-versus-boil-up duties instead of sum(m*h) + duties.
ENTHALPY_FIELD = "enthalpy_kJ_kg"
_ENTHALPY_KEYS = (ENTHALPY_FIELD, "H_kJ_kg")
ENERGY_TOL = 0.02  # same closure band the evaporator limit uses
ENERGY_BLOCK = 0.10
_LINE_TOKEN = re.compile(r"(?<!\d)(\d{3,6})(?!\d)")
_HEAT = {"hx", "heater", "cooler", "evaporator"}
_PID_QUANTITY = {"DesignHeatTransferArea": "area", "DesignVolumeFlowRate": "flow", "DesignShaftPower": "power",
                 "DesignHeatFlowRate": "duty", "NominalCapacity(Volume)": "volume"}
_SHEET_VALUE = {
    "area": re.compile(r"([\d][\d,]*(?:\.\d+)?)\s*m(?:2|²)\b", re.I),
    "flow": re.compile(r"([\d][\d,]*(?:\.\d+)?)\s*m(?:3|³)\s*/\s*h\b", re.I),
    "volume": re.compile(r"([\d][\d,]*(?:\.\d+)?)\s*m(?:3|³)(?!\s*/)", re.I),
    "power": re.compile(r"([\d][\d,]*(?:\.\d+)?)\s*kW\b", re.I),
    "duty": re.compile(r"([\d][\d,]*(?:\.\d+)?)\s*kW\b", re.I),
}


def load_gaps(path):
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else []


def record_gap(path, what, why, needed, phase=None):
    """Append one capability gap. `what`, `why` and `needed` are required; nothing is written if one is blank."""
    what, why, needed = (str(what or "").strip(), str(why or "").strip(), str(needed or "").strip())
    if not what or not why or not needed:
        return {"error": "report_gap needs what, why and needed"}
    path = Path(path)
    gaps = load_gaps(path)
    gap = {"what": what, "why": why, "needed": needed, "phase": phase, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    gaps.append(gap)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(gaps, indent=1) + "\n")
    return {"saved": True, "n": len(gaps), "gap": gap}


def collect_gaps(root):
    """Every gap saved under runs/ws/<case>/gaps.json, one row per gap, for `python -m plantagent.plant --gaps`."""
    root = Path(root)
    out = []
    if not root.exists():
        return out
    for f in sorted(root.glob("*/gaps.json")):
        for g in load_gaps(f):
            if isinstance(g, dict):
                out.append({"case": f.parent.name, **g})
    return out


def _finding(severity, check, evidence, items=None):
    f = {"severity": severity, "check": check, "evidence": evidence[:500]}
    if items:
        f["items"] = list(dict.fromkeys(items))
    return f


def _ports(u):
    ins, outs = [], []
    for key, bucket in (("in", ins), ("out", outs)):
        v = u.get(key)
        if isinstance(v, str):
            bucket.append(v)
        elif isinstance(v, list):
            bucket.extend(x for x in v if isinstance(x, str))
    for key in ("cold", "hot", "heating"):
        v = u.get(key)
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            ins.append(v[0])
            outs.append(v[1])
    for key in ("vapor", "liquid", "distillate", "bottoms", "product", "reject"):
        if isinstance(u.get(key), str):
            outs.append(u[key])
    return ins, outs


def _duty_inlets(u):
    if u.get("type") == "hx" and u.get("hot") and u.get("cold"):
        return [u["hot"][0], u["cold"][0]]
    if u.get("type") in ("heater", "cooler") and isinstance(u.get("in"), str):
        return [u["in"]]
    if u.get("type") == "evaporator" and u.get("heating"):
        return [u["heating"][0]]
    return []


def _tag_role(uid, tag):
    if uid == tag:
        return "exact"
    if not uid.startswith(tag) or len(uid) == len(tag):
        return None
    rest = uid[len(tag):]
    if re.fullmatch(r"[A-Z]", rest) or re.fullmatch(r"[-_/][A-Z0-9]", rest):
        return "parallel"  # C-101A, C-101-B: the P&ID count, drawn as one tag
    return "extra"


def _connections(pid_ov, spec):
    try:
        return coverage(pid_ov, spec)["connections"]
    except (KeyError, TypeError, AttributeError):
        rows = []
        for c in (pid_ov or {}).get("connections") or []:
            rows.append({"from": str(c.get("from") or "").split("(")[0], "to": str(c.get("to") or "").split("(")[0],
                         "lines": [str(x) for x in c.get("lines") or [] if x], "relief_path": False})
        return rows


def _pid_number(value):
    m = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(value))
    return float(m.group(0).replace(",", "")) if m else None


def _sheet_numbers(basis, tag, quantity):
    rx, out = _SHEET_VALUE[quantity], []
    for line in (basis or "").splitlines():
        if not re.search(rf"(?<![A-Za-z0-9]){re.escape(tag)}(?![A-Za-z0-9])", line):
            continue
        if quantity == "power" and not re.search(r"power|motor|shaft|kW", line, re.I):
            continue
        if quantity == "duty" and not re.search(r"duty|heat|kW", line, re.I):
            continue
        for m in rx.finditer(line):
            out.append((float(m.group(1).replace(",", "")), line.strip()))
    return out


def _source_conflicts(pid_ov, basis):
    findings = []
    for e in (pid_ov or {}).get("equipment") or []:
        tag = e.get("tag")
        if not tag:
            continue
        for attr, quantity in _PID_QUANTITY.items():
            pid_v = _pid_number((e.get("design") or {}).get(attr))
            if pid_v is None:
                continue
            got = _sheet_numbers(basis, tag, quantity)
            if not got:
                continue
            if any(abs(v - pid_v) <= 0.01 * max(abs(v), abs(pid_v), 1e-9) for v, _ in got):
                continue
            shown = ", ".join(f"{v:g}" for v, _ in got[:4])
            findings.append(_finding(
                "warn", "source conflict",
                f"P&ID {tag} {attr} is {pid_v:g}; the data sheet gives {shown} for the same quantity ({got[0][1][:160]}).",
                [tag]))
    return findings


def _enthalpy(stream):
    if not isinstance(stream, dict):
        return None
    for key in _ENTHALPY_KEYS:
        if isinstance(stream.get(key), (int, float)):
            return float(stream[key])
    return None


def _boundary_duty_kW(units):
    """Heat and shaft work crossing the flowsheet boundary. Cooler duty_kW is heat removed (positive in the result).
    Exchanger and evaporator duties stay inside the material streams, so they are not added again."""
    q = 0.0
    for u in (units or {}).values():
        if not isinstance(u, dict):
            continue
        t = u.get("type")
        if t == "heater":
            q += float(u.get("duty_kW") or 0)
        elif t == "cooler":
            q -= abs(float(u.get("duty_kW") or 0))
        elif t == "pump":
            q += float(u.get("kW") or 0)
        elif t == "compressor":
            q += float(u.get("duty_kW") or u.get("kW") or 0)
        elif t == "column":
            q += float(u.get("reboiler_kW") or 0) - float(u.get("condenser_kW") or 0)
    return q


def _energy(spec, result):
    """Overall closure when streams carry enthalpy; otherwise evaporator duty closure, and the missing field to add."""
    evap = any(u.get("type") == "evaporator" for u in spec.get("units") or [])
    note = ("An overall energy balance is not closed: the simulator's streams do not report enthalpy. "
            + ("Each evaporator's heat balance is checked instead (within 2 %; a model is blocked above 10 %)." if evap else
               "Unit duties are checked one by one instead."))
    info = {"method": "duty", "tolerance": ENERGY_TOL, "proposed_field": ENTHALPY_FIELD, "note": note}
    findings = []
    units = (result or {}).get("units") or {}
    streams = (result or {}).get("streams") or {}
    produced, consumed = set(), set()
    for u in spec.get("units") or []:
        ins, outs = _ports(u)
        consumed.update(ins)
        produced.update(outs)
    feeds = [s for s in (spec.get("feeds") or {}) if s not in produced]
    products = [s for s in produced if s not in consumed]
    boundary = feeds + products
    if boundary and streams and all(_enthalpy(streams.get(s)) is not None and isinstance((streams.get(s) or {}).get("kg_h"), (int, float))
                                    for s in boundary):
        inlet = sum((streams[s]["kg_h"] / 3600.0) * _enthalpy(streams[s]) for s in feeds)
        outlet = sum((streams[s]["kg_h"] / 3600.0) * _enthalpy(streams[s]) for s in products)
        duty = _boundary_duty_kW(units)
        gap = inlet - outlet + duty
        denom = max(abs(inlet), abs(outlet), abs(duty), 1.0)
        frac = abs(gap) / denom
        info = {"method": "enthalpy", "tolerance": ENERGY_TOL, "proposed_field": None,
                "in_kW": round(inlet, 1), "out_kW": round(outlet, 1), "duty_kW": round(duty, 1),
                "imbalance_kW": round(gap, 1), "fraction": round(frac, 4),
                "note": "Closed on stream enthalpy plus boundary duties."}
        if frac > ENERGY_TOL:
            findings.append(_finding(
                "block" if frac > ENERGY_BLOCK else "warn", "energy not closed",
                f"Feed enthalpy {inlet:.1f} kW, product enthalpy {outlet:.1f} kW, boundary duties {duty:.1f} kW, "
                f"imbalance {gap:.1f} kW ({frac:.1%} of the largest term; tolerance {ENERGY_TOL:.0%})."))
        return info, findings
    for uid, u in units.items():
        if not isinstance(u, dict) or u.get("type") != "evaporator" or u.get("heat_balance_kW") is None or u.get("heating_kW") is None:
            continue
        bal, heat, boil = float(u["heat_balance_kW"]), float(u["heating_kW"]), float(u.get("boil_kW") or 0)
        scale = max(abs(heat), abs(boil), 1.0)
        frac = abs(bal) / scale
        if frac > ENERGY_TOL:
            findings.append(_finding(
                "block" if frac > ENERGY_BLOCK else "warn", "energy not closed",
                f"{uid} heat balance is {bal:.1f} kW against heating {heat:.1f} kW and boil-up {boil:.1f} kW "
                f"({frac:.1%}; tolerance {ENERGY_TOL:.0%}).", [uid]))
    return info, findings


def review_trapped(spec, result):
    """Deterministic review of a blocked-in segment model: one segment, its isolating valves and relief, rated limits,
    a solved isochore. No LLM."""
    spec, findings = spec or {}, []
    units = spec.get("units") or []
    segs = [u for u in units if u.get("type") == "pipe_segment"]
    if len(segs) != 1:
        findings.append(_finding("block", "one pipe segment", f"the model has {len(segs)} pipe_segment units; it needs exactly one"))
    for s in segs:
        for k in ("od_m", "wall_m", "heat_leak_W_m"):
            if not isinstance(s.get(k), (int, float)) or s[k] <= 0:
                findings.append(_finding("block", "segment data", f"{s.get('id')} needs a positive {k}", [s.get("id")]))
        feed = (spec.get("feeds") or {}).get(s.get("in")) or {}
        if not 0 < float(feed.get("fill_fraction") or 0) <= 1:
            findings.append(_finding("block", "start state", f"feed {s.get('in')} needs fill_fraction between 0 and 1", [s.get("id")]))
        lim = (spec.get("limits") or {}).get(s.get("id")) or {}
        if not lim.get("design_psig"):
            findings.append(_finding("block", "design pressure", f"{s.get('id')} has no design_psig limit", [s.get("id")]))
        if not [u for u in units if u.get("type") == "valve" and u.get("isolates") == s.get("id")]:
            findings.append(_finding("warn", "isolation valves", f"no valve isolates {s.get('id')}: it can never be blocked in"))
        if not [u for u in units if u.get("type") == "relief_valve" and u.get("protects") == s.get("id")]:
            findings.append(_finding("warn", "relief", f"no relief valve protects {s.get('id')}"))
    if result is not None and (result.get("errors") or not result.get("checks")):
        findings.append(_finding("block", "solve", "the segment did not solve: " + "; ".join(result.get("errors") or ["no checks"])))
    findings.sort(key=lambda f: (0 if f["severity"] == "block" else 1, f["check"], f["evidence"]))
    status = "model needs review" if any(f["severity"] == "block" for f in findings) else "ok"
    return {"status": status, "findings": findings, "blocking": sum(f["severity"] == "block" for f in findings), "energy": {}}


def review_model(spec, result, pid_ov=None, basis=""):
    """Deterministic model review. No LLM. Findings are block (the model needs review) or warn (a conflict to read)."""
    spec = spec or {}
    units = [u for u in spec.get("units") or [] if u.get("id")]
    unit_ids = {u["id"] for u in units}
    findings = []
    tags = [e.get("tag") for e in (pid_ov or {}).get("equipment") or [] if e.get("tag")]
    tags = sorted(tags, key=len, reverse=True)
    classes = {e.get("tag"): e.get("class") or "" for e in (pid_ov or {}).get("equipment") or []}
    role_of = {}
    for u in units:
        for tag in tags:
            role = _tag_role(u["id"], tag)
            if role:
                role_of[u["id"]] = (tag, role)
                break
    represented = {role_of[u["id"]][0] for u in units if u["id"] in role_of}
    represented.update(u["id"] for u in units)
    by_tag = {}
    for u in units:
        hit = role_of.get(u["id"])
        if hit:
            by_tag.setdefault(hit[0], []).append((u, hit[1]))
    for tag, group in sorted(by_tag.items()):
        if len(group) >= 2 and not all(role == "parallel" for _, role in group):
            shown = ", ".join(f"{u['id']} ({u.get('type')})" for u, _ in group)
            findings.append(_finding("block", "equipment represented twice",
                                     f"P&ID {tag} is represented by {shown}.", [u["id"] for u, _ in group]))
        for u, _ in group:
            if u.get("type") in ("cooler", "heater") and "desuperheater" in classes.get(tag, "").casefold():
                findings.append(_finding(
                    "block", "desuperheater modelled as heat removal",
                    f"P&ID {tag} is a desuperheater; unit {u['id']} is a {u['type']}, so the superheat is removed as a duty "
                    "instead of by spray mixing.", [u["id"], tag]))
    if pid_ov:
        known = {}
        for c in _connections(pid_ov, spec):
            if c.get("relief_path"):
                continue
            for line in c.get("lines") or []:
                known.setdefault(str(line), set()).add(c.get("from"))
        tears = {u.get("out") for u in units if u.get("type") == "recycle" and isinstance(u.get("out"), str)}
        for fid in spec.get("feeds") or {}:
            if fid in tears:
                continue
            lines = [t for t in _LINE_TOKEN.findall(str(fid)) if t in known]
            origins = sorted({o for line in lines for o in known[line] if o and (o in unit_ids or o in represented)})
            if origins:
                findings.append(_finding(
                    "block", "internal source as a free feed",
                    f"Feed {fid} maps to P&ID line {', '.join(lines)}, which starts at modelled equipment {', '.join(origins)}.",
                    [fid, *origins]))
        duty_lines = {}
        for u in units:
            if u.get("type") not in _HEAT:
                continue
            for stream in _duty_inlets(u):
                for line in _LINE_TOKEN.findall(str(stream)):
                    if line in known:
                        duty_lines.setdefault(line, {}).setdefault(u["id"], stream)
        for line, owners in sorted(duty_lines.items()):
            if len(owners) < 2:
                continue
            shown = ", ".join(f"{uid} ({stream})" for uid, stream in owners.items())
            findings.append(_finding(
                "block", "duty modelled twice",
                f"P&ID line {line} is a heat-duty inlet of {shown}, so one equipment duty is in the flowsheet twice.",
                list(owners)))
        findings.extend(_source_conflicts(pid_ov, basis))
    if result:
        errs = [e for e in result.get("errors") or [] if e]
        if errs:
            findings.append(_finding("block", "unit did not solve", "Flowsheet errors: " + "; ".join(str(e) for e in errs[:6])))
        for uid, u in (result.get("units") or {}).items():
            if isinstance(u, dict) and u.get("error"):
                findings.append(_finding("block", "unit did not solve", f"{uid}: {u['error']}", [uid]))
        for c in result.get("checks") or []:
            if c.get("check") == "no limit check for this unit type" and c.get("type") == "dwsim":
                findings.append(_finding(
                    "block", "generic unit has no engineering limit checks",
                    f"{c.get('id')} is a generic DWSIM unit; its class-specific ratings are not mapped to capacity checks.",
                    [c.get("id")] if c.get("id") else None))
            elif (isinstance(c.get("utilisation"), (int, float)) and c["utilisation"] < 0 and
                  c.get("check") != "pressure drop vs available"):
                findings.append(_finding(
                    "block", "negative utilisation",
                    f"{c.get('id')} {c.get('check')} utilisation is {c['utilisation']} (value {c.get('value')} {c.get('unit') or ''}).",
                    [c.get("id")] if c.get("id") else None))
            elif c.get("error") and "did not solve" in str(c.get("error")).lower():
                findings.append(_finding("block", "unit did not solve", f"{c.get('id')}: {c['error']}", [c.get("id")] if c.get("id") else None))
        streams = result.get("streams") or {}
        for u in units:
            if u.get("type") != "recycle":
                continue
            a, b = streams.get(u.get("in")) or {}, streams.get(u.get("out")) or {}
            if not a or not b or a.get("error") or b.get("error"):
                findings.append(_finding("block", "recycle not converged",
                                         f"{u['id']} has no solved tear stream ({u.get('in')} / {u.get('out')}).", [u["id"]]))
                continue
            bad = []
            if isinstance(a.get("T_C"), (int, float)) and isinstance(b.get("T_C"), (int, float)) and abs(a["T_C"] - b["T_C"]) > 0.5:
                bad.append(f"T {a['T_C']} vs {b['T_C']} °C")
            if isinstance(a.get("P_bar"), (int, float)) and isinstance(b.get("P_bar"), (int, float)) and abs(a["P_bar"] - b["P_bar"]) > 0.02:
                bad.append(f"P {a['P_bar']} vs {b['P_bar']} bar")
            if isinstance(a.get("kg_h"), (int, float)) and isinstance(b.get("kg_h"), (int, float)):
                scale = max(abs(a["kg_h"]), abs(b["kg_h"]), 1.0)
                if abs(a["kg_h"] - b["kg_h"]) > 0.01 * scale:
                    bad.append(f"flow {a['kg_h']} vs {b['kg_h']} kg/h")
            if bad:
                findings.append(_finding("block", "recycle not converged",
                                         f"{u['id']} tear {u.get('out')} and return {u.get('in')} differ: {', '.join(bad)}.", [u["id"]]))
    energy, energy_findings = _energy(spec, result)
    findings.extend(energy_findings)
    findings.sort(key=lambda f: (0 if f["severity"] == "block" else 1, f["check"], f["evidence"]))
    status = "model needs review" if any(f["severity"] == "block" for f in findings) else "ok"
    return {"status": status, "findings": findings, "blocking": sum(f["severity"] == "block" for f in findings), "energy": energy}


def historian(path, tags=None, start=None, end=None):
    """Summary of a historian/SCADA export (CSV: a time column, then one column per tag): mean, p5, p95, min, max per tag,
    over an optional time window. Standard library only."""
    import csv
    import statistics
    with open(path) as f:
        rows = list(csv.reader(f))
    head, data = rows[0], rows[1:]
    if start or end:
        data = [r for r in data if (not start or r[0] >= start) and (not end or r[0] <= end)]
    out = {}
    for j, tag in enumerate(head[1:], 1):
        if tags and tag not in tags:
            continue
        v = sorted(float(r[j]) for r in data if j < len(r) and r[j] not in ("", "NaN", "nan"))
        if v:
            q = lambda p: v[min(len(v) - 1, int(p * len(v)))]  # noqa: E731
            out[tag] = {"n": len(v), "mean": round(statistics.fmean(v), 3), "p5": q(.05), "p95": q(.95), "min": v[0], "max": v[-1]}
    return {"from": data[0][0] if data else None, "to": data[-1][0] if data else None, "tags": out, "available": head[1:]}


def annual_energy(spec, units, bins, price=None):
    """Bin-method annual electricity of `units` over operating bins; each bin is a DWSIM solve."""
    rows, total = [], 0.0
    for b in bins:
        r = process.run(patch(spec, b.get("changes") or []), float(b.get("scale") or 1.0))
        kw = 0.0
        for uid in units:
            u = r["units"].get(uid) or {}
            f = (b.get("electric_per_kW_duty") or {}).get(uid)
            kw += abs(u.get("duty_kW") or 0) * f if f else (u.get("kW") or 0)
        rows.append({"bin": b.get("name"), "hours": b["hours"], "kW": round(kw, 1), "MWh": round(kw * b["hours"] / 1000, 1),
                     "errors": r["errors"]})
        total += kw * b["hours"]
    return {"bins": rows, "MWh_per_year": round(total / 1000, 1), "hours": sum(b["hours"] for b in bins),
            "cost_per_year": round(total * price) if price else None}


class PlantWorkspace(Study):
    def __init__(self, case_name, model="muse-spark-1.3-contributor"):
        self.name, self.model = case_name, model
        self.cfg = json.loads((ROOT / "cases" / case_name / "case.json").read_text())
        self.pid_file = ROOT / "runs" / "ws" / case_name / "pid_read.json"
        self.confirmed_file = self.pid_file.with_name("pid_confirmed.json")
        if self.cfg.get("pid"):
            self.pid = pid.overview(DATA / self.cfg["pid"])
        elif self.confirmed_file.exists():  # a PDF schematic: the engineer-confirmed read is the one models are built on
            self.pid = json.loads(self.confirmed_file.read_text())
        elif self.pid_file.exists():  # read by Muse vision, not yet confirmed by the engineer
            self.pid = json.loads(self.pid_file.read_text())
        else:
            self.pid = None
        self.basis = (ROOT / "cases" / case_name / self.cfg["basis"]).read_text()
        self.dir = ROOT / "runs" / "ws" / case_name / time.strftime("%Y%m%d-%H%M%S")
        self.log = _LazyLog(self.dir / "log.jsonl")  # the session folder appears only when something is logged
        self.steps, self.listener, self.answers, self.revisions = 0, None, [], []
        self.rev_file = None
        self.runs = {}
        self.model_file = ROOT / "runs" / "ws" / case_name / "model.json"
        self.rev_file = self.model_file.with_name("revisions.json")
        self.gaps = load_gaps(self.model_file.with_name("gaps.json"))
        self.built = json.loads(self.model_file.read_text()) if self.model_file.exists() else None
        if self.built and self.rev_file.exists():  # revisions survive restarts; the latest one is the current model
            self.revisions = json.loads(self.rev_file.read_text())  # calculation is optional on older revisions
            if self.revisions:
                self.built["spec"] = self.revisions[-1]["spec_after"]
                self.built["result"] = self.revisions[-1].get("result_after")  # None: re-solved on first reproduce
        if self.built:
            self.runs[self.built["label"]] = {"spec": self.built["spec"], "purpose": "calibrated model", "result": self.built.get("result")}
            self.built["gaps"] = self.gaps
            try:
                self.built["review"] = self._review(self.built["spec"], self.built.get("result"),
                                                    self.built.get("mapping"), self.built.get("assumptions"))
            except Exception as e:  # noqa: BLE001 - the workspace still opens; the failure is shown in the drawer
                finding = _finding("block", "model review failed",
                                   f"Model review raised {type(e).__name__}: {e}")
                self.built["review"] = {"status": "model needs review", "findings": [finding], "blocking": 1,
                                        "energy": {}, "error": f"{type(e).__name__}: {e}"}
            self.built["review_status"] = self.built["review"]["status"]
        self._state = {}
        # pick up the answers of the latest session made on this same model, so a restart keeps the engineer's thread
        for prev in sorted((ROOT / "runs" / "ws" / case_name).glob("2*/answers.json"), reverse=True):
            if prev.parent != self.dir and self.built and _made_after(prev.parent.name, self.built.get("at"), prev, self.model_file):
                self.answers = json.loads(prev.read_text())
                break

    @property
    def spec(self):
        return self.built["spec"] if self.built else None

    def emit(self, event):
        if self.listener:
            self.listener(event)

    def tools(self):
        f = lambda name, desc, props, req=(): {"type": "function", "function": {  # noqa: E731
            "name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": list(req)}}}
        shared = [
            f("read_pid", "The smart P&ID: equipment with design data and limits, connections (with inline valves), lines with fluid "
                          "codes, valves, control loops.", {}),
            f("search_documents", "Keyword search over the project documents (tenders, datasheets, reports); returns [doc, page].",
              {"query": S}, ["query"]),
            f("read_document_page", "Text of one page of a project document.", {"doc": S, "page": {"type": "integer"}}, ["doc", "page"]),
            f("read_data_sheet", "The operating data sheet: current operation, process requirements, equipment performance, utilities.", {}),
            f("get_spec", "Full spec of a logged run (the calibrated model is preloaded), to copy and modify. For a proposal, "
                          "return explicit changes rather than an opaque replacement spec. " + (ro_changes.CHANGE_HELP if _is_watertap(getattr(self, "cfg", None)) else CHANGE_HELP), {"label": S}, ["label"]),
            f("sweep", "Parameter study: re-solve a logged run with ONE input varied over the given values (e.g. feed temperature, "
                       "salinity, a utility flow, fouled U) at a throughput multiple; returns the utilisation of the tightest "
                       "checks per value and saves a chart for the engineer. Use it for 'what if X changes' and sensitivity requests.",
              {"label": S, "path": {"type": "string", "description": "dotted path in the spec, e.g. feeds.FEED.T_C or units.E-201.U_W_m2K"},
               "values": {"type": "array", "items": N}, "scale": N, "title": S}, ["label", "path", "values"]),
            f("check_coverage", "Compare a logged run's model with the P&ID / documented boundary: which equipment is modelled "
                                "(or mapped to a grouped block / note), which is missing, and which physics is intentionally not "
                                "simulated.",
              {"label": S}, ["label"]),
            f("historian", "Summary statistics (mean, p5, p95, min, max) of the plant's historian/SCADA export for chosen tags "
                           "and an optional time window; call with no tags to list what is available.",
              {"tags": {"type": "array", "items": S}, "start": S, "end": S}),
            f("report_gap", "Call this when the flowsheet spec cannot express the physics or the change you need. "
                            "Do not approximate the effect and do not change a documented limit to stand in for it. "
                            "Saved on the case and shown to the engineer.",
              {"what": S, "why": S, "needed": {"type": "string", "description": "what the spec or the tools would have to be able to do"}},
              ["what", "why", "needed"]),
            # electrical (plantagent/electrical.py): pandapower load flow + motor-start dip on the plant's one-line diagram
            f("electrical_check", "Electrical check of new or bigger motors: load flow of the plant's one-line diagram "
                                  "(cases/<case>/electrical.json) with motor loads from the process solve at `scale`, "
                                  "transformer and cable loading, bus voltages and the start dip of the largest new/changed "
                                  "motor. Give `answer` (index of a stored answer: its verified proposals) or `changes`; "
                                  "`motors` [{unit, kw, start DOL|VFD|SOFT, bus}] overrides a rating or starting method. "
                                  "Saves a one-line diagram SVG.",
              {"answer": {"type": "integer"}, "changes": {"type": "array", "items": {"type": "object"}}, "scale": N,
               "motors": {"type": "array", "items": {"type": "object"}}}),
            # documents (plantagent/documents.py): deterministic, numbers only from the record, saved as draft artifacts
            f("make_document", "Make an engineer document as a DRAFT artifact (markdown + PDF), deterministically from the "
                               "model, simulator solves, P&ID, data sheet and stored answers; every number carries its source. "
                               "kind: datasheet (subject = equipment tag, existing or added by a proposal), calc_sheet (subject = "
                               "'unit' or 'unit: check words'), summary (subject = answer index), work_order (subject = tag "
                               "of a proposal, e.g. a clean). answer = index of a stored answer (default: the latest).",
              {"kind": {"type": "string", "enum": ["datasheet", "calc_sheet", "summary", "work_order"]}, "subject": S,
               "scale": N, "answer": {"type": "integer"}}, ["kind"]),
            f("prefeed_assessment", "Build a deterministic DRAFT pre-FEED gate for the selected verified design (or the current "
                                    "model): re-solve an operating-envelope matrix, check mass closure, screen provisional new-"
                                    "equipment ratings, critical-loop dynamics when measured FOPDT constants are supplied, changed-"
                                    "equipment HAZOP/relief cases, and cost/constructability gaps. It also writes one cross-discipline "
                                    "impact register, ranked decision-changing evidence requests, a change comparison, vendor RFQ duty "
                                    "sheet and commissioning acceptance plan. Saves Markdown, JSON and PDF. "
                                    "It never invents vendor curves, dynamic constants or costs; omitted inputs stay open.",
              {"answer": {"type": "integer", "description": "stored answer index; default selects the current proposed design"},
               "scenarios": {"type": "array", "items": {"type": "object", "description": "{name, scale, changes, basis}; max 24"}},
               "dynamics": {"type": "array", "items": {"type": "object", "description": "measured FOPDT screen: name, variable, "
                                                                                         "initial, final, time_constant_s, dead_time_s, "
                                                                                         "duration_s, low_limit/high_limit, unit, source"}},
               "economics": {"type": "object", "description": "optional sourced capex_low/high, outage_days, production_value_per_day, currency, source"}}),
        ]
        # ---- drawing tool (plantagent/revb.py): a Rev B sheet for changes and notes the engineer asks for
        if (getattr(self, "cfg", None) or {}).get("svg"):
            shared = shared + [f("draw_revision", "Draw a draft Rev B of the project P&ID with revision clouds, value callouts and a "
                                                  "revision block; saved as a drawing artifact. Preferred: give `answer` (index of the answer, "
                                                  "-1 = latest) and/or `proposals` (titles or indices of its verified proposals) so the "
                                                  "verified proposals are drawn exactly; do not re-type their changes. `changes` (proposal "
                                                  "format: path changes, add_unit (parallel or in series on a line), reroute, {remove_unit: id}, {bypass: {unit: id}}) only "
                                                  "for something not in a verified proposal; "
                                                  "changes that match a verified proposal are replaced by it. `annotations` are free notes "
                                                  "[{tag, text}] at an equipment tag, a line number ('3003') or an inline item ('3003/C1', "
                                                  "'PSV-202'), e.g. 'car-seal open'. Does not run the simulator.",
                                 {"answer": {"type": "integer"}, "proposals": {"type": "array", "items": S},
                                  "changes": {"type": "array", "items": {"type": "object"}},
                                  "annotations": {"type": "array", "items": {"type": "object", "description": "{tag or line, text}"}},
                                  "title": S})]
        # ---- end drawing tool
        # ---- heat-exchanger detail + combustion tools (plantagent/hxdetail.py, plantagent/combustion.py)
        if not _is_watertap(getattr(self, "cfg", None)) and not _is_trapped(getattr(self, "cfg", None)) and not _is_grid(getattr(self, "cfg", None)):
            shared = shared + [
                f("hx_detail", "Detailed thermal-hydraulic rating of ONE heat exchanger (shell-and-tube or plate) with the ht/fluids "
                               "correlations: tube/channel velocity, tube- and shell-side h (Gnielinski, Bell-Delaware, condensing "
                               "film), U clean and with TEMA fouling, area required vs installed, tube/shell pressure drop, and "
                               "screening checks (velocity window, scaling velocity for salting brine, dP vs allowable, model U vs "
                               "correlation U > 20 %). Duty, flows and temperatures come from a DWSIM solve at `scale`; with `answer` "
                               "the answer's proposal on this exchanger is applied (a cleaning proposal rates the clean condition). "
                               "Saves a calculation-sheet artifact. Use for 'check the heater tube velocities', 'is E-201 thermally "
                               "OK after cleaning', 'what U should this exchanger have', 'pressure drop of H1008'.",
                  {"tag": {"type": "string", "description": "exchanger tag, e.g. E-201 (also V-201 for its heater), H1007, H1008"},
                   "scale": {"type": "number", "description": "throughput multiple of the solve (default 1.0)"},
                   "answer": {"type": "integer", "description": "stored answer index whose proposal on this tag is applied"},
                   "condition": {"type": "string", "enum": ["fouled", "clean"], "description": "fouling allowance (default: fouled, clean for a cleaning proposal)"}},
                  ["tag"]),
                f("combustion_check", "Combustion / fired-equipment screening with Cantera: adiabatic flame temperature, flue-gas "
                                      "composition, O2 and flow, efficiency by the ASME PTC 4 stack-loss method, and a NOx screening "
                                      "(equilibrium and thermal NO). On a plant with a gas turbine + HRSG on record (salt plant): the "
                                      "documented operation and one scenario: `steam_scale` (e.g. 1.2 = +20 % HRSG steam, the duct "
                                      "firing it needs is solved) or `firing_scale` (e.g. 1.2 = +20 % total fuel, the extra fired in a "
                                      "duct burner), giving steam, stack temperature, pinch, gas into the superheater and NOx added. "
                                      "Otherwise screens one burner from firing_kW, fuel, excess air or flue O2, air preheat and "
                                      "stack temperature. Saves a calculation-sheet artifact. Use for 'what does +20 % firing do to the "
                                      "stack temperature / NOx', 'can the HRSG support +20 % steam', 'boiler efficiency at this O2'.",
                  {"steam_scale": N, "firing_scale": N,
                   "exhaust_T_C": {"type": "number", "description": "override the illustrative turbine exhaust temperature (sensitivity)"},
                   "scale": {"type": "number", "description": "process throughput multiple for the turbine shaft power (default 1.0)"},
                   "firing_kW": {"type": "number", "description": "burner mode: firing rate, kW on `basis`"},
                   "basis": {"type": "string", "enum": ["HHV", "LHV"]},
                   "fuel": {"type": "object", "description": "mole fractions, GRI-Mech species (CH4, C2H6, C3H8, H2, CO, CO2, N2); default typical natural gas"},
                   "excess_air_pct": N, "o2_dry_pct": N, "air_T_C": N, "stack_T_C": N,
                   "residence_s": {"type": "number", "description": "residence time at flame temperature for the thermal-NO screening"}}),
            ]
        # ---- end heat-exchanger detail + combustion tools
        if _is_trapped(getattr(self, "cfg", None)):
            return shared + [
                f("run_trapped", "Solve the blocked-in segment (DWSIM thermodynamics along a constant-volume path) after `scale` x "
                                 "the documented time blocked in, and log it under `label`. Returns the pressure and temperature, "
                                 "when the liquid fills the pipe, when design and burst pressure are reached, the relief valve "
                                 "state, limit checks (utilisation = value/limit) and the pressure history. Spec: " + trapped.SPEC_HELP,
                  {"label": S, "purpose": S, "spec": {"type": "object"},
                   "scale": {"type": "number", "description": "multiplies the documented time blocked in (spec.hours)"}},
                  ["label", "spec"]),
                f("trapped_capacity", "Time multiple of a logged run at which the first stated limit reaches 100 %, and which.",
                  {"label": S}, ["label"]),
                f("pressure_history", "Chart the pressure against time of a logged run (with design and burst pressure lines) and "
                                      "save it as a chart artifact for the engineer.",
                  {"label": S, "title": S}, ["label"]),
                f("bubble_pressure", "DWSIM: saturation (bubble-point) pressure of a liquid at each temperature.",
                  {"compounds": {"type": "array", "items": S}, "x": {"type": "object"}, "T_C": {"type": "array", "items": N}},
                  ["compounds", "x", "T_C"]),
            ]
        if _is_grid(getattr(self, "cfg", None)):
            return shared + [
                f("run_grid", "Solve an AC load flow of a transmission-grid spec and log it under `label`. Returns every line and "
                              "transformer flow (MW, Mvar, A), bus voltages and angles, and every limit check (current vs the "
                              "protection setting in limits, or vs thermal rating; utilisation = value/limit). Spec: " + grid.SPEC_HELP,
                  {"label": S, "purpose": S, "spec": {"type": "object"},
                   "scale": {"type": "number", "description": "multiplies injections and grid-equivalent angles (transit)"}},
                  ["label", "spec"]),
                f("n_minus_1", "N-1 contingency screen of a logged run: switch off each line/transformer (or the listed `elements`) "
                               "in turn, optionally after `changes` (e.g. a switching action), and report every limit exceeded. "
                               "secure = no single outage exceeds a limit.",
                  {"label": S, "changes": {"type": "array", "items": {"type": "object"}}, "elements": {"type": "array", "items": S},
                   "scale": N}, ["label"]),
                f("grid_capacity", "Largest transit multiple of a logged run (optionally after `changes`) at which every check is "
                                   "still within 100 %, and which limit binds first.",
                  {"label": S, "changes": {"type": "array", "items": {"type": "object"}}}, ["label"]),
            ]
        if _is_watertap(getattr(self, "cfg", None)):
            return shared + [
                f("run_ro", "Solve a WaterTAP reverse-osmosis plant and log it under `label`. Returns stream flow, pressure and TDS, "
                            "flux, recovery, permeate TDS, specific energy and limit checks (utilisation = value/limit). Spec: " + ro.SPEC_HELP,
                  {"label": S, "purpose": S, "spec": {"type": "object"}, "scale": {"type": "number", "description": "multiplies the feed flow"}},
                  ["label", "spec"]),
                f("ro_capacity", "Largest feed-flow multiple of a logged WaterTAP run at which every check is still within 100 %, and which limit.",
                  {"label": S}, ["label"]),
                f("ro_normalize", "ASTM D4516: normalized permeate flow, normalized salt passage and normalized differential pressure "
                                  "from an actual and a standard condition.",
                  {"actual": {"type": "object"}, "standard": {"type": "object"}}, ["actual", "standard"]),
            ]
        return shared + [
            f("run_process", "Solve a DWSIM flowsheet and log it under `label`. Returns stream T/P/flows, unit results and every "
                             "limit check (utilisation = value/limit). Spec: " + json.dumps(process.SPEC_HELP),
              {"label": S, "purpose": S, "spec": {"type": "object"}, "scale": {"type": "number", "description": "multiplies non-utility feeds"}},
              ["label", "spec"]),
            f("process_capacity", "Throughput multiple of a logged run at which the first stated limit reaches 100 %, and which.",
              {"label": S}, ["label"]),
            f("annual_energy", "Annual electricity by the bin method: solve a logged model once per bin (e.g. wet-bulb bins) with "
                               "that bin's changes and throughput, then sum electric power x hours. Power counts pumps and "
                               "compressors in `units` from the solve; for equipment not modelled electrically (a chiller "
                               "modelled as a cooler) give electric_per_kW_duty {unit: kWe per kW of duty, e.g. 1/COP} per bin. "
                               "Use it to compare a base case and an alternative over the same bins.",
              {"label": S, "units": {"type": "array", "items": S},
               "bins": {"type": "array", "items": {"type": "object", "description": "{name, hours, scale, changes: [{path, value}], "
                                                                                       "electric_per_kW_duty: {unit: factor}}"}},
               "price_per_kWh": N}, ["label", "units", "bins"]),
            f("morning_check", "The morning check: exchanger fouling trends from the historian (U now vs at the start, days to the "
                               "outlet limit at today's and the target throughput), measured limits and data quality, and the top 3 "
                               "things to look at today.", {}),
            # fouling forecast (plantagent/forecast.py): historian fit + simulator bisection, chart artifact
            f("forecast_fouling", "Fouling forecast for an exchanger with a historian U signal: U trend since the last "
                                  "cleaning (fit and 95 % band), the U at which the plant hits its first limit (re-solved in "
                                  "the simulator), the date it is reached, production and money lost after it, the latest "
                                  "cleaning date, and a back-test. Saves a chart artifact.",
              {"equipment": S, "as_of_day": {"type": "integer", "description": "historian day to forecast from (default: the last)"}}),
            f("troubleshoot", "Rank the causes of an exchanger's process outlet running out of spec (fouling, utility short of flow, "
                              "utility too warm, process flow higher than metered, process arriving hotter): each cause is fitted in "
                              "DWSIM to the symptom and checked against the other historian readings; returns the ranked causes and "
                              "the field checks that separate causes that both fit.",
              {"equipment": S, "reading_C": N}, ["equipment"]),
            f("relief_scan", "Deterministic scan of the P&ID: for each side of each equipment item, whether it reaches a relief "
                             "device without passing a valve that could be closed, and which heated sides could be blocked in.", {}),
            f("bubble_pressure", "DWSIM: saturation (bubble-point) pressure of a liquid at each temperature, e.g. a refrigerant's "
                                 "condensing pressure at a condensing temperature.",
              {"compounds": {"type": "array", "items": S}, "x": {"type": "object"}, "T_C": {"type": "array", "items": N}},
              ["compounds", "x", "T_C"]),
            f("brine_bpe", "NaCl brine (Sparrow 2003): boiling temperature and boiling point elevation at a pressure, for a "
                           "salt mass fraction or saturated brine (omit x_NaCl). DWSIM water models miss this; add it yourself.",
              {"p_bar": N, "x_NaCl": N}, ["p_bar"]),
            f("blocked_in_pressure", "DWSIM: pressure a liquid-full, blocked-in vessel reaches when heated from T1 to T2 "
                                     "(API 521 hydraulic expansion), for relief checks.",
              {"compounds": {"type": "array", "items": S}, "x": {"type": "object"}, "T1_C": N, "P1_bar": N, "T2_C": N},
              ["compounds", "x", "T1_C", "P1_bar", "T2_C"]),
        ]

    def _capacity_of(self, spec):
        if self.cfg.get("engine") == "watertap":
            return ro.capacity(spec)
        if _is_trapped(self.cfg):
            return trapped.capacity(_trapped_spec(self.cfg, spec))
        if _is_grid(self.cfg):
            return grid.capacity(spec)
        return process.capacity(spec)

    def call(self, name, a):
        """Every tool result that is an artifact (a document, drawing or chart the engineer asked for) is collected, so the
        answer lists the files it produced."""
        r = self._call_tool(name, a)
        if isinstance(r, dict) and r.get("id") and r.get("kind") and r.get("files"):
            self.__dict__.setdefault("_artifacts", []).append({k: r.get(k) for k in ("id", "kind", "title", "files", "summary")})
        return r

    def _call_tool(self, name, a):
        if name == "prefeed_assessment":
            from . import prefeed
            return prefeed.make(self, a.get("answer"), a.get("scenarios"), a.get("dynamics"), a.get("economics"))
        if name == "electrical_check":
            from . import electrical
            changes = a.get("changes") or []
            if a.get("answer") is not None:
                ans = self.answers[int(a["answer"])] if -len(self.answers) <= int(a["answer"]) < len(self.answers) else None
                if ans is None:
                    return {"error": f"no answer {a['answer']}; {len(self.answers)} on record"}
                changes = [c for p in ans.get("proposals") or [] if p.get("verified") for c in p.get("changes") or []]
            try:
                return electrical.for_workspace(self, changes, a.get("scale"), a.get("motors"))
            except (ValueError, KeyError, RuntimeError) as e:
                return {"error": str(e)}
        if name == "forecast_fouling":
            try:
                return self.forecast_fouling(a.get("equipment"), a.get("as_of_day"))
            except (ValueError, KeyError, FileNotFoundError) as e:
                return {"error": str(e)}
        if name == "make_document":
            from . import documents
            try:
                return documents.make(self, a["kind"], a.get("subject"), a.get("scale"), a.get("answer"), by=self.model)
            except (ValueError, KeyError) as e:
                return {"error": str(e)}
        if name == "draw_revision":  # drawing tool block (plantagent/revb.py)
            from .revb import draw_revision_tool
            try:
                return draw_revision_tool(self, a)
            except ValueError as e:
                return {"error": str(e)}
        # ---- heat-exchanger detail + combustion tools
        if name == "hx_detail":
            from . import hxdetail
            try:
                return hxdetail.hx_detail(self, a["tag"], a.get("scale"), a.get("answer"), a.get("condition"), by=self.model)
            except (ValueError, KeyError) as e:
                return {"error": str(e)}
        if name == "combustion_check":
            from . import combustion
            keys = ("steam_scale", "firing_scale", "exhaust_T_C", "residence_s", "scale", "fuel", "firing_kW", "excess_air_pct",
                    "o2_dry_pct", "air_T_C", "stack_T_C")
            try:
                return combustion.combustion_check(self, **{k: a[k] for k in keys if a.get(k) is not None},
                                                   basis=a.get("basis") or "HHV", by=self.model)
            except (ValueError, KeyError) as e:
                return {"error": str(e)}
        # ---- end heat-exchanger detail + combustion tools
        if name == "read_pid":
            return self.pid or {"note": "this project has no drawing: take the equipment and connections from the data sheet"}
        if name == "search_documents":
            from .docs import _pages
            q = [w for w in a["query"].lower().split() if len(w) > 2]
            hits = [(sum(t.lower().count(w) for w in q), d["id"], i + 1) for d in self.cfg.get("documents", [])
                    for i, t in enumerate(_pages(DATA / d["pdf"]))]
            return [{"doc": d, "page": p} for n, d, p in sorted(hits, reverse=True)[:8] if n]
        if name == "read_document_page":
            from .docs import _pages
            d = next(x for x in self.cfg.get("documents", []) if x["id"] == a["doc"])
            # ponytail: whitespace squeezed and capped, so a dozen page reads stay inside the model's working context
            return {"doc": a["doc"], "page": a["page"], "text": " ".join(_pages(DATA / d["pdf"])[int(a["page"]) - 1].split())[:3500]}
        if name == "read_data_sheet":
            return {"text": self.basis}
        if name in ("run_trapped", "trapped_capacity", "pressure_history"):
            return self._trapped_tool(name, a)
        if name in ("run_grid", "grid_capacity", "n_minus_1"):
            if not _is_grid(self.cfg):
                return {"error": f"{name} is for transmission-grid cases (engine pandapower)"}
            if name == "run_grid":
                if isinstance(a.get("spec"), str):
                    try:
                        a["spec"] = json.loads(a["spec"])
                    except json.JSONDecodeError as e:
                        return {"error": f"spec is not valid JSON ({e}); send it as an object"}
                spec = {**a["spec"], "grid": True}
                label = a.get("label") or f"run{len(self.runs) + 1}"
                label = f"{label}-{len(self.runs) + 1}" if label in self.runs else label
                r = grid.run(spec, float(a.get("scale") or 1.0))
                self.runs[label] = {"spec": spec, "purpose": a.get("purpose", ""), "scale": a.get("scale") or 1.0, "result": r}
                return {"label": label, **r}
            run = self.runs.get(a.get("label"))
            if not run:
                return {"error": f"unknown label; logged: {list(self.runs)}"}
            try:
                spec = patch(run["spec"], a.get("changes") or []) if a.get("changes") else run["spec"]
            except ValueError as e:
                return {"error": str(e)}
            if name == "grid_capacity":
                run["capacity"] = grid.capacity(spec)
                return {"label": a["label"], **run["capacity"]}
            return {"label": a["label"], **grid.n_minus_1(spec, float(a.get("scale") or 1.0), a.get("elements"))}
        if name == "run_process":
            if _is_watertap(self.cfg):
                return {"error": "run_process is for DWSIM cases; this case uses run_ro (WaterTAP)"}
            if _is_trapped(self.cfg):
                return {"error": "run_process is for flowsheet cases; this case uses run_trapped"}
            if _is_grid(self.cfg):
                return {"error": "run_process is for DWSIM cases; this case uses run_grid (pandapower)"}
            if isinstance(a.get("spec"), str):  # the model sometimes sends the spec as JSON text
                try:
                    a["spec"] = json.loads(a["spec"])
                except json.JSONDecodeError as e:
                    return {"error": f"spec is not valid JSON ({e}); send it as an object"}
            label = a.get("label") or f"run{len(self.runs) + 1}"
            label = f"{label}-{len(self.runs) + 1}" if label in self.runs else label
            r = process.run(a["spec"], float(a.get("scale") or 1.0))
            self.runs[label] = {"spec": a["spec"], "purpose": a.get("purpose", ""), "scale": a.get("scale") or 1.0, "result": r}
            return {"label": label, **r}
        if name == "process_capacity":
            if _is_watertap(self.cfg):
                return {"error": "process_capacity is for DWSIM cases; this case uses ro_capacity (WaterTAP)"}
            r = self.runs[a["label"]]
            r["capacity"] = self._capacity_of(r["spec"])
            return {"label": a["label"], **r["capacity"]}
        if name == "morning_check":
            return self.morning_check() or {"note": "no historian mapping for this project"}
        if name == "troubleshoot":
            return self.troubleshoot(a["equipment"], a.get("reading_C"))
        if name == "historian":
            if not self.cfg.get("historian"):
                return {"note": "no historian export in this project"}
            return historian(ROOT / "cases" / self.name / self.cfg["historian"], a.get("tags"), a.get("start"), a.get("end"))
        if name == "annual_energy":
            return annual_energy(self.runs[a["label"]]["spec"], a["units"], a["bins"], a.get("price_per_kWh"))
        if name == "relief_scan":
            if not self.cfg.get("pid"):
                return {"error": "the relief scan needs a smart (DEXPI) P&ID; this drawing is a PDF read by vision"}
            return pid.relief_scan(DATA / self.cfg["pid"])
        if name == "check_coverage":
            r = self.runs.get(a["label"])
            if not r:
                return {"error": f"unknown label; logged: {list(self.runs)}"}
            if _is_watertap(self.cfg):
                return ro_coverage(self.pid, r["spec"], (self.built or {}).get("mapping") if self.built else None)
            if not self.pid:
                return {"note": "no drawing to compare with"}
            return coverage(self.pid, r["spec"])
        if name == "bubble_pressure":
            return process.bubble(a["compounds"], a["x"], a["T_C"])
        if name == "brine_bpe":
            return brine.bpe(float(a["p_bar"]), a.get("x_NaCl"))
        if name == "blocked_in_pressure":
            return process.blocked_in(a["compounds"], a["x"], a["T1_C"], a["P1_bar"], a["T2_C"])
        if name == "sweep":
            return self.sweep(a["label"], a["path"], a["values"], float(a.get("scale") or 1.0), a.get("title"))
        if name == "get_spec":
            r = self.runs.get(a["label"])
            return {"label": a["label"], "spec": r["spec"]} if r else {"error": f"unknown label; logged: {list(self.runs)}"}
        if name == "report_gap":
            return self.add_gap(a.get("what"), a.get("why"), a.get("needed"))
        if name == "run_ro":
            if self.cfg.get("engine") != "watertap":
                return {"error": "run_ro is for cases with engine watertap"}
            if isinstance(a.get("spec"), str):
                try:
                    a["spec"] = json.loads(a["spec"])
                except json.JSONDecodeError as e:
                    return {"error": f"spec is not valid JSON ({e}); send it as an object"}
            label = a.get("label") or f"run{len(self.runs) + 1}"
            label = f"{label}-{len(self.runs) + 1}" if label in self.runs else label
            r = ro.run(a["spec"], float(a.get("scale") or 1.0))
            self.runs[label] = {"spec": a["spec"], "purpose": a.get("purpose", ""), "scale": a.get("scale") or 1.0, "result": r}
            return {"label": label, **r}
        if name == "ro_capacity":
            if self.cfg.get("engine") != "watertap":
                return {"error": "ro_capacity is for cases with engine watertap"}
            r = self.runs[a["label"]]
            r["capacity"] = ro.capacity(r["spec"])
            return {"label": a["label"], **r["capacity"]}
        if name == "ro_normalize":
            if self.cfg.get("engine") != "watertap":
                return {"error": "ro_normalize is for cases with engine watertap"}
            try:
                return ro.normalize(a["actual"], a["standard"])
            except (KeyError, ValueError, TypeError) as e:
                return {"error": str(e)}
        raise ValueError(f"unknown tool {name}")

    def read_drawing(self):
        """A PDF schematic: Muse vision reads it once into the P&ID structure (cached)."""
        from . import pidvision
        t0, usd0 = time.time(), llm.spent()
        self.pid = {**pidvision.read(DATA / self.cfg["pid_pdf"], self.cfg.get("pid_page", 1) - 1, self.cfg.get("vision_model", "muse-spark-1.3")),
                    "seconds": round(time.time() - t0), "cost_usd": round(llm.spent() - usd0, 4)}
        self.pid_file.write_text(json.dumps(self.pid, indent=1))
        audit.append(self.name, "read_drawing", None, "PDF schematic read by Muse vision", {"model": self.pid["model"], "equipment": len(self.pid["equipment"])})
        return self.pid

    def confirm_read(self, raw, user=None, reason=None):
        """The engineer checks Muse's read of a PDF schematic and corrects it; models are built only on a confirmed read.
        Muse's original read stays untouched, so the corrections measure how well vision read the sheet."""
        from . import pidvision
        if not self.pid_file.exists():
            raise ValueError("there is no drawing read to confirm yet")
        if not (reason or "").strip():
            raise ValueError("a reason is required (e.g. 'checked against the drawing and the tender')")
        orig = json.loads(self.pid_file.read_text())
        clean = {"title": orig.get("title", ""), "notes": orig.get("raw", {}).get("notes", []),
                 "loops": [{k: lp.get(k) for k in ("name", "fluid", "supply_C", "return_C")} for lp in raw.get("loops") or [] if lp.get("name")],
                 "equipment": [{"tag": str(e["tag"]).strip(), "label_text": e.get("label_text") or "", "occurrence": int(e.get("occurrence") or 1),
                                "class": e.get("class") or "", "count": int(e.get("count") or 1),
                                "loops": [x.strip() for x in (e.get("loops") if isinstance(e.get("loops"), list) else str(e.get("loops") or "").split(",")) if x.strip()],
                                "capacity_kW": e.get("capacity_kW"), "flow_gpm": e.get("flow_gpm"), "notes": e.get("notes") or "", "box": e.get("box") or []}
                               for e in raw.get("equipment") or [] if str(e.get("tag") or "").strip()],
                 "connections": [{"from": c["from"], "to": c["to"], "loop": c.get("loop") or "",
                                  "inline": c.get("inline") if isinstance(c.get("inline"), list) else [x.strip() for x in str(c.get("inline") or "").split(",") if x.strip()]}
                                 for c in raw.get("connections") or [] if c.get("from") and c.get("to")]}
        tags = {e["tag"] for e in clean["equipment"]}
        bad = [f"{c['from']} -> {c['to']}" for c in clean["connections"] if c["from"] not in tags or c["to"] not in tags]
        if bad:
            raise ValueError("connections refer to equipment not in the list: " + ", ".join(bad[:5]))
        corr = read_corrections(orig.get("raw", {}), clean)
        self.pid = {**orig, "raw": clean, **pidvision.overview_of(clean), "confirmed": True, "corrections": corr,
                    "positions": {t: p for t, p in (orig.get("positions") or {}).items() if t in tags}}
        self.confirmed_file.write_text(json.dumps(self.pid, indent=1))
        audit.append(self.name, "confirm_read", user, reason, {"corrections": len(corr), "items": corr[:20]})
        return {"corrections": corr, "equipment": len(clean["equipment"]), "connections": len(clean["connections"])}

    def _trapped_tool(self, name, a):
        if not _is_trapped(self.cfg):
            return {"error": f"{name} is for blocked-in segment cases (engine trapped)"}
        if name == "run_trapped":
            if isinstance(a.get("spec"), str):
                try:
                    a["spec"] = json.loads(a["spec"])
                except json.JSONDecodeError as e:
                    return {"error": f"spec is not valid JSON ({e}); send it as an object"}
            label = a.get("label") or f"run{len(self.runs) + 1}"
            label = f"{label}-{len(self.runs) + 1}" if label in self.runs else label
            try:
                r = trapped.run(a["spec"], float(a.get("scale") or 1.0))
            except (KeyError, ValueError, TypeError) as e:
                return {"error": f"{type(e).__name__}: {e}"}
            self.runs[label] = {"spec": a["spec"], "purpose": a.get("purpose", ""), "scale": a.get("scale") or 1.0, "result": r}
            return {"label": label, **{k: v for k, v in r.items() if k != "series_h_psig"},
                    "series_h_psig": r["series_h_psig"][::3]}
        r = self.runs.get(a.get("label"))
        if not r:
            return {"error": f"unknown label; logged: {list(self.runs)}"}
        if name == "trapped_capacity":
            r["capacity"] = trapped.capacity(r["spec"])
            return {"label": a["label"], **r["capacity"]}
        from . import artifacts, charts
        lim = next(iter((r["spec"].get("limits") or {}).values()), {})
        title = a.get("title") or f"{self.cfg['title'][:50]}: pressure while blocked in"
        svg = charts.pressure_time_svg(title, r["result"]["series_h_psig"], lim.get("design_psig"), lim.get("burst_psig"),
                                       float(r["spec"].get("hours") or 0) * float(r.get("scale") or 1.0))
        seg = next(iter(r["result"]["units"].values()))
        return artifacts.save(self.name, "chart", title, {"pressure.svg": svg, "pressure.json": json.dumps(r["result"]["series_h_psig"])},
                              by=self.model, request=f"pressure history of {a['label']}", sources=[a["label"]],
                              summary="; ".join(f"{k} {v}" for k, v in seg.items()
                                                if k in ("P_psig", "hours", "liquid_full_h", "design_reached_h", "burst_reached_h")))

    def _build_prompt(self):
        """System and user messages for build(). DWSIM text stays byte-stable; WaterTAP gets an SWRO prompt."""
        if _is_trapped(self.cfg):
            return ("You are a process safety engineer modelling a blocked-in liquefied-gas pipe segment. " + RULES,
                    f"Unit: {self.cfg['title']}\n\n" + BUILD_TRAPPED, SUBMIT_MODEL_TRAPPED)
        if _is_grid(self.cfg):
            return ("You are a power-system engineer building a load-flow model of a transmission grid area. " + RULES,
                    f"Area: {self.cfg['title']}\n\n" + BUILD_GRID, SUBMIT_MODEL_GRID)
        if _is_watertap(self.cfg):
            return ("You are a process engineer building a seawater reverse-osmosis model with WaterTAP. " + RULES,
                    f"Unit: {self.cfg['title']}\n\n" + BUILD_WATERTAP, SUBMIT_MODEL_RO)
        return ("You are a process engineer building a steady-state simulation model of a unit from its P&ID. " + RULES,
                f"Unit: {self.cfg['title']}\n\n" + BUILD_DWSIM, SUBMIT_MODEL)

    def _review(self, spec, result, mapping=None, assumptions=None):
        if _is_trapped(self.cfg):
            return review_trapped(spec, result)
        if _is_grid(self.cfg):
            return grid.review(spec, result, self.basis)
        if _is_watertap(self.cfg):
            return review_ro(spec, result, self.pid, self.basis, mapping, assumptions)
        return review_model(spec, result, self.pid, self.basis)

    def _coverage(self, spec, mapping=None):
        if _is_trapped(self.cfg) or _is_grid(self.cfg):
            return None
        if _is_watertap(self.cfg):
            return ro_coverage(self.pid, spec, mapping)
        return coverage(self.pid, spec) if self.pid else None

    def sweep(self, label, path, values, scale=1.0, title=None):
        """Re-solve one logged run over values of one input; log each solve as a run and save a chart artifact."""
        from . import artifacts, charts
        base = self.runs.get(label)
        if not base:
            return {"error": f"unknown label; logged: {list(self.runs)}"}
        values = [float(v) for v in values][:12]  # ponytail: 12 solves cap one request's simulator time
        rows, util = [], {}
        for v in values:
            run_label = f"{label}~{path}={v:g}"
            try:
                spec = patch(base["spec"], [{"path": path, "value": v}])
                r = self._solve(spec, scale)
            except Exception as e:  # noqa: BLE001 - a value that does not solve is reported, the sweep goes on
                rows.append({"value": v, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            self.runs[run_label] = {"spec": spec, "purpose": f"sweep {path}", "scale": scale, "result": r}
            checks = {f'{c["id"]} {c["check"]}': c["utilisation"] for c in r.get("checks", []) if isinstance(c.get("utilisation"), (int, float))}
            for k, u in checks.items():
                util.setdefault(k, {})[v] = u
            top = sorted(checks.items(), key=lambda kv: -kv[1])[:4]
            rows.append({"value": v, "run": run_label, "errors": r.get("errors", [])[:2],
                         "tightest": [{"check": k, "utilisation": round(u, 3)} for k, u in top]})
        keep = sorted(util, key=lambda k: -max(util[k].values()))[:5]
        if not keep:
            return {"rows": rows, "note": "no limit checks solved"}
        title = title or f"{self.cfg['title'][:40]}: sweep of {path} at {scale:g}x"
        svg = charts.sweep_svg(title, path, values, {k: [util[k].get(v) for v in values] for k in keep})
        meta = artifacts.save(self.name, "chart", title, {"sweep.svg": svg, "sweep.json": json.dumps({"path": path, "scale": scale, "rows": rows}, indent=1)},
                              by=self.model, request=f"sweep {path} over {values}", sources=[r.get("run") for r in rows if r.get("run")],
                              summary=f"tightest at the extremes: {rows[0].get('tightest', [{}])[:1]} ... {rows[-1].get('tightest', [{}])[:1]}")
        return {**meta, "rows": rows}

    def _solve(self, spec, scale=1.0):
        if _is_trapped(self.cfg):
            return trapped.run(_trapped_spec(self.cfg, spec), scale)
        if _is_grid(self.cfg):
            return grid.run(spec, scale)
        return ro.run(spec, scale) if _is_watertap(self.cfg) else process.run(spec, scale)

    def build(self):
        """The agent reads the P&ID and data sheet and builds + calibrates the process model itself."""
        if getattr(self, "revisions", []):
            raise ValueError("cannot rebuild while revisions exist; archive or explicitly reset the revision history first")
        if self.pid is None and self.cfg.get("pid_pdf"):
            self.read_drawing()
        if self.cfg.get("pid_pdf") and not (self.pid or {}).get("confirmed"):
            raise ValueError("confirm the drawing read first: check Muse's reading of the schematic and correct it before a model is built")
        t0, usd0 = time.time(), llm.spent()
        llm.set_tag("plant:" + self.name)
        self._phase = "build"
        system, user, submit_tool = self._build_prompt()
        sub = self.loop("build", system, user, self.tools() + [submit_tool], "submit_model", 30)
        run = self.runs.get(sub["label"]) or list(self.runs.values())[-1]
        reviewed = self._review(run["spec"], run.get("result"), sub.get("mapping"), sub.get("assumptions"))
        if reviewed["blocking"]:
            raise RuntimeError("submitted model still has blocking review findings: " +
                               "; ".join(f["check"] for f in reviewed["findings"] if f["severity"] == "block"))
        cov = self._coverage(run["spec"], sub.get("mapping"))
        self.built = {"label": sub["label"] if sub["label"] in self.runs else list(self.runs)[-1], "spec": run["spec"],
                      "result": run["result"], "mapping": sub.get("mapping"), "calibration": sub.get("calibration"),
                      "assumptions": sub.get("assumptions"), "model": self.model, "engine": _simulator_name(self.cfg),
                      "coverage": cov,
                      "read_corrections": len((self.pid or {}).get("corrections") or []), "seconds": round(time.time() - t0),
                      "cost_usd": round(llm.spent() - usd0, 4), "at": time.strftime("%Y-%m-%d %H:%M"),
                      "review": reviewed, "review_status": reviewed["status"], "gaps": self.gaps}
        self.model_file.write_text(json.dumps(self.built, indent=1))
        self.revisions = []
        self.rev_file.write_text("[]")
        audit.append(self.name, "build", None, "model built from the P&ID and data sheet",
                     {"label": self.built["label"], "model": self.model, "engine": self.built["engine"],
                      "review_status": reviewed["status"],
                      "coverage_missing": (self.built["coverage"] or {}).get("missing_connections")
                                          or (self.built["coverage"] or {}).get("missing_equipment")})
        self._audit_review(reviewed, None, "model built")
        self._state = {}
        return self.built

    def add_gap(self, what, why, needed):
        saved = record_gap(self.model_file.with_name("gaps.json"), what, why, needed, phase=getattr(self, "_phase", None))
        if saved.get("saved"):
            self.gaps = load_gaps(self.model_file.with_name("gaps.json"))
            if self.built is not None:
                self.built["gaps"] = self.gaps
            audit.append(self.name, "report_gap", None, saved["gap"]["what"],
                         {"why": saved["gap"]["why"], "needed": saved["gap"]["needed"], "phase": saved["gap"]["phase"]})
        return saved

    def _audit_review(self, reviewed, user, reason):
        audit.append(self.name, "model_review", user, reason, {
            "status": reviewed["status"], "blocking": reviewed["blocking"],
            "findings": [{"severity": f["severity"], "check": f["check"], "evidence": f["evidence"]} for f in reviewed["findings"]]})

    def _review_run(self, label):
        run = self.runs.get(label) if label else None
        if run is None and self.runs:
            run = list(self.runs.values())[-1]
        if not run:
            empty = {"feed": {}, "stages": []} if _is_watertap(self.cfg) else {"units": [], "feeds": {}}
            return self._review(empty, None)
        return self._review(run["spec"], run.get("result"), (self.built or {}).get("mapping") if self.built else None,
                            (self.built or {}).get("assumptions") if self.built else None)

    def loop(self, phase, system, user, tools, submit_name, max_steps):
        self._phase = phase
        if phase != "build" or submit_name != "submit_model":
            return super().loop(phase, system, user, tools, submit_name, max_steps)
        return self._build_loop(phase, system, user, tools, submit_name, max_steps)

    def _build_loop(self, phase, system, user, tools, submit_name, max_steps):
        """Same agent loop as Study.loop, but a blocked submit_model comes back as a tool result.
        The fix round is at most 8 further steps and every later submission is reviewed too."""
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        step, limit, fixing = 0, max_steps, False
        while step < limit:
            self.steps += 1
            if not fixing and step == max_steps - 3:
                messages.append({"role": "user", "content": f"Step limit near. Call {submit_name} now with what you have."})
            if fixing and step == limit - 3:
                messages.append({"role": "user", "content": "Fix round is nearly done. Call submit_model now. If the spec cannot express "
                                 "the fix, call report_gap instead of approximating or changing a documented limit."})
            available = tools
            if _is_watertap(self.cfg) and step >= limit - 3:
                available = [t for t in tools if t["function"]["name"] in (submit_name, "report_gap")]
            msg = llm.complete(self.model, compact(messages), tools=available)
            self.log.write(json.dumps({"phase": phase, "step": step, "assistant": msg}) + "\n")
            if not msg["tool_calls"] and msg.get("content") and "invoke name=" in msg["content"]:
                msg = {**msg, "tool_calls": text_tool_calls(msg["content"]), "content": ""}
            if msg.get("content"):
                self.emit({"kind": "say", "text": msg["content"]})
            if not msg["tool_calls"]:
                messages += [{"role": "assistant", "content": msg["content"] or ""},
                             {"role": "user", "content": f"Use the tools. Finish by calling {submit_name}."}]
                step += 1
                continue
            messages.append({"role": "assistant", "content": msg["content"] or "", "tool_calls": [
                {"id": t["id"], "type": "function", "function": {"name": t["name"], "arguments": t["arguments"]}}
                for t in msg["tool_calls"]]})
            images, rejected = [], False
            for t in msg["tool_calls"]:
                try:
                    args = unstring(json.loads(t["arguments"] or "{}"))
                except json.JSONDecodeError as e:
                    args, result = {}, {"error": f"arguments are not valid JSON: {e}"}
                else:
                    if t["name"] == submit_name:
                        blocks = [f for f in self._review_run(args.get("label"))["findings"] if f["severity"] == "block"]
                        if blocks:
                            if not fixing:
                                limit = step + 1 + 8
                            fixing, rejected = True, True
                            result = {"accepted": False, "review_status": "model needs review",
                                      "instruction": "Blocking model-review findings. Fix the flowsheet and call submit_model again. "
                                                     "If the spec cannot express the physics or the change you need, call report_gap "
                                                     "instead of approximating or changing a documented limit.",
                                      "findings": [{"severity": f["severity"], "check": f["check"], "evidence": f["evidence"],
                                                    "items": f.get("items")} for f in blocks[:8]]}
                        else:
                            self.log.write(json.dumps({"phase": phase, "submit": args}) + "\n")
                            self.log.flush()
                            print(f"  {phase}: submitted after {step + 1} steps")
                            return args
                    else:
                        try:
                            result = self.call(t["name"], args)
                        except Exception as e:  # tool errors go back to the engineer, as they would in real work
                            result = {"error": f"{type(e).__name__}: {e}"}
                if isinstance(result, dict) and "image" in result:
                    images.append(result.pop("image"))
                    result = {"note": f"page {args.get('page')} image attached below"}
                print(f"  {phase}> {t['name']}({json.dumps(args)[:120]}) -> {json.dumps(result)[:140]}")
                self.log.write(json.dumps({"phase": phase, "tool": t["name"], "args": args, "result": result}) + "\n")
                self.emit({"kind": "tool", "name": t["name"], "args": args, "result": result})
                messages.append({"role": "tool", "tool_call_id": t["id"], "content": json.dumps(result)})
                if rejected:
                    break
            for url in images:
                messages.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]})
            self.log.flush()
            step += 1
        raise RuntimeError(f"{phase}: no {submit_name} after {step} steps")

    def verify(self, p):
        """Re-solve a proposal in DWSIM at the target throughput. It is verified when every limit of the equipment it targets
        is within 100 % and it pushes no other limit over 100 % that was within it before.

        Changes are canonicalized first. A proposal that fails that check is unverified with capacity_multiple left as None.
        A solved proposal also carries a calculation record; capacity_multiple remains the after value."""
        target = float(self.cfg.get("target_scale", 1.0))
        simulator = _simulator_name(self.cfg)
        norm_errors = normalize_proposal(p, self.spec, getattr(self, "runs", None) or {})
        changes = p.get("changes") or []
        is_ro = ro_changes.is_ro(self.spec)
        new = ro_changes.added_trains(changes, self.spec) if is_ro else added_equipment(changes)
        if norm_errors:
            return _reject_proposal(p, target, "; ".join(norm_errors), new, simulator, norm_errors)
        loosened = limit_changes(p)
        invalid = change_errors(self.spec, changes)
        if loosened or invalid:  # a documented rating does not move without a physical change behind it
            why = ("changes a documented limit (" + ", ".join(loosened) + "): a rating only changes with a physical "
                   "modification and its own evidence, so this cannot be verified in the simulator") if loosened else "; ".join(invalid)
            return _reject_proposal(p, target, why, new, simulator)
        before_state = self.state(target)
        before = {(c["id"], c["check"]): c["utilisation"] for c in before_state["checks"] if "utilisation" in c}
        before_cap = self._capacity_of(self.spec)
        spec = patch(self.spec, changes)
        at = self._solve(spec, target)
        cap = self._capacity_of(spec)
        over = [c for c in at["checks"] if c.get("utilisation", 0) > 1.0]
        tag = p.get("tag")
        affected = {tag} if tag else set()
        for ch in ([] if is_ro else changes):
            if ch.get("path"):
                affected.add(ch["path"].split(".", 2)[1])
            elif ch.get("add_unit"):
                affected.add(ch["add_unit"]["id"])
            elif ch.get("reroute"):
                affected.add(ch["reroute"]["unit"])
        if is_ro:  # RO paths are block.field / stages.<id>.field: map them to the ids their checks carry
            affected = ({tag} if tag else set()) | ro_changes.affected(self.spec, changes)
            affected |= {i for i in ro_changes.ids(self.spec) if tag and i.startswith(tag)}  # tag RO-201 covers RO-201-stage2
        own = [c for c in over if c["id"] in affected]
        broke = [c for c in over if before.get((c["id"], c["check"]), 0) <= 1.0]
        calculation = _calculation(p, target, before_cap, cap, before, at, spec, new, simulator)
        after_checks = {(c["id"], c["check"]): c["utilisation"] for c in at.get("checks") or [] if "utilisation" in c}
        removed = ro_changes.removed(self.spec, changes) if is_ro else set()  # e.g. a second pass switched off
        # a failed solve has no checks at all: the solver error is the reason, not vanished checks
        disappeared = [] if at.get("errors") else [{"id": uid, "check": check} for uid, check in before
                                                    if (uid, check) not in after_checks and uid not in removed]
        unchecked = [c for c in at.get("checks") or [] if c.get("id") in affected and
                     c.get("check") == "no limit check for this unit type" and c.get("type") not in ROUTING_UNITS]
        invalid_reason = None
        if disappeared:
            invalid_reason = "proposal removes existing limit checks: " + ", ".join(f"{c['id']} {c['check']}" for c in disappeared)
        elif unchecked:
            invalid_reason = "proposal adds or changes equipment with no engineering limit check: " + ", ".join(c["id"] for c in unchecked)
        if invalid_reason:
            calculation.setdefault("errors", []).append(invalid_reason)
        model_label = self.built.get("label") if isinstance(getattr(self, "built", None), dict) else None
        if model_label:
            calculation["model_label"] = model_label
        after = cap.get("capacity_multiple") if isinstance(cap, dict) else None
        return {"verified": not invalid_reason and not at["errors"] and not own and not broke, "fixes": tag,
                "still_over": own, "breaks": broke, "disappeared_checks": disappeared,
                "capacity_multiple": after, "limited_by": cap.get("limited_by") if isinstance(cap, dict) else None,
                "reaches_target": not invalid_reason and not over and not at["errors"], "over_limits_at_target": over,
                "target_scale": target, "new_equipment": new, "calculation": calculation,
                **({"unverified_reason": invalid_reason} if invalid_reason else {})}

    def ask(self, text, context=None, second_opinion=False):
        """Answer a request; with second_opinion the open-weights model answers it independently on the same model and
        tools, and the two answers are compared deterministically (no third model picks a winner)."""
        ans = self._ask_once(text, context)
        if second_opinion:
            main = self.model
            self.model = OPEN_MODEL
            try:
                other = self._ask_once(text, context)
                ans["second_opinion"] = {"model": OPEN_MODEL, "answer": other, "comparison": compare_answers(ans, other)}
            except Exception as e:  # noqa: BLE001 - the main answer stands; the missing second opinion is shown
                ans["second_opinion"] = {"model": OPEN_MODEL, "error": f"{type(e).__name__}: {e}"}
            finally:
                self.model = main
        self.answers.append(ans)
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "answers.json").write_text(json.dumps(self.answers, indent=1))
        return ans

    def _ask_once(self, text, context=None):
        if not self.built:
            self.build()
        self._phase = "ask"
        self._artifacts = []
        t0, usd0 = time.time(), llm.spent()
        llm.set_tag("plant:" + self.name)
        brief = {"unit": self.cfg["title"], "target_throughput_multiple": self.cfg.get("target_scale"),
                 "model_label": self.built["label"], "model_mapping": self.built.get("mapping"),
                 "tag_aliases": {**(self.cfg.get("model_aliases") or {}), "note": self.cfg.get("model_aliases_note")} if self.cfg.get("model_aliases") else None,
                 "revisions": [r["title"] for r in self.revisions],
                 # earlier answers with their index, so a document or drawing request can point at one instead of re-solving
                 "earlier_answers": [{"answer": i, "headline": x.get("headline"), "summary": x.get("summary"),
                                      "verified_proposals": [p.get("title") for p in (x.get("proposals") or []) if isinstance(p, dict) and p.get("verified")]}
                                     for i, x in list(enumerate(self.answers))[-4:]]}
        ans = self.loop("ask", "You are the process engineering copilot inside the engineer's P&ID workspace. The calibrated DWSIM "
                        "model is preloaded (get_spec, then modify and re-run). The engineer may ask a question OR give an instruction: change "
                        "or add equipment in the model, draw it, write a document, or analyse a scenario. Do what is asked with "
                        "the tools: a model change the engineer asks for is returned as a proposal (a draft the workspace re-solves; "
                        "propose it even if it does not reach the target, and report its effect); a what-if over a range of a value "
                        "uses sweep. When the request asks for a document (data sheet, calculation sheet, summary for a manager, "
                        "work order), call make_document once per document FIRST, pointing `answer` at the earlier answer that "
                        "holds the analysis (earlier_answers lists them with their index); do not redo an analysis that an "
                        "earlier answer already verified. Drawings use their drawing tool when available. The summary names "
                        "the files produced. Answer quickly and precisely and finish with "
                        "`answer`: a plain headline, calc cards, highlights on P&ID tags, and for a fix, proposals as model "
                        "changes (paths into the spec) that respect every utility and frame limit in the data sheet. Give one "
                        "proposal per limiting equipment item, each with its tag. " + (ro_changes.CHANGE_HELP if _is_watertap(self.cfg) else CHANGE_HELP) + " Prefer the cheapest fix that works: operating "
                        "changes within documented limits (levels, setpoints, utility flows), then cleaning a fouled exchanger "
                        "back to its documented clean performance, and only then new equipment. An operating strategy that changes "
                        "with weather or season (floating head pressure, economiser hours, chilled-water reset) is not a single model "
                        "change: evaluate it with annual_energy over the bins and report it in a card, and propose only changes "
                        "that hold at every condition. Answer every part of the request. Write for a non-specialist; "
                        "no acronyms in the headline. Label every card input with its basis (documented, measured, computed, assumed). If "
                        "a value that decides the answer is missing or only assumed, say the conclusion is provisional and add a "
                        "field check: what to measure, where, and which conclusion it would change. " + RULES,
                        json.dumps(brief) + "\n\nRequest: " + text + (f"\nContext: {json.dumps(context)}" if context else ""),
                        self.tools() + [ANSWER], "answer", 26 if llm._host(self.model) else 18)  # the open model takes more turns
        for k in ("cards", "highlights", "proposals"):
            ans[k] = ans.get(k) if isinstance(ans.get(k), list) else []
        ans["artifacts"] = list(self._artifacts)  # files the tools produced for this request (documents, drawings, charts)
        aliases = self.cfg.get("model_aliases") or {}
        unit_ids = {u.get("id") for u in self.spec.get("units") or []}
        for p in ans["proposals"]:  # a drawing tag modelled inside another unit (E-201 heats inside V-201) maps to that unit
            for c in (p.get("changes") or []) if isinstance(p, dict) else []:
                k, _, rest = str(c.get("path") or "").partition(".")
                oid, _, fld = rest.partition(".")
                if k == "units" and oid in aliases and oid not in unit_ids:
                    c["path"] = f"units.{aliases[oid]}.{fld}"
                    p.setdefault("normalized_changes", []).append(f"{oid} is modelled inside {aliases[oid]}: path set to {c['path']}")
        for p in ans["proposals"]:
            if isinstance(p, dict):  # canonical changes before `from` is attached and before verify()
                normalize_proposal(p, self.spec, getattr(self, "runs", None) or {}, cited_run_labels(p, ans))
            for c in p.get("changes") or []:  # the value it replaces, for the diff view
                try:
                    if c.get("reroute"):
                        r = c["reroute"]
                        c["from"] = next(u for u in self.spec["units"] if u["id"] == r["unit"]).get(r["field"])
                    elif c.get("path"):
                        k, oid, fld = c["path"].split(".", 2)
                        o = next(u for u in self.spec["units"] if u["id"] == oid) if k == "units" else self.spec.get(k, {}).get(oid, {})
                        c["from"] = o.get(fld)
                except (KeyError, ValueError, StopIteration):
                    c["from"] = None
            try:
                p.update(self.verify(p))
            except Exception as e:  # noqa: BLE001 - a proposal that does not solve is shown as failed
                p.update(verified=False, error=f"{type(e).__name__}: {e}")
        if len(ans["proposals"]) > 1:  # the fixes together: does the unit then reach the target?
            try:
                both = self.verify({"changes": [c for p in ans["proposals"] for c in p.get("changes") or []]})
                ans["combined"] = {k: both[k] for k in ("reaches_target", "capacity_multiple", "limited_by", "over_limits_at_target")}
            except Exception as e:  # noqa: BLE001
                ans["combined"] = {"error": f"{type(e).__name__}: {e}"}
        ans["checks"] = [self.reproduce(r) for r in dict.fromkeys(r for c in ans["cards"] for r in (c.get("runs") or []))]
        ans.update(seconds=round(time.time() - t0), cost_usd=round(llm.spent() - usd0, 4), request=text, model=self.model)
        self._electrical_hook(ans)
        from .revb import refresh_answer_drawings  # drawing hook: re-issue this answer's Rev B drawings with the verified status
        refresh_answer_drawings(self, ans)
        return ans

    def _electrical_hook(self, ans):
        """Verified proposals that add or re-rate a motor carry a one-line electrical check (verify stays process-only)."""
        from . import electrical
        if not (electrical.available() and electrical.config(self.name)):
            return
        for p in ans.get("proposals") or []:
            if p.get("verified") and electrical.motor_proposal(self, p):
                try:
                    e = electrical.for_workspace(self, p["changes"], p.get("target_scale"), title=f"Electrical check: {p.get('title')}")
                    p["electrical"] = {k: e.get(k) for k in ("summary", "svg", "start", "transformers", "transformers_before")}
                    p["electrical"]["over"] = [c for c in e["checks"] if c["utilisation"] > 1]
                    # 'verified' is the process re-solve; the electrical result sits next to it, never hidden by it
                    p["discipline_status"] = {**(p.get("discipline_status") or {}), "electrical": "fail" if p["electrical"]["over"] else "pass"}
                except Exception as ex:  # noqa: BLE001 - the process answer stands; the electrical check says why it failed
                    p["electrical"] = {"error": f"{type(ex).__name__}: {ex}"[:300]}
                    p["discipline_status"] = {**(p.get("discipline_status") or {}), "electrical": "open"}
                p["verified_scope"] = "process"

    def names(self):
        """display_names, with each utility named from the P&ID fluid code and the data sheet (e.g. 'Cooling water to H1007')."""
        import re as _re
        n = display_names(self.spec)
        codes = {str(l.get("line")): (l.get("fluid_code") or "").rstrip("abcdefghijklmnopqrstuvwxyz") for l in (self.pid or {}).get("lines") or []}
        for sid, f in (self.spec.get("feeds") or {}).items():
            if not f.get("utility"):
                continue
            code = next((codes[d] for d in _re.findall(r"\d{4,}", sid) if codes.get(d)), None)
            m = code and _re.search(r"([A-Z][a-z]+(?: [a-z]+)?)\s+to\s+\S+\s*\(fluid " + _re.escape(code) + r"\)", self.basis)
            fluid = m.group(1) if m else None
            if not fluid:
                continue
            for k, v in list(n.items()):
                if v == n[sid] or (k != sid and v.startswith("Utility return from") and k.startswith(("s", "S")) and
                                   any(codes.get(d) == code for d in _re.findall(r"\d{4,}", k))):
                    n[k] = v.replace("Utility supply", fluid).replace("Utility return", fluid + " return")
        return n

    def morning_check(self, refresh=False):
        """The morning check (plantagent.health): cached, because it re-solves the model ~30 times."""
        from . import health
        f = self.model_file.with_name("health.json")
        if refresh or not f.exists():
            if not (ROOT / "cases" / self.name / "historian_map.json").exists():
                return None
            f.write_text(json.dumps(health.check(self.name), indent=1, default=str))
            if refresh and self.built and "forecast" in json.loads((ROOT / "cases" / self.name / "historian_map.json").read_text()):
                self.forecast_fouling(refresh=True)
        return json.loads(f.read_text())

    def forecast_fouling(self, equipment=None, as_of_day=None, refresh=False):
        """Fouling forecast (plantagent.forecast) plus its chart as an artifact."""
        from . import artifacts, charts, forecast
        r = forecast.forecast(self, equipment, as_of_day, refresh=refresh)
        title = f"{r['tag']} fouling forecast as of {r['as_of'][:10]}"
        meta = artifacts.save(self.name, "chart", title, {"forecast.svg": charts.fouling_svg(title, r),
                                                          "forecast.json": json.dumps(r, indent=1)},
                              by="PlantAgent (deterministic)", sources=[r["source"], r["model"], r["simulator"]],
                              summary=forecast.headline(r))
        return {**{k: v for k, v in r.items() if k != "points"}, "headline": forecast.headline(r),
                "id": meta["id"], "kind": meta["kind"], "title": meta["title"], "files": meta["files"], "summary": meta["summary"]}

    def troubleshoot(self, equipment, reading=None, scale=None):
        """Rank the causes of an exchanger's process outlet running out of spec (plantagent.diagnose). The symptom is the
        engineer's reading (or the historian's last day); the other readings come from the historian's last day."""
        from . import diagnose
        key = hashlib.sha1(json.dumps([self.spec, equipment, reading, scale], sort_keys=True, default=str).encode()).hexdigest()
        cache = self.model_file.with_name("troubleshoot_cache.json")
        stored = json.loads(cache.read_text()) if cache.exists() else {}
        if key in stored:  # the same model, equipment and reading: the fitted result does not change
            return stored[key]
        m = json.loads((ROOT / "cases" / self.name / "historian_map.json").read_text())
        hx = (m.get("exchangers") or {}).get(equipment)
        if not hx:
            raise ValueError(f"no historian mapping for {equipment}: troubleshooting needs its measured temperatures and flows")
        rows = historian(ROOT / "cases" / self.name / m["file"])
        from .health import load
        data = load(ROOT / "cases" / self.name / m["file"])
        last = [r for r in data if r["day"] >= data[-1]["day"] - 1]
        mean = lambda tag: round(sum(r[tag] for r in last if r.get(tag) is not None) / max(1, sum(r.get(tag) is not None for r in last)), 2)  # noqa: E731
        u = next(x for x in self.spec["units"] if x["id"] == equipment)
        prod = next((k for k, f in self.spec["feeds"].items() if not f.get("utility")), None)
        symptom = {"path": f"streams.{hx['model_out_stream']}.T_C", "value": float(reading) if reading is not None else mean(hx["hot_out"]),
                   "name": f"{equipment} product out"}
        obs = [{"path": f"streams.{u['cold'][1]}.T_C", "value": mean(hx["cold_out"]), "name": "utility return", "sigma": 0.3},
               {"path": f"streams.{u['cold'][0]}.T_C", "value": mean(hx["cold_in"]), "name": "utility supply", "sigma": 0.3},
               {"path": f"streams.{u['hot'][0]}.T_C", "value": mean(hx["hot_in"]), "name": f"{equipment} product in", "sigma": 0.3},
               {"path": f"streams.{u['cold'][0]}.m3_h", "value": mean(hx["cold_flow_m3h"]), "name": "utility flow (meter)", "sigma": 0.3}]
        pf = next((k for k in rows["available"] if k.startswith("FI-") and prod and "product" in k.lower()), None)
        if pf and prod:
            obs.append({"path": f"streams.{prod}.m3_h", "value": mean(pf), "name": "product flow (meter)", "sigma": 0.2})
        r = diagnose.diagnose(self.spec, symptom, obs, diagnose.hypotheses_for(self.spec, equipment, names=self.names()),
                              float(scale or 1.0))
        out = {**r, "observations": obs, "source_note": m.get("note", "")}
        cache.write_text(json.dumps({**stored, key: out}, default=str))
        return out

    def whatif(self, changes, scale=None):
        """Preview one change in DWSIM at the current throughput: limit checks before and after. Not a revision."""
        if limit_changes({"changes": changes}):
            raise ValueError("a what-if changes the plant, not its documented limits")
        sc = float(scale or self.cfg.get("target_scale", 1.0))
        before, after = self.state(sc), self._solve(patch(self.spec, changes), sc)
        key = lambda r: {(c["id"], c["check"]): c for c in r["checks"] if "utilisation" in c}  # noqa: E731
        b, a = key(before), key(after)
        return {"scale": sc, "errors": after["errors"], "state_after": after,
                "changes": [{**c, "text": describe_change(self.spec, c)} for c in changes],
                "checks": [{"id": k[0], "check": k[1], "before": b[k]["utilisation"] if k in b else None, "after": a[k]["utilisation"],
                            "value_after": a[k]["value"], "limit": a[k]["limit"], "unit": a[k]["unit"]} for k in a],
                "units_after": after["units"]}

    def existing_state(self, scale):
        """The model as built, before any revision: what the Existing view colours."""
        # Existing = the corrected model before the first design change; model corrections are not plant changes
        first = next((r for r in self.revisions if r.get("kind") != "correction"), None)
        if not first:
            return self.state(scale)
        return {"scale": scale, **self._solve(first["spec_before"], scale)}

    def reproduce(self, label):
        """A cited run counts only if it exists and re-solves to the same result now."""
        r = self.runs.get(label)
        if not r:
            return {"item": f"run {label}", "ok": False, "why": "not in the log"}
        try:
            fresh = self._solve(r["spec"], float(r.get("scale") or 1.0))
        except Exception as e:  # noqa: BLE001
            return {"item": f"run {label}", "ok": False, "why": f"does not re-solve: {e}"}
        if r.get("result") is None:  # a revision saved before results were kept: this solve becomes the reference
            r["result"] = fresh
        same = fresh.get("units") == (r.get("result") or {}).get("units")
        return {"item": f"run {label}", "ok": same, "why": "" if same else "re-solved to a different result"}

    def accept(self, p, user=None, reason=None, answer=None):
        """Accept a verified proposal as a new revision. Revisions are kept on disk and never deleted."""
        if (self.built.get("review") or {}).get("blocking"):
            raise ValueError("the current model has blocking review findings; correct the model before applying plant changes")
        if not (reason or "").strip():
            raise ValueError("a reason for the change is required")
        v = self.verify(p)  # never trust the client's copy
        if not v["verified"]:
            raise ValueError("proposal does not verify in DWSIM: " +
                             (v.get("unverified_reason") or json.dumps(v["over_limits_at_target"])[:300]))
        after = patch(self.built["spec"], p["changes"])
        r = {"rev": len(self.revisions) + 1, "kind": "change", "title": p.get("title"), "changes": p["changes"],
             "spec_before": self.built["spec"], "spec_after": after, "capacity_multiple": v["capacity_multiple"],
             "new_equipment": v["new_equipment"], "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "user": user,
             "reason": reason, "proposed_by": p.get("_by") or self.model}
        if v.get("calculation") is not None:
            r["calculation"] = v["calculation"]
        so = (self.answers[answer].get("second_opinion") or {}) if isinstance(answer, int) and 0 <= answer < len(self.answers) else {}
        details = {"rev": r["rev"], "title": r["title"], "changes": p["changes"],
                   "verified_capacity_multiple": v["capacity_multiple"], "new_equipment": v["new_equipment"],
                   "proposed_by": p.get("_by") or self.model,
                   **({"second_opinion": so["comparison"]["status"], "models_disagree_on": so["comparison"]["disagree"][:8]}
                      if so.get("comparison") else {})}
        if v.get("calculation") is not None:
            details["calculation"] = v["calculation"]
        self._commit(r)
        r["audit"] = audit.append(self.name, "accept", user, reason, details)["hash"]
        if getattr(self, "rev_file", None):
            _write_json(self.rev_file, self.revisions)
        return {**v, "revisions": self.revisions}

    def correct(self, spec, title, user=None, reason=None):
        """An engineer's correction of the built model itself (wrong connection, double-counted unit), not a plant change:
        kept as its own revision kind with an audit entry, so the as-built model and the fix stay visible."""
        if not (reason or "").strip():
            raise ValueError("a reason for the correction is required")
        cap = self._capacity_of(spec)
        r = {"rev": len(self.revisions) + 1, "kind": "correction", "title": title, "changes": [], "spec_before": self.built["spec"],
             "spec_after": spec, "capacity_multiple": cap.get("capacity_multiple"), "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "user": user, "reason": reason}
        self._commit(r)
        r["audit"] = audit.append(self.name, "correct_model", user, reason, {"rev": r["rev"], "title": title,
                                  "capacity_multiple": r["capacity_multiple"]})["hash"]
        if getattr(self, "rev_file", None):
            _write_json(self.rev_file, self.revisions)
        return {"capacity": cap, "revisions": self.revisions}

    def restore(self, rev, user=None, reason=None):
        """Return the model to how it was before revision `rev` (0 = as built). History is kept: the return is itself a
        new revision with its own audit entry."""
        if not (reason or "").strip():
            raise ValueError("a reason for the change is required")
        target = self.revisions[rev - 1]["spec_before"] if 0 < rev <= len(self.revisions) else self._built_spec()
        r = {"rev": len(self.revisions) + 1, "kind": "revert", "title": f"Return to the model before Rev {rev}" if rev else
             "Return to the model as built", "changes": [], "spec_before": self.built["spec"], "spec_after": target,
             "capacity_multiple": None, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "user": user, "reason": reason}
        self._commit(r)
        r["audit"] = audit.append(self.name, "revert", user, reason, {"rev": r["rev"], "to_before_rev": rev})["hash"]
        if getattr(self, "rev_file", None):
            _write_json(self.rev_file, self.revisions)
        return {"revisions": self.revisions}

    def _built_spec(self):
        return json.loads(self.model_file.read_text())["spec"]

    def _commit(self, r):
        # the calibrated label now names the revised model, so its stored result must be the revised one too
        r.setdefault("result_after", self._solve(r["spec_after"]))
        reviewed = self._review(r["spec_after"], r["result_after"], self.built.get("mapping"), self.built.get("assumptions"))
        r["review"] = {"status": reviewed["status"], "blocking": reviewed["blocking"], "findings": reviewed["findings"]}
        self.revisions.append(r)
        self.built = {**self.built, "spec": r["spec_after"], "result": r["result_after"],
                      "engine": self.built.get("engine") or _simulator_name(self.cfg),
                      "review": reviewed, "review_status": reviewed["status"], "gaps": self.gaps}
        self.runs[self.built["label"]] = {"spec": r["spec_after"], "purpose": "calibrated model (current revision)", "result": r["result_after"]}
        _write_json(self.rev_file, self.revisions)
        self._audit_review(reviewed, r.get("user"), r.get("reason") or r.get("title") or "revision")
        self._state = {}

    def state(self, scale=1.0):
        """Solved unit at a throughput multiple: what the P&ID view colours. Cached per spec and scale.
        Without DWSIM installed (a judge's clean clone) the unmodified model replays precomputed DWSIM solutions."""
        if not self.built:
            return None
        key = hashlib.sha1(json.dumps([self.spec, round(scale, 3)], sort_keys=True).encode()).hexdigest()
        if key not in self._state:
            demo = self._demo()
            hit = demo and demo["spec"] == self.spec and min(abs(st["scale"] - scale) for st in demo["states"]) < 0.006
            simulator_available = (grid.available() if _is_grid(self.cfg) else ro.available() if _is_watertap(self.cfg)
                                   else process.available())
            if hit or (demo and demo["spec"] == self.spec and not simulator_available):
                # stored simulator solutions of this exact model: instant first load and clean-clone replay
                near = min(demo["states"], key=lambda st: abs(st["scale"] - scale))
                self._state[key] = {**near, "replayed": True}
            elif _is_watertap(self.cfg):
                self._state[key] = {"scale": scale, **ro.run(self.spec, scale)}
            elif _is_trapped(self.cfg):
                self._state[key] = {"scale": scale, **trapped.run(_trapped_spec(self.cfg, self.spec), scale)}
            elif _is_grid(self.cfg):
                self._state[key] = {"scale": scale, **grid.run(self.spec, scale)}
            elif process.available():
                self._state[key] = {"scale": scale, **process.run(self.spec, scale)}
            else:
                raise RuntimeError("DWSIM is not installed and there are no precomputed solutions for this model")
        return self._state[key]

    def _demo(self):
        f = self.model_file.with_name("states.json")
        return json.loads(f.read_text()) if f.exists() else None

    def precompute(self):
        """Store solved states from 80 % to 150 % throughput, so the slider works without the simulator."""
        states = [{"scale": round(x / 100, 2), **self._solve(self.spec, x / 100)} for x in range(80, 151)]
        self.model_file.with_name("states.json").write_text(json.dumps({"spec": self.spec, "capacity": self._capacity_of(self.spec),
                                                                        "engine": _simulator_name(self.cfg), "states": states}))
        return len(states)

    def capacity(self):
        key = "cap:" + hashlib.sha1(json.dumps(self.spec, sort_keys=True).encode()).hexdigest()
        if key not in self._state:
            demo = self._demo()
            self._state[key] = demo["capacity"] if demo and demo["spec"] == self.spec else self._capacity_of(self.spec)
        return self._state[key]


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "--gaps":
    print(json.dumps(collect_gaps(ROOT / "runs" / "ws"), indent=1))
    raise SystemExit

if __name__ == "__main__" and len(__import__("sys").argv) > 2:
    # python -m plantagent.plant --build <case> [model]   |   --precompute <case>
    import sys
    op, case = sys.argv[1], sys.argv[2]
    w = PlantWorkspace(case, *(sys.argv[3:4] or []))
    if op == "--build":
        b = w.build()
        print(json.dumps({k: b.get(k) for k in ("label", "calibration", "coverage", "seconds", "cost_usd")}, indent=1)[:4000])
        c = w.capacity()
        print("capacity", c.get("capacity_multiple"), c.get("limited_by"), c.get("errors"))
    elif op == "--precompute":
        print(w.precompute(), "stored solutions")
    sys.exit()

if __name__ == "__main__":
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("time,TI1,FI1\n2026-01-01T00:00,10,5\n2026-01-01T01:00,20,\n2026-01-01T02:00,30,7\n")
    h = historian(f.name)
    assert h["tags"]["TI1"]["mean"] == 20 and h["tags"]["FI1"]["n"] == 2 and h["available"] == ["TI1", "FI1"], h
    s = {"units": [{"id": "H1", "type": "hx", "area_m2": 10}], "feeds": {"CW": {"m3_h": 20}}, "limits": {"H1": {"area_m2": 10}}}
    p = patch(s, [{"path": "units.H1.area_m2", "value": 12}, {"path": "feeds.CW.m3_h", "value": 26}])
    assert p["units"][0]["area_m2"] == 12 and p["limits"]["H1"]["area_m2"] == 12 and p["feeds"]["CW"]["m3_h"] == 26
    assert s["units"][0]["area_m2"] == 10
    A = {"highlights": [{"tag": "H1", "severity": "fail"}], "proposals": [{"tag": "H1", "verified": True, "reaches_target": True,
                                                                           "changes": [{"path": "feeds.CW.m3_h", "value": 27}]}]}
    B = {"highlights": [{"tag": "H1", "severity": "fail"}], "proposals": [{"tag": "H1", "verified": True, "reaches_target": True,
                                                                           "changes": [{"path": "feeds.CW.m3_h", "value": 26}]}]}
    assert compare_answers(A, B)["status"] == "agree"
    B["proposals"][0]["changes"] = [{"path": "units.H1.area_m2", "value": 60}]
    cmp = compare_answers(A, B)
    assert cmp["status"] in ("partly", "disagree") and any("units.H1.area_m2" in d for d in cmp["disagree"]), cmp
    o = {"loops": [{"name": "CHW", "fluid": "water", "supply_C": 8, "return_C": 13}],
         "equipment": [{"tag": "PHE", "class": "plate heat exchanger", "count": 2, "loops": ["CHW"], "capacity_kW": 750}],
         "connections": [{"from": "PHE", "to": "RDHX", "loop": "CHW"}]}
    c = {"loops": o["loops"], "equipment": [{**o["equipment"][0]}, {"tag": "CH", "class": "chiller", "count": 2, "loops": ["CHW"], "capacity_kW": 1758}],
         "connections": [{"from": "CH", "to": "PHE", "loop": "CHW"}]}
    assert read_corrections(o, c) == ["equipment added: CH (chiller)", "connection added: CH -> PHE (CHW)", "connection removed: PHE -> RDHX (CHW)"], read_corrections(o, c)
    assert limit_changes({"changes": [{"path": "limits.H1.area_m2", "value": 99}, {"path": "units.H1.area_m2", "value": 12}]}) == ["limits.H1.area_m2"]
    print("ok")
