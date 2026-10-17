"""Smoke tests for scan_residual_names.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "tools" / "release" / "scan_residual_names.py"


class ScanResidualNamesTests(unittest.TestCase):
    def test_phase5_clean_in_repo(self):
        r = subprocess.run([sys.executable, str(SCAN), "--scope", "phase5"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fixture_hit(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("scan_residual_names", SCAN)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(mod)
        bad = b"packages/" + b"work" + b"flow\n"
        hits = mod.scan_file("packages/yakka/x.txt", bad)
        self.assertTrue(hits)
        self.assertIn("packages/" + "work" + "flow", hits[0][1])


if __name__ == "__main__":
    unittest.main()
