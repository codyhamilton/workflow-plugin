"""Build corpus.json (session -> harness/path/split) from locally discoverable Claude Code and Cursor sessions.

  build_corpus.py --root R [--min-bytes 30000] [--min-turns 15] [--exclude-path-substr scratchpad]

Split is a deterministic hash of the session id (60% discovery, 20% dev, 20% heldout) so it never shifts when
sessions are added. Sessions under this tool's own scratch/test directories are excluded. Existing entries keep
their split. Hook logs (tools/hooklog) are added with --hooklog-dir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "transcript"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


from events import load_events, total_turns  # noqa: E402


def split_of(session_id: str) -> str:
    b = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % 10
    return "discovery" if b < 6 else "dev" if b < 8 else "heldout"


def discover(min_bytes: int, min_turns: int, exclude: list[str]) -> dict[str, dict]:
    from lib.registry import REGISTRY
    import parsers  # noqa: F401  (registers parsers)
    out: dict[str, dict] = {}
    for name, harness in (("claude-code", "claude"), ("cursor", "cursor")):
        p = REGISTRY.get(name)
        for s in p.discover_all():
            if any(x in (s.project_path or "") for x in exclude):
                continue
            if name == "claude-code" and s.bytes < min_bytes:
                continue
            try:
                ref = p.resolve(s.session_id, s.project_path)
            except ValueError:
                continue  # ambiguous id (same session in two locations): skip rather than guess
            path = Path(ref.storage_path)
            if not path.exists():
                continue
            if path.is_dir():  # session dir: the parent jsonl lives inside
                cands = sorted(path.glob(f"{s.session_id}*.jsonl")) or sorted(path.glob("*.jsonl"))
                if not cands:
                    continue
                path = cands[0]
            if path.is_dir() or not path.exists():
                continue
            turns = total_turns(load_events(harness, path))
            if turns < min_turns:
                continue
            out[s.session_id] = {"harness": harness, "path": str(path), "split": split_of(s.session_id),
                                 "project_path": s.project_path, "start": s.start_time_iso, "bytes": s.bytes,
                                 "turns": turns}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--min-bytes", type=int, default=30000)
    ap.add_argument("--min-turns", type=int, default=15)
    ap.add_argument("--exclude-path-substr", nargs="*", default=["scratchpad", "/tmp/"])
    ap.add_argument("--hooklog-dir")
    a = ap.parse_args(argv)
    f = Path(a.root) / "corpus.json"
    corpus = json.loads(f.read_text()) if f.exists() else {}
    for sid, info in discover(a.min_bytes, a.min_turns, a.exclude_path_substr).items():
        info["split"] = corpus.get(sid, {}).get("split", info["split"])
        corpus[sid] = info
    if a.hooklog_dir:
        for p in Path(a.hooklog_dir).glob("*/*.jsonl"):
            corpus.setdefault(p.stem, {"harness": "hooklog", "path": str(p), "split": split_of(p.stem)})
    f.write_text(json.dumps(corpus, indent=1, sort_keys=True))
    by: dict[str, int] = {}
    for v in corpus.values():
        by[f"{v['harness']}/{v['split']}"] = by.get(f"{v['harness']}/{v['split']}", 0) + 1
    print(json.dumps(by, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
