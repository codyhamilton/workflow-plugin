# Brief: 5-07 — Residual runtime names outside release

Consumer: a phase 5 fixer running after `5-02`, `5-03`, and `5-04`, before `5-05`.
Owned paths:
`packages/hooklog/**`,
`packages/yakka/**` except `packages/yakka/README.md`,
`packages/yakka-analytics/**` except `packages/yakka-analytics/README.md`,
`packages/opencode-yakka-hooks/**` except `packages/opencode-yakka-hooks/README.md`,
`plugins/yakka/bin/RELEASE_URL`,
`docs/plans/13-monorepo-restructure/reports/5-07-residual-runtime-names.md` (new).
Touch nothing else. `tools/release/**` and the four package READMEs above are `5-05`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/5-07-residual-runtime-names.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: `5-02`, `5-03`, `5-04`.
Runs alongside: nothing.
Budget: 25 files to read, about 120 lines to change, 40 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/briefs/5-05-release-scan-and-index.md` — the residual-name patterns in **Contract**. Those patterns are binding. Do not weaken them.
2. The files listed under Changes. Read the matching lines, not whole trees.

## Goal

Phase 5's residual-name scan can pass on the runtime trees this unit owns. Names that `5-02`, `5-03`, and `5-04` left behind are the yakka names.

## Contract

Cited, binding (Phase 5 outcome): the residual-name scan reports nothing under `packages/yakka`, `packages/hooklog`, `packages/yakka-analytics`, `packages/opencode-yakka-hooks`, and `plugins/yakka`'s `bin/`.

Cited, binding (Domain: Names): repo URLs are `https://github.com/codyhamilton/yakka`. Cache and release assets use `yakka`. `WORKFLOW_*` in these trees becomes `YAKKA_*` except `WORKFLOW_QUALITY_`.

Settled exception, do not edit: `packages/yakka/internal/secrets/secrets_test.go` strings `Workflow-Phase:` and `Workflow-Phase-Trailer-Name`. The scan's allowed exception is Go test fixtures under `packages/yakka/` that carry recorded trailer text, and it applies only to `Workflow-Phase`, `Workflow-Plan`, and `workflow-report`. `5-05` implements that exception.

## Changes

- `packages/hooklog` README, example JSON/TOML, `hooklog.py` comment, and the two tests that rewrite `/ABS/PATH/workflow-plugin`: use `packages/opencode-yakka-hooks`, `plugins/yakka/bin/yakka`, `~/.config/yakka/client.toml`, `/ABS/PATH/yakka`, and MCP server key `yakka`. Keep example commands as absolute-path templates. Do not switch them to `./script/...`.
- `packages/opencode-yakka-hooks/package.json` and `packages/yakka-analytics/package.json` repository URLs: `https://github.com/codyhamilton/yakka.git`.
- `packages/opencode-yakka-hooks/tests/test_hooks.mjs`: the spool subprocess env is `YAKKA_QUEUE` and `YAKKA_HOOKLOG_KICK`. `packages/hooklog/spool.sh` reads those names.
- `packages/opencode-yakka-hooks/tests/test_batch.py`: delete the unused `WORKFLOW_SIGNAL_STATE_DIR` assignments and the `WORKFLOW_ANALYTICS_URL` pop. If a test must clear the analytics URL, pop `YAKKA_ANALYTICS_URL`.
- Placeholder marker `workflow-analytics-placeholder` becomes `yakka-analytics-placeholder` in `packages/yakka/internal/serve/site.go`, `site/index.html`, `site_test.go`, and `packages/yakka-analytics/tests/hosted/hosted.spec.ts`. The sentence around the marker stays. `5-05` updates `tools/release/build.sh` to the same marker.
- `packages/yakka/internal/compact/compact_test.go` fixture `repo_id` values: `github.com/codyhamilton/yakka`. Update any assertion in that test that expects the old repo id.
- `plugins/yakka/bin/RELEASE_URL`: `https://github.com/codyhamilton/yakka/releases/download`.

### Keep untouched

`packages/yakka/internal/secrets/secrets_test.go`. Package READMEs. `tools/release/**`. Plugin manifest `name` fields. Skill bodies.

## Done evidence

Identify the hits before editing. Report the before count and the after command.

- Before: the forbidden patterns in the `5-05` brief's Contract section, limited to this unit's owned paths, excluding `secrets_test.go`, have hits.
- After: that same search prints nothing.
- `python3 -m unittest packages/opencode-yakka-hooks/tests/test_batch.py` → pass.
- `python3 -m unittest discover -s packages/hooklog/tests -p 'test_*.py'` → pass.
- `cd packages/yakka && go test ./internal/serve/ ./internal/compact/` → pass.

## Report back

Under 1,500 tokens. Status, before and after hit counts, test output, deviations.
