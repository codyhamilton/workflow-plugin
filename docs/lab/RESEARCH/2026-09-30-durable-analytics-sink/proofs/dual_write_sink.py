"""Lab-only dual-write helper: local JSONL + optional HTTP POST (exit 0 on remote failure).

Not imported by tools/driver on master. See ../DUAL-WRITE-RECIPE.md.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

SCHEMA_VERSION = 1
DEFAULT_TIMEOUT_SEC = 10.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_host() -> tuple[str, str | None]:
    override = os.environ.get("WORKFLOW_ANALYTICS_HOST_KIND")
    if override:
        return override, os.environ.get("WORKFLOW_ANALYTICS_HOST_DETAIL")
    mode = os.environ.get("WORKFLOW_INSTALL_MODE", "")
    if mode == "opencode":
        return "opencode", "opencode"
    if os.environ.get("CURSOR_AGENT") == "1":
        return "cloud", "cursor-cloud"
    if os.environ.get("CLAUDE_CODE_REMOTE", "").lower() == "true":
        return "cloud", "claude-code-remote"
    if os.environ.get("CLAUDECODE"):
        return "local", "claude-code"
    return "local", os.environ.get("WORKFLOW_ANALYTICS_HOST_DETAIL") or "desktop"


def build_envelope(
    *,
    kind: str,
    payload: dict[str, Any],
    plan: str | None = None,
    slug: str | None = None,
    phase: int | str | None = None,
    source: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    host_kind, host_detail = detect_host()
    sid = session_id or os.environ.get("WORKFLOW_ANALYTICS_SESSION_ID")
    repo = os.environ.get("WORKFLOW_ANALYTICS_REPO")
    env: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "ts": _utc_now(),
        "host_kind": host_kind,
        "kind": kind,
        "payload": payload,
    }
    if host_detail:
        env["host_detail"] = host_detail
    if sid:
        env["session_id"] = sid
    if repo:
        env["repo"] = repo
    if plan:
        env["plan"] = plan.rstrip("/")
    if slug:
        env["slug"] = slug
    if phase is not None:
        env["phase"] = phase
    if source:
        env["source"] = source
    return env


def _append_local(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def post_remote(envelope: dict[str, Any], *, url: str | None = None, token: str | None = None) -> tuple[bool, str]:
    """POST envelope; return (ok, detail). Never raises."""
    endpoint = url or os.environ.get("WORKFLOW_ANALYTICS_URL")
    if not endpoint:
        return True, "skipped:no_url"
    body = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "workflow-plugin-analytics-lab/1"}
    tok = token if token is not None else os.environ.get("WORKFLOW_ANALYTICS_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=DEFAULT_TIMEOUT_SEC) as resp:
            code = resp.getcode()
            if 200 <= code < 300:
                return True, f"http:{code}"
            return False, f"http:{code}"
    except error.HTTPError as e:
        return False, f"http_error:{e.code}"
    except error.URLError as e:
        return False, f"url_error:{e.reason}"
    except TimeoutError:
        return False, "timeout"
    except OSError as e:
        return False, f"os_error:{e}"


def emit_event(
    *,
    kind: str,
    payload: dict[str, Any],
    local_path: Path | None = None,
    legacy_row: dict[str, Any] | None = None,
    plan: str | None = None,
    slug: str | None = None,
    phase: int | str | None = None,
    source: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Dual-write: local legacy row (if any) + optional remote envelope. Always returns envelope."""
    if local_path is not None and legacy_row is not None:
        _append_local(local_path, legacy_row)
    envelope = build_envelope(
        kind=kind,
        payload=payload,
        plan=plan,
        slug=slug,
        phase=phase,
        source=source,
        session_id=session_id,
    )
    ok, detail = post_remote(envelope)
    envelope["_remote_ok"] = ok
    envelope["_remote_detail"] = detail
    return envelope


def emit_from_jev_signal_row(row: dict[str, Any], *, local_path: Path | None = None) -> dict[str, Any]:
    kind = row.get("kind", "jev.unknown")
    namespaced = f"jev.{kind}" if not str(kind).startswith("jev.") else str(kind)
    payload = {k: v for k, v in row.items() if k not in ("ts", "kind")}
    return emit_event(
        kind=namespaced,
        payload=payload,
        local_path=local_path,
        legacy_row=row if local_path else None,
        session_id=row.get("session_id"),
        source="jev-signal-log",
    )
