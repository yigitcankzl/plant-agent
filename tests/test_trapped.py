import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plantagent import trapped
from plantagent.plant import change_errors, patch


def psat(T):  # bar, a methane-like vapour-pressure curve
    return math.exp(10.0 - 1300.0 / (T + 273.15))


def rho_l(T, P):
    return 420.0 - 1.6 * (T + 150.0) + 0.35 * (P - psat(T))


def fake_props(fluid, points):
    out = []
    for p in points:
        T, P = p["T_C"], p["P_bar"]
        if P >= psat(T):
            rho, h = rho_l(T, P), 2.0 * T
        else:
            rho, h = P * 1e5 * 0.017 / (8.314 * (T + 273.15)), 2.0 * T  # no latent heat: keeps the fake consistent at constant volume
        out.append({**p, "density_kg_m3": rho, "enthalpy_kJ_kg": h})
    return out


def fake_bubble(fluid, T):
    return psat(T)


SPEC = {"fluid": {"compounds": ["Methane"], "x": {"Methane": 1.0}},
        "feeds": {"LNG": {"P_psig": 37, "fill_fraction": 0.9}},
        "units": [{"id": "SEG", "type": "pipe_segment", "in": "LNG", "od_m": 0.4572, "wall_m": 0.00478, "length_m": 100,
                   "heat_leak_W_m": 15.0},
                  {"id": "PSV-1", "type": "relief_valve", "protects": "SEG", "set_psig": 230, "isolated": True},
                  {"id": "XV-1", "type": "valve", "isolates": "SEG", "closed": True},
                  {"id": "XV-2", "type": "valve", "isolates": "SEG", "closed": True}],
        "hours": 114.7, "limits": {"SEG": {"design_psig": 230, "burst_psig": 1456}}}


class Trapped(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [mock.patch.object(trapped, "_props", fake_props), mock.patch.object(trapped, "_bubble", fake_bubble),
                        mock.patch.object(trapped, "CACHE", Path(self.tmp.name))]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_isochore_rises_and_turns_steep_when_liquid_full(self):
        rows, basis = trapped.history(SPEC)
        hours = [h for h, _, _ in rows]
        self.assertEqual(hours, sorted(hours))
        knee = trapped._liquid_full_h(rows)
        self.assertIsNotNone(knee)
        before = [P for h, P, _ in rows if h < knee]
        self.assertLess(max(before), 40)  # vapour-pressure regime below the knee
        self.assertGreater(rows[-1][1], 200)  # hydraulic expansion after it

    def test_blocked_in_with_isolated_relief_overpressures(self):
        r = trapped.run(SPEC, 1.0)
        design = next(c for c in r["checks"] if c["check"].startswith("pressure vs design"))
        self.assertGreater(design["utilisation"], 1)
        self.assertIsNotNone(r["units"]["SEG"]["design_reached_h"])
        cap = trapped.capacity(SPEC)
        self.assertLess(cap["capacity_multiple"], 1)

    def test_relief_in_service_holds_set_pressure(self):
        spec = patch(SPEC, [{"path": "units.PSV-1.isolated", "value": False}])
        r = trapped.run(spec, 1.0)
        self.assertAlmostEqual(r["units"]["SEG"]["P_psig"], 230, delta=0.5)
        self.assertTrue(r["units"]["PSV-1"]["lifted"])
        self.assertTrue(all(c["utilisation"] <= 1.0 for c in r["checks"]))

    def test_open_isolating_valve_vents_to_start_pressure(self):
        spec = patch(SPEC, [{"path": "units.XV-2.closed", "value": False}])
        r = trapped.run(spec, 2.0)
        self.assertAlmostEqual(r["units"]["SEG"]["P_psig"], 37, delta=0.5)
        self.assertFalse(r["units"]["SEG"]["blocked_in"])

    def test_spec_uses_the_generic_change_boundary(self):
        self.assertFalse(change_errors(SPEC, [{"path": "units.PSV-1.isolated", "value": False}]))


if __name__ == "__main__":
    unittest.main()
