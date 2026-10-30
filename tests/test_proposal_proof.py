import unittest
from unittest.mock import patch

from plantagent import process
from plantagent.plant import (FRACTION_SUM_TOL, PlantWorkspace, change_errors, normalize_proposal, patch as apply_patch)


BASE = {
    "compounds": ["Methane"],
    "package": "Peng-Robinson (PR)",
    "feeds": {"F": {"T_C": 25, "P_bar": 1.2, "kg_h": 100000, "x": {"Methane": 1}}},
    "units": [{"id": "K-1", "type": "compressor", "in": "F", "out": "PRODUCT", "P_out_bar": 3, "eff_pct": 75}],
    "limits": {"K-1": {"max_kg_h": 100000}},
}

# Downstream exchanger so a parallel-compressor proposal has an area check to show.
SALT = {
    "compounds": ["Methane"],
    "package": "Peng-Robinson (PR)",
    "feeds": {
        "F": {"T_C": 25, "P_bar": 1.2, "kg_h": 100000, "x": {"Methane": 1}},
        "CU": {"T_C": 20, "P_bar": 5, "kg_h": 80000, "x": {"Methane": 1}, "utility": True},
    },
    "units": [
        {"id": "K-201", "type": "compressor", "in": "F", "out": "DIS", "P_out_bar": 3, "eff_pct": 75},
        {"id": "H-201", "type": "hx", "hot": ["DIS", "PRODUCT"], "cold": ["CU", "CU_OUT"],
         "U_W_m2K": 250, "area_m2": 200},
    ],
    "limits": {"K-201": {"max_kg_h": 100000}, "H-201": {"area_m2": 200, "out_T_C": 90, "side": "hot"}},
}


def workspace(spec=BASE):
    w = object.__new__(PlantWorkspace)
    w.cfg, w.built, w._state, w.runs = {"target_scale": 1.2}, {"spec": spec}, {}, {}
    w.state = lambda scale, spec=spec: process.run(spec, scale)
    return w


def salt_proposal():
    """The shape that failed before: K-202's add_unit and its inlet reroute in one object, fractions on the splitter."""
    return {"tag": "K-201", "title": "Parallel K-202", "assumptions": ["K-202 matches K-201 head and efficiency"],
            "changes": [
                {"add_unit": {"id": "K-SPLIT", "type": "splitter", "in": "F", "out": ["K1-SUC", "K2-SUC"],
                              "fractions": [0.8333, 0.1667]}},
                {"add_unit": {"id": "K-202", "type": "compressor", "in": "K2-SUC", "out": "K2-DIS",
                              "P_out_bar": 3, "eff_pct": 75},
                 "limits": {"max_kg_h": 25000},
                 "rating_source": "standard 25 t/h size; vendor quote to confirm",
                 "note": "parallel body",
                 "reroute": {"unit": "K-201", "field": "in", "value": "K1-SUC"}},
                {"add_unit": {"id": "K-JOIN", "type": "mixer", "in": ["K1-DIS", "K2-DIS"], "out": "DIS"}},
                {"reroute": {"unit": "K-201", "field": "out", "value": "K1-DIS"}},
            ]}


