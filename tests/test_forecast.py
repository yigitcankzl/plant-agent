"""Fouling forecast on the saved salt_mvr historian: the fit is deterministic; the limit U comes from DWSIM."""
import unittest

from plantagent import charts, forecast, health, process

HIST = health.ROOT / "cases" / "salt_mvr" / "historian.csv"
TAG = "UI-201 E-201 inferred U (W/m2K)"


class Fit(unittest.TestCase):
    def test_fit_starts_after_the_boil_out(self):
        f = forecast.fit(forecast.daily_u(health.load(HIST), TAG), 0.15)
        self.assertEqual(f["from_day"], 35)  # the 4 Oct boil-out, not a line through the cleaning jump
        self.assertAlmostEqual(f["slope_per_day"], -30.4, delta=0.5)
        self.assertGreater(f["r2"], 0.99)
        self.assertGreater(f["slope_se"], 0)
        day = forecast.crossing(f, 1854.0)
        self.assertAlmostEqual(day, 54.5, delta=0.5)  # 23 Oct
        lo = forecast.crossing(f, 1854.0, f["slope_per_day"] - 1.96 * f["slope_se"])
        hi = forecast.crossing(f, 1854.0, f["slope_per_day"] + 1.96 * f["slope_se"])
        self.assertTrue(lo <= day <= hi)
        self.assertIsNone(forecast.crossing({**f, "slope_per_day": 5.0}, 1854.0))

    def test_headline_and_chart(self):
        r = {"tag": "E-201", "simulator": "DWSIM", "status": "within the limit", "days_to_limit": 8.0, "limit_date": "2026-10-23",
             "after_days": 7, "clean_by": "2026-10-20",
             "after": {"lost_per_day": 289.0, "unit": "short t/d", "usd_per_day": 57753, "date": "2026-10-30", "day": 61.4}}
        self.assertEqual(forecast.headline(r), "E-201 reaches its limit in 8 days (2026-10-23) → about 289 short t/d and $57,753/d lost "
                                               "7 days after that → clean by 2026-10-20; verified in DWSIM.")
        f = forecast.fit(forecast.daily_u(health.load(HIST), TAG), 0.15)
        svg = charts.fouling_svg("t", {**r, "points": [[d, u] for d, u in f["points"]], "points_start": "2026-08-30", "fit": f,
                                      "U_critical": 1854.0, "first_limit": {"id": "V-201"}, "limit_day": 54.5, "as_of_day": 46,
                                      "U_clean": 2500})
        self.assertTrue(svg.startswith("<svg") and "limit U 1854" in svg and "today" in svg)


@unittest.skipUnless(process.available(), "DWSIM unavailable")
class Forecast(unittest.TestCase):
    def test_salt_mvr(self):
        from plantagent.plant import PlantWorkspace
        w = PlantWorkspace("salt_mvr")
        r = forecast.forecast(w, "E-201", refresh=True)
        self.assertTrue(1700 < r["U_critical"] < 2000, r["U_critical"])  # bisection on the simulator, not a constant
        self.assertEqual(r["first_limit"]["id"], "V-201")
        self.assertEqual(r["status"], "past the limit")
        self.assertGreater(r["now"]["lost_per_day"], 0)
        self.assertGreater(r["after"]["lost_per_day"], r["now"]["lost_per_day"])
        self.assertIn("ASSUMED", r["product_price"]["source"])
        b = forecast.forecast(w, "E-201", as_of_day=46)  # 15 Oct: the limit was still ahead
        self.assertEqual(b["status"], "within the limit")
        self.assertLess(b["clean_by"], b["limit_date"])


if __name__ == "__main__":
    unittest.main()
