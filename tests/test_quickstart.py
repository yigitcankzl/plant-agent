import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class QuickstartTest(unittest.TestCase):
    def test_help_and_bad_argument_do_not_install(self):
        help_run = subprocess.run(["bash", "start.sh", "--help"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(help_run.returncode, 0, help_run.stderr)
        self.assertIn("./start.sh --live", help_run.stdout)

        bad_run = subprocess.run(["bash", "start.sh", "--unknown"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(bad_run.returncode, 2)
        self.assertIn("Usage:", bad_run.stderr)


if __name__ == "__main__":
    unittest.main()
