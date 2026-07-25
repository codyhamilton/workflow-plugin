# Design: Conversation Indexer

This document reifies the contracts that the three child plans must obey. It is the authoritative reference for the schema, the parser interface, the library types, the indexer behavior, the CLI surface, and the test strategy. Each child PLAN.md can reference these contracts rather than restate them.

## Identity Model

A session is uniquely identified by `(tool, session_id)`.

`tool` is one of `'opencode'`, `'claude-code'`, `'cursor'`, `'copilot'`, `'codex'`. v1 ships `'opencode'`, `'claude-code'`, and `'cursor'`.

`session_id` is the tool-native session UUID (or equivalent opaque identifier). It is opaque to the indexer; the indexer never derives or transforms it.

`project_hash` (derived from `cwd.replace('/', '-')`) is **not** an identity key. It is a metadata field that aids discovery. Two sessions with the same `project_hash` may exist; one session may move between paths and keep its identity. The `projects` table maps human-meaningful labels to one or more sessions.

## Timestamp Format

All timestamp columns store ISO 8601 UTC strings with a trailing `Z` and exactly 3 decimal digits of millisecond precision (zero-padded). Example: `2026-01-15T10:30:00.123Z`. The indexer normalizes tool-native timestamps (which may have offsets or subsecond precision) to this form on parse. Comparing timestamps is lexicographic, which is correct for this format ONLY when all timestamps use the same subsecond width. The 3-digit fixed width guarantees correct string ordering across all precision levels.

## Tool-Name Canonicalization

Each tool reports tool names in its own convention. The indexer stores both raw and canonical names:

- `tool_name_raw`: the exact string the source emitted (`'Bash'`, `'Read'`, `'read_file'`, `'run_command'`).
- `tool_name_canonical`: a small enum: `Bash`, `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Agent`, `WebFetch`, `TodoWrite`, `Other`.

The mapping is implemented in a shared module-level function `conv_index/normalize.normalize_tool_name(raw_tool_name: str, tool: str) -> str`. Each parser calls this function rather than maintaining its own mapping. The function is registered in `normalize.py` with per-tool overrides. New tools add to the mapping; they do not invent new canonical names without updating the enum.

The enum is closed for v1. Adding a canonical name is a schema migration.

`tool_name_raw` is always stored, even when `tool_name_canonical` is recognized, to support debugging and future mapping changes. When `normalize_tool_name` returns `Other` (unknown tool), `tool_name_raw` is preserved exactly as the source emitted it.

## Schema (v1)

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now') || 'Z');

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    canonical_path TEXT,
    git_remote TEXT
);

CREATE TABLE sessions (
    tool TEXT NOT NULL,
    id TEXT NOT NULL,
    started_at TEXT NOT NULL,                       -- ISO 8601 UTC, e.g. '2026-01-15T10:30:00Z'
    ended_at TEXT,                                  -- ISO 8601 UTC
    wall_time_sec INTEGER,
    active_time_sec INTEGER,
    peak_context_tokens INTEGER,
    git_branch TEXT,
    cwd TEXT,
    raw_path TEXT NOT NULL,
    parse_status TEXT NOT NULL DEFAULT 'success' CHECK (parse_status IN ('success', 'partial', 'failed', 'live')),
    parse_errors TEXT,                              -- JSON array of {line, error}
    indexed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now') || 'Z'),
    parser_version TEXT,                            -- version of conv_index that parsed this session
    PRIMARY KEY (tool, id)
);

CREATE TABLE session_projects (
    tool TEXT NOT NULL,
    session_id TEXT NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    PRIMARY KEY (tool, session_id, project_id),
    FOREIGN KEY (tool, session_id) REFERENCES sessions(tool, id)
);

CREATE TABLE agents (
    tool TEXT NOT NULL,
    id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    parent_agent_id TEXT,                           -- null for parent
    type TEXT,                                      -- 'parent' | 'explore' | 'general' | ...
    model TEXT,
    description TEXT,
    started_at TEXT,                                -- ISO 8601 UTC
    ended_at TEXT,                                  -- ISO 8601 UTC
    wall_time_sec INTEGER,
    total_turns INTEGER NOT NULL DEFAULT 0 CHECK (total_turns >= 0),
    PRIMARY KEY (tool, id),
    FOREIGN KEY (tool, parent_agent_id) REFERENCES agents(tool, id),
    FOREIGN KEY (tool, session_id) REFERENCES sessions(tool, id)
);

