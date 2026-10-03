#!/usr/bin/env python3
"""Classify executor_reports.py rows with Flash: is the executor reporting a defect in the plan/brief it was given?
Usage: classify_executor_reports.py rows.jsonl out.jsonl [workers]"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

KINDS = "plan_defect|unproven_assumption|arbitrary_threshold|ambiguity|stale_reference|self_inflicted|not_about_plan"
PROMPT = """A subagent was given a TASK and later wrote the MESSAGE. Decide if the message reports a problem that comes from the TASK text (the brief/plan) rather than from the agent's own work or the environment.
Reply with ONE JSON object only. Keys: kind (%s); plan_defect (true only if the TASK text itself is wrong, ambiguous, stale, contradictory, or sets an unmeasurable/unjustified criterion); what_task_said (<=25 words quoted from TASK, or ""); what_was_wrong (one sentence); missing_in_task (one sentence naming what the task should have contained, or ""); quote (<=20 words copied from MESSAGE); confidence (0-1).
Be literal; use only the text below.

TASK:
%s

MESSAGE:
%s
"""


def classify(r):
    p = PROMPT % (KINDS, r["task"][:2500], r["text"][:2000])
    try:
        out = subprocess.run(["opencode", "run", "--model", "deepseek/deepseek-flash", "--format", "default", p],
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240).stdout
        m = re.search(r"\{.*\}", out, re.S)
        return {**r, "flash": json.loads(m.group(0)) if m else None}
    except Exception as e:  # noqa: BLE001
        return {**r, "flash": None, "err": str(e)}


if __name__ == "__main__":
    rows = list(map(json.loads, open(sys.argv[1])))
    with ThreadPoolExecutor(int(sys.argv[3]) if len(sys.argv) > 3 else 6) as ex, open(sys.argv[2], "w") as f:
        for r in ex.map(classify, rows):
            f.write(json.dumps(r) + "\n")
            f.flush()
