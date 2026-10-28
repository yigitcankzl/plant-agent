"""Hash-chained audit trail per project for accidental-edit detection, not tamper-proof evidence.

The whole file can be rewritten or truncated and rehashed by anyone who can write it; there is no external trust anchor.
User identity is only a claim from the unauthenticated X-User header.
"""
import hashlib
import json
import re
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_LOCK = threading.RLock()


def _file(case):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", case):
        raise ValueError("invalid audit case")
    f = ROOT / "runs" / "audit" / f"{case}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    return f


def _hash(entry):
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def entries(case):
    with _LOCK:
        f = _file(case)
        return [json.loads(line) for line in f.read_text().splitlines() if line.strip()] if f.exists() else []


def append(case, action, user=None, reason=None, details=None):
    with _LOCK:
        prev = entries(case)
        e = {"seq": len(prev) + 1, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "case": case, "action": action,
             "user": f"claimed: {user}" if user else "engineer (unauthenticated)", "reason": reason or "", "details": details or {},
             "prev": prev[-1]["hash"] if prev else "0" * 64}
        e["hash"] = _hash(e)
        with _file(case).open("a") as f:
            f.write(json.dumps(e) + "\n")
        return e


def verify(case):
    """Check internal consistency only; a valid chain does not prove the file was not rewritten."""
    with _LOCK:
        f = _file(case)
        lines = f.read_text().splitlines() if f.exists() else []
        prev = "0" * 64
        for i, line in enumerate(lines):
            try:
                e = json.loads(line)
                if e.get("prev") != prev or _hash(e) != e.get("hash") or e.get("seq") != i + 1:
                    return {"ok": False, "broken_at": i + 1, "entries": i}
                prev = e["hash"]
            except (ValueError, TypeError, AttributeError):
                return {"ok": False, "broken_at": i + 1, "entries": i}
        return {"ok": True, "entries": len(lines)}


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
