"""Append-only, hash-chained audit trail per project (who did what, when, why), for change control and data integrity.

Every entry carries the previous entry's hash, so any edit or deletion breaks the chain and verify() reports where.
ponytail: user identity comes from the X-User header (no login yet); an identity provider and e-signatures plug in here.
"""
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _file(case):
    f = ROOT / "runs" / "audit" / f"{case}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    return f


def _hash(entry):
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def entries(case):
    f = _file(case)
    return [json.loads(line) for line in f.read_text().splitlines() if line.strip()] if f.exists() else []


def append(case, action, user=None, reason=None, details=None):
    prev = entries(case)
    e = {"seq": len(prev) + 1, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "case": case, "action": action,
         "user": user or "engineer (unauthenticated)", "reason": reason or "", "details": details or {},
         "prev": prev[-1]["hash"] if prev else "0" * 64}
    e["hash"] = _hash(e)
    with _file(case).open("a") as f:  # append only
        f.write(json.dumps(e) + "\n")
    return e


def verify(case):
    """The chain is intact when every entry hashes to its stored hash and points at the one before it."""
    prev = "0" * 64
    for i, e in enumerate(entries(case)):
        if e.get("prev") != prev or _hash(e) != e.get("hash") or e.get("seq") != i + 1:
            return {"ok": False, "broken_at": i + 1, "entries": i}
        prev = e["hash"]
    return {"ok": True, "entries": len(entries(case))}


if __name__ == "__main__":
    case = "_selftest"
    _file(case).unlink(missing_ok=True)
    append(case, "accept", "a.engineer", "raise CW for +20 %", {"rev": 1})
    append(case, "revert", "a.engineer", "trial over", {"to_rev": 0})
    assert verify(case)["ok"]
    lines = _file(case).read_text().splitlines()
    tampered = json.loads(lines[0]); tampered["reason"] = "edited later"
    _file(case).write_text(json.dumps(tampered) + "\n" + lines[1] + "\n")
    assert verify(case) == {"ok": False, "broken_at": 1, "entries": 0}
    _file(case).unlink()
    print("ok")
