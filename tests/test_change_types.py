import unittest

from plantagent.plant import change_errors, patch

SPEC = {"feeds": {"F": {"T_C": 20}}, "units": [
    {"id": "P1", "type": "pump", "in": "F", "out": "S1"},
    {"id": "V1", "type": "valve", "in": "S1", "out": "S2"},
    {"id": "T1", "type": "tank", "in": "S2", "out": "S3"}],
    "limits": {"S1": {"max_T_C": 40}, "S2": {"max_P_bar": 5}, "V1": {"max_dP_bar": 2}}}


class ChangeTypes(unittest.TestCase):
    def test_series_insert_is_add_unit_plus_reroute(self):
        s = patch(SPEC, [{"add_unit": {"id": "P2", "type": "pump", "in": "S1", "out": "S1b"}, "limits": {"max_kW": 3},
                          "rating_source": "standard size"},
                         {"reroute": {"unit": "V1", "field": "in", "value": "S1b"}}])
        u = {x["id"]: x for x in s["units"]}
        self.assertEqual(u["V1"]["in"], "S1b")
        self.assertEqual(s["limits"]["P2"], {"max_kW": 3})

    def test_bypass_keeps_stream_limits_and_connects_around(self):
        s = patch(SPEC, [{"bypass": {"unit": "V1"}, "physical_change": "spool piece"}])
        u = {x["id"]: x for x in s["units"]}
        self.assertNotIn("V1", u)
        self.assertEqual(u["P1"]["out"], "S2")  # the inlet stream now carries the outlet's name
        self.assertEqual(u["T1"]["in"], "S2")
        self.assertEqual(s["limits"]["S2"], {"max_P_bar": 5, "max_T_C": 40})
        self.assertNotIn("V1", s["limits"])

    def test_remove_needs_a_reason_when_proposed(self):
        self.assertTrue(change_errors(SPEC, [{"remove_unit": "T1"}]))
        self.assertFalse(change_errors(SPEC, [{"remove_unit": "T1", "physical_change": "tank demolished"}]))
        self.assertTrue(change_errors(SPEC, [{"remove_unit": "X9", "physical_change": "x"}]))

    def test_remove_drops_unit_and_its_limits(self):
        s = patch(SPEC, [{"remove_unit": "V1", "physical_change": "valve removed"},
                         {"reroute": {"unit": "T1", "field": "in", "value": "S1"}}])
        self.assertEqual([x["id"] for x in s["units"]], ["P1", "T1"])
        self.assertNotIn("V1", s["limits"])


if __name__ == "__main__":
    unittest.main()
