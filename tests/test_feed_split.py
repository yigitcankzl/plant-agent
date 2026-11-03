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
