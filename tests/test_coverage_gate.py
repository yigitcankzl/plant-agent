import unittest

from plantagent.plant import PlantWorkspace


class CoverageGateTests(unittest.TestCase):
    """A submit that models only a column and a heater of a ten-item P&ID (seen on the NREL Area 500 build) is blocked."""

    def test_most_equipment_missing_blocks_submit(self):
        w = PlantWorkspace("nrel_ethanol_a500")
        w.gaps = []
        w.runs["thin"] = {"spec": {"units": [{"id": "PREHEAT", "type": "heater", "in": "S501", "out": "S506"},
                                             {"id": "D-501", "type": "distillation", "in": "S506"}]}}
        blocks = w._coverage_block("thin")
        self.assertEqual(len(blocks), 1)
        self.assertIn("H-512", blocks[0]["items"])
        tags = [e["tag"] for e in w.pid["equipment"]]
        w.runs["full"] = {"spec": {"units": [{"id": t, "type": "mixer"} for t in tags]}}
        self.assertEqual(w._coverage_block("full"), [])
        w.gaps = [{"what": " ".join(tags)}]  # every missing item reported as a gap
        self.assertEqual(w._coverage_block("thin"), [])


if __name__ == "__main__":
    unittest.main()
