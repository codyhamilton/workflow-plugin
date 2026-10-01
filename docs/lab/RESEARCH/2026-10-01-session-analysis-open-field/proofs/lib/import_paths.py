"""Wire cheap-analysis spike lib + progressive proofs on sys.path."""

from __future__ import annotations

import sys

from paths import CHEAP_LIB, PACK_ROOT, PROGRESSIVE_PROOFS


def ensure_import_paths() -> None:
    # Cheap-analysis lib first so its `bootstrap` module resolves correctly.
    for root in (str(CHEAP_LIB), str(PROGRESSIVE_PROOFS), str(PACK_ROOT / "lib")):
        if root not in sys.path:
            sys.path.insert(0, root)
