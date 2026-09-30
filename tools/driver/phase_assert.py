"""Phase-boundary assert: compact state, deterministic check, optional Jev log."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

QUESTION_OUTCOME_EVIDENCE = "outcome-evidence"
JEV_MODEL = "jev-1.13.0"
SCORE_PASS_THRESHOLD = 2.5

FAIL_BRANCH = "stop_and_escalate"

_OUTCOME_EVIDENCE_INSTRUCTIONS = (
    "Given the compact phase state (design outcome line, closing-record headings and "
    "body, workflow-report, and git trailer), how well does the closing record show "
    "that the phase outcome was verified — not merely claimed?"
)

_OUTCOME_EVIDENCE_CRITERIA: list[str] = [
    "No verification section or only placeholder text; outcome not evidenced",
    "Verification mentioned but does not tie to the design outcome",
    "Verification present with partial evidence (commands named but not tied to outcome)",
    "Clear verification evidence linked to the stated phase outcome",
]


def state_hash(state: dict[str, Any]) -> str:
    payload = json.dumps(state, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _headings_set(state: dict[str, Any]) -> set[str]:
    closing = state.get("closing_record") or {}
    headings = closing.get("headings") or []
    return {_normalize_text(str(h)) for h in headings}


def _trailer_phase(trailer: str, slug: str) -> int | None:
    trailer = (trailer or "").strip()
    if trailer == f"{slug}:done":
        return None
    if ":" not in trailer:
        return None
    left, right = trailer.rsplit(":", 1)
    if left != slug:
        return None
    try:
        return int(right)
    except ValueError:
        return None


def _report_phase_value(report: dict[str, Any]) -> int | str | None:
    phase = report.get("phase")
    if phase is None:
        return None
    if isinstance(phase, int):
        return phase
    if isinstance(phase, str) and phase.isdigit():
        return int(phase)
    return phase


@dataclass(frozen=True)
class DeterministicResult:
    pass_: bool
    checks: dict[str, bool]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass": self.pass_,
            "checks": self.checks,
            "reasons": self.reasons,
        }


def deterministic_outcome_evidence(state: dict[str, Any]) -> DeterministicResult:
    """Mechanical checks on compact phase state (authoritative for pass/fail)."""
    slug = str(state.get("slug") or "")
    phase = state.get("phase")
    trailer = str(state.get("trailer") or "")
    design_outcome = str(state.get("design_outcome") or "")
    closing = state.get("closing_record") or {}
    body = str(closing.get("body") or "")
    report = state.get("workflow_report") or {}

    checks: dict[str, bool] = {}
    reasons: list[str] = []

    report_status = str(report.get("status") or "")
    checks["report_closed"] = report_status == "closed"
    if not checks["report_closed"]:
        reasons.append("workflow_report.status is not closed")

    trailer_n = _trailer_phase(trailer, slug)
    checks["trailer_matches_slug"] = trailer_n is not None or trailer == f"{slug}:done"
    if trailer and trailer_n is None and trailer != f"{slug}:done":
        reasons.append("trailer does not match slug:phase")
        checks["trailer_matches_slug"] = False

    report_phase = _report_phase_value(report)
    if trailer_n is not None and phase is not None:
        checks["report_phase_matches"] = report_phase == phase
        if not checks["report_phase_matches"]:
            reasons.append("workflow_report.phase does not match state.phase")
        checks["trailer_phase_matches"] = trailer_n == phase
        if not checks["trailer_phase_matches"]:
            reasons.append("trailer phase index does not match state.phase")
    else:
        checks["report_phase_matches"] = True
        checks["trailer_phase_matches"] = True

    headings = _headings_set(state)
    has_verification = any(
        "verification" in h for h in headings
    )
    has_carried = any("carried" in h for h in headings)
    checks["headings_verification"] = has_verification
    checks["headings_carried"] = has_carried
    if not has_verification:
        reasons.append("closing record missing a Verification heading")
    if not has_carried:
        reasons.append("closing record missing a Carried heading")

    norm_body = _normalize_text(body)
    norm_outcome = _normalize_text(design_outcome)
    outcome_in_body = bool(norm_outcome) and norm_outcome in norm_body
    verification_block = re.search(
        r"(?:###\s*)?verification[^\n]*\n+(.+?)(?:\n###|\Z)",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    verification_substantive = bool(
        verification_block and len(verification_block.group(1).strip()) >= 24
    )
    checks["outcome_or_verification_evidence"] = outcome_in_body or verification_substantive
    if not checks["outcome_or_verification_evidence"]:
        reasons.append(
            "design outcome not quoted in closing body and verification block too thin"
        )

    pass_ = all(checks.values())
    return DeterministicResult(pass_=pass_, checks=checks, reasons=reasons)


def jev_state_slice(state: dict[str, Any]) -> dict[str, Any]:
    """Compact object sent to Jev (not a transcript snapshot)."""
    closing = state.get("closing_record") or {}
    return {
        "question_id": state.get("question_id", QUESTION_OUTCOME_EVIDENCE),
        "slug": state.get("slug"),
        "phase": state.get("phase"),
        "design_outcome": state.get("design_outcome"),
        "closing_headings": closing.get("headings"),
        "closing_body": closing.get("body"),
        "workflow_report": state.get("workflow_report"),
        "trailer": state.get("trailer"),
    }


def build_jev_request(state: dict[str, Any]) -> dict[str, Any]:
    jev_state = jev_state_slice(state)
    return {
        "model": JEV_MODEL,
        "state": jev_state,
        "questions": {
            "outcome_evidence": {
                "type": "score",
                "instructions": _OUTCOME_EVIDENCE_INSTRUCTIONS,
                "criteria": _OUTCOME_EVIDENCE_CRITERIA,
            },
        },
    }


def jev_score_from_response(response: dict[str, Any]) -> float | None:
    answers = response.get("answers") or {}
    raw = answers.get("outcome_evidence")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, dict):
        for key in ("value", "score", "answer"):
            if key in raw and isinstance(raw[key], (int, float)):
                return float(raw[key])
    return None


def jev_pass_from_score(score: float | None) -> bool:
    if score is None:
        return False
    return score >= SCORE_PASS_THRESHOLD


@dataclass(frozen=True)
class AssertResult:
    question_id: str
    pass_: bool
    fail_branch: str
    decision_source: str
    state_hash: str
    deterministic: DeterministicResult
    jev_score: float | None
    jev_pass: bool | None
    jev_disagreed: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "pass": self.pass_,
            "fail_branch": self.fail_branch if not self.pass_ else None,
            "decision_source": self.decision_source,
            "state_hash": self.state_hash,
            "deterministic": self.deterministic.to_dict(),
            "jev": (
                None
                if self.jev_score is None and self.jev_pass is None
                else {
                    "score": self.jev_score,
                    "pass": self.jev_pass,
                    "threshold": SCORE_PASS_THRESHOLD,
                    "disagreed_with_deterministic": self.jev_disagreed,
                }
            ),
        }


def evaluate_assert(
    state: dict[str, Any],
    *,
    jev_response: dict[str, Any] | None = None,
) -> AssertResult:
    """
    Pass/fail is always the deterministic check (kill line).

    When Jev is called, its score is logged; if it disagrees with deterministic
    on the same state, decision_source stays deterministic and jev_disagreed is set.
    """
    question_id = str(state.get("question_id") or QUESTION_OUTCOME_EVIDENCE)
    det = deterministic_outcome_evidence(state)
    jev_score: float | None = None
    jev_pass: bool | None = None
    jev_disagreed = False
    decision_source = "deterministic"

    if jev_response is not None:
        jev_score = jev_score_from_response(jev_response)
        jev_pass = jev_pass_from_score(jev_score)
        if jev_pass is not None and jev_pass != det.pass_:
            jev_disagreed = True

    return AssertResult(
        question_id=question_id,
        pass_=det.pass_,
        fail_branch=FAIL_BRANCH,
        decision_source=decision_source,
        state_hash=state_hash(state),
        deterministic=det,
        jev_score=jev_score,
        jev_pass=jev_pass,
        jev_disagreed=jev_disagreed,
    )
