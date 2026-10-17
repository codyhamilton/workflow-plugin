# Brief: 5-02 — Go yakka runtime package

Consumer: a phase 5 worker running after `5-01`.
Owned paths:
`packages/yakka/**`,
`docs/plans/13-monorepo-restructure/IMPLEMENTATION.md` (record module-path rewrite command only, under Phase 5),
`docs/plans/13-monorepo-restructure/reports/5-02-go-yakka-runtime.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-02-go-yakka-runtime.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`).
Depends on: `5-01`.
Runs alongside: `5-04`, `5-06` (disjoint paths).
Budget: 55 files to read, about 400 lines to change, 90 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Domain: Names (Go module, `cmd/yakka`, `yakka --version`, `WORKFLOW_*` → `YAKKA_*` except `WORKFLOW_QUALITY_`, state-path table), Phase 5 outcome [cmd] and [test] clauses that mention the binary, queue, serve, and MCP `serverInfo.name`.
2. `packages/yakka/go.mod` and grep `github.com/codyhamilton/workflow-plugin/packages/workflow` under `packages/yakka/`.
3. `packages/yakka/cmd/workflow/main.go` — version line and subcommand usage strings.
4. `packages/yakka/internal/mcp/mcp.go` — `serverInfo.name`.
5. Grep `WORKFLOW_` and `workflow` default paths under `packages/yakka/internal/{drain,serve,clientconfig,secrets}`.

## Goal

The Go module is `packages/yakka` with command `cmd/yakka`; runtime code reads `YAKKA_*` env vars and default state paths under `yakka`, and `yakka --version` / MCP initialize report the product name `yakka`.

## Contract

Cited, binding: "The Go module is `github.com/codyhamilton/yakka/packages/yakka`, command `cmd/yakka`."

Cited, binding: "Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code … except `WORKFLOW_QUALITY_`. No code reads the old env vars or the old state paths."

Cited, binding (state-path table): `~/.local/share/workflow/{queue,serve}` → `~/.local/share/yakka/{queue,serve}`; `~/.config/workflow/client.toml` → `~/.config/yakka/client.toml`; `~/.cache/workflow/` → `~/.cache/yakka/`; `~/.local/state/workflow/` → `~/.local/state/yakka/`; `~/.local/share/workflow-plugin/hooklog` → `~/.local/share/yakka/hooklog`.

Cited, binding: "`yakka --version` prints `yakka <version> <commit>`." "`bin/yakka` … Cache, release assets … use `yakka`."

Cited, binding: "MCP `serverInfo.name` is `yakka`."

Cited, binding: "`YAKKA_CHECKS_DIR`" replaces `WORKFLOW_CHECKS_DIR` wherever the catalogue env is named (same suffix rule). Catalogue stays at `packages/yakka/catalogue/`.

Cited, binding (Phase 5): sibling package `packages/hooklog` — keep `../../../hooklog/...` test fixture depth valid; do not move hooklog.

Settled: `bin/VERSION` is bumped in unit `5-03`, not here. Do not edit `plugins/yakka/bin/`.

## Changes

- `git mv packages/yakka/cmd/workflow` → `packages/yakka/cmd/yakka` if not already done in content pass.
- Rewrite `go.mod` module path to `github.com/codyhamilton/yakka/packages/yakka` and every internal import from `.../packages/workflow/...` to `.../packages/yakka/...`.
- Rename env accessors and defaults per the `YAKKA_*` rule in all `packages/yakka/**/*.go` (tests included). Remove reads of old `WORKFLOW_*` names except where a test documents legacy input — there should be none in this package after the rename.
- Update user-facing strings: `workflow serve` → `yakka serve` in usage lines; version output `yakka %s %s`; stderr prefixes `yakka mcp:` / `yakka serve:`.
- Set MCP `serverInfo.name` to `yakka`.
- Record the exact `find`/`sed` or equivalent module rewrite command in `IMPLEMENTATION.md` under `### Phase 5` (Decision 1 rebase protocol). Do not close the phase or write Carried.

### Keep untouched

Embedded site bytes under `internal/serve/site/` except path literals in Go that must change for env or module names. Release asset file names (`workflow-linux-amd64`, etc.) are updated in `5-05`, not here. Plugin manifests, `skills/` prose beyond catalogue citations (`5-06`), and `tools/driver`.

## Done evidence

Identify failing check before edits; report before and after.

- `cd packages/yakka && go test ./...` → pass (use auto toolchain if local Go is below `go.mod`; report version used).
- `grep -r 'WORKFLOW_' packages/yakka --include='*.go' | grep -v QUALITY` → no hits (or only comments you intentionally keep — there should be none in non-comment code).
- `grep -r 'packages/workflow' packages/yakka` → no hits in `.go` files.

## Report back

Under 1,500 tokens. Status, rewrite command recorded, test output, deviations.
