"""Proposal changes outside the process model: electrical one-line and start-up/transient parameters.

A process change is a path into the DWSIM spec (units.X.field). Some fixes the engineering loop needs live elsewhere:
a bigger tie transformer, a VFD on the new compressor motor, a bigger anti-surge valve. They are proposal changes with
paths

  electrical.<element>.<field>   element: a transformer id (TX-1) or a motor (unit id K-202 or motor id M-P201)
      sn_mva   transformer replaced by a larger one (MVA)           physical change
      tap_percent  transformer off-load tap setting, -10..+10 %      tap change (site work order, no new item)
      start    motor starting method: DOL | SOFT | VFD               physical change (starter / drive)
      cable    motor feeder cable type, one of the case cable_types  physical change
  transient.<param>              the K-202 start-up screen (plantagent/transient.py)
      anti_surge_capacity_frac   anti-surge valve capacity / K-202 design flow   physical change (valve)
      Kp, Ki                     suction-pressure PI gains                        tuning
      start_s                    K-202 start command time, s                      sequence
      boilup_ramp_start_s, boilup_ramp_end_s   boil-up ramp window, s             sequence
      min_speed_frac             VSD minimum speed                                tuning
      speed_ramp_pct_s           VSD speed ramp, % per second                     tuning

The process solve never sees them (plant.patch drops them); the electrical check and the start-up screen apply them as
overlays on the case files, which are not edited. A physical item needs physical_change, like any other physical
change; a value outside its range or an unknown element is refused, so the proposal is not verified.
"""
import copy

PREFIXES = ("electrical", "transient")
STARTS = ("DOL", "SOFT", "VFD")
# param: (transient.DEFAULTS key, lo, hi, physical)
TRANSIENT = {
    "anti_surge_capacity_frac": ("asc_max_q", 0.3, 1.2, True),
    "Kp": ("Kp", 0.05, 20.0, False),
    "Ki": ("Ki", 0.0005, 1.0, False),
    "start_s": ("t_start_s", 0.0, 900.0, False),
    "boilup_ramp_start_s": ("t_load0_s", 0.0, 1500.0, False),
    "boilup_ramp_end_s": ("t_load1_s", 1.0, 3000.0, False),
    "min_speed_frac": ("n_min", 0.5, 0.95, False),
    "speed_ramp_pct_s": ("ramp_pct_s", 0.1, 10.0, False),
}


def is_overlay(c):
    return isinstance(c, dict) and str(c.get("path") or "").split(".", 1)[0] in PREFIXES


def split(changes):
    """(process changes, overlay changes)."""
    changes = list(changes or [])
    return [c for c in changes if not is_overlay(c)], [c for c in changes if is_overlay(c)]


def _parts(c):
    parts = str(c.get("path") or "").split(".", 2)
    return parts if len(parts) == 3 else None


def _motor(cfg, element):
    return next((m for m in cfg.get("motors") or [] if element in (m["unit"], m["id"])), None)


def _new_drives(changes):
    return {c["add_unit"]["id"] for c in changes or [] if isinstance(c, dict) and isinstance(c.get("add_unit"), dict)
            and c["add_unit"].get("type") in ("pump", "compressor")}


