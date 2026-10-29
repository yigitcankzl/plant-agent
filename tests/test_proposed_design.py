import json
import tempfile
import unittest
from pathlib import Path

from plantagent import decision
from plantagent.proposed import centers_from_svg, overlay

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "parallel_compressor.json").read_text())
SVG = (ROOT / "cases" / "salt_mvr" / "pid.svg").read_text()
STORED = ("45.4", "1.88", "272.2", "226.8", "9.4", "7719", "95.5", "120.1")


def proposal(**extra):
    body = {"title": "Parallel recompressor", "tag": "K-201", "verified": True, "changes": FIXTURE["changes"],
            "calculation": FIXTURE["calculation"], "cost_class": ">$1M",
            "new_equipment": [{"id": "K-202", "type": "compressor", "limits": {"max_kg_h": 60000, "max_kW": 3000},
                               "rating_source": "preliminary size; vendor quote to confirm",
                               "status": "new equipment, rating to confirm"}]}
    body.update(extra)
    return body


class ProposedDrawingTests(unittest.TestCase):
    def test_as_built_file_is_unchanged_and_existing_coordinates_stay(self):
        path = ROOT / "cases" / "salt_mvr" / "pid.svg"
        before = path.read_bytes()
        before_centers = centers_from_svg(SVG)
        result = overlay(SVG, FIXTURE["spec"], FIXTURE["changes"], FIXTURE["calculation"])
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue(result["drawn"], result["reason"])
        self.assertEqual(result["unplaced"], [])
        after = centers_from_svg(result["svg"])
        for tag, point in before_centers.items():
            self.assertEqual(after[tag], point)
        k201 = SVG[SVG.index('<g data-tag="K-201"'):SVG.index('<g data-tag="D-201"')]
        self.assertIn(k201, result["svg"])
        self.assertTrue(result["svg"].startswith(SVG[:SVG.rfind("</svg>")]))

    def test_parallel_addition_is_drawn_from_the_calculation_record(self):
        result = overlay(SVG, FIXTURE["spec"], FIXTURE["changes"], FIXTURE["calculation"])
        svg = result["svg"]
        for tag in ("K-SPLIT", "K-202", "K-JOIN"):
            self.assertIn(f'data-tag="{tag}"', svg)
            self.assertIn('data-new="true"', svg)
        self.assertIn('data-line="K202-SUC"', svg)
        self.assertIn('data-from="K-SPLIT"', svg)
        self.assertIn('data-to="K-202"', svg)
        self.assertIn("DRAFT – NOT APPROVED", svg)
        self.assertIn("Proposed new", svg)
        self.assertIn("Rerouted", svg)
        self.assertIn("Rating to confirm", svg)
        self.assertIn("vendor confirmation required", svg)
        self.assertIn("vendor curve to confirm", svg)
        for value in STORED:
            if value in ("45.4", "1.88"):
                self.assertIn(value, svg)
        self.assertIn("K-202", result["placed"])

    def test_renderer_does_not_hard_code_the_fixture_numbers(self):
        for rel in ("plantagent/proposed.py", "plantagent/decision.py", "web/plant.html"):
            text = (ROOT / rel).read_text()
            for value in STORED:
                self.assertNotIn(value, text, rel)

    def test_unverified_proposal_is_not_drawn(self):
        result = overlay(SVG, FIXTURE["spec"], FIXTURE["changes"], FIXTURE["calculation"], verified=False)
        self.assertFalse(result["drawn"])
        self.assertEqual(result["svg"], SVG)
        self.assertIn("unverified", result["reason"])
        self.assertNotIn('data-tag="K-202"', result["svg"][len(SVG):] if False else result["svg"][result["svg"].find("K-202"):])
        self.assertEqual(result["svg"], SVG)

    def test_unplaceable_unit_is_named_and_not_drawn(self):
        changes = [{"add_unit": {"id": "H-9", "type": "heater", "in": "S3001", "out": "SNEW", "duty_kW": 10},
                    "limits": {"max_kW": 100}, "rating_source": "to confirm"}]
        result = overlay(SVG, FIXTURE["spec"], changes, None)
        self.assertIn("H-9", result["unplaced"])
        self.assertIn("unplaced new equipment", result["svg"])
        self.assertNotIn('data-tag="H-9"', result["svg"])


