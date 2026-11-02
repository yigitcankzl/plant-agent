import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent.plant import PlantWorkspace


class ProposedStateCacheTests(unittest.TestCase):
    def test_norco_featured_design_replays_without_solving_or_writing(self):
        from plantagent import web
        case = "shell_norco_c2splitter"
        with mock.patch("plantagent.process.available", return_value=False), \
                mock.patch("plantagent.process.run", side_effect=AssertionError("no solve on replay")), \
                mock.patch("plantagent.prefeed.discipline_gates", side_effect=AssertionError("no gates on load")), \
                mock.patch.object(Path, "write_text", side_effect=AssertionError("no writes on load")):
            w = PlantWorkspace(case)
            with mock.patch.dict(web.PLANTS, {case: w}):
                data = web.plant_project(case)
            state = w.proposed_state(1.25)
        self.assertTrue(state["replayed"])
        self.assertEqual(state["state_source"], "proposed design")
        self.assertAlmostEqual(state["checks"][0]["value"], .744, places=3)
        self.assertEqual(state["checks"][0]["id"], "PV-1767")
        self.assertTrue(any(g["id"] == "process" and g["status"] == "pass"
                            for a in data["answers"] for g in a.get("disciplines", [])))

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

    def test_precompute_proposed_keeps_checks_without_repeating_tray_profiles(self):
        with tempfile.TemporaryDirectory() as root:
            w = self.workspace(root)
            result = {"checks": [{"id": "P1", "utilisation": .8}], "streams": {},
                      "units": {"P1": {"kW": 8, "profile": [{"stage": 1}]}}}
            with mock.patch.object(w, "_solve", return_value=result), mock.patch.object(w, "_capacity_of", return_value={}):
                self.assertEqual(w.precompute_proposed(), 71)
            data = json.loads(w.model_file.with_name("proposed_states.json").read_text())
            self.assertEqual(data["states"][45]["scale"], 1.25)
            self.assertEqual(data["states"][45]["checks"], result["checks"])
            self.assertEqual(data["states"][45]["units"]["P1"], {"kW": 8})
            self.assertIn("profile", result["units"]["P1"])


if __name__ == "__main__":
    unittest.main()
