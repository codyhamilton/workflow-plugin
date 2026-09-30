"""Compact Jev state + request builders for four cheap-judgement use cases.

Dry-run validated in test_proofs.py (no live API). Pin: jev-1.13.0.
"""

from __future__ import annotations

import json
from typing import Any

JEV_MODEL = "jev-1.13.0"


def _size_guard(state: dict[str, Any], limit: int = 12_000) -> None:
    encoded = json.dumps(state, ensure_ascii=False)
    if len(encoded) > limit:
        raise ValueError(f"state JSON length {len(encoded)} exceeds budget {limit}")


def build_session_progress_request(state: dict[str, Any]) -> dict[str, Any]:
    """Use case 1 — PostToolBatch after deterministic gate."""
    _size_guard(state)
    return {
        "model": JEV_MODEL,
        "state": state,
        "questions": {
            "progress_vs_scope": {
                "type": "score",
                "instructions": (
                    "Given compact session counters (turns, peak context estimate, brief id) "
                    "and the last tool batch summary, how well is the worker progressing "
                    "against its stated scope versus wandering or re-reading?"
                ),
                "criteria": [
                    "Clearly off-scope or thrashing; repeated reads with no forward progress",
                    "Weak progress; scope drift or stall likely",
                    "Moderate progress; some redundancy",
                    "Solid progress on stated scope with acceptable exploration",
                ],
            },
            "handoff_recommended": {
                "type": "choice",
                "instructions": (
                    "Should a parent orchestrator consider handoff or split work soon? "
                    "This is advisory only."
                ),
                "criteria": {
                    "continue": "Worker should continue as-is",
                    "monitor": "Surface signal to parent; no handoff yet",
                    "handoff_soon": "Parent should plan handoff or narrower sub-brief",
                },
            },
        },
    }


def build_refine_brief_request(state: dict[str, Any]) -> dict[str, Any]:
    """Use case 2 — single brief complexity (call once per brief)."""
    _size_guard(state)
    return {
        "model": JEV_MODEL,
        "state": state,
        "questions": {
            "brief_complexity": {
                "type": "score",
                "instructions": (
                    "How large / risky is this execute brief relative to the DESIGN phase "
                    "outcome and typical unit size?"
                ),
                "criteria": [
                    "Small, well-bounded unit",
                    "Moderate scope; standard execute",
                    "Large brief; likely multi-session or needs human skim",
                    "Mega-brief; high burn risk before spawn",
                ],
            },
        },
    }


def build_unit_needs_review_request(state: dict[str, Any]) -> dict[str, Any]:
    """Use case 3 — unit complete."""
    _size_guard(state)
    return {
        "model": JEV_MODEL,
        "state": state,
        "questions": {
            "needs_review": {
                "type": "choice",
                "instructions": (
                    "Given the unit closing record (headings, verification excerpt, trailer), "
                    "should a human or comprehensive-review agent spend time on this unit?"
                ),
                "criteria": {
                    "skip": "Low risk; log only",
                    "maybe": "Borderline; sample or light skim",
                    "review": "Worth spawning review before merge",
                },
            },
            "review_confidence": {
                "type": "score",
                "instructions": "Confidence that skipping review would miss a material defect.",
                "criteria": [
                    "Very low risk of hidden defect",
                    "Low risk",
                    "Material uncertainty",
                    "High risk; review warranted",
                ],
            },
        },
    }


def build_phase_alignment_sanity_request(state: dict[str, Any]) -> dict[str, Any]:
    """Use case 4 — phase complete (does NOT replace outcome-evidence / kill line)."""
    _size_guard(state)
    return {
        "model": JEV_MODEL,
        "state": state,
        "questions": {
            "alignment_sanity": {
                "type": "score",
                "instructions": (
                    "Does the closing narrative match the design outcome intent? "
                    "This is a dig-deeper hint only; deterministic assert already passed."
                ),
                "criteria": [
                    "Narrative contradicts or ignores design intent",
                    "Thin alignment; intent only loosely addressed",
                    "Adequate alignment with minor gaps",
                    "Strong alignment with design outcome intent",
                ],
            },
        },
    }


def example_states() -> dict[str, dict[str, Any]]:
    """Minimal fixtures sized for jev-1.13.0 state budget."""
    return {
        "session_progress": {
            "question_id": "session-progress",
            "slug": "open-pajero-maps",
            "phase": 3,
            "brief_id": "unit-3c-api",
            "api_turns": 88,
            "peak_ctx_tokens": 127_000,
            "transcript_bytes": 4_200_000,
            "last_tool_batch": ["Read:src/foo.ts", "Grep:TODO"],
            "design_outcome_line": "Phase 3C API routes compile and tests pass.",
        },
        "refine_brief": {
            "question_id": "refine-brief-complexity",
            "slug": "open-pajero-maps",
            "phase": 3,
            "brief_id": "6c87c96bd9bb",
            "brief_title": "Refine Phase 3C",
            "brief_line_count": 240,
            "brief_excerpt": "### Scope\nImplement handlers for ...",
            "design_outcome": "Phase 3C delivers API parity for maps tiles.",
        },
        "unit_needs_review": {
            "question_id": "unit-needs-review",
            "slug": "trailer-completeness",
            "phase": 2,
            "unit_id": "u2-auth",
            "closing_headings": ["Verification", "Carried"],
            "closing_body_excerpt": "Verification: pytest tools/driver -k assert ...",
            "trailer": "trailer-completeness:2",
            "verifier_exit_code": 0,
        },
        "phase_alignment": {
            "question_id": "phase-alignment-sanity",
            "slug": "trailer-completeness",
            "phase": 2,
            "design_outcome": "Phase 2 closes with mechanical verifier on assert_state.",
            "closing_headings": ["Verification", "Carried"],
            "closing_body_excerpt": "Verified via python3 evals/.../verify.py exit 0.",
            "workflow_report": {"status": "closed", "phase": 2},
            "trailer": "trailer-completeness:2",
        },
    }


BUILDERS = {
    "session_progress": build_session_progress_request,
    "refine_brief": build_refine_brief_request,
    "unit_needs_review": build_unit_needs_review_request,
    "phase_alignment": build_phase_alignment_sanity_request,
}
