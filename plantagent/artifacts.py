"""Engineer-facing outputs of a plant workspace (documents, drawings, calculation sheets), one folder each:
runs/ws/<case>/artifacts/<id>/meta.json + files. Every artifact is a DRAFT until an engineer approves it elsewhere;
this module only stores and lists them. Tools that make an artifact call save(); the web lists and serves them.
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ("document", "drawing", "calculation", "chart", "model_change", "analysis")
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


def _dir(case):
    return ROOT / "runs" / "ws" / case / "artifacts"


def save(case, kind, title, files, by=None, request=None, sources=None, summary=None):
    """files: {file name: bytes or str}. Returns the meta dict (id, kind, title, files, at, by, request, sources, status)."""
    if kind not in KINDS:
        raise ValueError(f"artifact kind must be one of {KINDS}")
    if not files or not all(_NAME.match(n) for n in files):
        raise ValueError("artifact needs at least one file with a plain name (letters, digits, . _ -)")
    at = time.strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or kind
    d = _dir(case) / f"{at}-{slug}"
    n = 1
    while d.exists():
        n += 1
        d = _dir(case) / f"{at}-{slug}-{n}"
    d.mkdir(parents=True)
    for name, data in files.items():
        (d / name).write_bytes(data.encode() if isinstance(data, str) else data)
    meta = {"id": d.name, "kind": kind, "title": title, "files": sorted(files), "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "by": by, "request": request, "sources": sources or [], "summary": summary, "status": "draft"}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    return meta


def list_(case):
    d = _dir(case)
    if not d.exists():
        return []
    out = []
    for m in sorted(d.glob("*/meta.json"), reverse=True):
        try:
            out.append(json.loads(m.read_text()))
        except (OSError, ValueError):
            continue
    return out


def file(case, aid, name):
    """Path of one artifact file, or None (no traversal: plain names only)."""
    if not (_NAME.match(aid or "") and _NAME.match(name or "")) or name == "meta.json":
        return None
    f = (_dir(case) / aid / name).resolve()
    return f if f.is_relative_to(_dir(case).resolve()) and f.is_file() else None


if __name__ == "__main__":
    import shutil
    case = "_artifact_selftest"
    try:
        m = save(case, "document", "K-202 data sheet", {"datasheet.md": "# K-202", "datasheet.pdf": b"%PDF"}, by="test")
        assert m["status"] == "draft" and m["files"] == ["datasheet.md", "datasheet.pdf"]
        assert list_(case)[0]["id"] == m["id"] and file(case, m["id"], "datasheet.md").read_text() == "# K-202"
        assert file(case, m["id"], "../meta.json") is None and file(case, "..", "x") is None
        try:
            save(case, "document", "bad", {"../x": "y"})
            raise AssertionError("traversal name accepted")
        except ValueError:
            pass
        print("ok")
    finally:
        shutil.rmtree(ROOT / "runs" / "ws" / case, ignore_errors=True)
