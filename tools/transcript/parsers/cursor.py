"""Cursor agent-transcript parser."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from lib.paths import CURSOR_ROOT, cursor_project_hash, guess_project_path_from_hash
from lib.registry import REGISTRY
from lib.resolve import normalize_session_ref
from lib.tools import normalize_counts
from lib.types import NormalizedSession, SearchHit, SessionRef, SessionSummary


def _to_iso_z(epoch: float) -> str:
    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
    ms = int(dt.microsecond / 1000)
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{ms:03d}Z")


def _extract_text_from_content(content: list) -> str:
    parts = []
    for item in content:
        if item.get("type") == "text":
            parts.append(item.get("text", ""))
        elif item.get("type") == "tool_result":
            inner = item.get("content", [])
            if isinstance(inner, list):
                for sub in inner:
                    if sub.get("type") == "text":
                        parts.append(sub.get("text", ""))
            elif isinstance(inner, str):
                parts.append(inner)
    return "\n".join(parts)


def _parse_cursor_timestamp(text: str) -> str | None:
    """Parse `<timestamp>Monday, Sep 14, 2026, 9:51 PM (UTC+10)</timestamp>` to ISO Z."""
    match = re.search(r"<timestamp>(.*?)</timestamp>", text)
    if not match:
        return None
    raw = match.group(1).strip()
    tz_match = re.search(r"\(UTC([+-]\d+)\)\s*$", raw)
    tz_hours = int(tz_match.group(1)) if tz_match else 0
    body = re.sub(r"\s*\(UTC[+-]\d+\)\s*$", "", raw)
    try:
        local = datetime.strptime(body, "%A, %b %d, %Y, %I:%M %p")
    except ValueError:
        return None
    offset = timezone(timedelta(hours=tz_hours))
    utc = local.replace(tzinfo=offset).astimezone(timezone.utc)
    ms = int(utc.microsecond / 1000)
    return utc.strftime(f"%Y-%m-%dT%H:%M:%S.{ms:03d}Z")


def _extract_user_query(text: str) -> str | None:
    match = re.search(r"<user_query>(.*?)</user_query>", text, re.DOTALL)
    if match:
        query = match.group(1).strip()
        if query.startswith("The beginning of the above subagent result"):
            return None
        if query.startswith("Briefly inform the user about the task result"):
            return None
        return query
    if "<manually_attached_skills>" in text:
        after = re.split(r"</manually_attached_skills>", text, maxsplit=1)
        if len(after) > 1:
            query_part = after[1].strip()
            if query_part:
                return query_part[:500]
        return "[skill attachment]"
    stripped = text.strip()
    if len(stripped) < 10:
        return None
    return stripped


class CursorParser:
    name = "cursor"

    def discover(
        self,
        project_path: str | None,
        *,
        match: str | None = None,
        since: str | None = None,
        min_subagents: int | None = None,
    ) -> list[SessionSummary]:
        if not project_path:
            return []
        phash = cursor_project_hash(project_path)
        transcripts_dir = os.path.join(CURSOR_ROOT, phash, "agent-transcripts")
        return self._discover_dir(
            transcripts_dir, project_path, match, since, min_subagents
        )

    def discover_all(
        self,
        *,
        match: str | None = None,
        since: str | None = None,
        min_subagents: int | None = None,
    ) -> list[SessionSummary]:
        results = []
        if not os.path.isdir(CURSOR_ROOT):
            return results
        for proj in os.listdir(CURSOR_ROOT):
            transcripts_dir = os.path.join(CURSOR_ROOT, proj, "agent-transcripts")
            if not os.path.isdir(transcripts_dir):
                continue
            results.extend(
                self._discover_dir(
                    transcripts_dir, None, match, since, min_subagents
                )
            )
        return results

    def _discover_dir(
        self,
        transcripts_dir: str,
        project_path: str,
        match: str | None,
        since: str | None,
        min_subagents: int | None,
    ) -> list[SessionSummary]:
        if not os.path.isdir(transcripts_dir):
            return []
        sessions = []
        for entry in os.scandir(transcripts_dir):
            if not entry.is_dir():
                continue
            session_id = entry.name
            session_dir = entry.path
            parent_jsonl = os.path.join(session_dir, f"{session_id}.jsonl")
            parent_size = (
                os.path.getsize(parent_jsonl) if os.path.isfile(parent_jsonl) else 0
            )
            subagents_dir = os.path.join(session_dir, "subagents")
            sub_count = 0
            all_files = []
            if parent_size:
                all_files.append(parent_jsonl)
            if os.path.isdir(subagents_dir):
                for f in os.listdir(subagents_dir):
                    if f.endswith(".jsonl"):
                        sub_count += 1
                        all_files.append(os.path.join(subagents_dir, f))
            start_mtime = (
                min(os.path.getmtime(f) for f in all_files)
                if all_files
                else os.path.getmtime(session_dir)
            )
            start_iso = _to_iso_z(start_mtime)

            if match:
                hay = f"{session_id} {project_path}".lower()
                if match.lower() not in hay:
                    continue
            if since and start_iso < since:
                continue
            if min_subagents is not None and sub_count < min_subagents:
                continue

            sessions.append(
                SessionSummary(
                    source=self.name,
                    session_id=session_id,
                    external_url=None,
                    project_path=project_path or None,
                    start_time_iso=start_iso,
                    subagent_count=sub_count,
                    bytes=parent_size,
                )
            )
        return sessions

    def resolve(self, session_ref: str, project_path: str | None) -> SessionRef:
        ref = normalize_session_ref(session_ref)

        def resolve_in_dir(transcripts_dir: str, pp: str | None) -> SessionRef | None:
            if not os.path.isdir(transcripts_dir):
                return None
            exact = os.path.join(transcripts_dir, ref)
            if os.path.isdir(exact):
                parent = os.path.join(exact, f"{ref}.jsonl")
                return SessionRef(self.name, ref, pp, parent)
            matches = [
                d
                for d in os.listdir(transcripts_dir)
                if os.path.isdir(os.path.join(transcripts_dir, d)) and d.startswith(ref)
            ]
            if len(matches) == 1:
                sid = matches[0]
                parent = os.path.join(transcripts_dir, sid, f"{sid}.jsonl")
                return SessionRef(self.name, sid, pp, parent)
            if len(matches) > 1:
                raise ValueError(f"Ambiguous prefix {ref}: {matches}")
            return None

        if project_path:
            phash = cursor_project_hash(project_path)
            transcripts_dir = os.path.join(CURSOR_ROOT, phash, "agent-transcripts")
            result = resolve_in_dir(transcripts_dir, project_path)
            if result:
                return result

        all_matches: list[SessionRef] = []
        if os.path.isdir(CURSOR_ROOT):
            for proj in os.listdir(CURSOR_ROOT):
                transcripts_dir = os.path.join(CURSOR_ROOT, proj, "agent-transcripts")
                pp = guess_project_path_from_hash(proj)
                try:
                    r = resolve_in_dir(transcripts_dir, pp)
                    if r:
                        all_matches.append(r)
                except ValueError:
                    raise
        if not all_matches:
            raise FileNotFoundError(f"No session matching {ref}")
        if len(all_matches) > 1:
            raise ValueError(f"Ambiguous prefix {ref}: {[m.session_id for m in all_matches]}")
        return all_matches[0]

    def _parse_parent(self, jsonl_path: str) -> dict:
        tool_counts: Counter[str] = Counter()
        task_calls: list[dict] = []
        user_queries: list[dict] = []
        task_seq = 0

        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for msg_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = msg.get("role", "")
                content = msg.get("message", {}).get("content", [])

                if role == "user":
                    text = _extract_text_from_content(content)
                    query = _extract_user_query(text)
                    if query:
                        user_queries.append(
                            {
                                "ts": _parse_cursor_timestamp(text),
                                "text": query,
                            }
                        )

                elif role == "assistant":
                    for item in content:
                        if item.get("type") != "tool_use":
                            continue
                        name = item.get("name", "")
                        tool_counts[name] += 1
                        if name == "Task":
                            inp = item.get("input", {})
                            task_calls.append(
                                {
                                    "seq": task_seq,
                                    "agent_type": inp.get("subagent_type", ""),
                                    "model": inp.get("model", ""),
                                    "description": inp.get("description", ""),
                                }
                            )
                            task_seq += 1

        return {
            "tool_counts": dict(tool_counts),
            "task_calls": task_calls,
            "user_queries": user_queries,
        }

    def _parse_subagent(self, jsonl_path: str) -> dict:
        tool_counts: Counter[str] = Counter()
        direction_text = ""
        has_task_calls = False

        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = msg.get("role", "")
                content = msg.get("message", {}).get("content", [])

                if role == "user" and not direction_text:
                    direction_text = _extract_text_from_content(content)
                elif role == "assistant":
                    for item in content:
                        if item.get("type") == "tool_use":
                            name = item.get("name", "")
                            tool_counts[name] += 1
                            if name == "Task":
                                has_task_calls = True

        raw = dict(tool_counts)
        return {
            "tool_counts_raw": raw,
            "tool_counts": normalize_counts(raw),
            "total_tool_turns": sum(raw.values()),
            "description": direction_text[:300],
            "has_task_calls": has_task_calls,
        }

    def extract(self, ref: SessionRef) -> NormalizedSession:
        parent_data = self._parse_parent(ref.storage_path)
        raw_counts = parent_data["tool_counts"]
        session_dir = os.path.dirname(ref.storage_path)

        subagents_dir = os.path.join(session_dir, "subagents")
        subagents = []
        all_mtimes = []
        if os.path.isfile(ref.storage_path):
            all_mtimes.append(os.path.getmtime(ref.storage_path))

        if os.path.isdir(subagents_dir):
            entries = []
            for fname in os.listdir(subagents_dir):
                if not fname.endswith(".jsonl"):
                    continue
                fpath = os.path.join(subagents_dir, fname)
                entries.append((fname[:-6], fpath, os.path.getmtime(fpath)))
            entries.sort(key=lambda e: e[2])
            for agent_id, fpath, mtime in entries:
                all_mtimes.append(mtime)
                data = self._parse_subagent(fpath)
                subagents.append(
                    {
                        "id": agent_id,
                        "agent_type": "subagent",
                        "model": "unknown",
                        "tool_counts": data["tool_counts"],
                        "tool_counts_raw": data["tool_counts_raw"],
                        "total_tool_turns": data["total_tool_turns"],
                        "description": data["description"],
                        "has_task_calls": data["has_task_calls"],
                    }
                )

        query_times = [
            q["ts"]
            for q in parent_data["user_queries"]
            if q.get("ts")
        ]
        if query_times:
            start_time_iso = min(query_times)
            end_time_iso = max(query_times)
            start_dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time_iso.replace("Z", "+00:00"))
            wall_seconds = int((end_dt - start_dt).total_seconds())
        else:
            start_time = min(all_mtimes) if all_mtimes else 0
            end_time = max(all_mtimes) if all_mtimes else 0
            wall_seconds = int(end_time - start_time) if all_mtimes else None
            start_time_iso = _to_iso_z(start_time) if all_mtimes else None
            end_time_iso = _to_iso_z(end_time) if all_mtimes else None

        session = {
            "id": ref.session_id,
            "external_url": None,
            "project_path": ref.project_path,
            "start_time_iso": start_time_iso,
            "end_time_iso": end_time_iso,
            "wall_seconds": wall_seconds,
            "parent_tool_counts": normalize_counts(raw_counts),
            "parent_tool_counts_raw": raw_counts,
            "parent_tool_turns": sum(raw_counts.values()),
            "api_calls": None,
            "context_estimate": None,
            "token_usage": None,
            "subagent_count": len(subagents),
        }

        return NormalizedSession(
            source=self.name,
            session=session,
            agent_spawns=parent_data["task_calls"],
            subagents=subagents,
            user_queries=parent_data["user_queries"],
        )

    def search(
        self,
        ref: SessionRef,
        pattern: str,
        **opts: object,
    ) -> list[SearchHit]:
        import re as re_mod

        regex = bool(opts.get("regex"))
        role_filter = opts.get("role")
        context_chars = int(opts.get("context", 200))
        agent_filter = opts.get("agent")

        flags = re_mod.IGNORECASE
        compiled = (
            re_mod.compile(pattern, flags)
            if regex
            else re_mod.compile(re_mod.escape(pattern), flags)
        )

        session_dir = os.path.dirname(ref.storage_path)
        hits: list[SearchHit] = []

        def search_file(path: str, agent_id: str) -> None:
            if not os.path.isfile(path):
                return
            with open(path, encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    role = msg.get("role", "")
                    if role_filter and role != role_filter:
                        continue
                    content = msg.get("message", {}).get("content", [])
                    texts = _content_texts_for_search(content)
                    for text in texts:
                        if compiled.search(text):
                            m = compiled.search(text)
                            start = max(0, m.start() - context_chars // 2)
                            end = min(len(text), m.end() + context_chars // 2)
                            snippet = text[start:end].replace("\n", " ")
                            hits.append(SearchHit(agent_id, idx, role, snippet))
                            break

        if agent_filter:
            if agent_filter == "parent":
                search_file(ref.storage_path, "parent")
            else:
                p = os.path.join(session_dir, "subagents", f"{agent_filter}.jsonl")
                search_file(p, agent_filter)
        else:
            search_file(ref.storage_path, "parent")
            subagents_dir = os.path.join(session_dir, "subagents")
            if os.path.isdir(subagents_dir):
                for fname in sorted(os.listdir(subagents_dir)):
                    if fname.endswith(".jsonl"):
                        search_file(
                            os.path.join(subagents_dir, fname), fname[:-6]
                        )
        return hits


def _content_texts_for_search(content: list) -> list[str]:
    texts = []
    for item in content:
        if item.get("type") == "text":
            texts.append(item.get("text", ""))
        elif item.get("type") == "tool_use":
            inp = item.get("input", {})
            parts = [f"[tool:{item.get('name', '')}]"]
            for k, v in inp.items():
                if isinstance(v, str) and v:
                    parts.append(f"{k}: {v[:400]}")
            texts.append(" ".join(parts))
        elif item.get("type") == "tool_result":
            inner = item.get("content", [])
            if isinstance(inner, list):
                for sub in inner:
                    if sub.get("type") == "text":
                        texts.append(sub.get("text", ""))
            elif isinstance(inner, str):
                texts.append(inner)
    return texts


REGISTRY.register(CursorParser())
