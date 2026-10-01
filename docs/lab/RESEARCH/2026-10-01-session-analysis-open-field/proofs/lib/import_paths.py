"""Wire cheap-analysis spike lib + progressive proofs on sys.path."""

from __future__ import annotations

import sys

from pathlib import Path

from paths import CHEAP_LIB, PROGRESSIVE_PROOFS

PROOFS_LIB = Path(__file__).resolve().parent


def ensure_import_paths() -> None:
    # Cheap-analysis lib first so its `bootstrap` module resolves correctly.
    for root in (str(CHEAP_LIB), str(PROGRESSIVE_PROOFS), str(PROOFS_LIB)):
        if root not in sys.path:
            sys.path.insert(0, root)
