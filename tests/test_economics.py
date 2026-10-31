"""Economics of a design answer: factored capex per proposal, margin from the solved gain and energy, payback and NPV."""
import tempfile
import unittest
from pathlib import Path

from plantagent import economics


class FakeWorkspace:
    """Enough of PlantWorkspace for economics.assess: salt_mvr's case prices, a tiny model and a stub solver."""
    name = "salt_mvr"
    cfg = {"target_scale": 1.2, "throughput": {"name": "Salt production", "base": 2500, "unit": "short t/d"}}
    revisions = []

    def __init__(self, folder):
        self.model_file = Path(folder) / "model.json"
        self.spec = {"feeds": {"F": {"kg_h": 1000}}, "limits": {}, "units": [{"id": "K-201", "type": "compressor", "in": "F", "out": "S1"},
                                                                          {"id": "E-201", "type": "hx", "U_W_m2K": 2000}]}
        compressor = {"add_unit": {"id": "K-202", "type": "compressor", "in": "S0", "out": "S2"}, "limits": {"max_kW": 2400}, "rating_source": "provisional"}
        self.answers = [{"headline": "yes", "request": "+20 %", "combined": {"reaches_target": True, "capacity_multiple": 1.25},
                         "proposals": [{"title": "parallel compressor", "verified": True, "cost_class": "no capex",
                                        "changes": [{"add_unit": {"id": "TEE", "type": "splitter", "in": "F", "out": ["S0", "S9"]}}, compressor]},
                                       {"title": "clean", "verified": True, "cost_class": "<$100k",
                                        "changes": [{"path": "units.E-201.U_W_m2K", "from": 2000, "value": 2500}]}]}]

    def _solve(self, spec, scale=1.0):
        kw = {"K-201": 9000.0} if not any(u["id"] == "K-202" for u in spec["units"]) else {"K-201": 9000.0, "K-202": 2000.0}
        return {"units": {u: {"kW": v} for u, v in kw.items()}}


class TestEconomics(unittest.TestCase):
    def test_capex_margin_payback_npv(self):
        with tempfile.TemporaryDirectory() as d:
            w = FakeWorkspace(d)
            e = economics.assess(w)
            comp, clean = e["capex"]["proposals"]
            self.assertEqual(comp["capex_usd"], 2400 * 900 * 2.5 + 120000)  # driver rating, factor, install; one tie-in
            self.assertIn("outside the stated class", comp["cost_class_check"])  # Muse said no capex for a compressor
            self.assertEqual(clean["capex_usd"], 80000)
            a = e["annual"]
            self.assertEqual(a["sold_multiple"], 1.2)  # solved 125 % but only the 120 % target is sold
            energy = sum(x["usd_per_year"] for x in a["energy"])
            self.assertAlmostEqual(energy, round(2000 * 24 * 340 * 0.07, -2), delta=200)  # only K-202's added motor power
            self.assertAlmostEqual(a["margin_usd"], 500 * 340 * (200 - 60) - energy, delta=200)
            total = e["capex"]["total_usd"] + e["outage"]["usd"]
            self.assertAlmostEqual(e["payback_years"], total / a["margin_usd"], places=2)
            annuity = sum(1 / 1.1 ** t for t in range(1, 11))
            self.assertAlmostEqual(e["npv_usd"], -total + a["margin_usd"] * annuity, delta=1000)
            self.assertEqual(economics.assess(w)["made"], e["made"])  # second call is the cache
            self.assertIsNotNone(economics.cached(w, w.answers[0]))
            self.assertTrue(economics.for_prefeed(e)["capex_low"] < economics.for_prefeed(e)["capex_high"])


if __name__ == "__main__":
    unittest.main()
