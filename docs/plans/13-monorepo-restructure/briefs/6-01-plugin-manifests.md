# Brief: 6-01 — Plugin and marketplace manifests

Consumer: a phase 6 worker on the monorepo-restructure branch.
Owned paths:
`.cursor-plugin/marketplace.json`,
`.claude-plugin/marketplace.json`,
`plugins/yakka/.claude-plugin/plugin.json`,
`plugins/yakka/.cursor-plugin/plugin.json`,
`plugins/yakka/.codex-plugin/plugin.json`,
`docs/plans/13-monorepo-restructure/reports/6-01-plugin-manifests.md` (new).
Touch nothing else. Do not edit `plugins/yakka/skills/`, `install.sh`, hooks, or `CHANGELOG.md` (Phase 7 migration entry).
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer.
Report: before committing, write `docs/plans/13-monorepo-restructure/reports/6-01-plugin-manifests.md` (rubric in `packages/yakka/catalogue/checks/execution-report.json`) and include it in the commit.
Depends on: Phase 5 closed.
Runs alongside: `6-02`, `6-04`, `6-05`.
Budget: 12 files to read, about 80 lines to change, 35 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md`, commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Phase 6 outcome [cmd]; Domain: Plugin (marketplace `source`); Domain: Names (plugin and marketplace name `yakka`, major version bump rule).
2. The five owned JSON files as they stand on this branch.

## Goal

Every plugin and marketplace manifest names `yakka` at the next major version, and each marketplace `source` remains `plugins/yakka`.

## Contract

Cited, binding (Phase 6 outcome): "[cmd] Every plugin and marketplace manifest names `yakka` at the next major version, and each marketplace `source` is still `plugins/yakka`."

Cited, binding (Domain: Names): "The plugin name is `yakka` in every plugin manifest. Every marketplace manifest is named `yakka` and lists exactly one plugin, `yakka`, whose `source` is `plugins/yakka`."

Cited, binding (Domain: Plugin): "Each marketplace lists exactly one plugin. Its `source` is `plugins/yakka`, not `"./"` and not the repo root."

Cited, binding (Domain: Plugin, version bumps): "The rename phases move every manifest to the next major once, together, with one `CHANGELOG.md` entry. They do not also take a minor." "The Claude, Cursor and Codex manifests move together."

Settled: manifests are currently `2.12.0` with plugin name `workflow` and marketplace name `workflow-plugin`. The next major is `3.0.0`. Do not bump `plugins/yakka/bin/VERSION` (binary release version; Phase 5 already set `0.2.0`).

Settled: Phase 3 Carried item 1 (logged-in Cursor session) is not this unit. Automated checks only.

## Changes

- Set plugin `name` to `yakka` in all three harness manifests under `plugins/yakka/`.
- Set marketplace `name` to `yakka` in both root marketplace files. Set the sole listed plugin `name` to `yakka`. Keep `source` exactly `plugins/yakka`.
- Bump `version` to `3.0.0` in all five JSON files together.
- Refresh descriptions only where they still use the product name `workflow` as the plugin identifier (common noun "workflow" in skill-method prose may stay).

### Keep untouched

`hooks/`, `skills/`, `bin/`, `script/`, MCP configs, and `CHANGELOG.md`. Layout check marketplace rules are unchanged (`plugins/yakka` source).

## Done evidence

Identify failing check before edits:

- `python3 -c "import json, pathlib; …"` or `jq` one-liners asserting each owned file has `name`/`yakka`, version `3.0.0`, and marketplace `source` `plugins/yakka` → fail before; pass after.

After changes:

- `python3 -m unittest tools/release/test_layout.py` → pass (marketplace single-plugin and `plugins/yakka` source cases still clean).
- Observable: all five owned JSON files list plugin/marketplace identity `yakka` and version `3.0.0`.

## Report back

Under 1,500 tokens. Status, check output before/after, deviations.
