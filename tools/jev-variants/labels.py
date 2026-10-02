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


def _target(c: dict[str, Any]) -> str:
    i = c.get("input") or {}
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
    return {
        "writing-main-implementation": bool(src_edits),
        "docs-only-recordkeeping": bool(edits) and all(DOC.search(_target(c)) for c in edits),
        "investigating-before-editing": bool(calls) and not edits and all(n in READ or n == "Bash" for n in names),
        "stuck-repeating-failing-step": rep and failing >= 2,
        "last-test-run-green": any(c["name"] == "Bash" and TESTCMD.search(_target(c)) for c in calls[-3:]),
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
