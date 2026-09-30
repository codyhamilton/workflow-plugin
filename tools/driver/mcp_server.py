#!/usr/bin/env python3
"""MCP-shaped stdio JSON-RPC for Grok Bot (status, trigger_phase, poll).

One JSON object per line on stdin; one JSON object per line on stdout.
This is a thin contract surface until Phase 4 adds a full MCP SDK server.

Request shape:
  {"id": 1, "method": "status"|"trigger_phase"|"poll", "params": {...}}

Response shape:
  {"id": 1, "result": {...}} or {"id": 1, "error": {"message": "..."}}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from resolve import ResolveError, resolve_plan_folder
from trigger import trigger_once

_IN_FLIGHT: dict[str, Any] = {}


def _handle_status(params: dict[str, Any]) -> dict[str, Any]:
    plan = Path(params["plan_folder"])
    default_branch = params.get("default_branch")
    status = resolve_plan_folder(plan, default_branch=default_branch)
    return status.to_json_dict()


def _handle_trigger_phase(params: dict[str, Any]) -> dict[str, Any]:
    plan = Path(params["plan_folder"])
    outcome = trigger_once(
        plan,
        default_branch=params.get("default_branch"),
        provider=params.get("provider"),
        dry_run=bool(params.get("dry_run")),
        fixture_output=(
            Path(params["fixture_output"]) if params.get("fixture_output") else None
        ),
        review_posture=params.get("review", "terminal"),
    )
    return outcome.to_json_dict()


def _handle_poll(params: dict[str, Any]) -> dict[str, Any]:
    dispatch_id = params.get("dispatch_id", "")
    if dispatch_id and dispatch_id in _IN_FLIGHT:
        entry = _IN_FLIGHT.pop(dispatch_id)
        return {"in_flight": False, "outcome": entry}
    return {"in_flight": False, "outcome": None}


def dispatch_request(req: dict[str, Any]) -> dict[str, Any]:
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params") or {}
    try:
        if method == "status":
            result = _handle_status(params)
        elif method == "trigger_phase":
            result = _handle_trigger_phase(params)
        elif method == "poll":
            result = _handle_poll(params)
        else:
            return {"id": req_id, "error": {"message": f"Unknown method: {method}"}}
        return {"id": req_id, "result": result}
    except ResolveError as exc:
        return {"id": req_id, "error": {"message": str(exc)}}
    except KeyError as exc:
        return {"id": req_id, "error": {"message": f"Missing parameter: {exc}"}}


def serve_stdio() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps({"id": None, "error": {"message": str(exc)}}))
            continue
        print(json.dumps(dispatch_request(req)))
        sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MCP-shaped driver RPC (stdio JSON lines).")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Read JSON-RPC requests from stdin (default when no subcommand).",
    )
    parser.add_argument(
        "oneshot_method",
        nargs="?",
        choices=("status", "trigger_phase", "poll"),
        help="Optional one-shot call (for shell-based bots).",
    )
    parser.add_argument("--plan-folder", type=Path, default=None)
    parser.add_argument("--default-branch", default=None)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-output", type=Path, default=None)
    parser.add_argument("--review", default="terminal")
    args = parser.parse_args(argv)

    if args.oneshot_method:
        params: dict[str, Any] = {}
        if args.plan_folder is not None:
            params["plan_folder"] = str(args.plan_folder)
        if args.default_branch:
            params["default_branch"] = args.default_branch
        if args.provider:
            params["provider"] = args.provider
        if args.dry_run:
            params["dry_run"] = True
        if args.fixture_output:
            params["fixture_output"] = str(args.fixture_output)
        if args.review:
            params["review"] = args.review
        resp = dispatch_request({"id": 1, "method": args.oneshot_method, "params": params})
        if "error" in resp:
            print(resp["error"]["message"], file=sys.stderr)
            return 1
        json.dump(resp["result"], sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    return serve_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
