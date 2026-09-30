"""Cursor headless agent provider (live dispatch — Phase 3 driver plan)."""

from __future__ import annotations

import os

from base import DispatchTarget, ProviderRunResult, ProviderUnavailable
from resolve import PhaseStatus


class CursorProvider:
    name = "cursor"

    def run_phase(
        self,
        *,
        plan_folder: str,
        status: PhaseStatus,
        target: DispatchTarget,
        review_posture: str,
    ) -> ProviderRunResult:
        if not os.environ.get("CURSOR_API_KEY"):
            raise ProviderUnavailable(
                "CURSOR_API_KEY is not set; use --dry-run or choose another provider"
            )
        raise ProviderUnavailable(
            "Cursor live dispatch is not implemented yet (see docs/plans/06-phase-driver "
            "Phase 3). Use --dry-run to prove the trigger contract in this environment."
        )

    def poll(self, dispatch_id: str) -> ProviderRunResult | None:
        return None
