"""Extract numeric thresholds (with surrounding context) from plan briefs found anywhere in a git repo's history.
Usage: thresholds.py <repo> > rows.jsonl   Rows are scrubbed; one row per threshold line."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooklog"))
from hooklog import scrub

CMP = re.compile(r"(≤|≥|<=|>=|\bat most\b|\bat least\b|\bno more than\b|\bno fewer than\b|\bmust not exceed\b|\bunder \d|\bover \d|\bwithin \d|\bbelow \d|\babove \d|[<>]\s?\d)", re.I)
NUM = re.compile(r"\d[\d,._]*\s?(k|m|ms|s|kb|mb|gb|%|px|x|cells|rows|files|lines)?\b", re.I)
PTR = re.compile(r"(measured|measurement|benchmark|profil|baseline|observed|derived from|because|per spec|per \S+\.md|see \S+|\b[0-9a-f]{7,}\b|run on|\d{4}-\d\d-\d\d)", re.I)


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, errors="ignore").stdout


def briefs(repo):
    seen = {}
    for p in git(repo, "log", "--all", "--name-only", "--format=%H", "--", "docs/plans/*/briefs/*.md").split("\n"):
        pass
    commits = None
    out = git(repo, "log", "--all", "--name-only", "--format=@%H").split("@")
    for blk in out:
        lines = blk.strip().split("\n")
        if not lines or not lines[0]:
            continue
        for p in lines[1:]:
            if re.match(r"docs/plans/[^/]+/briefs/[^/]+\.md$", p) and p not in seen:
                seen[p] = lines[0]  # newest commit first
    for p, c in seen.items():
        yield p, git(repo, "show", f"{c}:{p}")


def rows(repo):
    for p, text in briefs(repo):
        ls = text.split("\n")
        for i, l in enumerate(ls):
            if CMP.search(l) and NUM.search(l) and not l.lstrip().startswith("#"):
                ctx = "\n".join(ls[max(0, i - 2): i + 3])
                yield {"brief": p, "line_no": i + 1, "line": scrub(l, 400), "context": scrub(ctx, 900), "ptr_regex": bool(PTR.search(ctx))}


if __name__ == "__main__":
    for r in rows(sys.argv[1]):
        print(json.dumps(r))
