"""Build a prefix-only Jev state from an event stream and a validated state spec.

Anything with event turn > checkpoint is never read. Output is a dict with a rendered `text`
(what Jev sees), `tokens_est`, and `truncated` (whether the max_tokens cap dropped content).
Pure function; no I/O.
"""

from __future__ import annotations

import json
from typing import Any

from jev_variants import spec_hash

TOKEN_CHARS = 4
_PATH_KEYS = ("file_path", "path", "notebook_path", "filePath")


def _est(text: str) -> int:
    return max(1, len(text) // TOKEN_CHARS)


def _clip(text: str, n: int) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def _target(call: dict[str, Any]) -> str | None:
    inp = call.get("input") or {}
    for k in _PATH_KEYS:
        if isinstance(inp.get(k), str):
            return inp[k]
    cmd = inp.get("command")
    return _clip(cmd, 80) if isinstance(cmd, str) else None


def _render_call(call: dict[str, Any], spec: dict[str, Any]) -> str:
    lim = spec.get("truncate_chars", 300)
    s = call["name"]
    mode = spec.get("tool_inputs", "none")
    if mode in ("truncated", "full"):
        inp = json.dumps(call.get("input") or {}, ensure_ascii=False)
        s += " " + (inp if mode == "full" else _clip(inp, lim))
    out_mode = spec.get("tool_outputs", "none")
    if out_mode != "none" and call.get("output") is not None:
        out = call["output"]
        s += "\n  -> " + (out if out_mode == "full" else _clip(out, lim))
    return s


def build_state(spec: dict[str, Any], events: list[dict[str, Any]], checkpoint: int) -> dict[str, Any]:
    prefix = [e for e in events if e["turn"] <= checkpoint]
    w = spec["window"]
    batches = [e for e in prefix if e["kind"] == "tool_batch"]
    if w["unit"] == "batches":
        keep = batches[-w["n"]:]
    elif w["unit"] == "turns":
        keep = [b for b in batches if b["turn"] > checkpoint - w["n"]]
    else:
        keep = batches
    prompts = [e for e in prefix if e["kind"] == "user_prompt"]
    pmode = spec.get("user_prompts", "none")
    if pmode == "first":
        prompts = prompts[:1]
    elif pmode == "last_k":
        prompts = prompts[-spec["user_prompts_k"]:]
    elif pmode == "none":
        prompts = []

    all_calls = [c for b in batches for c in b["calls"]]
    targets = [t for t in map(_target, all_calls) if t]
    counters = {}
    for c in spec.get("counters", []):
        counters[c] = {
            "turn_index": checkpoint,
            "tool_calls": len(all_calls),
            "distinct_files": len(set(targets)),
            "repeat_targets": len(targets) - len(set(targets)),
            "prompt_count": len([e for e in prefix if e["kind"] == "user_prompt"]),
            "tokens_est": sum(_est(json.dumps(e, ensure_ascii=False)) for e in prefix),
        }[c]

    parts: list[str] = []
    if counters:
        parts.append("COUNTERS " + json.dumps(counters))
    prompt_lines = [f"[turn {p['turn']}] {_clip(p['text'], spec.get('truncate_chars', 600) * 2)}" for p in prompts]
    if prompt_lines:
        parts.append("USER PROMPTS\n" + "\n".join(prompt_lines))
    batch_lines = [f"[turn {b['turn']}] " + " | ".join(_render_call(c, spec) for c in b["calls"]) for b in keep]
    truncated = False
    # Enforce the hard cap by dropping the oldest batches first.
    while batch_lines and _est("\n".join(parts + ["RECENT TOOL BATCHES\n" + "\n".join(batch_lines)])) > spec["max_tokens"]:
        batch_lines.pop(0)
        truncated = True
    if batch_lines:
        parts.append("RECENT TOOL BATCHES\n" + "\n".join(batch_lines))
    text = "\n\n".join(parts)
    if _est(text) > spec["max_tokens"]:  # prompts alone exceed the cap
        text = text[: spec["max_tokens"] * TOKEN_CHARS]
        truncated = True
    return {"text": text, "tokens_est": _est(text), "truncated": truncated,
            "state_hash": spec_hash({"spec": spec, "checkpoint": checkpoint, "n_events": len(prefix)})}
