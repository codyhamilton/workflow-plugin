"""Claude Code / opencode transcript parser."""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

from lib.paths import CLAUDE_ROOT, claude_project_hash, guess_project_path_from_hash
from lib.registry import REGISTRY
from lib.resolve import (
    BRIDGE_ID_RE,
    SESSION_SLUG_RE,
    extract_url_slug,
    normalize_session_ref,
    scan_claude_sessions_for_bridge,
    scan_claude_sessions_for_slug,
)
from lib.tools import canonical_name, normalize_counts
from lib.types import NormalizedSession, SearchHit, SessionRef, SessionSummary
from lib.usage import context_estimate_from_messages, dedupe_usage, merge_usage

SKIP_TYPES = {
    "mode",
    "permission-mode",
    "bridge-session",
    "file-history-snapshot",
    "atis-latch",
    "attachment",
}


def _parse_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [json.loads(line) for line in f if line.strip()]


def _to_iso_z(ts: str | None) -> str | None:
    if not ts:
        return None
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    ms = int(dt.microsecond / 1000)
    return dt.astimezone(timezone.utc).strftime(f"%Y-%m-%dT%H:%M:%S.{ms:03d}Z")


def _count_tools(messages: list[dict], is_parent: bool = True) -> Counter[str]:
    counts: Counter[str] = Counter()
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        if is_parent and msg.get("isSidechain"):
            continue
        for item in msg.get("message", {}).get("content", []):
            if isinstance(item, dict) and item.get("type") == "tool_use":
                counts[item.get("name", "unknown")] += 1
    return counts


def _extract_external_url(messages: list[dict]) -> str | None:
    for msg in messages:
        if msg.get("type") == "system" and msg.get("url"):
            return msg["url"]
        att = msg.get("attachment", {})
        if isinstance(att, dict) and att.get("url"):
            url = att["url"]
            if "claude.ai" in url:
                return url
        content = msg.get("content", "")
        if isinstance(content, str):
            slug = extract_url_slug(content)
            if slug:
                return f"https://claude.ai/code/{slug}"
    return None


def _extract_user_queries(messages: list[dict]) -> list[dict]:
    queries = []
    for msg in messages:
        if msg.get("type") != "user":
            continue
        if msg.get("isSidechain"):
            continue
        ts = _to_iso_z(msg.get("timestamp"))
        content = msg.get("message", {}).get("content", [])
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        text = "\n".join(text_parts).strip()
        if text:
            queries.append({"ts": ts, "text": text[:2000]})
    return queries


def _extract_agent_spawns(messages: list[dict]) -> list[dict]:
    spawns = []
    seq = 0
    for msg in messages:
        if msg.get("type") != "assistant" or msg.get("isSidechain"):
            continue
        for item in msg.get("message", {}).get("content", []):
            if not (isinstance(item, dict) and item.get("type") == "tool_use"):
                continue
            if item.get("name") not in ("Agent",):
                continue
            inp = item.get("input", {})
            spawns.append(
                {
                    "seq": seq,
                    "agent_type": inp.get("subagent_type", inp.get("agent_type", "")),
                    "model": inp.get("model", ""),
                    "description": inp.get("description", ""),
                }
            )
            seq += 1
    return spawns


def _filter_session_messages(messages: list[dict]) -> list[dict]:
    return [m for m in messages if m.get("type") not in SKIP_TYPES]


