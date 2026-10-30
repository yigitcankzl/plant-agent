"""Electrical one-line checks (pandapower in .venv-electrical): load flow converges, a new motor loads the transformer,
DOL starts dip more than VFD starts, limits are flagged. Motors run at rated kW here (no process solve, no AI)."""
import unittest

from plantagent import electrical

K202 = [{"add_unit": {"id": "K-202", "type": "compressor", "in": "a", "out": "b"}, "limits": {"max_kW": 2400, "max_kg_h": 55000},
         "rating_source": "vendor quote to confirm"}]


def by(res, check_word, uid=None):
    return [c for c in res["checks"] if check_word in c["check"] and (uid is None or c["id"] == uid)]


class Parsing(unittest.TestCase):
    def test_motor_changes(self):
        chem = electrical.config("chem_c01")
        found = electrical.motor_changes(chem, [
            {"add_unit": {"id": "P4711B", "type": "pump"}, "limits": {"max_kW": 2.2}, "rating_source": "same model"},
            {"path": "units.P4712.dP_bar", "value": 3.5, "physical_change": "Replace motor with next standard size 11 kW"},
            {"path": "feeds.s47130.m3_h", "value": 27}])
        self.assertEqual(found["P4711B"]["kw"], 2.2)
        self.assertTrue(found["P4711B"]["new"])
        self.assertEqual(found["P4712"]["kw"], 11.0)
        self.assertFalse(found["P4712"]["new"])
        self.assertEqual(len(found), 2)


@unittest.skipUnless(electrical.available(), "pandapower venv (.venv-electrical) unavailable")
class LoadFlow(unittest.TestCase):
    def test_both_cases_converge(self):
        for case in ("salt_mvr", "chem_c01"):
            with self.subTest(case=case):
                r = electrical.check(electrical.config(case), None)
                self.assertTrue(r["transformers"] and r["buses"])
                self.assertTrue(all(0.9 < b["vm_pu"] < 1.1 for b in r["buses"]), r["buses"])
                self.assertIsNone(r["start"])  # nothing new or changed: no start screen

    def test_k202_loads_the_utility_tie_and_dol_dips_more_than_vfd(self):
        cfg = electrical.config("salt_mvr")
        base = electrical.check(cfg, None)
        dol = electrical.check(cfg, None, K202)
        vfd = electrical.check(cfg, None, K202, [{"unit": "K-202", "kw": 2400, "start": "VFD"}])
        tx = lambda r: next(t["loading_percent"] for t in r["transformers"] if t["id"] == "TX-1")  # noqa: E731
        self.assertGreater(tx(dol), tx(base) + 50)
        self.assertEqual(next(m for m in dol["net"]["motors"] if m["unit"] == "K-202")["bus"], "MV")
        self.assertGreater(dol["start"]["terminal_dip_percent"], vfd["start"]["terminal_dip_percent"] + 10)
        over = [c for c in dol["checks"] if c["utilisation"] > 1]
        self.assertTrue(by(dol, "start dip") and by(dol, "start dip")[0]["utilisation"] > 1)  # DOL 2.4 MW on a 2.5 MVA tie
        self.assertTrue(any(c["id"] == "TX-1" for c in over))
        self.assertIn("IEC", by(dol, "transformer")[0]["basis"])

    def test_chem_small_motors_within_limits(self):
        cfg = electrical.config("chem_c01")
        r = electrical.check(cfg, None, [{"path": "units.P4712.dP_bar", "value": 3.5, "physical_change": "next standard size 11 kW"}])
        self.assertEqual(r["start"]["unit"], "P4712")
        self.assertTrue(0 < r["start"]["terminal_dip_percent"] < 15)
        self.assertFalse([c for c in r["checks"] if c["utilisation"] > 1])

    def test_svg(self):
        r = electrical.check(electrical.config("salt_mvr"), None, K202)
        svg = electrical.one_line_svg("t", r)
        self.assertTrue(svg.startswith("<svg") and "TX-1" in svg and "NEW" in svg and "Start of M-K-202" in svg)


if __name__ == "__main__":
    unittest.main()
