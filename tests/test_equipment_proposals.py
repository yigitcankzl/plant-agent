import unittest

from plantagent import process
from plantagent.plant import PlantWorkspace, describe_change, patch


BASE = {
    "compounds": ["Methane"],
    "package": "Peng-Robinson (PR)",
    "feeds": {"F": {"T_C": 25, "P_bar": 1.2, "kg_h": 100000, "x": {"Methane": 1}}},
    "units": [{"id": "K-1", "type": "compressor", "in": "F", "out": "PRODUCT", "P_out_bar": 3, "eff_pct": 75}],
    "limits": {"K-1": {"max_kg_h": 100000}},
}


def workspace():
    w = object.__new__(PlantWorkspace)
    w.cfg, w.built, w._state = {"target_scale": 1.2}, {"spec": BASE}, {}
    w.state = lambda scale: process.run(BASE, scale)
    return w


class EquipmentProposalTests(unittest.TestCase):
    def test_existing_rating_cannot_be_raised(self):
        result = workspace().verify({"tag": "K-1", "changes": [{"path": "limits.K-1.max_kg_h", "value": 125000}]})
        self.assertFalse(result["verified"])
        self.assertIn("changes a documented limit", result["unverified_reason"])
        missing_source = workspace().verify({"changes": [{"add_unit": {"id": "K-2", "type": "compressor"},
                                                            "limits": {"max_kg_h": 25000}}]})
        self.assertFalse(missing_source["verified"])
        self.assertIn("needs rating_source", missing_source["unverified_reason"])

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_parallel_compressor_verifies_and_lifts_suction_limit(self):
        changes = [
            {"add_unit": {"id": "SP-2", "type": "splitter", "in": "F", "out": ["K1-SUC", "K2-SUC"],
                          "fractions": [.8, .2]}},
            {"reroute": {"unit": "K-1", "field": "in", "value": "K1-SUC"}},
            {"reroute": {"unit": "K-1", "field": "out", "value": "K1-DIS"}},
            {"add_unit": {"id": "K-2", "type": "compressor", "in": "K2-SUC", "out": "K2-DIS",
                          "P_out_bar": 3, "eff_pct": 75},
             "limits": {"max_kg_h": 25000}, "rating_source": "standard 25 t/h size; vendor quote to confirm"},
            {"add_unit": {"id": "MX-2", "type": "mixer", "in": ["K1-DIS", "K2-DIS"], "out": "PRODUCT"}},
        ]
        before = process.run(BASE, 1.2)
        self.assertGreater(next(c["utilisation"] for c in before["checks"] if c["id"] == "K-1"), 1)

        result = workspace().verify({"tag": "K-1", "changes": changes})
        self.assertTrue(result["verified"], result)
        self.assertTrue(result["reaches_target"], result)
        self.assertGreater(result["capacity_multiple"], 1.2)
        self.assertEqual(result["new_equipment"][0]["status"], "new equipment, rating to confirm")
        self.assertEqual(result["new_equipment"][0]["id"], "K-2")

        proposed = patch(BASE, changes)
        checks = {c["id"]: c["utilisation"] for c in process.run(proposed, 1.2)["checks"] if "utilisation" in c}
        self.assertAlmostEqual(checks["K-1"], .96, places=2)
        self.assertAlmostEqual(checks["K-2"], .96, places=2)
        self.assertEqual(proposed["limits"]["K-2"]["max_kg_h"], 25000)
        self.assertEqual(describe_change(BASE, changes[3]),
                         "Adds K-2 compressor, 25 t/h suction (provisional rating: standard 25 t/h size; vendor quote to confirm)")


if __name__ == "__main__":
    unittest.main()
