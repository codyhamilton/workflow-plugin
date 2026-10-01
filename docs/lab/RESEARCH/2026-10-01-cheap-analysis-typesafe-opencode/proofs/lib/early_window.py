"""early_window_end and progressive grids (api_turn only)."""

from __future__ import annotations


def early_window_end(T: int) -> int:
    return min(120, T)


def label_60_grid(T: int) -> list[int]:
    """Progressive gold grid 60 + 15k inside the early window."""
    end = early_window_end(T)
    out: list[int] = []
    turn = 60
    while turn <= end:
        out.append(turn)
        turn += 15
    return out


def p0_75_grid(T: int) -> list[int]:
    """P0 schedule checkpoints(75, 15, T) — no turn 60."""
    if T < 75:
        return []
    end = early_window_end(T)
    out: list[int] = []
    turn = 75
    while turn <= end:
        out.append(turn)
        turn += 15
    return out
