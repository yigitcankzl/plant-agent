import json
import unittest
from pathlib import Path

from plantagent import pid
from plantagent.plant import coverage


ROOT = Path(__file__).resolve().parents[1]


class CoverageTopologyTests(unittest.TestCase):
    def test_follows_phase_ports_and_inline_model_units(self):
        drawing = {
            "equipment": [{"tag": "V-1"}, {"tag": "E-1"}],
            "connections": [
                {"from": "V-1(Vessel)", "to": "E-1(HeatExchanger)", "lines": ["10"], "inline": ["FV-1(GlobeValve)"]},
                {"from": "V-1(Vessel)", "to": "open-out:vent(OpenEnd)", "lines": ["70"],
                 "inline": ["PSV-1(SpringLoadedGlobeSafetyValve)"]},
            ],
            "lines": [{"line": "10", "fluid_code": "PROCESS"}, {"line": "70", "fluid_code": "PROCESS"}],
        }
        spec = {"feeds": {}, "units": [
            {"id": "V-1", "type": "flash", "vapor": "S1", "liquid": "L1"},
            {"id": "FV-1", "type": "valve", "in": "S1", "out": "S2"},
            {"id": "E-1", "type": "cooler", "in": "S2", "out": "S3"},
        ], "limits": {}}
        result = coverage(drawing, spec)
        self.assertEqual(result["capacity_relevant_simulated"], 1)
        self.assertEqual(result["capacity_relevant_total"], 1)
        self.assertEqual(result["capacity_relevant"][0]["match"], "equipment topology")
        self.assertEqual(len(result["auxiliary_not_modelled"]), 1)

    def test_salt_reports_process_and_auxiliary_lines_separately(self):
        case = ROOT / "cases" / "salt_mvr"
        drawing = pid.overview(case / "pid.xml")
        spec = json.loads((ROOT / "runs" / "ws" / "salt_mvr" / "model.json").read_text())["spec"]
        result = coverage(drawing, spec, {"E-201": "V-201", "E-301": "V-301"})
        self.assertEqual((result["capacity_relevant_simulated"], result["capacity_relevant_total"]), (12, 17))
        self.assertEqual((len(result["auxiliary_not_modelled"]), result["auxiliary_total"]), (8, 8))
        self.assertEqual({line for row in result["missing_capacity_relevant"] for line in row["lines"]},
                         {"1001", "1002", "1003", "1004", "3201"})
        self.assertTrue(any(row["match"] == "intentional recycle tear" for row in result["capacity_relevant"]))
        self.assertTrue(any(row["match"] == "grouped inside one model unit" for row in result["capacity_relevant"]))


if __name__ == "__main__":
    unittest.main()
