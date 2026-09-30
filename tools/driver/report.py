"""Parse workflow-report fenced blocks from phase agent output."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

WORKFLOW_REPORT_FENCE = re.compile(
    r"```workflow-report\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class WorkflowReport:
    status: str  # closed | incomplete | unsuccessful
    phase: int | str  # n or "done"
    reason: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "phase": self.phase,
            "reason": self.reason,
        }


class ReportParseError(ValueError):
    """Could not parse a workflow-report block."""


def parse_workflow_report(text: str) -> WorkflowReport:
    match = WORKFLOW_REPORT_FENCE.search(text)
    if not match:
        raise ReportParseError("No ```workflow-report fenced block in agent output")
    raw = match.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReportParseError(f"workflow-report is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReportParseError("workflow-report JSON must be an object")
    status = data.get("status")
    phase = data.get("phase")
    if status not in ("closed", "incomplete", "unsuccessful"):
        raise ReportParseError(f"Invalid report status: {status!r}")
    if phase is None:
        raise ReportParseError("report missing phase")
    if status != "closed" and not data.get("reason"):
        raise ReportParseError("report requires reason when status is not closed")
    reason = data.get("reason")
    if isinstance(reason, str):
        reason = reason.strip() or None
    return WorkflowReport(status=status, phase=phase, reason=reason)


def format_workflow_report(report: WorkflowReport) -> str:
    """Build agent-final-output text containing exactly one workflow-report fence."""
    body = json.dumps(report.to_json_dict(), indent=2)
    return f"```workflow-report\n{body}\n```\n"
