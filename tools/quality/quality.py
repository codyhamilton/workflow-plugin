#!/usr/bin/env python3
"""Score workflow briefs and designs against criteria.json, log every score, return ratings.

Informational and comparative: nothing here gates a workflow. Every scored artifact goes to the SQLite db
  $WORKFLOW_QUALITY_DIR or ~/.local/share/workflow-plugin/quality/quality.db
  (artifacts, scores, criterion_scores, links). `links` back-references later rework, missing scope or defects to the brief/design
  they trace to (`link` command; derived_from / overlaps_prior are added automatically).
tagged workflow_artifact=true.
Deterministic checks always run; Jev criteria run when TYPESAFE_API_KEY is set, after the hooklog secret scrub.

  quality.py score <path> [--kind brief|design] [--no-jev] [--no-log]
  quality.py backfill <workspace-root> [--no-jev]
  quality.py link --to <path> --type rework|missing_scope|defect|supersedes [--from <path>] [--note ..]
  quality.py report [--kind brief|design] [--by project|plan]
  quality.py hook            # PostToolUse stdin payload -> additionalContext when a brief/DESIGN.md was written
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(ROOT / "tools/transcript"), str(ROOT / "tools/hooklog")]
CRIT = json.loads((HERE / "criteria.json").read_text())
REG_VERSION = CRIT["version"]


def store_dir() -> Path:
    return Path(os.environ.get("WORKFLOW_QUALITY_DIR") or Path.home() / ".local/share/workflow-plugin/quality")


def kind_of(path: Path) -> str | None:
    p = path.as_posix()
    if path.name == "DESIGN.md" and "/docs/plans/" in p:
        return "design"
    if "/briefs/" in p and path.suffix == ".md" and "/docs/plans/" in p:
        return "brief"
    return None


_FM = re.compile(r"\A---\n(.*?)\n---[ \t]*\n?", re.S)


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Flat `key: value` frontmatter (identity only: design_id, brief_id) and the body. Ids never affect the score or the content hash."""
    m = _FM.match(text)
    if not m:
        return {}, text
    fm = {k.strip(): v.split("#")[0].strip().strip("\"'") for k, _, v in (ln.partition(":") for ln in m.group(1).splitlines()) if k.strip()}
    return fm, text[m.end():].lstrip("\n")


def sections(text: str, level: str = "## ") -> dict[str, str]:
    out: dict[str, list[str]] = {}
    cur = None
    for ln in text.splitlines():
        if ln.startswith(level) and not ln.startswith(level + "#"):
            cur = ln[len(level):].strip().lower()
            out[cur] = []
        elif cur is not None:
            out[cur].append(ln)
    return {k: "\n".join(v) for k, v in out.items()}


def has(secs: dict[str, str], *names: str) -> int:
    return sum(any(n in k for k in secs) for n in names)


def _git(repo: Path, *a: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def project_name(repo: Path) -> str:
    """Stable across clones and worktrees of one repo: origin URL basename, else the directory name."""
    u = _git(repo, "config", "--get", "remote.origin.url")
    return re.sub(r"\.git$", "", u.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]) if u else repo.name


def repo_root(path: Path) -> Path:
    r = _git(path.parent, "rev-parse", "--show-toplevel")
    if r:
        return Path(r)
    for a in path.parents:  # not a git checkout: the directory that holds docs/plans
        if a.name == "plans" and a.parent.name == "docs":
            return a.parent.parent
    return path.parent


# ---------- deterministic criteria (0-1, higher better) ----------

