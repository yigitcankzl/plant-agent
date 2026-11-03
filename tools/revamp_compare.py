"""Score a blind revamp worklog/session against its withheld published outcome. No LLM.

Usage:
  PYTHONPATH=. .venv/bin/python tools/revamp_compare.py CASE WORKLOG_OR_SESSION [--output FILE]
"""
import argparse
import json
import math
import re
from pathlib import Path

from plantagent.docs import redact

ROOT = Path(__file__).resolve().parents[1]


def _load_submission(path):
    path = Path(path)
    if path.is_dir():
        path = path / ("worklog.json" if (path / "worklog.json").exists() else "answers.json")
    data = json.loads(path.read_text())
    return ("session", data) if isinstance(data, list) else ("worklog", data)


def _worklog(data):
    rounds = data.get("rounds") or []
    steps = [s for r in rounds for s in r.get("steps") or []]
    muse = [s for s in steps if str(s.get("actor", "")).lower() == "muse"]
    changes = next((s.get("changes") or [] for s in reversed(muse) if s.get("changes")), [])
    rows = [s for s in steps if s.get("numbers")]
    return {
        "loop_status": "done" if data.get("status") == "done" else "not",
        "status_detail": data.get("status") or "missing",
        "changes": changes,
        "rows": rows,
        "text": steps,
    }


def _session(answers):
    answer = answers[-1] if answers else {}
    proposals = answer.get("proposals") or []
    verified = [p for p in proposals if p.get("verified")]
    chosen = verified or proposals
    changes = [c for p in chosen for c in p.get("changes") or []]
    rows = []
    for proposal in chosen:
        calculation = proposal.get("calculation") or {}
        rows.extend(calculation.get("checks") or [])
        rows.extend(proposal.get("open_checks") or calculation.get("open_checks") or [])
    explicit = answer.get("status") or (answer.get("result") or {}).get("status")
    return {
        "loop_status": "done" if explicit == "done" else "not",
        "status_detail": explicit or "session has no loop completion marker",
        "changes": changes,
        "rows": rows,
        "text": [answer],
    }


def _text(value):
    return re.sub(r"\s+", " ", json.dumps(value, sort_keys=True, default=str).lower())


def _change_score(categories, submission):
    blob = _text([submission["changes"], submission["text"]])
    rows = []
    for category in categories:
        hits = [word for word in category.get("keywords") or [] if word.lower() in blob]
        rows.append({
            "id": category["id"], "label": category["label"],
            "required": bool(category.get("required")), "matched": bool(hits), "matched_keywords": hits,
        })
    required = [r for r in rows if r["required"]]
    matched = sum(r["matched"] for r in required)
    verdict = "match" if required and matched == len(required) else "partial" if matched else "miss"
    return verdict, rows


def _numbers(row):
    values = row.get("numbers") if isinstance(row, dict) else None
    values = values if isinstance(values, dict) else row if isinstance(row, dict) else {}
    skip = {"seconds", "cost", "cost_usd", "round", "step"}
    return [(k, float(v)) for k, v in values.items()
            if k not in skip and isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)]


def _reported_value(item, submission):
    aliases = [x.lower() for x in item.get("reported_by") or []]
    for row in reversed(submission["rows"]):
        label = _text({k: row.get(k) for k in ("id", "check", "title", "detail", "name")})
        if aliases and not any(alias in label for alias in aliases):
            continue
        values = _numbers(row)
        if values:
            preferred = next((v for k, v in values if k in ("value", "after", "actual", "predicted")), values[0][1])
            return preferred * float(item.get("agent_scale", 1)), f"reported row: {label[:120]}"
    field = item.get("rating_field")
    path = item.get("agent_path")
    for change in reversed(submission["changes"]):
        if path and change.get("path") == path and isinstance(change.get("value"), (int, float)):
            return float(change["value"]) * float(item.get("agent_scale", 1)), f"change {path}"
        if field and isinstance((change.get("new_rating") or {}).get(field), (int, float)):
            return float(change["new_rating"][field]) * float(item.get("agent_scale", 1)), f"new rating {field}"
        if field and isinstance((change.get("add_unit") or {}).get(field), (int, float)):
            return float(change["add_unit"][field]) * float(item.get("agent_scale", 1)), f"new unit {field}"
    return None, None


