"""API-turn index for a Claude agent JSONL.

The schedule, gold labels, and metrics use ``api_turn`` (TERMS §1).

Coding Harness Manager / maps fixtures count unique ``message.id`` on
``type=assistant`` rows. Subagent files mark every row ``isSidechain: true``;
those rows are the worker, so they count. A parent transcript that mixes
main-thread and sidechain rows still drops sidechain assistants, matching
``post_tool_batch_signal.py``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SHORT_ID = re.compile(r"([0-9a-f]{12})$")
_READ_TOOLS = {"Read", "read"}
_PATH_KEYS = ("file_path", "path", "filePath", "notebook_path")


def checkpoints(first_at: int, interval: int, T: int) -> list[int]:
    """Turns ``first_at + k * interval`` that are ``<= T``. Empty if ``T < first_at``."""
    if first_at <= 0 or interval <= 0:
        raise ValueError("first_at and interval must be positive")
    out: list[int] = []
    turn = first_at
    while turn <= T:
        out.append(turn)
        turn += interval
    return out


def parse_schedule(text: str) -> tuple[int, int]:
    """Parse ``75:15`` into ``(first_at, interval)``."""
    parts = text.split(":")
    if len(parts) != 2:
        raise ValueError(f"schedule must be first_at:interval, got {text!r}")
    return int(parts[0]), int(parts[1])


def worker_id_from_path(path: Path) -> str:
    """Fixture stem, or the trailing 12-hex id inside ``agent-….jsonl``."""
    match = _SHORT_ID.search(path.stem)
    if match:
        return match.group(1)
    return path.stem


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _context_tokens(usage: Any) -> int | None:
    """Prompt-side context: input + cache read + cache creation.

    Maps fixtures publish this sum (``92a48e004519`` peak 129961). The max of
    the three buckets alone under-counts that worker.
    """
    if not isinstance(usage, dict):
        return None
    keys = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    if not any(key in usage for key in keys):
        return None
    total = 0
    for key in keys:
        raw = usage.get(key) or 0
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            continue
        total += int(raw)
    return total


def _visible_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    return "\n".join(part for part in parts if part)


def _usable_path(value: str) -> bool:
    text = value.strip()
    if not text or text == "[REDACTED]" or text.startswith("[REDACTED]"):
        return False
    return True


def _read_path(payload: Any, tool_name: str) -> str | None:
    if tool_name not in _READ_TOOLS or not isinstance(payload, dict):
        return None
    for key in _PATH_KEYS:
        raw = payload.get(key)
        if isinstance(raw, str) and _usable_path(raw):
            return raw.strip()
    return None


def is_compaction_row(row: dict[str, Any]) -> bool:
    subtype = row.get("subtype")
    if isinstance(subtype, str) and "compact" in subtype.lower():
        return True
    if row.get("isCompactSummary") or row.get("compactMetadata"):
        return True
    row_type = str(row.get("type") or "").lower()
    if row_type in {"compact", "compaction"}:
        return True
    if row_type != "system" and "compact" not in row_type:
        return False
    content = row.get("content")
    if isinstance(content, str):
        blob = content
    else:
        blob = _visible_text(content)
    stripped = blob.strip()
    if not stripped or stripped == "[REDACTED]" or stripped.startswith("[REDACTED]"):
        return False
    return "compact" in stripped.lower()


@dataclass
class AssistantTurn:
    number: int
    message_id: str | None
    text_parts: list[str] = field(default_factory=list)
    tool_names: list[str] = field(default_factory=list)
    read_paths: list[str] = field(default_factory=list)
    context_tokens: int | None = None
    _tool_ids: set[str] = field(default_factory=set)

    def absorb(self, row: dict[str, Any]) -> None:
        message = row.get("message") if isinstance(row.get("message"), dict) else {}
        content = message.get("content")
        text = _visible_text(content)
        if text:
            self.text_parts.append(text)
        ctx = _context_tokens(message.get("usage"))
        if ctx is not None:
            self.context_tokens = ctx if self.context_tokens is None else max(self.context_tokens, ctx)
        blocks = content if isinstance(content, list) else []
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = str(block.get("name") or "unknown")
            raw_id = block.get("id")
            tid = raw_id if isinstance(raw_id, str) and raw_id else None
            if tid is not None and tid in self._tool_ids:
                continue
            if tid is not None:
                self._tool_ids.add(tid)
            self.tool_names.append(name)
            path = _read_path(block.get("input"), name)
            if path:
                self.read_paths.append(path)

    @property
    def text(self) -> str:
        return "\n".join(self.text_parts)

    @property
    def has_tool(self) -> bool:
        return bool(self.tool_names)


@dataclass
class IndexedTranscript:
    path: str
    worker_id: str
    rows: list[dict[str, Any]]
    row_bytes: list[int]
    turns: list[AssistantTurn]
    row_turn: list[int | None]
    sidechain_mode: str
    agent_id: str | None = None

    @property
    def T(self) -> int:
        return len(self.turns)

    def prefix_indexes(self, checkpoint: int) -> list[int]:
        """Rows in ``prefix(c)``: turns ``1..c`` plus non-turn rows before turn ``c+1``."""
        if checkpoint < 1:
            return []
        first_next: int | None = None
        for index, turn_no in enumerate(self.row_turn):
            if turn_no == checkpoint + 1:
                first_next = index
                break
        chosen: list[int] = []
        for index, turn_no in enumerate(self.row_turn):
            if turn_no is not None and turn_no <= checkpoint:
                chosen.append(index)
            elif turn_no is None and (first_next is None or index < first_next):
                chosen.append(index)
        return chosen


def _sidechain_mode(rows: list[dict[str, Any]]) -> str:
    flags: list[bool] = []
    for row in rows:
        if row.get("type") == "assistant":
            flags.append(bool(row.get("isSidechain")))
    if not flags:
        return "unmarked"
    if all(flags):
        return "subagent_file"
    if any(flags):
        return "parent_exclude_sidechain"
    return "unmarked"


def _counts_as_turn(row: dict[str, Any], mode: str) -> bool:
    if row.get("type") != "assistant":
        return False
    if mode == "parent_exclude_sidechain" and row.get("isSidechain"):
        return False
    return True


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    sizes: list[int] = []
    with path.open("rb") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
                sizes.append(len(raw))
    return rows, sizes


def index_rows(
    rows: list[dict[str, Any]],
    row_bytes: list[int] | None = None,
    *,
    path: str = "",
    worker_id: str = "",
) -> IndexedTranscript:
    sizes = row_bytes if row_bytes is not None else [0] * len(rows)
    mode = _sidechain_mode(rows)
    turns: list[AssistantTurn] = []
    by_id: dict[str, AssistantTurn] = {}
    row_turn: list[int | None] = []
    agent_id: str | None = None
    for row in rows:
        if agent_id is None and isinstance(row.get("agentId"), str):
            agent_id = row["agentId"]
        if not _counts_as_turn(row, mode):
            row_turn.append(None)
            continue
        message = row.get("message") if isinstance(row.get("message"), dict) else {}
        message_id = message.get("id")
        mid = message_id if isinstance(message_id, str) and message_id else None
        if mid is not None and mid in by_id:
            turn = by_id[mid]
            turn.absorb(row)
            row_turn.append(turn.number)
            continue
        turn = AssistantTurn(number=len(turns) + 1, message_id=mid)
        turn.absorb(row)
        turns.append(turn)
        if mid is not None:
            by_id[mid] = turn
        row_turn.append(turn.number)
    return IndexedTranscript(
        path=path,
        worker_id=worker_id,
        rows=rows,
        row_bytes=sizes,
        turns=turns,
        row_turn=row_turn,
        sidechain_mode=mode,
        agent_id=agent_id,
    )


def index_transcript(path: Path, *, worker_id: str | None = None) -> IndexedTranscript:
    rows, sizes = load_jsonl(path)
    return index_rows(
        rows,
        sizes,
        path=str(path),
        worker_id=worker_id or worker_id_from_path(path),
    )


def first_user_text(indexed: IndexedTranscript, indexes: list[int]) -> str | None:
    """First user text in the prefix. Tool-result-only user rows are skipped."""
    for index in indexes:
        row = indexed.rows[index]
        if row.get("type") != "user":
            continue
        message = row.get("message") if isinstance(row.get("message"), dict) else {}
        text = _visible_text(message.get("content"))
        if text.strip():
            return text
    return None
