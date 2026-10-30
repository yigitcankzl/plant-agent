"""Feed-concentration and heat-limited evaporator regression tests."""
import copy
import unittest
from types import SimpleNamespace
from unittest import mock

from plantagent import brine, process


def spec(feed_x=0.26, feed_t=125.6, feed_kg_h=100000, evap_frac=0.5):
    return {"compounds": ["Water"], "package": "Steam Tables (IAPWS-IF97)",
            "feeds": {"B": {"T_C": feed_t, "P_bar": 3, "kg_h": feed_kg_h, "x": {"Water": 1}}},
            "units": [{"id": "V", "type": "evaporator", "in": "B", "vapor": "VAP", "liquid": "L",
                       "P_bar": 1.7, "evap_frac": evap_frac, "feed_x_NaCl": feed_x}]}


class BrineCp(unittest.TestCase):
    def test_laliberte_cp(self):
        self.assertAlmostEqual(brine.cp(100, 0), 4.215, places=2)
        self.assertAlmostEqual(brine.cp(100, 0.26), 3.303, places=2)
        self.assertLess(brine.cp(100, 0.26), brine.cp(100, 0.20))
        with self.assertRaises(ValueError):
            brine.cp(100, 0.5)

    def test_bpe_rejects_extrapolation(self):
        for pressure, fraction in ((0, 0.2), (1.7, -0.01), (1.7, 0.33), (100, 0.2)):
            with self.subTest(pressure=pressure, fraction=fraction), self.assertRaises(ValueError):
                brine.bpe(pressure, fraction)


