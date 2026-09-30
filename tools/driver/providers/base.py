"""Provider interface for one fresh phase agent session."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from resolve import PhaseStatus


@dataclass(frozen=True)
class ProviderRunResult:
    """Outcome of a single provider dispatch (sync or final poll)."""

    final_output: str
    turns: int | None = None
    cost_usd: float | None = None
    provider: str = ""
    mode: str = "live"  # live | dry-run


class ProviderUnavailable(Exception):
    """No provider configured or implementation missing for this environment."""


@dataclass(frozen=True)
class DispatchTarget:
    kind: str  # phase | wrap-up
    phase: int | None = None

    def to_json_dict(self) -> dict:
        return {"kind": self.kind, "phase": self.phase}


class PhaseProvider(Protocol):
    name: str

    def run_phase(
        self,
        *,
        plan_folder: str,
        status: PhaseStatus,
        target: DispatchTarget,
        review_posture: str,
    ) -> ProviderRunResult:
        """Run one fresh phase agent session and return final output text."""

    def poll(self, dispatch_id: str) -> ProviderRunResult | None:
        """Return final result if async dispatch completed; None if still in flight."""
