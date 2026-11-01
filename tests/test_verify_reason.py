"""A proposal the simulator cannot re-solve carries the solver's error as its reason (no DWSIM needed)."""
import json
import unittest
from pathlib import Path

from plantagent import designchecks, loop
from plantagent.plant import PlantWorkspace

ROOT = Path(__file__).resolve().parents[1]
CASE = "basf_process_column_k_2750_dexpi_c02_uns"


def failing_workspace(spec):
    w = object.__new__(PlantWorkspace)
    w.name, w.cfg, w.built, w._state, w.answers, w.runs = CASE, {"target_scale": 1.2}, {"spec": spec}, {}, [], {}
    w.state = lambda scale: {"checks": [{"id": "K 2750", "check": "Fair flood fraction vs limit", "utilisation": 1.1}], "errors": []}
    w._solve = lambda s, scale: {"checks": [], "errors": ["K 2750: PR EOS: Unable to calculate compressility factor at given conditions."]}
    w._capacity_of = lambda s: {}
    return w


class VerifyReasonTest(unittest.TestCase):
    def test_failed_resolve_names_the_solver_error(self):
        spec = json.loads((ROOT / "runs" / "ws" / CASE / "model.json").read_text())["spec"]
        v = failing_workspace(spec).verify({"tag": "K 2750", "changes": [{"path": "units.K 2750.reflux_ratio", "value": 1.2}]})
        self.assertFalse(v["verified"])
        self.assertIn("compressility factor", v["unverified_reason"])
        self.assertIn("re-solve failed", loop._why(v))  # the reason reaches the worklog and Muse's fix prompt

    def test_setting_the_process_feed_rate_is_refused_with_why(self):
        spec = json.loads((ROOT / "runs" / "ws" / CASE / "model.json").read_text())["spec"]
        feed = next(iter(spec["feeds"]))
        v = failing_workspace(spec).verify({"changes": [{"path": f"feeds.{feed}.kg_h", "value": 1200}]})
        self.assertFalse(v["verified"])
        self.assertIn("scaled twice", v["unverified_reason"])

    def test_impurity_maximum_spec(self):
        self.assertTrue(designchecks._spec_ok({"component": "Ethane", "max_mass_frac": 0.001}, 0.0005))
        self.assertFalse(designchecks._spec_ok({"component": "Ethane", "max_mass_frac": 0.001}, 0.15))
        self.assertTrue(designchecks._spec_ok({"component": "Ethylene", "min_mass_frac": 0.999}, 0.9994))


if __name__ == "__main__":
    unittest.main()
