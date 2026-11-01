"""Discipline drafts for a plant without case files: no solver, no model call."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import drafts, economics

SPEC = {"feeds": {"F1": {"T_C": 50, "P_bar": 1.5, "m3_h": 18.0}, "CW": {"T_C": 25, "P_bar": 4.0, "m3_h": 20.0, "utility": True}},
        "units": [{"id": "P1", "type": "pump", "in": "F1", "out": "S2", "dP_bar": 1.0, "kind": "centrifugal"},
                  {"id": "P2", "type": "pump", "in": "S3", "out": "S4", "dP_bar": 3.5, "kind": "positive_displacement"},
                  {"id": "E1", "type": "hx", "U_W_m2K": 600, "area_m2": 46.8},
                  {"id": "K1", "type": "compressor", "in": "V1", "out": "V2", "P_out_bar": 3.0, "eff_pct": 75}],
        "limits": {"P1": {"max_m3_h": 25, "max_kW": 2.2, "max_head_m": 12}}}
RESULT = {"units": {"P1": {"m3_h": 18.0, "head_m": 10.5, "kW": 0.71}, "P2": {"m3_h": 40, "head_m": 36, "kW": 5.6, "kind": "positive_displacement"},
                    "K1": {"kW": 900.0}},
          "streams": {"V1": {"m3_h": 50000, "P_bar": 1.5, "T_C": 110, "kg_h": 40000}, "V2": {"P_bar": 3.0}}}


class W:
    name = "draft_stub"
    cfg = {"target_scale": 1.2}
    basis = "Site datasheet: P1 rated 25 m3/h at 12 m, motor 2.2 kW.\n" + "-" * 150 + "\nPerformance test: E1 U 600 W/m2K."
    spec = SPEC
    built = {"spec": SPEC, "result": RESULT}


class DraftsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "cases" / W.name).mkdir(parents=True)
        p = mock.patch.object(drafts, "ROOT", self.root)
        p.start()
        self.addCleanup(p.stop)

    def test_provenance_documented_vs_assumed(self):
        p = drafts.provenance(W())
        self.assertEqual(p["limits.P1.max_kW"]["provenance"], "datasheet")
        self.assertEqual(p["units.E1.U_W_m2K"]["provenance"], "documented")
        self.assertEqual(p["units.E1.area_m2"]["provenance"], "muse_default")
        drafts.confirm(W.name, "units.E1.area_m2", 46.8)
        self.assertEqual(drafts.provenance(W())["units.E1.area_m2"]["provenance"], "engineer_confirmed")

    def test_electrical_sizes(self):
        e = drafts.draft_electrical(W())
        m = {x["unit"]: x for x in e["motors"]}
        self.assertEqual(m["P1"]["kw"], 2.2)                        # datasheet rating kept
        self.assertEqual(m["P2"]["kw"], 7.5)                        # 5.6 x 1.15 = 6.44 -> next IEC 7.5
        self.assertEqual((m["K1"]["kw"], m["K1"]["bus"]), (1120, "MV"))  # 900 x 1.15 = 1035 -> 1120, MV
        tx = e["transformers"][0]
        lv_kva = sum(x["kw"] / x["eff"] / x["pf"] for x in e["motors"] if x["bus"] == "LV")
        self.assertGreaterEqual(tx["sn_mva"] * 1000, 1.25 * lv_kva)
        self.assertTrue(all(c in e["cable_types"] for c in (x["cable"]["type"] for x in e["motors"])))

    def test_curves_skip_pd_and_anchor(self):
        c = drafts.draft_curves(W())
        self.assertNotIn("P2", c["units"])
        self.assertEqual(c["units"]["P1"]["design"]["q_m3_h"], 25)
        self.assertAlmostEqual(c["units"]["K1"]["design"]["pr"], 2.0)
        self.assertEqual(c["units"]["K1"]["surge_q"], 0.62)

    def test_economics_correlation_and_open_price(self):
        e = drafts.draft_economics(W())
        self.assertIsNone(e["product"]["price"]["value"])
        self.assertEqual(e["throughput"]["base"], 432.0)
        self.assertEqual(e["utilities"][0]["price"]["value"], 0.05)
        ln = economics._change_lines({"add_unit": {"id": "P9", "type": "pump"}}, {"P9": {"m3_h": 36}}, {}, corr=e["capex_correlations"])[0]
        want = (8000 + 240 * 10 ** 0.9) * 797.9 / 532.9 * 4.74
        self.assertEqual(ln["usd"], round(want, -3))

    def test_uncertainty_and_envelope(self):
        u = drafts.draft_uncertainty(W())
        self.assertIn("units.E1.area_m2", [i["path"] for i in u["inputs"]])
        self.assertTrue(all(i["kind"] == "assumed" for i in u["inputs"]))
        env = drafts.draft_envelope(W())
        self.assertEqual([s["scale"] for s in env["scenarios"][:2]], [1.32, 1.08])
        self.assertTrue(all(not str(c["path"]).startswith("limits.") for s in env["scenarios"] for c in s.get("changes") or []))

    def test_case_file_wins_over_draft(self):
        w = W()
        with mock.patch.object(drafts, "provenance", return_value={}):
            out = drafts.ensure(w)
        self.assertEqual(out["electrical.json"], "draft")
        self.assertTrue(drafts.is_draft(drafts.case_file(w.name, "electrical.json")))
        (self.root / "cases" / w.name / "electrical.json").write_text(json.dumps({"motors": []}))
        self.assertFalse(drafts.is_draft(drafts.case_file(w.name, "electrical.json")))


if __name__ == "__main__":
    unittest.main()
