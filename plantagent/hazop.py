"""Draft HAZOP worksheet for a proposed design change.

Muse supplies engineering judgement; every generic deviation the simulator can
represent is independently re-solved and clearly separated from that judgement.
"""
import hashlib
import json
import re
from pathlib import Path

from . import llm, pid
from .docs import DATA
from .plant import display_names, patch
from .revb import design_answer

ROOT = Path(__file__).resolve().parent.parent
LABEL = "DRAFT — not a substitute for a facilitated HAZOP team session"
TASK_BUDGET_USD = 3.0
GUIDEWORDS = (
    ("flow", "no"), ("flow", "more"), ("flow", "less"), ("flow", "reverse"),
    ("pressure", "more"), ("pressure", "less"),
    ("temperature", "more"), ("temperature", "less"),
    ("level", "more"), ("level", "less"), ("composition", "other than"),
)
VERSION = 1


def _answer(w, answer=None):
    if isinstance(answer, int) and 0 <= answer < len(w.answers):
        return w.answers[answer]
    return design_answer(w.answers)


def _proposal(w, answer=None):
    ans = _answer(w, answer)
    proposals = [p for p in (ans or {}).get("proposals") or [] if p.get("verified")]
    changes = [c for p in proposals for c in p.get("changes") or []]
    return ans, proposals, changes


def _stream_values(value):
    return [value] if isinstance(value, str) else [x for x in value or [] if isinstance(x, str)]


def nodes(w, answer=None):
    """Changed model units and their immediate process neighbours."""
    _ans, proposals, changes = _proposal(w, answer)
    spec = patch(w.spec, changes) if changes else w.spec
    units = {u["id"]: u for u in (spec or {}).get("units") or []}
    changed = set()
    for p in proposals:
        changed.update(x for x in (p.get("tag"), p.get("fixes")) if x)
    for c in changes:
        if c.get("path") and c["path"].startswith("units."):
            changed.add(c["path"].split(".", 2)[1])
        if c.get("add_unit"):
            if c["add_unit"].get("id"):
                changed.add(c["add_unit"]["id"])
        if c.get("reroute"):
            if c["reroute"].get("unit"):
                changed.add(c["reroute"]["unit"])
    aliases = w.cfg.get("model_aliases") or {}
    changed |= {aliases[t] for t in list(changed) if t in aliases}
    changed |= {tag for tag, uid in aliases.items() if uid in changed}
    model_changed = {x for x in changed if x in units}
    touched_streams = {s for uid in model_changed for k in ("in", "out", "vapor", "liquid", "heating", "cold", "hot")
                       for s in _stream_values(units[uid].get(k))}
    nearby = {uid for uid, u in units.items() if any(s in touched_streams for k in ("in", "out", "vapor", "liquid", "heating", "cold", "hot")
                                                  for s in _stream_values(u.get(k)))}
    ids = model_changed | nearby
    names = display_names(spec or {})
    out = [{"id": uid, "name": names.get(uid, uid), "type": units[uid].get("type", "unit"), "source": "model",
            "changed": uid in model_changed} for uid in sorted(ids)]
    out = [n for n in out if n["type"] not in {"splitter", "mixer"}]  # routing helpers are not HAZOP process nodes
    pid_tags = set()
    pid_classes = {}
    if w.cfg.get("pid"):
        drawing = pid.overview(DATA / w.cfg["pid"])
        pid_classes = {e["tag"]: e.get("class") or "P&ID equipment" for e in drawing.get("equipment") or []}
        changed_tags = {tag for tag in changed if tag in pid_classes} | {tag for tag, uid in aliases.items() if uid in model_changed}
        for connection in drawing.get("connections") or []:
            ends = {str(connection.get(k) or "").split("(", 1)[0] for k in ("from", "to")} & set(pid_classes)
            if ends & changed_tags:
                pid_tags |= ends
        pid_tags |= changed_tags
    # A changed P&ID tag with no model object is still a valid HAZOP node.
    out += [{"id": tag, "name": tag, "type": pid_classes.get(tag, "P&ID equipment"), "source": "P&ID",
             "changed": tag in changed}
            for tag in sorted((changed | pid_tags) - set(units)) if tag not in aliases]
    return out


def deviations(node_rows):
    return [{"key": f"{n['id']}|{g} {p}", "node_id": n["id"], "parameter": p, "guideword": g,
             "deviation": f"{g} {p}"} for n in node_rows for p, g in GUIDEWORDS]


def _upstream_feeds(spec, node_id):
    units = {u["id"]: u for u in spec.get("units") or []}
    producers = {}
    for uid, u in units.items():
        for k in ("out", "vapor", "liquid"):
            for stream in _stream_values(u.get(k)):
                producers[stream] = uid
    todo = [node_id]
    seen, feeds = set(), []
    while todo:
        uid = todo.pop()
        if uid in seen or uid not in units:
            continue
        seen.add(uid)
        for k in ("in", "heating", "cold", "hot"):
            for stream in _stream_values(units[uid].get(k)):
                if stream in (spec.get("feeds") or {}):
                    feeds.append(stream)
                elif stream in producers:
                    todo.append(producers[stream])
    return list(dict.fromkeys(feeds))


