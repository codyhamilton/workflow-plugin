"""Add progressive proof modules to sys.path once."""

from __future__ import annotations

import sys
from pathlib import Path

from paths import PROGRESSIVE_PROOFS  # noqa: F401 — re-export for callers


def ensure_progressive_proofs() -> None:
    root = str(PROGRESSIVE_PROOFS)
    if root not in sys.path:
        sys.path.insert(0, root)
