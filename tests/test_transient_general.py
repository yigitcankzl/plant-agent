"""General start-up and separator checks; no model or paid API calls."""
import unittest
from unittest import mock

from plantagent import drafts, electrical, transient
from plantagent.designchecks import separation_checks
from plantagent.plant import PlantWorkspace


class GeneralTransientTests(unittest.TestCase):
    def test_chem_c01_checks_every_pump(self):
        w = PlantWorkspace("chem_c01")
        drafts.ensure(w, refresh=True)
        solved = w.built["result"]

        def electrical_start(cfg, solved, changes=None, overrides=None, scale=1.0):
            unit = overrides[0]["unit"]
            return {"start": {"unit": unit, "terminal_dip_percent": 3.0}}

        with mock.patch.object(electrical, "check", side_effect=electrical_start):
            rows = transient.startup_checks(w, w.spec, solved)
        checks = {r["check"]: r for r in rows}
        for unit in ("P4711", "P4712"):
            self.assertEqual(checks[f"startup.{unit}.voltage"]["status"], "pass")
            self.assertIn(checks[f"startup.{unit}.acceleration"]["status"], ("pass", "fail"))
        self.assertFalse(any(k.endswith(".surge") for k in checks))

    def test_flash_checks_without_an_electrical_grid(self):
        spec = {"units": [{"id": "V-1", "type": "flash", "in": "F", "vapor": "V", "liquid": "L"}],
                "limits": {"V-1": {"diameter_m": 2.0, "K_factor_m_s": 0.1,
                                      "liquid_volume_m3": 1.0, "min_residence_min": 5}}}
        solved = {"streams": {"V": {"kg_h": 100, "m3_h": 100, "vapour_frac": 1.0},
                               "L": {"kg_h": 900, "m3_h": 1, "vapour_frac": 0.0}},
                  "units": {"V-1": {"type": "flash"}}}
        rows = separation_checks(spec, solved)
        self.assertEqual({r["check"] for r in rows}, {"separation.V-1.vapour_velocity", "separation.V-1.residence"})
        self.assertTrue(all(r["status"] == "pass" for r in rows))

    def test_column_without_internals_stays_open(self):
        rows = separation_checks({"units": [{"id": "C-1", "type": "distillation"}]},
                                 {"streams": {}, "units": {"C-1": {"type": "distillation"}}})
        self.assertEqual(rows[0]["status"], "open")
        self.assertIn("needs internals", rows[0]["title"])

    def test_missing_motor_and_compressor_curve_are_explicit(self):
        w = type("Workspace", (), {"name": "no-data"})()
        spec = {"units": [{"id": "K-1", "type": "compressor", "in": "A", "out": "B"}]}
        with mock.patch.object(electrical, "config", return_value=None), \
             mock.patch("plantagent.curves.overlay", return_value=None):
            rows = transient.startup_checks(w, spec, {"streams": {}, "units": {}})
        self.assertEqual([r["status"] for r in rows], ["open", "open", "open"])
        self.assertIn("needs: motor list", rows[0]["title"])
        self.assertIn("needs: curve", rows[2]["title"])


if __name__ == "__main__":
    unittest.main()
