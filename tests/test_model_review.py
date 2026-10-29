import json
import tempfile
import unittest
from pathlib import Path

from plantagent import process
from plantagent.plant import (ENERGY_TOL, ENTHALPY_FIELD, RULES, PlantWorkspace, collect_gaps, record_gap,
                              review_model)


def salt_pattern():
    """The salt-MVR failure, shrunk: line 3003 is both a free steam feed into a heater and the hot side of a second heater,
    and the desuperheater is a cooler plus a mixer."""
    pid = {
        "equipment": [
            {"tag": "K-201", "class": "CentrifugalCompressor", "design": {}},
            {"tag": "D-201", "class": "Desuperheater", "design": {}},
            {"tag": "E-201", "class": "TubularHeatExchanger", "design": {"DesignHeatTransferArea": "6500 MetreSquared"}},
            {"tag": "E-102", "class": "PlateHeatExchanger", "design": {}},
            {"tag": "V-201", "class": "Vessel", "design": {}},
            {"tag": "P-201", "class": "CentrifugalPump", "design": {"DesignVolumeFlowRate": "12000 MetreCubedPerHour"}},
        ],
        "connections": [
            {"from": "E-102(PlateHeatExchanger)", "to": "V-201(Vessel)", "lines": ["1004"], "inline": []},
            {"from": "V-201(Vessel)", "to": "P-201(CentrifugalPump)", "lines": ["2001"], "inline": []},
            {"from": "K-201(CentrifugalCompressor)", "to": "D-201(Desuperheater)", "lines": ["3002"], "inline": []},
            {"from": "D-201(Desuperheater)", "to": "E-201(TubularHeatExchanger)", "lines": ["3003"], "inline": []},
        ],
    }
    spec = {
        "compounds": ["Water"], "package": "Steam Tables (IAPWS-IF97)",
        "feeds": {
            "S1004mix": {"T_C": 80, "P_bar": 2.4, "kg_h": 2000, "x": {"Water": 1}},
            "S3003FEED": {"T_C": 135, "P_bar": 3.08, "kg_h": 400, "x": {"Water": 1}},
            "VAP": {"T_C": 115, "P_bar": 1.7, "kg_h": 350, "x": {"Water": 1}},
            "TEXH": {"T_C": 200, "P_bar": 3.08, "kg_h": 20, "x": {"Water": 1}},
            "BRINE": {"T_C": 40, "P_bar": 3, "kg_h": 2000, "x": {"Water": 1}},
        },
        "units": [
            {"id": "K-201", "type": "compressor", "in": "VAP", "out": "S3002raw", "P_out_bar": 3.08, "eff_pct": 75},
            {"id": "D-201MIX", "type": "mixer", "in": ["S3002raw", "TEXH"], "out": "S3002m"},
            {"id": "D-201", "type": "cooler", "in": "S3002m", "out": "S3003", "T_out_C": 135},
            {"id": "E-201", "type": "hx", "hot": ["S3003", "COND"], "cold": ["BRINE", "BRINEO"],
             "U_W_m2K": 1500, "area_m2": 10, "hot_out_T_C": 134},
            {"id": "V-201", "type": "heater", "in": "S3003FEED", "out": "S4001", "duty_kW": 80},
        ],
    }
    basis = "E-201 circulating heater: 8,800 m².\nP-201 forced-circulation pump: 15,000 m³/h rated.\n"
    return spec, pid, basis


def _checks(review):
    return {f["check"] for f in review["findings"]}