CREATE TABLE tool_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    message_index INTEGER NOT NULL,                 -- links to token_usage.message_index for the assistant message
    tool_name_raw TEXT NOT NULL,
    tool_name_canonical TEXT NOT NULL CHECK (tool_name_canonical IN ('Bash', 'Read', 'Edit', 'Write', 'Glob', 'Grep', 'Agent', 'WebFetch', 'TodoWrite', 'Other')),
    delegates_to_agent_id TEXT,                     -- parent to subagent edge
    timestamp TEXT NOT NULL,                        -- ISO 8601 UTC
    duration_ms INTEGER,
    success INTEGER NOT NULL DEFAULT 1 CHECK (success IN (0, 1)),
    error TEXT CHECK (length(error) <= 4096),
    FOREIGN KEY (tool, agent_id) REFERENCES agents(tool, id),
    FOREIGN KEY (tool, session_id) REFERENCES sessions(tool, id),
    FOREIGN KEY (tool, delegates_to_agent_id) REFERENCES agents(tool, id)
);

CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    message_index INTEGER NOT NULL,                 -- index within agent
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read INTEGER NOT NULL DEFAULT 0,
    cache_creation INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT                                  -- ISO 8601 UTC
    FOREIGN KEY (tool, agent_id) REFERENCES agents(tool, id),
    FOREIGN KEY (tool, session_id) REFERENCES sessions(tool, id)
);

CREATE TABLE compaction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT,                                  -- null for parent compact
    occurred_at TEXT NOT NULL,                      -- ISO 8601 UTC
    pre_compact_tokens INTEGER,
    post_compact_tokens INTEGER,
    FOREIGN KEY (tool, agent_id) REFERENCES agents(tool, id),
    FOREIGN KEY (tool, session_id) REFERENCES sessions(tool, id)
);

CREATE TABLE index_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,                       -- ISO 8601 UTC
    ended_at TEXT,                                  -- ISO 8601 UTC
    tool TEXT,                                      -- null for cross-tool runs
    sessions_seen INTEGER,
    sessions_indexed INTEGER,
    sessions_errored INTEGER,
    sessions_skipped INTEGER,                       -- sessions deferred by Session Completeness rule
    error_log TEXT                                  -- JSON
);

CREATE INDEX idx_tool_turns_session ON tool_turns(tool, session_id);
CREATE INDEX idx_tool_turns_agent ON tool_turns(tool, agent_id);
CREATE INDEX idx_tool_turns_timestamp ON tool_turns(timestamp);
CREATE INDEX idx_tool_turns_canonical ON tool_turns(tool_name_canonical);
CREATE INDEX idx_token_usage_session ON token_usage(tool, session_id);
CREATE INDEX idx_agents_session ON agents(tool, session_id);
CREATE INDEX idx_sessions_started_at ON sessions(started_at);
CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_model ON agents(model);
CREATE INDEX idx_session_projects_project ON session_projects(project_id);
```

The v1 schema is bootstrapped by `Indexer._init_schema()` using hardcoded DDL rather than a migration file. The first migration `001_initial.sql` contains the same DDL and is applied by the migration runner during first-run upgrades from a schema-less DB. After bootstrap, `schema_version` is inserted with `version=1` inside the same transaction. Subsequent schema changes go in numbered migration files.

The indexer connection runs `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;` on init. The DB file is created with mode 0600 and the parent directory with mode 0700.

## Session Completeness

A session is considered "complete enough to index" in v1 when its source file's mtime is older than the wall-clock time of the indexer run minus a configurable grace period (default: 5 minutes). Two cases:

- **Never-before-seen session**: if the mtime is within the grace period, the session is skipped entirely (no row created) and counted in `index_runs.sessions_skipped`.
- **Previously-indexed session**: if the mtime is within the grace period, the existing row's `parse_status` is updated to `'live'` and the session data (agents, turns, tokens) is kept intact from the previous parse.

A later run whose mtime falls outside the grace period will re-index the session normally (setting `parse_status` to `'success'`, `'partial'`, or `'failed'` as appropriate).

The v1 rule is mtime-based and conservative: it errs on the side of not indexing sessions that are still being written. A more accurate rule (tracking the most recent assistant message timestamp) is v2.

The grace period absorbs the case where the tool wrote a row, then updated mtime, but the user is mid-conversation.

## Parser Interface

```python
# conv_index/parsers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator


