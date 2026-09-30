#!/usr/bin/env python3
"""Lab shim — canonical stdin helper in packages/opencode-workflow-hooks/python."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[5]
_PKG_PY = _REPO / "packages" / "opencode-workflow-hooks" / "python"
if str(_PKG_PY) not in sys.path:
    sys.path.insert(0, str(_PKG_PY))

from batch_flush_cli import main  # noqa: E402

if __name__ == "__main__":
    main()
