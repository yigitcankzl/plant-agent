import unittest

from plantagent.plant import calibration_check
from plantagent.prefeed import _gate, hazard_screen


def chk(util, source="DWSIM", check="x"):
    return {"id": "U1", "check": check, "value": 1.0, "limit": 1.0, "unit": "-", "utilisation": util, "source": source}


class Gates(unittest.TestCase):
    def test_firm_overload_fails_and_illustrative_overload_stays_open(self):
        self.assertEqual(_gate("electrical", [chk(1.3)], "pandapower", "s")["status"], "fail")
        g = _gate("heat_transfer", [chk(0.8), chk(3.9, "pump rating (ILLUSTRATIVE)")], "ht", "s")
        self.assertEqual(g["status"], "open")
        self.assertIn("ILLUSTRATIVE", g["summary"])
        self.assertEqual(_gate("process", [chk(0.9)], "DWSIM", "s")["status"], "pass")

    def test_no_check_or_open_reason_is_never_green(self):
        self.assertEqual(_gate("mechanical", [], "src", "s")["status"], "open")
        self.assertEqual(_gate("mechanical", [chk(0.5)], "src", "s", open_reason="vendor curve")["status"], "open")
        self.assertEqual(_gate("heat_transfer", [chk(1.5, check="model U 600 vs correlation U 300")], "ht", "s")["status"], "open")

    def test_calibration_inputs_are_not_reproduced_outputs(self):
        spec = {"feeds": {"F": {"kg_h": 1000.0, "T_C": 20.0}}, "units": [], "limits": {"S2": {"max_T_C": 61.0}}}
        result = {"streams": {"F": {"kg_h": 1000.0, "T_C": 20.0}, "S2": {"T_C": 60.5}}}
        rows = [{"item": "feed", "measured": "1.0 t/h", "simulated": "1.000 t/h - stream F"},
                {"item": "outlet T", "measured": "60 C", "simulated": "60.5 C - stream S2"},
                {"item": "invented", "measured": "70 C", "simulated": "71.3 C - stream S2"}]
        r = calibration_check(spec, result, rows)
        self.assertEqual([x["check"] for x in r["rows"]], ["input", "reproduced", "not_in_solve"])

    def test_hazop_skips_routing_nodes_and_names_folded_heater(self):
        spec = {"units": [{"id": "V-201", "type": "evaporator"}, {"id": "SPLIT", "type": "splitter"}]}
        changes = [{"path": "units.V-201.U_W_m2K", "value": 2500}, {"reroute": {"unit": "SPLIT", "field": "out", "value": "x"}}]
        rows = hazard_screen(spec, changes, [], {"E-201": "V-201"})["rows"]
        self.assertEqual({r["tag"] for r in rows}, {"E-201"})
        relief_rows = [r for r in rows if r["deviation"] != "Tube rupture"]
        self.assertTrue(all("relief" not in r["existing_safeguard"] for r in relief_rows))


if __name__ == "__main__":
    unittest.main()
