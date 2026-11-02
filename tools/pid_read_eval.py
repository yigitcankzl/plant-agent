"""Score a schematic read against an engineer-confirmed read, without a model call."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re


def _normal(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def score(read, confirmed):
    read, confirmed = read.get("raw", read), confirmed.get("raw", confirmed)
    truth = confirmed["equipment"]
    by_label = {}
    for e in truth:
        key = (_normal(e.get("label_text") or e["tag"]), e.get("occurrence", 1))
        if key in by_label:
            raise ValueError("confirmed equipment labels need unique occurrence numbers")
        by_label[key] = e
    mapping, found, wrong_types, extras = {}, set(), [], []
    for e in read["equipment"]:
        match = by_label.get((_normal(e.get("label_text") or e["tag"]), e.get("occurrence", 1)))
        if not match or match["tag"] in found:
            extras.append(e["tag"])
            continue
        mapping[e["tag"]] = match["tag"]
        found.add(match["tag"])
        if _normal(e["class"]) != _normal(match["class"]):
            wrong_types.append({"tag": match["tag"], "read": e["class"], "confirmed": match["class"]})

    def links(data, tags):
        return Counter((tags.get(c["from"], "unmatched:" + c["from"]),
                        tags.get(c["to"], "unmatched:" + c["to"]), _normal(c.get("loop", "")))
                       for c in data["connections"])

    predicted = links(read, mapping)
    expected = links(confirmed, {e["tag"]: e["tag"] for e in truth})
    predicted_paths, expected_paths = Counter(), Counter()
    for (a, b, _), n in predicted.items():
        predicted_paths[(a, b)] += n
    for (a, b, _), n in expected.items():
        expected_paths[(a, b)] += n
    details = lambda counts: [{"from": a, "to": b, "line": line, "count": n} for (a, b, line), n in sorted(counts.items())]
    return {"equipment": {"found": len(found), "total": len(truth), "type_correct": len(found) - len(wrong_types),
                          "missing": sorted({e["tag"] for e in truth} - found), "extra": extras, "wrong_types": wrong_types},
            "connections": {"correct": sum((predicted & expected).values()), "total": sum(expected.values()),
                            "missing": sum((expected - predicted).values()), "extra": sum((predicted - expected).values()),
                            "directed_topology_correct_ignoring_line_ids": sum((predicted_paths & expected_paths).values()),
                            "missing_links": details(expected - predicted), "extra_links": details(predicted - expected)},
            "rules": "Equipment: printed label + occurrence, unique one-to-one match; type: exact case/punctuation-normalised class. "
                     "Connections: directed from/to plus printed line identifier; duplicates count as extra. No semantic LLM grading."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("read", type=Path)
    parser.add_argument("--confirmed", type=Path, default=Path(__file__).resolve().parents[1] / "runs/ws/salt_mvr_vision/pid_confirmed.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = score(json.loads(args.read.read_text()), json.loads(args.confirmed.read_text()))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
