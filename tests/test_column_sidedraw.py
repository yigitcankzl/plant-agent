import unittest

from plantagent import process


@unittest.skipUnless(process.available(), "DWSIM not installed")
class ColumnSideDrawTests(unittest.TestCase):
    """A beer-column-like water/ethanol column: two feeds, a vapour side draw and Murphree trays (NREL 2011 D-501/D-502)."""

    def spec(self, **col):
        unit = {"id": "C", "type": "distillation", "in": ["F", "R"], "feed_stage": [3, 6], "distillate": "D", "bottoms": "B",
                "stages": 12, "condenser": "total", "P_bar": 2.0, "reflux_ratio": 3.0, "bottoms_mol_s": 120.0,
                "out": ["SD"], "side_draws": [{"stage": 5, "phase": "vapor", "mol_s": 5.0}], "efficiency": 0.6, **col}
        return {"compounds": ["Water", "Ethanol"], "package": "NRTL",
                "feeds": {"F": {"T_C": 77, "P_bar": 2, "kg_h": 10000, "x": {"Water": 0.95, "Ethanol": 0.05}},
                          "R": {"T_C": 77, "P_bar": 2, "kg_h": 1000, "x": {"Water": 0.5, "Ethanol": 0.5}}},
                "units": [unit]}

    def test_side_draw_two_feeds_and_efficiency_solve(self):
        r = process.run(self.spec())
        s = r["streams"]
        self.assertGreater(s["SD"]["kg_h"], 300)  # 5 mol/s of a water-ethanol vapour
        self.assertEqual(s["SD"]["vapour_frac"], 1.0)
        total = s["D"]["kg_h"] + s["B"]["kg_h"] + s["SD"]["kg_h"]
        self.assertAlmostEqual(total, 11000, delta=30)
        # column products carry their compound split (DWSIM leaves compound flows empty on column products)
        eth = sum(s[n]["components_kg_h"]["Ethanol"] for n in ("D", "B", "SD"))
        feed_eth = s["F"]["components_kg_h"]["Ethanol"] + s["R"]["components_kg_h"]["Ethanol"]
        self.assertAlmostEqual(eth, feed_eth, delta=0.02 * feed_eth)
        self.assertGreater(s["D"]["components_kg_h"]["Ethanol"], s["B"]["components_kg_h"]["Ethanol"])

    def test_trace_heavies_in_a_vapour_feed_are_stripped(self):
        # Muse's NREL Area 500 build: glycol traces (x ~ 1e-7) carried over in D-501's vapour stalled D-502's solver
        import json
        from pathlib import Path
        spec = json.loads((Path(__file__).parent / "fixtures" / "nrel_d501_d502.json").read_text())
        r = process.run(spec)
        self.assertEqual(r["errors"], [])
        self.assertTrue(any("stripped traces" in n for n in r.get("notes", [])))  # the retry is reported, never silent
        self.assertGreater(r["streams"]["S511L"]["components_kg_h"]["Ethanol"], 20000)

    def test_mismatched_side_draw_is_rejected(self):
        with self.assertRaises(RuntimeError):
            process.run(self.spec(out=["SD", "SD2"]))


if __name__ == "__main__":
    unittest.main()
