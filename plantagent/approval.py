"""Small, audit-chained review and sign-off record for issued MOC packs."""
import hashlib
import json
import os
import time
import zipfile
from pathlib import Path

from . import audit
from .revb import design_answer

ROOT = Path(__file__).resolve().parent.parent
ROLES = {"process", "electrical", "safety", "operations", "manager"}
TARGETS = {"proposal", "gate", "document"}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _file(case):
    return ROOT / "runs" / "ws" / case / "approvals.json"


def _source(w):
    answer = design_answer(w.answers)
    payload = {"model": (w.built or {}).get("label"), "spec": w.spec,
               "revisions": getattr(w, "revisions", []),
               "proposal": {k: (answer or {}).get(k) for k in ("headline", "proposals", "combined")}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _read(case):
    path = _file(case)
    return json.loads(path.read_text()) if path.exists() else {"version": 1, "case": case, "packs": [], "comments": [], "signoffs": []}


def _write(case, value):
    path = _file(case)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=1))
    os.replace(tmp, path)


def _manifest(folder):
    rows = []
    for path in sorted(p for p in folder.iterdir() if p.is_file() and p.name not in {"approval.json", "decision.zip"}):
        rows.append([path.name, hashlib.sha256(path.read_bytes()).hexdigest()])
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def _invalidate(w, state, user=None, reason="design changed"):
    current = _source(w)
    active = [p for p in state["packs"] if p.get("status") == "issued"]
    if not active or active[-1].get("source_hash") == current:
        return False
    pack = active[-1]
    pack.update(status="superseded", superseded_at=_now(), superseded_reason=reason)
    for signoff in state["signoffs"]:
        if signoff.get("pack_revision") == pack["revision"] and signoff.get("active", True):
            signoff.update(active=False, invalidated_at=_now(), invalidated_reason=reason)
    audit.append(w.name, "approval_invalidated", user, reason,
                 {"pack_revision": pack["revision"], "source_hash": current})
    return True


def invalidate(w, user=None, reason="design changed"):
    state = _read(w.name)
    if not state["packs"] or not _invalidate(w, state, user, reason):
        return False
    _write(w.name, state)
    return True


def status(w):
    state = _read(w.name)
    if _invalidate(w, state):
        _write(w.name, state)
    current = _source(w)
    for pack in state["packs"]:
        folder = w.model_file.parent / pack["folder"]
        pack["integrity"] = "intact" if folder.is_dir() and _manifest(folder) == pack.get("manifest_hash") else "changed"
    state["source_hash"] = current
    state["next_revision"] = max([p["revision"] for p in state["packs"]] or [0]) + 1
    state["roles"] = sorted(ROLES)
    state["target_types"] = sorted(TARGETS)
    return state


def issue(w, folder, user=None, reason=None):
    state = _read(w.name)
    _invalidate(w, state, user, "design changed before issue")
    path = w.model_file.parent / Path(str(folder)).name
    if not path.is_dir() or not (path / "decision.json").is_file():
        raise ValueError("issue an existing decision pack folder")
    if any(p["folder"] == path.name for p in state["packs"]):
        raise ValueError("that pack is already issued and frozen")
    revision = max([p["revision"] for p in state["packs"]] or [0]) + 1
    record = {"id": f"MOC-{w.name}-R{revision}", "revision": revision, "folder": path.name, "status": "issued",
              "issued_at": _now(), "issued_by": user or "engineer (unauthenticated)", "reason": str(reason or ""),
              "source_hash": _source(w), "manifest_hash": _manifest(path)}
    approval_file = {k: record[k] for k in ("id", "revision", "status", "issued_at", "issued_by", "reason", "source_hash", "manifest_hash")}
    (path / "approval.json").write_text(json.dumps(approval_file, indent=1))
    archive = path / "decision.zip"
    if archive.exists():
        with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED) as z:
            z.writestr("approval.json", json.dumps(approval_file, indent=1))
    state["packs"].append(record)
    _write(w.name, state)
    audit.append(w.name, "pack_issued", user, reason, {"pack_id": record["id"], "revision": revision,
                                                         "folder": path.name, "manifest_hash": record["manifest_hash"]})
    return record


def comment(w, target_type, target_id, text, user=None, pack_revision=None):
    if target_type not in TARGETS:
        raise ValueError("target_type must be proposal, gate or document")
    if not str(target_id or "").strip() or not str(text or "").strip():
        raise ValueError("target_id and comment text are required")
    state = _read(w.name)
    _invalidate(w, state, user)
    revision = int(pack_revision or max([p["revision"] for p in state["packs"] if p.get("status") == "issued"] or [0]))
    if not revision:
        raise ValueError("issue a pack before commenting")
    row = {"id": len(state["comments"]) + 1, "pack_revision": revision,
           "target": {"type": target_type, "id": str(target_id)}, "text": str(text).strip(),
           "name": user or "engineer (unauthenticated)", "at": _now()}
    state["comments"].append(row)
    _write(w.name, state)
    audit.append(w.name, "approval_comment", user, row["text"], {"pack_revision": revision, "target": row["target"]})
    return row


def signoff(w, role, name, reason, user=None, pack_revision=None):
    if role not in ROLES:
        raise ValueError("unknown sign-off role")
    if not str(name or "").strip() or not str(reason or "").strip():
        raise ValueError("name and reason are required")
    state = _read(w.name)
    _invalidate(w, state, user)
    current = [p for p in state["packs"] if p.get("status") == "issued" and p.get("source_hash") == _source(w)]
    revision = int(pack_revision or (current[-1]["revision"] if current else 0))
    if not any(p["revision"] == revision and p.get("status") == "issued" and p.get("source_hash") == _source(w) for p in state["packs"]):
        raise ValueError("sign-off requires the current issued pack")
    for old in state["signoffs"]:
        if old["pack_revision"] == revision and old["role"] == role and old.get("active", True):
            old.update(active=False, invalidated_at=_now(), invalidated_reason="role signed again")
    row = {"id": len(state["signoffs"]) + 1, "pack_revision": revision, "role": role,
           "name": str(name).strip(), "reason": str(reason).strip(), "at": _now(), "active": True}
    state["signoffs"].append(row)
    _write(w.name, state)
    audit.append(w.name, "approval_signoff", user or name, reason,
                 {"pack_revision": revision, "role": role, "name": row["name"]})
    return row
