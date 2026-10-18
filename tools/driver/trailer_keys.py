"""Canonical git trailer keys and report fence tags (dual-read legacy + yakka)."""

from __future__ import annotations

# Ordered list: readers merge values from every phase trailer key.
PHASE_TRAILER_KEYS: tuple[str, ...] = (
    "Workflow-Phase",
    "Yakka-Phase",
)

PLAN_TRAILER_KEYS: tuple[str, ...] = (
    "Workflow-Plan",
    "Yakka-Plan",
)

REPORT_FENCE_TAGS: tuple[str, ...] = (
    "workflow-report",
    "yakka-report",
)
