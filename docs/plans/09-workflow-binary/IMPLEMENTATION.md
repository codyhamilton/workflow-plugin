# Workflow binary implementation

Tool: Claude Code (Opus 5.5 orchestrator, subagent workers), on `hooks-reconcile`.
Run identity: session https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp, starting HEAD
`9e79ede`.
Started: 2026-10-05 (Australia/Brisbane).

Unattended run: the maintainer asked for designs 3 to 5 and execution of everything designed, with
no stops, on this branch. No push, tag, release publish or PR. Go 1.27.1 was installed to
`~/.local/go` for the build (no system Go existed).

Execution logging uses the legacy `workflow-quality` service on 8765 while it is still the live
ledger; phase 5 retires that requirement.

## Phase 1 — Service core

Refined into three sequential units (briefs 210–212, design_id 209), committed in `dc64539`.
Refine decisions the later phases rely on: the fact JSON keys are fixed in brief 1-03; the row hash
excludes `id` and `content`; a resent rejected fact is rejected again, not `duplicate`.

### 1-01-module-keys-secrets (execution 14)

- Built: the Go module `tools/workflow`, `internal/keys` (repo_id, repo path, content and row
  hashes) and `internal/secrets` (one shared pattern set), with tests. A test scans every tracked
  `.md` file and finds no hits.
- Commit: `ae37ae0`. `go vet` and `go test ./...` pass.
- Deviations: none. Known limits are in its report: the `.env`-style pattern is loose, and
  `RepoPath` errors for a directory that does not exist.
- Agent: Sonnet, 10 tool calls, about 53k tokens.

### 1-02-store (execution 15)

- Built: `internal/store`: tenant directories, `ledger.db` (WAL), blobs and pending, the facts,
  rejections, screens and scores tables, and one group-commit writer per tenant.
- Commit: `8024966`. `go test ./...` passes, and the race tests pass with 50 concurrent appenders
  and no `SQLITE_BUSY`.
- Writer burst (8 tenants, 4,800 facts, 20-fact requests): p50 11 ms, p99 20–30 ms, ledger 6 MB.
  Reported only; there is no threshold.
- Deviations: an empty `Raw` errors explicitly, because `INSERT OR IGNORE` swallows the NOT NULL
  violation; a `tmp/` directory was added to each tenant directory; index names are the worker's
  own.
- Agent: Sonnet, 9 tool calls, about 58k tokens.
