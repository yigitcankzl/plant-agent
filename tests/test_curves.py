import json
import unittest
from pathlib import Path

from plantagent import curves

SHAPE = [[0.6, 1.10, 0.86], [0.7, 1.10, 0.92], [0.8, 1.08, 0.97], [0.9, 1.05, 0.995], [1.0, 1.00, 1.00],
         [1.1, 0.92, 0.97], [1.18, 0.80, 0.88]]


def comp(q_d, vsd=False):
    return {"kind": "compressor", "design": {"q_m3_h": q_d, "pr": 1.8, "T_in_C": 115, "eff_pct": 75}, "points": SHAPE,
            "surge_q": 0.62, "stonewall_q": 1.18, "variable_speed": vsd, "max_speed_pct": 100}


class TestCurves(unittest.TestCase):
    def test_affinity_and_inverse(self):
        c = curves.Curve(comp(1000))
        self.assertAlmostEqual(c.head(1000), c.h_d, places=6)
        self.assertAlmostEqual(c.head(900, 0.9), 0.81 * c.h_d, places=6)  # Q ~ n, H ~ n^2
        self.assertAlmostEqual(c.flow_at_head(c.h_d), 1000, places=3)
        self.assertAlmostEqual(c.flow_at_head(0.81 * c.h_d, 0.9), 900, places=3)
        self.assertIsNone(c.flow_at_head(1.2 * c.h_d))  # above the peak: the machine cannot make the head
        n = c.speed_for(900, c.h_d)
        self.assertAlmostEqual(c.flow_at_head(c.h_d, n), 900, delta=0.5)
        self.assertEqual(c.eff_pct(10), c.eff_pct(600))  # flat outside the points, never extrapolated

    def test_parallel_sharing_and_surge_flag(self):
        """Fixed-speed K1 at its curve flow; the VSD K2 takes the rest. A small remainder puts K2 below surge."""
        spec = {"units": [{"id": "S", "type": "splitter", "in": "A", "out": ["A1", "A2"], "fractions": [0.5, 0.5]},
                          {"id": "K1", "type": "compressor", "in": "A1", "out": "B1", "P_out_bar": 3.24, "curve": comp(1000)},
                          {"id": "K2", "type": "compressor", "in": "A2", "out": "B2", "P_out_bar": 3.24, "curve": comp(400, True)}]}

        def res(total):
            s = lambda q: {"T_C": 115, "P_bar": 1.8, "kg_h": q, "m3_h": q}  # noqa: E731 - density 1
            return {"streams": {"A1": s(total / 2), "A2": s(total / 2), "B1": {"P_bar": 3.24}, "B2": {"P_bar": 3.24}}}
        rows = curves.checks(spec, res(1300))
        op = {r["id"]: r["operating_point"] for r in rows if "operating_point" in r}
        self.assertAlmostEqual(op["K1"]["q_m3_h"], 1000, delta=1)
        self.assertAlmostEqual(op["K2"]["q_m3_h"], 300, delta=1)
        cap = next(r for r in rows if r["id"] == "K1" and "capacity" in r["check"])
        self.assertAlmostEqual(cap["utilisation"], 1300 / 1400, places=3)
        self.assertTrue(all(r["utilisation"] <= 1 for r in rows if r["id"] == "K2" and "surge" in r["check"]))
        low = curves.checks(spec, res(1050))  # K2 left with 50 m3/h: far below its surge line
        self.assertTrue(any(r["id"] == "K2" and "surge" in r["check"] and r["utilisation"] > 1 for r in low))

    def test_salt_overlay_is_labelled(self):
        ov = json.loads((Path(curves.ROOT) / "cases/salt_mvr/curves.json").read_text())
        self.assertIn("ILLUSTRATIVE", ov["basis"])
        self.assertEqual(set(ov["units"]), {"K-201", "K-202"})
        spec = curves.apply({"units": [{"id": "K-201", "type": "compressor"}]}, ov)
        self.assertIn("curve", spec["units"][0])


if __name__ == "__main__":
    unittest.main()
