"""Extract subagent (executor) passages that complain about the brief/plan, with the task prompt they were given.
Usage: executor_reports.py <project-dir> > rows.jsonl   (scrubbed with hooklog.scrub)"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooklog"))
from hooklog import scrub

PAT = re.compile(r"(brief (says|states|is wrong|is ambiguous|contradict)|not in (the )?brief|brief (does not|doesn't|omits|missing)|ambigu|contradict|assumption|cannot be (met|satisfied)|impossible|unclear|stale|doesn't match|does not match)", re.I)


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text")


def rows(project):
    for f in sorted(glob.glob(os.path.join(project, "**", "subagents", "*.jsonl"), recursive=True)):
        task, n = None, 0
        for l in open(f, errors="ignore"):
            try:
                d = json.loads(l)
            except ValueError:
                continue
            m = d.get("message") or {}
            if d.get("type") == "user" and task is None:
                task = text_of(m.get("content"))
            elif d.get("type") == "assistant":
                n += 1
                t = text_of(m.get("content"))
                hit = PAT.search(t)
                if hit and len(t) > 80:
                    yield {"file": os.path.basename(f), "n": n, "ts": d.get("timestamp"), "match": hit.group(0),
                           "task": scrub(task or "", 3000), "text": scrub(t, 2500)}


if __name__ == "__main__":
    for r in rows(sys.argv[1]):
        print(json.dumps(r))
