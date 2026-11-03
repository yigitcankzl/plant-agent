import unittest
from plantagent.plant import _redistributes

SPEC = {"feeds": {"UP": {"kg_h": 96500.0}, "LOW": {"kg_h": 1e-06}}}
PATHS = ["feeds.UP.kg_h", "feeds.LOW.kg_h"]


class FeedSplitTest(unittest.TestCase):
    def test_split_at_todays_total_is_allowed(self):
        split = [{"path": "feeds.UP.kg_h", "value": 48250}, {"path": "feeds.LOW.kg_h", "value": 48250}]
        self.assertTrue(_redistributes(SPEC, split, PATHS))

    def test_a_new_rate_is_not_a_split(self):
        more = [{"path": "feeds.UP.kg_h", "value": 117730}]
        self.assertFalse(_redistributes(SPEC, more, ["feeds.UP.kg_h"]))


if __name__ == "__main__":
    unittest.main()


class TrayFactorTest(unittest.TestCase):
    def test_tray_factor_replaces_on_a_column_without_a_written_default(self):
        from plantagent.plant import change_errors
        spec = {"units": [{"id": "T-201", "type": "distillation", "diameter_m": 2.74}], "limits": {"T-201": {"flood_frac_max": 0.8}}}
        ch = [{"replace_unit": "T-201", "new_rating": {"tray_capacity_factor": 1.35}, "basis": "vendor tray", "vendor_confirm": True}]
        self.assertEqual([e for e in change_errors(spec, ch) if "tray_capacity_factor" in e], [])
        pump = {"units": [{"id": "P-1", "type": "pump"}], "limits": {}}
        ch[0]["replace_unit"] = "P-1"
        self.assertTrue(any("not an existing" in e for e in change_errors(pump, ch)))


class AnswerTagJsonTest(unittest.TestCase):
    def test_json_inside_answer_tags(self):
        from plantagent.study import bare_json
        self.assertEqual(bare_json('<answer>\n{"headline": "h"}\n</answer>'), {"headline": "h"})


class PatchUnwrittenRatingTest(unittest.TestCase):
    def test_unwritten_tray_factor_lands_in_limits(self):
        from plantagent.plant import patch
        spec = {"units": [{"id": "T-201", "type": "distillation", "diameter_m": 2.74}], "limits": {}}
        out = patch(spec, [{"replace_unit": "T-201", "new_rating": {"tray_capacity_factor": 1.35, "diameter_m": 3.0}}])
        self.assertEqual(out["limits"]["T-201"], {"tray_capacity_factor": 1.35})
        self.assertEqual(out["units"][0]["diameter_m"], 3.0)
