import unittest

from plantagent import prefeed
from plantagent.plant import PlantWorkspace


SPEC = {
    "feeds": {"F": {"kg_h": 100, "x": {"Water": 1}}},
    "units": [{"id": "K-1", "type": "compressor", "in": "F", "out": "P", "eff_pct": 75}],
    "limits": {"K-1": {"max_kg_h": 120}},
}


def patch(spec, changes):
    for change in changes:
        kind, uid, field = change["path"].split(".")
        if kind == "units":
            next(u for u in spec["units"] if u["id"] == uid)[field] = change["value"]
    return spec


def solve(spec, scale):
    flow = 100 * scale
    return {"errors": [], "streams": {
        "F": {"kg_h": flow, "components_kg_h": {"Water": flow}},
        "P": {"kg_h": flow, "components_kg_h": {"Water": flow}}},
        "units": {"K-1": {"type": "compressor", "kW": 10 * scale}},
        "checks": [{"id": "K-1", "check": "suction flow vs capacity", "value": flow, "limit": 120,
                    "unit": "kg/h", "utilisation": flow / 120}]}


class PrefeedTests(unittest.TestCase):
    def test_agent_has_one_prefeed_tool_for_the_complete_gate(self):
        workspace = object.__new__(PlantWorkspace)
        workspace.cfg = {}
        tools = {t["function"]["name"]: t["function"] for t in workspace.tools()}
        self.assertIn("prefeed_assessment", tools)
        text = tools["prefeed_assessment"]["description"]
        for word in ("operating-envelope", "equipment", "dynamics", "HAZOP", "constructability", "impact register",
                     "RFQ", "commissioning"):
            self.assertIn(word, text)

    def test_envelope_requires_every_scenario_and_closes_mass(self):
        result = prefeed.run_envelope(SPEC, [
            {"name": "normal", "scale": 1}, {"name": "target", "scale": 1.25}], solve, patch)
        self.assertFalse(result["robust_pass"])
        self.assertTrue(result["scenarios"][0]["pass"])
        self.assertFalse(result["scenarios"][1]["pass"])
        self.assertEqual(result["governing"]["scenario"], "target")
        self.assertEqual(result["scenarios"][0]["balance"]["mass_error_pct"], 0)
        self.assertEqual(result["scenarios"][0]["all_checks"][0]["id"], "K-1")
        self.assertIn("enthalpy", result["scenarios"][0]["balance"]["energy"])
        with self.assertRaisesRegex(ValueError, "documented limits"):
            prefeed.run_envelope(SPEC, [{"name": "cheat", "changes": [{"path": "limits.K-1.max_kg_h", "value": 999}]}],
                                    solve, patch)

    def test_scenario_that_loses_mass_is_not_robust(self):
        def leaky(spec, scale):
            r = solve(spec, scale)
            r["streams"]["P"] = {"kg_h": 50, "components_kg_h": {"Water": 50}}  # 100 in, 50 out
            return r
        result = prefeed.run_envelope(SPEC, [{"name": "normal", "scale": 1}], leaky, patch)
        self.assertEqual(result["scenarios"][0]["balance"]["mass_error_pct"], 50)
        self.assertFalse(result["scenarios"][0]["pass"])
        self.assertFalse(result["robust_pass"])
        self.assertIn("balance", result["scenarios"][0]["errors"][0])

    def test_dynamic_screen_needs_sourced_constants_and_catches_limit(self):
        self.assertEqual(prefeed.dynamic_screen([])["status"], "not run")
        result = prefeed.dynamic_screen([{"name": "pressure step", "variable": "P", "initial": 1, "final": 4,
                                          "time_constant_s": 5, "dead_time_s": 2, "duration_s": 30,
                                          "high_limit": 3.5, "unit": "bar", "source": "field step test 2026-10-01"}])
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["loops"][0]["pass"])
        with self.assertRaisesRegex(ValueError, "source"):
            prefeed.dynamic_screen([{"name": "x", "variable": "P", "initial": 1, "final": 2,
                                      "time_constant_s": 5, "duration_s": 20}])

    def test_new_equipment_stays_provisional_and_hazop_is_open(self):
        changes = [{"add_unit": {"id": "K-2", "type": "compressor", "in": "S", "out": "D"},
                    "limits": {"max_kg_h": 60000, "max_kW": 3000}, "rating_source": "vendor quote to confirm"},
                   {"reroute": {"unit": "K-1", "field": "out", "value": "J"}}]
        calculation = {"new_equipment": [{"id": "K-2", "type": "compressor",
                                            "operating_point": {"kg_h": 50000, "kW": 2500},
                                            "limits": {"max_kg_h": 60000, "max_kW": 3000},
                                            "rating_source": "vendor quote to confirm"}]}
        equipment = prefeed.equipment_screen(changes, [calculation])
        self.assertEqual(equipment[0]["status"], "provisional pass")
        self.assertEqual(equipment[0]["flow_margin"], 1.2)
        hazards = prefeed.hazard_screen({"units": SPEC["units"]}, changes, [])
        self.assertTrue(any(r["deviation"] == "High pressure" for r in hazards["rows"]))
        self.assertTrue(all(r["status"] == "open" for r in hazards["rows"]))
        gate = prefeed.constructability(changes, equipment, [">$1M"])
        self.assertTrue(gate["outage_required"])
        self.assertIn("electrical and controls", gate["unpriced"])
        with self.assertRaisesRegex(ValueError, "capex_low"):
            prefeed.constructability(changes, equipment, [">$1M"], {
                "capex_low": 2, "capex_high": 1, "outage_days": 1, "production_value_per_day": 1,
                "source": "estimate E-1"})
        priced = prefeed.constructability(changes, equipment, [">$1M"], {
            "capex_low": 100, "capex_high": 200, "outage_days": 2, "production_value_per_day": 10,
            "source": "estimate E-1"})
        self.assertEqual(priced["quantified"]["first_year_high"], 220)

    def test_change_lifecycle_stays_open_until_sourced_results_and_field_acceptance(self):
        changes = [{"path": "units.K-1.eff_pct", "from": 70, "value": 75},
                   {"add_unit": {"id": "K-2", "type": "compressor", "in": "S", "out": "D"},
                    "limits": {"max_kg_h": 120}, "rating_source": "budget quote Q-1"},
                   {"reroute": {"unit": "K-1", "field": "out", "value": "J"}}]
        env = prefeed.run_envelope(SPEC, [{"name": "target", "scale": 1}], solve, patch)
        equipment = [{"id": "K-2", "type": "compressor", "status": "provisional pass",
                      "operating_flow": 100, "flow_unit": "kg/h", "rating_flow": 120,
                      "calculated_shaft": 10, "shaft_unit": "kW", "rating_shaft": 15,
                      "rating_source": "budget quote Q-1", "vendor_gate": ["guaranteed curve"]}]
        hazards = {"rows": [{"tag": "K-2"}]}
        dynamics = {"status": "not run"}
        construction = {"physical_units": ["K-2"], "reroutes": 1}
        disciplines = prefeed.discipline_register(env, equipment, dynamics, hazards, construction,
                                                   [{"id": "electrical", "status": "pass", "summary": "MCC holds",
                                                     "source": "pandapower run E-1", "checks": [{"loading_pct": 82}]}])
        self.assertEqual(next(r for r in disciplines if r["id"] == "electrical")["status"], "pass")
        self.assertEqual(next(r for r in disciplines if r["id"] == "mechanical")["status"], "open")
        with self.assertRaisesRegex(ValueError, "needs id"):
            prefeed.discipline_register(env, equipment, dynamics, hazards, construction,
                                        [{"id": "electrical", "status": "pass"}])

        inputs = prefeed.decision_inputs(changes)
        self.assertTrue(any("K-2" in r["item"] for r in inputs))
        self.assertTrue(any("Tie-in" in r["item"] for r in inputs))
        self.assertIn("K-2", prefeed.rfq_markdown(equipment))

        plan = prefeed.commissioning_plan(changes, env, equipment)
        self.assertEqual(plan["status"], "open")
        test_id = plan["tests"][0]["id"]
        closed = prefeed.commissioning_plan(changes, env, equipment,
                                            [{"test_id": test_id, "value": 100, "source": "SAT sheet 1"}])
        self.assertEqual(closed["tests"][0]["status"], "pass")
        self.assertIn("SAT sheet 1", prefeed.commissioning_markdown(closed))
        with self.assertRaisesRegex(ValueError, "needs a source"):
            prefeed.commissioning_plan(changes, env, equipment, [{"test_id": test_id, "value": 100}])
        self.assertEqual(prefeed._direction({"check": "residence time", "value": 10, "limit": 10,
                                             "utilisation": 1}), "min")

        options = prefeed.option_comparison([{"title": "K-2", "verified": True, "reaches_target": False,
                                               "cost_class": ">$1M", "changes": changes}], env)
        self.assertEqual(options["options"][0]["role"], "partial change")
        self.assertIn("not ranked", options["pareto"])


if __name__ == "__main__":
    unittest.main()
