"""Red team: a second Muse attacks a verified design with credible operating deviations; the simulator decides.

The attacker only proposes scenarios (HAZOP-style deviations of operating inputs, bounded to +/-30 % of the design
value and 0.8-1.1x the target throughput). Every scenario is re-solved with the same limit checks as the envelope
(prefeed.run_envelope). A scenario that breaks a limit or does not solve is a failed check that goes back to the
proposing Muse in the next loop round. The attacker never edits limits, topology or equipment.
"""
import copy
import hashlib
import json
import math
import re
import time
from pathlib import Path

from . import llm
from .plant import _REPLACEMENT_FIELDS, _STRUCTURAL_UNIT_FIELDS, change_errors, patch

# degradation of these ratings is an operating deviation (fouling, worn trays); every other rating is equipment
DEGRADES = {"efficiency", "eff_pct", "U_W_m2K"}

ROOT = Path(__file__).resolve().parent.parent
MAX_SCENARIOS = 8
BAND = 0.30            # an attack moves an operating input at most +/-30 % from the design value
DT_C = 15.0           # temperatures move by an absolute band: a percentage of a Celsius value has no physical meaning
SCALE = (0.80, 1.10)   # throughput of an attack, relative to the target: the envelope band, not a capacity search


def _numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _allowed(path, base):
    return DT_C if path.endswith("T_C") else BAND * abs(base)


def _band_text(path):
    return f"+/-{DT_C:g} °C" if path.endswith("T_C") else f"+/-{BAND:.0%}"


def attack_surface(spec):
    """Operating inputs the attacker may move, with their design values. Feed rates are excluded: throughput is `scale`."""
    out = {}
    for fid, f in (spec.get("feeds") or {}).items():
        for k in ("T_C", "P_bar"):
            if _numeric(f.get(k)):
                out[f"feeds.{fid}.{k}"] = f[k]
        for comp, x in (f.get("x") or {}).items():
            if _numeric(x) and x > 0:
                out[f"feeds.{fid}.x.{comp}"] = x
    for u in spec.get("units") or []:
        for k, v in u.items():
            if k not in _STRUCTURAL_UNIT_FIELDS and (k not in _REPLACEMENT_FIELDS or k in DEGRADES) and _numeric(v) and v != 0:
                out[f"units.{u['id']}.{k}"] = v
    return out


def validate(spec, raw):
    """Keep only bounded, well-formed scenarios; say why each other one was dropped."""
    surface, kept, dropped = attack_surface(spec), [], []
    for s in (raw or [])[:MAX_SCENARIOS]:
        name = str(s.get("name") or "").strip()[:80]
        try:
            rel = float(s.get("scale", 1.0))
        except (TypeError, ValueError):
            rel = float("nan")
        changes, why = [], []
        if not name or name in {k["name"] for k in kept}:
            why.append("missing or duplicate name")
        if not (math.isfinite(rel) and SCALE[0] <= rel <= SCALE[1]):
            why.append(f"scale {s.get('scale')} outside {SCALE[0]}-{SCALE[1]} of the target")
        for c in s.get("changes") or []:
            path, value = str(c.get("path") or ""), c.get("value")
            base = surface.get(path)
            if base is None:
                why.append(f"{path}: not an operating input of this design")
            elif not _numeric(value) or abs(value - base) > _allowed(path, base) + 1e-12:
                why.append(f"{path}: {value} is outside {_band_text(path)} of {base}")
            else:
                changes.append({"path": path, "value": value})
        if changes:
            why += change_errors(spec, changes, require_evidence=False)
        if why:
            dropped.append({"name": name or "?", "why": "; ".join(why)})
        else:
            kept.append({"name": name, "scale": rel, "changes": changes,
                         "basis": f"{s.get('guideword') or 'deviation'}: {str(s.get('basis') or '')[:300]}"})
    return kept, dropped


PROMPT = """You are the red-team engineer on a plant-change review. The design below was verified at the target throughput \
({target:.2f}x today). Find credible operating deviations under which it is most likely to break a limit: HAZOP guide \
words (more/less flow, temperature, pressure, composition other than), fouling or degraded efficiency between \
cleanings, seasonal utility temperatures, upstream feed swings. Each must be physically credible for this plant; say why.

Rules: at most {n} scenarios. "scale" is the throughput relative to the target ({lo}-{hi}). Change only paths from the \
attack surface below, each within +/-{band:.0%} of its design value (temperatures within +/-{dt:g} °C). Do not change limits, equipment or connections.

Design changes under attack: {changes}
Limits: {limits}
Attack surface (path: design value): {surface}

Think briefly, then reply with the JSON only: {{"scenarios": [{{"name": "...", "guideword": "...", "basis": "...", "scale": 1.0, \
"changes": [{{"path": "...", "value": 0.0}}]}}]}}"""


