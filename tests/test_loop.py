"""Engineering loop control flow on a stub workspace: no model call, no solver."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import loop
from plantagent.plant import _spec_object


class Stub:
    name = "stub"
    model = "baseten:meta-models/muse-spark-open-1026"

    def __init__(self, answers, d):
        self.queue, self.answers, self.asked = list(answers), [], []
        self.model_file = Path(d) / "model.json"

    def ask(self, text):
        self.asked.append(text)
        a = self.queue.pop(0)
        if isinstance(a, Exception):
            raise a
        self.answers.append(a)
        return a


def prop(title, ok=True):
    return {"title": title, "verified": ok, "changes": [{"path": "units.X.y", "value": 1}]}


class LoopTest(unittest.TestCase):
    def run_loop(self, answers, rows):
        d = tempfile.mkdtemp()
        w = Stub(answers, d)
        with mock.patch.object(loop, "checks", side_effect=rows):
            log = loop.run(w, "reach 120 % and pass every check", max_rounds=3, budget_usd=5)
        saved = json.loads((loop.work_dir(w) / log["id"] / "worklog.json").read_text())
        self.assertEqual(saved["status"], log["status"])
        self.assertEqual(saved["model"], w.model)
        self.assertEqual(saved["provider"], "baseten")
        return w, log

    def test_fail_then_fix_then_done(self):
        w, log = self.run_loop([{"headline": "a", "proposals": [prop("K-202")]}, {"headline": "b", "proposals": [prop("K-202"), prop("TX-1 3.15 MVA")]}],
                               [[{"check": "electrical", "title": "TX-1 133 %", "status": "fail"}],
                                [{"check": "process", "title": "120 %", "status": "pass"}, {"check": "electrical", "title": "TX-1 96 %", "status": "pass"}]])
        self.assertEqual(log["status"], "done")
        self.assertEqual(len(log["rounds"]), 2)
        self.assertIn("TX-1 133 %", w.asked[1])  # the failed check went back to Muse with its numbers
        self.assertEqual(log["result"]["passes"], ["process", "electrical"])
        self.assertEqual(log["approval_status"], "ready_for_review")
        self.assertEqual({s["actor"] for s in log["rounds"][0]["steps"]}, {"muse", "engine"})

    def test_unsolvable_stops(self):
        _, log = self.run_loop([{"headline": loop.UNSOLVABLE + " no vendor curve", "proposals": []}], [])
        self.assertEqual(log["status"], "unsolved")

    def test_unsolvable_with_a_fixable_rejection_goes_back_first(self):
        w, log = self.run_loop([{"headline": loop.UNSOLVABLE + " no curve", "proposals": [prop("K-202", ok=False) | {"unverified_reason": "unknown motor M-K-202"}]},
                                {"headline": "b", "proposals": [prop("K-202")]}],
                               [[{"check": "process", "title": "120 %", "status": "pass"}]])
        self.assertIn("unknown motor M-K-202", w.asked[1])
        self.assertEqual(log["status"], "done")

    def test_unverified_proposal_goes_back(self):
        w, log = self.run_loop([{"headline": "a", "proposals": [prop("raise limit", ok=False) | {"unverified_reason": "edits a limit"}]},
                                {"headline": "b", "proposals": [prop("K-202")]}],
                               [[{"check": "process", "title": "120 %", "status": "pass"}]])
        self.assertEqual(log["status"], "done")
        self.assertIn("edits a limit", w.asked[1])


    def test_rejected_proposal_reason_goes_back_even_when_checks_run(self):
        w, log = self.run_loop([{"headline": "a", "proposals": [prop("clean"), prop("K-202", ok=False) | {"unverified_reason": "cable must be one of X"}]},
                                {"headline": "b", "proposals": [prop("clean"), prop("K-202")]}],
                               [[{"check": "process", "title": "98 %", "status": "fail"}],
                                [{"check": "process", "title": "120 %", "status": "pass"}]])
        self.assertIn("cable must be one of X", w.asked[1])
        self.assertEqual(log["status"], "done")

    def test_grid_list_path_gets_previous_value(self):
        spec = {"gens": [{"id": "DOL injection", "p_mw": 1564}]}
        self.assertEqual(_spec_object(spec, "gens", "DOL injection").get("p_mw"), 1564)

    def test_budget_stop_keeps_last_completed_result(self):
        _, log = self.run_loop([{"headline": "first result", "proposals": [prop("K-202")]},
                                loop.llm.BudgetExceeded("run budget reached")],
                               [[{"check": "startup", "title": "voltage dip", "status": "fail"}]])
        self.assertEqual(log["status"], "budget")
        self.assertEqual(log["result"]["headline"], "first result")
        self.assertEqual(log["result"]["fails"], ["startup"])
        self.assertEqual(log["approval_status"], "not_reached")

    def test_budget_after_rejected_proposal_is_not_reported_as_a_design(self):
        rejected = prop("bigger trays", ok=False) | {"unverified_reason": "rating needs replace_unit"}
        _, log = self.run_loop([{"headline": "Quarter more product", "proposals": [rejected]},
                                loop.llm.BudgetExceeded("run budget reached")], [])
        self.assertEqual(log["status"], "budget")
        self.assertEqual(log["result"]["headline"], "No verified design before budget limit")
        self.assertEqual(log["result"]["fails"], ["proposal verification"])

    def test_open_check_stops_loop_but_keeps_approval_open(self):
        _, log = self.run_loop([{"headline": "screening passes", "proposals": [prop("K-202")]}],
                               [[{"check": "process", "title": "120 %", "status": "pass"}, {"check": "vendor confirmation", "title": "curve needed", "status": "open"}]])
        self.assertEqual(log["status"], "done")
        self.assertEqual(log["approval_status"], "open")
        self.assertEqual(log["result"]["open"], ["vendor confirmation"])


    def test_no_checks_is_not_done(self):  # an empty check list (a broken adapter) must never read as a pass
        _, log = self.run_loop([{"headline": "a", "proposals": [prop("K-202")]}] * 3, [[], [], []])
        self.assertNotEqual(log["status"], "done")

    def test_grid_limits_and_n1_pass_is_done(self):  # grid cases have no 'process' row
        _, log = self.run_loop([{"headline": "a", "proposals": [prop("redispatch")]}],
                               [[{"check": "limits", "status": "pass"}, {"check": "N-1", "status": "pass"}]])
        self.assertEqual(log["status"], "done")

    def test_unverified_without_reason_sends_the_limit_back(self):
        p = prop("bottoms 3.6", ok=False) | {"capacity_multiple": 1.131, "over_limits_at_target": [
            {"id": "K 2750", "check": "Fair flood fraction vs limit", "utilisation": 1.09}]}
        w, _ = self.run_loop([{"headline": "a", "proposals": [p]}, {"headline": "b", "proposals": [prop("reflux 1.1")]}],
                             [[{"check": "process", "title": "120 %", "status": "pass"}]])
        self.assertIn("K 2750 Fair flood fraction vs limit 109 %", w.asked[1])


if __name__ == "__main__":
    unittest.main()