def det_brief(text: str, repo: Path) -> dict[str, tuple[float, Any]]:
    s = sections(text)
    need = ("required reading", "goal", "contract", "changes", "done evidence", "report back")
    out: dict[str, tuple[float, Any]] = {}
    out["b.sections"] = (has(s, *need) / len(need), {"missing": [n for n in need if not has(s, n)]})
    cons = bool(re.search(r"^Consumer:", text, re.M)); owned = re.search(r"^Owned paths:\s*(.+)$", text, re.M)
    paths = re.findall(r"`([^`]+)`", owned.group(1)) if owned else []
    out["b.consumer_and_owned"] = ((cons + bool(paths)) / 2, {"consumer": cons, "owned": len(paths)})
    exist = new = 0
    for p in paths:
        if (repo / p).exists():
            exist += 1
        elif re.search(re.escape(p) + r"[^\n]{0,80}\b(new|create|added?)\b", text, re.I) or re.search(r"\b(new|create)\b[^\n]{0,80}" + re.escape(p), text, re.I):
            new += 1
    out["b.owned_paths_resolve"] = (((exist + new) / len(paths)) if paths else 0.0, {"existing": exist, "declared_new": new, "unresolved": len(paths) - exist - new})
    bud = re.search(r"^Budget:\s*(.+)$", text, re.M); b = bud.group(1) if bud else ""
    got = [bool(re.search(r"\d+\s*files?", b)), bool(re.search(r"\d+\s*lines?", b)), bool(re.search(r"\d+\s*(tool )?turns?", b))]
    out["b.budget_complete"] = (sum(got) / 3, {"files_lines_turns": got})
    de = s.get(next((k for k in s if "done evidence" in k), ""), "")
    items = [l for l in de.splitlines() if re.match(r"\s*[-*]\s+", l)]
    ok = [bool(re.search(r"`[^`]+`", l) and re.search(r"→|->|=>|expected|exit|passes|fails|returns|prints", l, re.I)) for l in items]
    out["b.done_runnable"] = ((sum(ok) / len(ok)) if ok else 0.0, {"items": len(items), "runnable": sum(ok)})
    rd = s.get(next((k for k in s if "required reading" in k), ""), "")
    rl = [l for l in rd.splitlines() if re.match(r"\s*\d+\.", l)]
    spec = [bool(re.search(r"`[^`]+`\s*[—-]\s*\S{12,}|:\d+|lines? \d+|§|section", l)) for l in rl]
    out["b.reading_specific"] = ((sum(spec) / len(spec)) if spec else 0.0, {"entries": len(rl), "specific": sum(spec)})
    return out


def det_design(text: str, repo: Path) -> dict[str, tuple[float, Any]]:
    s = sections(text)
    need = ("intent", "problem", "solution shape", "decisions", "open questions", "phases")
    out: dict[str, tuple[float, Any]] = {}
    out["d.sections"] = (has(s, *need) / len(need), {"missing": [n for n in need if not has(s, n)]})
    intent = s.get("intent", "")
    out["d.intent_verbatim"] = (1.0 if re.search(r"^\s*>\s*\S", intent, re.M) else 0.0, {})
    doms = re.split(r"^### Domain:", text, flags=re.M)[1:]
    dok = [all(re.search(rf"^- {f}:\s*\S", d, re.M | re.I) for f in ("Owns", "Contract", "Non-goals")) for d in doms]
    if dok:  # no Domain headings = pre-template era: not applicable, not zero (see facts.legacy_format)
        out["d.domains_complete"] = (sum(dok) / len(dok), {"domains": len(dok)})
    ph = re.split(r"^### Phase \d+", text, flags=re.M)[1:]
    pok = [all(re.search(rf"^- {f}:\s*\S", p, re.M | re.I) for f in ("Outcome", "Surfaces", "Approach", "Depends on")) for p in ph]
    if pok:
        out["d.phases_complete"] = (sum(pok) / len(pok), {"phases": len(ph), "open_approach": sum(bool(re.search(r"Approach:\s*open", p, re.I)) for p in ph)})
    asm = re.split(r"^### Assumption \d+", text, flags=re.M)[1:]
    if asm:
        aok = [all(re.search(rf"^- {f}:\s*\S", a, re.M | re.I) for f in ("Question", "Answer chosen", "Rationale", "If wrong")) for a in asm]
        out["d.ledger_complete"] = (sum(aok) / len(aok), {"assumptions": len(asm)})
    return out