def _changed_spec(spec, node_id, parameter, guideword, target):
    if parameter == "flow" and guideword in ("no", "more", "less"):
        return spec, target * {"no": 0.0, "more": 1.1, "less": 0.9}[guideword], "throughput scale"
    if parameter not in ("pressure", "temperature"):
        return None
    field = "P_bar" if parameter == "pressure" else "T_C"
    feed = next((f for f in _upstream_feeds(spec, node_id) if field in spec["feeds"][f]), None)
    if not feed:
        return None
    old = float(spec["feeds"][feed][field])
    value = old * (1.1 if guideword == "more" else 0.9) if field == "P_bar" else old + (10 if guideword == "more" else -10)
    return patch(spec, [{"path": f"feeds.{feed}.{field}", "value": value}]), target, f"{feed}.{field} {old:g} → {value:g}"


def _metric(result, node_id):
    unit = (result.get("units") or {}).get(node_id) or {}
    pressure = next((unit[k] for k in ("P_out_bar", "P_bar", "pressure_bar") if isinstance(unit.get(k), (int, float))), None)
    temperature = next((unit[k] for k in ("T_out_C", "T_C", "temperature_C") if isinstance(unit.get(k), (int, float))), None)
    checks = [c for c in result.get("checks") or [] if isinstance(c.get("utilisation"), (int, float))]
    local = [c for c in checks if c.get("id") == node_id]
    worst = max(local or checks, key=lambda c: c["utilisation"], default=None)
    values = {"pressure_bar": pressure, "temperature_C": temperature,
              "max_utilisation": worst.get("utilisation") if worst else None,
              "limiting_item": f"{worst.get('id')} — {worst.get('check')}" if worst else None}
    return {k: v for k, v in values.items() if v is not None}


def _calculations(w, spec, node_rows, target):
    solved, cache = {}, {}
    for d in deviations(node_rows):
        change = _changed_spec(spec, d["node_id"], d["parameter"], d["guideword"], target)
        if not change:
            continue
        changed, scale, basis = change
        key = hashlib.sha256(json.dumps([changed, scale], sort_keys=True).encode()).hexdigest()
        if key not in cache:
            cache[key] = w._solve(changed, scale)
        result = cache[key]
        if result.get("errors"):
            continue
        values = _metric(result, d["node_id"])
        if values:
            solved[d["key"]] = {"basis": basis, "scale": round(scale, 4), "result": values}
    return solved


def _relief(w, node_rows):
    rows = pid.relief_scan(DATA / w.cfg["pid"]) if w.cfg.get("pid") else []
    aliases = w.cfg.get("model_aliases") or {}
    out = {}
    for node in node_rows:
        tags = {node["id"]} | {tag for tag, uid in aliases.items() if uid == node["id"]}
        out[node["id"]] = [r for r in rows if r.get("tag") in tags]
    return out


def content(w, answer=None):
    ans, proposals, changes = _proposal(w, answer)
    node_rows = nodes(w, answer)
    spec = patch(w.spec, changes) if changes else w.spec
    return {"version": VERSION, "case": w.name, "answer": (ans or {}).get("headline"), "proposals": proposals,
            "spec": spec, "target_scale": float(w.cfg.get("target_scale", 1.0)), "nodes": node_rows,
            "deviations": deviations(node_rows), "relief": _relief(w, node_rows)}


def content_hash(w, answer=None):
    return hashlib.sha256(json.dumps(content(w, answer), sort_keys=True, default=str).encode()).hexdigest()


