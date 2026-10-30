"""RO (WaterTAP) proposal changes: trains, added train, membrane, area, pumps, energy recovery, operating scenarios.
Validation runs without WaterTAP; the verify tests re-solve swro_brownsville in WaterTAP (no AI)."""
import unittest

from plantagent import ro, ro_changes
from plantagent.plant import PlantWorkspace, patch

EV = {"physical_change": "test", "rating_source": "vendor quote to confirm (test)"}
SPEC = {"feed": {"flow_m3_h": 100, "TDS_g_L": 35, "T_C": 20}, "trains": {"installed": 3, "in_service": 2},
        "hp_pump": {"id": "P1", "max_bar": 70, "max_kW": 500, "P_out_bar": 60}, "energy_recovery": {"type": "turbine", "efficiency": 0.85},
        "stages": [{"id": "S1", "area_m2": 1000, "max_feed_pressure_bar": 70, "max_flux_lmh": 15, "recovery": 0.4}],
        "target_TDS_g_L": 0.5, "min_overall_recovery": 0.4}


class Validation(unittest.TestCase):
    def test_limit_definitions_never_change(self):
        for path in ("stages.S1.max_flux_lmh", "target_TDS_g_L", "stages.S1.recovery"):
            with self.subTest(path=path):  # recovery is the design minimum here: HP discharge is fixed
                self.assertTrue(ro_changes.change_errors(SPEC, [{"path": path, "value": 1, **EV}]))
        solve_p = {**SPEC, "hp_pump": {k: v for k, v in SPEC["hp_pump"].items() if k != "P_out_bar"}}
        self.assertFalse(ro_changes.change_errors(solve_p, [{"path": "stages.S1.recovery", "value": 0.42}]))

    def test_physical_needs_evidence_operating_does_not(self):
        for path, value in (("hp_pump.max_kW", 900), ("stages.S1.A_m_per_Pa_s", 3e-12), ("stages.S1.area_m2", 1200),
                            ("energy_recovery.efficiency", 0.9), ("trains.installed", 4), ("second_pass", {"fraction": 0.5})):
            with self.subTest(path=path):
                self.assertTrue(ro_changes.change_errors(SPEC, [{"path": path, "value": value}]))
                self.assertFalse(ro_changes.change_errors(SPEC, [{"path": path, "value": value, **EV}]))
        for path, value in (("feed.T_C", 10), ("feed.TDS_g_L", 40), ("trains.in_service", 3), ("hp_pump.P_out_bar", 65)):
            with self.subTest(path=path):
                self.assertFalse(ro_changes.change_errors(SPEC, [{"path": path, "value": value}]))

    def test_structure(self):
        self.assertTrue(ro_changes.change_errors(SPEC, [{"reroute": {"unit": "S1", "field": "in", "value": "x"}}]))
        self.assertTrue(ro_changes.change_errors(SPEC, [{"path": "stages.S1.vessels", "value": 10, **EV}]))  # sized by area_m2
        self.assertTrue(ro_changes.change_errors(SPEC, [{"add_unit": {"id": "T2", "type": "ro_train"}}]))  # no rating_source
        t = patch(SPEC, [{"add_unit": {"id": "T2", "type": "ro_train", "count": 2, "stage": {"max_feed_pressure_bar": 90},
                                       "hp_pump": {"P_out_bar": 85, "max_bar": 90}}, "rating_source": "quote"}])["added_trains"][0]
        self.assertEqual((t["count"], t["stages"][0]["id"], t["stages"][0]["max_feed_pressure_bar"], t["hp_pump"]["id"]), (2, "T2-s1", 90, "T2-HP"))
        self.assertEqual(SPEC["stages"][0]["max_feed_pressure_bar"], 70)  # the existing train keeps its rating


@unittest.skipUnless(ro.available(), "WaterTAP unavailable")
class Brownsville(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = PlantWorkspace("swro_brownsville")

    def verify(self, changes, tag="RO-201"):
        v = self.w.verify({"tag": tag, "title": "test", "changes": changes})
        self.assertFalse((v.get("calculation") or {}).get("errors"), v.get("calculation"))
        return v, {(c["id"], c["check"]): c for c in v["over_limits_at_target"]}

    def test_plant_is_trains(self):
        self.assertEqual(self.w.spec["trains"], {"installed": 6, "in_service": 5})
        r = self.w.state(1.0)
        self.assertTrue(any(c["id"] == "trains" for c in r["checks"]))
        self.assertAlmostEqual(r["streams"]["intake"]["flow_m3_h"], self.w.spec["feed"]["flow_m3_h"], delta=0.1)

    def test_spare_train_in_service_raises_plant_recovery(self):
        v, over = self.verify([{"path": "trains.in_service", "value": 6}])
        self.assertLess(over[("plant", "overall recovery vs minimum")]["utilisation"], 1.271)
        self.assertIn(("RO-201-stage2", "minimum recovery vs design"), {(c["id"], c["check"]) for c in v["still_over"]})

    def test_installed_train_and_area_and_membrane(self):
        for changes in ([{"path": "trains.installed", "value": 7, **EV}, {"path": "trains.in_service", "value": 6}],
                        [{"path": "stages.RO-201-stage2.area_m2", "value": 35000, **EV}],
                        [{"path": "stages.RO-201-stage1.A_m_per_Pa_s", "value": 3e-12, **EV}],
                        [{"path": "energy_recovery.efficiency", "value": 0.9, **EV}],
                        [{"path": "feed.T_C", "value": 24}], [{"path": "hp_pump.P_out_bar", "value": 70}]):
            with self.subTest(changes=changes[0]["path"]):
                v, over = self.verify(changes)
                self.assertTrue(over)  # the cold, salty corner still fails: none of these alone is the fix

    def test_added_higher_pressure_train_has_its_own_checks(self):
        v, over = self.verify([{"add_unit": {"id": "RO-207", "type": "ro_train", "stage": {"max_feed_pressure_bar": 95},
                                             "hp_pump": {"P_out_bar": 90, "max_bar": 95, "max_kW": 4290}},
                                "rating_source": "vendor quote to confirm (test)"}])
        ids = {c["id"] for c in v["calculation"]["checks"]}
        self.assertTrue({"RO-207-s1", "RO-207-s2"} <= ids, ids)
        self.assertEqual(v["new_equipment"][0]["limits"]["max_feed_pressure_bar"], 95)

    def test_hp_pump_replacement_alone_breaks_the_vessel_rating(self):
        v, _ = self.verify([{"path": "hp_pump.max_bar", "value": 95, **EV}, {"path": "hp_pump.max_kW", "value": 4290, **EV},
                            {"path": "hp_pump.P_out_bar", "value": 85}], tag="P-201")
        self.assertFalse(v["verified"])
        self.assertIn(("RO-201-stage1", "feed pressure vs max"), {(c["id"], c["check"]) for c in v["breaks"]})

    def test_limit_redefinition_refused(self):
        v = self.w.verify({"tag": "RO-201", "changes": [{"path": "stages.RO-201-stage1.max_flux_gfd", "value": 20}]})
        self.assertFalse(v["verified"])
        self.assertIn("redefines a limit", v["unverified_reason"])


if __name__ == "__main__":
    unittest.main()
