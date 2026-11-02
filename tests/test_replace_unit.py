import json
import unittest
from pathlib import Path
from unittest import mock

from plantagent import process, revb
from plantagent.loop import _fix_prompt
from plantagent.plant import PlantWorkspace, patch


ROOT = Path(__file__).resolve().parents[1]
CASE = "basf_process_column_k_2750_dexpi_c02_uns"


def workspace(spec):
    w = object.__new__(PlantWorkspace)
    w.cfg, w.built, w._state = {"target_scale": 1.2}, {"spec": spec, "label": "stored C02 model"}, {}
    w.state = lambda scale: process.run(spec, scale)
    return w


class ReplaceUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / "runs" / "ws" / CASE / "model.json").read_text())["spec"]
        cls.change = {"replace_unit": "K 2750", "new_rating": {"diameter_m": 0.6},
                      "basis": "Fair flooding below 80 percent at 120 percent feed", "vendor_confirm": True}

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_600_mm_replacement_verifies_without_changing_purity(self):
        before = process.run(self.spec, 1.2)
        result = workspace(self.spec).verify({"tag": "K 2750", "changes": [self.change]})
        after_spec = patch(self.spec, [self.change])
        after = process.run(after_spec, 1.2)
        flood = next(c for c in after["checks"] if c["id"] == "K 2750" and "flood" in c["check"])

        purity = lambda solved: solved["streams"]["VENT_INT"]["components_kg_h"]["Ethanol"] / sum(  # noqa: E731
            solved["streams"]["VENT_INT"]["components_kg_h"].values())
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["verification_status"], "verified (new rating, vendor to confirm)")
        self.assertLess(flood["value"], 0.8)
        self.assertAlmostEqual(purity(before), purity(after), places=8)
        self.assertEqual(result["open_checks"][0]["status"], "open")
        self.assertEqual(result["open_checks"][0]["check"], "vendor confirmation of K 2750 new rating")
        self.assertEqual(after_spec["limits"]["K 2750"]["diameter_m"], 0.6)

    def test_plain_limit_edit_and_non_rating_replacement_stay_refused(self):
        plain = workspace(self.spec).verify({"changes": [{"path": "limits.K 2750.diameter_m", "value": 0.6}]})
        invalid = workspace(self.spec).verify({"changes": [{"replace_unit": "K 2750", "new_rating": {"reflux_ratio": 2},
                                                             "basis": "more separation", "vendor_confirm": True}]})
        self.assertFalse(plain["verified"])
        self.assertIn("changes a documented limit", plain["unverified_reason"])
        self.assertFalse(invalid["verified"])
        self.assertIn("not an existing rating or geometry field", invalid["unverified_reason"])
        compressor = {"feeds": {}, "units": [{"id": "K-1", "type": "compressor"}],
                      "limits": {"K-1": {"max_kg_h": 100000}}}
        replaced = patch(compressor, [{"replace_unit": "K-1", "new_rating": {"max_kg_h": 125000},
                                       "basis": "larger wheel", "vendor_confirm": True}])
        self.assertEqual(replaced["limits"]["K-1"]["max_kg_h"], 125000)

    def test_rev_b_cloud_marks_replaced_unit(self):
        svg = (ROOT / "cases" / CASE / "pid.svg").read_text()
        drawing = revb.generate(svg, self.spec, [{"rev": 1, "title": "New shell", "changes": [self.change]}])
        self.assertIn('data-replaced="K 2750"', drawing["svg"])
        self.assertIn("K 2750 REPLACED", drawing["svg"])
        self.assertEqual(drawing["unplaced"], [])

    def test_limit_rejection_teaches_the_fix_round_to_replace(self):
        prompt = _fix_prompt("reach 120 percent", [{"check": "proposal rejected",
                                                     "title": "changes a documented limit limits.K 2750.diameter_m"}], {})
        self.assertIn("replace_unit: id", prompt)
        self.assertIn("vendor_confirm: true", prompt)

    def test_accept_records_replacement_and_open_checks_in_revision_and_audit(self):
        w = object.__new__(PlantWorkspace)
        w.name, w.model, w.built, w.revisions, w.answers, w.rev_file = "test", "model", {"spec": self.spec}, [], [], None
        verified = {"verified": True, "capacity_multiple": 1.2, "new_equipment": [],
                    "replaced_equipment": [{"id": "K 2750", "new_rating": {"diameter_m": 0.6}}],
                    "open_checks": [{"check": "vendor confirmation of K 2750 new rating", "status": "open"}],
                    "calculation": None}
        w.verify = lambda proposal: verified
        w._commit = lambda revision: w.revisions.append(revision)
        proposal = {"title": "Replace shell", "changes": [self.change]}
        with mock.patch("plantagent.plant.audit.append", return_value={"hash": "audit"}) as append:
            w.accept(proposal, reason="capacity replacement")
        self.assertEqual(w.revisions[0]["replaced_equipment"], verified["replaced_equipment"])
        self.assertEqual(w.revisions[0]["open_checks"], verified["open_checks"])
        details = append.call_args.args[4]
        self.assertEqual(details["replaced_equipment"], verified["replaced_equipment"])
        self.assertEqual(details["open_checks"], verified["open_checks"])


if __name__ == "__main__":
    unittest.main()
