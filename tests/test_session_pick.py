import unittest
from pathlib import Path

from plantagent.plant import _made_after

F = Path(__file__)


class SessionPick(unittest.TestCase):
    def test_uses_recorded_times_not_mtimes(self):
        self.assertTrue(_made_after("20261031-210628", "2026-10-31 21:06", F, F))
        self.assertFalse(_made_after("20261031-205900", "2026-10-31 21:06", F, F))


if __name__ == "__main__":
    unittest.main()