def errors(case, changes, all_changes=None, require_evidence=True, known_units=()):
    """Reasons the overlay changes cannot be applied. `all_changes`: the whole design (new drives a motor change may name);
    `known_units`: ids of drives added by other verified proposals or present in the model."""
    from . import electrical
    cfg = electrical.config(case)
    out = []
    drives = _new_drives(all_changes if all_changes is not None else changes) | set(known_units)
    for i, c in enumerate(changes or []):
        p = _parts(c)
        n = i + 1
        if not p or "value" not in c:
            out.append(f"change {n}: path must be electrical|transient.<element>.<field> with a value")
            continue
        kind, element, field = p
        v = c["value"]
        physical = True
        if kind == "electrical":
            if not cfg:
                out.append(f"change {n}: this plant has no one-line diagram (cases/{case}/electrical.json)")
                continue
            tx = next((t for t in cfg.get("transformers") or [] if t["id"] == element), None)
            if field == "sn_mva":
                if not tx:
                    out.append(f"change {n}: unknown transformer {element}")
                elif not isinstance(v, (int, float)) or not tx["sn_mva"] < float(v) <= 4 * tx["sn_mva"]:
                    out.append(f"change {n}: {element} replacement rating must be above {tx['sn_mva']:g} and at most "
                               f"{4 * tx['sn_mva']:g} MVA")
            elif field == "tap_percent":
                physical = False
                if not tx:
                    out.append(f"change {n}: unknown transformer {element}")
                elif not isinstance(v, (int, float)) or not -10 <= float(v) <= 10:
                    out.append(f"change {n}: {element} tap_percent must be within -10..+10 %")
            elif field in ("start", "cable"):
                if not _motor(cfg, element) and element not in drives:
                    known = sorted({m["unit"] for m in cfg.get("motors") or []} | set(drives))
                    out.append(f"change {n}: unknown motor {element}; use the unit id of one of: {', '.join(known)}")
                elif field == "start" and str(v).upper() not in STARTS:
                    out.append(f"change {n}: start must be one of {', '.join(STARTS)}")
                elif field == "cable" and v not in (cfg.get("cable_types") or {}):
                    out.append(f"change {n}: cable must be one of {', '.join(cfg.get('cable_types') or {})}")
            else:
                out.append(f"change {n}: electrical field must be sn_mva or tap_percent (transformer), start or cable (motor)")
                continue
        else:
            spec = TRANSIENT.get(field)
            if element not in ("K-202", "startup") or not spec:
                out.append(f"change {n}: transient path must be transient.startup.<{'|'.join(TRANSIENT)}>")
                continue
            _, lo, hi, physical = spec
            if not isinstance(v, (int, float)) or not lo <= float(v) <= hi:
                out.append(f"change {n}: {field} must be a number in [{lo:g}, {hi:g}]")
        if physical and require_evidence and not str(c.get("physical_change") or "").strip():
            out.append(f"change {n}: {c['path']} is a physical change; state physical_change (what is installed)")
    return out


def electrical(cfg, changes):
    """(one-line config with the overlays applied, motor overrides, upgrade notes). The case file is not changed."""
    ov = [c for c in changes or [] if is_overlay(c) and _parts(c) and _parts(c)[0] == "electrical"]
    if not ov:
        return cfg, [], []
    cfg = copy.deepcopy(cfg)
    overrides, notes = {}, []
    for c in ov:
        _, element, field = _parts(c)
        v = c["value"]
        if field == "sn_mva":
            tx = next(t for t in cfg["transformers"] if t["id"] == element)
            notes.append(f"proposed upgrade {element} {tx['sn_mva']:g} → {float(v):g} MVA (rating to confirm)")
            tx.update(sn_mva=float(v), source=f"PROPOSED replacement: {c.get('physical_change') or ''}".strip())
            continue
        if field == "tap_percent":
            tx = next(t for t in cfg["transformers"] if t["id"] == element)
            notes.append(f"proposed {element} tap {tx.get('tap_percent', 0):g} → {float(v):g} %")
            tx["tap_percent"] = float(v)
            continue
        m = _motor(cfg, element)
        unit = m["unit"] if m else element
        o = overrides.setdefault(unit, {"unit": unit, "source": c.get("physical_change") or c["path"]})
        if m:
            o["kw"] = m["kw"]
        o["start" if field == "start" else "cable"] = str(v).upper() if field == "start" else v
        notes.append(f"proposed {unit} {'start ' + str(v).upper() if field == 'start' else 'feeder cable ' + str(v)}")
    return cfg, list(overrides.values()), notes


def transient_params(changes):
    """transient.run keyword overrides from the design's transient.* changes."""
    out = {}
    for c in changes or []:
        p = _parts(c) if is_overlay(c) else None
        if p and p[0] == "transient" and p[2] in TRANSIENT:
            out[TRANSIENT[p[2]][0]] = float(c["value"])
    return out


def describe(changes):
    return [f"{c['path']} = {c['value']}" for c in changes or [] if is_overlay(c)]
