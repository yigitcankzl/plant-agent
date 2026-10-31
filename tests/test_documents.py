"""Document generators on saved workspace data (no AI): files exist and every number in a table names its source."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from plantagent import artifacts, documents, process
from plantagent.plant import PlantWorkspace

ROOT = Path(__file__).resolve().parent.parent


def sourced(test, md):
    """Every table row with a digit outside its last (Source) column has a non-empty source."""
    rows = [r for r in md.splitlines() if r.startswith("|") and not r.startswith("|---")]
    test.assertTrue(rows, "document has no tables")
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if re.search(r"\d", " ".join(cells[:-1])) and cells[0] not in ("Role",):
            test.assertTrue(cells[-1] and cells[-1] != "Source", f"number without a source: {r}")


class Documents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root, artifacts.ROOT = artifacts.ROOT, Path(self.tmp)

    def tearDown(self):
        artifacts.ROOT = self.root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check(self, w, kind, subject, answer=None):
        m = documents.make(w, kind, subject, answer=answer)
        self.assertEqual(m["status"], "draft")
        self.assertEqual(m["kind"], documents.KINDS[kind])
        md_name = next(n for n in m["files"] if n.endswith(".md"))
        self.assertTrue(any(n.endswith(".pdf") for n in m["files"]), m["summary"])
        for n in m["files"]:
            self.assertTrue(artifacts.file(w.name, m["id"], n), n)
        md = artifacts.file(w.name, m["id"], md_name).read_text()
        self.assertIn("DRAFT", md)
        sourced(self, md)
        return md

    def test_salt_mvr(self):
        w = PlantWorkspace("salt_mvr")
        w.answers = json.loads((ROOT / "runs/ws/salt_mvr/20261030-224752/answers.json").read_text())
        ds = self.check(w, "datasheet", "K-202", 3)
        self.assertIn("proposed new equipment", ds)
        self.assertIn("55,000", ds)  # K-202 suction rating from the proposal, with its rating source
        self.assertIn("vendor quote to confirm", ds)
        calc = self.check(w, "calc_sheet", "V-201: heater area", 3)
        self.assertIn("A_needed", calc)
        self.assertIn("Before / after", calc)
        self.check(w, "summary", None, 3)
        wo = self.check(w, "work_order", "E-201", 3)
        self.assertIn("3003/C1", wo)  # the steam-side isolation valve on the P&ID
        self.assertIn("Acceptance check", wo)
        with self.assertRaises(ValueError):
            documents.make(w, "work_order", "P-101", answer=3)

    @unittest.skipUnless(process.available(), "DWSIM unavailable (chem_c01 proposals carry no stored calculation)")
    def test_chem_c01(self):
        w = PlantWorkspace("chem_c01")
        w.answers = [json.loads((ROOT / "runs/ws/chem_c01/second_opinion_answer.json").read_text())["answer"]]
        self.assertIn("H1007", self.check(w, "datasheet", "H1007", 0))
        self.assertIn("area needed", self.check(w, "calc_sheet", "H1007"))
        self.check(w, "summary", None, 0)
        self.check(w, "work_order", "H1007", 0)


if __name__ == "__main__":
    unittest.main()
