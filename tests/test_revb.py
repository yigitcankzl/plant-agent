"""Rev B sheet generator (plantagent/revb.py): the proposed P&ID re-issued with the changes drawn in."""
import json
import re
import unittest
from pathlib import Path

from plantagent import revb

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "parallel_compressor.json").read_text())
SALT = (ROOT / "cases" / "salt_mvr" / "pid.svg").read_text()
C01 = (ROOT / "cases" / "chem_c01" / "pid.svg").read_text()


def clouds(svg):
    return {m for m in re.findall(r'data-rev-cloud="(\d+)"', svg)}


class RevBTests(unittest.TestCase):
    def test_parallel_unit_and_value_change_on_the_salt_sheet(self):
        revisions = [
            {"rev": 1, "title": "Clean E-201", "changes": [{"path": "units.E-201.U_W_m2K", "value": 2500, "from": 2000,
                                                           "physical_change": "Clean E-201 circulating heater tubes"}]},
            {"rev": 2, "title": "Parallel K-202", "changes": FIXTURE["changes"], "calculation": FIXTURE["calculation"]},
        ]
        before = (ROOT / "cases" / "salt_mvr" / "pid.svg").read_bytes()
        r = revb.generate(SALT, FIXTURE["spec"], revisions, meta={"drawing": "test"})
        svg = r["svg"]
        self.assertEqual((ROOT / "cases" / "salt_mvr" / "pid.svg").read_bytes(), before)  # the case file is only read
        self.assertEqual(r["unplaced"], [])
        self.assertIn('data-tag="K-202" data-pid="K-202" data-new="true"', svg)  # added unit drawn as a symbol
        self.assertIn("K-202 (NEW)", svg)
        self.assertIn("Rating source: preliminary size; vendor quote to confirm", svg)
        self.assertIn('data-line="K202-SUC"', svg)  # routed new line
        self.assertIn("U 2000 → 2500 W/m²K", svg)  # annotation of the changed value next to E-201
        self.assertEqual(clouds(svg), {"1", "2"})  # one revision cloud (and triangle) per change
        self.assertEqual(len(re.findall(r'data-rev-triangle="1"', svg)), 2)  # on the sheet and in the revision block
        self.assertIn("REV B - DRAFT - NOT APPROVED", svg)
        self.assertIn("PA-SALT-01 · Rev B", svg)
        for tag in re.findall(r'<g data-tag="([^"]+)"', SALT):  # every existing group survives for the viewer
            self.assertIn(f'data-tag="{tag}"', svg)
        self.assertNotEqual(re.search(r'viewBox="([^"]*)"', svg).group(1), re.search(r'viewBox="([^"]*)"', SALT).group(1))

    def test_value_changes_on_the_dexpi_sheet(self):
        spec = {"units": [{"id": "H1007", "type": "hx", "hot": ["a", "b"], "cold": ["s47130", "c"]}, {"id": "T4750", "type": "tank", "in": "b", "out": "d"}],
                "feeds": {"s47130": {"m3_h": 20}}}
        revisions = [{"rev": 1, "title": "CW", "changes": [{"path": "feeds.s47130.m3_h", "value": 27.0, "from": 20.0}]},
                     {"rev": 2, "title": "Level", "changes": [{"path": "units.T4750.volume_m3", "value": 22.1, "from": 20.8}]}]
        r = revb.generate(C01, spec, revisions, names={"s47130": "Cooling water to H1007"})
        self.assertEqual(r["unplaced"], [])
        self.assertIn("Cooling water flow 20 → 27 m³/h", r["svg"])
        self.assertIn("working volume 20.8 → 22.1 m³", r["svg"])
        self.assertEqual(clouds(r["svg"]), {"1", "2"})
        self.assertEqual(r["clouds"], 2)

    def test_free_note_and_geometry_with_transforms(self):
        sheet = revb.Sheet(C01)
        x0, y0, x1, y1 = sheet.boxes["T4750"]  # the DEXPI symbol, not its data table or label
        self.assertLess(x1 - x0, 60)
        self.assertLess(y1 - y0, 70)
        r = revb.generate(C01, {"units": []}, [{"rev": 1, "title": "Note", "changes": [],
                                                "notes": [{"tag": "H1008", "text": "bypass to be added here"}]}])
        self.assertIn("bypass to be added here", r["svg"])
        self.assertIn('data-note="H1008"', r["svg"])
        self.assertEqual(r["clouds"], 1)

    def test_render_revision_for_the_agent_tool(self):
        class W:  # the workspace surface render_revision uses
            name, cfg, built, revisions, answers = "salt_mvr", {"svg": "pid.svg"}, {"spec": FIXTURE["spec"]}, [], []
            spec = FIXTURE["spec"]
            names = staticmethod(lambda: {})
        svg = revb.render_revision(W(), FIXTURE["changes"], [{"line": "3003", "text": "bypass to be added here"}], "K-202 study")
        self.assertIn('data-tag="K-202"', svg)
        self.assertIn("bypass to be added here", svg)
        self.assertIn("NOT verified in DWSIM", svg)  # a drawing request is not a verification
        with self.assertRaises(ValueError):
            revb.render_revision(W(), [{"path": "units.NOPE.U_W_m2K", "value": 1}])


if __name__ == "__main__":
    unittest.main()
