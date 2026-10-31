"""Monte Carlo of a design: Latin-hypercube strata, percentiles, P(target) and a design that is over a limit at any throughput."""
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import prefeed, uncertainty


class FakeWorkspace:
    """Capacity = 1.2 x the sampled compressor capacity factor; below 0.95 of it the design is over a limit at any throughput."""
    name = "fake_mc"
    cfg = {"target_scale": 1.2, "engine": "fake"}  # not DWSIM: the serial path through _capacity_of/_solve
    revisions = []

    def __init__(self, folder):
        self.model_file = Path(folder) / "model.json"
        self.spec = {"feeds": {}, "units": [{"id": "K", "type": "compressor", "eff_pct": 75}], "limits": {"K": {"max_kg_h": 100.0}}}
        self.answers = [{"headline": "yes", "request": "+20 %", "combined": {"reaches_target": True, "capacity_multiple": 1.2},
                         "proposals": [{"title": "trim", "verified": True, "changes": [{"path": "units.K.eff_pct", "value": 76}]}]}]

    def _capacity_of(self, spec):
        f = spec["limits"]["K"]["max_kg_h"] / 100
        lim = {"id": "K", "check": "suction flow vs capacity"}
        return {"capacity_multiple": None, "limited_by": lim, "errors": []} if f < 0.95 else {"capacity_multiple": 1.2 * f, "limited_by": lim}

    def _solve(self, spec, scale=1.0):
        return {"checks": [{"id": "K", "check": "suction flow vs capacity", "utilisation": scale / (1.2 * spec["limits"]["K"]["max_kg_h"] / 100)}]}


class TestUncertainty(unittest.TestCase):
    def test_lhs_one_point_per_stratum(self):
        pts = uncertainty.lhs(20, 3, random.Random(0))
        for j in range(3):
            self.assertEqual(sorted(int(p[j] * 20) for p in pts), list(range(20)))
        self.assertEqual(uncertainty.pct([1, 2, 3, 4, 5], 0.5), 3)

    def test_monte_carlo_of_a_design(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "cases" / "fake_mc").mkdir(parents=True)
            (root / "cases" / "fake_mc" / "uncertainty.json").write_text(json.dumps({"n": 40, "inputs": [
                {"path": "limits.K.max_kg_h", "kind": "illustrative"}]}))
            with mock.patch.object(uncertainty, "ROOT", root), mock.patch.object(prefeed, "ROOT", root):
                w = FakeWorkspace(d)
                u = uncertainty.assess(w)
                self.assertEqual((u["n"], u["solved"], u["failed"]), (40, 40, 0))
                # ±15 % uniform: 1/3 of samples below 0.95 (infeasible), 1/2 at or above 1.0 (target met)
                self.assertAlmostEqual(u["infeasible_share"], 0.1 / 0.3, delta=0.06)
                self.assertAlmostEqual(u["p_target"], 0.5, delta=0.06)
                c = u["capacity"]
                self.assertTrue(1.2 * 0.95 <= c["p10"] < c["p50"] < c["p90"] <= 1.2 * 1.15)
                self.assertEqual(u["limiting"][0]["item"], "K: suction flow vs capacity")
                self.assertGreater(u["drivers"][0]["effect"], 0)  # more compressor capacity, more throughput
                self.assertIsNotNone(uncertainty.cached(w, w.answers[0]))
                self.assertIn("Monte Carlo", "\n".join(uncertainty.markdown(u)))


if __name__ == "__main__":
    unittest.main()