def context_facts(kind: str, text: str) -> dict[str, Any]:
    """Size and shape, logged for relative analysis; never scored as good or bad."""
    f: dict[str, Any] = {"chars": len(text), "lines": text.count("\n") + 1}
    if kind == "brief":
        ch = sections(text).get(next((k for k in sections(text) if k.startswith("changes")), ""), "")
        f["change_items"] = len(re.findall(r"^\s*(?:[-*]|\d+\.)\s", ch, re.M))
    else:
        f["phases"] = len(re.findall(r"^### Phase \d+", text, re.M)); f["domains"] = len(re.findall(r"^### Domain:", text, re.M))
        f["legacy_format"] = not (f["phases"] and f["domains"])
    return f


# ---------- Jev criteria ----------

def jev_scores(kind: str, text: str) -> tuple[dict[str, tuple[float, Any]], str | None]:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return {}, "no TYPESAFE_API_KEY"
    try:
        from lib.jev_client import JEV_MODEL, post_systemone
        from hooklog import scrub
    except Exception as e:  # pragma: no cover
        return {}, f"jev client unavailable: {e}"
    spec = CRIT[kind]["jev"]
    qs = {k: {"type": "score", "instructions": v["q"], "criteria": v["levels"]} for k, v in spec.items()}
    snap = ("BRIEF:\n" if kind == "brief" else "DESIGN DOCUMENT:\n") + scrub(text[:60000], 10**9)
    try:
        resp = post_systemone({"model": JEV_MODEL, "state": {"snapshot": snap}, "questions": qs})
    except SystemExit as e:
        return {}, str(e)
    out = {}
    for k, v in spec.items():
        a = resp.get("answers", {}).get(k)
        if a is not None:
            x = a["score"] / 3
            out[k] = (round(1 - x if v["invert"] else x, 3), {"raw": a["score"], "model": resp.get("model")})
    return out, None


# ---------- scoring, logging, relative rating ----------

def score_text(kind: str, text: str, repo: Path, use_jev: bool = True) -> dict[str, Any]:
    det = (det_brief if kind == "brief" else det_design)(text, repo)
    jev, err = jev_scores(kind, text) if use_jev else ({}, "jev disabled")
    crit = {k: {"score": round(v[0], 3), "how": "det", "detail": v[1]} for k, v in det.items()}
    crit.update({k: {"score": v[0], "how": "jev", "detail": v[1]} for k, v in jev.items()})
    sc = [c["score"] for c in crit.values()]
    return {"criteria": crit, "composite": round(sum(sc) / len(sc), 3) if sc else None,
            "composite_det": round(sum(c["score"] for c in crit.values() if c["how"] == "det") / max(1, len(det)), 3),
            "jev_error": err, "facts": context_facts(kind, text)}


def tag(path: Path, repo: Path, harness: str, session: str) -> dict[str, Any]:
    try:
        ver = json.loads((ROOT / ".claude-plugin/plugin.json").read_text()).get("version")
    except Exception:
        ver = None
    rel = path.resolve().relative_to(repo.resolve()).as_posix() if path.resolve().is_relative_to(repo.resolve()) else str(path)
    m = re.search(r"docs/plans/([^/]+)/", rel)
    return {"workflow_artifact": True, "plugin_version": ver, "harness": harness, "session_id": session, "project": project_name(repo),
            "plan": m.group(1) if m else None, "path": rel, "head": _git(repo, "rev-parse", "--short", "HEAD") or None, "repo": str(repo)}


SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, project TEXT NOT NULL, plan TEXT, path TEXT NOT NULL,
  first_seen REAL, UNIQUE(kind, project, path));
CREATE TABLE IF NOT EXISTS scores(id INTEGER PRIMARY KEY, artifact_id INTEGER NOT NULL REFERENCES artifacts(id), ts REAL, sha TEXT, registry TEXT,
  harness TEXT, session_id TEXT, head TEXT, plugin_version TEXT, workflow_artifact INTEGER DEFAULT 1, composite REAL, composite_det REAL,
  jev_error TEXT, facts TEXT, UNIQUE(artifact_id, sha, registry));
