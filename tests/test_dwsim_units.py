import unittest

from plantagent import process


class DWSIMAllowlistTests(unittest.TestCase):
    def test_unknown_class_lists_the_allowlist(self):
        with self.assertRaises(ValueError) as caught:
            process.validate_dwsim_unit({"id": "X", "type": "dwsim", "class": "ExcelUO", "in": ["A"], "out": ["B"]})
        message = str(caught.exception)
        self.assertIn("ExcelUO", message)
        self.assertIn("Pump", message)
        self.assertIn("RCT_PFR", message)
        self.assertIn("DistillationColumn", message)
        self.assertNotIn("CustomUO", message)

    def test_unknown_property_lists_valid_properties_and_units(self):
        with self.assertRaises(ValueError) as caught:
            process.validate_dwsim_unit({"id": "V", "type": "dwsim", "class": "Valve", "in": ["A"], "out": ["B"],
                                         "set": {"NotAProperty": 1}})
        message = str(caught.exception)
        self.assertIn("NotAProperty", message)
        self.assertIn("DeltaP (Pa)", message)
        self.assertIn("CalcMode", message)

    def test_bad_enum_lists_names(self):
        with self.assertRaises(ValueError) as caught:
            process.validate_dwsim_unit({"id": "P", "type": "dwsim", "class": "Pump", "in": ["A"], "out": ["B"],
                                         "set": {"CalcMode": "NotAMode"}})
        self.assertIn("Delta_P", str(caught.exception))

    def test_property_values_are_typed_and_bounded(self):
        base = {"id": "R", "type": "dwsim", "class": "RCT_PFR", "in": ["A"], "out": ["B"]}
        for values in ({"Volume": -1}, {"Volume": float("nan")}, {"UseUserDefinedPressureDrop": "false"},
                       {"CatalystVoidFraction": 1.1}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                process.validate_dwsim_unit({**base, "set": values})
        props = process.validate_dwsim_unit({**base, "set": {"Volume": 1.0, "UseUserDefinedPressureDrop": False}})
        self.assertIn("Volume", props)

    def test_fair_capacity_factor_and_flood_fraction_rises_with_vapour(self):
        # Lygeros and Magoulas fit of Fair's chart at 0.5 m spacing and F_LV = 0.1.
        self.assertAlmostEqual(process._fair_csb(0.5, 0.1), 0.0823, places=3)
        low = process.fair_flood_fraction(1.0, 1.0, 3.0, 800.0, 0.02, 1.2, 0.5)
        high = process.fair_flood_fraction(2.0, 1.0, 3.0, 800.0, 0.02, 1.2, 0.5)
        self.assertGreater(high, low)
        self.assertGreater(low, 0)


if __name__ == "__main__":
    unittest.main()
