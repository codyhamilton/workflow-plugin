#!/usr/bin/env python3
"""Offline progressive Jev session-gate replay.

Dry-run writes checkpoint rows and does not call Jev. ``--call-jev`` POSTs
``jev-1.13.0`` only when ``TYPESAFE_API_KEY`` is set and the state fits the
12_000-character guard. Checkout fires only when ``checkout_now`` is
``checkout`` and ``checkout_confidence >= 3`` (fail-open). Any other answer,
including a missing answer, leaves the counterfactual worker running.

This is lab proof code. It does not install a hook or change ``assert_phase``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from session_checkout import (
    QUESTION_SET_FULL,
    apply_rule,
    as_choice,
    as_score,
    build_jev_request,
    request_json,
    request_over_soft_guard,
    summarize_metrics,
)
from snapshot_state import (
    JEV_MODEL,
    prepare_gold_bundle,
    prepare_hybrid_state,
    state_json_len,
)
from turn_index import (
    checkpoints,
    file_sha256,
    index_transcript,
    parse_schedule,
    worker_id_from_path,
)

API_URL = "https://api.typesafe.ai/v1/systemone"

# Published maps sizes. A file whose turn count disagrees is priority_mismatch.
EXPECTED_T = {
    "92a48e004519": 296,
    "bb6165018de0": 154,
    "6c87c96bd9bb": 70,
}
NEGATIVE_CONTROL_IDS = {"6c87c96bd9bb"}
PRIORITY_IDS = ("92a48e004519", "bb6165018de0")

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[2]
    / "2026-09-30-jev-cheap-judgement-signals"
    / "proofs"
    / "fixtures"
    / "maps-5h-workers"
)

REPO_ROOT = Path(__file__).resolve().parents[5]


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def resolve_corpus(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit)
    env = os.environ.get("WORKFLOW_PROGRESSIVE_CORPUS", "").strip()
    if env:
        return Path(env)
    if DEFAULT_CORPUS.is_dir():
        return DEFAULT_CORPUS
    return None


def post_systemone(request: dict[str, Any], api_key: str) -> dict[str, Any]:
    body = request_json(request).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _answers_from_response(response: dict[str, Any]) -> dict[str, Any]:
    answers = response.get("answers")
    return answers if isinstance(answers, dict) else {}


def replay_transcript(
    path: Path,
    *,
    first_at: int,
    interval: int,
    dry_run: bool,
    call_jev: bool,
    gold_exit: int | None,
    gold_exit_provided: bool,
    question_set: str = QUESTION_SET_FULL,
    confidence_min: int = 3,
    on_uncertain: str = "open",
    api_key: str | None = None,
    poster: Callable[[dict[str, Any], str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    indexed = index_transcript(path)
    schedule = checkpoints(first_at, interval, indexed.T)
    rows: list[dict[str, Any]] = []
    prior: int | None = None
    for checkpoint in schedule:
        state, shrink_steps = prepare_hybrid_state(
            indexed,
            checkpoint,
            first_at=first_at,
            interval=interval,
            prior=prior,
        )
        bundle, _bundle_steps = prepare_gold_bundle(indexed, checkpoint)
        row: dict[str, Any] = {
            "worker_id": indexed.worker_id,
            "checkpoint_turn": checkpoint,
            "snapshot_mode": "hybrid_v0",
            "snapshot_params": {"N": 8, "excerpt": 400},
            "question_set": question_set,
            "shrink_steps": shrink_steps,
            "state_chars": state_json_len(state) if state is not None else None,
            "request_chars": None,
            "gold_bundle_chars": state_json_len(bundle) if bundle is not None else None,
            "gold_bundle_status": "ok" if bundle is not None else "unlabelable",
            "decision": "missing",
            "fires": False,
            "reason": "dry_run" if dry_run or not call_jev else None,
            "ungrounded_choice": False,
            "answers": None,
            "state": state,
        }
        if state is None:
            row["reason"] = "state_over_budget"
            row["decision"] = "missing"
            row["fires"] = on_uncertain == "closed"
        else:
            try:
                request = build_jev_request(state, question_set)
            except ValueError as exc:
                row["reason"] = "state_over_budget"
                row["decision"] = "missing"
                row["fires"] = on_uncertain == "closed"
                row["error"] = str(exc)
                request = None
            if request is not None:
                encoded = request_json(request)
                row["request_chars"] = len(encoded)
                if call_jev and not dry_run:
                    if request_over_soft_guard(request):
                        row["reason"] = "request_over_soft_guard"
                        row["decision"] = "missing"
                        row["fires"] = on_uncertain == "closed"
                    else:
                        key = (api_key or os.environ.get("TYPESAFE_API_KEY") or "").strip()
                        send = poster or post_systemone
                        try:
                            response = send(request, key)
                        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                            row["reason"] = "api_error"
                            row["decision"] = "missing"
                            row["fires"] = on_uncertain == "closed"
                            row["error"] = str(exc)
                        else:
                            answers = _answers_from_response(response)
                            choice = as_choice(answers.get("checkout_now"))
                            confidence = as_score(answers.get("checkout_confidence"))
                            ruled = apply_rule(
                                choice=choice,
                                confidence=confidence,
                                confidence_min=confidence_min,
                                on_uncertain=on_uncertain,
                                missing=choice is None,
                                runaway=as_score(answers.get("runaway_pattern")),
                                progress=as_score(answers.get("progress_since_prior")),
                                drift=as_score(answers.get("scope_drift")),
                            )
                            row["answers"] = answers
                            row["decision"] = ruled["decision"]
                            row["fires"] = ruled["fires"]
                            row["ungrounded_choice"] = ruled["ungrounded_choice"]
                            row["reason"] = ruled["reason"]
        rows.append(row)
        prior = checkpoint

    metrics = {
        "worker_id": indexed.worker_id,
        "agent_id": indexed.agent_id,
        "path": display_path(path),
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "T": indexed.T,
        "tool_assistant_turns": sum(1 for turn in indexed.turns if turn.has_tool),
        "peak_ctx_tokens": _full_peak(indexed),
        "sidechain_mode": indexed.sidechain_mode,
        "schedule": {"first_at": first_at, "interval": interval},
        "checkpoints": schedule,
        "model": JEV_MODEL,
        "dry_run": dry_run or not call_jev,
    }
    metrics.update(
        summarize_metrics(
            T=indexed.T,
            rows=rows,
            gold_exit=gold_exit,
            gold_exit_provided=gold_exit_provided,
            interval=interval,
        )
    )
    chars = [row["state_chars"] for row in rows if isinstance(row.get("state_chars"), int)]
    metrics["schema_budget_p0"] = {
        "snapshot_mode": "hybrid_v0",
        "n_checkpoints": len(rows),
        "state_chars_max": max(chars) if chars else None,
        "state_chars_median": _median(chars),
        "n_over_budget": sum(1 for row in rows if row.get("reason") == "state_over_budget"),
        "gold_bundle_chars_max": max(
            (row["gold_bundle_chars"] for row in rows if isinstance(row.get("gold_bundle_chars"), int)),
            default=None,
        ),
    }
    return {"rows": rows, "metrics": metrics}


def _full_peak(indexed: Any) -> int | None:
    values = [turn.context_tokens for turn in indexed.turns if turn.context_tokens is not None]
    if not values:
        return None
    return max(values)


def _median(values: list[int]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def corpus_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.jsonl") if path.is_file())


def build_corpus_manifest(directory: Path) -> dict[str, Any]:
    if not directory.is_dir():
        return {
            "status": "blocked",
            "n_workers_ge_75": 0,
            "priority_found": {worker_id: False for worker_id in PRIORITY_IDS},
            "reason": "transcript directory not configured",
        }
    workers: list[dict[str, Any]] = []
    negative: list[dict[str, Any]] = []
    under: list[dict[str, Any]] = []
    mismatch: list[dict[str, Any]] = []
    found = {worker_id: False for worker_id in PRIORITY_IDS}
    for path in corpus_files(directory):
        indexed = index_transcript(path)
        record = {
            "worker_id": indexed.worker_id,
            "path": display_path(path),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
            "T": indexed.T,
            "tool_assistant_turns": sum(1 for turn in indexed.turns if turn.has_tool),
            "peak_ctx_tokens": _full_peak(indexed),
            "sidechain_mode": indexed.sidechain_mode,
            "source": "maps",
        }
        expected = EXPECTED_T.get(indexed.worker_id)
        if expected is not None and indexed.T != expected:
            mismatch.append(
                {
                    "worker_id": indexed.worker_id,
                    "expected_T": expected,
                    "T": indexed.T,
                }
            )
            record["priority_mismatch"] = True
        if indexed.worker_id in PRIORITY_IDS and indexed.T == EXPECTED_T[indexed.worker_id]:
            found[indexed.worker_id] = True
        if indexed.worker_id in NEGATIVE_CONTROL_IDS:
            negative.append(record)
        elif indexed.T >= 75 and not record.get("priority_mismatch"):
            workers.append(record)
        else:
            under.append(record)
    return {
        "status": "ok",
        "corpus_dir": display_path(directory),
        "counting": (
            "unique message.id on type=assistant; "
            "subagent files whose assistant rows are all isSidechain are counted"
        ),
        "n_workers_ge_75": len(workers),
        "priority_found": found,
        "priority_mismatch": mismatch,
        "workers": workers,
        "negative_control": negative,
        "excluded_under_75": under,
    }


def _write_jsonl(path: Path | None, rows: list[dict[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    text = ("\n".join(lines) + "\n") if lines else ""
    if path is None:
        sys.stdout.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path | None, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        sys.stderr.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _select_paths(corpus: Path, workers: list[str] | None) -> list[Path]:
    files = corpus_files(corpus)
    if not workers:
        return files
    by_id = {worker_id_from_path(path): path for path in files}
    missing = [worker_id for worker_id in workers if worker_id not in by_id]
    if missing:
        raise SystemExit(f"workers not in corpus: {', '.join(missing)}")
    return [by_id[worker_id] for worker_id in workers]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline progressive Jev session-gate replay")
    parser.add_argument("--transcript", type=Path, action="append", default=[], help="Claude JSONL")
    parser.add_argument(
        "--corpus",
        type=str,
        default=None,
        help="Directory of JSONLs. Default: WORKFLOW_PROGRESSIVE_CORPUS, else maps-5h-workers",
    )
    parser.add_argument(
        "--workers",
        default="",
        help="Comma-separated short ids to replay from the corpus",
    )
    parser.add_argument("--schedule", default="75:15", help="first_at:interval (default 75:15)")
    parser.add_argument("--dry-run", action="store_true", help="Write checkpoint rows; do not call Jev")
    parser.add_argument("--call-jev", action="store_true", help="POST jev-1.13.0 when TYPESAFE_API_KEY is set")
    parser.add_argument("--gold-exit", type=int, default=None, help="Optional gold exit turn for overshoot")
    parser.add_argument("--question-set", default=QUESTION_SET_FULL)
    parser.add_argument("--confidence-min", type=int, default=3)
    parser.add_argument("--on-uncertain", choices=("open", "closed"), default="open")
    parser.add_argument("--out", type=Path, default=None, help="Checkpoint JSONL path (stdout if omitted)")
    parser.add_argument("--metrics", type=Path, default=None, help="Metrics JSON path (stderr if omitted)")
    parser.add_argument("--manifest", type=Path, default=None, help="Write corpus manifest JSON")
    parser.add_argument(
        "--omit-state",
        action="store_true",
        help="Drop embedded state objects from checkpoint rows",
    )
    args = parser.parse_args(argv)

    if args.call_jev and args.dry_run:
        raise SystemExit("pass only one of --dry-run and --call-jev")
    dry_run = not args.call_jev
    if args.call_jev and not (os.environ.get("TYPESAFE_API_KEY") or "").strip():
        raise SystemExit("TYPESAFE_API_KEY is not set; refuse --call-jev (dry-run does not need a key)")

    first_at, interval = parse_schedule(args.schedule)
    worker_filter = [part.strip() for part in args.workers.split(",") if part.strip()]

    paths = list(args.transcript)
    corpus: Path | None = None
    if not paths:
        corpus = resolve_corpus(args.corpus)
        if corpus is None:
            blocked = build_corpus_manifest(Path("/nonexistent-progressive-corpus"))
            if args.manifest:
                _write_json(args.manifest, blocked)
            raise SystemExit(
                "no --transcript and no corpus directory "
                "(set WORKFLOW_PROGRESSIVE_CORPUS or pass --corpus)"
            )
        if not corpus.is_dir():
            raise SystemExit(f"corpus directory not found: {corpus}")
        paths = _select_paths(corpus, worker_filter or None)
    elif args.corpus or worker_filter:
        corpus = resolve_corpus(args.corpus)

    if args.manifest:
        manifest_dir = corpus if corpus is not None else resolve_corpus(None)
        if manifest_dir is None:
            _write_json(args.manifest, build_corpus_manifest(Path("/nonexistent-progressive-corpus")))
        else:
            _write_json(args.manifest, build_corpus_manifest(manifest_dir))

    all_rows: list[dict[str, Any]] = []
    per_worker: list[dict[str, Any]] = []
    for path in paths:
        result = replay_transcript(
            path,
            first_at=first_at,
            interval=interval,
            dry_run=dry_run,
            call_jev=args.call_jev,
            gold_exit=args.gold_exit,
            gold_exit_provided=args.gold_exit is not None,
            question_set=args.question_set,
            confidence_min=args.confidence_min,
            on_uncertain=args.on_uncertain,
        )
        rows = result["rows"]
        if args.omit_state:
            for row in rows:
                row.pop("state", None)
        all_rows.extend(rows)
        per_worker.append(result["metrics"])

    _write_jsonl(args.out, all_rows)
    _write_json(
        args.metrics,
        {
            "status": "diagnostic",
            "dry_run": dry_run,
            "schedule": args.schedule,
            "model": JEV_MODEL,
            "question_set": args.question_set,
            "confidence_min": args.confidence_min,
            "on_uncertain": args.on_uncertain,
            "h5_pass": None,
            "h5": "not_run",
            "note": "Dry-run or single replay. Not a lock recommendation. h5_pass is null because alpha was not computed.",
            "workers": per_worker,
        },
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
