"""Assumptions (provenance + engineer confirmation), input uploads, task types and the DEXPI drawing on new projects."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import assumptions as A
from plantagent import web

REPO = Path(__file__).resolve().parent.parent


class AssumptionsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "cases" / "p").mkdir(parents=True)
        (self.root / "cases" / "p" / "case.json").write_text('{"kind": "process", "target_scale": 1.2}')
        (self.root / "cases" / "p" / "electrical.json").write_text(json.dumps({
            "note": "every value ILLUSTRATIVE unless marked",
            "transformers": [{"id": "TX-1", "sn_mva": 2.5, "source": "basis.md p. 3"}],
            "motors": [{"id": "M-1", "kw": {"value": 75, "unit": "kW", "source": "vendor datasheet"}, "eff": 0.9}]}))
        (self.root / "runs" / "ws" / "p" / "drafts").mkdir(parents=True)
        (self.root / "runs" / "ws" / "p" / "drafts" / "economics.json").write_text(json.dumps(
            {"capex": {"value": 1.5e6, "unit": "USD", "source": "muse_default"}, "years": 10}))
        self.p = mock.patch.object(A, "ROOT", self.root)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def by_id(self):
        return {i["id"]: i for i in A.collect("p")}

    def test_classify(self):
        self.assertEqual(A.classify("ILLUSTRATIVE", "documented"), "assumed")
        self.assertEqual(A.classify("vendor datasheet", "assumed"), "datasheet")
        self.assertEqual(A.classify("basis.md: 18 m3/h", "assumed"), "documented")
        self.assertEqual(A.classify("muse_default", "assumed"), "muse_default")
        self.assertEqual(A.classify("", "assumed"), "assumed")

    def test_collect_sources(self):
        i = self.by_id()
        self.assertEqual(i["electrical:transformers.TX-1.sn_mva"]["source"], "documented")
        self.assertEqual(i["electrical:motors.M-1.kw"]["source"], "datasheet")
        self.assertEqual(i["electrical:motors.M-1.eff"]["source"], "assumed")  # no source anywhere: never claimed as documented
        self.assertEqual(i["drafts/economics:capex"]["source"], "muse_default")
        self.assertEqual(i["drafts/economics:years"]["source"], "muse_default")
        self.assertNotIn("case:target_scale", i)

    def test_confirm_and_edit(self):
        A.confirm("p", "electrical:motors.M-1.eff", user="eng")
        i = self.by_id()["electrical:motors.M-1.eff"]
        self.assertEqual((i["source"], i["value"]), ("engineer_confirmed", 0.9))
        # shipped case file is not rewritten; the log carries the new value
        A.confirm("p", "electrical:transformers.TX-1.sn_mva", 3.15)
        self.assertEqual(self.by_id()["electrical:transformers.TX-1.sn_mva"]["value"], 3.15)
        self.assertIn('"sn_mva": 2.5', (self.root / "cases" / "p" / "electrical.json").read_text())
        # drafts are rewritten in place
        A.confirm("p", "drafts/economics:capex", 2e6)
        d = json.loads((self.root / "runs/ws/p/drafts/economics.json").read_text())
        self.assertEqual(d["capex"], {"value": 2e6, "unit": "USD", "source": "engineer_confirmed"})
        self.assertEqual(len(A.log("p")), 3)
        with self.assertRaises(ValueError):
            A.confirm("p", "electrical:nope")
        with self.assertRaises(ValueError):
            A.confirm("p", "drafts/economics:years", float("nan"))

    def test_bulk_confirmation_logs_every_value(self):
        values = [{"id": "electrical:motors.M-1.eff", "value": 0.91},
                  {"id": "electrical:motors.M-1.kw", "value": 75}]
        entries = A.confirm_many("p", values, user="eng")
        self.assertEqual(len(entries), 2)
        self.assertEqual([x["id"] for x in A.log("p")], [x["id"] for x in values])
        before = len(A.log("p"))
        with self.assertRaisesRegex(ValueError, "one file/group"):
            A.confirm_many("p", [values[0], {"id": "drafts/economics:years", "value": 10}])
        self.assertEqual(len(A.log("p")), before)  # the whole bulk request is validated before its first write

    def test_sensitivity_prefers_stored_uncertainty_and_only_ranks_assumptions(self):
        model = self.root / "runs/ws/p/model.json"
        (model.parent / "uncertainty.json").write_text(json.dumps({
            "inputs": [{"path": "units.K.eff_pct", "kind": "assumed", "band_pct": 10, "source": "model assumption"},
                       {"path": "limits.K.max_kW", "kind": "documented", "band_pct": 3}],
            "drivers": [{"path": "limits.K.max_kW", "effect": 0.4}, {"path": "units.K.eff_pct", "effect": 0.05}]}))
        w = type("W", (), {"model_file": model})()
        ranked = A.sensitivity(w)
        self.assertEqual(ranked["method"], "stored uncertainty re-solves")
        self.assertEqual([x["path"] for x in ranked["rows"]], ["units.K.eff_pct"])
        self.assertIn("+5.0 points", ranked["rows"][0]["change"])

    def test_sensitivity_falls_back_to_deterministic_plus_minus_ten_percent(self):
        (self.root / "cases/p/uncertainty.json").write_text(json.dumps(
            {"inputs": [{"path": "units.K.eff_pct", "kind": "assumed"}]}))
        model = self.root / "runs/ws/p/model.json"
        spec = {"compounds": ["Water"], "package": "Steam Tables", "feeds": {},
                "units": [{"id": "K", "type": "compressor", "eff_pct": 75}], "limits": {}}

        class W:
            name, model_file, cfg = "p", model, {"target_scale": 1.2}
            def __init__(self):
                self.spec = spec
            def _solve(self, changed, scale):
                eff = changed["units"][0]["eff_pct"]
                return {"checks": [{"id": "K", "check": "power vs motor", "utilisation": 0.98 * eff / 75}]}

        ranked = A.sensitivity(W())
        self.assertEqual(ranked["method"], "deterministic ±10 % what-if")
        self.assertEqual(ranked["rows"][0]["path"], "units.K.eff_pct")
        self.assertEqual(ranked["rows"][0]["change"], "+10 % → limit 98 → 108 %")

    def test_uploads(self):
        r = A.upload("p", "motors", b"tag,kw,start\nP-101,75,dol\nK-201,2400,vfd\n")
        self.assertEqual(r["rows"], 2)
        i = self.by_id()
        self.assertEqual(i["inputs/motors:motors.K-201.kw"]["source"], "datasheet")
        A.upload("p", "curves", b"tag,flow_m3h,head_m\nP-101,0,60\nP-101,50,55\nP-101,100,40\n")
        self.assertIn("inputs/curves:curves.P-101.points.2.head_m", self.by_id())
        for kind, data in (("motors", b"tag,power\nP,1\n"), ("motors", b"tag,kw\nP,abc\n"), ("motors", b"tag,kw,start\nP,1,star\n"),
                           ("curves", b"tag,flow_m3h,head_m\nP,0,1\nP,0,1\nP,1,1\n"), ("datasheet", b"not a pdf"), ("bogus", b"")):
            with self.assertRaises(ValueError, msg=(kind, data)):
                A.upload("p", kind, data)
        r = A.upload("p", "datasheet", b"%PDF-1.4 x", "../../evil name.pdf")
        self.assertEqual(r["file"], "inputs/datasheets/evil_name.pdf")
        self.assertTrue((self.root / "runs/ws/p/inputs/datasheets/evil_name.pdf").exists())


class NewProjectTest(unittest.TestCase):
    def test_task_types_offer_questions(self):
        for key, (label, qs) in web.TASK_TYPES.items():
            self.assertEqual(len(qs), 4)
            self.assertNotIn("incident", label)  # incident pages have their own questions
        self.assertEqual(web.TASK_TYPES["capacity"][1][0].format(pct=20), "What limits +20% throughput?")

    def test_bad_task_type_rejected_before_anything_is_written(self):
        with self.assertRaisesRegex(ValueError, "task_type"):
            web.new_project({"title": "x" * 8, "question": "q" * 20, "data_sheet": "d" * 300, "task_type": "magic"})

    @unittest.skipUnless((REPO / ".venv-pid/bin/python").exists() or os.getenv("PID_RENDER_PYTHON"), "pyDEXPI renderer not installed")
    def test_dexpi_rendered_to_svg(self):
        out = Path(tempfile.mkdtemp()) / "pid.svg"
        self.assertIsNone(web.render_pid_svg(REPO / "cases/chem_c01/C01V04-VER.EX01.xml", out))
        self.assertIn('data-tag="', out.read_text())

    def test_missing_renderer_is_reported_not_raised(self):
        with mock.patch.dict(os.environ, {"PID_RENDER_PYTHON": "/nonexistent/python"}):
            self.assertIn("not installed", web.render_pid_svg(REPO / "cases/chem_c01/C01V04-VER.EX01.xml", Path("/tmp/x.svg")))


if __name__ == "__main__":
    unittest.main()