class ClaudeParser:
    name = "claude-code"

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
        phash = claude_project_hash(project_path)
        proj_dir = os.path.join(CLAUDE_ROOT, phash)
        return self._discover_dir(proj_dir, project_path, match, since, min_subagents)

    def discover_all(
        self,
        *,
        match: str | None = None,
        since: str | None = None,
        min_subagents: int | None = None,
    ) -> list[SessionSummary]:
        results = []
        if not os.path.isdir(CLAUDE_ROOT):
            return results
        for proj in os.listdir(CLAUDE_ROOT):
            proj_dir = os.path.join(CLAUDE_ROOT, proj)
            if not os.path.isdir(proj_dir):
                continue
            results.extend(
                self._discover_dir(proj_dir, None, match, since, min_subagents)
            )
        return results

    def _discover_dir(
        self,
        proj_dir: str,
        project_path: str,
        match: str | None,
        since: str | None,
        min_subagents: int | None,
    ) -> list[SessionSummary]:
        if not os.path.isdir(proj_dir):
            return []
        sessions = []
        for fname in os.listdir(proj_dir):
            if not fname.endswith(".jsonl"):
                continue
            session_id = fname[:-6]
            path = os.path.join(proj_dir, fname)
            size = os.path.getsize(path)
            sub_dir = os.path.join(proj_dir, session_id, "subagents")
            sub_count = (
                len(glob.glob(os.path.join(sub_dir, "*.meta.json")))
                if os.path.isdir(sub_dir)
                else 0
            )
            try:
                msgs = _parse_jsonl(path)
            except (json.JSONDecodeError, OSError):
                continue
            timestamps = [
                m["timestamp"]
                for m in msgs
                if "timestamp" in m and m.get("type") in ("user", "assistant")
            ]
            start = min(timestamps) if timestamps else None
            start_iso = _to_iso_z(start) or ""
            external_url = _extract_external_url(msgs)
            resolved_path = project_path
            if not resolved_path:
                for m in msgs:
                    cwd = m.get("cwd")
                    if cwd:
                        resolved_path = cwd
                        break

            if match:
                hay = f"{session_id} {resolved_path} {external_url or ''}".lower()
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
                    external_url=external_url,
                    project_path=resolved_path or None,
                    start_time_iso=start_iso,
                    subagent_count=sub_count,
                    bytes=size,
                )
            )
        return sessions

    def resolve(self, session_ref: str, project_path: str | None) -> SessionRef:
        ref = normalize_session_ref(session_ref)

        if SESSION_SLUG_RE.match(ref):
            matches = scan_claude_sessions_for_slug(CLAUDE_ROOT, ref)
            if not matches:
                raise FileNotFoundError(f"No session for slug {ref}")
            if len(matches) > 1 and project_path:
                phash = claude_project_hash(project_path)
                filtered = [
                    (sid, p)
                    for sid, p in matches
                    if phash in p
                ]
                if len(filtered) == 1:
                    matches = filtered
            if len(matches) > 1:
                raise ValueError(f"Ambiguous slug {ref}: {[m[0] for m in matches]}")
            session_id, path = matches[0]
            return SessionRef(self.name, session_id, project_path, path)

        if BRIDGE_ID_RE.match(ref):
            matches = scan_claude_sessions_for_bridge(CLAUDE_ROOT, ref)
            if not matches:
                raise FileNotFoundError(f"No session for bridge {ref}")
            if len(matches) > 1:
                raise ValueError(f"Ambiguous bridge {ref}: {[m[0] for m in matches]}")
            session_id, path = matches[0]
            return SessionRef(self.name, session_id, project_path, path)

        if project_path:
            phash = claude_project_hash(project_path)
            proj_dir = os.path.join(CLAUDE_ROOT, phash)
            exact = os.path.join(proj_dir, f"{ref}.jsonl")
            if os.path.isfile(exact):
                return SessionRef(self.name, ref, project_path, exact)
            if os.path.isdir(proj_dir):
                matches = [
                    f[:-6]
                    for f in os.listdir(proj_dir)
                    if f.endswith(".jsonl") and f.startswith(ref)
                ]
                if len(matches) == 1:
                    sid = matches[0]
                    return SessionRef(
                        self.name, sid, project_path, os.path.join(proj_dir, f"{sid}.jsonl")
                    )
                if len(matches) > 1:
                    raise ValueError(f"Ambiguous prefix {ref}: {matches}")

        # Global prefix search
        all_matches: list[tuple[str, str, str | None]] = []
        if os.path.isdir(CLAUDE_ROOT):
            for proj in os.listdir(CLAUDE_ROOT):
                proj_dir = os.path.join(CLAUDE_ROOT, proj)
                for fname in os.listdir(proj_dir):
                    if fname.endswith(".jsonl") and fname.startswith(ref):
                        sid = fname[:-6]
                        pp = guess_project_path_from_hash(proj)
                        all_matches.append(
                            (sid, os.path.join(proj_dir, fname), pp)
                        )
        if not all_matches:
            raise FileNotFoundError(f"No session matching {ref}")
        if len(all_matches) > 1:
            raise ValueError(f"Ambiguous prefix {ref}: {[m[0] for m in all_matches]}")
        sid, path, pp = all_matches[0]
        return SessionRef(self.name, sid, pp, path)

    def extract(self, ref: SessionRef) -> NormalizedSession:
        parent_msgs = _filter_session_messages(_parse_jsonl(ref.storage_path))
        raw_counts = dict(_count_tools(parent_msgs))
        canon_counts = normalize_counts(raw_counts)

        timestamps = [
            m["timestamp"]
            for m in parent_msgs
            if "timestamp" in m and m.get("type") in ("user", "assistant")
        ]
        first_ts = _to_iso_z(min(timestamps) if timestamps else None)
        last_ts = _to_iso_z(max(timestamps) if timestamps else None)
        wall_seconds = None
        if timestamps:
            dt0 = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
            dt1 = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00"))
            wall_seconds = int((dt1 - dt0).total_seconds())

        parent_api_calls, parent_token_usage = dedupe_usage(parent_msgs)
        context_est = context_estimate_from_messages(parent_msgs)
        external_url = _extract_external_url(parent_msgs)
        agent_spawns = _extract_agent_spawns(parent_msgs)
        user_queries = _extract_user_queries(parent_msgs)

        # Resolve project path from cwd in messages if missing
        project_path = ref.project_path
        if not project_path:
            for m in parent_msgs:
                cwd = m.get("cwd")
                if cwd:
                    project_path = cwd
                    break

        session_dir = os.path.dirname(ref.storage_path)
        subagent_dir = os.path.join(session_dir, ref.session_id, "subagents")
        subagents = []
        if os.path.isdir(subagent_dir):
            for meta_file in sorted(glob.glob(os.path.join(subagent_dir, "*.meta.json"))):
                with open(meta_file, encoding="utf-8") as f:
                    meta = json.load(f)
                agent_id = os.path.basename(meta_file).replace(".meta.json", "")
                jsonl_path = os.path.join(subagent_dir, f"{agent_id}.jsonl")
                sub_msgs = (
                    _filter_session_messages(_parse_jsonl(jsonl_path))
                    if os.path.exists(jsonl_path)
                    else []
                )
                sub_model = None
                for m in sub_msgs:
                    sub_model = m.get("message", {}).get("model")
                    if sub_model:
                        break
                sub_raw = dict(_count_tools(sub_msgs, is_parent=False))
                sub_api_calls, sub_token_usage = dedupe_usage(sub_msgs)
                subagents.append(
                    {
                        "id": agent_id,
                        "agent_type": meta.get("agentType", "unknown"),
                        "model": sub_model or "unknown",
                        "tool_counts": normalize_counts(sub_raw),
                        "tool_counts_raw": sub_raw,
                        "total_tool_turns": sum(sub_raw.values()),
                        "api_calls": sub_api_calls,
                        "token_usage": sub_token_usage,
                        "description": meta.get("description", ""),
                    }
                )

        subagent_api_calls = sum(sa["api_calls"] for sa in subagents)
        subagent_token_usage = merge_usage(
            *(sa["token_usage"] for sa in subagents)
        )

        session = {
            "id": ref.session_id,
            "external_url": external_url,
            "project_path": project_path,
            "start_time_iso": first_ts,
            "end_time_iso": last_ts,
            "wall_seconds": wall_seconds,
            "parent_tool_counts": canon_counts,
            "parent_tool_counts_raw": raw_counts,
            "parent_tool_turns": sum(raw_counts.values()),
            "parent_api_calls": parent_api_calls,
            "parent_token_usage": parent_token_usage,
            "subagent_api_calls": subagent_api_calls,
            "subagent_token_usage": subagent_token_usage,
            "api_calls": parent_api_calls + subagent_api_calls,
            "context_estimate": context_est,
            "token_usage": merge_usage(parent_token_usage, subagent_token_usage),
            "subagent_count": len(subagents),
        }

        return NormalizedSession(
            source=self.name,
            session=session,
            agent_spawns=agent_spawns,
            subagents=subagents,
            user_queries=user_queries,
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

        hits: list[SearchHit] = []
        session_dir = os.path.dirname(ref.storage_path)
        subagent_dir = os.path.join(session_dir, ref.session_id, "subagents")

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
                    if msg.get("type") in SKIP_TYPES:
                        continue
                    role = msg.get("role") or msg.get("type", "")
                    if role_filter and role != role_filter:
                        continue
                    texts = _message_texts(msg)
                    for text in texts:
                        if compiled.search(text):
                            snippet = _snippet(text, compiled, context_chars)
                            hits.append(
                                SearchHit(agent_id, idx, role, snippet)
                            )
                            break

        if agent_filter:
            if agent_filter == "parent":
                search_file(ref.storage_path, "parent")
            else:
                p = os.path.join(subagent_dir, f"{agent_filter}.jsonl")
                search_file(p, agent_filter)
        else:
            search_file(ref.storage_path, "parent")
            if os.path.isdir(subagent_dir):
                for fname in sorted(os.listdir(subagent_dir)):
                    if fname.endswith(".jsonl"):
                        search_file(
                            os.path.join(subagent_dir, fname), fname[:-6]
                        )
        return hits


def _message_texts(msg: dict) -> list[str]:
    texts = []
    content = msg.get("message", {}).get("content", [])
    if isinstance(content, str):
        texts.append(content)
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif item.get("type") == "tool_use":
                    inp = item.get("input", {})
                    parts = [f"[tool:{item.get('name', '')}]"]
                    for k, v in inp.items():
                        if isinstance(v, str) and v:
                            parts.append(f"{k}: {v[:400]}")
                    texts.append(" ".join(parts))
    if msg.get("type") == "user" and not texts:
        c = msg.get("message", {}).get("content")
        if isinstance(c, str):
            texts.append(c)
    return texts


def _snippet(text: str, pattern: re.Pattern, context_chars: int) -> str:
    m = pattern.search(text)
    if not m:
        return ""
    start = max(0, m.start() - context_chars // 2)
    end = min(len(text), m.end() + context_chars // 2)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet.replace("\n", " ")


REGISTRY.register(ClaudeParser(), "claude")
