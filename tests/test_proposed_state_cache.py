import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent.plant import PlantWorkspace


class ProposedStateCacheTests(unittest.TestCase):
    def workspace(self, root):
        w = PlantWorkspace.__new__(PlantWorkspace)
        w.name = "cache_test"
        w.cfg = {}
        w.model_file = Path(root) / "model.json"
        w.built = {"spec": {"compounds": ["Water"], "package": "Steam Tables (IAPWS-IF97)",
                            "feeds": {"F": {"T_C": 20, "P_bar": 1, "kg_h": 100}},
                            "units": [{"id": "P1", "type": "pump", "in": "F", "out": "O", "dP_bar": 1, "eff_pct": 70}],
                            "limits": {"P1": {"max_kW": 10}}}}
        w.answers = [{"headline": "Higher-efficiency pump", "proposals": [{"verified": True,
                      "changes": [{"path": "units.P1.eff_pct", "value": 80}]}],
                      "combined": {"reaches_target": True}}]
        w._state = {}
        return w

    def test_replays_matching_proposed_design_without_dwsim(self):
        with tempfile.TemporaryDirectory() as root:
            w = self.workspace(root)
            cached = {"scale": 1.2, "errors": [], "checks": [{"id": "P1", "utilisation": .8}],
                      "units": {"P1": {"kW": 8}}, "streams": {}}
            w.model_file.with_name("proposed_states.json").write_text(json.dumps({
                "spec": w._proposed_spec(), "capacity": {}, "engine": "dwsim", "states": [cached]}))
            with mock.patch("plantagent.process.available", return_value=False):
                state = w.proposed_state(1.2)
            self.assertTrue(state["replayed"])
            self.assertEqual(state["state_source"], "proposed design")
            self.assertEqual(state["state_capacity"], {})
            self.assertEqual(state["units"]["P1"]["kW"], 8)

            w._state.clear()
            stored = json.loads(w.model_file.with_name("proposed_states.json").read_text())
            stored["spec"]["units"][0]["eff_pct"] = 79
            w.model_file.with_name("proposed_states.json").write_text(json.dumps(stored))
            with mock.patch("plantagent.process.available", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "no precomputed proposed-design solutions"):
                    w.proposed_state(1.2)


if __name__ == "__main__":
    unittest.main()
