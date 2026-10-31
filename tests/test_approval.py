import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from plantagent import approval, audit


class Workspace:
    def __init__(self, root):
        self.name = "sample"
        self.model_file = root / "runs/ws/sample/model.json"
        self.model_file.parent.mkdir(parents=True)
        self.spec = {"units": [{"id": "U", "type": "heater"}]}
        self.built = {"label": "model", "spec": self.spec}
        self.revisions = []
        self.answers = [{"headline": "proposal", "proposals": [{"verified": True, "changes": []}]}]


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.w = Workspace(self.root)
        for module in (approval, audit):
            patcher = mock.patch.object(module, "ROOT", self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.folder = self.w.model_file.parent / "decision-test"
        self.folder.mkdir()
        (self.folder / "decision.json").write_text(json.dumps({"case": "sample"}))
        (self.folder / "decision.md").write_text("draft")
        with zipfile.ZipFile(self.folder / "decision.zip", "w") as z:
            z.writestr("decision.json", "{}")

    def test_actions_keep_the_existing_audit_chain_intact(self):
        pack = approval.issue(self.w, self.folder.name, "alice", "issue for review")
        approval.comment(self.w, "gate", "electrical", "verify transformer margin", "bob")
        approval.signoff(self.w, "process", "Alice Engineer", "process calculation checked", "alice")
        self.assertEqual(pack["revision"], 1)
        self.assertEqual(audit.verify("sample"), {"ok": True, "entries": 3})
        self.assertIn("approval.json", zipfile.ZipFile(self.folder / "decision.zip").namelist())

    def test_design_change_invalidates_signoffs_and_next_issue_is_new_revision(self):
        approval.issue(self.w, self.folder.name, "alice", "first issue")
        approval.signoff(self.w, "safety", "S. Reviewer", "HAZOP reviewed", "safety")
        self.w.revisions.append({"rev": 1, "changes": [{"path": "units.U.area_m2", "value": 20}]})
        state = approval.status(self.w)
        self.assertEqual(state["packs"][0]["status"], "superseded")
        self.assertFalse(state["signoffs"][0]["active"])
        second = self.w.model_file.parent / "decision-test-2"
        second.mkdir(); (second / "decision.json").write_text("{}"); (second / "decision.md").write_text("revision 2")
        pack = approval.issue(self.w, second.name, "alice", "changed design")
        self.assertEqual(pack["revision"], 2)
        with self.assertRaisesRegex(ValueError, "already issued and frozen"):
            approval.issue(self.w, second.name)
        (second / "decision.md").write_text("edited after issue")
        self.assertEqual(approval.status(self.w)["packs"][-1]["integrity"], "changed")


if __name__ == "__main__":
    unittest.main()