CREATE TABLE IF NOT EXISTS criterion_scores(score_id INTEGER NOT NULL REFERENCES scores(id), criterion TEXT NOT NULL, score REAL, how TEXT, detail TEXT,
  PRIMARY KEY(score_id, criterion));
CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY, ts REAL, from_artifact INTEGER REFERENCES artifacts(id), to_artifact INTEGER NOT NULL REFERENCES artifacts(id),
  type TEXT NOT NULL, note TEXT, evidence TEXT, source TEXT, UNIQUE(from_artifact, to_artifact, type, evidence));
CREATE INDEX IF NOT EXISTS ix_scores_art ON scores(artifact_id, ts);
CREATE TABLE IF NOT EXISTS executions(id INTEGER PRIMARY KEY, brief_id INTEGER NOT NULL REFERENCES artifacts(id), started REAL, ended REAL, status TEXT,
  outcome TEXT, summary TEXT, metrics TEXT, harness TEXT, workflow_version TEXT, model TEXT, conversation_id TEXT, initiator_type TEXT, initiator_id TEXT,
  repo TEXT, head_start TEXT, head_end TEXT, design_stage TEXT, execution_stage TEXT,
  cost_usd REAL, tokens_in INTEGER, tokens_out INTEGER, turns INTEGER, tool_calls INTEGER);
CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY, execution_id INTEGER NOT NULL REFERENCES executions(id), brief_id INTEGER NOT NULL REFERENCES artifacts(id),
  ts REAL, kind TEXT NOT NULL, category TEXT, severity TEXT, text TEXT NOT NULL, UNIQUE(execution_id, kind, text));
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts REAL, event TEXT NOT NULL, artifact_id INTEGER, execution_id INTEGER, harness TEXT, workflow_version TEXT,
  model TEXT, conversation_id TEXT, initiator_type TEXT, initiator_id TEXT, repo TEXT, design_stage TEXT, execution_stage TEXT, payload TEXT);
