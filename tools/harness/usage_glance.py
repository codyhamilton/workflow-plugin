#!/usr/bin/env python3
"""Read-only Claude Code + Codex Plus usage glance → JSON on stdout.

Cody greenlight 2026-10-01 via Bot Team Manager: meters only.
No auto-prods, no threshold escalation, no network dashboards.

Claude: `claude /usage` (this machine's subscription windows).
Codex: newest ~/.codex/sessions/**/rollout-*.jsonl rate_limits blob
       (freshness = last Codex turn on this machine).

Exit 0 even when a source is missing (that key is null + error string).
Exit 2 only on unexpected script failure.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
from typing import Any

TZ_NAME = "Australia/Brisbane"
AEST = dt.timezone(dt.timedelta(hours=10))


def now_iso() -> str:
    return dt.datetime.now(AEST).isoformat(timespec="seconds")


def ts_iso(epoch: Any) -> str | None:
    if epoch is None:
        return None
    try:
        return dt.datetime.fromtimestamp(int(epoch), AEST).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError):
        return None


def run_claude_usage() -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": False,
        "session_used_pct": None,
        "session_resets_at": None,
        "week_used_pct": None,
        "week_resets_at": None,
        "raw_head": None,
        "error": None,
    }
    claude = os.environ.get("CLAUDE_BIN", "claude")
    try:
        proc = subprocess.run(
            [claude, "/usage"],
            input="",
            text=True,
            capture_output=True,
            timeout=60,
            env={**os.environ, "TERM": "dumb"},
        )
    except FileNotFoundError:
        out["error"] = f"claude binary not found ({claude})"
        return out
    except subprocess.TimeoutExpired:
        out["error"] = "claude /usage timed out"
        return out
    except Exception as e:  # noqa: BLE001 — surface as JSON
        out["error"] = f"{type(e).__name__}: {e}"
        return out

    text = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    out["raw_head"] = "\n".join(text.strip().splitlines()[:12]) or None

    # Current session: 54% used · resets Oct 2, 3:40am (Australia/Brisbane)
    m_sess = re.search(
        r"Current session:\s*(\d+(?:\.\d+)?)%\s*used\s*·\s*resets\s*(.+)",
        text,
    )
    m_week = re.search(
        r"Current week(?:\s*\([^)]*\))?:\s*(\d+(?:\.\d+)?)%\s*used\s*·\s*resets\s*(.+)",
        text,
    )
    if m_sess:
        out["session_used_pct"] = float(m_sess.group(1))
        out["session_resets_at"] = m_sess.group(2).strip()
    if m_week:
        out["week_used_pct"] = float(m_week.group(1))
        out["week_resets_at"] = m_week.group(2).strip()

    if out["session_used_pct"] is None and out["week_used_pct"] is None:
        out["error"] = (
            f"could not parse claude /usage (exit {proc.returncode})"
        )
        return out
    out["ok"] = True
    return out


def _walk_rate_limits(obj: Any):
    if isinstance(obj, dict):
        rl = obj.get("rate_limits")
        if (
            isinstance(rl, dict)
            and isinstance(rl.get("primary"), dict)
            and "used_percent" in rl["primary"]
        ):
            yield rl
        for v in obj.values():
            yield from _walk_rate_limits(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_rate_limits(v)


def run_codex_usage() -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": False,
        "plan_type": None,
        "window_5h_used_pct": None,
        "window_5h_resets_at": None,
        "weekly_used_pct": None,
        "weekly_resets_at": None,
        "source_rollout": None,
        "error": None,
    }
    home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    pattern = os.path.join(home, "sessions", "**", "rollout-*.jsonl")
    paths = sorted(glob.glob(pattern, recursive=True))
    if not paths:
        out["error"] = f"no rollout jsonl under {pattern}"
        return out

    best_rl = None
    best_path = None
    # Prefer newest files; read only the tail of each.
    for path in paths[-40:]:
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                n = f.tell()
                f.seek(max(0, n - 262144))
                data = f.read().decode("utf-8", "ignore")
        except OSError:
            continue
        for line in data.splitlines():
            if '"rate_limits"' not in line or "used_percent" not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            for rl in _walk_rate_limits(obj):
                best_rl, best_path = rl, path

    if not best_rl:
        out["error"] = "no rate_limits found in recent rollouts"
        out["source_rollout"] = paths[-1] if paths else None
        return out

    primary = best_rl.get("primary") or {}
    secondary = best_rl.get("secondary") or {}
    out["plan_type"] = best_rl.get("plan_type")
    out["window_5h_used_pct"] = primary.get("used_percent")
    out["window_5h_resets_at"] = ts_iso(primary.get("resets_at"))
    out["weekly_used_pct"] = secondary.get("used_percent")
    out["weekly_resets_at"] = ts_iso(secondary.get("resets_at"))
    out["source_rollout"] = best_path
    out["ok"] = True
    return out


def main() -> int:
    payload = {
        "ts": now_iso(),
        "tz": TZ_NAME,
        "host": os.uname().nodename if hasattr(os, "uname") else None,
        "claude": run_claude_usage(),
        "codex": run_codex_usage(),
        "notes": [
            "read-only glance; no auto-prods / thresholds",
            "claude percentages are this-machine subscription windows",
            "codex percentages are as-of last Codex turn on this machine",
        ],
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:  # noqa: BLE001
        json.dump(
            {"ts": now_iso(), "ok": False, "error": f"{type(e).__name__}: {e}"},
            sys.stdout,
        )
        sys.stdout.write("\n")
        raise SystemExit(2)