def _json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _raw_set(ident, label, design, raw, source, run_id=None, note=None, challenge=None):
    attacks = []
    for scenario in raw.get("scenarios") or []:
        attacks.append({"name": scenario.get("name") or "Unnamed attack",
                        "rationale": scenario.get("basis") or "Attacker rationale was not stored.",
                        "changed_inputs": scenario.get("changes") or [], "scale": scenario.get("scale"),
                        "pass": bool(scenario.get("pass")), "errors": scenario.get("errors") or [],
                        "worst": scenario.get("worst"), "source_url": source})
    known = [a for a in attacks if _numeric((a.get("worst") or {}).get("utilisation"))]
    worst = max(known, key=lambda a: a["worst"]["utilisation"]) if known else None
    held = sum(a["pass"] for a in attacks)
    return {"id": ident, "label": label, "design_label": design, "attacker_model": raw.get("model"),
            "cost_usd": raw.get("usd"), "seconds": raw.get("seconds"), "target": raw.get("target"),
            "run_id": run_id, "source_url": source, "note": note, "challenge": challenge, "attacks": attacks,
            "summary": {"total": len(attacks), "held": held, "broke": len(attacks) - held,
                        "worst_utilisation": (worst or {}).get("worst", {}).get("utilisation"),
                        "worst_check": (worst or {}).get("worst", {}).get("check")}}


def _redteam_step(log):
    return next((step for round_ in log.get("rounds") or [] for step in round_.get("steps") or []
                 if step.get("check") == "redteam"), None)


def _harsh_set(log, source):
    step = _redteam_step(log) or {}
    attacks = []
    pattern = r"'([^']+)' \(([\d.]+)x target; ([^)]+)\): (.*?)(?=; '[^']+' \(|$)"
    for name, scale, changed, result in re.findall(pattern, step.get("title") or ""):
        changes = []
        for item in changed.split(", "):
            path, value = item.rsplit("=", 1)
            try:
                value = float(value)
            except ValueError:
                pass
            changes.append({"path": path, "value": value})
        match = re.match(r"(.+?) (Fair flood fraction vs limit) ([\d.]+) %$", result)
        worst = ({"id": match.group(1), "check": match.group(2), "utilisation": float(match.group(3)) / 100}
                 if match else None)
        attacks.append({"name": name, "rationale": "Attacker rationale was not preserved in this worklog.",
                        "changed_inputs": changes, "scale": float(scale), "pass": False, "errors": [result],
                        "worst": worst, "source_url": source})
    total = int((step.get("numbers") or {}).get("attacks") or len(attacks))
    for n in range(len(attacks), total):
        attacks.append({"name": f"Attack {n + 1} — detail not stored",
                        "rationale": "The worklog preserved the aggregate result, not this attack's name or numbers.",
                        "changed_inputs": [], "scale": None, "pass": False, "errors": [], "worst": None,
                        "source_url": source})
    known = [a for a in attacks if a.get("worst")]
    worst = max(known, key=lambda a: a["worst"]["utilisation"]) if known else None
    numbers = step.get("numbers") or {}
    return {"id": "600-harsh", "label": "600 mm · 1.25× target", "design_label": "600 mm replacement shell",
            "attacker_model": "muse-spark-1.3", "cost_usd": numbers.get("usd"), "seconds": None,
            "target": 1.25, "run_id": log.get("id"), "source_url": source,
            "note": "Only three per-attack results were retained; the worklog records that all eight broke the design.",
            "challenge": None, "attacks": attacks,
            "summary": {"total": total, "held": 0, "broke": int(numbers.get("broke") or total),
                        "worst_utilisation": (worst or {}).get("worst", {}).get("utilisation"),
                        "worst_check": (worst or {}).get("worst", {}).get("check")}}


def source(w, ident):
    """The exact stored source behind one replay set; ids are allowlisted, never paths from the request."""
    base = w.model_file.parent
    paths = {"600-envelope": base / "redteam_600mm.json",
             "600-harsh": base / "work" / "20261102-194930" / "worklog.json",
             "700-robust": base / "redteam_700mm.json", "featured": base / "redteam.json"}
    return _json(paths[ident]) if ident in paths else None


def stored(w):
    """Normalized, replay-only red-team sets available for this case."""
    case, base = w.name, w.model_file.parent
    sets = []
    raw = _json(base / "redteam_600mm.json")
    if raw:
        src = f"/api/plant/{case}/redteam?source=600-envelope"
        sets.append(_raw_set("600-envelope", "600 mm · envelope band", "600 mm replacement shell", raw, src,
                             note="Attacks stay within the normal +10% envelope band."))
    log = _json(base / "work" / "20261102-194930" / "worklog.json")
    if log:
        sets.append(_harsh_set(log, f"/api/plant/{case}/work/{log['id']}"))
    raw = _json(base / "redteam_700mm.json")
    if raw:
        src = f"/api/plant/{case}/redteam?source=700-robust"
        challenge = {"scale": 1.25, "utilisation": .864,
                     "text": "A separate 1.25×-target worst-case DWSIM sizing check reached 86.4% of the flood limit.",
                     "source_url": f"/api/plant/{case}/work/20261102-194930"}
        sets.append(_raw_set("700-robust", "700 mm · robust design", "700 mm replacement shell", raw, src,
                             run_id="20261102-203128", challenge=challenge,
                             note="The stored eight-attack replay uses the bounded envelope; the sizing check is shown separately."))
    # Other cases may have the ordinary cache even when they do not have the three BASF demo sets.
    raw = _json(base / "redteam.json")
    if raw and not sets:
        src = f"/api/plant/{case}/redteam?source=featured"
        sets.append(_raw_set("featured", "Featured design · envelope band", "Featured verified design", raw, src))
    return {"case": case, "sets": sets}


