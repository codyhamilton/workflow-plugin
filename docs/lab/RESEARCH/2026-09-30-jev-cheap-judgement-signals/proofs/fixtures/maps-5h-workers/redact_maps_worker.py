#!/usr/bin/env python3
"""Redact Claude Code subagent JSONL for commit-friendly Jev lab fixtures.

Preserves structure needed for API-turn counting and light Jev replay:
  - row type (user/assistant/system/attachment)
  - unique assistant message.id
  - message.usage (peak ctx)
  - tool_use name + id; tool_result tool_use_id + is_error
Strips/replaces free text, thinking, tool inputs/outputs, paths, and bulky fields.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


PLACEHOLDER = "[REDACTED]"


def _redact_str(s: str, keep_len: bool = True) -> str:
    if not isinstance(s, str):
        return PLACEHOLDER
    if keep_len and len(s) > 0:
        return f"{PLACEHOLDER}:{len(s)}"
    return PLACEHOLDER


def _redact_content_blocks(content: Any) -> Any:
    if isinstance(content, str):
        return _redact_str(content)
    if not isinstance(content, list):
        return PLACEHOLDER
    out = []
    for b in content:
        if not isinstance(b, dict):
            out.append({"type": "unknown", "note": PLACEHOLDER})
            continue
        t = b.get("type")
        if t == "text":
            out.append({"type": "text", "text": _redact_str(b.get("text", ""))})
        elif t == "thinking":
            # keep type marker only; drop signature + thinking body
            out.append({"type": "thinking", "thinking": PLACEHOLDER})
        elif t == "tool_use":
            name = b.get("name") if isinstance(b.get("name"), str) else "unknown"
            tid = b.get("id") if isinstance(b.get("id"), str) else None
            inp = b.get("input")
            # keep shallow input *keys* only (no values) for replay shape
            keys = sorted(inp.keys()) if isinstance(inp, dict) else []
            nb = {"type": "tool_use", "name": name, "input_keys": keys, "input": PLACEHOLDER}
            if tid:
                nb["id"] = tid
            out.append(nb)
        elif t == "tool_result":
            nb = {
                "type": "tool_result",
                "content": PLACEHOLDER,
            }
            if "tool_use_id" in b:
                nb["tool_use_id"] = b.get("tool_use_id")
            if "is_error" in b:
                nb["is_error"] = b.get("is_error")
            out.append(nb)
        elif t == "image":
            out.append({"type": "image", "note": PLACEHOLDER})
        else:
            # unknown block: keep type only
            out.append({"type": t or "unknown", "note": PLACEHOLDER})
    return out


def _redact_usage(usage: Any) -> Any:
    if not isinstance(usage, dict):
        return usage
    keep = (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "cache_creation",
        "service_tier",
    )
    return {k: usage[k] for k in keep if k in usage}


def _redact_message(msg: Any, row_type: str | None) -> Any:
    if not isinstance(msg, dict):
        return PLACEHOLDER
    out: dict[str, Any] = {}
    if "role" in msg:
        out["role"] = msg["role"]
    if "id" in msg:
        out["id"] = msg["id"]  # critical for unique assistant API-turn count
    if "model" in msg and isinstance(msg["model"], str):
        # model id is not secret; useful for fixtures
        out["model"] = msg["model"]
    if "stop_reason" in msg:
        out["stop_reason"] = msg["stop_reason"]
    if "usage" in msg:
        out["usage"] = _redact_usage(msg["usage"])
    if "content" in msg:
        out["content"] = _redact_content_blocks(msg["content"])
    # drop: container, diagnostics, context_management, input_transformations, etc.
    return out


ROW_KEEP = (
    "type",
    "uuid",
    "parentUuid",
    "timestamp",
    "isSidechain",
    "agentId",
    "sessionId",
    "requestId",
    "apiBlockIndex",
)


def redact_row(obj: dict[str, Any]) -> dict[str, Any] | None:
    t = obj.get("type")
    # Drop bulky attachment/system payloads; keep a stub so line density stays similar
    if t == "attachment":
        stub = {"type": "attachment", "uuid": obj.get("uuid"), "timestamp": obj.get("timestamp")}
        # preserve attachment type name if present without content
        for k in ("attachment", "name", "filename"):
            if k in obj and isinstance(obj[k], str) and len(obj[k]) < 80:
                stub[k] = obj[k]
            elif k in obj:
                stub[k] = PLACEHOLDER
        return stub
    if t == "system":
        return {
            "type": "system",
            "uuid": obj.get("uuid"),
            "timestamp": obj.get("timestamp"),
            "content": PLACEHOLDER,
        }

    out: dict[str, Any] = {}
    for k in ROW_KEEP:
        if k in obj:
            out[k] = obj[k]
    # Scrub cwd / gitBranch / slug (may leak private paths/repo names)
    if "cwd" in obj:
        out["cwd"] = PLACEHOLDER
    if "gitBranch" in obj:
        out["gitBranch"] = PLACEHOLDER
    if "slug" in obj:
        out["slug"] = PLACEHOLDER

    if "message" in obj:
        out["message"] = _redact_message(obj["message"], t)
    elif t in ("user", "assistant"):
        # unexpected; keep type only
        pass

    return out


def analyze(path: str) -> dict[str, Any]:
    ids: set[str] = set()
    peak = 0
    lines = 0
    with open(path) as fh:
        for line in fh:
            lines += 1
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}
            if o.get("type") == "assistant":
                mid = msg.get("id")
                if isinstance(mid, str):
                    ids.add(mid)
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else {}
            it = usage.get("input_tokens") or 0
            cr = usage.get("cache_read_input_tokens") or 0
            cc = usage.get("cache_creation_input_tokens") or 0
            if all(isinstance(x, int) for x in (it, cr, cc)):
                peak = max(peak, it + cr + cc)
    return {
        "api_turns": len(ids),
        "peak_ctx": peak,
        "source_lines": lines,
        "source_bytes": os.path.getsize(path),
    }


def redact_file(src: str, dst: str) -> dict[str, Any]:
    stats = analyze(src)
    out_lines = 0
    with open(src) as inf, open(dst, "w") as outf:
        for line in inf:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            red = redact_row(obj)
            if red is None:
                continue
            outf.write(json.dumps(red, separators=(",", ":"), ensure_ascii=False) + "\n")
            out_lines += 1
    stats["redacted_lines"] = out_lines
    stats["redacted_bytes"] = os.path.getsize(dst)
    # verify turn count preserved on redacted
    verify = analyze(dst)
    stats["redacted_api_turns"] = verify["api_turns"]
    stats["redacted_peak_ctx"] = verify["peak_ctx"]
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--short-id", required=True)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.dst)) or ".", exist_ok=True)
    stats = redact_file(args.src, args.dst)
    stats["short_id"] = args.short_id
    stats["source_path"] = os.path.abspath(args.src)
    stats["fixture_path"] = os.path.abspath(args.dst)
    print(json.dumps(stats))
    if stats["api_turns"] != stats["redacted_api_turns"]:
        print(
            f"WARN turn mismatch {stats['api_turns']} vs {stats['redacted_api_turns']}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
