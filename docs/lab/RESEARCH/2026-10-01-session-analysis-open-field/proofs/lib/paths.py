"""Repo paths for session-analysis open-field proofs."""

from __future__ import annotations

import os
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
OPEN_FIELD = PACK_ROOT.parent
REPO_ROOT = OPEN_FIELD.parents[3]

CHEAP_LIB = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-10-01-cheap-analysis-typesafe-opencode/proofs/lib"
)
PROGRESSIVE_PROOFS = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"
)
DEFAULT_FIXTURES = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers"
)
GOLD_PACKS = PROGRESSIVE_PROOFS / "validated/gold/packs"
SHAPE_QUAL_PACK = GOLD_PACKS / "shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl"
AGREEMENT_MATRIX = (
    PROGRESSIVE_PROOFS
    / "validated/gold/shape-qual-full-maps-v1/agreement-matrix.json"
)

# Stratified 8 for one 32-call wave (OPEN-FIELD.md §3)
STRATIFIED_EIGHT = (
    "ca977b9ca0dd",
    "92a48e004519",
    "87a380bc64ff",
    "bb6165018de0",
    "15f24c7ba18c",
    "0677f597286e",
    "074c8cf22927",
    "07357f196666",
)

# Mount probe pilots (summary-then-judge + thrash/poll spotlight)
MOUNT_PROBE_WORKERS = (
    "ca977b9ca0dd",
    "92a48e004519",
    "87a380bc64ff",
    "bb6165018de0",
    "6e06ab86aa72",
    "0aab88c525de",
    "15f24c7ba18c",
    "8e36f8e80baa",
)


def validated_dir(name: str) -> Path:
    return PACK_ROOT / "validated" / name


def resolve_corpus_dir() -> Path | None:
    env = os.environ.get("WORKFLOW_PROGRESSIVE_CORPUS", "").strip()
    if env:
        path = Path(env)
        return path if path.is_dir() else None
    if DEFAULT_FIXTURES.is_dir():
        return DEFAULT_FIXTURES
    return None
