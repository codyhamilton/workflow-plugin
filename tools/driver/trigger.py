"""Dispatch one phase agent session (resolve → provider → report)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DRIVER = Path(__file__).resolve().parent
_PROVIDERS = _DRIVER / "providers"
for _path in (_DRIVER, _PROVIDERS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from base import DispatchTarget, ProviderUnavailable  # noqa: E402
from report import ReportParseError, WorkflowReport, parse_workflow_report  # noqa: E402
from resolve import PhaseStatus, ResolveError, resolve_plan_folder  # noqa: E402
from picker import select_provider  # noqa: E402


@dataclass(frozen=True)
class TriggerOutcome:
    status: PhaseStatus
    skipped: bool
    skip_reason: str | None
    dispatch: dict[str, Any] | None
    report: WorkflowReport | None
    report_parse_error: str | None
    turns: int | None
    cost_usd: float | None
    provider: str | None
    mode: str | None

    def to_json_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.to_json_dict(),
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "dispatch": self.dispatch,
            "report": self.report.to_json_dict() if self.report else None,
            "report_parse_error": self.report_parse_error,
            "turns": self.turns,
            "cost_usd": self.cost_usd,
            "provider": self.provider,
            "mode": self.mode,
        }
        return payload


def _dispatch_target(status: PhaseStatus) -> DispatchTarget:
    if status.open == "wrap-up":
        return DispatchTarget(kind="wrap-up", phase=None)
    if status.open == "phase":
        return DispatchTarget(kind="phase", phase=status.phase)
    return DispatchTarget(kind="done", phase=None)


def trigger_once(
    plan_folder: Path,
    *,
    default_branch: str | None = None,
    provider: str | None = None,
    dry_run: bool = False,
    fixture_output: Path | None = None,
    review_posture: str = "terminal",
) -> TriggerOutcome:
    status = resolve_plan_folder(
        plan_folder,
        default_branch=default_branch,
    )

    if status.open == "done":
        return TriggerOutcome(
            status=status,
            skipped=True,
            skip_reason="Run already has Workflow-Phase done trailer; nothing to dispatch.",
            dispatch=None,
            report=None,
            report_parse_error=None,
            turns=None,
            cost_usd=None,
            provider=None,
            mode=None,
        )

    target = _dispatch_target(status)
    plan_path = status.plan

    try:
        phase_provider = select_provider(
            provider=provider,
            dry_run=dry_run,
            fixture_output=fixture_output,
        )
    except ProviderUnavailable as exc:
        raise ResolveError(str(exc)) from exc

    run = phase_provider.run_phase(
        plan_folder=plan_path,
        status=status,
        target=target,
        review_posture=review_posture,
    )

    dispatch_info = {
        "target": target.to_json_dict(),
        "review_posture": review_posture,
        "plan_folder": plan_path,
    }

    report: WorkflowReport | None = None
    parse_error: str | None = None
    try:
        report = parse_workflow_report(run.final_output)
    except ReportParseError as exc:
        parse_error = str(exc)

    return TriggerOutcome(
        status=status,
        skipped=False,
        skip_reason=None,
        dispatch=dispatch_info,
        report=report,
        report_parse_error=parse_error,
        turns=run.turns,
        cost_usd=run.cost_usd,
        provider=run.provider or phase_provider.name,
        mode=run.mode,
    )
