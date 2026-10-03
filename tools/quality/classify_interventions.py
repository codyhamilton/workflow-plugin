#!/usr/bin/env python3
"""Classify intervention rows (interventions.py output) with Flash via opencode. Rows are already scrubbed.
Usage: classify_interventions.py rows.jsonl out.jsonl [limit] [workers]"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

NOISE = ("/compact", "This session is being continued", "<task-notification", "/clear")
TYPES = "correction|rejected_result|missing_requirement|scope_add|clarify_intent|ack_continue|new_task|question|relay|other"
CAUSES = "brief_gap|design_gap|unproven_assumption|arbitrary_threshold|agent_drift|environment|user_change_of_mind|none"
PROMPT = """You classify one human message sent to a coding agent mid-project. Reply with ONE JSON object only, no prose.
Keys: type (%s); rework (true if the message makes the agent redo, undo or fix prior work); cause (%s: what in the plan/spec or agent behaviour made this message necessary; none if it is just direction); plan_text_that_would_have_prevented (one sentence, or ""); quote (<=20 words copied from the human message supporting the call); confidence (0-1).
Be literal; use only the text below.

ASSISTANT SAID BEFORE:
%s

HUMAN MESSAGE:
%s
"""


def classify(row: dict) -> dict:
    p = PROMPT % (TYPES, CAUSES, row["assistant_before"][-1200:] or "(nothing)", (f"[{row.get('kind')}] " + (f"(user rejected tool call {row['rejected_tool']}) " if row.get("rejected_tool") else "") + row["human"][:2000]))
    try:
        out = subprocess.run(["opencode", "run", "--model", "deepseek/deepseek-flash", "--format", "default", p],
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240).stdout
        m = re.search(r"\{.*\}", out, re.S)
        return {**row, "flash": json.loads(m.group(0)) if m else None, "flash_raw": None if m else out[-300:]}
    except Exception as e:  # noqa: BLE001
        return {**row, "flash": None, "flash_raw": f"error: {e}"}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    rows = [r for r in map(json.loads, open(src)) if not r["human"].startswith(NOISE)][:limit]
    key = lambda r: (r["session"], r.get("kind"), r.get("ts"), r["human"][:60])  # noqa: E731
    done = {key(r) for r in map(json.loads, open(dst))} if Path(dst).exists() else set()  # resume: keep finished rows (retry parse failures)
    prior = [r for r in map(json.loads, open(dst)) if r.get("flash")] if done else []
    done = {key(r) for r in prior}
    rows = [r for r in rows if key(r) not in done]
    with ThreadPoolExecutor(workers) as ex, open(dst, "w") as f:
        for r in prior:
            f.write(json.dumps(r) + "\n")
        for r in ex.map(classify, rows):
            f.write(json.dumps(r) + "\n")
            f.flush()
