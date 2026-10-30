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
        for word in ("operating-envelope", "equipment", "dynamics", "HAZOP", "constructability"):
            self.assertIn(word, text)

    def test_envelope_requires_every_scenario_and_closes_mass(self):
        result = prefeed.run_envelope(SPEC, [
            {"name": "normal", "scale": 1}, {"name": "target", "scale": 1.25}], solve, patch)
        self.assertFalse(result["robust_pass"])
        self.assertTrue(result["scenarios"][0]["pass"])
        self.assertFalse(result["scenarios"][1]["pass"])
        self.assertEqual(result["governing"]["scenario"], "target")
        self.assertEqual(result["scenarios"][0]["balance"]["mass_error_pct"], 0)
        self.assertIn("enthalpy", result["scenarios"][0]["balance"]["energy"])
        with self.assertRaisesRegex(ValueError, "documented limits"):
            prefeed.run_envelope(SPEC, [{"name": "cheat", "changes": [{"path": "limits.K-1.max_kg_h", "value": 999}]}],
                                    solve, patch)

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


if __name__ == "__main__":
    unittest.main()
