#!/usr/bin/env python3
"""Flash pass over thresholds.py rows: is it an acceptance/success threshold, and what provenance does the brief give it?
Usage: classify_thresholds.py rows.jsonl out.jsonl [workers]"""
import json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

PROMPT = """Below is a LINE from a software plan brief and its CONTEXT. Reply with ONE JSON object only.
Keys:
 is_acceptance (true only if the number is a pass/fail or success criterion for the work, NOT a resource budget, parallelism, formatting or reporting limit);
 provenance_class (what the context itself says about where the number came from: measured|derived|external|judgement|none);
 evidence_pointer (<=20 words copied from CONTEXT that gives the evidence, or "");
 justifies (0 none, 1 vague, 2 plausible, 3 specific and checkable: does the stated provenance explain why THIS number);
 quote (<=15 words of the number and what it limits);
 confidence (0-1).
Use only the text below; do not guess provenance that is not written.

LINE: %s

CONTEXT:
%s
"""


def run(r):
    try:
        out = subprocess.run(["opencode", "run", "--model", "deepseek/deepseek-flash", "--format", "default", PROMPT % (r["line"], r["context"])],
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240).stdout
        m = re.search(r"\{.*\}", out, re.S)
        return {**r, "flash": json.loads(m.group(0)) if m else None}
    except Exception as e:  # noqa: BLE001
        return {**r, "flash": None, "err": str(e)}


if __name__ == "__main__":
    rows = list(map(json.loads, open(sys.argv[1])))
    with ThreadPoolExecutor(int(sys.argv[3]) if len(sys.argv) > 3 else 8) as ex, open(sys.argv[2], "w") as f:
        for r in ex.map(run, rows):
            f.write(json.dumps(r) + "\n"); f.flush()
