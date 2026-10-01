#!/usr/bin/env python3
"""Phase 1c — mount probe for raw progressive corpus (no vendored JSONL)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from import_paths import ensure_import_paths

ensure_import_paths()

from pack_io import evidence_class_from_fixture_indexed  # noqa: E402
from paths import MOUNT_PROBE_WORKERS, resolve_corpus_dir, validated_dir  # noqa: E402


def probe_worker(corpus: Path, worker_id: str) -> dict[str, object]:
    path = corpus / f"{worker_id}.jsonl"
    if not path.is_file():
        return {
            "worker_id": worker_id,
            "jsonl": str(path),
            "status": "absent",
            "reason": "file_missing",
        }
    ensure_import_paths()
    from turn_index import index_transcript  # type: ignore

    indexed = index_transcript(path)
    ev = evidence_class_from_fixture_indexed(indexed)
    if ev == "prose":
        return {
            "worker_id": worker_id,
            "jsonl": str(path),
            "status": "prose",
            "T": indexed.T,
            "reason": None,
        }
    return {
        "worker_id": worker_id,
        "jsonl": str(path),
        "status": "prose_required",
        "T": indexed.T,
        "reason": "redacted_or_empty_assistant_text",
    }


def main() -> int:
    out_dir = validated_dir("phase-1b-1c")
    out_dir.mkdir(parents=True, exist_ok=True)

    corpus = resolve_corpus_dir()
    env = __import__("os").environ.get("WORKFLOW_PROGRESSIVE_CORPUS", "").strip()

    payload: dict[str, object] = {
        "phase": "1c",
        "WORKFLOW_PROGRESSIVE_CORPUS": env or None,
        "corpus_dir": str(corpus) if corpus else None,
        "documented_default": "docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/fixtures/maps-5h-workers",
        "workers": [],
    }

    if corpus is None:
        payload["mount_status"] = "absent"
        payload["note"] = "No corpus directory; expected on cloud VM without raw Ubuntu mount."
        for wid in MOUNT_PROBE_WORKERS:
            payload["workers"].append(
                {
                    "worker_id": wid,
                    "status": "prose_required",
                    "reason": "corpus_not_mounted",
                }
            )
    else:
        payload["mount_status"] = "resolved"
        for wid in MOUNT_PROBE_WORKERS:
            payload["workers"].append(probe_worker(corpus, wid))

    out_path = out_dir / "mount_probe_results.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), "mount_status": payload["mount_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
