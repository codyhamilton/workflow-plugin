# Unit report: 5-02 — Go yakka runtime package

**Status:** `done`

## Before edits (done evidence)

- `cd packages/yakka && go test ./...` — `internal/ingest` failed (`TestRemoveListMatchesPlugin`: missing `packages/opencode-workflow-hooks/...` after `5-01`); other packages passed.
- `grep -r 'WORKFLOW_' packages/yakka --include='*.go'` — many hits (runtime still on `WORKFLOW_*` and `packages/workflow` module path).
- `grep -r 'packages/workflow' packages/yakka --include='*.go'` — import paths on old module.

## What was built

- `packages/yakka/cmd/workflow` → `cmd/yakka`; module `github.com/codyhamilton/yakka/packages/yakka`; internal imports repointed.
- All `WORKFLOW_*` env accessors and tests → `YAKKA_*` (no `WORKFLOW_QUALITY_*` in tree). Default state paths: `~/.config/yakka/client.toml`, `~/.local/share/yakka/{queue,serve}`.
- CLI: `yakka --version`, usage lines, `yakka serve:` / `yakka mcp:` stderr; MCP `serverInfo.name` = `yakka`.
- `policy_test` reads `packages/opencode-yakka-hooks` (post–`5-01` name).
- `cmd/yakka` tests: Go queue writer + kick helper (lock-aware, `YAKKA_BIN` override) instead of `spool.sh` while hooklog still uses `WORKFLOW_*` (`5-04`).

**Rewrite command recorded:** `IMPLEMENTATION.md` → `### Phase 5 module-path rewrite (Decision 1 rebase protocol)`.

## After edits

```
cd packages/yakka && go test ./... → ok (all packages; auto toolchain go 1.27.1; system `go version` go1.22.2)
grep -r 'WORKFLOW_' packages/yakka --include='*.go' | grep -v QUALITY → (no output)
grep -r 'packages/workflow' packages/yakka --include='*.go' → (no output)
```

## Deviations

1. **Spool test helper** — Brief did not name it; required so `go test ./cmd/yakka` passes without `WORKFLOW_*` in Go sources while `packages/hooklog/spool.sh` is unchanged (`5-04` owns hooklog env renames).
2. **Extra CLI stderr** — Also renamed `yakka drain`, `yakka ledger`, and `yakka login` strings in errors/comments where they were still `workflow …`, for consistency with the top-level usage line (brief explicitly named serve/mcp/version only).

## Unfinished work

- `packages/hooklog/spool.sh` and plugin wrappers still use `WORKFLOW_*` until `5-03` / `5-04`.
- `packages/yakka/README.md` updated for test path only; broader docs/skills citations are `5-06`.

## Known problems

None in this unit’s done evidence.
