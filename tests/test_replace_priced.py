import unittest
from plantagent.economics import _change_lines


class ReplacePriced(unittest.TestCase):
    def test_replacement_is_never_free(self):
        lines = _change_lines({"replace_unit": "K1", "new_rating": {"diameter_m": 0.6}}, {}, {})
        self.assertEqual(len(lines), 1)
        self.assertIsNone(lines[0]["usd"])
        self.assertIn("vendor", lines[0]["source"])


if __name__ == "__main__":
    unittest.main()
