"""Heat-exchanger detail rating (ht/fluids) and combustion screening (Cantera): deterministic, no AI."""
import math
import shutil
import tempfile
import unittest
import warnings
from pathlib import Path

from plantagent import artifacts, combustion, hxdetail
from plantagent.plant import PlantWorkspace

warnings.filterwarnings("ignore", category=DeprecationWarning)


def water_side(T_in, T_out, kg_h, P=4.0):
    return {"in": {"T_C": T_in, "P_bar": P, "kg_h": kg_h}, "out": {"T_C": T_out, "P_bar": P, "kg_h": kg_h}}


GEOM = {"type": "shell_and_tube", "tube_side": "cold",
        "fluids": {"hot": {"model": "iapws_water"}, "cold": {"model": "iapws_water"}},
        "geometry": {"area_m2": 20.0, "tube_od_m": 0.019, "tube_wall_m": 0.0016, "tube_length_m": 3.0, "tube_passes": 1,
                     "tube_pitch_m": 0.02375, "layout_angle_deg": 30, "baffle_spacing_m": 0.2, "baffle_cut": 0.25,
                     "tube_k_W_mK": 15.0},
        "fouling_m2K_W": {"tube": {"value": 0.000176, "source": "TEMA"}, "shell": {"value": 0.000176, "source": "TEMA"}},
        "limits": {"tube_velocity_min_m_s": {"value": 1.0, "source": "typical"}, "tube_velocity_max_m_s": {"value": 3.0, "source": "typical"},
                   "dP_tube_max_bar": {"value": 0.7, "source": "typical"}, "dP_shell_max_bar": {"value": 0.7, "source": "typical"}}}


class Properties(unittest.TestCase):
    def test_brine_properties_match_handbook_magnitudes(self):
        p = hxdetail.nacl_brine(25.0, 0.26)
        self.assertAlmostEqual(p["rho"], 1194, delta=8)          # 26 wt% NaCl, 25 C: about 1,197 kg/m3
        self.assertTrue(1.6e-3 < p["mu"] < 2.1e-3, p["mu"])        # about 1.9 mPa s
        self.assertTrue(3.2e3 < p["cp"] < 3.4e3, p["cp"])
        w = hxdetail.nacl_brine(20.0, 0.0)
        self.assertAlmostEqual(w["rho"], 998.2, delta=0.5)
        self.assertAlmostEqual(w["mu"], 1.0e-3, delta=0.03e-3)
        self.assertAlmostEqual(w["k"], 0.598, delta=0.01)

    def test_saturated_steam(self):
        s = hxdetail.saturated_steam(3.08)
        self.assertAlmostEqual(s["T_C"], 134.4, delta=0.1)
        self.assertAlmostEqual(s["hfg"] / 1e3, 2160, delta=5)


class Rating(unittest.TestCase):
    def test_water_water_shell_and_tube(self):
        sides = {"hot": water_side(60, 40, 36000), "cold": water_side(20, 40, 36000)}
        Q = 36000 / 3600 * 4180 * 20 / 1000
        rows, num, notes = hxdetail.rate(GEOM, sides, Q, None, "fouled")
        n = round(20.0 / (math.pi * 0.019 * 3.0))
        di = 0.019 - 0.0032
        self.assertEqual(num["n_tubes"], n)
        self.assertAlmostEqual(num["v_tube"], 10.0 / (hxdetail.water(30, 4)["rho"] * n * math.pi * di ** 2 / 4), places=3)
        self.assertGreater(num["U_clean"], num["U"])
        self.assertLess(num["U_clean"], min(num["h_tube"], num["h_shell"]))
        self.assertAlmostEqual(num["A_req"], Q * 1000 / (num["U"] * num["F"] * num["LMTD"]), places=3)
        self.assertEqual(num["LMTD"], 20.0)
        chk = hxdetail.checks("E-1", GEOM, num, model_U=num["U"] * 2, condition="fouled")
        u = next(c for c in chk if c["check"].startswith("model U"))
        self.assertGreater(u["utilisation"], 1)                    # 100 % difference > 20 % flag
        self.assertTrue(all({"id", "check", "value", "limit", "unit", "utilisation"} <= set(c) for c in chk))
        clean = hxdetail.rate(GEOM, sides, Q, None, "clean")[1]
        self.assertAlmostEqual(clean["U"], clean["U_clean"])

    def test_temperature_cross_is_reported(self):
        with self.assertRaises(ValueError):
            hxdetail.lmtd(30, 20, 25, 35)


