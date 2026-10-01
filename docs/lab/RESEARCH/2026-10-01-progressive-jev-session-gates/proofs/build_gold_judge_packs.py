#!/usr/bin/env python3
"""Emit commit-safe hybrid_v0 judge packs from gitignored ubuntu-raw gold-bundles.

Reads (local only, gitignored):
  proofs/validated/ubuntu-raw/*-gold-bundles-*.jsonl
  proofs/validated/ubuntu-raw/*-dry-run-thrash-table-*.json
  proofs/validated/ubuntu-raw/*-dry-run-checkpoints-*.with-state.jsonl

Writes:
  proofs/validated/gold/packs/{worker}-judge-packs-{run}.jsonl
  proofs/validated/gold/packs/p0-judge-packs-{run}.jsonl

Redaction matches PR #36 / hybrid_v0 intent: strip home/workspace/mount/tmp-claude
paths and secrets; keep tool names, turn structure, short excerpts (N=8, 400 chars).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
VALIDATED = HERE / "validated"
RAW = VALIDATED / "ubuntu-raw"
OUT = VALIDATED / "gold" / "packs"

DEFAULT_RUN = "20261001-194107"
DEFAULT_WORKERS = ("92a48e004519", "bb6165018de0")
HYBRID_N = 8
HYBRID_EXCERPT = 400
BRIEF_CAP = 500

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}", re.I),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|token|password)\s*[:=]\s*\S+"),
)
_PATH_PREFIXES = (
    ("/home/codyh/workspace/open-pajero-maps/", "<REPO>/"),
    ("/home/codyh/workspace/open-pajero-maps", "<REPO>"),
    ("/home/codyh/workspace/workflow-plugin/", "<WF>/"),
    ("/home/codyh/workspace/workflow-plugin", "<WF>"),
    ("/home/codyh/workspace/", "<WORKSPACE>/"),
    ("/home/codyh/", "<HOME>/"),
    ("/home/codyh", "<HOME>"),
)
_TMP_CLAUDE_HOME = re.compile(
    r"/tmp/claude-[0-9]+/-home-codyh-workspace-open-pajero-maps", re.I
)
_TMP_CLAUDE_HOME2 = re.compile(
    r"/tmp/claude-[0-9]+/-home-codyh-workspace-[A-Za-z0-9._-]+", re.I
)
_TMP_CLAUDE_ANY = re.compile(r"/tmp/claude-[0-9]+/[A-Za-z0-9._/-]*", re.I)
_ABS_HOME = re.compile(r"/home/[A-Za-z0-9._/-]+")
_MEDIA_RE = re.compile(
    r"(?<![A-Za-z0-9_])(/media/[A-Za-z0-9._/-]+|/mnt/[A-Za-z0-9._/-]+|/run/media/[A-Za-z0-9._/-]+)"
)
_USERNAME = re.compile(r"(?i)codyh")


def redact_secrets(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def redact_paths(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    out = redact_secrets(text)
    out = _TMP_CLAUDE_HOME.sub("<TMP_REPO>", out)
    out = _TMP_CLAUDE_HOME2.sub("<TMP_WORKSPACE>", out)
    out = _TMP_CLAUDE_ANY.sub("<TMP_CLAUDE>/…", out)
    for src, dst in _PATH_PREFIXES:
        out = out.replace(src, dst)
    out = _MEDIA_RE.sub("<MOUNT>/…", out)
    out = _ABS_HOME.sub("<ABS_HOME>/…", out)
    out = _USERNAME.sub("<USER>", out)
    return out


def clip(text: str, limit: int) -> str:
    t = redact_paths(text or "")
    return t if len(t) <= limit else t[:limit]


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_paths(obj)
    if isinstance(obj, list):
        return [redact_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    return obj


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_worker(wid: str, run: str) -> list[dict[str, Any]]:
    gold_path = RAW / f"{wid}-gold-bundles-{run}.jsonl"
    thrash_path = RAW / f"{wid}-dry-run-thrash-table-{run}.json"
    ws_path = RAW / f"{wid}-dry-run-checkpoints-{run}.with-state.jsonl"
    if not gold_path.exists() or gold_path.stat().st_size == 0:
        raise FileNotFoundError(f"missing gold-bundles: {gold_path}")
    if not thrash_path.exists():
        raise FileNotFoundError(f"missing thrash table: {thrash_path}")

    gold_rows = load_jsonl(gold_path)
    thrash = {r["checkpoint_turn"]: r for r in json.loads(thrash_path.read_text())}
    with_state: dict[int, dict[str, Any]] = {}
    if ws_path.exists() and ws_path.stat().st_size > 0:
        for r in load_jsonl(ws_path):
            with_state[int(r["checkpoint_turn"])] = r.get("state") or {}

    pack_rows: list[dict[str, Any]] = []
    for gr in gold_rows:
        cp = int(gr["checkpoint_turn"])
        gb = gr["gold_bundle"]
        cum = redact_obj(copy.deepcopy(gb.get("cumulative") or {}))
        th = thrash.get(cp) or {}
        thrash_top = redact_obj(
            copy.deepcopy(th.get("reread_paths") or cum.get("reread_paths") or [])
        )
        raw_tail = gb.get("tail") or []
        tail8 = [
            {
                "turn": t.get("turn"),
                "excerpt": clip(str(t.get("excerpt") or ""), HYBRID_EXCERPT),
                "tool_names": list(t.get("tool_names") or [])[:32],
            }
            for t in raw_tail[-HYBRID_N:]
        ]
        ws = with_state.get(cp) or {}
        delta = redact_obj(copy.deepcopy(ws.get("delta_since_prior") or {}))
        prior = ws.get("prior_checkpoint_turn")
        if prior is None and cp > 75:
            prior = cp - 15
        pack = {
            "worker_id": wid,
            "checkpoint_turn": cp,
            "schedule": {"first_at": 75, "interval": 15},
            "snapshot_mode": "hybrid_v0",
            "snapshot_params": {"N": HYBRID_N, "excerpt": HYBRID_EXCERPT},
            "prior_checkpoint_turn": prior,
            "brief_anchor": clip(str(gb.get("brief_anchor") or "missing"), BRIEF_CAP),
            "api_turns_note": gb.get("api_turns_note") or f"api_turns = {cp}",
            "cumulative": cum,
            "delta_since_prior": delta,
            "thrash_top_rereads": thrash_top,
            "tail": tail8,
            "gold_bundle_status": gr.get("gold_bundle_status"),
            "shrink_steps": gr.get("shrink_steps") or [],
            "pack_meta": {
                "source_run": run,
                "sources": [
                    s
                    for s in [
                        f"{wid}-gold-bundles-{run}.jsonl (tail+brief+cumulative)",
                        f"{wid}-dry-run-thrash-table-{run}.json (top rereads)",
                        (
                            f"{wid}-dry-run-checkpoints-{run}.with-state.jsonl "
                            "(delta_since_prior)"
                            if ws
                            else None
                        ),
                    ]
                    if s
                ],
                "redaction": (
                    "hybrid_v0 N=8 excerpt=400; secrets; "
                    "home/workspace/mount/tmp-claude paths → tokens; username scrubbed"
                ),
                "note": (
                    "Safe judge pack for GOLD-LABEL-RUBRIC.md. Hybrid_v0 budget "
                    "(last 8×400), not full gold 30×700. Raw gold-bundles/with-state "
                    "stay gitignored under ubuntu-raw/."
                ),
            },
        }
        pack["pack_chars"] = len(json.dumps(pack, ensure_ascii=False))
        pack_rows.append(pack)
    return pack_rows


def assert_no_leaks(rows: list[dict[str, Any]], label: str) -> None:
    blob = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    needles = ("/home/", "codyh", "/media/", "/mnt/", "sk-ant")
    hits = [n for n in needles if n.lower() in blob.lower()]
    if hits:
        raise SystemExit(f"leak check failed for {label}: {hits}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default=DEFAULT_RUN)
    parser.add_argument("--workers", nargs="+", default=list(DEFAULT_WORKERS))
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    combined_rows: list[dict[str, Any]] = []
    for wid in args.workers:
        rows = build_worker(wid, args.run)
        assert_no_leaks(rows, wid)
        path = args.out / f"{wid}-judge-packs-{args.run}.jsonl"
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"wrote {path} rows={len(rows)}", file=sys.stderr)
        combined_rows.extend(rows)

    combined = args.out / f"p0-judge-packs-{args.run}.jsonl"
    with combined.open("w") as f:
        for row in combined_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {combined} rows={len(combined_rows)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
