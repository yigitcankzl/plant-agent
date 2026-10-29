import unittest

from plantagent import process


class HydraulicsTests(unittest.TestCase):
    def test_cv_and_characteristics_hand_calculation(self):
        # 100 US gpm water across 25 psi: Cv = 100 / sqrt(25) = 20.
        q = 100 * 0.0000630901964
        dp = 25 / 14.5037738
        eq = process._valve_sizing(q, 999.016, dp, 50, "equal_percentage", 50)
        linear = process._valve_sizing(q, 999.016, dp, 50, "linear", 50)
        self.assertAlmostEqual(eq["cv_required"], 20, places=5)
        self.assertAlmostEqual(eq["opening_pct"], 76.57757, places=4)
        self.assertAlmostEqual(linear["opening_pct"], 38.77551, places=4)
        self.assertGreater(process._valve_sizing(q * 2, 999.016, dp, 50)["opening_pct"], 90)

    def test_pipe_darcy_colebrook_hand_calculation(self):
        # 10 L/s, 100 m x 100 mm commercial-steel pipe, K=2, +5 m static lift.
        p = process._pipe_hydraulics(.01, 998, .001, 100, .1, .000045, 5, 2)
        self.assertAlmostEqual(p["velocity_m_s"], 1.27323954, places=6)
        self.assertAlmostEqual(p["Reynolds"], 127069.31, places=1)
        self.assertAlmostEqual(p["friction_factor"], .0195067, places=5)
        self.assertAlmostEqual(p["dP_bar"], .66332994, places=5)

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_valve_result_and_capacity_stop_at_travel(self):
        q = 100 * 0.0000630901964
        spec = {"compounds": ["Water"], "package": "NRTL",
                "feeds": {"F": {"T_C": 25, "P_bar": 5, "kg_h": q * 999.016 * 3600, "x": {"Water": 1}}},
                "units": [{"id": "V", "type": "valve", "in": "F", "out": "O", "dP_bar": 25 / 14.5037738,
                           "cv_rated": 50, "characteristic": "equal_percentage"}]}
        run = process.run(spec)
        self.assertFalse(run["errors"])
        self.assertAlmostEqual(run["units"]["V"]["cv_required"], 20, delta=.1)
        self.assertAlmostEqual(run["units"]["V"]["opening_pct"], 76.6, delta=.2)
        spec["units"][0].pop("cv_rated")
        spec["units"][0].update(kv_rated=50 / 1.156, characteristic="linear")
        linear = process.run(spec)
        self.assertFalse(linear["errors"])
        self.assertAlmostEqual(linear["units"]["V"]["opening_pct"], 38.8, delta=.2)
        spec["units"][0].pop("kv_rated")
        spec["units"][0]["cv_rated"] = 50
        spec["units"][0]["characteristic"] = "equal_percentage"
        cap = process.capacity(spec)
        self.assertFalse(cap["errors"])
        self.assertEqual(cap["limited_by"]["check"], "valve opening vs max travel")
        self.assertAlmostEqual(cap["capacity_multiple"], 1.69, delta=.04)

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_pipe_outlet_pressure_and_limits(self):
        spec = {"compounds": ["Water"], "package": "NRTL",
                "feeds": {"F": {"T_C": 25, "P_bar": 5, "kg_h": 35928, "x": {"Water": 1}}},
                "units": [{"id": "L", "type": "pipe", "in": "F", "out": "O", "length_m": 100,
                           "id_mm": 100, "roughness_mm": .045, "elevation_m": 5, "fittings_K": 2}],
                "limits": {"L": {"max_velocity_m_s": 3, "max_dP_bar": .7}}}
        run = process.run(spec)
        self.assertFalse(run["errors"])
        pipe = run["units"]["L"]
        self.assertAlmostEqual(pipe["velocity_m_s"], 1.273, delta=.01)
        self.assertAlmostEqual(pipe["dP_bar"], .6633, delta=.01)
        self.assertAlmostEqual(run["streams"]["F"]["P_bar"] - run["streams"]["O"]["P_bar"],
                               pipe["dP_bar"], delta=.002)
        self.assertEqual({c["check"] for c in run["checks"]}, {"velocity vs limit", "pressure drop vs available"})


if __name__ == "__main__":
    unittest.main()
