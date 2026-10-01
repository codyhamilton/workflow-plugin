"""Paths for session-analysis open-field proofs."""

from __future__ import annotations

import os
from pathlib import Path

# open-field research pack root (…/2026-10-01-session-analysis-open-field)
PACK_ROOT = Path(__file__).resolve().parents[2]
PROOFS_ROOT = PACK_ROOT / "proofs"
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
DEFAULT_FIXTURES = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers"
)
GOLD_PACKS = PROGRESSIVE_PROOFS / "validated/gold/packs"
SHAPE_QUAL_PACK = GOLD_PACKS / "shape-qual-full-maps-v1-judge-packs-20261001-214046.jsonl"
SHAPE_QUAL_INVENTORY = (
    PROGRESSIVE_PROOFS
    / "validated/gold/packs/INVENTORY-shape-qual-full-maps-v1-20261001-214046.json"
)
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


def phase_out_dir(slug: str) -> Path:
    return PROOFS_ROOT / slug


def validated_dir(name: str) -> Path:
    return PROOFS_ROOT / "validated" / name


def capture_root(registration_id: str = "pilot-field-proof") -> Path:
    return PROOFS_ROOT / "capture" / registration_id


def capture_jev_dir(registration_id: str, mode: str) -> Path:
    """mode: dry-twin | live"""
    return capture_root(registration_id) / "jev" / mode


def capture_local_swarm_dir(registration_id: str) -> Path:
    return capture_root(registration_id) / "local-swarm"


def resolve_corpus_dir() -> Path | None:
    env = os.environ.get("WORKFLOW_PROGRESSIVE_CORPUS", "").strip()
    if env:
        path = Path(env)
        return path if path.is_dir() else None
    if DEFAULT_FIXTURES.is_dir():
        return DEFAULT_FIXTURES
    return None
