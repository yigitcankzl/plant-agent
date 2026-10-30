"""Case documents as the agent sees them: allowed pages only, recommendation clauses withheld."""
import base64
import json
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_DATA_CANDIDATES = (ROOT.parent / "case-data", Path.home() / "Desktop" / "hackathon" / "case-data")
DATA = Path(os.getenv("PLANTAGENT_DATA_ROOT") or next((path for path in _DATA_CANDIDATES if path.exists()),
                                                      _DATA_CANDIDATES[0])).expanduser().resolve()

# Clauses that state a recommendation or a conclusion about a required change.
# Applied per clause (split on , ; :) so facts sharing a sentence with a conclusion survive.
# ponytail: keyword heuristic; leaks are caught by Case.leaks() against the answer key phrases.
CONCLUSION = re.compile(
    r"\b(should|recommend\w*|will (?:need|be needed|require|be required|provide|result in)|need(?:s)? to be|"
    r"would (?:need|require|provide|be required)|must be|it (?:is|will be) necessary|"
    r"true firm capacity|inadequate|insufficient|replace(?:d|ment)? (?:with|by)|bottleneck|"
    r"bringing the|preferred|propose[ds]?|it is suggested|suggest(?:s|ed)? that)\b",
    re.I,
)


@lru_cache
def _pages(pdf):
    if str(pdf).endswith(".txt"):  # plain-text source (e.g. a dataset README): one page
        return [Path(pdf).read_text()]
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return out.split("\f")


def _paragraphs(text):
    # Join wrapped lines into paragraphs; keep table rows (runs of 3+ spaces) as their own lines.
    lines, para = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or re.search(r"\S {3,}\S", line):
            if para:
                lines.append(" ".join(para)); para = []
            if line:
                lines.append(line)
        else:
            para.append(line)
    if para:
        lines.append(" ".join(para))
    return lines


def redact(text):
    out, hidden = [], 0
    for line in _paragraphs(text):
        kept = []
        for sentence in re.split(r"(?<=[.;])\s+(?=[A-Z0-9(])", line):
            clauses = re.split(r"(?<=[,;:])\s+", sentence)
            keep = [c for c in clauses if not CONCLUSION.search(c)]
            hidden += len(clauses) - len(keep)
            if keep:
                kept.append(" ".join(keep))
        if kept:
            out.append(" ".join(kept))
    return "\n".join(out), hidden


class Case:
    def __init__(self, name):
        self.name = name
        self.dir = ROOT / "cases" / name
        self.cfg = cfg = json.loads((self.dir / "case.json").read_text())
        self.pdf = DATA / cfg["pdf"]
        self.pages = [p for a, b in cfg["allowed_pages"] for p in range(a, b + 1)]
        self.question = cfg["question"]
        self.strip = cfg.get("strip", [])
        key = self.dir / "answer_key.json"
        self.answer_key = json.loads(key.read_text()) if key.exists() else None

    def page(self, n):
        n = int(n)
        if n not in self.pages:
            return f"Page {n} is not available. Available pages: {self.pages}."
        text = _pages(self.pdf)[n - 1]
        for pat in self.strip:
            text = re.sub(pat.replace(" ", r"\s+"), "[withheld]\n", text, flags=re.S | re.I)
        # A sentence continuing from the previous page is judged together with its beginning.
        head = re.match(r"\s*([a-z][^.;]*[.;])", text)
        if head and n > 1:
            tail = re.split(r"(?<=[.;])\s+", re.sub(r"\s+", " ", _pages(self.pdf)[n - 2]).strip())[-1]
            if CONCLUSION.search(tail + " " + head.group(1)):
                text = text[head.end():]
        if not self.cfg.get("redact", True):  # raw source documents: nothing is withheld
            return f"[p.{n}]\n" + "\n".join(_paragraphs(text))
        body, hidden = redact(text)
        return f"[p.{n}]\n" + body + (f"\n[{hidden} recommendation clause(s) withheld]" if hidden else "")

    def page_image(self, n, dpi=100):
        """PNG of an allowed page as a data URL, for figures, curves and drawings."""
        n = int(n)
        if n not in self.pages:
            raise ValueError(f"page {n} not available")
        png = subprocess.run(["pdftoppm", "-f", str(n), "-l", str(n), "-r", str(dpi), "-png", str(self.pdf)],
                             capture_output=True, check=True).stdout
        return "data:image/png;base64," + base64.b64encode(png).decode()

    def search(self, query):
        terms = [t.lower() for t in query.split()]
        hits = sorted(((sum(self.page(n).lower().count(w) for w in terms), n) for n in self.pages), reverse=True)
        return [n for score, n in hits[:8] if score]

    def visible_text(self):
        return "\n".join(self.page(n) for n in self.pages)

    def leaks(self):
        """Answer-key phrases that still appear in what the agent can read."""
        text = re.sub(r"\s+", " ", self.visible_text().lower())
        phrases = [p for item in (self.answer_key or {}).get("items", []) for p in item.get("leak_phrases", [])]
        return [p for p in phrases if re.sub(r"\s+", " ", p.lower()) in text]


def all_cases(kind="study"):
    """Document-study cases by default; kind="process" lists the P&ID process-plant workspaces."""
    return sorted(p.name for p in (ROOT / "cases").iterdir() if (p / "case.json").exists()
                  and json.loads((p / "case.json").read_text()).get("kind", "study") == kind)


if __name__ == "__main__":
    for name in all_cases():
        c = Case(name)
        leaks = c.leaks()
        print(f"{name}: {len(c.pages)} pages, {len(c.visible_text())} chars, leaks={leaks}")
        assert not leaks, f"{name} leaks answer-key phrases: {leaks}"
    r = Case("roseburg")
    assert "0.4 fps" in r.page(109) and "4,200 gpm" in r.page(108), "facts must survive redaction"