@unittest.skipUnless(process.available(), "DWSIM unavailable")
class Evaporator(unittest.TestCase):
    def test_recycle_guess_can_scale_with_capacity_case(self):
        sheet = process._Sheet.__new__(process._Sheet)
        sheet.scale, sheet.spec = 1.25, {"feeds": {"F": {"T_C": 20, "kg_h": 100}}}
        sheet._add = mock.Mock(return_value=SimpleNamespace(MaximumIterations=0))
        sheet.stream = mock.Mock(side_effect=lambda name: name)
        sheet._feed, sheet._link = mock.Mock(), mock.Mock()
        sheet._unit({"id": "R", "type": "recycle", "in": "back", "out": "tear",
                     "guess": {"kg_h": 1000}, "guess_scales": True})
        self.assertEqual(sheet._feed.call_args.args[-1], 1.25)

    def test_crystal_and_liquid_mass_balances(self):
        r = process.run(spec(feed_t=60))
        self.assertFalse(r["errors"])
        v = r["units"]["V"]
        self.assertTrue(v["crystallising"])
        self.assertAlmostEqual(v["salt_in_kg_h"], 26000, delta=1)
        self.assertAlmostEqual(v["salt_kg_h"] + v["liquid_out_brine_kg_h"] + v["vapour_kg_h"], 100000, delta=2)
        self.assertAlmostEqual(v["salt_kg_h"] + v["liquid_out_brine_kg_h"] * v["body_x_NaCl"], 26000, delta=5)
        self.assertLess(v["sensible_correction_kW"], 0)

    def test_unsaturated_body_does_not_crystallise(self):
        r = process.run(spec(feed_x=0.1, evap_frac=0.2))
        self.assertFalse(r["errors"])
        v = r["units"]["V"]
        self.assertFalse(v["crystallising"])
        self.assertEqual(v["salt_kg_h"], 0)
        self.assertAlmostEqual(v["body_x_NaCl"], 0.125, places=3)
        self.assertLess(v["bpe_K"], brine.bpe(1.7)["bpe_K"])

    def test_cannot_evaporate_more_than_feed_water(self):
        r = process.run(spec(evap_frac=0.9))
        self.assertIn("boil-up exceeds water", r["units"]["V"]["error"])
        self.assertIsNone(r["units"]["V"]["salt_kg_h"])

    def test_same_boilup_concentration_ratio(self):
        rich = spec(feed_x=0.26, feed_kg_h=247700 / 0.73, evap_frac=0.73)
        lean = spec(feed_x=0.20, feed_kg_h=247700 / 0.79, evap_frac=0.79)
        a, b = process.run(rich), process.run(lean)
        self.assertFalse(a["errors"] or b["errors"])
        av, bv = a["units"]["V"], b["units"]["V"]
        self.assertAlmostEqual(av["vapour_kg_h"], bv["vapour_kg_h"], delta=1)
        self.assertAlmostEqual(bv["salt_kg_h"] / av["salt_kg_h"], (0.2 / 0.8) / (0.26 / 0.74), delta=0.02)

    def test_cold_feed_reduces_heat_limited_boilup(self):
        s = spec(feed_kg_h=362900, evap_frac=0.68)
        s["units"][0].update(heating=["ST", "C"], U_W_m2K=2000, area_m2=8800)
        s["units"].extend([{"id": "SP", "type": "splitter", "in": "VAP", "out": ["SUC", "X"],
                            "fixed_kg_h": {"SUC": 226800}},
                           {"id": "K", "type": "compressor", "in": "SUC", "out": "ST", "P_out_bar": 3.08, "eff_pct": 78}])
        warm = process.run(s)
        cold_spec = copy.deepcopy(s)
        cold_spec["feeds"]["B"]["T_C"] = 120
        cold = process.run(cold_spec)
        self.assertFalse(warm["errors"] or cold["errors"])
        self.assertLess(cold["units"]["V"]["vapour_kg_h"], warm["units"]["V"]["vapour_kg_h"])
        self.assertAlmostEqual(cold["units"]["V"]["boil_kW"], cold["units"]["V"]["heating_kW"], delta=1)

    def test_bpe_energy_correction_includes_vapour_superheat(self):
        result = process.run(spec(feed_t=60))
        self.assertFalse(result["errors"])
        unit = result["units"]["V"]
        expected = unit["vapour_kg_h"] / 3600 * 2.08 * unit["bpe_K"]
        self.assertAlmostEqual(unit["vapor_superheat_kW"], expected, delta=0.2)
        self.assertAlmostEqual(unit["sensible_correction_kW"],
                               unit["brine_sensible_kW"] - unit["water_sensible_kW"] +
                               unit["vapor_superheat_kW"], delta=0.2)

    def test_closed_circulation_uses_net_streams_for_balance(self):
        s = spec(feed_t=60, feed_kg_h=100000, evap_frac=50000 / 1000000)
        s["feeds"]["BF"] = {"T_C": 60, "P_bar": 3, "kg_h": 1000000, "x": {"Water": 1}}
        s["units"] = [
            {**s["units"][0], "in": "BF", "liquid": "LT", "net_feed": "B", "net_liquid": "L"},
            {"id": "S", "type": "splitter", "in": "LT", "out": ["L", "RS"],
             "fixed_kg_h": {"L": 50000}},
        ]
        result = process.run(s)
        self.assertFalse(result["errors"], result)
        unit = result["units"]["V"]
        self.assertAlmostEqual(unit["salt_in_kg_h"], 26000, delta=2)
        self.assertAlmostEqual(unit["vapour_kg_h"], 50000, delta=2)
        self.assertAlmostEqual(unit["salt_kg_h"] + unit["liquid_out_brine_kg_h"] + unit["vapour_kg_h"],
                               100000, delta=3)

    def test_heat_balance_tolerance_is_explicit_model_closure_not_a_rating(self):
        s = spec(feed_kg_h=362900, evap_frac=0.68)
        s["units"][0].update(heating=["ST", "C"], U_W_m2K=2000, area_m2=8800,
                             heat_balance_tolerance_pct=10)
        s["units"].extend([{"id": "SP", "type": "splitter", "in": "VAP", "out": ["SUC", "X"],
                            "fixed_kg_h": {"SUC": 226800}},
                           {"id": "K", "type": "compressor", "in": "SUC", "out": "ST",
                            "P_out_bar": 3.08, "eff_pct": 78}])
        result = process.run(s)
        check = next(c for c in result["checks"] if "closure tolerance" in c["check"])
        self.assertIn("10 %", check["check"])
        self.assertAlmostEqual(check["limit"], result["units"]["V"]["heating_kW"] * 1.10, delta=0.2)


if __name__ == "__main__":
    unittest.main()
