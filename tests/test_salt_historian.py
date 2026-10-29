"""Synthetic salt MVR signals must be legible to the existing historian/health readers."""
import unittest
import json
from datetime import datetime, timedelta
from pathlib import Path
from statistics import fmean

from plantagent import health
from plantagent.plant import historian


CSV = Path(__file__).resolve().parent.parent / "cases" / "salt_mvr" / "historian.csv"


class SaltHistorianTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = health.load(CSV)

    def mean(self, tag, start, end):
        return fmean(r[tag] for r in self.rows if start <= r["day"] < end and r[tag] is not None)

    def test_hourly_and_boiling_out(self):
        self.assertEqual(len(self.rows), 1440)
        start = datetime.fromisoformat(self.rows[0]["time"])
        self.assertTrue(all(datetime.fromisoformat(r["time"]) == start + timedelta(hours=i)
                            for i, r in enumerate(self.rows)))
        self.assertTrue(all(r["FI-3001 K-201 suction (t/h)"] == 0 for r in self.rows[35 * 24:35 * 24 + 8]))
        self.assertLess(self.mean("UI-201 E-201 inferred U (W/m2K)", 32, 35),
                        self.mean("UI-201 E-201 inferred U (W/m2K)", 36, 39) - 500)

    def test_fouling_pressure_power_and_capacity(self):
        self.assertGreater(self.mean("PI-3002 K-201 discharge (bar a)", 20, 23),
                           self.mean("PI-3002 K-201 discharge (bar a)", 0, 3) + .12)
        self.assertGreater(self.mean("JI-201 K-201 shaft power (kW)", 20, 23),
                           self.mean("JI-201 K-201 shaft power (kW)", 0, 3) + 600)
        self.assertAlmostEqual(self.mean("FI-3001 K-201 suction (t/h)", 20, 23), 226.8, delta=2)
        self.assertLess(self.mean("FI-3000 V-201 total vapour (t/h)", 32, 35),
                        self.mean("FI-3000 V-201 total vapour (t/h)", 0, 3) - 20)
        self.assertLess(self.mean("FI-9001 dry salt production (t/h)", 32, 35),
                        self.mean("FI-9001 dry salt production (t/h)", 0, 3) - 8)
        self.assertGreater(self.mean("DI-201 E-201 brine rise (K)", 20, 23),
                           self.mean("DI-201 E-201 brine rise (K)", 0, 3) + .15)

    def test_purge_bpe_and_morning_check(self):
        self.assertLess(self.mean("FI-5001 V-201 purge (t/h)", 20, 23), 40)
        self.assertGreater(self.mean("TI-201 V-201 body (C)", 29, 32),
                           self.mean("TI-201 V-201 body (C)", 0, 3) + .4)
        result = health.check("salt_mvr")  # read-only; no model or runs/ output needed
        e = result["exchangers"][0]
        self.assertEqual(e["trend_from_day"], 35)
        self.assertLess(e["slope_per_day"], -20)
        self.assertGreater(e["r2"], .9)
        self.assertEqual(result["today"][0]["kind"], "fouling")

    def test_generic_historian_is_wired_to_case(self):
        cfg = json.loads(CSV.with_name("case.json").read_text())
        self.assertEqual(cfg["historian"], CSV.name)
        summary = historian(CSV, tags=["FI-3001 K-201 suction (t/h)"])
        self.assertEqual(summary["tags"]["FI-3001 K-201 suction (t/h)"]["n"], 1440)


if __name__ == "__main__":
    unittest.main()
