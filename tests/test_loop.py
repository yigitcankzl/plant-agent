"""Engineering loop control flow on a stub workspace: no model call, no solver."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import loop


class Stub:
    name = "stub"

    def __init__(self, answers, d):
        self.queue, self.answers, self.asked = list(answers), [], []
        self.model_file = Path(d) / "model.json"

    def ask(self, text):
        self.asked.append(text)
        a = self.queue.pop(0)
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
        return w, log

    def test_fail_then_fix_then_done(self):
        w, log = self.run_loop([{"headline": "a", "proposals": [prop("K-202")]}, {"headline": "b", "proposals": [prop("K-202"), prop("TX-1 3.15 MVA")]}],
                               [[{"check": "electrical", "title": "TX-1 133 %", "status": "fail"}],
                                [{"check": "electrical", "title": "TX-1 96 %", "status": "pass"}]])
        self.assertEqual(log["status"], "done")
        self.assertEqual(len(log["rounds"]), 2)
        self.assertIn("TX-1 133 %", w.asked[1])  # the failed check went back to Muse with its numbers
        self.assertEqual(log["result"]["passes"], ["electrical"])
        self.assertEqual({s["actor"] for s in log["rounds"][0]["steps"]}, {"muse", "engine"})

    def test_unsolvable_stops(self):
        _, log = self.run_loop([{"headline": loop.UNSOLVABLE + " no vendor curve", "proposals": []}], [])
        self.assertEqual(log["status"], "unsolved")

    def test_unverified_proposal_goes_back(self):
        w, log = self.run_loop([{"headline": "a", "proposals": [prop("raise limit", ok=False) | {"unverified_reason": "edits a limit"}]},
                                {"headline": "b", "proposals": [prop("K-202")]}],
                               [[{"check": "process", "title": "120 %", "status": "pass"}]])
        self.assertEqual(log["status"], "done")
        self.assertIn("edits a limit", w.asked[1])


if __name__ == "__main__":
    unittest.main()
