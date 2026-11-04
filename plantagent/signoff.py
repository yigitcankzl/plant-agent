"""MOC sign-off for a decision pack: draft -> reviewed -> approved (or rejected), with the package frozen at approval.

- Roles: preparer (the agent), reviewer, approver. Names are typed by the people signing (the X-User header is only a claim).
- Every failed check needs a written disposition (accepted risk with a reason, or must fix) before review or approval;
  open items are listed in the record. A pack with a "must fix" can be rejected, not approved.
- The approver cannot be the reviewer.
- At approval the package files (MOC pack, Rev B, check rows, assumptions log) are hashed into a manifest appended to the
  audit chain. A later change to any of them drops the state back to draft and says which file changed.
No model call anywhere in this module.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path

from . import audit

ROOT = Path(__file__).resolve().parent.parent
STATES = ("draft", "reviewed", "approved", "rejected")
KINDS = {"accepted_risk": "Accepted risk", "must_fix": "Must fix before approval"}
PREPARER = "PlantAgent (Muse proposes, the engines check)"
SKIP = {"decision.zip", "approval.json"}  # the zip repeats the files; approval.json is written by issuing


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _ws(case):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", case or ""):
        raise ValueError("invalid case")
    return ROOT / "runs" / "ws" / case


def _file(case):
    return _ws(case) / "signoff.json"


def _write(case, state):
    p = _file(case)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, indent=1))
    os.replace(tmp, p)


def packs(case):
    """Decision pack folders of the case, oldest first (decision.make writes them next to model.json)."""
    return sorted(p.name for p in _ws(case).glob("decision-*") if p.is_dir() and (p / "decision.json").is_file())


def package_files(case, pack):
    """The files frozen at approval: the pack folder, the check rows behind it and the assumptions log."""
    ws = _ws(case)
    out = [ws / pack / f.name for f in sorted((ws / pack).iterdir()) if f.is_file() and f.name not in SKIP]
    out += [ws / n for n in ("gates.json", "assumptions_log.jsonl") if (ws / n).is_file()]
    return out


def manifest(case, pack):
    ws = _ws(case)
    files = {str(f.relative_to(ws)): hashlib.sha256(f.read_bytes()).hexdigest() for f in package_files(case, pack)}
    return {"files": files, "hash": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def checks(case):
    """Failed and open discipline checks of the design (gates.json), each with the id a disposition is written against."""
    g = _ws(case) / "gates.json"
    rows = json.loads(g.read_text()).get("disciplines", []) if g.is_file() else []
    out = {"fail": [], "open": []}
    for d in rows:
        st = str(d.get("status", "")).lower()
        if st in out:
            out[st].append({"id": d.get("id"), "summary": str(d.get("summary") or "")[:400], "source": d.get("source")})
    return out


def _fresh(case, pack):
    return {"version": 1, "case": case, "pack": pack, "state": "draft", "preparer": PREPARER,
            "reviewer": None, "approver": None, "rejected": None, "dispositions": {}, "evidence": {}, "frozen": None, "history": []}


def _load(case):
    """The record for the latest pack; a newer pack starts a new draft record (the old one is kept in history)."""
    p, latest = _file(case), (packs(case) or [None])[-1]
    state = json.loads(p.read_text()) if p.is_file() else None
    if state is None or (latest and state.get("pack") != latest):
        old = state
        state = _fresh(case, latest)
        if old:
            state["history"] = old.get("history", []) + [{"at": _now(), "event": f"new pack {latest}; record for {old.get('pack')} closed in state {old.get('state')}"}]
    return state


def _event(state, case, action, name, reason, details=None):
    state["history"].append({"at": _now(), "event": action, "name": name, "reason": reason})
    audit.append(case, f"moc_{action}", name, reason, {"pack": state.get("pack"), **(details or {})})


def _check_frozen(case, state):
    """An approved package that changed afterwards goes back to draft, naming the changed files."""
    if state.get("state") != "approved" or not state.get("frozen"):
        return False
    now = manifest(case, state["pack"])
    if now["hash"] == state["frozen"]["hash"]:
        return False
    old = state["frozen"]["files"]
    changed = sorted(k for k in set(old) | set(now["files"]) if old.get(k) != now["files"].get(k))
    state.update(state="draft", changed_since_approval=changed, reviewer=None, approver=None)
    _event(state, case, "package_changed", None, "package changed since approval", {"changed": changed})
    return True


def status(case):
    state = _load(case)
    state.setdefault("evidence", {})
    if _check_frozen(case, state):
        _write(case, state)
    c = checks(case)
    undisposed = [r["id"] for r in c["fail"] if r["id"] not in state["dispositions"]]
    ws = _ws(case)
    files = [{"path": str(f.relative_to(ws)), "bytes": f.stat().st_size} for f in package_files(case, state["pack"])] if state["pack"] else []
    memo = ws / (state["pack"] or "-") / "memo.md"
    rec = next((ln.split(":**", 1)[1].strip() for ln in (memo.read_text().splitlines() if memo.is_file() else [])
                if ln.startswith("**Recommendation:**")), None)
    decision = ws / (state.get("pack") or "-") / "decision.json"
    pack_design = (json.loads(decision.read_text()).get("design") or {}) if decision.is_file() else {}
    return {**state, "checks": c, "undisposed": undisposed, "files": files, "kinds": KINDS, "recommendation": rec, "pack_design": pack_design,
            "must_fix": [k for k, v in state["dispositions"].items() if v.get("kind") == "must_fix"]}


def evidence(case, check_id, note, name):
    """Record supplied evidence without pretending that it closes or recalculates the gate."""
    s = _load(case)
    _need(s, "draft", "reviewed")
    valid = {r["id"] for rows in checks(case).values() for r in rows}
    if check_id not in valid:
        raise ValueError(f"{check_id} is not a failed or open check of this design")
    if not str(note or "").strip():
        raise ValueError("evidence needs a written note")
    row = {"note": str(note).strip(), "by": _name(name), "at": _now()}
    s.setdefault("evidence", {}).setdefault(check_id, []).append(row)
    if s["state"] == "reviewed":
        s.update(state="draft", reviewer=None)
    _event(s, case, "evidence_recorded", name, note, {"check": check_id})
    _write(case, s)
    return status(case)


def _need(s, *allowed):
    if s["state"] not in allowed:
        raise ValueError(f"not allowed in state {s['state']} (needs {' or '.join(allowed)})")


def _name(name):
    name = str(name or "").strip()
    if not name:
        raise ValueError("a name is required")
    return name


def dispose(case, check_id, kind, reason, name):
    """Write the disposition of one failed check. Changing one after review sends the pack back to draft."""
    s = _load(case)
    _need(s, "draft", "reviewed")
    if kind not in KINDS:
        raise ValueError("kind must be accepted_risk or must_fix")
    if not str(reason or "").strip():
        raise ValueError("a disposition needs a written reason")
    if check_id not in [r["id"] for r in checks(case)["fail"]]:
        raise ValueError(f"{check_id} is not a failed check of this design")
    s["dispositions"][check_id] = {"kind": kind, "reason": str(reason).strip(), "by": _name(name), "at": _now()}
    if s["state"] == "reviewed":
        s.update(state="draft", reviewer=None)
    _event(s, case, "disposition", name, reason, {"check": check_id, "kind": kind})
    _write(case, s)
    return status(case)


def _complete(case, s):
    missing = [r["id"] for r in checks(case)["fail"] if r["id"] not in s["dispositions"]]
    if missing:
        raise ValueError("every failed check needs a disposition first: " + ", ".join(missing))


def review(case, name, note=""):
    s = _load(case)
    _need(s, "draft")
    if not s["pack"]:
        raise ValueError("no decision pack to review")
    _complete(case, s)
    s.update(state="reviewed", reviewer={"name": _name(name), "at": _now(), "note": str(note or "")}, changed_since_approval=None)
    _event(s, case, "reviewed", name, note)
    _write(case, s)
    return status(case)


def _approver(s, name):
    name = _name(name)
    if s.get("reviewer") and name.casefold() == s["reviewer"]["name"].casefold():
        raise ValueError("the approver cannot be the reviewer")
    return name


def approve(case, name, note=""):
    s = _load(case)
    _need(s, "reviewed")
    name = _approver(s, name)
    _complete(case, s)
    if any(v.get("kind") == "must_fix" for v in s["dispositions"].values()):
        raise ValueError("a check is marked must fix: reject the pack or change the disposition")
    frozen = manifest(case, s["pack"])
    s.update(state="approved", approver={"name": name, "at": _now(), "note": str(note or "")},
             frozen={**frozen, "at": _now(), "open_items": [r["id"] for r in checks(case)["open"]]})
    _event(s, case, "approved", name, note, {"manifest_hash": frozen["hash"], "files": len(frozen["files"])})
    _write(case, s)
    return status(case)


def reject(case, name, reason):
    s = _load(case)
    _need(s, "reviewed")
    name = _approver(s, name)
    if not str(reason or "").strip():
        raise ValueError("a rejection needs a reason")
    s.update(state="rejected", rejected={"name": name, "at": _now(), "reason": str(reason).strip()})
    _event(s, case, "rejected", name, reason)
    _write(case, s)
    return status(case)


def reopen(case, name, reason):
    """A rejected pack goes back to draft once the reason is answered (the record keeps the rejection in history)."""
    s = _load(case)
    _need(s, "rejected")
    s.update(state="draft", reviewer=None, approver=None)
    _event(s, case, "reopened", _name(name), reason)
    _write(case, s)
    return status(case)
