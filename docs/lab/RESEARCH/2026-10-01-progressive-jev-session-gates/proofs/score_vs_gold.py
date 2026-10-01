#!/usr/bin/env python3
"""Score a Jev replay JSONL against primary gold_exit.

``--replay`` is the checkpoint JSONL from ``replay_progressive_gates.py``
(``--call-jev`` or a dry-run). ``fires`` is the gate. ``--gold`` is
``summary.json`` from ``aggregate_gold.py``, or a directory / file of CHM
verdict objects in the canonical shape::

    {worker_id, checkpoint_turn, model, checkout_recommended, rationale,
     first_checkout_turn_guess}

Pending, unsigned drafts, and a one-seat Sonnet panel do not fill
overshoot, false_early, or false_late. ``max_allowed_turns`` still follows
the replay when ``T`` is known: the gate exit, otherwise ``T`` (fail-open).
A dry-run therefore reports ``max_allowed_turns = T`` and does not invent a
gold exit. Grok 4.7 and Composer seats stay empty until signed packs arrive.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gold_panel import aggregate_labels, load_labels, load_metrics_T, load_replay_rows, score_replay


def _gold_summary(path: Path, *, include_pending: bool) -> dict:
    if path.is_file() and path.name == "summary.json":
        doc = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and "workers" in doc and "gold_rule" in doc:
            return doc
    labels = load_labels(path, include_pending=include_pending)
    return aggregate_labels(labels)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score Jev replay JSONL against gold_exit")
    parser.add_argument("--replay", type=Path, action="append", default=[], help="Checkpoint JSONL from the replay")
    parser.add_argument("--metrics", type=Path, action="append", default=[], help="Replay metrics or ubuntu-raw SUMMARY JSON")
    parser.add_argument("--gold", type=Path, required=True, help="summary.json or CHM verdict file/directory")
    parser.add_argument("--include-pending", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.replay:
        raise SystemExit("pass at least one --replay JSONL")
    for path in list(args.replay) + list(args.metrics) + [args.gold]:
        if not path.exists():
            raise SystemExit(f"not found: {path}")
    summary = _gold_summary(args.gold, include_pending=args.include_pending)
    metrics = load_metrics_T(args.metrics)
    rows = load_replay_rows(args.replay)
    scored = score_replay(rows, summary, metrics=metrics)
    text = json.dumps(scored, ensure_ascii=False, indent=2) + "\n"
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        sys.stdout.write(json.dumps({"status": scored["status"], "out": str(args.out)}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
