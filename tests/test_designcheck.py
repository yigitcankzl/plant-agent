import unittest

from plantagent.designcheck import _leak_hits, score


class DesignCheckTests(unittest.TestCase):
    def test_score_kelvin_components_and_duties(self):
        metrics = [{"id": "t", "type": "T_K", "stream": "OUT", "expected": 300, "page": 1},
                   {"id": "p", "type": "P_bar", "stream": "OUT", "expected": 100, "page": 1},
                   {"id": "co2", "type": "component_kg_h", "stream": "OUT", "component": "Carbon dioxide",
                    "expected": 1000, "page": 1},
                   {"id": "power", "type": "compressor_kW", "expected": 100, "page": 1}]
        run = {"errors": [], "streams": {"OUT": {"T_C": 31.85, "P_bar": 106,
                                               "components_kg_h": {"Carbon dioxide": 980}}},
               "units": {"C1": {"type": "compressor", "kW": 60}, "C2": {"type": "compressor", "kW": 40}}}
        out = score(metrics, run)
        self.assertEqual(out["overall"], {"within_2pct": 0.75, "within_5pct": 0.75, "within_10pct": 1.0})
        self.assertEqual(score(metrics, None)["overall"]["within_10pct"], 0)
        self.assertEqual(score(metrics, {**run, "errors": ["failed"]})["overall"]["within_10pct"], 0)
        bad_pump = {**run, "units": {**run["units"], "P8": {"type": "pump", "kW": 0.01,
                                                             "dP_bar": 60, "m3_h": 0}}}
        self.assertIsNone(score(metrics, bad_pump)["metrics"][3]["actual"])

    def test_leak_check_looks_for_celsius_and_mpa_too(self):
        class Page:
            def visible_text(self):
                return "outlet 204 C at 2.8 MPa"
        metrics = [{"id": "t", "type": "T_K", "expected": 477.15},
                   {"id": "p", "type": "P_bar", "expected": 28.0}]
        self.assertEqual({x["metric"] for x in _leak_hits(Page(), metrics)}, {"t", "p"})


if __name__ == "__main__":
    unittest.main()