class ProposalProofTests(unittest.TestCase):
    def test_blocked_model_cannot_apply_a_proposal(self):
        w = workspace()
        w.built["review"] = {"blocking": 1}
        w.revisions, w.answers = [], []
        with self.assertRaisesRegex(ValueError, "blocking review findings"):
            w.accept({"title": "unsafe", "changes": []}, reason="try anyway")

    def test_existing_structure_and_performance_need_real_physical_changes(self):
        structural = change_errors(BASE, [{"path": "units.K-1.kind", "value": "positive_displacement"}])
        self.assertTrue(any("cannot edit existing unit structure" in error for error in structural))
        unsupported = change_errors(BASE, [{"path": "units.K-1.eff_pct", "value": 85}])
        self.assertTrue(any("needs physical_change and rating_source" in error for error in unsupported))
        supported = change_errors(BASE, [{"path": "units.K-1.eff_pct", "value": 85,
                                          "physical_change": "replace impeller",
                                          "rating_source": "vendor curve VC-12 to confirm"}])
        self.assertEqual(supported, [])

    def test_verify_rejects_a_proposal_that_removes_a_limit_check(self):
        w = workspace()
        before = {"errors": [], "units": {"K-1": {}}, "streams": {},
                  "checks": [{"id": "K-1", "check": "head vs curve", "utilisation": 0.8}]}
        after = {"errors": [], "units": {"K-1": {}}, "streams": {}, "checks": []}
        w.state = lambda scale: before
        w._solve = lambda changed, scale: after
        w._capacity_of = lambda changed: {"capacity_multiple": 1.5, "limited_by": None}
        result = w.verify({"tag": "K-1", "changes": [{"path": "units.K-1.eff_pct", "value": 80,
                                                        "physical_change": "new impeller",
                                                        "rating_source": "vendor curve to confirm"}]})
        self.assertFalse(result["verified"])
        self.assertFalse(result["reaches_target"])
        self.assertIn("removes existing limit checks", result["unverified_reason"])
        self.assertEqual(result["disappeared_checks"], [{"id": "K-1", "check": "head vs curve"}])

    def test_capacity_search_never_turns_solver_failure_into_capacity(self):
        def solver_fails(scale):
            if scale > 1:
                return None, [], ["did not converge"]
            check = {"id": "K", "check": "flow", "utilisation": 0.8}
            return check, [check], []

        failed = process._capacity_search(solver_fails)
        self.assertIsNone(failed["capacity_multiple"])
        self.assertEqual(failed["capacity_lower_bound"], 1.0)
        self.assertIn("solver failed", failed["note"])

        def no_limit(scale):
            check = {"id": "K", "check": "flow", "utilisation": scale / 10}
            return check, [check], []

        unbounded = process._capacity_search(no_limit, max_scale=2)
        self.assertIsNone(unbounded["capacity_multiple"])
        self.assertEqual(unbounded["capacity_lower_bound"], 2)
    def test_fraction_tolerance_accepts_the_logged_split(self):
        self.assertLessEqual(abs(0.8333 + 0.1667 - 1), FRACTION_SUM_TOL)
        p = {"changes": [{"add_unit": {"id": "K-SPLIT", "type": "splitter", "in": "F",
                                       "out": ["A", "B"], "fractions": [0.8333, 0.1667]}}]}
        self.assertEqual(normalize_proposal(p, BASE, {}), [])
        self.assertEqual(p["normalized_changes"], [])

    def test_combined_add_and_reroute_splits_without_dropping_fields(self):
        p = salt_proposal()
        self.assertEqual(normalize_proposal(p, SALT, {}), [])
        self.assertEqual([c["add_unit"]["id"] if "add_unit" in c else c["reroute"]["unit"] + "." + c["reroute"]["field"]
                          for c in p["changes"]],
                         ["K-SPLIT", "K-202", "K-201.in", "K-JOIN", "K-201.out"])
        added = p["changes"][1]
        self.assertEqual(set(added), {"add_unit", "limits", "rating_source", "note"})
        self.assertEqual(added["limits"], {"max_kg_h": 25000})
        self.assertEqual(added["rating_source"], "standard 25 t/h size; vendor quote to confirm")
        self.assertEqual(added["note"], "parallel body")
        self.assertEqual(added["add_unit"]["out"], "K2-DIS")
        self.assertEqual(p["changes"][2]["reroute"], {"unit": "K-201", "field": "in", "value": "K1-SUC"})
        self.assertNotIn("limits", p["changes"][2])
        self.assertNotIn("rating_source", p["changes"][2])
        self.assertTrue(any(n.startswith("split change 2 into add_unit K-202 then reroute K-201.in")
                            for n in p["normalized_changes"]))
        self.assertTrue(any("kept extra field note" in n for n in p["normalized_changes"]))
        spec = apply_patch(SALT, p["changes"])
        self.assertEqual(spec["limits"]["K-201"], {"max_kg_h": 100000})
        splitter = next(u for u in spec["units"] if u["id"] == "K-SPLIT")
        self.assertEqual(splitter["fractions"], [0.8333, 0.1667])
        self.assertEqual(next(u["id"] for u in spec["units"] if u["id"] == "K-202"), "K-202")
        self.assertEqual(next(u for u in spec["units"] if u["id"] == "K-JOIN")["in"], ["K1-DIS", "K2-DIS"])
        # a second pass does not rewrite the canonical list or the audit note
        canonical, notes = p["changes"], list(p["normalized_changes"])
        self.assertEqual(normalize_proposal(p, SALT, {}), [])
        self.assertEqual(p["changes"], canonical)
        self.assertEqual(p["normalized_changes"], notes)

    def test_change_errors_stays_strict_and_unplaceable_fields_are_kept(self):
        combined = {"add_unit": {"id": "K-2", "type": "compressor"}, "reroute": {"unit": "K-1", "field": "in", "value": "A"},
                    "limits": {"max_kg_h": 1}, "rating_source": "x"}
        self.assertTrue(any("exactly one" in e for e in change_errors(BASE, [combined])))
        original = {"path": "feeds.F.kg_h", "value": 90000, "add_unit": {"id": "X", "type": "mixer", "in": ["A"], "out": "B"}}
        p = {"changes": [original]}
        errors = normalize_proposal(p, BASE, {})
        self.assertTrue(errors)
        self.assertIn("combines path and add_unit", errors[0])
        self.assertEqual(p["changes"], [original])

    def test_already_canonical_changes_are_a_noop(self):
        changes = [
            {"add_unit": {"id": "SP-2", "type": "splitter", "in": "F", "out": ["K1-SUC", "K2-SUC"], "fractions": [.8, .2]}},
            {"reroute": {"unit": "K-1", "field": "in", "value": "K1-SUC"}, "from": "F"},
        ]
        p = {"changes": changes}
        self.assertEqual(normalize_proposal(p, BASE, {}), [])
        self.assertIs(p["changes"], changes)
        self.assertEqual(p["normalized_changes"], [])
        self.assertEqual(changes[1]["from"], "F")

    def test_existing_limit_cannot_be_raised_by_path_or_add_unit(self):
        raised = workspace().verify({"changes": [{"path": "limits.K-1.max_kg_h", "value": 200000}]})
        self.assertFalse(raised["verified"])
        self.assertIsNone(raised["capacity_multiple"])
        self.assertIn("changes a documented limit", raised["unverified_reason"])
        self.assertIn("changes a documented limit", raised["calculation"]["errors"][0])
        via_add = workspace().verify({"changes": [{
            "add_unit": {"id": "K-1", "type": "compressor", "in": "F", "out": "PRODUCT", "P_out_bar": 3, "eff_pct": 75},
            "limits": {"max_kg_h": 250000}, "rating_source": "not a quote"}]})
        self.assertFalse(via_add["verified"])
        self.assertIsNone(via_add["capacity_multiple"])
        self.assertIn("cannot raise existing limit K-1.max_kg_h", via_add["unverified_reason"])

    def test_new_physical_unit_still_needs_limits_and_rating_source(self):
        missing_limits = workspace().verify({"changes": [{
            "add_unit": {"id": "K-2", "type": "compressor", "in": "A", "out": "B"},
            "rating_source": "vendor quote to confirm"}]})
        self.assertIn("needs its own limits", missing_limits["unverified_reason"])
        self.assertIsNone(missing_limits["capacity_multiple"])
        missing_source = workspace().verify({"changes": [{
            "add_unit": {"id": "K-2", "type": "compressor", "in": "A", "out": "B"}, "limits": {"max_kg_h": 25000}}]})
        self.assertIn("needs rating_source", missing_source["unverified_reason"])
        self.assertIsNone(missing_source["capacity_multiple"])

    def test_splitter_without_a_unique_cited_run_is_rejected(self):
        w = workspace()
        missing = w.verify({"changes": [{"add_unit": {"id": "K-SPLIT", "type": "splitter", "in": "F", "out": ["A", "B"]}}]})
        self.assertFalse(missing["verified"])
        self.assertIsNone(missing["capacity_multiple"])
        self.assertNotEqual(missing["capacity_multiple"], 0)
        self.assertIn("missing fractions", missing["unverified_reason"])
        self.assertTrue(any("missing fractions" in e for e in missing["calculation"]["errors"]))
        w.runs = {
            "a": {"spec": {"units": [{"id": "K-SPLIT", "type": "splitter", "fractions": [0.8, 0.2]}]}},
            "b": {"spec": {"units": [{"id": "K-SPLIT", "type": "splitter", "fractions": [0.8333, 0.1667]}]}},
        }
        ambiguous = {"runs": ["a", "b"], "changes": [
            {"add_unit": {"id": "K-SPLIT", "type": "splitter", "in": "F", "out": ["A", "B"]}}]}
        rejected = w.verify(ambiguous)
        self.assertIsNone(rejected["capacity_multiple"])
        self.assertIn("ambiguous", rejected["unverified_reason"])
        self.assertNotIn("fractions", ambiguous["changes"][0]["add_unit"])

    def test_splitter_recovers_fractions_from_the_one_cited_run(self):
        w = workspace()
        w.runs = {"trial": {"spec": {"units": [
            {"id": "K-SPLIT", "type": "splitter", "in": "F", "out": ["A", "B"], "fractions": [0.8333, 0.1667]}]}}}
        p = {"runs": ["trial"], "changes": [
            {"add_unit": {"id": "K-SPLIT", "type": "splitter", "in": "F", "out": ["A", "B"]}},
            {"path": "not-a-path"},
        ]}
        result = w.verify(p)
        self.assertIsNone(result["capacity_multiple"])
        self.assertEqual(p["changes"][0]["add_unit"]["fractions"], [0.8333, 0.1667])
        self.assertIn("trial", p["changes"][0]["fractions_source"])
        self.assertTrue(any("recovered fractions for K-SPLIT from run trial" in n for n in p["normalized_changes"]))
        # an answer card is also a citation, before verify() sees the proposal
        cited = {"changes": [{"add_unit": {"id": "K-SPLIT", "type": "splitter", "in": "F", "out": ["A", "B"]}}]}
        answer = {"cards": [{"runs": ["trial"]}]}
        from plantagent.plant import cited_run_labels
        self.assertEqual(normalize_proposal(cited, BASE, w.runs, cited_run_labels(cited, answer)), [])
        self.assertEqual(cited["changes"][0]["add_unit"]["fractions"], [0.8333, 0.1667])

    def test_malformed_proposal_never_reports_capacity_zero(self):
        result = workspace().verify({"changes": [{
            "add_unit": {"id": "K-2", "type": "compressor", "in": "A", "out": "B"},
            "reroute": {"unit": "K-1", "field": "in", "value": "A"}}]})
        self.assertFalse(result["verified"])
        self.assertIsNone(result["capacity_multiple"])
        self.assertIsNone(result["calculation"]["capacity_multiple_after"])
        self.assertTrue(result["unverified_reason"])
        self.assertTrue(result["calculation"]["errors"])
        self.assertIn("needs its own limits", result["unverified_reason"])

    def test_accept_persists_calculation_on_the_revision_and_the_audit(self):
        w = workspace()
        w.name, w.model, w.revisions = "proof", "test-model", []
        calc = {"target_scale": 1.2, "capacity_multiple_after": 1.4, "errors": [], "warnings": []}
        captured = {}
        w.verify = lambda p: {"verified": True, "capacity_multiple": 1.4, "new_equipment": [],
                              "over_limits_at_target": [], "calculation": calc}
        w._commit = lambda rev: captured.update(rev=rev)

        def fake_append(case, action, user=None, reason=None, details=None):
            captured["details"] = details
            return {"hash": "abc"}

        with patch("plantagent.plant.audit.append", fake_append):
            w.accept({"title": "trim feed", "changes": [{"path": "feeds.F.kg_h", "value": 90000}]},
                     user="eng", reason="keep the calculation")
        self.assertEqual(captured["rev"]["calculation"], calc)
        self.assertEqual(captured["details"]["calculation"], calc)
        old = {"rev": 1, "kind": "change", "title": "earlier", "changes": [], "spec_after": BASE}
        self.assertIsNone(old.get("calculation"))

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_parallel_compressor_verifies_with_heater_area_in_the_calculation(self):
        w = workspace(SALT)
        p = salt_proposal()
        result = w.verify(p)
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["target_scale"], 1.2)
        self.assertIsNotNone(result["capacity_multiple"])
        self.assertNotEqual(result["capacity_multiple"], 0)
        calc = result["calculation"]
        self.assertEqual(calc["target_scale"], 1.2)
        self.assertEqual(calc["simulator"], "dwsim")
        self.assertEqual(result["capacity_multiple"], calc["capacity_multiple_after"])
        self.assertIsNotNone(calc["capacity_multiple_before"])
        self.assertEqual(calc["assumptions"], ["K-202 matches K-201 head and efficiency"])
        flows = {s["id"]: s for s in calc["streams"]}
        self.assertAlmostEqual(flows["K1-SUC"]["kg_h"], 99996, delta=1)
        self.assertAlmostEqual(flows["K2-SUC"]["kg_h"], 20004, delta=1)
        self.assertIn("T_C", flows["K1-SUC"])
        self.assertIn("kW", calc["units"]["K-201"])
        self.assertIn("kW", calc["units"]["K-202"])
        self.assertTrue(any(c["id"] == "H-201" and "area" in c["check"] for c in calc["checks"]))
        added = calc["new_equipment"]
        self.assertEqual([item["id"] for item in added], ["K-202"])
        self.assertEqual(added[0]["status"], "new equipment, rating to confirm")
        self.assertEqual(added[0]["limits"], {"max_kg_h": 25000})
        self.assertIn("kW", added[0]["operating_point"])
        self.assertEqual(result["new_equipment"][0]["status"], "new equipment, rating to confirm")
        self.assertEqual(apply_patch(SALT, p["changes"])["limits"]["K-201"]["max_kg_h"], 100000)


if __name__ == "__main__":
    unittest.main()
