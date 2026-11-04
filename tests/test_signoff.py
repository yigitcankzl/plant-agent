"""MOC sign-off: state machine, the same-person rule, and the frozen package (no model call, no solver)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import audit, signoff


class SignoffTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        for mod in (signoff, audit):
            p = mock.patch.object(mod, "ROOT", self.root)
            p.start()
            self.addCleanup(p.stop)
        ws = self.root / "runs" / "ws" / "c1"
        (ws / "decision-1").mkdir(parents=True)
        (ws / "decision-1" / "decision.json").write_text(json.dumps({"design": {"answer_index": 2, "headline": "Checked design", "revisions": 1}}))
        (ws / "decision-1" / "rev_b.svg").write_text("<svg/>")
        (ws / "gates.json").write_text(json.dumps({"disciplines": [
            {"id": "process", "status": "pass"}, {"id": "electrical", "status": "fail", "summary": "TX-1 133 %"},
            {"id": "controls", "status": "open", "summary": "no adapter"}]}))
        self.ws = ws

    def test_review_needs_dispositions_then_approve_freezes(self):
        with self.assertRaisesRegex(ValueError, "electrical"):
            signoff.review("c1", "Ada")
        signoff.dispose("c1", "electrical", "accepted_risk", "illustrative TX-1; real rating to be confirmed", "Ada")
        s = signoff.review("c1", "Ada", "checked")
        self.assertEqual(s["state"], "reviewed")
        s = signoff.approve("c1", "Grace")
        self.assertEqual(s["state"], "approved")
        self.assertEqual(s["frozen"]["open_items"], ["controls"])
        self.assertIn("gates.json", s["frozen"]["files"])
        self.assertTrue(audit.verify("c1")["ok"])

    def test_approver_cannot_be_reviewer(self):
        signoff.dispose("c1", "electrical", "accepted_risk", "r", "Ada")
        signoff.review("c1", "Ada")
        with self.assertRaisesRegex(ValueError, "cannot be the reviewer"):
            signoff.approve("c1", "ada")
        with self.assertRaisesRegex(ValueError, "cannot be the reviewer"):
            signoff.reject("c1", "Ada", "no")

    def test_must_fix_blocks_approval_but_allows_rejection(self):
        signoff.dispose("c1", "electrical", "must_fix", "transformer must be resized", "Ada")
        signoff.review("c1", "Ada")
        with self.assertRaisesRegex(ValueError, "must fix"):
            signoff.approve("c1", "Grace")
        self.assertEqual(signoff.reject("c1", "Grace", "resize TX-1 first")["state"], "rejected")
        self.assertEqual(signoff.reopen("c1", "Ada", "TX-1 resized")["state"], "draft")

    def test_change_after_approval_drops_to_draft(self):
        signoff.dispose("c1", "electrical", "accepted_risk", "r", "Ada")
        signoff.review("c1", "Ada")
        signoff.approve("c1", "Grace")
        (self.ws / "decision-1" / "rev_b.svg").write_text("<svg>edited</svg>")
        s = signoff.status("c1")
        self.assertEqual(s["state"], "draft")
        self.assertEqual(s["changed_since_approval"], ["decision-1/rev_b.svg"])

    def test_disposition_after_review_returns_to_draft(self):
        signoff.dispose("c1", "electrical", "accepted_risk", "r", "Ada")
        signoff.review("c1", "Ada")
        self.assertEqual(signoff.dispose("c1", "electrical", "must_fix", "changed my mind", "Ada")["state"], "draft")
        with self.assertRaisesRegex(ValueError, "not a failed check"):
            signoff.dispose("c1", "controls", "accepted_risk", "r", "Ada")

    def test_open_item_evidence_is_audited_but_does_not_close_the_gate(self):
        s = signoff.evidence("c1", "controls", "Vendor datasheet received", "Ada")
        self.assertEqual(s["pack_design"]["answer_index"], 2)
        self.assertEqual(s["evidence"]["controls"][0]["note"], "Vendor datasheet received")
        self.assertEqual([r["id"] for r in s["checks"]["open"]], ["controls"])
        self.assertTrue(audit.verify("c1")["ok"])
        with self.assertRaisesRegex(ValueError, "not a failed or open check"):
            signoff.evidence("c1", "missing", "x", "Ada")


if __name__ == "__main__":
    unittest.main()
