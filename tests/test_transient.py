import json
import unittest
from pathlib import Path

from plantagent import transient

OV = json.loads((Path(__file__).resolve().parent.parent / "cases/salt_mvr/curves.json").read_text())["units"]


class TestTransient(unittest.TestCase):
    def test_steady_at_rated_point(self):
        """K-201 alone at its rated suction with boil-up equal to it: the pressure does not move."""
        r = transient.run(OV["K-201"], OV["K-202"], 226800, 226800, t_start_s=1e9, t_end_s=60)
        self.assertLess(max(abs(x["P_s_bar"] - 1.70) for x in r["series"]), 1e-3)
        self.assertLess(r["mass_balance_rel_error"], 1e-9)

    def test_ramp_mass_balance_and_settling(self):
        r = transient.run(OV["K-201"], OV["K-202"], 226800, 276300, asc_max_q=1.0)
        self.assertLess(r["mass_balance_rel_error"], 1e-9)
        last = r["series"][-1]
        self.assertAlmostEqual(last["K201_t_h"] + last["K202_t_h"], 276.3, delta=1.0)  # flows meet the new boil-up
        self.assertTrue(next(c for c in r["checks"] if "settles" in c["check"])["pass"])
        self.assertTrue(next(c for c in r["checks"] if "no surge" in c["check"])["pass"])


if __name__ == "__main__":
    unittest.main()
