"""Engineer uploads feed the discipline files the checks read: inputs > case file > draft. No solver, no model call."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import assumptions as A
from plantagent import curves, drafts

REPO = Path(__file__).resolve().parent.parent
CURVES = {"basis": "ILLUSTRATIVE", "units": {"K-1": {"kind": "compressor", "design": {"q_m3_h": 1000, "pr": 1.8, "T_in_C": 115, "eff_pct": 75},
                                                     "points": [[0.6, 1.1, 0.9], [1.0, 1.0, 1.0], [1.2, 0.8, 0.9]], "surge_q": 0.6,
                                                     "stonewall_q": 1.2, "variable_speed": True}}}
ELEC = {"buses": [{"id": "MV", "vn_kv": 6.6}, {"id": "LV", "vn_kv": 0.4}], "cable_types": {"LV-4x95Cu": [0.193, 0.232]},
        "motors": [{"id": "M-K-1", "unit": "K-1", "bus": "MV", "kw": 900, "start": "DOL", "cable": {"type": "MV-3x95Cu", "length_km": 0.2}}]}


class PrecedenceTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "cases" / "p").mkdir(parents=True)
        (self.root / "cases" / "p" / "curves.json").write_text(json.dumps(CURVES))
        d = self.root / "runs" / "ws" / "p" / "drafts"
        d.mkdir(parents=True)
        (d / "electrical.json").write_text(json.dumps({**ELEC, "draft": True}))
        for m in (A, drafts):
            p = mock.patch.object(m, "ROOT", self.root)
            p.start()
            self.addCleanup(p.stop)

    def test_order_inputs_case_draft(self):
        self.assertEqual(drafts.case_file("p", "curves.json", self.root)["basis"], "ILLUSTRATIVE")  # case over nothing
        self.assertTrue(drafts.is_draft(drafts.case_file("p", "electrical.json", self.root)))  # draft when no case file
        A.upload("p", "curves", b"# ILLUSTRATIVE vendor curve\ntag,flow_m3h,head_m,efficiency_pct\nK-1,500,12900,70\n"
                                b"K-1,1000,11650,80\nK-1,1200,9500,72\n")
        cfg = drafts.case_file("p", "curves.json", self.root)
        k = cfg["units"]["K-1"]
        self.assertEqual(cfg["uploaded"], ["K-1"])
        self.assertEqual((k["design"]["q_m3_h"], k["design"]["eff_pct"], k["surge_q"], k["stonewall_q"]), (1000, 80, 0.5, 1.2))
        self.assertEqual(k["design"]["T_in_C"], 115)  # the case's suction state is kept
        self.assertAlmostEqual(curves.head_kJ_kg(k["design"]["pr"], 115) * 1000 / 9.80665, 11650, delta=1)  # vendor head kept
        self.assertTrue(k["variable_speed"])
        self.assertIn("ILLUSTRATIVE vendor curve", k["basis"])
        self.assertTrue((self.root / "runs/ws/p/inputs/curves.csv").exists())  # raw upload kept
        self.assertIn('"surge_q": 0.6', (self.root / "cases/p/curves.json").read_text())  # case file untouched
        self.assertEqual(drafts.label(cfg), "vendor data (uploaded, ILLUSTRATIVE) for K-1: ")  # the file's own label shows
        self.assertEqual(drafts.label(cfg, "K-1"), "vendor data (uploaded, ILLUSTRATIVE): ")

    def test_motor_list_merges_into_one_line(self):
        r = A.upload("p", "motors", b"tag,kw,voltage_kv,start,cable_m\nK-1,1200,6.6,vfd,300\nP-9,15,0.4,dol,50\n")
        self.assertEqual(r["applied_to"], {"electrical.json": ["K-1", "P-9"]})
        cfg = drafts.case_file("p", "electrical.json", self.root)
        m = {x["unit"]: x for x in cfg["motors"]}
        self.assertEqual((m["K-1"]["kw"], m["K-1"]["start"], m["K-1"]["cable"]["length_km"]), (1200, "VFD", 0.3))
        self.assertEqual((m["P-9"]["bus"], m["P-9"]["start"]), ("LV", "DOL"))
        self.assertEqual(drafts.label(cfg, "K-1"), f"{drafts.VENDOR}: ")
        self.assertEqual(drafts.label(cfg, "X"), f"{drafts.DRAFT}: ")  # units not uploaded stay draft

    def test_pump_curve_min_flow(self):
        c = drafts.vendor_curve([{"flow_m3h": 10, "head_m": 60}, {"flow_m3h": 50, "head_m": 55}, {"flow_m3h": 100, "head_m": 40}])
        self.assertEqual((c["kind"], c["design"]["q_m3_h"], c["min_flow_q"]), ("pump", 50, 0.2))

    def test_demo_curve_is_labelled_and_valid(self):
        data = (REPO / "cases/salt_mvr/demo_inputs/K-202_vendor_curve_ILLUSTRATIVE.csv").read_bytes()
        self.assertTrue(data.startswith(b"# ILLUSTRATIVE"))
        A.upload("p", "curves", data)
        self.assertIn("K-202", drafts.case_file("p", "curves.json", self.root)["uploaded"])


if __name__ == "__main__":
    unittest.main()
