#!/usr/bin/env python3
"""Emit card-hash placeholder manifest for stratified + full n=34 workers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from import_paths import ensure_import_paths

ensure_import_paths()

from paths import AGREEMENT_MATRIX, STRATIFIED_EIGHT, validated_dir  # noqa: E402
from stats_card import manifest_all_workers, worker_T_from_matrix  # noqa: E402


def main() -> int:
    T_map = worker_T_from_matrix(AGREEMENT_MATRIX)
    all_workers = tuple(T_map.keys())
    cards = manifest_all_workers(all_workers, T_map)
    stratified = [c for c in cards if c["worker_id"] in STRATIFIED_EIGHT]

    manifest = {
        "card_kind": "stats_card_placeholder",
        "phase_1a_dependency": (
            "Full stats-card extractor (marker columns, round-trip gate) is phase 1a. "
            "This manifest uses shape-qual pack rows ≤120 until 1a merges."
        ),
        "n_workers": len(cards),
        "stratified_eight_hashes": {c["worker_id"]: c["card_hash"] for c in stratified},
        "workers": [
            {"worker_id": c["worker_id"], "card_hash": c["card_hash"], "checkpoint_turn": c["checkpoint_turn"]}
            for c in cards
        ],
    }
    out_dir = ROOT / "manifests"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "card_hash_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(path), "n_workers": len(cards)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