def _error(item, actual):
    if actual is None:
        return None
    if "expected_range" in item:
        low, high = map(float, item["expected_range"])
        if low <= actual <= high:
            return 0.0
        edge = low if actual < low else high
        return abs(actual - edge) / max(abs(edge), 1e-12) * 100
    expected = float(item["expected"])
    return abs(actual - expected) / max(abs(expected), 1e-12) * 100


def score(case, submission_path):
    outcome = json.loads((ROOT / "cases" / case / "outcome.json").read_text())
    kind, raw = _load_submission(submission_path)
    submission = _session(raw) if kind == "session" else _worklog(raw)
    verdict, categories = _change_score(outcome.get("change_categories") or [], submission)
    after = []
    for item in outcome.get("after_data") or []:
        actual, source = _reported_value(item, submission)
        after.append({
            "id": item["id"], "label": item["label"], "expected": item.get("expected", item.get("expected_range")),
            "unit": item["unit"], "actual": actual, "error_pct": _error(item, actual),
            "actual_source": source, "published_source": item["source"],
        })
    return {
        "case": case, "submission": str(Path(submission_path)), "submission_kind": kind,
        "loop_status": submission["loop_status"], "loop_status_detail": submission["status_detail"],
        "change_type": verdict, "change_categories": categories, "after_data": after,
        "summary": {"reported_after_items": sum(x["actual"] is not None for x in after), "after_items": len(after)},
        "source": outcome["source"],
    }


def markdown(result):
    lines = [
        f"# Revamp comparison: {result['case']}", "",
        f"- Loop status: **{result['loop_status']}** ({result['loop_status_detail']})",
        f"- Published change type: **{result['change_type']}**", "",
        "## Change categories", "", "| Published category | Required | Agent match |", "|---|---:|---:|",
    ]
    lines += [f"| {r['label']} | {'yes' if r['required'] else 'no'} | {'yes' if r['matched'] else 'no'} |"
              for r in result["change_categories"]]
    lines += ["", "## Published after data", "",
              "Numbers are taken by keyword from the agent's check rows, without unit conversion. "
              "A large error here is often a wrong pick by this script, not an engineering error; "
              "the score uses only the change categories above.", "",
              "| Item | Published | Agent verified design | Error |", "|---|---:|---:|---:|"]
    for row in result["after_data"]:
        expected = row["expected"]
        expected = "–".join(map(str, expected)) if isinstance(expected, list) else str(expected)
        actual = "not reported" if row["actual"] is None else f"{row['actual']:.6g}"
        error = "—" if row["error_pct"] is None else f"{row['error_pct']:.1f}%"
        lines.append(f"| {row['label']} | {expected} {row['unit']} | {actual} {row['unit']} | {error} |")
    lines += ["", f"Source: {result['source']}", ""]
    return "\n".join(lines)


def contamination(case):
    folder = ROOT / "cases" / case
    basis = (folder / "basis.md").read_text()
    outcome = json.loads((folder / "outcome.json").read_text())
    _, hidden = redact(basis)
    low = re.sub(r"\s+", " ", basis.lower())
    phrase_hits = [p for p in outcome.get("leak_phrases") or [] if re.sub(r"\s+", " ", p.lower()) in low]
    value_hits = []
    for item in outcome.get("after_data") or []:
        if not item.get("withheld"):
            continue
        values = item.get("expected_range") or [item.get("expected")]
        for value in values:
            token = f"{float(value):g}"
            if re.search(rf"(?<![\d.,]){re.escape(token)}(?![\d.,])", basis):
                value_hits.append({"item": item["id"], "value": token})
    return {"redacted_clauses": hidden, "phrase_hits": phrase_hits, "value_hits": value_hits}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("submission")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = score(args.case, args.submission)
    output = args.output or ROOT / "runs" / "ws" / args.case / "revamp-comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    output.with_suffix(".md").write_text(markdown(result))
    print(markdown(result))


if __name__ == "__main__":
    main()
