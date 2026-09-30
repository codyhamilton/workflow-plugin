#!/usr/bin/env python3
"""Classify a session snapshot via TypeSafe Jev (System One)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from lib.cli import add_tool_arg, load_normalized_json, setup_path
from lib.jev_client import (
    JEV_MODEL,
    build_request,
    post_systemone,
    require_api_key,
)
from lib.snapshot import (
    build_snapshot_state,
    estimate_snapshot_tokens,
    snapshot_hash,
)

setup_path()

DEFAULT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".classify-log.jsonl")


def _append_log(path: str, record: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _log_record(
    data: dict[str, Any],
    state: dict[str, Any],
    response: dict[str, Any] | None,
) -> dict[str, Any]:
    session = data.get("session", {})
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": JEV_MODEL,
        "source": data.get("source", ""),
        "session_id": session.get("id", ""),
        "snapshot_hash": snapshot_hash(state),
        "snapshot_token_estimate": estimate_snapshot_tokens(state),
        "answers": (response or {}).get("answers"),
        "usage": (response or {}).get("usage"),
        "human_label": None,
        "human_notes": None,
        "agree_with_iterate_phase_mode": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify agent session kind via TypeSafe Jev (snapshot, not full transcript)."
    )
    parser.add_argument(
        "--session",
        metavar="REF",
        help="Re-extract from this session instead of reading stdin",
    )
    parser.add_argument(
        "--project",
        dest="project_flag",
        metavar="PATH",
        help="Project path (with --session; default: cwd)",
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project path (with --session; default: cwd)",
    )
    add_tool_arg(parser)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print request JSON only (default when TYPESAFE_API_KEY is unset)",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="POST to TypeSafe and append JSONL log (requires TYPESAFE_API_KEY)",
    )
    parser.add_argument(
        "--log",
        default=DEFAULT_LOG_PATH,
        metavar="PATH",
        help=f"JSONL log path for --live (default: {DEFAULT_LOG_PATH})",
    )
    parser.add_argument(
        "--no-workflow-alignment",
        action="store_true",
        help="Omit workflow_alignment Score question (session_kind Choice only)",
    )
    args = parser.parse_args()

    project = args.project_flag or args.project_path or (os.getcwd() if args.session else None)
    data = load_normalized_json(args.session, project, args.tool)
    state = build_snapshot_state(data)
    request = build_request(
        state,
        include_workflow_alignment=not args.no_workflow_alignment,
    )

    if not args.live:
        print(json.dumps(request, indent=2, ensure_ascii=False))
        return

    require_api_key()
    response = post_systemone(request)
    record = _log_record(data, state, response)
    _append_log(args.log, record)
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
