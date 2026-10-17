# Brief: 3-01 — Cursor plugin and hook scripts

Consumer: the phase 3 worker.
Owned paths:
`plugins/yakka/**` (new),
`.cursor-plugin/marketplace.json`,
`.claude-plugin/marketplace.json`,
`.claude-plugin/plugin.json`,
`.cursor-plugin/plugin.json`,
`.codex-plugin/**`,
`.mcp.json`,
`.codex-mcp.json`,
`skills/**`,
`hooks/**`,
`bin/**`,
`install.sh`,
`tools/driver/tests/test_install_route.py`,
`tools/release/build.sh`,
`packages/hooklog/spool.sh`,
`packages/hooklog/README.md`,
`packages/hooklog/tests/test_surfaces.py`,
`packages/hooklog/tests/test_write_surfaces.py`,
`docs/design/02-edge-capture.md`,
`docs/design/05-distribution.md`,
`CHANGELOG.md`,
`docs/plans/13-monorepo-restructure/reports/3-01-cursor-plugin.md` (new).
Touch nothing else. Do not edit `IMPLEMENTATION.md` unless you stop over budget.
Commits: two commits on the current branch, Decision 1's move shape. First: rename-only `git mv`, no content edits. Second: path rewrite, new `script/` files, version bump, docs, tests, and this unit's report. Plain-summary titles. Do not push. Do not open a pull request. Do not add a `Workflow-Phase:` trailer. The report is not in the rename commit.
Report: before the second commit, write `docs/plans/13-monorepo-restructure/reports/3-01-cursor-plugin.md` (rubric in `packages/workflow/catalogue/checks/execution-report.json`) and include it in that commit.
Depends on: Phase 2.
Runs alongside: nothing.
Budget: 40 files to read, about 500 lines to change, 80 tool turns. Past the budget, stop: write a handoff under this brief's name in `IMPLEMENTATION.md` (done, not done, what you learned), commit if this brief commits, and report `over budget`.

## Required reading, in order

1. `docs/plans/13-monorepo-restructure/DESIGN.md` — Domain: Plugin (`plugins/yakka`), Decision 2, Phase 3 outcome and surfaces. Do not read Phases 4–7 except to avoid doing their work.
2. `hooks/cursor.json`, `hooks/hooks.json`, `hooks/codex.json` — current commands.
3. `.cursor-plugin/plugin.json`, `.cursor-plugin/marketplace.json`, `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.mcp.json`, `.codex-mcp.json`.
4. `install.sh` — `is_valid_plugin_source`, `ensure_cursor_core_plugin`, skill source paths.
5. `bin/workflow` — four-step resolution; `ROOT` is today both the plugin root and the repo root.
6. `packages/hooklog/spool.sh` — drain kicks `bash <repo>/bin/workflow`.
7. `packages/hooklog/tests/test_surfaces.py` and `test_write_surfaces.py` — repo-root hook paths and `cwd` of the spawned command.
8. `docs/design/02-edge-capture.md` section "Per-harness install and trust"; `docs/design/05-distribution.md` sections "Layout" and "Per-harness configs".

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Cursor loads the workflow plugin from `plugins/yakka`, and the Cursor hooks file's commands are `./script/...` scripts that live in that directory.

## Contract

Cited, binding. Settled by Decision 2 and the Plugin domain. Do not reopen them.

- "The workflow plugin lives at `plugins/yakka`. That directory is the install root: skills, harness manifests, hooks, and the `script/` directory its Cursor hooks execute. It is not a package."
- "Each marketplace lists exactly one plugin. Its `source` is `plugins/yakka`, not `"./"` and not the repo root." "Until the rename phases, the plugin name stays `workflow` and the marketplace name and repo URL stay as they are. The directory is `plugins/yakka` from Phase 3, before those renames."
- "Cursor hook commands are plugin-root-relative `./script/...`. They do not use `${CURSOR_PLUGIN_ROOT}`, an absolute path, or a path that leaves `plugins/yakka`. Arguments stay as they are today (`--harness cursor --event <event>` on the spool; the detached `--version` prefetch stays a second command). The scripts those commands name exist under `plugins/yakka/script/` and are what actually runs. Cursor runs them with `plugins/yakka` as the working directory."
- "Claude and Codex hook commands keep their shape: `bash "<root>/...spool.sh" --harness <h> [--event <E>]`, Codex with no `--event`. `<root>` is `plugins/yakka`. The path they name is inside that directory (the same scripts `script/` provides, or `bin/` for the prefetch), not a sibling the install does not contain."
- "`packages/hooklog` remains the hook-edge package. `plugins/yakka` contains the copies its hooks execute, because a marketplace install of that directory is the whole install root and does not include `packages/`."
- "`bin/workflow` keeps its four-step resolution and its cache key, `${XDG_CACHE_HOME:-~/.cache}/workflow/<bin/VERSION>/workflow-<os>-<arch>`, until the rename phases. Its step-4 source build reads `packages/workflow` when the checkout contains it. A marketplace install that contains only `plugins/yakka` uses the released binary; it does not contain the Go module."
- "`bin/VERSION` is not bumped before the rename phases."
- "A phase that changes a shipped plugin file and can merge on its own bumps the plugin manifests one minor version." "The Claude, Cursor and Codex manifests move together."
- "`install.sh` (every mode) and `tools/cloud-env/bootstrap-workflow-skills.sh` install core skills only." "`Cursor install materializes `plugins/yakka`, not the repo root."
- Phase 3 outcome, the clauses this unit can check: both marketplace `source` values are `plugins/yakka`; that directory contains `.cursor-plugin/plugin.json`, `skills/`, and the hooks file the manifest names; the plugin is not under `packages/`; every Cursor hook command is `./script/...`; with cwd `plugins/yakka`, the spool command from that file, given a `sessionStart` payload, exits 0 and writes an event into the queue; the detached `--version` command is the other `./script/...` entry; install-route tests show Cursor install copies `plugins/yakka`, and the installed tree contains `script/` and the hooks file; Claude and Codex hook commands in that tree resolve inside `plugins/yakka`.
- The Cursor session that loads skills and fires a hook is the orchestrator's check. Do not start Cursor. Do not run `workflow serve`.