@dataclass
class TurnRecord:
    tool_name_raw: str
    tool_name_canonical: str       # one of the enum values
    timestamp: datetime
    duration_ms: int | None
    success: bool
    error: str | None
    delegates_to_agent_id: str | None  # populated post-parse from agent map
    message_index: int | None


@dataclass
class AgentRecord:
    id: str
    parent_agent_id: str | None
    type: str
    model: str | None
    description: str
    session_id: str
    started_at: datetime | None
    ended_at: datetime | None
    wall_time_sec: int | None
    total_turns: int = 0
    turns: list[TurnRecord] = field(default_factory=list)
    token_usage: list['TokenUsageRecord'] = field(default_factory=list)


@dataclass
class TokenUsageRecord:
    message_index: int
    input_tokens: int
    output_tokens: int
    cache_read: int
    cache_creation: int
    timestamp: datetime | None


@dataclass
class CompactionEvent:
    occurred_at: datetime
    pre_compact_tokens: int | None
    post_compact_tokens: int | None
    agent_id: str | None


@dataclass
class SessionRecord:
    id: str
    tool: str
    started_at: datetime
    ended_at: datetime | None
    git_branch: str | None
    cwd: str | None
    raw_path: str
    wall_time_sec: int | None
    active_time_sec: int | None
    peak_context_tokens: int | None
    parse_status: str = 'success'
    parser_version: str = ''
    agents: list[AgentRecord]
    compactions: list[CompactionEvent] = field(default_factory=list)
    parse_errors: list[dict] = field(default_factory=list)  # list of {"line": int, "error": str}


class BaseParser(ABC):
    def __init__(self, threshold: float = 0.1):
        """Initialize parser with configurable malformed-row threshold.
        
        threshold: fraction of malformed source rows above which the session
        is marked parse_status='failed' (default 0.1 = 10%).
        """
        self.threshold = threshold

    @abstractmethod
    def discover_sessions(self, project_path: str) -> list[str]:
        """Return session IDs (and their raw paths via get_raw_path) for a project."""

    @abstractmethod
    def get_raw_path(self, project_path: str, session_id: str) -> str:
        """Resolve the on-disk path of a session's source file(s)."""

    @abstractmethod
    def parse_session(self, raw_path: str, session_id: str) -> SessionRecord:
        """Parse a single session's source into a SessionRecord.

        Implementations must:
        - Be tolerant of malformed rows: append to parse_errors and continue.
        - Set parse_status based on error count: 'failed' if more than 10% of
          source rows are malformed, 'partial' if 1-10%, otherwise 'success'.
          The threshold is configurable via a parser constructor argument.
        - Set delegates_to_agent_id on TurnRecord by resolving subagent IDs.
        - Populate token_usage on each AgentRecord from assistant messages.
        - Populate compactions on the SessionRecord from compact boundaries.
        - Compute wall_time_sec from the gap between the first and last event
          timestamps in the session.
        - Compute active_time_sec from the sum of gaps between consecutive
          same-agent events, capped at 60s gaps to skip idle time.
         - Compute active_time_sec as 0 when an agent has 0 or 1 events (no consecutive pairs to sum).
         - Compute peak_context_tokens as MAX(input_tokens + cache_read +
          cache_creation) over all TokenUsageRecord rows in the session.
        - Return a parser_version string identifying the conv_index release
          that produced the SessionRecord.
        """
