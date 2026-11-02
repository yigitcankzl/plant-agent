import json
import tempfile
import unittest
from pathlib import Path

from tools import revamp_compare


class RevampCompareTests(unittest.TestCase):
    def test_synthetic_worklog_scores_change_and_after_values(self):
        log = {
            "status": "done",
            "rounds": [{"steps": [
                {"actor": "Muse", "title": "Rerate the first stage", "changes": [{
                    "replace_unit": "C1", "new_rating": {"first_stage_bore_in": 20.5},
                    "basis": "increase first stage bore and remove the double deck valve restriction",
                }]},
                {"actor": "DWSIM", "check": "compressor flow capacity", "status": "pass",
                 "numbers": {"value": 30.9}},
            ]}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "worklog.json"
            path.write_text(json.dumps(log))
            result = revamp_compare.score("revamp_toledo_h2_compressors", path)
        self.assertEqual(result["loop_status"], "done")
        self.assertEqual(result["change_type"], "match")
        flow = next(x for x in result["after_data"] if x["id"] == "flow_each")
        bore = next(x for x in result["after_data"] if x["id"] == "first_stage_bore")
        self.assertEqual((flow["actual"], flow["error_pct"]), (30.9, 0.0))
        self.assertEqual((bore["actual"], bore["error_pct"]), (20.5, 0.0))
        self.assertIn("Published after data", revamp_compare.markdown(result))

    def test_change_match_partial_and_miss(self):
        cats = [
            {"id": "a", "label": "A", "required": True, "keywords": ["packing"]},
            {"id": "b", "label": "B", "required": True, "keywords": ["preheat"]},
        ]
        base = {"changes": [], "rows": [], "text": []}
        self.assertEqual(revamp_compare._change_score(cats, {**base, "changes": [{"basis": "packing"}]})[0], "partial")
        self.assertEqual(revamp_compare._change_score(cats, base)[0], "miss")

    def test_blind_bases_have_no_withheld_phrases_or_values(self):
        cases = sorted(p.name for p in (revamp_compare.ROOT / "cases").glob("revamp_*") if (p / "outcome.json").exists())
        self.assertEqual(len(cases), 7)
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(revamp_compare.contamination(case), {
                    "redacted_clauses": 0, "phrase_hits": [], "value_hits": [],
                })


if __name__ == "__main__":
    unittest.main()
