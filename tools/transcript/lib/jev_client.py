"""Thin client for TypeSafe System One (Jev)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-1.13.0"
ALLOWED_QUESTION_TYPES = frozenset({"choice", "score", "noul"})

SESSION_KIND_CRITERIA: dict[str, str] = {
    "question": "User seeking explanation or advice; little implementation",
    "plan": "Designing, spiking, or writing a spec",
    "build": "Implementing or scaffolding code as the main thrust",
    "debug": "Fixing failures, errors, or regressions",
    "review": "Reviewing diffs, PRs, or prior agent output",
    "ops": "Install, config, deploy, CI, environment",
    "research": "Surveying docs/repo/web before deciding",
    "workflow": "Running or tuning the iterate/lab workflow itself",
    "chat": "Casual or off-task conversation",
    "mixed": "No single dominant kind",
    "other": "Does not fit the labels above",
}

SESSION_KIND_INSTRUCTIONS = (
    "What is the single dominant kind of this agent session, given the snapshot? "
    "Prefer the user's intent and tool mix over isolated phrases. "
    "Use mixed only when two kinds are roughly equal; other only as last resort."
)

WORKFLOW_ALIGNMENT_INSTRUCTIONS = (
    "How aligned is this session with a deliberate iterate-style workflow "
    "(research → plan → execute → review), versus ad-hoc chatting or thrashing?"
)

WORKFLOW_ALIGNMENT_CRITERIA: list[str] = [
    "Ad-hoc chat or thrashing; no clear phase discipline",
    "Loose goal; some structure but skips planning or review",
    "Clear phases present; mostly on-rails for the task",
    "Tight workflow execution (phases, gates, eval/cost hygiene)",
]


def require_api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "TYPESAFE_API_KEY is not set. Export it for live classify, or use --dry-run."
        )
    return key


def build_questions(*, include_workflow_alignment: bool = True) -> dict[str, Any]:
    questions: dict[str, Any] = {
        "session_kind": {
            "type": "choice",
            "instructions": SESSION_KIND_INSTRUCTIONS,
            "criteria": SESSION_KIND_CRITERIA,
        },
    }
    if include_workflow_alignment:
        questions["workflow_alignment"] = {
            "type": "score",
            "instructions": WORKFLOW_ALIGNMENT_INSTRUCTIONS,
            "criteria": WORKFLOW_ALIGNMENT_CRITERIA,
        }
    return questions


def validate_systemone_questions(questions: dict[str, Any]) -> None:
    """Reject question shapes TypeSafe System One will not accept (before HTTP)."""
    if not isinstance(questions, dict):
        raise ValueError("questions must be a JSON object")
    for qid, spec in questions.items():
        if not isinstance(spec, dict):
            raise ValueError(f"question '{qid}': must be an object")
        qtype = spec.get("type")
        if qtype not in ALLOWED_QUESTION_TYPES:
            allowed = ", ".join(sorted(ALLOWED_QUESTION_TYPES))
            raise ValueError(
                f"question '{qid}': type '{qtype}' is invalid; allowed: {allowed}"
            )
        criteria = spec.get("criteria")
        if qtype == "score":
            if not isinstance(criteria, list):
                raise ValueError(
                    f"question '{qid}': score criteria must be an array of level strings"
                )
        elif qtype == "choice":
            if not isinstance(criteria, dict):
                raise ValueError(f"question '{qid}': choice criteria must be a map")


def validate_systemone_request(request: dict[str, Any]) -> None:
    questions = request.get("questions")
    if questions is None:
        raise ValueError("request missing questions")
    validate_systemone_questions(questions)


def build_request(
    state: dict[str, Any],
    *,
    include_workflow_alignment: bool = True,
) -> dict[str, Any]:
    return {
        "model": JEV_MODEL,
        "state": state,
        "questions": build_questions(include_workflow_alignment=include_workflow_alignment),
    }


def post_systemone(request: dict[str, Any], *, api_key: str | None = None) -> dict[str, Any]:
    key = (api_key or os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if not key:
        require_api_key()

    try:
        validate_systemone_request(request)
    except ValueError as e:
        raise SystemExit(f"TypeSafe request preflight failed: {e}") from e

    body = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"TypeSafe API HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"TypeSafe API request failed: {e}") from e

    return json.loads(raw)
