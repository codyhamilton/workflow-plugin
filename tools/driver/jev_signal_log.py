"""Resolve the Jev signal log path (Assumption 11; shared with OpenCode batch flush)."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_jev_signal_log_path() -> Path:
    override = os.environ.get("YAKKA_JEV_SIGNAL_LOG")
    if override:
        return Path(override)
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        base = Path(state_home)
    else:
        base = Path.home() / ".local" / "state"
    return base / "yakka" / "jev-signal-log.jsonl"
