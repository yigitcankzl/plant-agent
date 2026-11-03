"""Monterey and Brownsville seawater cases: historian loads, the drawing parses, citations are on the data sheet."""
import json
import re
import unittest
from pathlib import Path

from plantagent import health, pid

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"
DATA = Path("/home/kizil/Desktop/hackathon/case-data/drawn")
CITED = re.compile(r"\(RFP|\(ILLUSTRATIVE|\(derived|\(2004")


def uncited(path):
    bad = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if re.search(r"\d", line) and not CITED.search(line) and not line.strip().startswith("|---"):
            bad.append(f"{path.name}:{i}: {line.strip()[:120]}")
    return bad


class SwroCaseTest(unittest.TestCase):
    def test_monterey_historian_loads(self):
        rows = health.load(CASES / "swro_monterey" / "historian.csv")
        self.assertEqual(len(rows), 772)
        self.assertIn("PI-201 first-pass feed (bar)", rows[0])
        self.assertIsInstance(rows[0]["TI-1001 seawater temperature (C)"], float)
        report = health.check("swro_monterey")
        self.assertEqual(report["samples"], 772)
        self.assertEqual(report["source"], "historian.csv")

    def test_drawings_match_the_equipment_lists(self):
        if not DATA.exists():
            self.skipTest("drawn P&ID files live outside the repo (case-data/drawn)")
        monterey = pid.overview(DATA / "swro_monterey_pid.xml")
        brownsville = pid.overview(DATA / "swro_brownsville_pid.xml")
        self.assertEqual(len(monterey["equipment"]), 19)
        self.assertEqual(len(brownsville["equipment"]), 11)
        self.assertGreaterEqual(len(monterey["connections"]), 15)
        svg = (CASES / "swro_monterey" / "pid.svg").read_text()
        self.assertIn("drawn by PlantAgent on the Monterey RFP flowsheet", svg)
        self.assertEqual(svg.count("data-tag="), 19)
        self.assertGreater(svg.count("data-line="), 15)

    def test_every_basis_number_is_cited(self):
        self.assertEqual(uncited(CASES / "swro_monterey" / "basis.md"), [])
        self.assertEqual(uncited(CASES / "swro_brownsville" / "basis.md"), [])

    def test_pilot_outcome_is_not_a_project_document(self):
        cfg = json.loads((CASES / "swro_brownsville" / "case.json").read_text())
        blob = json.dumps(cfg) + (CASES / "swro_brownsville" / "basis.md").read_text()
        self.assertNotIn("2008", blob)
        self.assertNotIn("2.5", blob)
        hidden = (CASES / "swro_brownsville" / "hidden_outcome.md").read_text()
        self.assertIn("2.5", hidden)
        answer = (CASES / "swro_monterey" / "engineer_answer.md").read_text().split("---", 1)[1]
        self.assertFalse(answer.strip())


if __name__ == "__main__":
    unittest.main()
