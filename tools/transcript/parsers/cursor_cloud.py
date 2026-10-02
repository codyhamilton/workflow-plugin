"""Read locally cached Cursor cloud-run metadata and any cached conversation.

The `cloudAgentRepository.agents.*` cache has run IDs and timestamps only.
Conversation bodies exist locally for a small minority of runs, from two
stores (both populated only when the run was opened in the Cursor UI):

* `cursorDiskKV` composerData/bubbleId rows, the same model used for local
  chats. A run links to them via `composerData:<bc-id>` / `bubbleId:<bc-id>:*`
  keys or a local composer whose `createdFromBackgroundAgent.bcId` is the run.
  Bubbles may be absent (evicted/never loaded) even when headers remain.
* `conversation-search.db` `cloud-cache` rows: role-labelled flattened text
  (`user:` / `assistant:` blocks), no tool calls.

`bcCachedDetails:*` is a file-diff cache, not conversation. Turn counts are
reported as exact (`parent_*_turns`) only when every bubble header has a body;
otherwise they stay null and only `observed_*` lower bounds are given.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone

from lib.registry import REGISTRY
from lib.resolve import normalize_session_ref
from lib.types import NormalizedSession, SearchHit, SessionRef, SessionSummary


DEFAULT_DB = os.path.expanduser("~/.config/Cursor/User/globalStorage/state.vscdb")
DEFAULT_SEARCH_DB = os.path.expanduser("~/.config/Cursor/User/globalStorage/conversation-search.db")


def _iso(epoch_ms: int | None) -> str | None:
    if not isinstance(epoch_ms, (int, float)):
        return None
    return datetime.fromtimestamp(epoch_ms / 1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class CursorCloudParser:
    name = "cursor-cloud"

    def __init__(self, db_path: str = DEFAULT_DB, search_db_path: str = DEFAULT_SEARCH_DB) -> None:
        self.db_path = db_path
        self.search_db_path = search_db_path

    def _kv(self):
        if not os.path.isfile(self.db_path):
            return None
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def _linked_composers(self, conn) -> dict[str, list[str]]:
        """bc-id -> local composer ids whose createdFromBackgroundAgent.bcId matches (one scan, cached)."""
        if getattr(self, "_link_cache", None) is None:
            links: dict[str, list[str]] = {}
            for key, raw in conn.execute(
                "SELECT key, value FROM cursorDiskKV WHERE key >= 'composerData:' AND key < 'composerData;'"
            ):
                if not raw or "createdFromBackgroundAgent" not in raw:
                    continue
                try:
                    bc = (json.loads(raw).get("createdFromBackgroundAgent") or {}).get("bcId")
                except (TypeError, ValueError, AttributeError):
                    continue
                if isinstance(bc, str):
                    links.setdefault(bc, []).append(key.split(":", 1)[1])
            self._link_cache = links
        return self._link_cache

    def _bubbles(self, bc_id: str) -> dict | None:
        """Cached composer bubbles for a run, or None if no composer links to it."""
        conn = self._kv()
        if conn is None:
            return None
        try:
            composer_ids: list[str] = []
            if conn.execute("SELECT 1 FROM cursorDiskKV WHERE key = ?", (f"composerData:{bc_id}",)).fetchone():
                composer_ids.append(bc_id)
            for cid in self._linked_composers(conn).get(bc_id, []):
                if cid not in composer_ids:
                    composer_ids.append(cid)
            # bubbles stored directly under the run id without a composerData row
            if not composer_ids and conn.execute(
                "SELECT 1 FROM cursorDiskKV WHERE key >= ? AND key < ? LIMIT 1",
                (f"bubbleId:{bc_id}:", f"bubbleId:{bc_id};"),
            ).fetchone():
                composer_ids.append(bc_id)
            if not composer_ids:
                return None
            headers = 0
            bubbles: list[dict] = []
            for cid in composer_ids:
                row = conn.execute("SELECT value FROM cursorDiskKV WHERE key = ?", (f"composerData:{cid}",)).fetchone()
                order: dict[str, int] = {}
                if row and row[0]:
                    try:
                        hdrs = json.loads(row[0]).get("fullConversationHeadersOnly") or []
                    except (TypeError, ValueError):
                        hdrs = []
                    headers += len(hdrs)
                    order = {h.get("bubbleId"): i for i, h in enumerate(hdrs) if isinstance(h, dict)}
                for _key, raw in conn.execute(
                    "SELECT key, value FROM cursorDiskKV WHERE key >= ? AND key < ?",
                    (f"bubbleId:{cid}:", f"bubbleId:{cid};"),
                ):
                    if not raw:
                        continue
                    try:
                        b = json.loads(raw)
                    except (TypeError, ValueError):
                        continue
                    if isinstance(b, dict):
                        b["_order"] = order.get(b.get("bubbleId"), len(order) + len(bubbles))
                        bubbles.append(b)
            bubbles.sort(key=lambda b: (b["_order"], b.get("createdAt") or ""))
            return {"composer_ids": composer_ids, "headers": headers, "bubbles": bubbles}
        except sqlite3.DatabaseError:
            return None
        finally:
            conn.close()

    @staticmethod
    def _bubble_stats(info: dict) -> dict:
        user = asst = tools = 0
        for b in info["bubbles"]:
            if b.get("type") == 1:
                user += 1
            elif b.get("type") == 2:
                asst += 1
                if isinstance(b.get("toolFormerData"), dict) and b["toolFormerData"].get("name"):
                    tools += 1
        return {"user": user, "assistant": asst, "tools": tools}

    def _indexed_turns(self, bc_id: str) -> list[tuple[str, str]]:
        """Role-labelled blocks from the flattened search-index text."""
        body = self._indexed_body(bc_id)
        if not body:
            return []
        parts = re.split(r"(?m)^(user|assistant):\n", body)
        return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]

    def _indexed_body(self, bc_id: str) -> str:
        if not os.path.isfile(self.search_db_path):
            return ""
        conn = sqlite3.connect(f"file:{self.search_db_path}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT f.body FROM conversations c JOIN conversation_fts f ON c.fts_rowid = f.rowid "
                "WHERE c.id = ? AND c.source = 'cloud-cache'", (bc_id,)
            ).fetchone()
            return row[0] or "" if row else ""
        except sqlite3.DatabaseError:
            return ""
        finally:
            conn.close()

    def _indexed_chars(self, bc_id: str) -> int:
        """Length of flattened search-index text, if locally cached."""
        if not os.path.isfile(self.search_db_path):
            return 0
        conn = sqlite3.connect(f"file:{self.search_db_path}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT length(f.body) FROM conversations c "
                "JOIN conversation_fts f ON c.fts_rowid = f.rowid "
                "WHERE c.id = ? AND c.source = 'cloud-cache'", (bc_id,)
            ).fetchone()
            return int(row[0] or 0) if row else 0
        except sqlite3.DatabaseError:
            return 0
        finally:
            conn.close()

    def _rows(self) -> list[dict]:
        if not os.path.isfile(self.db_path):
            return []
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT value FROM ItemTable WHERE key LIKE 'cloudAgentRepository.agents.%'"
            ).fetchall()
        finally:
            conn.close()
        by_id: dict[str, dict] = {}
        for (raw,) in rows:
            try:
                entries = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and isinstance(entry.get("bcId"), str) and entry["bcId"].startswith("bc-"):
                    by_id[entry["bcId"]] = entry
        return list(by_id.values())

    def discover(
        self, project_path: str | None, *, match: str | None = None,
        since: str | None = None, min_subagents: int | None = None,
    ) -> list[SessionSummary]:
        # A cloud workspace path is a remote path, not a local project mapping.
        if not project_path:
            return []
        return self._discover(project_path, match, since, min_subagents)

    def discover_all(
        self, *, match: str | None = None, since: str | None = None,
        min_subagents: int | None = None,
    ) -> list[SessionSummary]:
        return self._discover(None, match, since, min_subagents)

    def _discover(self, project_path, match, since, min_subagents):
        if min_subagents is not None:
            return []  # Subagent count is unavailable.
        out = []
        for row in self._rows():
            path = row.get("workspaceRootPath")
            if project_path and path != project_path:
                continue
            if match and match.lower() not in f"{row['bcId']} {row.get('name', '')} {path or ''}".lower():
                continue
            start = _iso(row.get("createdAt"))
            if since and (start is None or start < since):
                continue
            out.append(SessionSummary(self.name, row["bcId"], None, path, start or "", None, 0))
        return out

    def resolve(self, session_ref: str, project_path: str | None) -> SessionRef:
        ref = normalize_session_ref(session_ref)
        matches = [r for r in self._rows() if r["bcId"].startswith(ref)
                   and (not project_path or r.get("workspaceRootPath") == project_path)]
        if not matches:
            raise FileNotFoundError(f"No cached cloud run matching {ref}")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous cloud-run prefix {ref}: {len(matches)} matches")
        row = matches[0]
        return SessionRef(self.name, row["bcId"], row.get("workspaceRootPath"), self.db_path)

    def extract(self, ref: SessionRef) -> NormalizedSession:
        row = next((r for r in self._rows() if r["bcId"] == ref.session_id), None)
        if row is None:
            raise FileNotFoundError(f"Cloud run {ref.session_id} is no longer in the local cache")
        start, end = _iso(row.get("createdAt")), _iso(row.get("updatedAt"))
        indexed_chars = self._indexed_chars(ref.session_id)
        info = self._bubbles(ref.session_id)
        stats = self._bubble_stats(info) if info else None
        have = len(info["bubbles"]) if info else 0
        idx = self._indexed_turns(ref.session_id)
        complete = bool(info and have and info["headers"] and have >= info["headers"])
        use_bubbles = bool(have and (complete or not idx))
        if use_bubbles:
            store, available = "cursorDiskKV composerData/bubbleId", True
        elif idx:
            store, available = "conversation-search.db cloud-cache (text only)", True
        else:
            store, available = "local cloud-run metadata cache only", False
        out = NormalizedSession(self.name, {
            "id": ref.session_id,
            "external_url": None,
            "project_path": row.get("workspaceRootPath"),
            "start_time_iso": start,
            "end_time_iso": end,
            "wall_seconds": (row["updatedAt"] - row["createdAt"]) // 1000
            if isinstance(row.get("updatedAt"), int) and isinstance(row.get("createdAt"), int) else None,
            "name": row.get("name"),
            "status": row.get("status"),
            "transcript_available": available,
            "transcript_complete": complete,
            "transcript_store": store,
            "bubble_headers": info["headers"] if info else None,
            "bubbles_present": have if info else None,
            "observed_assistant_turns": stats["assistant"] if use_bubbles else (sum(1 for r, _ in idx if r == "assistant") or None),
            "observed_user_turns": stats["user"] if use_bubbles else (sum(1 for r, _ in idx if r == "user") or None),
            "observed_tool_calls": stats["tools"] if use_bubbles else None,
            "indexed_text_available": indexed_chars > 0,
            "indexed_text_chars": indexed_chars,
            "parent_assistant_turns": stats["assistant"] if complete else None,
            "parent_user_turns": stats["user"] if complete else None,
            "assistant_turns": stats["assistant"] if complete else None,
            "user_turns": stats["user"] if complete else None,
            "parent_tool_turns": stats["tools"] if complete else None,
            "subagent_count": None,
            "api_calls": None,
            "token_usage": None,
        })
        return out

    def search(self, ref: SessionRef, pattern: str, **opts: object) -> list[SearchHit]:
        flags = re.IGNORECASE
        rx = re.compile(pattern if opts.get("regex") else re.escape(pattern), flags)
        role_filter = opts.get("role")
        ctx = int(opts.get("context", 200))
        info = self._bubbles(ref.session_id)
        items: list[tuple[str, str]] = []
        idx = self._indexed_turns(ref.session_id)
        full = bool(info and info["bubbles"] and info["headers"] and len(info["bubbles"]) >= info["headers"])
        if info and info["bubbles"] and (full or not idx):
            for b in info["bubbles"]:
                role = "user" if b.get("type") == 1 else "assistant"
                parts = [b.get("text") or ""]
                tfd = b.get("toolFormerData")
                if isinstance(tfd, dict) and tfd.get("name"):
                    parts.append(f"[tool:{tfd['name']}] {str(tfd.get('rawArgs') or '')[:400]}")
                items.append((role, "\n".join(p for p in parts if p)))
        else:
            items = idx
        if not items:
            raise ValueError("Cloud-run transcript body is unavailable in the local metadata cache")
        hits = []
        for i, (role, text) in enumerate(items):
            if role_filter and role != role_filter:
                continue
            m = rx.search(text)
            if m:
                hits.append(SearchHit("parent", i, role, text[max(0, m.start() - ctx): m.end() + ctx]))
        return hits


REGISTRY.register(CursorCloudParser())
