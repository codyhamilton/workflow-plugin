"""Full text of every posted design/brief version, in bodies.db beside the ledger (kept out of quality.db for size and lock reasons).
Content-addressed by the same sha as scores.sha, so a version joins to its scores. Stored text is secret-scrubbed. FTS5 search over all versions."""
from __future__ import annotations

import sqlite3
import time
from typing import Any

import quality as q

SCHEMA = """
CREATE TABLE IF NOT EXISTS body(sha TEXT PRIMARY KEY, text TEXT NOT NULL, size INTEGER, ts REAL);
CREATE TABLE IF NOT EXISTS ref(id INTEGER PRIMARY KEY, artifact_id INTEGER NOT NULL, sha TEXT NOT NULL REFERENCES body(sha), ts REAL,
  conversation_id TEXT, workflow_version TEXT, harness TEXT, UNIQUE(artifact_id, sha));
CREATE INDEX IF NOT EXISTS ix_ref_art ON ref(artifact_id, ts);
CREATE VIRTUAL TABLE IF NOT EXISTS body_fts USING fts5(text, content='body', content_rowid='rowid', tokenize='porter unicode61');
CREATE TRIGGER IF NOT EXISTS body_ai AFTER INSERT ON body BEGIN INSERT INTO body_fts(rowid, text) VALUES (new.rowid, new.text); END;
CREATE TRIGGER IF NOT EXISTS body_ad AFTER DELETE ON body BEGIN INSERT INTO body_fts(body_fts, rowid, text) VALUES ('delete', old.rowid, old.text); END;
"""


def db() -> sqlite3.Connection:
    d = q.store_dir(); d.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(d / "bodies.db", timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=10000"); c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    return c


def put(artifact_id: int, sha: str, text: str, ctx: dict[str, Any]) -> bool:
    """Record this version for the artifact. True if the artifact had not seen this sha."""
    from hooklog import scrub
    with db() as c:
        c.execute("INSERT OR IGNORE INTO body(sha,text,size,ts) VALUES(?,?,?,?)", (sha, scrub(text, 10**9), len(text), time.time()))
        cur = c.execute("INSERT OR IGNORE INTO ref(artifact_id,sha,ts,conversation_id,workflow_version,harness) VALUES(?,?,?,?,?,?)",
                        (artifact_id, sha, time.time(), ctx.get("conversation_id"), ctx.get("workflow_version"), ctx.get("harness")))
        return bool(cur.rowcount)


def versions(artifact_id: int) -> list[dict[str, Any]]:
    with db() as c:
        return [dict(r) for r in c.execute("SELECT r.sha, r.ts, r.conversation_id, r.workflow_version, r.harness, b.size FROM ref r JOIN body b USING(sha)"
                                           " WHERE r.artifact_id=? ORDER BY r.ts, r.id", (artifact_id,))]


def get(artifact_id: int, sha: str | None = None) -> dict[str, Any] | None:
    with db() as c:
        r = c.execute("SELECT r.sha, r.ts, b.text FROM ref r JOIN body b USING(sha) WHERE r.artifact_id=?" + (" AND r.sha=?" if sha else "")
                      + " ORDER BY r.ts DESC, r.id DESC LIMIT 1", (artifact_id, sha) if sha else (artifact_id,)).fetchone()
        return dict(r) if r else None


def search(query: str, kind: str | None = None, project: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """FTS5 query syntax (terms, "phrases", AND/OR/NOT, prefix*). Hits are artifact versions, best first."""
    with db() as c:
        try:
            hits = c.execute("SELECT r.artifact_id, r.sha, r.ts, snippet(body_fts, 0, '[', ']', ' … ', 24) AS snippet, bm25(body_fts) AS rank FROM body_fts"
                             " JOIN body b ON b.rowid=body_fts.rowid JOIN ref r ON r.sha=b.sha WHERE body_fts MATCH ? ORDER BY rank LIMIT ?", (query, int(limit) * 4)).fetchall()
        except sqlite3.OperationalError as e:
            raise ValueError(f"bad search query: {e}")
    with q.db() as m:
        out = []
        for h in hits:
            a = m.execute("SELECT kind, project, plan, path FROM artifacts WHERE id=?", (h["artifact_id"],)).fetchone()
            if a and (not kind or a["kind"] == kind) and (not project or a["project"] == project):
                out.append({**dict(h), **dict(a)})
        return out[: int(limit)]
