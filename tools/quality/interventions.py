#!/usr/bin/env python3
"""Extract human interventions from Claude Code transcripts with the context needed to classify them.
Each row: one human message, the assistant's preceding reply, and the plan artifacts (briefs, plans) in play.
Text is secret-scrubbed (hooklog.scrub) before it leaves this module. Usage: interventions.py <session.jsonl>... > rows.jsonl"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooklog"))
from hooklog import scrub  # noqa: E402

BRIEF = re.compile(r"docs/plans/([\w.-]+)/briefs/([\w./-]+?)\.md")
PLAN = re.compile(r"docs/plans/([\w.-]+?)(?:/|\.md|\b)")
SKIP = ("<command-name>", "<local-command", "<command-message>", "Caveat:", "[Request interrupted")
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
LIMIT_USER, LIMIT_ASSIST = 2500, 1500


def text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text") if isinstance(content, list) else ""


def session_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    last_assist, recent_refs, n_human = "", [], 0
    last_skill, skill_at = "", 0
    tools: dict[str, str] = {}  # tool_use id -> "Name: input summary"
    for line in path.read_text(errors="ignore").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain"):
            continue
        msg, content = d.get("message") or {}, (d.get("message") or {}).get("content")
        blob = json.dumps(content)[:6000] if content else ""
        for m in BRIEF.finditer(blob):
            recent_refs.append(f"docs/plans/{m.group(1)}/briefs/{m.group(2)}.md")
        if d.get("type") == "assistant":
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    if b.get("name") == "Skill":
                        last_skill, skill_at = str((b.get("input") or {}).get("skill")), n_human
                    tools[b.get("id", "")] = f"{b.get('name')}: {json.dumps(b.get('input'))[:400]}"
            t = text_of(content).strip()
            if t:
                last_assist = t
        elif d.get("type") == "user" and not d.get("isMeta") and (d.get("origin") or {}).get("kind", "human") == "human":
            if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        rt = text_of(b.get("content")) if not isinstance(b.get("content"), str) else b["content"]
                        if "doesn't want to proceed" in rt or "was rejected" in rt or "interrupted by user" in rt:
                            rows.append({"session": path.stem[:8], "n": 0, "kind": "tool_rejection", "ts": d.get("timestamp"), "branch": d.get("gitBranch"),
                                         "cwd": d.get("cwd"), "briefs_in_play": sorted(set(recent_refs[-12:]))[-4:],
                                         "assistant_before": scrub(last_assist[-LIMIT_ASSIST:], LIMIT_ASSIST),
                                         "rejected_tool": scrub(tools.get(b.get("tool_use_id", ""), "?"), 400), "human": scrub(rt, LIMIT_USER)})
                continue
            t = REMINDER.sub("", text_of(content)).strip()
            cm = re.search(r"<command-name>/?([\w:-]+)</command-name>", t)
            if cm and cm.group(1) not in ("compact", "context", "usage", "clear", "model", "plugin", "reload-plugins", "autocompact", "reload-skills", "radio"):
                last_skill, skill_at = cm.group(1), n_human
            if not t:
                continue
            if t.startswith("[Request interrupted"):
                rows.append({"session": path.stem[:8], "n": 0, "kind": "interrupt", "ts": d.get("timestamp"), "briefs_in_play": sorted(set(recent_refs[-12:]))[-4:],
                             "assistant_before": scrub(last_assist[-LIMIT_ASSIST:], LIMIT_ASSIST), "human": t[:200]})
                continue
            if t.startswith(SKIP):
                continue
            n_human += 1
            rows.append({"session": path.stem[:8], "n": n_human, "kind": "prompt", "last_skill": last_skill, "skill_age": n_human - skill_at, "ts": d.get("timestamp"), "branch": d.get("gitBranch"), "cwd": d.get("cwd"),
                         "briefs_in_play": sorted(set(recent_refs[-12:]))[-4:], "assistant_before": scrub(last_assist[-LIMIT_ASSIST:], LIMIT_ASSIST),
                         "human": scrub(t, LIMIT_USER)})
    return rows


if __name__ == "__main__":
    for p in sys.argv[1:]:
        for r in session_rows(Path(p)):
            print(json.dumps(r))
