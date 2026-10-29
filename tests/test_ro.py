"""WaterTAP reverse osmosis: solver checks, build-path routing, coverage and review."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import process, ro
from plantagent.plant import (BUILD_DWSIM, BUILD_WATERTAP, PlantWorkspace, review_model, review_ro,
                              ro_coverage)


def _watertap():
    if not ro.available():
        raise unittest.SkipTest("WaterTAP venv is not installed (.venv-watertap)")


def _tiny_spec(**extra):
    spec = {
        "feed": {"flow_m3_h": 100, "TDS_g_L": 35, "T_C": 25, "P_bar": 1},
        "pretreatment": [
            {"id": "MF-1", "type": "media_filter", "dP_bar": 0.2, "recovery": 0.98},
            {"id": "CHEM-1", "type": "chemical", "notes": "antiscalant; not simulated"},
        ],
        "hp_pump": {"efficiency": 0.8, "P_out_bar": 70, "max_bar": 150, "max_kW": 5000},
        "stages": [{
            "id": "RO-1", "area_m2": 1000, "elements_per_vessel": 7, "vessels": 8,
            "membrane": "watertap_seawater", "recovery": 0.42,
            "max_feed_pressure_bar": 150, "min_concentrate_m3_h_per_vessel": 0.1,
        }],
        "energy_recovery": {"type": "PX", "efficiency": 0.95, "booster_pump": {"efficiency": 0.8, "max_kW": 500}},
        "posttreatment": {"notes": "CO2 + calcite; chemistry not simulated"},
        "target_TDS_g_L": 0.5,
    }
    spec.update(extra)
    return spec


def _ok_result(spec, **overrides):
    raw = float(spec["feed"]["flow_m3_h"])
    pret = raw * 0.98
    perm, brine = pret * 0.42, pret * 0.58
    result = {
        "scale": 1.0, "errors": [], "recovery": perm / raw, "sec_kWh_m3": 2.8,
        "permeate_TDS_g_L": 0.25, "boron": "not modelled",
        "pumps_kW": {"HP": 400.0, "booster": 50.0},
        "stages": [{"id": "RO-1", "feed_pressure_bar": 70.0, "recovery": 0.42,
                    "flux_lmh_avg": 15.0, "flux_lmh_lead": 18.0}],
        "streams": {
            "intake": {"flow_m3_h": raw, "P_bar": 1.0, "TDS_g_L": 35},
            "hp_suction": {"flow_m3_h": pret, "P_bar": 0.8, "TDS_g_L": 35},
            "hp_discharge": {"flow_m3_h": pret, "P_bar": 70.0, "TDS_g_L": 35},
            "permeate": {"flow_m3_h": perm, "P_bar": 1.0, "TDS_g_L": 0.25},
            "brine": {"flow_m3_h": brine, "P_bar": 1.0, "TDS_g_L": 60},
        },
        "checks": [
            {"id": "RO-1", "check": "feed pressure vs max", "value": 70, "limit": 150, "unit": "bar", "utilisation": 70 / 150},
            {"id": "permeate", "check": "permeate TDS vs target", "value": 0.25, "limit": 0.5, "unit": "g/L", "utilisation": 0.5},
        ],
        "not_modelled": ["boron (pass boron in the feed and B_boron_m_per_s on each stage to track it)",
                         "post-treatment reactions (stored as notes)"],
    }
    result.update(overrides)
    return result


def _ws(engine=None, title="Test plant"):
    ws = PlantWorkspace.__new__(PlantWorkspace)
    ws.cfg = {"title": title, **({"engine": engine} if engine else {})}
    ws.pid = {"equipment": [{"tag": "P-HP", "class": "Pump"}, {"tag": "RO-1", "class": "Membrane"},
                            {"tag": "PX-1", "class": "EnergyRecovery"}, {"tag": "MF-1", "class": "Filter"},
                            {"tag": "POST-1", "class": "Chemical"}],
              "connections": [{"from": "MF-1", "to": "P-HP", "lines": ["1"], "inline": []},
                              {"from": "P-HP", "to": "RO-1", "lines": ["2"], "inline": []},
                              {"from": "RO-1", "to": "PX-1", "lines": ["3"], "inline": []}]}
    ws.basis = "one train out of service; partial second pass"
    ws.runs = {}
    ws.built = None
    ws.gaps = []
    ws.name = "test_ro"
    ws.model = "test"
    ws._state = {}
    return ws


class RoTests(unittest.TestCase):
    def test_example_matches_watertap(self):
        _watertap()
        ex = ro.example()
        self.assertLess(abs(ex["recovery"] - 0.420696) / 0.420696, 1e-3, ex)
        self.assertLess(abs(ex["feed_pressure_bar"] - 70.0), 0.05, ex)
        self.assertLess(abs(ex["permeate_TDS_g_L"] - 0.2126), 0.002, ex)
        self.assertLess(abs(ex["sec_kWh_m3"] - 3.3917) / 3.3917, 0.01, ex)
        self.assertEqual(ex["boron"], "not modelled")
        self.assertGreater(ex["hp_kW"], 1000)
        self.assertGreater(ex["booster_kW"], 0)

    def test_capacity_hits_flux_limit(self):
        _watertap()
        spec = {
            "feed": {"flow_m3_h": 80, "TDS_g_L": 35, "T_C": 25, "P_bar": 1},
            "hp_pump": {"efficiency": 0.8, "max_bar": 150, "max_kW": 5000},
            "stages": [{
                "id": "RO-1", "area_m2": 800, "elements_per_vessel": 7, "vessels": 6,
                "membrane": "watertap_seawater", "recovery": 0.40,
                "max_feed_pressure_bar": 150, "min_concentrate_m3_h_per_vessel": 0.1,
            }],
            "target_TDS_g_L": 50,
        }
        base = ro.run(spec)
        self.assertFalse(base.get("errors"), base)
        lead = base["flux_lmh_lead"]
        self.assertGreater(lead, 1)
        spec["stages"][0]["max_flux_lmh"] = round(lead * 1.2, 4)
        cap = ro.capacity(spec)
        self.assertFalse(cap.get("errors"), cap)
        self.assertGreater(cap["capacity_multiple"], 1.05)
        self.assertLess(cap["capacity_multiple"], 2.0)
        self.assertIn("flux", cap["limited_by"]["check"])
        self.assertGreater(cap["limited_by"]["utilisation"], 0.95)
        self.assertLessEqual(cap["limited_by"]["utilisation"], 1.0)

    def test_normalize_hand_example(self):
        actual = {"Q_permeate": 80, "T_C": 20, "P_feed": 40, "dP": 2, "P_permeate": 1,
                  "pi_fb": 20, "pi_permeate": 0.5, "salt_passage": 1.5, "C_fb": 55, "Q_fb": 120}
        standard = {"Q_permeate": 100, "T_C": 25, "P_feed": 50, "dP": 2, "P_permeate": 1,
                    "pi_fb": 22, "pi_permeate": 0.4, "salt_passage": 1.0, "C_fb": 45, "Q_fb": 100}
        n = ro.normalize(actual, standard)
        self.assertAlmostEqual(n["TCF_actual"], 0.8413364867, places=6)
        self.assertAlmostEqual(n["NDP_actual"], 18.5, places=6)
        self.assertAlmostEqual(n["NDP_standard"], 26.4, places=6)
        self.assertAlmostEqual(n["normalized_permeate_flow"], 135.6914432840, places=6)
        self.assertAlmostEqual(n["normalized_salt_passage"], 0.7235667615, places=6)
        self.assertAlmostEqual(n["normalized_differential_pressure"], 1.5494453080, places=6)

    def test_capacity_does_not_report_ten_percent_when_low_solve_fails(self):
        base = {"id": "RO-1", "check": "flux vs max", "utilisation": 1.04}

        def solve(_spec, scale):
            if scale == 1.0:
                return {"checks": [base], "errors": []}
            return {"checks": [], "errors": ["infeasible"]}

        with mock.patch("plantagent.ro._solve", solve):
            cap = ro._capacity({})
        self.assertIsNone(cap["capacity_multiple"])
        self.assertEqual(cap["limited_by"], base)
        self.assertIn("no feasible capacity", cap["note"])

    def test_dwsim_tools_and_build_prompt_unchanged(self):
        ws = _ws()
        names = [t["function"]["name"] for t in ws.tools()]
        self.assertIn("run_process", names)
        self.assertIn("process_capacity", names)
        self.assertNotIn("run_ro", names)
        self.assertNotIn("ro_capacity", names)
        system, user, submit = ws._build_prompt()
        self.assertIn("P&ID", system)
        self.assertNotIn("WaterTAP", system)
        self.assertIn("DWSIM", user)
        self.assertIn("run_process", user)
        self.assertEqual(user, f"Unit: {ws.cfg['title']}\n\n" + BUILD_DWSIM)
        self.assertIn("run_process", submit["function"]["parameters"]["properties"]["label"]["description"])

    def test_watertap_tools_exclude_dwsim_process(self):
        ws = _ws("watertap")
        names = [t["function"]["name"] for t in ws.tools()]
        self.assertIn("run_ro", names)
        self.assertIn("ro_capacity", names)
        self.assertIn("check_coverage", names)
        self.assertIn("report_gap", names)
        self.assertNotIn("run_process", names)
        self.assertNotIn("process_capacity", names)
        system, user, submit = ws._build_prompt()
        self.assertIn("WaterTAP", system)
        self.assertIn("seawater reverse-osmosis", system)
        self.assertEqual(user, f"Unit: {ws.cfg['title']}\n\n" + BUILD_WATERTAP)
        self.assertIn("run_ro", user)
        self.assertIn("ro_capacity", user)
        self.assertNotIn("DWSIM", user)
        self.assertIn("Do not use run_process", user)
        self.assertIn("run_ro", submit["function"]["parameters"]["properties"]["label"]["description"])
        blocked = ws.call("run_process", {"label": "x", "spec": {}})
        self.assertIn("run_ro", blocked["error"])

    def test_watertap_build_saves_model_with_ro_paths(self):
        ws = _ws("watertap", title="SWRO test")
        spec = _tiny_spec()
        result = _ok_result(spec)
        mapping = [{"tag": "P-HP", "modelled_as": "HP", "source": "basis"},
                   {"tag": "RO-1", "modelled_as": "RO-1", "source": "basis"},
                   {"tag": "PX-1", "modelled_as": "ERD", "source": "basis"},
                   {"tag": "MF-1", "modelled_as": "MF-1", "source": "basis"},
                   {"tag": "POST-1", "modelled_as": "posttreatment", "source": "basis"}]
        assumptions = ["one train out of service at rated capacity",
                       "no second pass in this screening model"]

        def fake_loop(_self, phase, system, user, tools, submit_name, max_steps):
            self.assertEqual(phase, "build")
            self.assertEqual(max_steps, 30)
            self.assertIn("WaterTAP", system)
            self.assertIn("run_ro", user)
            tool_names = [t["function"]["name"] for t in tools]
            self.assertIn("run_ro", tool_names)
            self.assertNotIn("run_process", tool_names)
            return {"label": "design", "mapping": mapping, "calibration": [], "assumptions": assumptions}

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ws.model_file = root / "model.json"
            ws.rev_file = root / "revisions.json"
            ws.dir = root
            ws.log = (root / "log.jsonl").open("w")
            ws.runs["design"] = {"spec": spec, "purpose": "calibrated", "result": result}
            try:
                with mock.patch.object(PlantWorkspace, "loop", fake_loop), \
                     mock.patch("plantagent.plant.llm.spent", return_value=0.0), \
                     mock.patch("plantagent.plant.audit.append", return_value={"hash": "0"}):
                    built = ws.build()
            finally:
                ws.log.close()
            self.assertEqual(built["engine"], "watertap")
            self.assertEqual(built["review_status"], "ok", built["review"])
            self.assertEqual(built["coverage"]["engine"], "watertap")
            self.assertTrue(any(n["kind"] == "post-treatment" for n in built["coverage"]["notes"]))
            saved = json.loads(ws.model_file.read_text())
            self.assertEqual(saved["engine"], "watertap")
            self.assertEqual(saved["spec"]["stages"][0]["id"], "RO-1")
            self.assertEqual(saved["result"]["boron"], "not modelled")

    def test_watertap_final_build_steps_force_submit_or_gap(self):
        ws = _ws("watertap")
        ws.steps, ws.listener, ws.log = 0, None, io.StringIO()
        ws._review_run = lambda _label: {"findings": []}
        tools = [
            {"type": "function", "function": {"name": "run_ro"}},
            {"type": "function", "function": {"name": "report_gap"}},
            {"type": "function", "function": {"name": "submit_model"}},
        ]
        seen = []

        def complete(_model, _messages, **params):
            seen.append([t["function"]["name"] for t in params["tools"]])
            return {"content": "", "tool_calls": [{"id": "1", "name": "submit_model",
                                                       "arguments": '{"label":"design"}'}]}

        with mock.patch("plantagent.plant.llm.complete", complete):
            self.assertEqual(ws._build_loop("build", "system", "user", tools, "submit_model", 3),
                             {"label": "design"})
        self.assertEqual(seen, [["report_gap", "submit_model"]])

    def test_watertap_never_calls_process_or_dwsim_review(self):
        ws = _ws("watertap")
        spec = _tiny_spec()
        result = _ok_result(spec)
        assumptions = ["one-train-out N+1", "second pass not in this model"]
        with mock.patch.object(process, "run", side_effect=AssertionError("process.run")) as pr, \
             mock.patch.object(process, "capacity", side_effect=AssertionError("process.capacity")), \
             mock.patch("plantagent.plant.review_model", side_effect=AssertionError("review_model")) as rm, \
             mock.patch("plantagent.plant.coverage", side_effect=AssertionError("coverage")), \
             mock.patch.object(ro, "run", return_value=result) as rr, \
             mock.patch.object(ro, "capacity", return_value={"capacity_multiple": 1.2, "limited_by": {"check": "flux"}}):
            reviewed = ws._review(spec, result, assumptions=assumptions)
            self.assertEqual(reviewed["status"], "ok", reviewed)
            cov = ws._coverage(spec, [])
            self.assertEqual(cov["engine"], "watertap")
            ws.built = {"label": "design", "spec": spec, "result": result, "engine": "watertap"}
            ws.model_file = Path(tempfile.mkdtemp()) / "model.json"
            ws._state = {}
            state = ws.state(1.0)
            self.assertEqual(state["recovery"], result["recovery"])
            cap = ws.capacity()
            self.assertEqual(cap["capacity_multiple"], 1.2)
            rr.assert_called()
            pr.assert_not_called()
            rm.assert_not_called()

    def test_mass_balance_blocks_ro_review(self):
        spec = _tiny_spec()
        bad = _ok_result(spec, streams={
            "intake": {"flow_m3_h": 100, "P_bar": 1},
            "hp_suction": {"flow_m3_h": 98, "P_bar": 0.8},
            "hp_discharge": {"flow_m3_h": 98, "P_bar": 70},
            "permeate": {"flow_m3_h": 10, "P_bar": 1, "TDS_g_L": 0.2},
            "brine": {"flow_m3_h": 10, "P_bar": 1, "TDS_g_L": 60},
        }, recovery=0.1)
        review = review_ro(spec, bad, assumptions=["one train out", "no second pass"])
        self.assertEqual(review["status"], "model needs review")
        self.assertTrue(any(f["check"] == "mass balance" for f in review["findings"]))
        self.assertGreater(review["blocking"], 0)

    def test_boron_gap_is_honest(self):
        spec = _tiny_spec()
        result = _ok_result(spec)
        review = review_ro(spec, result, assumptions=["one train out", "second pass omitted"])
        boron = next(f for f in review["findings"] if f["check"] == "boron not modelled")
        self.assertEqual(boron["severity"], "warn")
        self.assertIn("not modelled", boron["evidence"].casefold())
        self.assertNotIn("mg/L", boron["evidence"])

    def test_ro_coverage_notes_posttreatment(self):
        spec = _tiny_spec()
        cov = ro_coverage(None, spec, [{"tag": "POST-1", "modelled_as": "posttreatment", "source": "basis"}])
        self.assertTrue(any(n["kind"] == "post-treatment" and not n["modelled"] for n in cov["intentionally_not_simulated"]))
        self.assertTrue(any(m["note_only"] for m in cov["mappings"]))
        chem = next(n for n in cov["notes"] if n["id"] == "CHEM-1")
        self.assertFalse(chem["modelled"])

    def test_optional_tiny_solve_without_llm(self):
        _watertap()
        spec = {
            "feed": {"flow_m3_h": 50, "TDS_g_L": 35, "T_C": 25, "P_bar": 1},
            "hp_pump": {"efficiency": 0.8, "P_out_bar": 70, "max_bar": 150, "max_kW": 2000},
            "stages": [{"id": "RO-1", "area_m2": 400, "membrane": "watertap_seawater", "recovery": 0.40,
                        "max_feed_pressure_bar": 150}],
            "energy_recovery": {"type": "none"},
            "target_TDS_g_L": 1.0,
        }
        result = ro.run(spec)
        self.assertFalse(result.get("errors"), result)
        review = review_ro(spec, result, assumptions=["one train online", "no second pass"])
        self.assertFalse(any(f["check"] == "mass balance" and f["severity"] == "block" for f in review["findings"]),
                         review)


if __name__ == "__main__":
    unittest.main()
