# Implementation: Analytics Dashboard Overhaul

## Run

- Tool: Claude Code (orchestrator on Sonnet 5.5)
- Session: https://claude.ai/code/session_011T4Vh5cPS7acScndWmdobz
- Started: 2026-10-09
- Branch: plan/12-analytics-dashboard-overhaul

## Phase 1 — Event policy, archive and slim ingest

Units: six, from `refine` (briefs in `briefs/`). 1-01 to 1-04 parallel; 1-05 then 1-06 in sequence.

### 1-03-plugin-remove-list

Built (9f2c7de): `recordHooklog` skips the four removed events by `hook_event_name`; the list sits in a marked `remove-list` block in `src/index.ts`; README updated. Plugin tests 7 pass, 0 fail (were 5 pass, 2 fail with tests updated first). Surfaces: `packages/opencode-workflow-hooks/{src/index.ts,tests/test_hooks.mjs,README.md}`. Deviations: none.

### 1-01-archive-package

Built (64404aa): new `tools/workflow/internal/archive` with `Line`, `Entry`, `Append`, `Read`; one zstd frame per file per call, package mutex, file-name escaping per brief. `go test -race`, `go build ./...`, `go vet` pass. Surfaces: `tools/workflow/internal/archive/`, `go.mod`, `go.sum`. Deviations: none. Limit for 1-05: a crash mid-write can leave a torn last frame, which makes `Read` error for that conversation instead of skipping it.
