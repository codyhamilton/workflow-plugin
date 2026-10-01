"""jev.classify / typesafe.classify dry-run handler (no socket)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from bootstrap import ensure_progressive_proofs
from paths import REPO_ROOT
from pack_io import pack_row_to_jev_state
from schemas import (
    DEFAULT_INSTRUCTION,
    FRAMING_REGISTRY,
    JEV_MODEL,
    SCHEMA_BUILDERS,
    STATE_CHAR_LIMIT,
    cache_key,
    canonical_questions_json,
    framing_id,
    schema_needs_prose,
    state_json_len,
)

TYPESAFE_ENDPOINT = "https://api.typesafe.ai/v1/systemone"


def _preflight_questions(questions: dict[str, Any]) -> str | None:
    transcript_root = str(REPO_ROOT / "tools" / "transcript")
    if transcript_root not in sys.path:
        sys.path.insert(0, transcript_root)
    from lib.jev_client import validate_systemone_questions  # noqa: WPS433

    try:
        validate_systemone_questions(questions)
    except ValueError as e:
        return str(e)
    return None


def _checkout_questions(question_set: str) -> dict[str, Any]:
    ensure_progressive_proofs()
    from session_checkout import session_checkout_questions  # type: ignore

    return session_checkout_questions(question_set)


def resolve_questions(
    schema_id: str,
    framing_slug: str,
    *,
    evidence_class: str,
    question_set: str = "Y_full",
    questions_override: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    if questions_override is not None:
        return questions_override, None
    if schema_id == "session-checkout":
        if framing_slug != "Y_full":
            return None, "unregistered_framing"
        return _checkout_questions(question_set), None
    table = FRAMING_REGISTRY.get(schema_id) or {}
    if framing_slug not in table:
        return None, "unregistered_framing"
    return table[framing_slug], None


def classify(
    *,
    schema_id: str,
    framing_slug: str,
    state: dict[str, Any],
    evidence_class: str,
    live: bool = False,
    confirm_live: bool = False,
    question_set: str = "Y_full",
    instruction: str = DEFAULT_INSTRUCTION,
    questions_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    questions, reg_err = resolve_questions(
        schema_id,
        framing_slug,
        evidence_class=evidence_class,
        question_set=question_set,
        questions_override=questions_override,
    )
    if reg_err:
        return {
            "decision": "missing",
            "reason": reg_err,
            "schema_id": schema_id,
            "framing_id": framing_slug,
            "cache_key": None,
            "model": JEV_MODEL,
        }

    if schema_id != "session-checkout":
        builder = SCHEMA_BUILDERS.get(schema_id)
        if builder and not questions:
            questions = builder(evidence_class)
        if not questions:
            return {
                "decision": "missing",
                "reason": "prose_required",
                "schema_id": schema_id,
                "framing_id": framing_slug,
                "cache_key": None,
                "model": JEV_MODEL,
                "would_post": False,
            }
        if schema_needs_prose(schema_id, questions or {}) and evidence_class != "prose":
            return {
                "decision": "missing",
                "reason": "prose_required",
                "schema_id": schema_id,
                "framing_id": framing_slug,
                "cache_key": None,
                "model": JEV_MODEL,
            }

    if questions is None:
        return {
            "decision": "missing",
            "reason": "unregistered_framing",
            "schema_id": schema_id,
            "framing_id": framing_slug,
            "cache_key": None,
            "model": JEV_MODEL,
        }

    preflight_err = _preflight_questions(questions)
    if preflight_err:
        return {
            "decision": "missing",
            "reason": "invalid_questions",
            "detail": preflight_err,
            "schema_id": schema_id,
            "framing_id": framing_id(framing_slug, questions),
            "cache_key": None,
            "model": JEV_MODEL,
            "would_post": False,
        }

    size = state_json_len(state)
    if size > STATE_CHAR_LIMIT:
        return {
            "decision": "missing",
            "reason": "state_guard",
            "schema_id": schema_id,
            "framing_id": framing_id(framing_slug, questions),
            "state_chars": size,
            "cache_key": None,
            "model": JEV_MODEL,
        }

    stored_fid = framing_id(framing_slug, questions)
    request = {
        "model": JEV_MODEL,
        "state": state,
        "questions": questions,
    }
    key = cache_key(
        endpoint=TYPESAFE_ENDPOINT,
        model=JEV_MODEL,
        questions=questions,
        state=state,
        instruction=instruction,
    )

    has_key = bool(os.environ.get("TYPESAFE_API_KEY", "").strip())
    if live and confirm_live and not has_key:
        return {
            "decision": "missing",
            "reason": "missing_api_key",
            "schema_id": schema_id,
            "framing_id": stored_fid,
            "cache_key": key,
            "model": JEV_MODEL,
            "would_post": False,
        }

    would_post = live and confirm_live and has_key
    return {
        "decision": "dry_run",
        "schema_id": schema_id,
        "framing_id": stored_fid,
        "cache_key": key,
        "request": request,
        "model": JEV_MODEL,
        "would_post": would_post,
    }


def checkout_y_full_request_from_state(state: dict[str, Any]) -> dict[str, Any]:
    ensure_progressive_proofs()
    from session_checkout import build_jev_request  # type: ignore

    return build_jev_request(state, "Y_full")


def questions_text_from_request(request: dict[str, Any]) -> str:
    return canonical_questions_json(request.get("questions") or {})
