"""Backfill bodies.db for artifacts scored before bodies were stored: find, in each artifact's repo history,
the file version whose sha matches a recorded score sha. Usage: backfill_bodies.py [--dry]"""
import hashlib
import subprocess
import sys
from pathlib import Path

import bodies
import quality as q
from hooklog import scrub


WS = Path.home() / "workspace"


def repo_for(proj):
    for c in (WS / proj, Path.home() / ".cursor/plugins/local" / proj):
        if (c / ".git").exists():
            return str(c)
    return None


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout


def main(dry):
    con = q.db()
    arts = con.execute("select a.id,a.kind,a.project,a.path,a.repo_path from artifacts a").fetchall()
    shas = {}
    for aid, sha in con.execute("select artifact_id, sha from scores"):
        shas.setdefault(aid, set()).add(sha)
    got = miss = 0
    for aid, kind, proj, path, repo in arts:
        want = shas.get(aid, set())
        repo = repo or repo_for(proj)
        if not want or not repo:
            miss += bool(want)
            continue
        rel = path
        found = set()
        for c in git(repo, "log", "--all", "--format=%H", "--", rel).split():
            t = git(repo, "show", f"{c}:{rel}")
            h = hashlib.sha256(t.encode()).hexdigest()[:16]
            if h in want and h not in found:
                found.add(h)
                if not dry:
                    bodies.put(aid, h, scrub(t, 10**7), {"kind": kind, "project": proj, "path": path})
        got += len(found)
        miss += len(want - found)
    print(f"versions found {got}, not found {miss}")


if __name__ == "__main__":
    main("--dry" in sys.argv)
