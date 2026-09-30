"""External run record: one JSON object per driver invocation (outside plan folder).

Kill line: no fields that duplicate git Workflow-Phase trailers or IMPLEMENTATION.md.
Ground truth for *which* phase is open stays in git (status.py); the record holds
provider cost/turns, the last workflow-report, and assert results.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RECORD_VERSION = 1

DEFAULT_RUN_RECORD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".run-record.jsonl",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plan_key(plan: str) -> str:
    return plan.rstrip("/")


def append_record(path: str | Path, entry: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def entry_from_trigger(
    *,
    plan: str,
    slug: str,
    default_branch: str | None,
    skipped: bool,
    report: dict[str, Any] | None,
    dispatch_target: dict[str, Any] | None,
    turns: int | None,
    cost_usd: float | None,
    provider: str | None,
    mode: str | None,
) -> dict[str, Any]:
    """Build one trigger invocation record (no git trailer / status duplication)."""
    entry: dict[str, Any] = {
        "record_version": RECORD_VERSION,
        "ts": _utc_now(),
        "kind": "trigger",
        "plan": _plan_key(plan),
        "slug": slug,
        "default_branch": default_branch,
        "skipped": skipped,
    }
    if report is not None:
        entry["last_report"] = {
            "status": report.get("status"),
            "phase": report.get("phase"),
            "reason": report.get("reason"),
        }
    if not skipped and dispatch_target is not None:
        target = dispatch_target.get("target") or dispatch_target
        kind = target.get("kind") if isinstance(target, dict) else None
        phase_key: str
        if kind == "wrap-up":
            phase_key = "wrap-up"
        elif kind == "phase":
            phase_key = str(target.get("phase"))
        else:
            phase_key = "unknown"
        entry["phase_dispatch"] = {
            "phase": phase_key,
            "turns": turns,
            "cost_usd": cost_usd,
            "provider": provider,
            "mode": mode,
        }
    return entry


def entry_from_assert(
    *,
    plan: str | None,
    slug: str | None,
    phase: int | str | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Build one assert invocation record (compact; no closing-record body)."""
    assert_slice: dict[str, Any] = {
        "question_id": result.get("question_id"),
        "pass": result.get("pass"),
        "decision_source": result.get("decision_source"),
    }
    if not result.get("pass"):
        assert_slice["fail_branch"] = result.get("fail_branch")
    jev = result.get("jev")
    if isinstance(jev, dict) and jev.get("disagreed_with_deterministic"):
        assert_slice["jev_disagreed"] = True
    entry: dict[str, Any] = {
        "record_version": RECORD_VERSION,
        "ts": _utc_now(),
        "kind": "assert",
        "assert": assert_slice,
    }
    if plan:
        entry["plan"] = _plan_key(plan)
    if slug:
        entry["slug"] = slug
    if phase is not None:
        entry["phase"] = phase
    return entry


def _iter_entries(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            entries.append(row)
    return entries


def summarize(path: str | Path, *, plan: str | None = None) -> dict[str, Any]:
    """
    Roll up a JSONL run record for one plan.

    Combined with status.py (git), answers: open phase, last report status, cost.
    """
    entries = _iter_entries(Path(path))
    plan_key = _plan_key(plan) if plan else None
    if plan_key:
        entries = [e for e in entries if _plan_key(str(e.get("plan") or "")) == plan_key]

    phases: dict[str, dict[str, Any]] = {}
    total_cost = 0.0
    last_report: dict[str, Any] | None = None
    last_assert: dict[str, Any] | None = None
    default_branch: str | None = None
    slug: str | None = None
    record_plan: str | None = plan_key

    for entry in entries:
        if entry.get("kind") == "trigger":
            if entry.get("default_branch"):
                default_branch = entry["default_branch"]
            if entry.get("slug"):
                slug = entry["slug"]
            if entry.get("plan"):
                record_plan = _plan_key(str(entry["plan"]))
            if "last_report" in entry and entry["last_report"] is not None:
                last_report = entry["last_report"]
            dispatch = entry.get("phase_dispatch")
            if isinstance(dispatch, dict):
                phase_key = str(dispatch.get("phase", "unknown"))
                phases[phase_key] = {
                    "turns": dispatch.get("turns"),
                    "cost_usd": dispatch.get("cost_usd"),
                    "provider": dispatch.get("provider"),
                    "mode": dispatch.get("mode"),
                }
                cost = dispatch.get("cost_usd")
                if isinstance(cost, (int, float)):
                    total_cost += float(cost)
        elif entry.get("kind") == "assert":
            if entry.get("assert"):
                last_assert = entry["assert"]
            if entry.get("slug"):
                slug = entry["slug"]
            if entry.get("plan"):
                record_plan = _plan_key(str(entry["plan"]))

    return {
        "plan": record_plan,
        "slug": slug,
        "default_branch": default_branch,
        "last_report": last_report,
        "phases": phases,
        "total_cost_usd": round(total_cost, 6),
        "last_assert": last_assert,
        "invocation_count": len(entries),
    }


def merge_status_with_record(
    status: dict[str, Any],
    record_summary: dict[str, Any],
) -> dict[str, Any]:
    """Attach record rollup next to git-derived status (no duplicate closed[])."""
    return {
        **status,
        "run_record": record_summary,
    }


def resolve_record_path(explicit: str | Path | None) -> Path | None:
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get("DRIVER_RUN_RECORD", "").strip()
    if env:
        return Path(env)
    return None
