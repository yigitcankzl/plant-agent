import unittest
from plantagent.designchecks import product_checks


class W:
    cfg = {"target_scale": 1.25, "product": {"stream": "P", "component": "E"}}

    def state(self, scale):
        return {"streams": {"P": {"components_kg_h": {"E": 100.0}}}}


class ProductCheck(unittest.TestCase):
    def test_feed_up_but_product_not(self):
        rows = product_checks(W(), {"streams": {"P": {"components_kg_h": {"E": 107.0}}}})
        self.assertEqual(rows[0]["status"], "fail")

    def test_product_meets_target(self):
        rows = product_checks(W(), {"streams": {"P": {"components_kg_h": {"E": 126.0}}}})
        self.assertEqual(rows[0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
