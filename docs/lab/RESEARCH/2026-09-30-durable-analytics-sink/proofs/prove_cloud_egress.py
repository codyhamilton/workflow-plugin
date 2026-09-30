#!/usr/bin/env python3
"""Record HTTPS POST egress from this host (Cursor cloud or local). Writes validated JSON."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

from dual_write_sink import build_envelope, detect_host

OUT = Path(__file__).resolve().parent / "validated" / "egress_cloud_result.json"
TARGET = os.environ.get("WORKFLOW_ANALYTICS_EGRESS_PROBE_URL", "https://httpbin.org/post")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    envelope = build_envelope(
        kind="harness.egress_probe",
        payload={"probe": "workflow-analytics-sink", "note": "lab proof only"},
        source="prove_cloud_egress.py",
        session_id=os.environ.get("WORKFLOW_ANALYTICS_SESSION_ID"),
    )
    body = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        TARGET,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "workflow-plugin-egress-probe/1"},
        method="POST",
    )
    result: dict[str, object] = {
        "recorded_at": _utc_now(),
        "target": TARGET,
        "host": dict(zip(("host_kind", "host_detail"), detect_host())),
        "envelope_kind": envelope["kind"],
        "ok": False,
    }
    try:
        with request.urlopen(req, timeout=15.0) as resp:
            result["http_status"] = resp.getcode()
            raw = resp.read().decode("utf-8", errors="replace")
            result["ok"] = 200 <= resp.getcode() < 300
            if len(raw) < 4000:
                result["response_preview"] = raw
            else:
                result["response_preview"] = raw[:2000] + "…"
    except error.HTTPError as e:
        result["http_status"] = e.code
        result["error"] = f"HTTPError:{e.code}"
    except error.URLError as e:
        result["error"] = f"URLError:{e.reason}"
    except TimeoutError:
        result["error"] = "timeout"
    except OSError as e:
        result["error"] = f"OSError:{e}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
