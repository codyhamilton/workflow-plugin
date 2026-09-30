"""Dry-run provider: proves the report contract without calling an SDK."""

from __future__ import annotations

from pathlib import Path

from base import DispatchTarget, PhaseProvider, ProviderRunResult
from report import WorkflowReport, format_workflow_report
from resolve import PhaseStatus


class DryRunProvider:
    name = "dry-run"

    def __init__(self, *, fixture_output: Path | None = None) -> None:
        self._fixture_output = fixture_output

    def run_phase(
        self,
        *,
        plan_folder: str,
        status: PhaseStatus,
        target: DispatchTarget,
        review_posture: str,
    ) -> ProviderRunResult:
        if self._fixture_output is not None:
            text = self._fixture_output.read_text(encoding="utf-8")
            return ProviderRunResult(
                final_output=text,
                turns=0,
                cost_usd=0.0,
                provider=self.name,
                mode="dry-run",
            )

        phase_value: int | str
        if target.kind == "wrap-up":
            phase_value = "done"
        else:
            phase_value = target.phase or status.phase or 0

        report = WorkflowReport(
            status="incomplete",
            phase=phase_value,
            reason=(
                "Dry-run dispatch: no live phase agent was started "
                f"(target={target.kind}, review={review_posture}). "
                "Set ANTHROPIC_API_KEY or CURSOR_API_KEY for live dispatch, "
                "or pass --fixture-output to exercise a fixture report."
            ),
        )
        text = format_workflow_report(report)
        return ProviderRunResult(
            final_output=text,
            turns=0,
            cost_usd=0.0,
            provider=self.name,
            mode="dry-run",
        )

    def poll(self, dispatch_id: str) -> ProviderRunResult | None:
        return None
