import unittest
from plantagent.redteam import _parse, attack_surface, validate

SPEC = {"feeds": {"F": {"kg_h": 100.0, "T_C": 40.0, "P_bar": 3.0, "x": {"A": 0.6, "B": 0.4}}},
        "units": [{"id": "C1", "type": "distillation", "inlet": ["F"], "reflux_ratio": 2.0, "stages": 20, "efficiency": 0.7}],
        "limits": {"C1": {"flood_fraction": 0.8}}}


class RedTeam(unittest.TestCase):
    def test_surface_excludes_feed_rate_and_connections(self):
        s = attack_surface(SPEC)
        self.assertIn("feeds.F.T_C", s)
        self.assertIn("units.C1.reflux_ratio", s)
        self.assertNotIn("feeds.F.kg_h", s)
        self.assertNotIn("units.C1.inlet", s)
        self.assertNotIn("units.C1.stages", s)       # equipment, not an operating deviation
        self.assertIn("units.C1.efficiency", s)      # degradation is

    def test_bounds_and_unknown_paths_are_dropped(self):
        kept, dropped = validate(SPEC, [
            {"name": "hot feed", "scale": 1.0, "changes": [{"path": "feeds.F.T_C", "value": 50.0}]},
            {"name": "too hot", "scale": 1.0, "changes": [{"path": "feeds.F.T_C", "value": 80.0}]},
            {"name": "limit edit", "scale": 1.0, "changes": [{"path": "limits.C1.flood_fraction", "value": 0.9}]},
            {"name": "huge rate", "scale": 2.0, "changes": [{"path": "feeds.F.P_bar", "value": 3.1}]}])
        self.assertEqual([k["name"] for k in kept], ["hot feed"])
        self.assertEqual(len(dropped), 3)

    def test_parse_tolerates_prose(self):
        self.assertEqual(len(_parse('Here: {"scenarios": [{"name": "x"}]} done')), 1)
        self.assertEqual(_parse("no json"), [])


if __name__ == "__main__":
    unittest.main()
