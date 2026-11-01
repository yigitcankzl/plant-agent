import unittest

from plantagent.plant import stitch_areas


class StitchAreasTests(unittest.TestCase):
    """Area models joined into one plant (NREL 2011 areas): forward interfaces join, recycles back upstream are torn."""

    def specs(self):
        a300 = {"compounds": ["Water", "Ethanol"], "package": "NRTL",
                "feeds": {"S301": {"kg_h": 100}, "S551": {"kg_h": 5}},
                "units": [{"id": "F-300", "type": "mixer", "in": ["S301", "S551"], "out": "S501"}]}
        a500 = {"compounds": ["Water", "Ethanol", "Carbon dioxide"], "package": "NRTL",
                "feeds": {"S501": {"kg_h": 105}, "S524": {"kg_h": 3}},
                "units": [{"id": "T-512", "type": "mixer", "in": ["S501", "S524"], "out": "S551"}]}
        return [("A300", a300), ("A500", a500)]

    def test_forward_joined_backward_torn(self):
        spec, faces = stitch_areas(self.specs())
        self.assertEqual(spec["compounds"], ["Water", "Ethanol", "Carbon dioxide"])
        self.assertNotIn("S501", spec["feeds"])  # A500's beer feed is now A300's outlet
        self.assertIn("S551-torn", spec["feeds"])  # the scrubber return is held at its documented value
        self.assertEqual(spec["units"][0]["in"], ["S301", "S551-torn"])
        self.assertEqual(spec["units"][1]["out"], "S551")
        kinds = {f["stream"]: f["kind"] for f in faces}
        self.assertEqual(kinds["S501"], "joined")
        self.assertTrue(kinds["S551"].startswith("torn"))

    def test_clashing_unit_ids_and_packages_are_refused(self):
        a, b = self.specs()
        b[1]["units"][0]["id"] = "F-300"
        with self.assertRaises(ValueError):
            stitch_areas([a, b])
        a, b = self.specs()
        b[1]["package"] = "Peng-Robinson (PR)"
        with self.assertRaises(ValueError):
            stitch_areas([a, b])


if __name__ == "__main__":
    unittest.main()
