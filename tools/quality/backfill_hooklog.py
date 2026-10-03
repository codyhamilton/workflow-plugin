#!/usr/bin/env python3
"""Load hooklog JSONL files into the quality ledger (idempotent: rows are keyed by content hash, so reruns and
spool drains are safe). Direct DB by default; --url posts to a running service instead.
Usage: backfill_hooklog.py [--dir DIR] [--url http://127.0.0.1:8765] [--batch 2000]"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hookevents as he  # noqa: E402
import hooklog  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(hooklog.store_dir()))
    ap.add_argument("--url")
    ap.add_argument("--exclude", action="append", default=[], help="session id prefix to skip (repeatable)")
    ap.add_argument("--batch", type=int, default=2000)
    a = ap.parse_args()
    tot = {"inserted": 0, "duplicate": 0, "rejected": 0, "torn": 0, "files": 0}

    def send(rows: list) -> None:
        if not rows:
            return
        if a.url:
            hdr = {"Content-Type": "application/json", **({"Authorization": f"Bearer {os.environ['WORKFLOW_QUALITY_TOKEN']}"} if os.environ.get("WORKFLOW_QUALITY_TOKEN") else {})}
            res = json.load(urllib.request.urlopen(urllib.request.Request(a.url.rstrip("/") + "/v1/hook-events", json.dumps({"rows": rows}).encode(), hdr), timeout=120))
        else:
            res = he.ingest(rows)
        for k, v in res.items():
            tot[k] += v

    for f in sorted(Path(a.dir).glob("*/*.jsonl")):
        if any(f.stem.startswith(x) for x in a.exclude):
            continue
        tot["files"] += 1
        buf: list = []
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                buf.append(json.loads(line))
            except json.JSONDecodeError:
                tot["torn"] += 1
                continue
            if len(buf) >= a.batch:
                send(buf); buf = []
        send(buf)
    print(json.dumps(tot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