def run_featured(w):
    """Run the fixed Spark 1.3 attacker against the featured verified design (the simulator remains the judge)."""
    from .revb import design_answer
    answer = design_answer(w.answers)
    if answer is None:
        raise ValueError("no verified featured design to attack")
    idx = next(i for i, item in enumerate(w.answers) if item is answer)
    raw = attack(w, idx, "muse-spark-1.3")
    return _raw_set("live", "Live attack", "Featured verified design", raw,
                    f"/api/plant/{w.name}/redteam?source=featured")


def _parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return (json.loads(m.group(0)) if m else {}).get("scenarios") or []
    except json.JSONDecodeError:
        return []


def attack(w, idx, model):
    """Ask the attacker, re-solve every kept scenario. Cached per design, model and attack rules."""
    from .prefeed import gates_key, run_envelope
    ans = w.answers[idx]
    changes = [c for p in ans.get("proposals") or [] if p.get("verified") for c in p.get("changes") or []]
    design = patch(copy.deepcopy(w.spec), changes)
    target = float(w.cfg.get("target_scale") or 1.0)
    key = hashlib.sha1(json.dumps([gates_key(w, ans)["content"], model, MAX_SCENARIOS, BAND, DT_C, SCALE]).encode()).hexdigest()
    cache = w.model_file.with_name("redteam.json")
    if cache.exists() and json.loads(cache.read_text()).get("key") == key:
        return json.loads(cache.read_text())
    surface = attack_surface(design)
    prompt = PROMPT.format(target=target, n=MAX_SCENARIOS, lo=SCALE[0], hi=SCALE[1], band=BAND, dt=DT_C,
                           changes=json.dumps(changes)[:4000], limits=json.dumps(design.get("limits") or {})[:3000],
                           surface=json.dumps(surface)[:6000])
    t0, u0 = time.time(), llm.spent()
    msg = llm.complete(model, [{"role": "user", "content": prompt}], max_tokens=20000)
    kept, dropped = validate(design, _parse(msg.get("content")))
    out = {"key": key, "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "model": model, "target": target,
           "usd": round(llm.spent() - u0, 4), "seconds": round(time.time() - t0), "dropped": dropped, "scenarios": []}
    if kept:
        env = run_envelope(design, [{**s, "scale": s["scale"] * target} for s in kept], w._solve, patch)
        out["scenarios"] = [{"name": r["name"], "basis": r["basis"], "scale": r["scale"] / target, "pass": r["pass"],
                             "errors": r["errors"][:2], "worst": r["worst"],
                             "changes": next(s["changes"] for s in kept if s["name"] == r["name"])} for r in env["scenarios"]]
    cache.write_text(json.dumps(out, indent=1))
    return out


def check_rows(w, idx, model):
    """One loop check row: fail names the attacks that broke the design, with their numbers."""
    try:
        r = attack(w, idx, model)
    except llm.BudgetExceeded:
        raise
    except Exception as ex:  # noqa: BLE001 - an attack that cannot run is open, never a pass
        return [{"check": "redteam", "engine": "red team", "status": "open",
                 "title": f"red team could not run: {type(ex).__name__}: {ex}"[:200]}]
    sc = r["scenarios"]
    if not sc:
        return [{"check": "redteam", "engine": "red team", "status": "open",
                 "title": f"red team proposed no valid scenario ({len(r['dropped'])} dropped)"}]
    broke = [s for s in sc if not s["pass"]]
    def said(s):
        wst = s.get("worst") or {}
        how = s["errors"][0] if s["errors"] else f"{wst.get('id')} {wst.get('check')} {round((wst.get('utilisation') or 0) * 100)} %"
        return f"'{s['name']}' ({s['scale']:.2f}x target; {', '.join(f'{c['path']}={c['value']}' for c in s['changes'])}): {how}"
    return [{"check": "redteam", "engine": f"red team ({r['model']}) + DWSIM", "status": "fail" if broke else "pass",
             "title": (f"{len(broke)}/{len(sc)} red-team attacks break the design: " + "; ".join(map(said, broke[:3])))
             if broke else f"design holds all {len(sc)} red-team attacks",
             "numbers": {"attacks": len(sc), "broke": len(broke), "dropped": len(r["dropped"]), "usd": r["usd"]},
             "source": "attacker proposes bounded operating deviations; each re-solved with the envelope limit checks"}]
