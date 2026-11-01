"""Proposal changes outside the process model (plantagent/overlays.py): electrical one-line, start-up screen, curve rating."""
import copy
import json
import unittest
from pathlib import Path

from plantagent import curves, electrical, overlays, process, transient
from plantagent.plant import patch

ROOT = Path(__file__).resolve().parent.parent
K202 = {"add_unit": {"id": "K-202", "type": "compressor", "in": "S3001_K202", "out": "S3002_K202", "P_out_bar": 3.08, "eff_pct": 75},
        "limits": {"max_kg_h": 55000, "max_kW": 2400}, "rating_source": "test"}


class OverlayPaths(unittest.TestCase):
    def test_errors_refuse_unknown_out_of_range_and_unevidenced(self):
        ok = [{"path": "electrical.TX-1.sn_mva", "value": 3.15, "physical_change": "new 3.15 MVA transformer"},
              {"path": "electrical.TX-1.tap_percent", "value": 2.5},
              {"path": "electrical.K-202.start", "value": "VFD", "physical_change": "VFD"},
              {"path": "electrical.P-201.cable", "value": "MV-3x185Al", "physical_change": "bigger cable"},
              {"path": "transient.startup.anti_surge_capacity_frac", "value": 0.75, "physical_change": "larger valve"},
              {"path": "transient.startup.Kp", "value": 3.0}]
        self.assertEqual(overlays.errors("salt_mvr", ok, ok + [K202]), [])
        bad = [{"path": "electrical.TX-9.sn_mva", "value": 3, "physical_change": "x"},
               {"path": "electrical.TX-1.sn_mva", "value": 2.0, "physical_change": "x"},  # not larger
               {"path": "electrical.TX-1.sn_mva", "value": 3.15},                           # no physical_change
               {"path": "electrical.K-999.start", "value": "VFD", "physical_change": "x"},
               {"path": "electrical.K-202.start", "value": "STAR", "physical_change": "x"},
               {"path": "transient.startup.Kp", "value": 99},
               {"path": "transient.startup.anti_surge_capacity_frac", "value": 0.8}]          # valve without physical_change
        self.assertEqual(len(overlays.errors("salt_mvr", bad, bad + [K202])), len(bad))

    def test_patch_leaves_the_process_model_alone(self):
        spec = json.loads((ROOT / "runs/ws/salt_mvr/model.json").read_text())["spec"]
        ov = [{"path": "electrical.TX-1.sn_mva", "value": 3.15}, {"path": "transient.startup.Kp", "value": 3.0}]
        self.assertEqual(patch(spec, ov), spec)
        self.assertEqual(overlays.split(ov + [K202]), ([K202], ov))

    def test_transient_params_fix_the_anti_surge_finding(self):
        cv = json.loads((ROOT / "cases/salt_mvr/curves.json").read_text())["units"]
        art = next((ROOT / "runs/ws/salt_mvr/artifacts").glob("*k-202-start-up-transient"))
        g0, g1 = json.loads((art / "transient.json").read_text())["boilup_kg_h"]
        base = transient.run(cv["K-201"], cv["K-202"], g0, g1)
        fixed = transient.run(cv["K-201"], cv["K-202"], g0, g1, **overlays.transient_params(
            [{"path": "transient.startup.anti_surge_capacity_frac", "value": 0.75}]))
        surge = lambda r: next(c for c in r["checks"] if c["check"].startswith("no surge"))["pass"]  # noqa: E731
        self.assertFalse(surge(base))
        self.assertTrue(surge(fixed))

    def test_curve_follows_a_larger_rating(self):
        c = json.loads((ROOT / "cases/salt_mvr/curves.json").read_text())["units"]["K-202"]
        spec = {"limits": {"K-202": {"max_kg_h": 66000}}}
        self.assertAlmostEqual(curves.scaled(c, spec, "K-202")["design"]["q_m3_h"], c["design"]["q_m3_h"] * 1.2)
        self.assertIs(curves.scaled(c, {"limits": {"K-202": {"max_kg_h": 55000}}}, "K-202"), c)

    @unittest.skipUnless(electrical.available(), "pandapower venv missing")
    def test_electrical_overlay_replaces_transformer_and_starter(self):
        cfg = electrical.config("salt_mvr")
        before = electrical.check(cfg, {}, [K202])
        after = electrical.check(cfg, {}, [K202, {"path": "electrical.TX-1.sn_mva", "value": 4.0, "physical_change": "x"},
                                           {"path": "electrical.K-202.start", "value": "VFD", "physical_change": "x"}])
        tx = lambda r: next(t for t in r["transformers"] if t["id"] == "TX-1")["loading_percent"]  # noqa: E731
        self.assertLess(tx(after), tx(before))
        self.assertEqual(after["start"]["method"], "VFD")
        self.assertTrue(any("TX-1 2.5 → 4 MVA" in u for u in after["upgrades"]))
        self.assertEqual(cfg["transformers"][0]["sn_mva"], 2.5)  # the case file is not changed


@unittest.skipUnless(process.available(), "DWSIM unavailable")
class ChecksForDesign(unittest.TestCase):
    def test_salt_design_rows(self):
        from plantagent import designchecks, revb
        from plantagent.plant import PlantWorkspace
        w = PlantWorkspace("salt_mvr")
        rows = designchecks.checks_for_design(w, w.answers.index(revb.design_answer(w.answers)))
        by = {r["check"]: r for r in rows}
        self.assertTrue({"process", "curves", "startup"} <= set(by))
        self.assertTrue(all(r["status"] in ("pass", "fail", "open") and r["engine"] and r["title"] for r in rows))
        self.assertEqual(by["process"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
