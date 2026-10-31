import importlib.util
import unittest
from pathlib import Path

from plantagent import grid
from plantagent.plant import _simulator_name, change_errors, patch

ROOT = Path(__file__).resolve().parent.parent
_s = importlib.util.spec_from_file_location("make_ucte_case", ROOT / "tools" / "make_ucte_case.py")
UCTE = importlib.util.module_from_spec(_s)
_s.loader.exec_module(UCTE)
ANGLE = -5.432  # SOUTH_W angle that gives Fig. 30's 1,225 MW on Landesbergen-Wehrendorf (calibrated once)


class GridChanges(unittest.TestCase):
    def test_engine_and_path_changes(self):
        self.assertEqual(_simulator_name({"engine": "pandapower"}), "pandapower")
        spec = UCTE.reference_spec(ANGLE)
        s = patch(spec, [{"path": "switches.LAN coupler.closed", "value": True}])
        self.assertTrue(s["switches"][0]["closed"])
        self.assertFalse(spec["switches"][0]["closed"])
        self.assertTrue(change_errors(spec, [{"path": "lines.NOPE.in_service", "value": False}]))
        self.assertTrue(change_errors(spec, [{"add_unit": {"id": "X"}}]))

    def test_review_blocks_undefined_bus_and_basis_has_no_outcome(self):
        spec = UCTE.reference_spec(ANGLE)
        spec["lines"].append({"id": "BAD", "from": "LAN_A", "to": "NOWHERE", "length_km": 1, "r_ohm_per_km": 0.03, "x_ohm_per_km": 0.26})
        self.assertGreater(grid.review(spec, None)["blocking"], 0)
        basis = (ROOT / "cases" / "ucte_2006" / "basis.md").read_text()
        for leak in ("67 A", "1,274", "opposite effect", "Fig. 31"):
            self.assertNotIn(leak, basis)

    def test_review_blocks_duplicate_element_ids(self):
        spec = UCTE.reference_spec(ANGLE)
        spec["lines"].append({**spec["lines"][0]})
        review = grid.review(spec, None)
        self.assertGreater(review["blocking"], 0)
        self.assertTrue(any(f["check"] == "duplicate element id" for f in review["findings"]))


@unittest.skipUnless(grid.available(), "pandapower venv (.venv-electrical) not installed")
class UcteReproduction(unittest.TestCase):
    """The incident's two findings from the reconstructed network, against the report's numbers."""

    def test_coupling_raises_the_tie_line_current(self):
        before = grid.run(UCTE.reference_spec(ANGLE))["units"]
        after = grid.run(UCTE.reference_spec(ANGLE, coupler=True))["units"]
        self.assertAlmostEqual(before["LAN-WEH"]["p_mw"], 1225, delta=10)       # Fig. 30 (calibrated)
        d_a = after["LAN-WEH"]["i_A"] - before["LAN-WEH"]["i_A"]
        self.assertGreater(d_a, 25)                                              # report: +67 A, not -80 A
        self.assertLess(d_a, 110)
        for lid, fig31 in (("LAN-OVE 1", 621), ("LAN-OVE 2", 621), ("LAN-DOL 1", -784), ("LAN-GRO 2", -261)):
            self.assertAlmostEqual(after[lid]["p_mw"], fig31, delta=60)           # Fig. 31, predicted not fitted

    def test_report_double_circuit_outages_leave_one_circuit(self):
        n1 = grid.n_minus_1(UCTE.reference_spec(ANGLE), elements=["BEC-ELS", "ELS-TWI"])
        self.assertTrue(n1["secure"])
        for case in n1["cases"]:
            self.assertEqual(case["remaining"]["circuits"], 1)
            self.assertLess(case["worst"]["value"], 2100)  # reduced model no longer reproduces report p.48 after true N-1

    def test_n_minus_1_flags_lost_radial_load(self):
        spec = {"grid": True, "buses": [{"id": "A", "vn_kv": 110}, {"id": "B", "vn_kv": 110}],
                "lines": [{"id": "L", "from": "A", "to": "B", "length_km": 10, "r_ohm_per_km": 0.05,
                           "x_ohm_per_km": 0.2, "max_i_ka": 1.0}],
                "loads": [{"id": "LOAD", "bus": "B", "p_mw": 50, "q_mvar": 5}],
                "ext_grids": [{"id": "GRID", "bus": "A", "vm_pu": 1.0}]}
        n1 = grid.n_minus_1(spec, elements=["L"])
        self.assertFalse(n1["secure"])
        lost = next(c for c in n1["cases"][0]["over"] if c.get("kind") == "load lost")
        self.assertEqual((lost["id"], lost["value"]), ("LOAD", 50.0))

    def test_n_minus_1_parallel_line_loses_one_circuit(self):
        spec = {"grid": True, "buses": [{"id": "A", "vn_kv": 110}, {"id": "B", "vn_kv": 110}],
                "lines": [{"id": "L", "from": "A", "to": "B", "length_km": 10, "r_ohm_per_km": 0.05,
                           "x_ohm_per_km": 0.2, "max_i_ka": 1.0, "parallel": 2}],
                "loads": [{"id": "LOAD", "bus": "B", "p_mw": 50, "q_mvar": 5}],
                "ext_grids": [{"id": "GRID", "bus": "A", "vm_pu": 1.0}]}
        case = grid.n_minus_1(spec, elements=["L"])["cases"][0]
        self.assertIn("one of 2 circuits", case["out"])
        self.assertEqual(case["remaining"]["circuits"], 1)
        self.assertGreater(abs(case["remaining"]["p_mw"]), 49)


if __name__ == "__main__":
    unittest.main()
