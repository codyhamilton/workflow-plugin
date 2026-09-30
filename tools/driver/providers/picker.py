"""Select phase provider from flags and environment keys."""

from __future__ import annotations

import os
from pathlib import Path

from base import PhaseProvider, ProviderUnavailable
from claude import ClaudeProvider
from cursor import CursorProvider
from dry_run import DryRunProvider


def _keys_present() -> tuple[bool, bool]:
    anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    cursor = bool(os.environ.get("CURSOR_API_KEY"))
    return anthropic, cursor


def select_provider(
    *,
    provider: str | None,
    dry_run: bool,
    fixture_output: Path | None = None,
) -> PhaseProvider:
    if dry_run or fixture_output is not None:
        return DryRunProvider(fixture_output=fixture_output)

    anthropic, cursor = _keys_present()
    if provider is None:
        if anthropic and cursor:
            raise ProviderUnavailable(
                "Both ANTHROPIC_API_KEY and CURSOR_API_KEY are set; pass --provider claude|cursor"
            )
        if anthropic:
            provider = "claude"
        elif cursor:
            provider = "cursor"
        else:
            return DryRunProvider()

    if provider == "claude":
        return ClaudeProvider()
    if provider == "cursor":
        return CursorProvider()
    if provider == "dry-run":
        return DryRunProvider(fixture_output=fixture_output)
    raise ProviderUnavailable(f"Unknown provider: {provider!r}")
