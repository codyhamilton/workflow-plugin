# Brief: 7-02 — Root README install and layout prose

Consumer: a phase 7 worker on the restructure branch after Phases 5 and 6 are closed.
Owned paths:
`README.md`,
`docs/plans/13-monorepo-restructure/reports/7-02-root-readme.md` (new).
Touch nothing else.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-02-root-readme.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phases 5 and 6.
Runs alongside: `7-01`, `7-03`, `7-04`, `7-05`.
Budget: 15 files to read, about 250 lines to change, 50 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 outcome [cmd] README clause; Solution Shape (plugin at `plugins/yakka`, packages, tools); Domain: Names repo URL and install path.
2. `README.md` — full file; grep `workflow`, `WORKFLOW_`, `opencode-workflow`, `tools/driver/.jev`.
3. `install.sh` — `YAKKA_REPO_URL`, Cursor/Claude install targets.
4. `.claude-plugin/marketplace.json` — plugin coordinates for examples.

## Goal

Rewrite root `README.md` so install instructions and runtime layout prose match the yakka monorepo, including the Jev signal-log default carried from Phase 6.

## Contract

Cited, binding (Phase 7 outcome): "[cmd] `README.md` install instructions use `codyhamilton/yakka` and `yakka@yakka`."

Cited, binding (Domain: Names): "Repo URL `https://github.com/codyhamilton/yakka` everywhere a repo URL appears. `install.sh` installs Cursor to `~/.cursor/plugins/local/yakka` from `plugins/yakka`."

Cited, binding (Packages, OpenCode signal log): "Its new default is `${XDG_STATE_HOME:-~/.local/state}/workflow/jev-signal-log.jsonl`, overridable by `WORKFLOW_JEV_SIGNAL_LOG`." — **post-rename live default:** `${XDG_STATE_HOME:-~/.local/state}/yakka/jev-signal-log.jsonl`, overridable by `YAKKA_JEV_SIGNAL_LOG` (Phase 5–6 code; README must not cite `tools/driver/.jev-signal-log.jsonl`).

Cited, binding (Solution Shape): plugin at `plugins/yakka`; packages under `packages/`; maintainer skills at `.claude/skills/`; binary `plugins/yakka/bin/yakka` and package `packages/yakka`.

Absorbed (Phase 6 Carried): root README must stop documenting the signal log as `tools/driver/.jev-signal-log.jsonl`.

## Changes

- Title and repo identity: `yakka` / `codyhamilton/yakka` (not `workflow-plugin`).
- Clone, curl install, marketplace examples: `git@github.com:codyhamilton/yakka.git`, raw `install.sh` URL on that repo, Claude `/plugin install yakka@yakka`, Cursor path `~/.cursor/plugins/local/yakka`, skills under `.cursor/skills/yakka/`.
- Layout tree: `plugins/yakka`, `packages/yakka`, `packages/opencode-yakka-hooks`, etc.
- Env vars and CLI: `YAKKA_*`, `yakka` subcommands; phase trailers `Yakka-Phase:` with one sentence that readers still accept `Workflow-Phase:` where relevant.
- OpenCode hooks section: package path `packages/opencode-yakka-hooks`, signal log default under `~/.local/state/yakka/jev-signal-log.jsonl`.
- Remove stale `workflow@workflow-plugin`, `~/.cursor/plugins/local/workflow`, and `packages/opencode-workflow-hooks` path literals unless quoting migration from CHANGELOG (prefer pointing to CHANGELOG for migration).

### Keep untouched

`docs/lab/` links that are historical notebooks. Do not edit `CHANGELOG.md` (unit `7-01`).

## Done evidence

Before: `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^README.md:' | wc -l` → non-zero (expect dozens).

After:

- `rg 'codyhamilton/yakka' README.md` → at least one install/clone hit.
- `rg 'yakka@yakka' README.md` → at least one hit.
- `rg 'tools/driver/\.jev-signal-log' README.md` → no matches.
- `rg 'workflow-plugin|workflow@workflow-plugin' README.md` → no matches.
- `python3 tools/release/scan_residual_names.py --scope all 2>&1 | rg '^README.md:'` → no output.

## Report back

Under 1,500 tokens. Status, scan grep before/after, deviations, contradictions.
