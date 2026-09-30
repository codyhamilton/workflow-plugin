"""Deterministic PostToolBatch gate thresholds (maps-grounded).

Validated by gate_threshold_simulation.py against headline maps aggregates
and named workers from evidence-maps-claude-5h.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Workflow ideal band (docs/analysis/2026-09-08-workflow-vs-field.md; maps JSON).
IDEAL_TURNS_LO = 50
IDEAL_TURNS_HI = 75
IDEAL_CTX_LO = 100_000
IDEAL_CTX_HI = 125_000

# Trip points (closed recommendation for white paper).
BAND_EXIT_TURNS = 76  # first turn outside 50–75 band (log-only, no Jev)
WARN_TURNS = 75  # inclusive: at 75 still in band top; signal at 76 via BAND_EXIT
HANDOFF_SIGNAL_TURNS = 85  # optional Jev eligibility (progress/size question)
ESCALATE_TURNS = 100  # maps OVER_TURNS flag threshold (8/150 workers)

PEAK_CTX_WARN = 125_000  # maps OVER_CTX neighborhood
PEAK_CTX_JEV = 128_000  # between warn and 130k smoking-gun worker
PEAK_CTX_ESCALATE = 130_000

JSONL_BYTES_WARN = 3 * 1024 * 1024  # early fat transcript
JSONL_BYTES_ESCALATE = 5 * 1024 * 1024  # maps FAT_JSONL pattern (~12.7MB worker)


@dataclass(frozen=True)
class GateFlags:
    band_exit: bool
    handoff_signal: bool
    escalate: bool
    jev_eligible: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "band_exit": self.band_exit,
            "handoff_signal": self.handoff_signal,
            "escalate": self.escalate,
            "jev_eligible": self.jev_eligible,
            "reasons": list(self.reasons),
        }


def evaluate_gate(
    *,
    api_turns: int,
    peak_ctx_tokens: int | None = None,
    transcript_bytes: int | None = None,
) -> GateFlags:
    """Pure deterministic gate; does not call Jev."""
    reasons: list[str] = []
    peak = peak_ctx_tokens or 0
    tbytes = transcript_bytes or 0

    band_exit = api_turns >= BAND_EXIT_TURNS
    if band_exit:
        reasons.append(f"api_turns>={BAND_EXIT_TURNS}")

    handoff = api_turns >= HANDOFF_SIGNAL_TURNS
    if peak >= PEAK_CTX_WARN:
        handoff = True
        reasons.append(f"peak_ctx>={PEAK_CTX_WARN}")
    if tbytes >= JSONL_BYTES_WARN:
        handoff = True
        reasons.append(f"transcript_bytes>={JSONL_BYTES_WARN}")

    escalate = api_turns >= ESCALATE_TURNS
    if peak >= PEAK_CTX_ESCALATE:
        escalate = True
        reasons.append(f"peak_ctx>={PEAK_CTX_ESCALATE}")
    if tbytes >= JSONL_BYTES_ESCALATE:
        escalate = True
        reasons.append(f"transcript_bytes>={JSONL_BYTES_ESCALATE}")

    jev_eligible = handoff and (
        api_turns >= HANDOFF_SIGNAL_TURNS
        or peak >= PEAK_CTX_JEV
        or tbytes >= JSONL_BYTES_WARN
    )
    if jev_eligible:
        reasons.append("jev_eligible")

    return GateFlags(
        band_exit=band_exit,
        handoff_signal=handoff,
        escalate=escalate,
        jev_eligible=jev_eligible,
        reasons=tuple(dict.fromkeys(reasons)),
    )


def thresholds_documentation() -> dict[str, Any]:
    return {
        "ideal_band": {
            "turns": [IDEAL_TURNS_LO, IDEAL_TURNS_HI],
            "peak_ctx_tokens": [IDEAL_CTX_LO, IDEAL_CTX_HI],
        },
        "trip_points": {
            "band_exit_turns": BAND_EXIT_TURNS,
            "handoff_signal_turns": HANDOFF_SIGNAL_TURNS,
            "escalate_turns": ESCALATE_TURNS,
            "peak_ctx_warn": PEAK_CTX_WARN,
            "peak_ctx_jev": PEAK_CTX_JEV,
            "peak_ctx_escalate": PEAK_CTX_ESCALATE,
            "transcript_bytes_warn": JSONL_BYTES_WARN,
            "transcript_bytes_escalate": JSONL_BYTES_ESCALATE,
        },
        "rationale": {
            "band_exit": "Maps: 16% (24/150) over ideal; logging at 76 catches exit from 50–75 without per-turn Jev inside the band.",
            "escalate_turns": "Maps: 8/150 workers exceeded 100 API turns; 296-call worker had zero prior signal today.",
            "peak_ctx": "Maps: 17/150 over 125k; peak (not final) is sizing signal; worker 92a48e at 130k peak.",
            "jsonl_bytes": "Worker 92a48e: 12.7MB JSONL with FAT_JSONL flag; 5MB escalate is conservative early warning.",
            "jev_eligible": "Optional Jev only after handoff_signal; caps calls to ~minority of workers (maps 16% over ideal).",
        },
    }