class ModelReviewTests(unittest.TestCase):
    def test_rules_and_gap_tool(self):
        self.assertIn("call report_gap instead of approximating or changing a documented limit", RULES)
        names = [t["function"]["name"] for t in PlantWorkspace.tools(None)]
        self.assertIn("report_gap", names)

    def test_double_heater_free_feed_and_source_conflict(self):
        spec, pid, basis = salt_pattern()
        review = review_model(spec, {"errors": [], "streams": {}, "units": {}, "checks": []}, pid, basis)
        checks = _checks(review)
        self.assertEqual(review["status"], "model needs review")
        self.assertIn("internal source as a free feed", checks)
        self.assertIn("duty modelled twice", checks)
        self.assertIn("equipment represented twice", checks)
        self.assertIn("desuperheater modelled as heat removal", checks)
        self.assertIn("source conflict", checks)
        free = next(f for f in review["findings"] if f["check"] == "internal source as a free feed")
        self.assertIn("S3003FEED", free["evidence"])
        self.assertNotIn("S1004mix", free["evidence"])
        self.assertTrue(any("E-201" in f["evidence"] and "6500" in f["evidence"] and "8800" in f["evidence"]
                            for f in review["findings"] if f["check"] == "source conflict"))
        self.assertEqual(review["energy"]["proposed_field"], ENTHALPY_FIELD)
        self.assertEqual(review["energy"]["method"], "duty")
        self.assertEqual(review["energy"]["tolerance"], ENERGY_TOL)

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_double_heater_flagged_on_a_solved_sheet(self):
        spec, pid, basis = salt_pattern()
        result = process.run(spec)
        self.assertIn("units", result)
        review = review_model(spec, result, pid, basis)
        checks = _checks(review)
        self.assertIn("internal source as a free feed", checks)
        self.assertIn("duty modelled twice", checks)
        self.assertEqual(review["status"], "model needs review")

    def test_solve_quality_and_enthalpy_closure(self):
        spec = {"feeds": {"F": {}}, "units": [
            {"id": "H", "type": "heater", "in": "F", "out": "P"},
            {"id": "R", "type": "recycle", "in": "back", "out": "tear"}]}
        closed = {"errors": [], "checks": [], "units": {"H": {"type": "heater", "duty_kW": 50}},
                  "streams": {"F": {"kg_h": 3600, "enthalpy_kJ_kg": 100}, "P": {"kg_h": 3600, "enthalpy_kJ_kg": 150},
                              "back": {"T_C": 20, "P_bar": 1.2, "kg_h": 100}, "tear": {"T_C": 20, "P_bar": 1.2, "kg_h": 100}}}
        # the recycle streams are present, so drop the recycle unit for the closure-only sheet
        heater = {"feeds": spec["feeds"], "units": spec["units"][:1]}
        ok = review_model(heater, {**closed, "streams": {"F": closed["streams"]["F"], "P": closed["streams"]["P"]}}, None, "")
        self.assertEqual(ok["status"], "ok", ok)
        self.assertIsNone(ok["energy"]["proposed_field"])
        self.assertEqual(ok["energy"]["method"], "enthalpy")
        open_sheet = review_model(heater, {"errors": [], "checks": [], "units": {"H": {"type": "heater", "duty_kW": 0}},
                                           "streams": closed["streams"]}, None, "")
        self.assertIn("energy not closed", _checks(open_sheet))
        bad = review_model(spec, {"errors": ["K-201: did not solve"], "checks": [
            {"id": "V-301", "check": "boil-up", "utilisation": -0.379, "value": -4869, "unit": "kW"}],
            "units": {"H": {"type": "heater", "error": "did not solve (TypeError): check the unit's inlet streams and specs"}},
            "streams": {"back": {"T_C": 40, "P_bar": 1, "kg_h": 100}, "tear": {"T_C": 20, "P_bar": 1, "kg_h": 180}}}, None, "")
        checks = _checks(bad)
        self.assertIn("unit did not solve", checks)
        self.assertIn("negative utilisation", checks)
        self.assertIn("recycle not converged", checks)

    def test_report_gap_persists_and_aggregates(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = root / "alpha" / "gaps.json", root / "beta" / "gaps.json"
            self.assertEqual(record_gap(a, "", "why", "needed")["error"][:10], "report_gap")
            self.assertFalse(a.exists())
            self.assertTrue(record_gap(a, "add a compressor", "the spec has no insert", "a compressor unit the agent can add")["saved"])
            record_gap(b, "spray desuperheat", "only a cooler exists", "a mixer that adds condensate")
            rows = collect_gaps(root)
            self.assertEqual({(r["case"], r["what"]) for r in rows},
                             {("alpha", "add a compressor"), ("beta", "spray desuperheat")})
            self.assertEqual(json.loads(a.read_text())[0]["needed"], "a compressor unit the agent can add")


if __name__ == "__main__":
    unittest.main()