```

The module-level function `conv_index/normalize.normalize_tool_name(raw_name: str, tool: str) -> str` provides the canonical mapping. Each parser's `parse_session` must call this function to populate `tool_name_canonical` on every `TurnRecord`.

### Opencode / Claude Code Parser

- `discover_sessions(project_path)` walks `~/.claude/projects/{project_hash}/` for `*.jsonl` files.
- `get_raw_path(project_path, session_id)` returns `~/.claude/projects/{project_hash}/{session_id}.jsonl`.
- `parse_session` reads the parent JSONL line-by-line. For each assistant message:
  - If `isSidechain` is true, the message is part of a subagent, emitted under the matching `agent-{id}` from `subagents/agent-{id}.jsonl`.
  - Tool-use blocks become `TurnRecord` rows; the `name` field is `tool_name_raw`; `normalize_tool_name` maps it to `tool_name_canonical`.
  - The `usage` field, when present, becomes a `TokenUsageRecord`.
  - When a tool-use block has `name == 'Agent'`, the subagent ID is resolved from the message's `input.subagent_type` or a sibling `toolUseId` lookup, and `delegates_to_agent_id` is set on the parent turn.
- Compact boundaries: a `compactBoundary: true` row in the JSONL produces a `CompactionEvent`.

### Tool-Format Discriminator

opencode and claude-code share JSONL structure but originate from different binaries. The parser identifies the format by inspecting the first non-empty JSON line: claude-code emits a `sessionId` key at the top level; opencode emits a `sessionID` key (camelCase). If the file is empty or contains no valid JSON lines, the parser falls back to the registry's `tool` argument and logs a warning. When the discriminator cannot determine the tool from the first JSON line, it also falls back to the tool argument.

### Subagent Identification Fallback

When `input.subagent_type` and `toolUseId` are both missing on a sidechain message, the parser logs a `parse_errors` entry naming the orphaned sidechain. The orphaned sidechain's turns are attached to a synthetic agent with `id='orphan-{session_id}-{n}'` where `n` is a deterministic counter assigned by sorting sidechain file names lexicographically before processing. This ensures orphan IDs are stable across re-parses. Orphaned sidechains do not block indexing.

### Cursor Parser

- `discover_sessions(project_path)` walks `~/.cursor/projects/{hash}/agent-transcripts/`.
- `get_raw_path` returns the session directory.
- `parse_session` reads the JSONL files in the directory. Cursor uses `role` / `message.content[].type` (a separate format from opencode); the parser handles this.
- Tool-name normalization is the main divergence: Cursor uses `read_file`, `run_command`, `edit_file`, etc. The mapping goes through `normalize_tool_name` to the canonical enum.
- Cursor does not store subagent transcripts separately. `agents` will be a single parent agent unless the format changes.

### Cursor Token Usage Defaults

Cursor transcripts do not report per-message token usage. The parser populates `TokenUsageRecord` rows with `input_tokens=0`, `output_tokens=0`, `cache_read=0`, `cache_creation=0` for cursor messages. Sessions whose only token data is zero are queryable, but the user can filter `WHERE tool != 'cursor'` for accurate cost data. Cursor sessions still record `tool_turns` rows with the correct `tool_name_canonical` values.

## Library Types

```python
# conv_index/__init__.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Session:
    tool: str
    id: str
    started_at: datetime
    ended_at: datetime | None
    wall_time_sec: int | None
    active_time_sec: int | None
    peak_context_tokens: int | None
    git_branch: str | None
    cwd: str | None
    raw_path: str
    parser_version: str
    parse_status: str
    agents: list['Agent']
    compactions: list[Compaction]


@dataclass
class Agent:
    id: str
    session_id: str
    parent_agent_id: str | None
    type: str | None
    model: str | None
    description: str
    started_at: datetime | None
    ended_at: datetime | None
    wall_time_sec: int | None
    total_turns: int
    turns: list['Turn']
    token_usage: list[TokenUsage]


@dataclass
class Turn:
    tool_name_raw: str
    tool_name_canonical: str
    delegates_to_agent_id: str | None
    message_index: int | None
    timestamp: datetime
    duration_ms: int | None
    success: bool
    error: str | None


@dataclass
class TokenUsage:
    message_index: int
    input_tokens: int
    output_tokens: int
    cache_read: int
    cache_creation: int
    timestamp: datetime | None


@dataclass
class Compaction:
    occurred_at: datetime
    pre_compact_tokens: int | None
    post_compact_tokens: int | None
    agent_id: str | None


@dataclass
class IndexRunReport:
    started_at: datetime
    ended_at: datetime
    tool: str | None
    sessions_seen: int
    sessions_indexed: int
    sessions_errored: int
    sessions_skipped: int
    error_log: list[str]  # one entry per errored session
