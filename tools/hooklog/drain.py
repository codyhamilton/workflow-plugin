#!/usr/bin/env python3
"""Drain the hook spool: normalise + scrub each raw payload, append it to the per-session JSONL archive, and post batches
to the quality service. Runs outside the agent's hot path (systemd timer, or kicked in the background by session-end hooks).

A spool file is deleted only after its batch was accepted (or, with no service configured, archived), so a down service just
means the spool grows and the next pass retries. Re-delivery is harmless: the service keys rows by content hash and `ts` is
the time the hook fired, not the drain time. Files that cannot be parsed, or that the service refuses outright, move to
spool/bad/ for inspection.

  drain.py [--once | --watch [--interval S]] [--batch N] [--status]
Env: WORKFLOW_QUALITY_URL (default http://127.0.0.1:8765; empty = local archive only; an explicit WORKFLOW_HOOKLOG_DIR
without a URL also means local only), WORKFLOW_QUALITY_TOKEN, WORKFLOW_QUALITY_TIMEOUT (default 30 s per batch),
WORKFLOW_HOOKLOG_ARCHIVE=0 to skip the JSONL archive when the service has the rows.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hooklog  # noqa: E402

STALE_TMP_S = 3600


def service_url() -> str | None:
    default = None if os.environ.get("WORKFLOW_HOOKLOG_DIR") else "http://127.0.0.1:8765"
    return os.environ.get("WORKFLOW_QUALITY_URL", default) or None


def to_row(path: Path) -> dict[str, Any] | None:
    """Spool file -> normalised row (None when the payload names no event). Raises on a malformed file."""
    head, _, body = path.read_text(encoding="utf-8", errors="replace").partition("\n")
    env = json.loads(head)
    payload = json.loads(body or "{}")
    if not isinstance(payload, dict):
        raise ValueError("hook payload must be an object")
    if env.get("event"):
        payload["hook_event_name"] = env["event"]  # the registration's name wins, as it always did
    harness = env.get("harness") or "auto"
    if harness == "auto":
        harness = hooklog.detect_harness(payload)
    return hooklog.normalize(harness, payload, ts=float(env["ts"]))


def post(base: str, rows: list[dict[str, Any]]) -> str:
    """'ok' | 'retry' (service down, auth, throttled, 5xx) | 'refused' (the service will never take this batch)."""
    hdr = {"Content-Type": "application/json"}
    if os.environ.get("WORKFLOW_QUALITY_TOKEN"):
        hdr["Authorization"] = f"Bearer {os.environ['WORKFLOW_QUALITY_TOKEN']}"
    req = urllib.request.Request(base.rstrip("/") + "/v1/hook-events", json.dumps({"rows": rows}, default=str).encode(), hdr)
    try:
        return "ok" if urllib.request.urlopen(req, timeout=float(os.environ.get("WORKFLOW_QUALITY_TIMEOUT", "30"))).status < 300 else "retry"
    except urllib.error.HTTPError as e:
        return "retry" if e.code >= 500 or e.code in (401, 403, 408, 429) else "refused"
    except Exception:
        return "retry"


def quarantine(sd: Path, *paths: Path) -> None:
    (sd / "bad").mkdir(exist_ok=True)
    for p in paths:
        try:
            p.rename(sd / "bad" / p.name)
        except OSError:
            pass


def drain_once(sd: Path, base: str | None, batch: int = 500) -> dict[str, int]:
    st = {"sent": 0, "archived": 0, "dropped": 0, "bad": 0, "pending": 0}
    files = sorted(sd.glob("*.evt"))
    archive = os.environ.get("WORKFLOW_HOOKLOG_ARCHIVE", "1") not in ("0", "off", "false")
    for i in range(0, len(files), batch):
        rows, paths = [], []
        for p in files[i:i + batch]:
            try:
                row = to_row(p)
            except Exception:
                quarantine(sd, p)
                st["bad"] += 1
                continue
            if row is None:
                p.unlink(missing_ok=True)
                st["dropped"] += 1
                continue
            rows.append(row)
            paths.append(p)
        if not rows:
            continue
        if base:
            res = post(base, rows)
            if res == "retry":
                st["pending"] = len(files) - i - st["bad"] - st["dropped"]
                return st
            if res == "refused":
                quarantine(sd, *paths)
                st["bad"] += len(paths)
                continue
            st["sent"] += len(rows)
        if archive or not base:
            for r in rows:
                hooklog.append(r)
            st["archived"] += len(rows)
        for p in paths:
            p.unlink(missing_ok=True)
    return st


def sweep_tmp(sd: Path) -> None:
    """Remove half-written files left by a hook that was killed between create and rename."""
    for p in (sd / "tmp").glob("*"):
        try:
            if time.time() - p.stat().st_mtime > STALE_TMP_S:
                p.unlink()
        except OSError:
            pass


def status(sd: Path) -> dict[str, int]:
    return {"pending": len(list(sd.glob("*.evt"))), "bad": len(list((sd / "bad").glob("*"))) if (sd / "bad").is_dir() else 0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--watch", action="store_true", help="loop forever instead of one pass")
    ap.add_argument("--once", action="store_true", help="one pass (default)")
    ap.add_argument("--interval", type=float, default=10.0, help="seconds between passes with --watch")
    ap.add_argument("--batch", type=int, default=500)
    ap.add_argument("--status", action="store_true", help="print pending/bad counts and exit")
    a = ap.parse_args()
    sd = hooklog.spool_dir()
    if a.status:
        print(json.dumps(status(sd)))
        return 0
    (sd / "tmp").mkdir(parents=True, exist_ok=True)
    lock = open(sd / ".drain.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0  # another drain is running
    delay = a.interval
    while True:
        sweep_tmp(sd)
        st = drain_once(sd, service_url(), a.batch)
        if not a.watch:
            print(json.dumps(st))
            return 0
        delay = min(delay * 2, 300.0) if st["pending"] else a.interval  # back off while the service is unreachable
        time.sleep(delay)


if __name__ == "__main__":
    sys.exit(main())
