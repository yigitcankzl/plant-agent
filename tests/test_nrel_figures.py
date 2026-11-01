"""NREL figures build from the stored comparisons and status table (no LLM, no solver)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import nrel_figures  # noqa: E402


class NrelFigures(unittest.TestCase):
    def test_build(self):
        figs, comps = nrel_figures.build()
        self.assertEqual(set(figs), {"nrel_parity.svg", "nrel_parity_a300.svg", "nrel_parity_a500.svg", "nrel_plant_map.svg"})
        for svg in figs.values():
            self.assertTrue(svg.startswith("<svg") and svg.endswith("</svg>"))
        s = comps["A300"]["summary"]
        self.assertIn(f"{s['within_5']} of {s['checks']} checks within 5 %", figs["nrel_parity_a300.svg"])
        self.assertIn("Aspen Plus", figs["nrel_parity.svg"])  # the honesty note travels with the figure
        self.assertEqual(figs["nrel_plant_map.svg"].count("<rect x="), 9 + 4)  # nine areas + four legend swatches
        self.assertIn("not feasible in DWSIM", figs["nrel_plant_map.svg"])


if __name__ == "__main__":
    unittest.main()
