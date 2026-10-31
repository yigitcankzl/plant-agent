import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import audit, hazop


class Workspace:
    def __init__(self, root):
        self.name = "sample"
        self.cfg = {"target_scale": 1.2, "model_aliases": {}}
        self.model = "muse-test"
        self.model_file = root / "runs/ws/sample/model.json"
        self.model_file.parent.mkdir(parents=True)
        self.spec = {"feeds": {"F": {"T_C": 40, "P_bar": 5, "kg_h": 1000}},
                     "units": [{"id": "U", "type": "heater", "in": "F", "out": "S", "efficiency": 0.9},
                               {"id": "V", "type": "vessel", "in": "S", "out": "P"}],
                     "limits": {"U": {"max_kW": 100}}}
        self.built = {"label": "model", "spec": self.spec}
        self.answers = [{"headline": "change U", "combined": {"reaches_target": True}, "proposals": [
            {"verified": True, "tag": "U", "changes": [{"path": "units.U.efficiency", "value": 0.95}]}]}]
        self.revisions = []

    def names(self):
        return {}

    def _solve(self, spec, scale=1):
        feed = spec["feeds"]["F"]
        return {"errors": [], "units": {"U": {"P_out_bar": feed["P_bar"], "T_out_C": feed["T_C"] + 20},
                                          "V": {"P_bar": feed["P_bar"], "T_C": feed["T_C"] + 18}},
                "checks": [{"id": "U", "check": "duty", "utilisation": scale / 1.2}]}


def judgements(payload):
    return [{"key": row["key"], "cause": "control or equipment failure", "consequence": "process deviation",
             "safeguards": ["operator alarm"]} for row in payload["deviations"]]


class HazopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.w = Workspace(self.root)
        patcher = mock.patch.object(hazop, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(audit, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_nodes_and_standard_guidewords_are_generated(self):
        nodes = hazop.nodes(self.w)
        self.assertEqual({n["id"] for n in nodes}, {"U", "V"})
        rows = hazop.deviations(nodes)
        self.assertEqual(len(rows), 22)
        self.assertEqual({(r["guideword"], r["parameter"]) for r in rows}, set((g, p) for p, g in hazop.GUIDEWORDS))

    def test_computable_deviations_are_resolved(self):
        study = hazop.generate(self.w, proposer=judgements)
        row = next(r for r in study["rows"] if r["node_id"] == "U" and r["deviation"] == "more pressure")
        self.assertEqual(row["basis"], "computed")
        self.assertEqual(row["calculation"]["result"]["pressure_bar"], 5.5)
        self.assertEqual(row["calculation"]["result"]["max_utilisation"], 1.0)

    def test_draft_and_row_labels_separate_calculation_from_judgement(self):
        study = hazop.generate(self.w, proposer=judgements)
        self.assertEqual(study["label"], "DRAFT — not a substitute for a facilitated HAZOP team session")
        self.assertEqual({r["basis"] for r in study["rows"]}, {"computed", "judgement (LLM)"})
        self.assertEqual(study["summary"]["rows"], len(study["rows"]))
        self.assertEqual(json.loads(self.w.model_file.with_name("hazop.json").read_text())["content_hash"], study["content_hash"])

    def test_aggregate_budget_blocks_a_paid_call(self):
        payload = hazop.content(self.w)
        with mock.patch.object(hazop, "spend_status", return_value={"total_usd": 10, "task_usd": 0,
                                                                    "overall_cap_usd": 5, "task_cap_usd": 3}), \
                mock.patch.object(hazop.llm, "CACHE", self.root / "empty-cache"), \
                mock.patch.object(hazop.llm, "complete") as complete:
            with self.assertRaisesRegex(RuntimeError, "aggregate Muse budget"):
                hazop._muse(payload, "muse-spark-1.3-contributor")
            complete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