CREATE INDEX IF NOT EXISTS ix_events_art ON events(artifact_id, ts);
CREATE INDEX IF NOT EXISTS ix_exec_brief ON executions(brief_id);
"""
MIGRATE = {"artifacts": [("parent_id", "INTEGER"), ("repo_path", "TEXT"), ("design_stage", "TEXT"), ("execution_stage", "TEXT"), ("work_type", "TEXT")],
           "scores": [("model", "TEXT"), ("initiator_type", "TEXT"), ("initiator_id", "TEXT"), ("repo", "TEXT")]}
LINK_TYPES = ("rework", "missing_scope", "defect", "supersedes", "derived_from", "overlaps_prior")


def db() -> sqlite3.Connection:
    d = store_dir(); d.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(d / "quality.db"); c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    for t, cols in MIGRATE.items():
        have = {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
        for n, ty in cols:
            if n not in have:
                c.execute(f"ALTER TABLE {t} ADD COLUMN {n} {ty}")
    return c


def artifact_id(c: sqlite3.Connection, kind: str, project: str, path: str, plan: str | None, ts: float) -> int:
    c.execute("INSERT OR IGNORE INTO artifacts(kind,project,plan,path,first_seen) VALUES(?,?,?,?,?)", (kind, project, plan, path, ts))
    return c.execute("SELECT id FROM artifacts WHERE kind=? AND project=? AND path=?", (kind, project, path)).fetchone()[0]


def log_row(row: dict[str, Any]) -> bool:
    """Insert one score (idempotent on artifact+content hash+registry). Returns True if new."""
    with db() as c:
        aid = artifact_id(c, row["kind"], row["project"], row["path"], row.get("plan"), row["ts"])
        if not row["jev_error"]:  # a Jev-scored row replaces an earlier deterministic-only row for the same content
            old = c.execute("SELECT id FROM scores WHERE artifact_id=? AND sha=? AND registry=? AND jev_error IS NOT NULL", (aid, row["sha"], row["registry"])).fetchone()
            if old:
                c.execute("DELETE FROM criterion_scores WHERE score_id=?", (old[0],)); c.execute("DELETE FROM scores WHERE id=?", (old[0],))
        cur = c.execute("INSERT OR IGNORE INTO scores(artifact_id,ts,sha,registry,harness,session_id,head,plugin_version,workflow_artifact,composite,composite_det,jev_error,facts)"
                        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (aid, row["ts"], row["sha"], row["registry"], row["harness"], row["session_id"], row["head"],
                        row["plugin_version"], 1, row["composite"], row["composite_det"], row["jev_error"], json.dumps(row["facts"])))
        if cur.rowcount:
            c.execute("UPDATE scores SET model=?,initiator_type=?,initiator_id=?,repo=? WHERE id=?",
                      (row.get("model"), row.get("initiator_type"), row.get("initiator_id"), row.get("repo"), cur.lastrowid))
            c.executemany("INSERT INTO criterion_scores VALUES(?,?,?,?,?)", [(cur.lastrowid, k, v["score"], v["how"], json.dumps(v["detail"])) for k, v in row["criteria"].items()])
        row["artifact_id"] = aid
        return bool(cur.rowcount)


def rows(kind: str | None = None) -> list[dict[str, Any]]:
    """Every logged score as a dict (criteria included), oldest first."""
    if not (store_dir() / "quality.db").exists():
        return []
    with db() as c:
        q = "SELECT s.*, a.kind, a.project, a.plan, a.path FROM scores s JOIN artifacts a ON a.id=s.artifact_id" + (" WHERE a.kind=?" if kind else "") + " ORDER BY s.ts, s.id"
        out = []
        for r in c.execute(q, (kind,) if kind else ()):
            d = dict(r); d["facts"] = json.loads(d["facts"] or "{}")
            d["criteria"] = {x["criterion"]: {"score": x["score"], "how": x["how"]} for x in c.execute("SELECT * FROM criterion_scores WHERE score_id=?", (r["id"],))}
            out.append(d)
        return out


def latest_per_artifact(rs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    d: dict[tuple, dict] = {}
    for r in sorted(rs, key=lambda r: r["ts"]):
        d[(r["kind"], r["project"], r["path"])] = r
    return list(d.values())


def percentile(v: float, ref: list[float]) -> float | None:
    return round(sum(x < v for x in ref) / len(ref) + 0.5 * sum(x == v for x in ref) / len(ref), 2) if ref else None


def rate(res: dict[str, Any], kind: str, exclude: tuple | None = None) -> dict[str, Any]:
    """Relative rating vs every other logged artifact of the same kind (latest version of each)."""
    ref = [r for r in latest_per_artifact(rows(kind)) if (r["kind"], r["project"], r["path"]) != exclude]
    out: dict[str, Any] = {"vs_n": len(ref)}
    if res["composite"] is not None:
        out["composite_percentile"] = percentile(res["composite"], [r["composite"] for r in ref if r.get("composite") is not None])
    out["criterion_percentile"] = {k: percentile(c["score"], [r["criteria"][k]["score"] for r in ref if k in r["criteria"]]) for k, c in res["criteria"].items()}
    return out


def summary(row: dict[str, Any]) -> str:
    c = row["criteria"]; weak = sorted(c.items(), key=lambda kv: kv[1]["score"])[:3]
    rt = row["rating"]; pct = rt.get("composite_percentile")
    rel = f"{int(pct * 100)}th percentile of {rt['vs_n']} logged {row['kind']}s" if pct is not None and rt["vs_n"] >= 5 else f"not enough history to rank ({rt['vs_n']} logged {row['kind']}s)"
    return (f"[workflow quality, informational] {row['kind']} {row['path']}: composite {row['composite']} ({rel}). Weakest: "
            + "; ".join(f"{k} {v['score']}" for k, v in weak) + (f". Jev unavailable: {row['jev_error']}" if row.get("jev_error") else "") + ".")


def score_content(kind: str, text: str, path: Path, repo: Path, use_jev: bool, log: bool, harness="manual", session="manual", ts=None, **over: Any) -> dict[str, Any]:
    text = split_frontmatter(text)[1]
    res = score_text(kind, text, repo, use_jev)
    row = {"v": 1, "ts": ts or time.time(), "kind": kind, "registry": REG_VERSION, "sha": hashlib.sha256(text.encode()).hexdigest()[:16], **tag(path, repo, harness, session), **res}
    row.update({k: v for k, v in over.items() if v})
    row["rating"] = rate(res, kind, (kind, row["project"], row["path"]))
    if log:
        log_row(row)
        row["links_added"] = auto_links(row)
    return row


def score_path(path: Path, kind: str | None, use_jev: bool, log: bool, harness="manual", session="manual", ts=None) -> dict[str, Any]:
    path = path.resolve(); kind = kind or kind_of(path)
    if kind is None:
        raise SystemExit(f"{path} is not a brief or DESIGN.md under docs/plans/")
    return score_content(kind, path.read_text(errors="ignore"), path, repo_root(path), use_jev, log, harness, session, ts)


def owned_paths(repo: Path, rel: str) -> set[str]:
    try:
        t = (repo / rel).read_text(errors="ignore")
    except OSError:
        return set()
    m = re.search(r"^Owned paths:\s*(.+)$", t, re.M)
    return set(re.findall(r"`([^`]+)`", m.group(1))) if m else set()


def auto_links(row: dict[str, Any]) -> int:
    """Deterministic back-references: brief -> its plan's DESIGN.md (derived_from); brief -> earlier briefs in the project whose
    owned paths overlap (overlaps_prior: candidate rework / missing scope, to be confirmed with `link`)."""
    if row["kind"] != "brief":
        return 0
    repo = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel") or ".")
    n = 0
    with db() as c:
        me = row["artifact_id"]
        d = c.execute("SELECT id FROM artifacts WHERE kind='design' AND project=? AND plan=?", (row["project"], row["plan"])).fetchone()
        if d:
            n += c.execute("INSERT OR IGNORE INTO links(ts,from_artifact,to_artifact,type,evidence,source) VALUES(?,?,?,?,?,?)", (time.time(), me, d[0], "derived_from", "plan", "auto")).rowcount
        mine = owned_paths(Path(row.get("repo") or repo), row["path"]) if row.get("repo") else set()
        for o in c.execute("SELECT id, path, first_seen FROM artifacts WHERE kind='brief' AND project=? AND id<>? AND first_seen<=?", (row["project"], me, row["ts"])):
            if mine & owned_paths(Path(row["repo"]), o["path"]):
                n += c.execute("INSERT OR IGNORE INTO links(ts,from_artifact,to_artifact,type,evidence,source) VALUES(?,?,?,?,?,?)",
                               (time.time(), me, o["id"], "overlaps_prior", ",".join(sorted(mine & owned_paths(Path(row["repo"]), o["path"])))[:300], "auto")).rowcount
    return n


def cmd_link(frm: str | None, to: str, typ: str, note: str, evidence: str) -> int:
    """Record that later work (rework, missing scope, a defect) traces back to an earlier brief/design: `link --to <path> --type defect --note ... [--from <path>]`."""
    def find(c, p):
        r = c.execute("SELECT id FROM artifacts WHERE path=? OR path LIKE ? ORDER BY first_seen DESC", (p, "%" + p)).fetchone()
        if not r:
            raise SystemExit(f"no scored artifact matches {p}")
        return r[0]
    with db() as c:
        f = find(c, frm) if frm else None
        c.execute("INSERT OR IGNORE INTO links(ts,from_artifact,to_artifact,type,note,evidence,source) VALUES(?,?,?,?,?,?,?)", (time.time(), f, find(c, to), typ, note, evidence, "manual"))
    print("linked"); return 0


def cmd_hook() -> int:
    try:
        p = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    ti = p.get("tool_input") or {}
    fp = ti.get("file_path") or ti.get("path") or ti.get("filePath")
    if not fp or not Path(fp).exists() or kind_of(Path(fp).resolve()) is None:
        return 0
    harness = "cursor" if (p.get("cursor_version") or p.get("conversation_id")) else "claude"
    r = score_path(Path(fp), None, True, True, harness, str(p.get("session_id") or p.get("conversation_id") or "unknown"))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": summary(r)}}))
    return 0


def cmd_backfill(root: Path, use_jev: bool) -> int:
    done = {(r["kind"], r["project"], r["path"], r["sha"], r["registry"]) for r in rows() if not (use_jev and r.get("jev_error"))}
    paths = sorted(set(root.glob("*/docs/plans/*/briefs/*.md")) | set(root.glob("*/docs/plans/*/DESIGN.md")))
    n = 0
    for p in paths:
        k = kind_of(p)
        if not k:
            continue
        repo = repo_root(p)
        text = p.read_text(errors="ignore")
        key = (k, project_name(repo), p.resolve().relative_to(repo.resolve()).as_posix() if p.resolve().is_relative_to(repo.resolve()) else str(p), hashlib.sha256(text.encode()).hexdigest()[:16], REG_VERSION)
        if key in done:
            continue
        ts = _git(repo, "log", "-1", "--format=%ct", "--", str(p))
        score_path(p, k, use_jev, True, "backfill", "backfill", ts=float(ts) if ts else p.stat().st_mtime)
        n += 1
    print(json.dumps({"scored": n, "candidates": len(paths)}))
    return 0


def cmd_report(kind: str | None, by: str) -> int:
    rs = latest_per_artifact(rows(kind))
    g: dict[tuple, list] = {}
    for r in rs:
        g.setdefault((r["kind"], r.get(by) or "?"), []).append(r)
    print(f"{'kind':7} {by:36} {'n':>4} {'composite':>9} {'det':>6}  weakest criterion (mean)")
    for (k, name), v in sorted(g.items()):
        mean = lambda xs: sum(xs) / len(xs)
        crit: dict[str, list] = {}
        for r in v:
            for c, d in r["criteria"].items():
                crit.setdefault(c, []).append(d["score"])
        wk = min(crit.items(), key=lambda kv: mean(kv[1]))
        comp = [r["composite"] for r in v if r.get("composite") is not None]
        print(f"{k:7} {name[:36]:36} {len(v):4} {mean(comp) if comp else float('nan'):9.2f} {mean([r['composite_det'] for r in v]):6.2f}  {wk[0]} {mean(wk[1]):.2f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("score"); s.add_argument("path"); s.add_argument("--kind", choices=["brief", "design"]); s.add_argument("--no-jev", action="store_true"); s.add_argument("--no-log", action="store_true")
    b = sp.add_parser("backfill"); b.add_argument("root"); b.add_argument("--no-jev", action="store_true")
    r = sp.add_parser("report"); r.add_argument("--kind", choices=["brief", "design"]); r.add_argument("--by", default="project", choices=["project", "plan"])
    sp.add_parser("hook")
    l = sp.add_parser("link"); l.add_argument("--to", required=True); l.add_argument("--from", dest="frm"); l.add_argument("--type", required=True, choices=LINK_TYPES); l.add_argument("--note", default=""); l.add_argument("--evidence", default="")
    a = ap.parse_args()
    if a.cmd == "hook":
        return cmd_hook()
    if a.cmd == "link":
        return cmd_link(a.frm, a.to, a.type, a.note, a.evidence)
    if a.cmd == "backfill":
        return cmd_backfill(Path(a.root).expanduser(), not a.no_jev)
    if a.cmd == "report":
        return cmd_report(a.kind, a.by)
    row = score_path(Path(a.path), a.kind, not a.no_jev, not a.no_log)
    print(json.dumps(row, indent=1)); print(summary(row), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
