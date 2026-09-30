#!/usr/bin/env python3
"""Phase-boundary Jev assert on compact phase state (not session classify)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase_assert import (
    JEV_MODEL,
    QUESTION_OUTCOME_EVIDENCE,
    build_jev_request,
    evaluate_assert,
    state_hash,
)
from run_record import append_record, entry_from_assert, resolve_record_path

DEFAULT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".assert-log.jsonl",
)

_TRANSCRIPT_ROOT = Path(__file__).resolve().parent.parent / "transcript"
if str(_TRANSCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(_TRANSCRIPT_ROOT))

from lib.jev_client import post_systemone, require_api_key  # noqa: E402


def _load_state(path: Path | None, stdin: bool) -> dict[str, Any]:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    if stdin:
        raw = sys.stdin.read()
        if not raw.strip():
            raise SystemExit("Expected JSON state on stdin or --state PATH")
        return json.loads(raw)
    raise SystemExit("Provide --state PATH or JSON on stdin")


def _append_log(path: str, record: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _log_record(
    state: dict[str, Any],
    result: dict[str, Any],
    response: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": JEV_MODEL,
        "question_id": state.get("question_id", QUESTION_OUTCOME_EVIDENCE),
        "state_hash": state_hash(state),
        "pass": result.get("pass"),
        "decision_source": result.get("decision_source"),
        "answers": (response or {}).get("answers"),
        "usage": (response or {}).get("usage"),
        "deterministic": result.get("deterministic"),
        "jev": result.get("jev"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assert phase closure alignment from compact state (closing record, "
            "trailer, workflow-report). Pass/fail is deterministic; Jev is logged when live."
        ),
    )
    parser.add_argument(
        "--state",
        type=Path,
        metavar="PATH",
        help="JSON file with compact phase state",
    )
    parser.add_argument(
        "--question",
        default=QUESTION_OUTCOME_EVIDENCE,
        choices=[QUESTION_OUTCOME_EVIDENCE],
        help="Assert question id (only outcome-evidence is implemented)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print Jev request JSON only (default when TYPESAFE_API_KEY is unset)",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="POST to TypeSafe, append assert JSONL, print result (requires TYPESAFE_API_KEY)",
    )
    mode.add_argument(
        "--deterministic",
        action="store_true",
        help=(
            "Evaluate the deterministic check only. Print result JSON and exit "
            "0 on pass, 2 on fail. Does not call Jev or classify."
        ),
    )
    parser.add_argument(
        "--log",
        default=DEFAULT_LOG_PATH,
        metavar="PATH",
        help=f"JSONL log path for --live (default: {DEFAULT_LOG_PATH})",
    )
    parser.add_argument(
        "--fixture-jev",
        type=Path,
        metavar="PATH",
        help="Offline: merge answers from a fixture response JSON (no API); still evaluates",
    )
    parser.add_argument(
        "--record",
        type=Path,
        default=None,
        metavar="PATH",
        help="Append assert slice to external run record JSONL (DRIVER_RUN_RECORD env).",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Do not append to run record even when DRIVER_RUN_RECORD is set.",
    )
    args = parser.parse_args(argv)

    state = _load_state(args.state, args.state is None)
    if args.question:
        state = {**state, "question_id": args.question}

    if args.deterministic:
        result_obj = evaluate_assert(state, jev_response=None)
        result = result_obj.to_json_dict()
        record_path = None if args.no_record else resolve_record_path(args.record)
        if record_path is not None:
            record_entry = entry_from_assert(
                plan=state.get("plan"),
                slug=state.get("slug"),
                phase=state.get("phase"),
                result=result,
            )
            append_record(record_path, record_entry)
            result = {**result, "run_record": record_entry}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result_obj.pass_ else 2

    request = build_jev_request(state)
    live = args.live
    if not live and not args.dry_run and not args.fixture_jev:
        key = os.environ.get("TYPESAFE_API_KEY", "").strip()
        if not key:
            print(json.dumps(request, indent=2, ensure_ascii=False))
            return 0
        live = True

    if args.dry_run:
        print(json.dumps(request, indent=2, ensure_ascii=False))
        return 0

    jev_response: dict[str, Any] | None = None
    if args.fixture_jev:
        jev_response = json.loads(args.fixture_jev.read_text(encoding="utf-8"))
    elif live:
        require_api_key()
        jev_response = post_systemone(request)

    result_obj = evaluate_assert(state, jev_response=jev_response)
    result = result_obj.to_json_dict()

    if live or args.fixture_jev:
        if live:
            _append_log(args.log, _log_record(state, result, jev_response))
        record_path = None if args.no_record else resolve_record_path(args.record)
        if record_path is not None:
            record_entry = entry_from_assert(
                plan=state.get("plan"),
                slug=state.get("slug"),
                phase=state.get("phase"),
                result=result,
            )
            append_record(record_path, record_entry)
            result = {**result, "run_record": record_entry}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result_obj.pass_ else 2

    print(json.dumps(request, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