Hooks filename, settled for this unit: Cursor's docs discover `hooks/hooks.json` unless the manifest `hooks` field overrides that path. Claude's registration is already `hooks/hooks.json` in the same plugin directory, so the two files cannot share that name. Keep `hooks/hooks.json` (Claude), `hooks/cursor.json` (Cursor), and `hooks/codex.json` (Codex). `.cursor-plugin/plugin.json` keeps `"hooks": "./hooks/cursor.json"`. That is the hooks file the manifest names.

## Changes

Two commits.

### Commit 1 — rename only

`git mv` these into `plugins/yakka/`, with no content edits and no new files:

- `skills/` → `plugins/yakka/skills/`
- `hooks/` → `plugins/yakka/hooks/`
- `bin/` → `plugins/yakka/bin/`
- `.mcp.json` → `plugins/yakka/.mcp.json`
- `.codex-mcp.json` → `plugins/yakka/.codex-mcp.json`
- `.claude-plugin/plugin.json` → `plugins/yakka/.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json` → `plugins/yakka/.cursor-plugin/plugin.json`
- `.codex-plugin/` → `plugins/yakka/.codex-plugin/`

Leave `.cursor-plugin/marketplace.json` and `.claude-plugin/marketplace.json` at the repo root. Do not move `packages/`, `tools/`, `.claude/skills/`, or `install.sh`.

### Commit 2 — rewrite

- Marketplace: both core-plugin `source` values are the string `plugins/yakka`. Plugin name stays `workflow`. Marketplace name and repo URL stay as they are. One plugin each.
- Cursor hooks file `plugins/yakka/hooks/cursor.json`: every `command` is plugin-root-relative `./script/...`. None contains `${CURSOR_PLUGIN_ROOT}`, `tools/hooklog`, `packages/hooklog`, or an absolute path. Keep the same events, timeouts, and arguments.
  - Spool entries: `./script/spool.sh --harness cursor --event <event>` with the event names that file has today.
  - The `sessionStart` prefetch is a second command, `./script/prefetch-version.sh`, not a `bin/workflow` command in the hooks file.
