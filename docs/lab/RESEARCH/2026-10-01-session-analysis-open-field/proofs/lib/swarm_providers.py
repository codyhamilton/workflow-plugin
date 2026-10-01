"""Pilot segment-swarm completion backends (Flash / Luna / local legacy)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from typing import Any

LOCAL_PROMPT = (
    "Return JSON only: {\"phase_tag\": <string>, \"theme_guess\": one of "
    "thrash_bundle|poll_monitor|productive|unknown}."
)

PILOT_SWARM_PROVIDER_DEFAULT = "luna"
PILOT_SWARM_PROVIDERS = ("luna", "flash", "local")

FLASH_MODEL_DEFAULT = "deepseek/deepseek-flash"
LUNA_MODEL_DEFAULT = "gpt-6-luna"


def _user_payload(cell: dict[str, Any]) -> str:
    return json.dumps(
        {"segment_id": cell["segment_id"], "worker_id": cell["worker_id"]},
        ensure_ascii=False,
    )


def _parse_theme_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]*\"theme_guess\"[^{}]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _local_chat_url() -> str:
    base = os.environ.get("WORKFLOW_LOCAL_LLM_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    return f"{base}/chat/completions"


def complete_local(cell: dict[str, Any]) -> dict[str, Any]:
    url = _local_chat_url()
    body = json.dumps(
        {
            "model": os.environ.get("WORKFLOW_LOCAL_LLM_MODEL", "local"),
            "messages": [
                {"role": "system", "content": LOCAL_PROMPT},
                {"role": "user", "content": _user_payload(cell)},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return {
            "decision": "live_local",
            "provider": "local",
            "response": payload,
            "parsed": _parse_theme_json(
                payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            ),
            "error": None,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, IndexError, KeyError) as exc:
        return {"decision": "missing", "provider": "local", "response": None, "parsed": None, "error": str(exc)}


def _subprocess_text(cmd: list[str], timeout: int = 120) -> tuple[str, str | None]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", str(exc)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        return proc.stdout or "", err
    return proc.stdout or "", None


def complete_flash(cell: dict[str, Any]) -> dict[str, Any]:
    """DeepSeek Flash via OpenCode CLI (no secrets in repo)."""
    bin_path = os.environ.get("WORKFLOW_OPENCODE_BIN", "opencode")
    model = os.environ.get("WORKFLOW_FLASH_MODEL", FLASH_MODEL_DEFAULT)
    prompt = f"{LOCAL_PROMPT}\n\n{_user_payload(cell)}"
    timeout = int(os.environ.get("WORKFLOW_FLASH_TIMEOUT_SEC", "120"))
    stdout, err = _subprocess_text([bin_path, "run", "--model", model, "--", prompt], timeout=timeout)
    parsed = _parse_theme_json(stdout)
    if err or parsed is None:
        return {
            "decision": "missing",
            "provider": "flash",
            "model": model,
            "response": {"stdout": stdout[:4000]} if stdout else None,
            "parsed": parsed,
            "error": err or "flash_parse_failed",
        }
    return {
        "decision": "live_flash",
        "provider": "flash",
        "model": model,
        "response": {"stdout": stdout[:4000], "parsed": parsed},
        "parsed": parsed,
        "error": None,
    }


def complete_luna(cell: dict[str, Any]) -> dict[str, Any]:
    """Codex Luna pin for focused-volume segment labels."""
    bin_path = os.environ.get("WORKFLOW_CODEX_BIN", "codex")
    model = os.environ.get("WORKFLOW_LUNA_MODEL", LUNA_MODEL_DEFAULT)
    prompt = f"{LOCAL_PROMPT}\n\n{_user_payload(cell)}"
    stdout, err = _subprocess_text(
        [bin_path, "exec", "-m", model, "--", prompt],
        timeout=180,
    )
    parsed = _parse_theme_json(stdout)
    if err or parsed is None:
        return {
            "decision": "missing",
            "provider": "luna",
            "model": model,
            "response": {"stdout": stdout[:4000]} if stdout else None,
            "parsed": parsed,
            "error": err or "luna_parse_failed",
        }
    return {
        "decision": "live_luna",
        "provider": "luna",
        "model": model,
        "response": {"stdout": stdout[:4000], "parsed": parsed},
        "parsed": parsed,
        "error": None,
    }


def complete_cell(provider: str, cell: dict[str, Any], *, live: bool) -> dict[str, Any]:
    if not live:
        return {"decision": "dry_stub", "provider": provider, "response": None, "parsed": None, "error": None}
    if provider == "local":
        return complete_local(cell)
    if provider == "flash":
        return complete_flash(cell)
    if provider == "luna":
        return complete_luna(cell)
    raise ValueError(f"unknown swarm provider: {provider}")