def _parse_json(text):
    text = str(text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    value = json.loads(text)
    if not isinstance(value, list):
        raise ValueError("HAZOP response must be a JSON array")
    return value


def _main_checkout():
    dotgit = ROOT / ".git"
    if dotgit.is_file():
        gitdir = Path(dotgit.read_text().split(":", 1)[1].strip())
        return gitdir.parents[2] if gitdir.parent.name == "worktrees" else ROOT
    return ROOT


def spend_status():
    main = _main_checkout()
    ledgers = [main / "runs/usage.jsonl", *sorted((main / ".claude/worktrees").glob("*/runs/usage.jsonl"))]
    total = task = 0.0
    for ledger in dict.fromkeys(ledgers):
        if not ledger.exists():
            continue
        for line in ledger.read_text().splitlines():
            try:
                row = json.loads(line)
                usd = float(row.get("usd") or 0)
                total += usd
                if str(row.get("tag") or "").startswith("hazop:"):
                    task += usd
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
    cap = llm.BUDGET_USD
    env = main / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "MUSE_BUDGET_USD":
                cap = float(value.strip().strip("'\""))
                break
    return {"total_usd": total, "task_usd": task, "overall_cap_usd": cap, "task_cap_usd": TASK_BUDGET_USD}


def _muse(payload, model):
    prompt = {
        "role": "user",
        "content": "Prepare concise HAZOP judgement for every supplied row. Return only a JSON array with exactly these keys: "
                   "key, cause, consequence, safeguards (array of strings). Do not invent calculations or relief coverage; those are "
                   "handled deterministically. One object per row, no omissions.\n" + json.dumps({
                       "plant": payload["case"], "nodes": payload["nodes"], "rows": payload["deviations"],
                       "relief_scan": payload["relief"]}, default=str)
    }
    messages = [{"role": "system", "content": "You are an experienced process-safety HAZOP scribe."}, prompt]
    params = {"temperature": 0, "max_tokens": 6000}
    key = hashlib.sha256(json.dumps([model, messages, params], sort_keys=True).encode()).hexdigest()
    if not (llm.CACHE / f"{key}.json").exists():
        spend = spend_status()
        reserve = llm._reserve(model, messages, params)
        if spend["total_usd"] + reserve > spend["overall_cap_usd"]:
            raise RuntimeError(f"aggregate Muse budget already reached (${spend['total_usd']:.2f} of ${spend['overall_cap_usd']:.2f}); no call made")
        if spend["task_usd"] + reserve > TASK_BUDGET_USD:
            raise RuntimeError(f"HAZOP task budget would exceed ${TASK_BUDGET_USD:.2f}; no call made")
    old_tag = llm.current_tag()
    llm.set_tag("hazop:" + payload["case"])
    try:
        message = llm.complete(model, messages, **params)
    finally:
        llm.set_tag(old_tag)
    return _parse_json(message.get("content"))


def markdown(study):
    lines = [f"# HAZOP — {study['case']}", "", f"**{study['label']}**", "",
             "| Node | Deviation | Cause | Consequence | Safeguards | Basis |", "|---|---|---|---|---|---|"]
    for r in study["rows"]:
        calc = r.get("calculation") or {}
        consequence = r["consequence"]
        if calc:
            consequence += "; re-solve: " + ", ".join(f"{k}={v}" for k, v in calc["result"].items())
        lines.append(f"| {r['node_id']} | {r['deviation']} | {r['cause']} | {consequence} | "
                     f"{'; '.join(r['safeguards']) or 'none stated'} | {r['basis']} |")
    return "\n".join(lines) + "\n"


def generate(w, answer=None, model=None, proposer=None):
    payload = content(w, answer)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    cache = ROOT / "runs" / "cache" / "hazop" / f"{digest}.json"
    latest = w.model_file.with_name("hazop.json")
    if cache.exists():
        result = json.loads(cache.read_text())
        latest.write_text(json.dumps(result, indent=1))
        return result
    judgements = (proposer or (lambda p: _muse(p, model or w.model)))(payload)
    by_key = {r.get("key"): r for r in judgements if isinstance(r, dict)}
    missing = [d["key"] for d in payload["deviations"] if d["key"] not in by_key]
    if missing:
        raise ValueError("Muse omitted HAZOP rows: " + ", ".join(missing[:5]))
    calculations = _calculations(w, payload["spec"], payload["nodes"], payload["target_scale"])
    rows = []
    for d in payload["deviations"]:
        judgement = by_key[d["key"]]
        calc = calculations.get(d["key"])
        rows.append({**d, "cause": str(judgement.get("cause") or "").strip(),
                     "consequence": str(judgement.get("consequence") or "").strip(),
                     "safeguards": [str(x) for x in judgement.get("safeguards") or []],
                     "basis": "computed" if calc else "judgement (LLM)", **({"calculation": calc} if calc else {}),
                     "relief": payload["relief"].get(d["node_id"]) or []})
    result = {"version": VERSION, "case": w.name, "content_hash": digest, "label": LABEL, "model": model or w.model,
              "nodes": payload["nodes"], "rows": rows,
              "summary": {"rows": len(rows), "computed": sum(r["basis"] == "computed" for r in rows),
                          "judgement": sum(r["basis"] == "judgement (LLM)" for r in rows)}}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, indent=1))
    latest.write_text(json.dumps(result, indent=1))
    latest.with_suffix(".md").write_text(markdown(result))
    from . import audit
    audit.append(w.name, "hazop_draft", None, LABEL,
                 {"content_hash": digest, "rows": result["summary"]["rows"], "computed": result["summary"]["computed"],
                  "judgement": result["summary"]["judgement"], "model": result["model"]})
    return result


def load(w, answer=None):
    path = w.model_file.with_name("hazop.json")
    if not path.exists():
        return None
    value = json.loads(path.read_text())
    return value if value.get("content_hash") == content_hash(w, answer) else None


if __name__ == "__main__":
    import sys
    from .plant import PlantWorkspace
    workspace = PlantWorkspace(sys.argv[1])
    print(json.dumps(generate(workspace), indent=1))
