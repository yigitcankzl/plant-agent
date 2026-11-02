"""Red team: a second Muse attacks a verified design with credible operating deviations; the simulator decides.

The attacker only proposes scenarios (HAZOP-style deviations of operating inputs, bounded to +/-30 % of the design
value and 0.8-1.25x the target throughput). Every scenario is re-solved with the same limit checks as the envelope
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
SCALE = (0.80, 1.10)   # throughput of an attack, relative to the target: the envelope band, not a capacity search


def _numeric(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


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
            elif not _numeric(value) or abs(value - base) > BAND * abs(base) + 1e-12:
                why.append(f"{path}: {value} is outside +/-{BAND:.0%} of {base}")
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
attack surface below, each within +/-{band:.0%} of its design value. Do not change limits, equipment or connections.

Design changes under attack: {changes}
Limits: {limits}
Attack surface (path: design value): {surface}

Think briefly, then reply with the JSON only: {{"scenarios": [{{"name": "...", "guideword": "...", "basis": "...", "scale": 1.0, \
"changes": [{{"path": "...", "value": 0.0}}]}}]}}"""


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
    key = hashlib.sha1(json.dumps([gates_key(w, ans)["content"], model, MAX_SCENARIOS, BAND, SCALE]).encode()).hexdigest()
    cache = w.model_file.with_name("redteam.json")
    if cache.exists() and json.loads(cache.read_text()).get("key") == key:
        return json.loads(cache.read_text())
    surface = attack_surface(design)
    prompt = PROMPT.format(target=target, n=MAX_SCENARIOS, lo=SCALE[0], hi=SCALE[1], band=BAND,
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
