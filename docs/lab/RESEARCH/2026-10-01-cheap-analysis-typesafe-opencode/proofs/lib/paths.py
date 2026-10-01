"""Repo-relative paths for the cheap-analysis spike harness."""

from __future__ import annotations

import os
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACK_ROOT.parents[3]
PROGRESSIVE_PROOFS = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-10-01-progressive-jev-session-gates/proofs"
)
DEFAULT_FIXTURES = (
    REPO_ROOT
    / "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers"
)
GOLD_PACKS = PROGRESSIVE_PROOFS / "validated/gold/packs"

WORKERS_T_GE_75 = (
    "92a48e004519",
    "bb6165018de0",
    "0aab88c525de",
    "036ff3ed4a89",
)
CONTROL_WORKER = "6c87c96bd9bb"
ALL_SPIKE0_WORKERS = (*WORKERS_T_GE_75, CONTROL_WORKER)

EXPECTED_T = {
    "92a48e004519": 296,
    "bb6165018de0": 154,
    "0aab88c525de": 192,
    "036ff3ed4a89": 161,
    "6c87c96bd9bb": 70,
}

JUDGE_PACK_BY_WORKER: dict[str, Path] = {
    "92a48e004519": GOLD_PACKS / "p0-judge-packs-20261001-194107.jsonl",
    "bb6165018de0": GOLD_PACKS / "p0-judge-packs-20261001-194107.jsonl",
    "0aab88c525de": GOLD_PACKS / "0aab88c525de-judge-packs-20261001-202909.jsonl",
    "036ff3ed4a89": GOLD_PACKS / "036ff3ed4a89-judge-packs-20261001-202909.jsonl",
}


def proofs_out_dir(spike: str) -> Path:
    return PACK_ROOT / "proofs" / spike


def resolve_fixture_dir() -> Path:
    env = os.environ.get("WORKFLOW_PROGRESSIVE_CORPUS", "").strip()
    if env:
        return Path(env)
    return DEFAULT_FIXTURES


def fixture_path(worker_id: str) -> Path:
    return resolve_fixture_dir() / f"{worker_id}.jsonl"
