#!/usr/bin/env python3
from __future__ import annotations

import os
import unittest
from pathlib import Path

_DRIVER = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(_DRIVER))

from jev_signal_log import resolve_jev_signal_log_path  # noqa: E402


class JevSignalLogPathTests(unittest.TestCase):
    def _clear(self) -> None:
        os.environ.pop("YAKKA_JEV_SIGNAL_LOG", None)
        os.environ.pop("XDG_STATE_HOME", None)

    def setUp(self) -> None:
        self._clear()

    def tearDown(self) -> None:
        self._clear()

    def test_default_under_local_state(self) -> None:
        p = resolve_jev_signal_log_path()
        self.assertEqual(p, Path.home() / ".local" / "state" / "yakka" / "jev-signal-log.jsonl")
        self.assertNotIn("tools", str(p))

    def test_xdg_state_home(self) -> None:
        os.environ["XDG_STATE_HOME"] = "/tmp/custom-state"
        p = resolve_jev_signal_log_path()
        self.assertEqual(p, Path("/tmp/custom-state/yakka/jev-signal-log.jsonl"))

    def test_yakka_jev_signal_log_override(self) -> None:
        os.environ["YAKKA_JEV_SIGNAL_LOG"] = "/var/log/jev.jsonl"
        p = resolve_jev_signal_log_path()
        self.assertEqual(p, Path("/var/log/jev.jsonl"))


if __name__ == "__main__":
    unittest.main()