def _workspace(tmp, answer, spec=None):
    spec = spec or FIXTURE["spec"]

    class Workspace:
        pass

    w = Workspace()
    model = tmp / "model.json"
    model.write_text(json.dumps({"spec": spec, "label": "fixture", "model": "fixture", "at": "t",
                                  "assumptions": ["fixture"], "review": {"status": "ok", "findings": [], "blocking": 0}}))
    w.model_file = model
    w.name = "salt_mvr"
    w.cfg = {"title": "Salt fixture", "question": "Can a parallel compressor be screened?", "target_scale": 1.2,
             "svg": "pid.svg", "pid": "drawn/salt_mvr_pid.xml"}
    w.revisions = []
    w.answers = [answer]
    w.built = json.loads(model.read_text())
    w.gaps = []
    w.spec = spec
    w._built_spec = lambda: spec
    w.names = lambda: {}
    return w


class DecisionPackTests(unittest.TestCase):
    def setUp(self):
        self.run = decision.process.run
        self.entries, self.verify, self.append = decision.audit.entries, decision.audit.verify, decision.audit.append
        decision.process.run = lambda spec, scale=1.0: {"checks": [
            {"id": "K-201", "check": "flow", "utilisation": 0.5, "value": 1, "limit": 2, "unit": "kg/h"}], "errors": [], "units": {}, "streams": {}}
        decision.audit.entries = lambda case: [{"hash": "abc"}]
        decision.audit.verify = lambda case: {"ok": True, "entries": 1}
        decision.audit.append = lambda *a, **k: {"hash": "abc"}

    def tearDown(self):
        decision.process.run = self.run
        decision.audit.entries, decision.audit.verify, decision.audit.append = self.entries, self.verify, self.append

    def _make(self, answer, spec=None):
        with tempfile.TemporaryDirectory() as folder:
            w = _workspace(Path(folder), answer, spec)
            out = decision.make(w, 0)
            folder = w.model_file.with_name(out["folder"])
            return out, folder, json.loads((folder / "decision.json").read_text()), (folder / "decision.md").read_text(), (
                (folder / "redline.svg").read_text() if (folder / "redline.svg").exists() else "")

    def test_new_equipment_pack_carries_the_stored_record(self):
        out, folder, data, md, svg = self._make({"headline": "Add a compressor", "summary": "Screened.", "proposals": [proposal()],
                                                  "model": "fixture", "field_checks": []})
        self.assertIn("decision.md", out["files"])
        self.assertIn("redline.svg", out["files"])
        calc_json = json.dumps(data["calculation"])
        for value in ("45.4", "1.88", "226.8", "9.4", "7719", "95.5", "120.1"):
            self.assertIn(value, md)
        self.assertTrue("272.2" in md or "272.1" in md)
        self.assertIn("45.4", svg)
        self.assertIn("1.88", svg)
        self.assertIn("operating_point", calc_json)
        self.assertIn("capacity_multiple_after", calc_json)
        self.assertIn("45400", calc_json)
        self.assertIn("1880", calc_json)
        self.assertIn('data-tag="K-202"', svg)
        self.assertIn("Preliminary equipment datasheet", md)
        self.assertIn("Before / Proposed calculation", md)
        self.assertIn("Simulator screening", md)
        self.assertIn("Provisional equipment selection", md)
        self.assertIn("Vendor and mechanical design approval", md)
        self.assertIn("to confirm", md)
        for phrase in ("Isolation", "backflow", "parallel load sharing", "Alarms and trips", "Relief review",
                       "Commissioning", "wet-service", "Vendor curve", "Turndown and surge"):
            self.assertTrue(any(phrase in item for item in data["pssr"]), phrase)
        ids = {u["id"] for u in data["topology"]["units"]}
        self.assertTrue({"K-SPLIT", "K-202", "K-JOIN", "K-201"} <= ids)
        self.assertIn("pressure ratio", md.lower())
        self.assertIn("head", md.lower())

    def test_unverified_answer_does_not_draw_new_equipment(self):
        _, _, data, md, svg = self._make({"headline": "Not verified", "summary": "No.", "proposals": [proposal(verified=False)],
                                           "field_checks": []})
        self.assertNotIn('data-tag="K-202"', svg)
        self.assertEqual(data["calculation"], [])
        self.assertIn("No change", md)

    def test_no_change_and_existing_equipment_packs_still_build(self):
        _, _, data, md, _ = self._make({"headline": "Already fits", "summary": "No plant change.", "proposals": [], "field_checks": []})
        self.assertIn("No change", md)
        self.assertEqual(data["new_equipment"], [])
        existing = proposal(changes=[{"path": "units.K-201.eff_pct", "value": 78}], calculation=None, new_equipment=[])
        _, _, data, md, svg = self._make({"headline": "Raise the setpoint", "summary": "Existing machine only.",
                                           "proposals": [existing], "field_checks": []})
        self.assertNotIn('data-new="true"', svg)
        self.assertNotIn("Preliminary equipment datasheet", md)
        self.assertIn("K-201", md)
        self.assertTrue(data["pssr"])


if __name__ == "__main__":
    unittest.main()
