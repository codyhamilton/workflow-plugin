"""Registered question blobs for stats→Jev / frozen-card search (≥8 pool)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from import_paths import ensure_import_paths

ensure_import_paths()

from schemas import canonical_questions_json, framing_id, questions_early_signal_stats

Choice = dict[str, Any]


def _choice(instructions: str, criteria: dict[str, str]) -> Choice:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def _bool_q(instructions: str) -> Choice:
    return _choice(instructions, {"yes": "Yes", "no": "No"})


def _likert_foreshadow() -> dict[str, Any]:
    return {
        "foreshadow_strength": _choice(
            "Rate how strongly the cumulative stats suggest runaway/context thrash "
            "(0=none, 3=strong). Collapse: yes if score ≥ 2.",
            {"0": "none", "1": "weak", "2": "moderate", "3": "strong"},
        ),
        "reread_cluster": questions_early_signal_stats()["reread_cluster"],
    }


def _binary_foreshadow_ids() -> dict[str, Any]:
    return {
        **questions_early_signal_stats(),
        "thrash_bundle": _bool_q(
            "Binary: does compaction slope plus high reread counts match a frozen-narration thrash bundle?"
        ),
        "poll_monitor": _bool_q(
            "Binary: does Monitor tool presence dominate over compaction churn?"
        ),
    }


def _monitor_called_out() -> dict[str, Any]:
    return {
        **questions_early_signal_stats(),
        "monitor_present": _bool_q(
            "Is Monitor count ≥ 1 in cumulative.tool_histogram at this checkpoint?"
        ),
        "thrash_bundle": _bool_q("Compaction rising with flat assistant_text_chars and no Edit/Write?"),
    }


def _no_story_beyond_counts() -> dict[str, Any]:
    return {
        **questions_early_signal_stats(),
        "instruction_scope": {
            "type": "report",
            "instructions": (
                "Do not infer a story beyond the counts. Answer only from printed cumulative fields."
            ),
        },
    }


def _compact_likert_collapsed() -> dict[str, Any]:
    return {
        "compaction_pressure": _choice(
            "Likert compaction pressure (collapse yes if ≥ high).",
            {"low": "low", "mid": "mid", "high": "high"},
        ),
        "reread_cluster": questions_early_signal_stats()["reread_cluster"],
    }


def _echo_guard_reread() -> dict[str, Any]:
    base = questions_early_signal_stats()
    base["reread_cluster"] = _bool_q(
        "Mechanical: is any reread_paths[].count >= 3 in the snapshot state?"
    )
    return base


def _phase_hint_stats() -> dict[str, Any]:
    return {
        **questions_early_signal_stats(),
        "stall_like": _bool_q("Histogram skew: mostly Read/Bash with no Edit/Write through checkpoint?"),
    }


def _anchor_agnostic() -> dict[str, Any]:
    return {
        **questions_early_signal_stats(),
        "scope_drift_hint": _bool_q("Do delta_since_prior tool counts suggest scope drift without naming files?"),
    }


# Slug → canonical question JSON (schema early-signal-v0, stats_card state)
OPEN_FIELD_FRAMING_SLUGS: dict[str, dict[str, Any]] = {
    "tournament-binary-foreshadow": _binary_foreshadow_ids(),
    "tournament-likert-collapsed": _compact_likert_collapsed(),
    "tournament-monitor-called-out": _monitor_called_out(),
    "tournament-no-story-beyond-counts": _no_story_beyond_counts(),
    "pool-likert-foreshadow": _likert_foreshadow(),
    "pool-echo-guard-reread": _echo_guard_reread(),
    "pool-phase-hint-stats": _phase_hint_stats(),
    "pool-anchor-agnostic": _anchor_agnostic(),
    # Aliases into cheap-analysis spike registry (imported at runtime for hashes)
    "signal-v0-default": None,
    "signal-v0-alt": None,
}


def blob_digest(questions: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_questions_json(questions).encode("utf-8")).hexdigest()


def registry_rows(
    cheap_registry: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Emit one row per registered slug with framing_id and question hash."""
    rows: list[dict[str, Any]] = []
    early = cheap_registry.get("early-signal-v0") or {}
    for slug, questions in OPEN_FIELD_FRAMING_SLUGS.items():
        if questions is None:
            questions = early.get(slug)
        if not questions:
            continue
        rows.append(
            {
                "schema_id": "early-signal-v0",
                "slug": slug,
                "framing_id": framing_id(slug, questions),
                "questions_sha256": blob_digest(questions),
                "registered": True,
            }
        )
    return rows


def unregistered_framing_demo() -> dict[str, Any]:
    """Question JSON not present in the registry (for dry-run missing rows)."""
    return {
        "reread_cluster": _bool_q("This blob was never registered before the batch run."),
    }