```

## Indexer Behavior

```python
# conv_index/indexer.py
class Indexer:
    def __init__(self, db_path: str = "~/.conv-index/analytics.db"):
        """
        On init:
        - Set the parent directory of the DB to mode 0700 and the DB file to
          mode 0600 (multi-user host defense).
        - Open a SQLite connection.
        - Run PRAGMA journal_mode=WAL (concurrent readers during writes).
        - Run PRAGMA foreign_keys=ON (FK enforcement).
        - Run PRAGMA busy_timeout=5000 (graceful backoff under contention).
        - NOTE: _init_schema() is called by init() and index_project() after
          the advisory lock is acquired, not in __init__.
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.db_path.parent, 0o700)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute("PRAGMA busy_timeout=5000;")
        # chmod the db file right after opening, before any PRAGMAs write to it
        os.chmod(self.db_path, 0o600)

    def _init_schema(self):
        # Apply pending migrations from conv_index/migrations/.
        # Each migration is wrapped in BEGIN IMMEDIATE; ... COMMIT; so a
        # partial migration does not leave the schema in a mixed state.
        # schema_version is updated within the same transaction so a partial
        # migration is not recorded as applied.
        ...

    def acquire_indexer_lock(self) -> None:
        """
        A single-writer advisory lock file at ~/.conv-index/.lock using POSIX
        fcntl.flock prevents two index_project invocations from running
        concurrently. The second process exits with a non-zero exit code
        (3) and a clear error message including the PID of the holder (if determinable).
        """
        ...

    def release_indexer_lock(self) -> None:
        ...

    def index_project(self, project_path: str, tools: list[str] | None = None) -> IndexRunReport:
        """Index all sessions for a project across the given tools.

        Algorithm:
        1. Acquire the indexer lock; release in a finally block.
        2. Call _init_schema() to apply any pending migrations under the lock.
        3. Open an index_runs row with started_at, run the work, then update
           the row with ended_at, sessions_seen, sessions_indexed,
           sessions_errored, sessions_skipped, and error_log.
        4. For each tool, call parser.discover_sessions(project_path).
        5. For each session_id, check whether a row exists in sessions
           WHERE tool=? AND id=?. If no row exists, or if indexed_at is
           older than the source file mtime, re-parse. Sessions whose mtime
           is within the Session Completeness grace period follow the rules
           in the Session Completeness section.
        6. Parse into SessionRecord; upsert into the database.
        7. If the source file was deleted between discovery and parse:
           - If a previous parse_status='success' row exists, keep old data
             and skip with a warning (do not overwrite with 'failed').
           - Otherwise, set parse_status='failed' on a minimal row and continue.
        8. Track per-session outcome in IndexRunReport.
        """

    def upsert_session(self, record: SessionRecord) -> None:
        """Atomic upsert: write session, replace its agents/turns/tokens/compactions.

        Recompute session-level summary columns (wall_time_sec, active_time_sec, peak_context_tokens) from the new (total_turns is recomputed per agent, not at the session level)
        SessionRecord inside the same transaction. Stale summaries from a
        previous parse are guaranteed overwritten.
        """
        # Use a single transaction. The strategy is "replace on reindex":
        # DELETE FROM agents WHERE tool=? AND session_id=?
        # Delete in child-first order to respect FK enforcement:
        # 1. DELETE FROM token_usage WHERE tool=? AND session_id=?
        # 2. DELETE FROM compaction_events WHERE tool=? AND session_id=?
        # 3. DELETE FROM tool_turns WHERE tool=? AND session_id=?
        # 4. DELETE FROM session_projects WHERE tool=? AND session_id=?
        # 5. DELETE FROM agents WHERE tool=? AND session_id=?
        # Then INSERT the new rows.
        # Then INSERT the new rows.
        ...
```

## CLI Surface (v1)

| Command | Purpose |
|---------|---------|
| `conv-index init` | Create the DB at `~/.conv-index/analytics.db` (mode 0600), enable WAL, enable FK enforcement, apply migrations. |
| `conv-index index <project-path>` | Index all sessions for a project. `--tool X` filters to one tool. |
| `conv-index index --all` | Index all known projects. |
| `conv-index sessions` | List sessions, latest first. `--project LABEL`, `--tool X`, `--since YYYY-MM-DD`, `--limit N` filters. |
| `conv-index session <tool> <id>` | Show structured data for a session. |
| `conv-index stats` | Aggregate statistics. `--group-by tool\|agent_type\|day\|week\|project\|model`. |
| `conv-index tool-usage` | Tool usage frequency, cross-tool. |
| `conv-index projects` | List projects and their session counts. |
| `conv-index project <label>` | Show a project's attached sessions. |
| `conv-index project attach <tool> <id> <label>` | Attach a session to a human-meaningful project label. |
| `conv-index cost-comparison <tool> <id>` | Render the eval-schema section from a session. `--format md\|json`, `--baseline <tool> <id>` for side-by-side. |
| `conv-index history` | Show recent `index_runs` rows. |
| `conv-index doctor` | Report DB health: schema version, WAL mode, FK enforcement, file permissions, lock status. |
| `conv-index reset` | Delete the DB and re-initialize. Requires `--yes` to confirm. |
| `conv-index vacuum` | Run `VACUUM` on the DB to reclaim disk space after large reindexes. |

### Common Flags

- `--format json|table` (default `table`): output format for `sessions`, `stats`, `tool-usage`, `projects`, `project`, `history`. Cost-comparison defaults to `md`.
- `--quiet`: suppress progress messages on stderr.
- `--limit N`: applies to `sessions` (default 100) and `history` (default 20).

### `--since` Format

ISO 8601 date `YYYY-MM-DD`. Sessions whose `started_at` is on or after that date match. No relative formats (e.g., `7d`) in v1.

### `stats --group-by` Values

`tool`, `agent_type`, `day`, `week`, `project`, `model`. The default is `tool`.

### Output Discipline

Data goes to `stdout`. Progress messages and errors go to `stderr`. This enables `conv-index sessions --format json | jq '.[] | .id'`.

### Exit Codes

- 0: success
- 1: command error (bad arguments, missing file, parser exception)
- 2: partial success (some sessions indexed, some errored; details in `error_log`)
- 3: lock contention (another `conv-index index` is running)

### Library API Naming

The library in `conv_index/query.py` exposes functions whose names are the canonical contract: `list_sessions`, `get_session`, `list_projects`, `get_project`, `attach_project`, `stats`, `tool_usage`, `history`, `doctor`. The CLI commands are thin wrappers. The naming `list_*` (not `query_*`) is the standard.

The CLI is a thin wrapper over the library. Each command's logic is a function in `conv_index/query.py` that can be called from Python.

## Migrations

Migrations are SQL files in `conv_index/migrations/`. Naming: `NNN_description.sql`, where `NNN` is a zero-padded monotonic integer.

On `init` (and on every indexer start), the indexer reads the highest applied version from `schema_version` and applies any migrations with a higher number, in order. Each migration is executed in its own `BEGIN IMMEDIATE; ... COMMIT;` transaction so a partial migration does not leave the schema in a mixed state. `schema_version` is updated within the same transaction so a partial migration is not recorded as applied.

Migrations are append-only. A migration is never modified after it is applied. Schema changes go in a new migration.

## Concurrency and Locking

The indexer uses a single-writer advisory lock at `~/.conv-index/.lock` to prevent two `index_project` invocations from corrupting the DB:

- `conv-index index` acquires the lock; the second invocation exits with exit code 3 and a message naming the holder.
- `conv-index sessions`, `conv-index session`, `conv-index stats`, and other read commands do not acquire the lock. They read from the DB via WAL mode and do not block writers.
- `conv-index doctor` reports whether the DB is currently locked and by which process (if determinable).

The lock is `fcntl.flock`-based on POSIX systems. v1 is POSIX-only; Windows support is v2.

## Privacy and Security

The DB at `~/.conv-index/analytics.db` contains metadata about user sessions, including:

- `tool_turns.error` (free text that may include file paths or content fragments)
- `sessions.cwd`, `sessions.raw_path`, `sessions.git_branch` (directory and git context)
- `tool_turns.tool_name_raw` (raw tool name, no arguments)

To minimize leakage on multi-user systems, the indexer:

1. Sets the DB file to mode 0600 and the parent directory to mode 0700 on `init`.
2. Does not include `content` or `arguments` fields from source transcripts in any stored column. Only metadata that aids analytics is stored.
3. The test corpus's `build_fixtures.py` rejects any fixture content that matches `sk-[A-Za-z0-9]{20,}`, `BEGIN PRIVATE KEY`, `ghp_`, or `xoxb-` patterns.
4. Logs a warning (but does not block) when a `tool_turns.error` field exceeds 1KB, as this may indicate accidental content capture.

## Cross-Platform Support

v1 is POSIX-only. Session paths and the indexer lock rely on POSIX semantics:

- `~/.claude/projects/{project_hash}/` and `~/.cursor/projects/{hash}/agent-transcripts/{session}/` are the v1 source paths.
- The advisory lock uses `fcntl.flock` from the stdlib.
- The DB path `~/.conv-index/analytics.db` uses `~` expansion (i.e., `$HOME`).

Windows is explicitly out of scope for v1. Adapting to `%APPDATA%` and replacing `fcntl.flock` with a Windows-equivalent (e.g., `msvcrt.locking`) is a v2 task. The plan should not be considered broken on Windows; the code should fail gracefully on import or `init` with a clear message.

## Test Strategy

### Test Infrastructure

- Each test uses a temporary `analytics.db` (via `tmp_path`) and a temporary project directory containing the fixture. The `tmp_db` fixture in `tests/conftest.py` is a thin wrapper around `tmp_path` that creates a fresh DB and runs migrations.
- A `frozen_time` fixture in `conftest.py` uses `freezegun` to fix wall-clock time during tests that assert on `indexed_at` or `started_at`. This makes `stats --group-by day` deterministic.
- An end-to-end test harness uses `subprocess.run([sys.executable, '-m', 'conv_index.cli', ...])` to invoke the actual `conv-index` binary. This catches packaging, entry-point, and PATH issues that in-process `CliRunner` tests miss.

### Synthetic Fixtures

Fixtures are generated synthetically by `tests/fixtures/build_fixtures.py`. Real session data must never be committed to the test corpus. The generator:

- Rejects any fixture content that matches `sk-[A-Za-z0-9]{20,}`, `BEGIN PRIVATE KEY`, `ghp_`, or `xoxb-` patterns.
- Produces deterministic timestamps derived from a fixed seed.
- Records the source arguments and a hash so accidental edits to fixtures surface as test failures.

### Required Fixture Scenarios

- `tests/fixtures/opencode/session-with-subagent/` — one opencode session with a parent and one explore subagent, including a `/compact` boundary and a small set of tool calls.
- `tests/fixtures/claude-code/simple/` — one claude-code session, no subagents. Verifies the same parser handles it.
- `tests/fixtures/cursor/single/` — one cursor session with a few tool calls. Verifies tool-name normalization and the zero-default for token usage.
- `tests/fixtures/malformed/` — a session with one malformed row mid-file. Verifies `parse_status='partial'` and that indexing continues.
- `tests/fixtures/malformed-structural/` — a session where the JSONL fails to parse as a whole (e.g., truncated). Verifies `parse_status='failed'` is set and the session is still recorded.
- `tests/fixtures/empty/` — a session with no messages (just a header). Verifies the parser produces a `SessionRecord` with empty agent list.
- `tests/fixtures/deeply-nested/` — a session with 3+ levels of subagent nesting. Verifies agent tree resolution and `delegates_to_agent_id` chain.
- `tests/fixtures/multi-compact/` — a session with 3+ `/compact` boundaries. Verifies multiple `compaction_events` rows.
- `tests/fixtures/cross-day/` — a session whose `started_at` and `ended_at` are on different UTC days. Verifies `stats --group-by day` boundary.
- `tests/fixtures/cursor-no-usage/` — a cursor session with no `usage` field. Verifies zero-default token rows.
- `tests/fixtures/grown-on-disk/` — a session indexed once, then appended to (file size and mtime changed). Verifies the staleness check re-indexes.

### Required Test Files

- `tests/test_opencode_parser.py` — parser unit tests including subagent resolution and malformed rows.
- `tests/test_cursor_parser.py` — cursor parser including zero-default token usage and single-parent-agent behavior.
- `tests/test_normalize.py` — tool-name normalization mapping for all known tools.
- `tests/test_cursor_no_usage.py` — verifies cursor session with no `usage` field produces zero-default token rows.
- `tests/test_indexer.py` — indexer upsert, staleness check, summary-column recomputation.
- `tests/test_migrations.py` — `init` idempotence; a test that simulates a future migration 002 by inserting a fake `002_*.sql` and verifying it applies on the next indexer start (not just on `init`).
- `tests/test_query.py` — query API on indexed fixtures.
- `tests/test_cli.py` — in-process `CliRunner` smoke tests plus subprocess E2E tests.
- `tests/test_failure_paths.py` — `PermissionError` on `~/.conv-index/`, `SQLiteError` (simulated via corrupt DB), missing project dir, file deleted between discovery and parse, lock contention.
- `tests/test_privacy.py` — post-index scan of the DB for credential patterns; asserts the synthetic generator rejects seeded credential patterns.
- `tests/test_concurrency.py` — two indexer threads with a shared DB; verifies the second blocks or fails cleanly under the advisory lock.
- `tests/test_parser_snapshot.py` — snapshot test of `parse_session` output for one opencode and one cursor fixture, catching normalization regressions.

No test mutates the user's real `~/.conv-index/analytics.db`.