- `plugins/yakka/script/spool.sh`: executable copy of `packages/hooklog/spool.sh`. Its drain, when `WORKFLOW_BIN` is unset, runs `bash <plugin>/bin/workflow drain`, where `<plugin>` is the parent of `script/` (`plugins/yakka` in a checkout, the install root in a marketplace install). It must not call `packages/hooklog`.
- `plugins/yakka/script/prefetch-version.sh`: executable. It runs `nohup bash <plugin>/bin/workflow --version </dev/null >/dev/null 2>&1 & exit 0` and always exits 0. `<plugin>` is the parent of `script/`.
- Claude commands in `plugins/yakka/hooks/hooks.json`: `bash "${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}/script/spool.sh" --harness claude --event <E>`, and the prefetch `nohup bash "${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}/bin/workflow" --version ...`. Same events as today.
- Codex commands in `plugins/yakka/hooks/codex.json`: `bash "${PLUGIN_ROOT}/script/spool.sh" --harness codex` (no `--event`), and the prefetch `nohup bash "${PLUGIN_ROOT}/bin/workflow" --version ...`.
- `.mcp.json` and `.codex-mcp.json` already name `bin/workflow` inside the plugin root. After the move they stay that way. Do not point them at `packages/`.
- `plugins/yakka/bin/workflow`: keep the four steps and the cache key. `bin/VERSION`, `bin/SHA256SUMS`, and `bin/RELEASE_URL` are read from the plugin directory (the parent of `bin/`). Step 4 builds `packages/workflow` only when `<plugin>/../packages/workflow/go.mod` exists (a repo checkout). A copy of `plugins/yakka` alone has no module and stops at the release download. `bin/VERSION` stays `0.1.0`.
- `packages/hooklog/spool.sh`: when `WORKFLOW_BIN` is unset, kick `plugins/yakka/bin/workflow` from the repo root (this file stays the package; `../..` from `packages/hooklog` is the repo root, and `bin/workflow` is no longer there). Do not change scrub, queue naming, or flags.
- `packages/hooklog/README.md`: repoint links that named repo-root `hooks/` or `bin/workflow` at `plugins/yakka`. Do not rewrite the package's behaviour.
- `tools/release/build.sh`: read `plugins/yakka/bin/VERSION` and write `plugins/yakka/bin/SHA256SUMS`.
- `install.sh`: a repo checkout's plugin source is `$SCRIPT_DIR/plugins/yakka` (skills and `.cursor-plugin/plugin.json` live there, not at the repo root). Cursor local install copies that directory into `~/.cursor/plugins/local/workflow`, not the repo root. The git-clone fallback clones the repo to the cache and copies `plugins/yakka` out of it; it does not leave the whole repo as the plugin. Claude, OpenCode, and Cursor-cloud skill copies read `plugins/yakka/skills`. `verify_cursor_core_plugin` still requires `.cursor-plugin/plugin.json` and `skills/`; also require `script/spool.sh` and the hooks file named by that manifest. Do not restore a lab install.
- `tools/driver/tests/test_install_route.py`: the Cursor local install assertion shows the installed tree is the `plugins/yakka` copy: it contains `script/` and the hooks file the manifest names, and the Claude and Codex hook commands in that tree name paths inside that tree (`script/` or `bin/`), not `packages/` or `tools/`. Existing core-only and maintainer-skill assertions stay.
- `packages/hooklog/tests/test_surfaces.py` and `test_write_surfaces.py`: shipped configs are under `plugins/yakka/`. Cursor commands are `./script/...`, so run those with cwd `plugins/yakka`. `CLAUDE_PLUGIN_ROOT` and `PLUGIN_ROOT` for the shipped commands are the plugin directory. Manifest version and hooks assertions read `plugins/yakka/.cursor-plugin/plugin.json` (and the sibling manifests). The example file `packages/hooklog/cursor-hooks.example.json` stays where it is.
- Versions: `2.11.0` → `2.12.0` in the three plugin manifests together. `CHANGELOG.md` gets a `2.12.0` entry: the plugin directory is `plugins/yakka`, marketplace `source` is that path, Cursor hook commands are `./script/...`.
- Docs: the per-harness path rows in `docs/design/02-edge-capture.md` and the Layout plus Per-harness configs tables in `docs/design/05-distribution.md` name `plugins/yakka` for the plugin's hooks, `script/`, and `bin/`. Do not add the Phase 4 Layout section or the layout check.

### Keep untouched

Product name `workflow`, marketplace name, repo URL, `bin/VERSION`, hook event lists, MCP tool name, `packages/hooklog` as the package, `packages/workflow`, maintainer skills under `.claude/skills/`, and anything Phase 4–7 owns (layout check, signal-log default, yakka rename).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

- `python3 -c` (or `jq`) over both marketplace files: the core plugin `source` is the string `plugins/yakka`, and the plugin name is `workflow`.
- `test -f plugins/yakka/.cursor-plugin/plugin.json && test -d plugins/yakka/skills && test -f plugins/yakka/hooks/cursor.json && test ! -d packages/yakka`.
- Every `command` in `plugins/yakka/hooks/cursor.json` matches `^\./script/`. `rg 'CURSOR_PLUGIN_ROOT|tools/hooklog|^/' plugins/yakka/hooks/cursor.json` → no hits.
- From cwd `plugins/yakka`, the `sessionStart` spool command, with a JSON payload containing `"session_id":"phase3"` on stdin and `WORKFLOW_QUEUE` set to a temp dir and `WORKFLOW_HOOKLOG_KICK=0`, exits 0 and writes one `*.evt` whose envelope harness is `cursor` and event is `sessionStart`.
- `python3 -m unittest tools/driver/tests/test_install_route.py` → OK, including the new installed-tree assertions.
- `python3 -m unittest packages/hooklog/tests/test_surfaces.py` → OK.
- The three plugin manifests are `2.12.0`. `plugins/yakka/bin/VERSION` is `0.1.0`.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.

## Amendment

`tools/cloud-env/bootstrap-workflow-skills.sh` is not an owned path. It only runs `install.sh`. The cloud route in `install.sh` is what installs `plugins/yakka/skills`. A re-dispatch does not edit the bootstrap script.
