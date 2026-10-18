# Brief: 7-01 — CHANGELOG migration guide

Consumer: a phase 7 worker on the restructure branch after Phases 5 and 6 are closed.
Owned paths:
`CHANGELOG.md`,
`docs/plans/13-monorepo-restructure/reports/7-01-changelog-migration-guide.md` (new).
Touch nothing else. Do not edit `tools/release/scan_residual_names.py` (unit `7-06`).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/7-01-changelog-migration-guide.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phases 5 and 6.
Runs alongside: `7-02`, `7-03`, `7-04`, `7-05`.
Budget: 25 files to read, about 200 lines to change, 45 tool turns. Past the budget, hand off in `IMPLEMENTATION.md`, commit if this brief commits, report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 7 outcome [cmd] CHANGELOG clause; Domain: Names (state-path table, `WORKFLOW_*` rule, maintainer actions).
2. `CHANGELOG.md` — section heading style; keep all existing sections below the new entry.
3. `install.sh`, `tools/cloud-env/bootstrap-yakka-skills.sh`, `plugins/yakka/.mcp.json` — harness install/remove facts to quote accurately.
4. `rg 'YAKKA_[A-Z0-9_]+'` over `packages/yakka`, `plugins/yakka`, `tools/driver`, `install.sh` — inventory env vars for the map (exclude `WORKFLOW_QUALITY_*`; those stay legacy per design).

## Goal

Add the single major-version CHANGELOG entry that is the migration guide for the yakka rename cut.

## Contract

Cited, binding (Phase 7 outcome): "[cmd] The CHANGELOG rename entry carries one `YAKKA_*` row for every `WORKFLOW_*` identifier removed by Phases 5–6, every path in the state-path table, remove-and-install commands for Claude Code, Cursor, Codex and OpenCode, and the numbered maintainer actions."

Cited, binding (Domain: Names): "The CHANGELOG rename entry is the migration guide: the full `WORKFLOW_*` → `YAKKA_*` map, every state path above, per-harness remove-then-install commands, the `.gitignore` change (`.cursor/skills/workflow/` → `.cursor/skills/yakka/`), the MCP-prefix and skill-prefix note, and the maintainer actions (repo rename, release publish, serve data-dir move, `client.toml`, harness reinstall, cloud `environment.json`, optional Pages project, optional checkout rename)."

Cited, binding (Domain: Names, state paths):

| Was | Becomes |
|---|---|
| `~/.local/share/workflow/{queue,serve}` | `~/.local/share/yakka/{queue,serve}` |
| `~/.config/workflow/client.toml` | `~/.config/yakka/client.toml` |
| `~/.cache/workflow/` | `~/.cache/yakka/` |
| `~/.local/state/workflow/` | `~/.local/state/yakka/` |
| `~/.local/share/workflow-plugin/hooklog` | `~/.local/share/yakka/hooklog` |
| `~/.cache/workflow-plugin` (cloud-env checkout) | `~/.cache/yakka/src` |

Cited, binding (Domain: Names): "Every identifier that starts with `WORKFLOW_` becomes `YAKKA_` with the same suffix, in shipped code and in maintainer tools, except `WORKFLOW_QUALITY_`."

Settled: plugin manifests are already `yakka` `3.0.0` from Phase 6. The new CHANGELOG section is `3.0.0` and its heading must contain the word `rename` (case-insensitive) so `tools/release/scan_residual_names.py` `rename_changelog_cutoff()` returns true for unit `7-06`.

## Changes

- Insert a new top `## 3.0.0 — …` section whose title includes `rename`.
- **Env map:** one table row per `WORKFLOW_*` → `YAKKA_*` pair that Phases 5–6 removed from live code (same suffix; no `WORKFLOW_QUALITY_*` rows).
- **State paths:** reproduce the table quoted above in prose or table form.
- **Per-harness remove-then-install:** numbered steps for Claude Code (`yakka@yakka` / marketplace `codyhamilton/yakka`), Cursor (`install.sh` / `~/.cursor/plugins/local/yakka`), Codex (plugin root `plugins/yakka`, `bin/yakka`), OpenCode (`packages/opencode-yakka-hooks`, skill prefix / env). Say explicitly to remove the old `workflow` plugin or install tree before installing `yakka` so hooks do not double-fire (per DESIGN Compatibility).
- **`.gitignore`:** document `.cursor/skills/workflow/` → `.cursor/skills/yakka/`.
- **MCP and skill prefixes:** `mcp__plugin_yakka_*`, `/yakka:` or skill names as shipped under `plugins/yakka/skills/`.
- **Maintainer actions:** numbered list matching the parenthetical in the Domain: Names CHANGELOG sentence (repo rename, release publish, serve data-dir move, `client.toml`, harness reinstall, cloud `environment.json`, optional Pages project, optional checkout rename).

### Keep untouched

All pre-existing `CHANGELOG.md` sections and their wording (historical paths stay historical). Do not bump plugin manifest versions here.

## Done evidence

Before: `grep -i rename CHANGELOG.md` → no match (or no `3.0.0` migration section).

After:

- `python3 -c "import re; t=open('CHANGELOG.md').read(); assert re.search(r'(?m)^##\\s+.*\\brename\\b', t, re.I)"` → exit 0.
- Manual checklist against the Phase 7 [cmd] CHANGELOG clause: env map complete, state-path table present, four harness command blocks, maintainer actions numbered — cite section headings in the report.
- `rg 'WORKFLOW_QUALITY_' CHANGELOG.md` in the new section only if documenting the exception; do not imply quality service env vars renamed.

## Report back

Under 1,500 tokens. Status, evidence commands, deviations, contradictions.
