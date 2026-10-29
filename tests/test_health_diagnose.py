"""Morning check and troubleshooting: the arithmetic always; the DWSIM-backed parts when DWSIM is installed."""
import unittest

from plantagent import health, process


class Arithmetic(unittest.TestCase):
    def test_u_from_the_data_sheet_operating_point(self):
        c = {"hot_in": "a", "hot_out": "b", "cold_in": "c", "cold_out": "d", "cold_flow_m3h": "q", "area_m2": 46.8}
        u = health.exchanger_u([{"day": 0, "a": 50, "b": 35, "c": 25, "d": 37.7, "q": 20}], c)[0]["U"]
        self.assertTrue(550 < u < 650, u)

    def test_temperature_cross_gives_no_u(self):
        c = {"hot_in": "a", "hot_out": "b", "cold_in": "c", "cold_out": "d", "cold_flow_m3h": "q", "area_m2": 10}
        self.assertEqual(health.exchanger_u([{"day": 0, "a": 30, "b": 20, "c": 25, "d": 35, "q": 5}], c), [])

    def test_trend(self):
        s, i, r2 = health.trend([0, 1, 2, 3], [10, 8, 6, 4])
        self.assertAlmostEqual(s, -2)
        self.assertGreater(r2, 0.999)


@unittest.skipUnless(process.available(), "DWSIM not installed")
class WithDWSIM(unittest.TestCase):
    def test_recovers_the_imposed_fouling_drift(self):
        r = health.check("chem_c01")
        e = r["exchangers"][0]
        imposed = (585 - 640) / 30  # tools/make_synthetic_historian.py
        self.assertLess(abs(e["slope_per_day"] / imposed - 1), 0.15, e)
        self.assertEqual(r["today"][0]["unit"], "H1007")
        self.assertEqual(e["status_target"], "already over the limit")

    def test_diagnosis_tells_short_flow_from_fouling(self):
        from plantagent import diagnose
        r = diagnose.demo()
        self.assertIn("short of flow", r["ranked"][0]["name"])
        self.assertAlmostEqual(r["ranked"][0]["fitted"], 13.0, delta=0.5)
        self.assertTrue(any("fouled" in h["name"] and "contradicted" in h["verdict"] for h in r["ranked"]))


if __name__ == "__main__":
    unittest.main()