class SaltHeater(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root, artifacts.ROOT = artifacts.ROOT, Path(self.tmp)

    def tearDown(self):
        artifacts.ROOT = self.root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_e201_rating_from_the_solved_model(self):
        w = PlantWorkspace("salt_mvr")
        r = hxdetail.hx_detail(w, "E-201", 1.0)
        res, names = r["results"], [c["check"] for c in r["checks"]]
        # 154 MW with a 3 K brine rise needs about 48,800 m3/h of saturated brine, three times the P-201 rating
        self.assertAlmostEqual(res["circulation_m3_h"], 48760, delta=500)
        self.assertTrue(2.0 < res["v_tube"] < 2.6, res["v_tube"])
        self.assertTrue(1500 < res["U"] < 1900 and 2900 < res["U_clean"] < 3400, (res["U"], res["U_clean"]))
        for want in ("tube velocity vs minimum", "tube-side pressure drop vs allowable", "shell-side pressure drop vs allowable",
                     "brine circulation needed for the rise limit vs pump rating"):
            self.assertIn(want, names)
        self.assertTrue(any(n.startswith("model U 2000") for n in names))
        self.assertTrue(any(f.endswith(".pdf") for f in r["files"]) and r["kind"] == "calculation")
        md = (Path(self.tmp) / "runs" / "ws" / "salt_mvr" / "artifacts" / r["id"] / "hx-E-201.md").read_text()
        self.assertIn("ILLUSTRATIVE", md)
        for row in [x for x in md.splitlines() if x.startswith("| ") and not x.startswith("| Quantity") and not x.startswith("| Check")]:
            self.assertTrue(row.rstrip(" |").rsplit("|", 1)[-1].strip(), row)   # every row names its source
        # the stored 'clean E-201' proposal rates the clean condition
        i = next(i for i, a in enumerate(w.answers) if any("lean" in p.get("title", "") for p in a.get("proposals") or []))
        c = hxdetail.hx_detail(w, "V-201", answer=i, save=False)   # stored calculation record of the proposal
        self.assertEqual(c["condition"], "clean")
        self.assertEqual(c["model_U"], 2500)

    def test_tools_are_offered_to_the_agent(self):
        w = object.__new__(PlantWorkspace)
        w.cfg = {}
        tools = {t["function"]["name"]: t["function"]["description"] for t in w.tools()}
        self.assertIn("tube velocities", tools["hx_detail"])
        self.assertIn("after cleaning", tools["hx_detail"])
        self.assertIn("stack temperature / NOx", tools["combustion_check"])
        w.cfg = {"engine": "watertap"}
        self.assertNotIn("hx_detail", [t["function"]["name"] for t in w.tools()])


class Combustion(unittest.TestCase):
    def test_methane_heating_values_and_flame(self):
        hv = combustion.heating_values({"CH4": 1})
        self.assertAlmostEqual(hv["LHV"] / 1e6, 50.0, delta=0.2)
        self.assertAlmostEqual(hv["HHV"] / 1e6, 55.5, delta=0.2)
        r = combustion.burn({"CH4": 1}, 1000, "HHV", excess_air_pct=0, humidity=0, residence_s=None)
        self.assertAlmostEqual(r["T_ad_K"], 2225, delta=15)         # stoichiometric methane-air, 298 K

    def test_burner_o2_target_efficiency_and_closure(self):
        r = combustion.burn(None, 10000, "HHV", o2_dry_pct=3.0, stack_T_C=150)
        self.assertAlmostEqual(r["O2_dry_pct"], 3.0, delta=0.02)
        self.assertTrue(83 < r["efficiency_HHV_pct"] < 86, r["efficiency_HHV_pct"])
        hot = combustion.burn(None, 10000, "HHV", o2_dry_pct=3.0, stack_T_C=250)
        self.assertLess(hot["efficiency_HHV_pct"], r["efficiency_HHV_pct"])
        pre = combustion.burn(None, 10000, "HHV", o2_dry_pct=3.0, air_T_C=250)
        self.assertGreater(pre["T_ad_K"], r["T_ad_K"])
        self.assertGreater(pre["NO_thermal_ppmvd_ref"], r["NO_thermal_ppmvd_ref"])  # preheat raises the thermal-NO tendency
        self.assertTrue(55 < r["dew_point_C"] < 62)

    def test_salt_hrsg_reproduces_the_patent_and_extra_steam_needs_duct_firing(self):
        cfg = combustion.load_case("salt_mvr")
        base = combustion.hrsg_case(cfg, 9399.0)
        self.assertAlmostEqual(base["hrsg"]["steam_lb_h"], 35000, delta=150)   # calibrated at patent Table I
        self.assertAlmostEqual(base["losses"]["efficiency_HHV_pct"], base["fuel_utilisation_HHV_pct"], delta=0.1)
        up = combustion.hrsg_case(cfg, 9399.0, steam_scale=1.2)
        self.assertAlmostEqual(up["hrsg"]["steam_lb_h"], 42000, delta=200)
        self.assertGreater(up["duct_burner"]["fuel_MMBtu_h_HHV"], 0)
        self.assertGreater(up["duct_burner"]["T_C"], base["gas_turbine"]["exhaust_T_C"])
        chk = combustion.checks_hrsg(cfg, up, "HRSG-201")
        self.assertTrue(any("no duct burner on record" in c["check"] for c in chk))
        fired = combustion.hrsg_case(cfg, 9399.0, firing_scale=1.2)
        self.assertGreater(fired["hrsg"]["steam_lb_h"], up["hrsg"]["steam_lb_h"])
        self.assertGreater(fired["duct_burner"]["NOx_added_ppmvd_15O2"], up["duct_burner"]["NOx_added_ppmvd_15O2"])


if __name__ == "__main__":
    unittest.main()
