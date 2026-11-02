"""A feed composition change (feeds.<id>.x.<compound>) reaches the solved spec: written as a flat key it was ignored and
the server re-solved the old composition (Norco: an infeasible column reported only as a PR EOS failure)."""
import unittest

from plantagent.plant import _get_field, change_errors, patch

SPEC = {"compounds": ["Ethylene", "Ethane"], "package": "Peng-Robinson (PR)",
        "feeds": {"FEED": {"T_C": -9.5, "P_bar": 25.5, "kg_h": 92000, "x": {"Ethylene": 0.641, "Ethane": 0.359}}},
        "units": [{"id": "C1", "type": "distillation", "in": "FEED", "distillate": "D", "bottoms": "B", "stages": 10,
                   "feed_stage": 5, "reflux_ratio": 6.0, "bottoms_mol_s": 300}],
        "limits": {}}


class PatchNestedTest(unittest.TestCase):
    def test_feed_composition_change_is_applied_inside_x(self):
        s = patch(SPEC, [{"path": "feeds.FEED.x.Ethylene", "value": 0.7052}, {"path": "feeds.FEED.x.Ethane", "value": 0.2912}])
        self.assertEqual(s["feeds"]["FEED"]["x"], {"Ethylene": 0.7052, "Ethane": 0.2912})
        self.assertNotIn("x.Ethylene", s["feeds"]["FEED"])
        self.assertEqual(SPEC["feeds"]["FEED"]["x"]["Ethylene"], 0.641)  # the original spec is untouched

    def test_plain_fields_still_set(self):
        s = patch(SPEC, [{"path": "units.C1.reflux_ratio", "value": 5.2}])
        self.assertEqual(s["units"][0]["reflux_ratio"], 5.2)

    def test_rated_limit_edited_by_path_asks_for_replace_unit(self):
        spec = {**SPEC, "units": [{**SPEC["units"][0], "tray_capacity_factor": 1.3}],
                "limits": {"C1": {"tray_capacity_factor": 1.3, "diameter_m": 4.877}}}
        errs = change_errors(spec, [{"path": "units.C1.tray_capacity_factor", "value": 1.85,
                                     "physical_change": "re-tray", "rating_source": "vendor"}])
        self.assertTrue(errs and "replace_unit" in errs[0], errs)
        ok = change_errors(spec, [{"replace_unit": "C1", "new_rating": {"tray_capacity_factor": 1.85}, "basis": "vendor rating",
                                  "vendor_confirm": True}])
        self.assertEqual(ok, [])

    def test_from_value_reads_the_nested_field(self):
        self.assertEqual(_get_field(SPEC["feeds"]["FEED"], "x.Ethane"), 0.359)
        self.assertEqual(_get_field(SPEC["feeds"]["FEED"], "kg_h"), 92000)

    def test_unknown_or_invalid_composition_is_rejected(self):
        for field, value in (("x.Typo", 0.1), ("y.Ethylene", 0.1), ("x.Ethylene", -0.1), ("x.Ethylene", float("nan"))):
            with self.subTest(field=field, value=value):
                errors = change_errors(SPEC, [{"path": f"feeds.FEED.{field}", "value": value}])
                self.assertTrue(errors)

    def test_known_compound_can_be_added_to_existing_composition(self):
        spec = {**SPEC, "compounds": [*SPEC["compounds"], "Methane"]}
        changed = patch(spec, [{"path": "feeds.FEED.x.Methane", "value": 0.01}])
        self.assertEqual(changed["feeds"]["FEED"]["x"]["Methane"], 0.01)


if __name__ == "__main__":
    unittest.main()
