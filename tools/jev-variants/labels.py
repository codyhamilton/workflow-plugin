"""Programmatic proxy labels for activity-phase signals, computed from the same event prefix the state saw.

These are zero-call detectors, not ground truth: they say what the tools did in the last K batches.
Use them to measure Jev-vs-detector agreement (auc), and to find where Jev adds something detectors cannot.
Usage: labels.py --root <registry> --corpus corpus.json --ledger ledger.jsonl [--k 5]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from events import load_events

DOC = re.compile(r"\.(md|mdx|rst|txt)$|(^|/)(docs?|README)", re.I)
TEST = re.compile(r"(^|/)(tests?|__tests__|spec)/|[._]test\.|test_|_test\.|\.spec\.", re.I)
TESTCMD = re.compile(r"\b(pytest|unittest|npm (run )?test|yarn test|jest|vitest|go test|cargo test|mvn test|rspec|make test)\b")
READ = {"Read", "Grep", "Glob", "LS", "ReadFile", "SemanticSearch", "WebFetch", "WebSearch"}
EDIT = {"Edit", "Write", "MultiEdit", "StrReplace", "NotebookEdit", "ApplyPatch"}
FAIL = re.compile(r"(error|failed|traceback|exception|no such file)", re.I)
TESTFAIL = re.compile(r"(\b[1-9]\d* (failed|failures?|errors?)\b|\bFAILED\b|Traceback|exit code [1-9]|\bFAIL\b)", re.I)


def _target(c: dict[str, Any]) -> str:
    i = c.get("input") or {}
    if not isinstance(i, dict):
        return str(i)[:200]
    return str(i.get("file_path") or i.get("path") or i.get("command") or i.get("pattern") or "")[:200]


def window_calls(events: list[dict[str, Any]], checkpoint: int, k: int) -> list[dict[str, Any]]:
    batches = [e for e in events if e["kind"] == "tool_batch" and e["turn"] <= checkpoint]
    return [c for b in batches[-k:] for c in b["calls"]]


def detectors(calls: list[dict[str, Any]]) -> dict[str, bool]:
    names = [c["name"] for c in calls]
    edits = [c for c in calls if c["name"] in EDIT]
    src_edits = [c for c in edits if not DOC.search(_target(c)) and not TEST.search(_target(c))]
    tgts = [(c["name"], _target(c)) for c in calls]
    rep = any(tgts.count(t) >= 3 for t in set(tgts))
    failing = sum(1 for c in calls if c.get("output") and FAIL.search(c["output"][:400]))
    tests = [c for c in calls[-3:] if c["name"] == "Bash" and TESTCMD.search(_target(c))]
    green = bool(tests) and not any(c.get("output") and TESTFAIL.search(c["output"]) for c in tests[-1:]) \
        and not any(x["name"] in EDIT for x in calls[calls.index(tests[-1]) + 1:]) if tests else False
    return {
        "writing-main-implementation": bool(src_edits),
        "docs-only-recordkeeping": bool(edits) and all(DOC.search(_target(c)) for c in edits),
        "investigating-before-editing": bool(calls) and not edits and all(n in READ or n == "Bash" for n in names),
        "stuck-repeating-failing-step": rep and (failing >= 1 or sum(1 for t in tgts if t[0] == "Bash") >= 3),
        "last-test-run-green": green,
        "last-test-run-any": bool(tests),
    }


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    allv = sorted([(v, 0) for v in neg] + [(v, 1) for v in pos])
    ranks: dict[float, float] = {}
    i = 0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        ranks[allv[i][0]] = (i + j + 1) / 2
        i = j
    rp = sum(ranks[v] for v in pos)
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--by", choices=["marker", "state"], default="marker")
    ap.add_argument("--min-pos", type=int, default=10)
    a = ap.parse_args()
    corpus = json.loads(Path(a.corpus).read_text())
    corpus = corpus.get("sessions", corpus)
    names = {}
    for f in Path(a.root, "signals").glob("*.json"):
        d = json.loads(f.read_text())
        names[d["id"]] = d["spec"]["name"]
    cache: dict[str, list] = {}
    dcache: dict[tuple, dict] = {}
    got: dict[tuple, list[tuple[float, bool]]] = defaultdict(list)
    for line in Path(a.ledger).read_text().splitlines():
        r = json.loads(line)
        if r.get("score") is None or r["session"] not in corpus:
            continue
        nm = names.get(r["signal"])
        s = corpus[r["session"]]
        ev = cache.setdefault(r["session"], load_events(s["harness"], s["path"]))
        key = (r["session"], r["checkpoint"])
        if key not in dcache:
            dcache[key] = detectors(window_calls(ev, r["checkpoint"], a.k))
        d = dcache[key]
        if nm in d:
            got[(nm, r[a.by], s["harness"])].append((r["score"], d[nm]))
    print(f"{'signal':34}{a.by:16}{'harness':8}{'n':>4}{'pos':>4}{'auc':>6}")
    for (nm, mk, h), v in sorted(got.items()):
        pos = [s for s, l in v if l]
        neg = [s for s, l in v if not l]
        if len(pos) < a.min_pos or len(neg) < a.min_pos:
            continue
        x = auc(pos, neg)
        print(f"{nm:34}{mk:16}{h:8}{len(v):>4}{len(pos):>4}{'  n/a' if x is None else f'{x:6.2f}'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


CORRECTION = re.compile(r"^\s*(no\b|nope|wrong|stop|don'?t|do not|that'?s (not|wrong)|not what|instead|revert|undo|actually|why did you|you (should|shouldn'?t|didn'?t|missed)|still (broken|fails|failing))|\b(not what i|that is wrong|that's wrong|doesn'?t work|isn'?t working|still not|you missed|why are you)\b", re.I)


def outcome(events: list[dict[str, Any]], checkpoint: int, horizon: int = 8) -> dict[str, bool | None]:
    """What the human did next (events AFTER the checkpoint; never shown to Jev).
    next_prompt_in_horizon: any user prompt within `horizon` turns; next_is_correction: that prompt reads as a correction."""
    nxt = next((e for e in events if e["kind"] == "user_prompt" and e["turn"] > checkpoint), None)
    if nxt is None or nxt["turn"] - checkpoint > horizon:
        return {"prompt_soon": False, "correction": None if nxt is None else False}
    return {"prompt_soon": True, "correction": bool(CORRECTION.search(nxt["text"][:300]))}
