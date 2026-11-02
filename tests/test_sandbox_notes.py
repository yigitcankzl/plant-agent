import unittest
from plantagent.plant import sandbox_notes

BASE = {"units": [{"id": "T1", "type": "column", "tray_capacity_factor": 1.3}],
        "limits": {"T1": {"tray_capacity_factor": 1.3}},
        "feeds": {"FEED": {"kg_h": 100.0}, "CW": {"kg_h": 5.0, "utility": True}}}


class SandboxNotes(unittest.TestCase):
    def test_same_spec_is_silent(self):
        self.assertEqual(sandbox_notes(BASE, BASE), [])

    def test_rated_limit_and_feed_rate_are_named(self):
        trial = {"units": [{"id": "T1", "type": "column", "tray_capacity_factor": 1.85}],
                 "feeds": {"FEED": {"kg_h": 125.0}, "CW": {"kg_h": 9.0}}}
        notes = sandbox_notes(BASE, trial)
        self.assertEqual(len(notes), 2, notes)
        self.assertIn("replace_unit", notes[0])
        self.assertIn("feeds.FEED.kg_h", notes[1])


if __name__ == "__main__":
    unittest.main()
