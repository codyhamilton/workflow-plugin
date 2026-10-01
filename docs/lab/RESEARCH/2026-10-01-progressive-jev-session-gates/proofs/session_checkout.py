"""session-checkout questions, fail-open rule R(t), and metric arithmetic.

Question id ``session-checkout`` is not added to the resolved
``session-progress`` builder. ``Y_legacy`` reuses that builder's question text.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from snapshot_state import JEV_MODEL, REQUEST_CHAR_SOFT, assert_state_within_budget

QUESTION_SET_FULL = "Y_full"
QUESTION_SET_CHOICE = "Y_choice_only"
QUESTION_SET_LEGACY = "Y_legacy"

_CHEAP_SCHEMAS = (
    Path(__file__).resolve().parents[2]
    / "2026-09-30-jev-cheap-judgement-signals"
    / "proofs"
    / "jev_signal_schemas.py"
)


def _score(instructions: str, criteria: list[str]) -> dict[str, Any]:
    return {"type": "score", "instructions": instructions, "criteria": criteria}


def _choice(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


RUNAWAY_PATTERN = _score(
    "On this prefix snapshot, how strong is repeated thrash "
    "(re-reading the same paths, polling or sleeping, compaction churn) "
    "relative to new work?",
    [
        "No repeated thrash in the snapshot",
        "A small repeat or stall that still has a next step",
        "Clear re-reads, polls, or compaction churn, with weak new output",
        "Thrash is the dominant pattern in the snapshot",
    ],
)

PROGRESS_SINCE_PRIOR = _score(
    "Since prior_checkpoint_turn (or since the start, when that field is null), "
    "how much checkable progress does the snapshot show against brief_anchor?",
    [
        "No new artifact, edit, test outcome, or narrowing decision",
        "Motion without a checkable step (more reads, a restated plan)",
        "One checkable step: an edit, a test result, or a decision that narrows the brief",
        "Clear delivery against the brief anchor",
    ],
)

SCOPE_DRIFT = _score(
    "How far is the latest work from brief_anchor?",
    [
        "The latest work matches the brief anchor",
        "Adjacent exploration that still serves the anchor",
        "Substantial work on a different task",
        "The latest work is a different task from the anchor",
    ],
)

CHECKOUT_NOW = _choice(
    "Should this worker be checked out now (stop continuing this worker; "
    "hand off or end the run)? Judge only the snapshot. Later turns are not "
    "in the snapshot. This is a counterfactual label for offline tuning.",
    {
        "continue": "The worker should keep going until the next checkpoint",
        "inconclusive": "The snapshot does not justify checkout",
        "checkout": "Continuing past this checkpoint is a mistake",
    },
)

CHECKOUT_CONFIDENCE = _score(
    "How sure are you of checkout_now? Score the confidence of that choice, "
    "not the severity of the task.",
    [
        "A guess",
        "Weak; a careful reader could easily disagree",
        "Moderate; a careful reader might disagree",
        "The snapshot would convince a careful reader",
    ],
)


def session_checkout_questions(question_set: str = QUESTION_SET_FULL) -> dict[str, Any]:
    if question_set == QUESTION_SET_FULL:
        return {
            "runaway_pattern": RUNAWAY_PATTERN,
            "progress_since_prior": PROGRESS_SINCE_PRIOR,
            "scope_drift": SCOPE_DRIFT,
            "checkout_now": CHECKOUT_NOW,
            "checkout_confidence": CHECKOUT_CONFIDENCE,
        }
    if question_set == QUESTION_SET_CHOICE:
        return {
            "checkout_now": CHECKOUT_NOW,
            "checkout_confidence": CHECKOUT_CONFIDENCE,
        }
    if question_set == QUESTION_SET_LEGACY:
        return legacy_session_progress_questions()
    raise ValueError(f"unknown question set {question_set!r}")


def legacy_session_progress_questions() -> dict[str, Any]:
    """Resolved pair from jev_signal_schemas.build_session_progress_request."""
    spec = importlib.util.spec_from_file_location("jev_signal_schemas", _CHEAP_SCHEMAS)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {_CHEAP_SCHEMAS}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    request = module.build_session_progress_request({"question_id": "session-progress"})
    return request["questions"]


def build_jev_request(state: dict[str, Any], question_set: str = QUESTION_SET_FULL) -> dict[str, Any]:
    """Reject an over-budget state before a request exists."""
    assert_state_within_budget(state)
    return {
        "model": JEV_MODEL,
        "state": state,
        "questions": session_checkout_questions(question_set),
    }


def request_json(request: dict[str, Any]) -> str:
    import json

    return json.dumps(request, ensure_ascii=False)


def request_over_soft_guard(request: dict[str, Any]) -> bool:
    return len(request_json(request)) > REQUEST_CHAR_SOFT


def _answer_value(raw: Any) -> Any:
    if isinstance(raw, dict):
        for key in ("choice", "value", "score", "answer"):
            if key in raw:
                return raw[key]
        return None
    return raw


def as_choice(raw: Any) -> str | None:
    value = _answer_value(raw)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def as_score(raw: Any) -> int | None:
    value = _answer_value(raw)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        if float(value) != int(value):
            return None
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def ungrounded_choice(
    *,
    choice: str | None,
    runaway: int | None,
    progress: int | None,
    drift: int | None,
) -> bool:
    """Checkout while thrash and drift are quiet and progress is real.

    The flag does not change ``gate_exit`` (TERMS §3).
    """
    if choice != "checkout":
        return False
    if runaway not in {0, 1} or drift not in {0, 1} or progress not in {2, 3}:
        return False
    return True


def apply_rule(
    *,
    choice: str | None,
    confidence: int | None,
    confidence_min: int = 3,
    on_uncertain: str = "open",
    missing: bool = False,
    runaway: int | None = None,
    progress: int | None = None,
    drift: int | None = None,
) -> dict[str, Any]:
    """Fail-open unless choice is checkout and confidence >= confidence_min.

    ``decision`` stays ``missing`` when there is no answer. It is not relabeled
    ``continue``. ``fires`` is the only checkout signal.
    """
    if on_uncertain not in {"open", "closed"}:
        raise ValueError(f"on_uncertain must be open or closed, got {on_uncertain!r}")
    flagged = ungrounded_choice(choice=choice, runaway=runaway, progress=progress, drift=drift)
    if missing or choice is None:
        fires = on_uncertain == "closed"
        return {
            "decision": "missing",
            "fires": fires,
            "ungrounded_choice": False,
            "reason": "missing",
        }
    fires = choice == "checkout" and confidence is not None and confidence >= confidence_min
    if not fires and on_uncertain == "closed" and choice in {"inconclusive", "checkout"}:
        fires = True
    return {
        "decision": choice,
        "fires": fires,
        "ungrounded_choice": flagged,
        "reason": None,
    }


def max_allowed_turns(T: int, gate_exit: int | None) -> int:
    return gate_exit if gate_exit is not None else T


def outcome_vs_gold(
    *,
    T: int,
    gate_exit: int | None,
    gold_exit: int | None,
) -> dict[str, Any]:
    """TERMS §8 signs. ``overshoot`` is null unless both exits exist."""
    both = gate_exit is not None and gold_exit is not None
    overshoot = (gate_exit - gold_exit) if both else None
    false_early = gate_exit is not None and (gold_exit is None or gate_exit < gold_exit)
    false_late = gold_exit is not None and (gate_exit is None or gate_exit > gold_exit)
    on_time = both and gate_exit == gold_exit
    return {
        "overshoot": overshoot,
        "false_early": false_early,
        "false_late": false_late,
        "on_time": on_time,
        "max_allowed_turns": max_allowed_turns(T, gate_exit),
    }


def gate_exit_from_rows(rows: list[dict[str, Any]]) -> int | None:
    firing = [row["checkpoint_turn"] for row in rows if row.get("fires")]
    if not firing:
        return None
    return min(firing)


def summarize_metrics(
    *,
    T: int,
    rows: list[dict[str, Any]],
    gold_exit: int | None,
    gold_exit_provided: bool,
    interval: int,
) -> dict[str, Any]:
    gate = gate_exit_from_rows(rows)
    missing = sum(1 for row in rows if row.get("decision") == "missing")
    summary: dict[str, Any] = {
        "first_checkout_turn": gate,
        "max_allowed_turns": max_allowed_turns(T, gate),
        "worker_policy": "checkout" if gate is not None else "continue",
        "missing_rate": (missing / len(rows)) if rows else None,
        "gold_exit": gold_exit if gold_exit_provided else None,
        "overshoot": None,
        "false_early": None,
        "false_late": None,
        "on_time": None,
        "within_one_interval": None,
    }
    if gold_exit_provided:
        scored = outcome_vs_gold(T=T, gate_exit=gate, gold_exit=gold_exit)
        summary.update(scored)
        if scored["overshoot"] is not None:
            summary["within_one_interval"] = abs(scored["overshoot"]) <= interval
        else:
            summary["within_one_interval"] = False
    return summary
