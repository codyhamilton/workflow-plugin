"""Paths for session-analysis open-field proofs."""

from __future__ import annotations

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACK_ROOT.parents[3]
CHEAP_LIB = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/proofs/lib"
)
PACK_REL = (
    "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs/"
    "validated/gold/packs/shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl"
)
PROGRESSIVE_PROOFS = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"
)
SHAPE_QUAL_PACK = (
    PROGRESSIVE_PROOFS
    / "validated/gold/packs/shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl"
)
SHAPE_QUAL_INVENTORY = (
    PROGRESSIVE_PROOFS
    / "validated/gold/packs/INVENTORY-shape-qual-full-maps-v1-20261001-214046.json"
)


def phase_out_dir(slug: str) -> Path:
    return PACK_ROOT / "proofs" / slug
