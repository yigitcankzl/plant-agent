import unittest

from plantagent.plant import calibration_check
from plantagent.prefeed import _fmt, _gate, hazard_screen


def chk(util, source="DWSIM", check="x"):
    return {"id": "U1", "check": check, "value": 1.0, "limit": 1.0, "unit": "-", "utilisation": util, "source": source}


class Gates(unittest.TestCase):
    def test_firm_overload_fails_and_illustrative_overload_stays_open(self):
        self.assertEqual(_gate("electrical", [chk(1.3)], "pandapower", "s")["status"], "fail")
        g = _gate("heat_transfer", [chk(0.8), chk(3.9, "pump rating (ILLUSTRATIVE)")], "ht", "s")
        self.assertEqual(g["status"], "open")
        self.assertIn("1 check over illustrative ratings", g["summary"])
        self.assertEqual([c["status"] for c in g["checks"]], ["ok", "over (illustrative rating)"])
        self.assertEqual(_gate("process", [chk(0.9)], "DWSIM", "s")["status"], "pass")

    def test_minimum_and_temperature_checks_read_as_margins(self):
        rows = _gate("heat_transfer", [
            {"id": "E", "check": "tube velocity vs minimum", "value": 2.83, "limit": 1.5, "unit": "m/s", "utilisation": 0.53, "source": "x"},
            {"id": "H", "check": "gas temperature vs design inlet", "value": 534.0, "limit": 485.0, "unit": "C", "utilisation": 1.1, "source": "x"},
            {"id": "E", "check": "model U 2,500 vs correlation U 3,297 W/m²K", "value": 24.2, "limit": 20.0, "unit": "% difference",
             "utilisation": 1.21, "source": "x", "kind": "note"}], "ht", "s")["checks"]
        self.assertEqual([r["kind"] for r in rows], ["min", "max", "max"])
        self.assertEqual(rows[0]["result"], "1.33 m/s above the minimum")
        self.assertEqual(rows[1]["result"], "49 K over the limit")
        self.assertEqual((rows[2]["status"], rows[2]["result"]), ("note", "24 % apart (flagged above 20 %)"))

    def test_numbers_have_separators_not_exponents(self):
        self.assertEqual([_fmt(x) for x in (7130.4, 226800, 0.3642, 156000.0, 12)], ["7,130", "226,800", "0.3642", "156,000", "12"])

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

    def test_calibration_compares_only_the_named_stream_field(self):
        # measured 60 C; the named stream is at 70 C; an unrelated unit has 60 (% efficiency) - must not count
        result = {"streams": {"S2": {"T_C": 70.0}}, "units": {"P1": {"eff_pct": 60.0}}}
        rows = [{"item": "outlet T", "measured": "60 C", "simulated": "60 C - stream S2"},
                {"item": "outlet T", "measured": "60 C", "simulated": "70 C - stream S2"},
                {"item": "no ref", "measured": "60 C", "simulated": "60 C"}]
        r = calibration_check({"feeds": {}, "units": []}, result, rows)
        self.assertEqual([x["check"] for x in r["rows"]], ["not_in_solve", "differs", "no_reference"])
        self.assertEqual(r["rows"][1]["reference"], "S2.T_C")
        self.assertEqual(r["counts"]["reproduced"], 0)

    def test_gates_key_changes_with_model_and_changes(self):
        from types import SimpleNamespace
        from plantagent.prefeed import gates_key
        w = SimpleNamespace(name="no_such_case", spec={"units": [{"id": "P1", "kW": 5}]}, revisions=[])
        ans = {"headline": "h", "proposals": [{"verified": True, "title": "t", "changes": [{"path": "units.P1.kW", "value": 7}]}]}
        k1 = gates_key(w, ans)
        w.spec["units"][0]["kW"] = 6  # model changed, same answer
        k2 = gates_key(w, ans)
        ans["proposals"][0]["changes"][0]["value"] = 8  # proposal content changed, same title
        k3 = gates_key(w, ans)
        self.assertEqual(k1["titles"], k2["titles"])
        self.assertEqual(len({k1["content"], k2["content"], k3["content"]}), 3)

    def test_hazop_skips_routing_nodes_and_names_folded_heater(self):
        spec = {"units": [{"id": "V-201", "type": "evaporator"}, {"id": "SPLIT", "type": "splitter"}]}
        changes = [{"path": "units.V-201.U_W_m2K", "value": 2500}, {"reroute": {"unit": "SPLIT", "field": "out", "value": "x"}}]
        rows = hazard_screen(spec, changes, [], {"E-201": "V-201"})["rows"]
        self.assertEqual({r["tag"] for r in rows}, {"E-201"})
        relief_rows = [r for r in rows if r["deviation"] != "Tube rupture"]
        self.assertTrue(all("relief" not in r["existing_safeguard"] for r in relief_rows))


if __name__ == "__main__":
    unittest.main()
