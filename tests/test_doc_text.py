import unittest

from plantagent import documents, forecast
from plantagent.plant import describe_change, model_only_change

SPEC = {"feeds": {}, "units": [{"id": "V-201", "type": "evaporator", "in": "S1", "out": "S2"},
                               {"id": "MIX", "type": "mixer", "in": ["A", "B"], "out": "S3"},
                               {"id": "SPL", "type": "splitter", "in": "S3", "out": ["S4", "S5"], "fractions": [0.0843762616067824, 0.9156237383932176]}]}


class ChangeText(unittest.TestCase):
    def test_fractions_are_percent_and_lists_are_joined(self):
        t = describe_change(SPEC, {"path": "units.SPL.fractions", "from": SPEC["units"][2]["fractions"], "value": [0.070317, 0.929683]})
        self.assertIn("8.4 % / 91.6 % → 7.0 % / 93.0 %", t)
        self.assertNotIn("0.0843", t)
        t = describe_change(SPEC, {"reroute": {"unit": "MIX", "field": "in", "value": ["C", "B"]}, "from": ["A", "B"]})
        self.assertNotIn("[", t)

    def test_heater_field_is_named_by_its_pid_tag(self):
        t = describe_change(SPEC, {"path": "units.V-201.U_W_m2K", "from": 2000, "value": 2500}, aliases={"E-201": "V-201"})
        self.assertTrue(t.startswith("E-201"), t)
        self.assertIn("2,000 → 2,500", t)

    def test_routing_nodes_are_model_only(self):
        add = {"add_unit": {"id": "J", "type": "mixer", "in": ["x", "y"], "out": "z"}}
        self.assertTrue(model_only_change(SPEC, add))
        self.assertTrue(model_only_change(SPEC, {"reroute": {"unit": "MIX", "field": "in", "value": ["C"]}}))
        self.assertTrue(model_only_change(SPEC, {"reroute": {"unit": "J", "field": "in", "value": ["C"]}}, [add]))
        self.assertFalse(model_only_change(SPEC, {"reroute": {"unit": "V-201", "field": "in", "value": "S9"}}))


class DocumentText(unittest.TestCase):
    def test_model_keys_never_reach_a_document(self):
        self.assertEqual(documents._label("discharge_C"), "discharge temperature")
        self.assertEqual(documents._label("max_kg_h"), "rated mass flow (suction)")
        self.assertEqual(documents._klass("TubularHeatExchanger"), "Tubular heat exchanger")
        self.assertEqual(documents._n(48750.0), "48,750")
        self.assertEqual(documents._n(2020.68), "2,021")

    def test_forecast_headline_flags_an_illustrative_price(self):
        r = {"tag": "E-201", "simulator": "DWSIM", "status": "past the limit", "limit_date": "2026-10-23", "days_to_limit": -4.5,
             "now": {"lost_per_day": 185.8, "unit": "short t/d", "usd_per_day": 37163},
             "after": {"lost_per_day": 474.6, "unit": "short t/d", "date": "2026-11-04", "usd_per_day": 94916},
             "product_price": {"source": "ASSUMED, ILLUSTRATIVE"}}
        h = forecast.headline(r)
        self.assertIn("4.5 days ago", h)
        self.assertIn("illustrative price", h)


if __name__ == "__main__":
    unittest.main()
