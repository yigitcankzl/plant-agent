"""A tray replacement is a rating change: tray_capacity_factor scales Fair's flood screen and can be replaced, not edited."""
import json
import unittest
from pathlib import Path

from plantagent import process
from plantagent.plant import change_errors, limit_changes, patch

ROOT = Path(__file__).resolve().parents[1]
CASE = "basf_process_column_k_2750_dexpi_c02_uns"


class TrayCapacityTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / "runs" / "ws" / CASE / "model.json").read_text())["spec"]
        self.spec["limits"]["K 2750"]["tray_capacity_factor"] = 1.0

    def test_replacing_trays_is_accepted_but_editing_the_factor_is_not(self):
        swap = {"replace_unit": "K 2750", "new_rating": {"tray_capacity_factor": 1.3},
                "basis": "high-capacity trays, vendor rating", "vendor_confirm": True}
        self.assertEqual(change_errors(self.spec, [swap]), [])
        self.assertTrue(limit_changes({"changes": [{"path": "limits.K 2750.tray_capacity_factor", "value": 1.3}]}))

    @unittest.skipUnless(process.available(), "DWSIM not installed")
    def test_factor_divides_the_flood_fraction(self):
        swap = {"replace_unit": "K 2750", "new_rating": {"tray_capacity_factor": 1.25}, "basis": "x", "vendor_confirm": True}
        f1 = process.run(self.spec, 1.0)["units"]["K 2750"]["flood_frac"]
        f2 = process.run(patch(self.spec, [swap]), 1.0)["units"]["K 2750"]["flood_frac"]
        self.assertAlmostEqual(f2, f1 / 1.25, delta=0.002)


if __name__ == "__main__":
    unittest.main()
