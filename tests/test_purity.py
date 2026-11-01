"""Column purity and minimum-reflux check on a stub solver: purity rises with reflux, no DWSIM."""
import unittest

from plantagent import designchecks

SPEC = {"units": [{"id": "C1", "type": "distillation", "in": "F", "distillate": "D", "bottoms": "B", "stages": 15,
                   "reflux_ratio": 0.8}]}
CFG = {"draft": True, "columns": {"C1": {"distillate": {"component": "A", "min_mass_frac": 0.908},
                                         "bottoms": {"component": "W", "min_mass_frac": 0.2}}}}


def solve(spec, scale=1.0):
    r = spec["units"][0]["reflux_ratio"]
    x = min(0.99, 0.88 + 0.025 * r)  # 0.8 -> 0.90, 1.12 -> 0.908
    return {"streams": {"D": {"components_kg_h": {"A": 100 * x, "W": 100 * (1 - x)}},
                        "B": {"components_kg_h": {"A": 70, "W": 30}}}, "units": {}}


class Stub:
    _solve = staticmethod(solve)


class PurityTest(unittest.TestCase):
    def test_low_reflux_fails_and_minimum_is_found(self):
        rows = {r["check"]: r for r in designchecks.purity_checks(Stub(), SPEC, solve(SPEC), 1.2, CFG)}
        self.assertEqual(rows["separation.C1.purity_distillate"]["status"], "fail")
        self.assertEqual(rows["separation.C1.purity_bottoms"]["status"], "pass")
        m = rows["separation.C1.min_reflux"]
        self.assertEqual(m["status"], "fail")
        self.assertAlmostEqual(m["numbers"]["limit"], 1.12, delta=0.03)
        self.assertTrue(m["title"].startswith("draft (assumed values)"))

    def test_no_spec_is_open(self):
        rows = designchecks.purity_checks(Stub(), SPEC, solve(SPEC), 1.2, None)
        self.assertEqual([r["status"] for r in rows], ["open"])


if __name__ == "__main__":
    unittest.main()
