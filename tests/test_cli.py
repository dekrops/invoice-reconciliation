"""The command line against the fixture dataset: the report must stay exactly as documented."""

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Cli(unittest.TestCase):
    def test_fixture_report(self):
        out = subprocess.run(
            [sys.executable, "-m", "reconcile", "fixtures/invoices.json", "fixtures/orders.json"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
        expected = json.loads((ROOT / "fixtures" / "expected-report.json").read_text())
        self.assertEqual(json.loads(out), expected)

    def test_usage(self):
        r = subprocess.run([sys.executable, "-m", "reconcile"], cwd=ROOT, capture_output=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
