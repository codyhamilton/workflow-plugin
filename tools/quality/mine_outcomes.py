#!/usr/bin/env python3
"""Mine proxy outcome labels for logged briefs from git history of the consuming repos.
Labels are noisy proxies, not truth: brief edited after landing, remediation sibling, fix-like churn on owned paths.
Usage: mine_outcomes.py <workspace-root> > outcomes.jsonl"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

FIX = re.compile(r"\b(fix|revert|regress|hotfix|remediat|repair|broken|bug)\w*", re.I)
DONE = re.compile(r"\b(complet|landed|record|done|close)\w*", re.I)


def git(repo: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True).stdout


def project(repo: Path) -> str:
    u = git(repo, "config", "--get", "remote.origin.url").strip()
    return re.sub(r"\.git$", "", u.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]) if u else repo.name


def owned(text: str) -> list[str]:
    m = re.search(r"^Owned paths:(.*?)(?:\n\n|\n[A-Z][\w ]+:)", text, re.S | re.M)
    return [p.rstrip("/*") for p in re.findall(r"`([^`\s]+/[^`\s]*|[^`\s]+\.\w+)`", m.group(1))] if m else []


def mine(repo: Path, brief: Path) -> dict:
    rel = brief.relative_to(repo).as_posix()
    log = [l.split("\t") for l in git(repo, "log", "--follow", "--format=%h\t%ct\t%s", "--", rel).splitlines() if l]
    if not log:
        return {}
    log.sort(key=lambda x: int(x[1]))
    t0 = int(log[0][1])
    done_ts = next((int(t) for _, t, s in log[1:] if DONE.search(s)), None)
    paths = owned(brief.read_text(errors="ignore"))
    rec = {"project": project(repo), "path": rel, "plan": rel.split("/")[2], "first_commit_ts": t0, "brief_edits": len(log) - 1,
           "edited_after_landing": bool(done_ts), "owned_paths": len(paths),
           "remediation_sibling": any(re.search(r"remediat|fix", p.name) for p in brief.parent.glob("*.md") if p != brief) if not re.search(r"remediat|fix", brief.name) else False,
           "is_remediation": bool(re.search(r"remediat|fix", brief.name))}
    for days in (14, 60):
        if not paths:
            rec[f"churn_{days}d"] = rec[f"fixchurn_{days}d"] = None
            continue
        out = git(repo, "log", "--all", f"--since=@{t0}", f"--until=@{t0 + days * 86400}", "--no-merges", "--format=%h\t%s", "--", *paths)
        subs = [l.split("\t", 1)[1] for l in out.splitlines() if "\t" in l and not l.split("\t", 1)[1].startswith("docs")]
        rec[f"churn_{days}d"] = len(subs)
        rec[f"fixchurn_{days}d"] = sum(bool(FIX.search(s)) for s in subs)
    return rec


if __name__ == "__main__":
    root = Path(sys.argv[1])
    only = set(sys.argv[2:])  # restrict to named projects
    seen: set[tuple[str, str]] = set()
    for brief in sorted(root.glob("*/docs/plans/*/briefs/*.md")) + sorted(root.glob("*/docs/plans/*/briefs/*/*.md")):
        repo = Path(git(brief.parent, "rev-parse", "--show-toplevel").strip() or ".")
        r = mine(repo, brief)
        key = (r.get("project"), r.get("path"))
        if not r or key in seen or (only and r["project"] not in only):
            continue
        seen.add(key)
        print(json.dumps(r))
