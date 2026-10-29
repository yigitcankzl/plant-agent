"""WaterTAP reverse osmosis: the packaged seawater example, a flux-limited capacity, and ASTM D4516."""
import unittest

from plantagent import ro
from plantagent.plant import PlantWorkspace


def _watertap():
    if not ro.available():
        raise unittest.SkipTest("WaterTAP venv is not installed (.venv-watertap)")


class RoTests(unittest.TestCase):
    def test_example_matches_watertap(self):
        _watertap()
        ex = ro.example()
        self.assertLess(abs(ex["recovery"] - 0.420696) / 0.420696, 1e-3, ex)
        self.assertLess(abs(ex["feed_pressure_bar"] - 70.0), 0.05, ex)
        self.assertLess(abs(ex["permeate_TDS_g_L"] - 0.2126), 0.002, ex)
        self.assertLess(abs(ex["sec_kWh_m3"] - 3.3917) / 3.3917, 0.01, ex)
        self.assertEqual(ex["boron"], "not modelled")
        self.assertGreater(ex["hp_kW"], 1000)
        self.assertGreater(ex["booster_kW"], 0)

    def test_capacity_hits_flux_limit(self):
        _watertap()
        spec = {
            "feed": {"flow_m3_h": 80, "TDS_g_L": 35, "T_C": 25, "P_bar": 1},
            "hp_pump": {"efficiency": 0.8, "max_bar": 150, "max_kW": 5000},
            "stages": [{
                "id": "RO-1", "area_m2": 800, "elements_per_vessel": 7, "vessels": 6,
                "membrane": "watertap_seawater", "recovery": 0.40,
                "max_feed_pressure_bar": 150, "min_concentrate_m3_h_per_vessel": 0.1,
            }],
            "target_TDS_g_L": 50,
        }
        base = ro.run(spec)
        self.assertFalse(base.get("errors"), base)
        lead = base["flux_lmh_lead"]
        self.assertGreater(lead, 1)
        spec["stages"][0]["max_flux_lmh"] = round(lead * 1.2, 4)
        cap = ro.capacity(spec)
        self.assertFalse(cap.get("errors"), cap)
        self.assertGreater(cap["capacity_multiple"], 1.05)
        self.assertLess(cap["capacity_multiple"], 2.0)
        self.assertIn("flux", cap["limited_by"]["check"])
        self.assertGreater(cap["limited_by"]["utilisation"], 0.95)
        self.assertLessEqual(cap["limited_by"]["utilisation"], 1.0)

    def test_normalize_hand_example(self):
        # Hand values: TCF_a = exp(3020*(1/298.15 - 1/293.15)) = 0.8413364867, TCF_s = 1,
        # NDP_a = 40 - 1 - 1 - 20 + 0.5 = 18.5, NDP_s = 50 - 1 - 1 - 22 + 0.4 = 26.4,
        # Q_n = 80 * (26.4/18.5) / 0.8413364867 = 135.6914432840,
        # SP_n = 1.5 * (18.5/26.4) * (45/55) * 0.8413364867 = 0.7235667615,
        # dP_n = 2 * (100/120)**1.4 = 1.5494453080.
        actual = {"Q_permeate": 80, "T_C": 20, "P_feed": 40, "dP": 2, "P_permeate": 1,
                  "pi_fb": 20, "pi_permeate": 0.5, "salt_passage": 1.5, "C_fb": 55, "Q_fb": 120}
        standard = {"Q_permeate": 100, "T_C": 25, "P_feed": 50, "dP": 2, "P_permeate": 1,
                    "pi_fb": 22, "pi_permeate": 0.4, "salt_passage": 1.0, "C_fb": 45, "Q_fb": 100}
        n = ro.normalize(actual, standard)
        self.assertAlmostEqual(n["TCF_actual"], 0.8413364867, places=6)
        self.assertAlmostEqual(n["NDP_actual"], 18.5, places=6)
        self.assertAlmostEqual(n["NDP_standard"], 26.4, places=6)
        self.assertAlmostEqual(n["normalized_permeate_flow"], 135.6914432840, places=6)
        self.assertAlmostEqual(n["normalized_salt_passage"], 0.7235667615, places=6)
        self.assertAlmostEqual(n["normalized_differential_pressure"], 1.5494453080, places=6)

    def test_tools_only_for_watertap_cases(self):
        ws = PlantWorkspace.__new__(PlantWorkspace)
        ws.cfg = {}
        names = [t["function"]["name"] for t in ws.tools()]
        self.assertNotIn("run_ro", names)
        self.assertNotIn("ro_capacity", names)
        self.assertNotIn("ro_normalize", names)
        ws.cfg = {"engine": "watertap"}
        names = [t["function"]["name"] for t in ws.tools()]
        self.assertIn("run_ro", names)
        self.assertIn("ro_capacity", names)
        self.assertIn("ro_normalize", names)
        seen = {}

        def fake(spec):
            seen["spec"] = spec
            return {"capacity_multiple": 1.5}

        original = ro.capacity
        try:
            ro.capacity = fake
            self.assertEqual(ws._capacity_of({"feed": {"flow_m3_h": 1}})["capacity_multiple"], 1.5)
            self.assertEqual(seen["spec"]["feed"]["flow_m3_h"], 1)
        finally:
            ro.capacity = original
        self.assertIn("T_C", ws.call("ro_normalize", {"actual": {}, "standard": {}})["error"])
