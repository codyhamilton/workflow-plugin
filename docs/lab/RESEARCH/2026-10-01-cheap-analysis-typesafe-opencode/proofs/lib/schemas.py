"""Registered framings and schema question JSON for dry-run spikes."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

STATE_CHAR_LIMIT = 12_000
JEV_MODEL = "jev-1.13.0"
PROSE_FIELD_IDS = frozenset(
    {
        "compaction_cycle",
        "no_checkable_step",
        "anchor_divergence",
        "phase_sketch",
        "trajectory",
    }
)
STATS_MECHANICAL_IDS = frozenset({"reread_cluster", "compaction_event_count"})


def _choice(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def _bool_q(instructions: str) -> dict[str, Any]:
    return _choice(
        instructions,
        {"yes": "Yes", "no": "No"},
    )


def questions_early_signal_stats() -> dict[str, Any]:
    return {
        "reread_cluster": _bool_q(
            "Does any single read path appear at least three times in cumulative.reread_paths?"
        ),
        "compaction_event_count": {
            "type": "report",
            "instructions": "Report cumulative.compaction_event_count as an integer (not a judgment).",
        },
    }


def questions_early_signal_prose() -> dict[str, Any]:
    base = questions_early_signal_stats()
    base.update(
        {
            "compaction_cycle": _bool_q(
                "Does the prefix show compaction churn without durable new artifacts?"
            ),
            "no_checkable_step": _bool_q(
                "Since the prior checkpoint (or start), is there motion without a checkable step?"
            ),
            "anchor_divergence": _bool_q(
                "Is the latest work drifting from brief_anchor?"
            ),
        }
    )
    return base


def questions_shape_v0_stats() -> dict[str, Any]:
    return {"reread_cluster": questions_early_signal_stats()["reread_cluster"]}


def questions_shape_v0_prose() -> dict[str, Any]:
    return {
        "compaction_cycle": questions_early_signal_prose()["compaction_cycle"],
        "no_checkable_step": questions_early_signal_prose()["no_checkable_step"],
        "anchor_divergence": questions_early_signal_prose()["anchor_divergence"],
        "reread_cluster": questions_early_signal_stats()["reread_cluster"],
    }


def questions_phase_sketch_v0_prose() -> dict[str, Any]:
    return {
        "phase_sketch": _choice(
            "Order up to three phase tags that best describe the prefix (first match wins).",
            {
                "orient": "orient",
                "search": "search",
                "edit": "edit",
                "verify": "verify",
                "replan": "replan",
                "stall": "stall",
            },
        )
    }


def questions_phase_sketch_v0_stats() -> dict[str, Any]:
    return {}


SCHEMA_BUILDERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "early-signal-v0": lambda ev: (
        questions_early_signal_prose() if ev == "prose" else questions_early_signal_stats()
    ),
    "shape-v0": lambda ev: (
        questions_shape_v0_prose() if ev == "prose" else questions_shape_v0_stats()
    ),
    "phase-sketch-v0": lambda ev: (
        questions_phase_sketch_v0_prose() if ev == "prose" else questions_phase_sketch_v0_stats()
    ),
}

# Registered framing slugs → canonical question JSON per schema
FRAMING_REGISTRY: dict[str, dict[str, dict[str, Any]]] = {
    "early-signal-v0": {
        "signal-v0-default": questions_early_signal_stats(),
        "signal-v0-alt": {
            **questions_early_signal_stats(),
            "reread_cluster": _bool_q(
                "Mechanical: is any reread_paths[].count >= 3 in the snapshot state?"
            ),
        },
    },
    "shape-v0": {
        "shape-v0-default": questions_shape_v0_stats(),
    },
    "phase-sketch-v0": {
        "phase-v0-default": questions_phase_sketch_v0_prose(),
    },
    "session-checkout": {},
}


def canonical_questions_json(questions: dict[str, Any]) -> str:
    return json.dumps(questions, ensure_ascii=False, sort_keys=True)


def framing_id(slug: str, questions: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_questions_json(questions).encode("utf-8")).hexdigest()[:16]
    return f"{slug}#{digest}"


def schema_needs_prose(schema_id: str, questions: dict[str, Any]) -> bool:
    if schema_id == "phase-sketch-v0":
        return bool(questions)
    return bool(PROSE_FIELD_IDS.intersection(questions.keys()))


def state_json_len(state: dict[str, Any]) -> int:
    return len(json.dumps(state, ensure_ascii=False))


def cache_key(
    *,
    endpoint: str,
    model: str,
    questions: dict[str, Any],
    state: dict[str, Any],
    instruction: str,
    sampling: dict[str, Any] | None = None,
) -> str:
    payload = {
        "endpoint": endpoint,
        "model": model,
        "questions": questions,
        "state": state,
        "instruction": instruction,
        "sampling": sampling or {},
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


DEFAULT_INSTRUCTION = (
    "Answer only from the provided state JSON. Return a JSON object mapping question ids to answers."
)
