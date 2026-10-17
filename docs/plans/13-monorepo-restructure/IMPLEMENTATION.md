# Implementation

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-6567db80-03ab-533d-8a33-89e515bdc24d
Start: 2026-10-17T17:15:00Z

Re-dispatch (phase 1 verification and close):
Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-687260bb-d69c-599d-b5b2-00a309f320b0
Start: 2026-10-17T17:33:48Z

Phase 2:
Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-31ad8066-77e3-5acc-8b24-bcdf36e79742
Start: 2026-10-17T17:46:00Z

## Phase 1: Lab collapses into maintainer skills

Refine skipped. DESIGN.md says Phase 1 is one worker. Assumption 9's check, which that skipped refine would have made, is settled in the brief: Cursor's skills doc loads `.claude/skills/` for compatibility, so this phase adds no `.cursor/skills/` symlinks.

### 1-01-lab-collapse

Brief: `docs/plans/13-monorepo-restructure/briefs/1-01-lab-collapse.md`.
Report: `docs/plans/13-monorepo-restructure/reports/1-01-lab-collapse.md`.
Worker: Composer (`composer-2.5`), agent `bc-0371e3dd-ff21-5ed6-9b32-2abd27c21522`. The harness did not report turns or final context.
Commit: `31848c6` (no `Workflow-Phase` trailer). The report was written and left untracked; it is committed with this record.

Built: the lab plugin is removed. `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, and `workflow-tuning` are renames (R100) into `.claude/skills/`. `lab-proposal` is deleted. Both marketplaces list only `workflow`. Plugin manifests are `2.10.0`. `bin/VERSION` stays `0.1.0`. `install.sh` and `tools/cloud-env/bootstrap-workflow-skills.sh` no longer copy lab skills. `LAB_SKILLS` is `MAINTAINER_SKILLS` (those six names). `WORKFLOW_INSTALL_LAB=1` is set by the install-route test harness and does not install them.

Surfaces: the brief's owned paths, plus `docs/design/system-architecture.md` (already owned).

Deviations: the worker reported none. After verification, the orchestrator added `.claude/skills/` on the Maintainer skills row. Architectural Implications says that row points at `.claude/skills/`; the unit's row named the skills and did not point at the directory.

`artifact_feedback` on the brief and the report: unreachable. No cached `bin/workflow`, the v0.1.0 linux asset returns 404, and source build stops because `go.mod` requires go 1.27.1 and this machine has go 1.22.2 (`GOTOOLCHAIN=local`).

### Verification

Closed. Re-run on this branch at `/workspace` (the phase 1 tree; not merged to master). Claude Code 2.1.302.

- `claude -p "/skills"` stdout: `/skills isn't available in this environment.` Exit 0. The session record's command outcome is `unavailable_headless`. Print mode does not register that slash command: it opens an interactive panel. That is the departure below. The command did not print the six names.
- Same loader, same working directory. Debug log: `Loading skills from: managed=/etc/claude-code/.claude/skills, user=/home/ubuntu/.claude/skills, project=[/workspace/.claude/skills]` and `Loaded 6 unique skills (6 unconditional, 0 conditional, managed: 0, user: 0, project: 6, additional: 0, legacy commands: 0)`. Managed, user, and additional counts are 0, so the six are the project skills.
- Each of these print-mode slash commands resolved to that project skill and attached its `SKILL.md` (`Base directory for this skill: /workspace/.claude/skills/<name>`) before auth stopped the turn with `Not logged in`: `/iterate`, `/jev-variants`, `/setup`, `/transcript-parser`, `/white-paper`, `/workflow-tuning`. `/lab-proposal` and `/not-a-skill` did not resolve (unknown-command fallback). `setup` and `workflow-tuning` set `disable-model-invocation: true`, so they are absent from the model skill listing and still load as slash commands. The model listing included `iterate`, `jev-variants`, `transcript-parser`, and `white-paper`.
- `python3 tools/transcript/find.py --help` at the repo root → exit 0.
- `test ! -e plugins` → exit 0. `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json` plugin names are `['workflow']`.
- `python3 -m unittest tools/driver/tests/test_check_skills.py tools/driver/tests/test_install_route.py` → 32 tests, OK. The install-route env sets `WORKFLOW_INSTALL_LAB=1`. The suite asserts each `MAINTAINER_SKILLS` name is absent for Claude local, Cursor cloud, OpenCode, and both bootstrap paths, and that Cursor local does not create `~/.cursor/plugins/local/workflow-lab`.
- Live search for `plugins/workflow-lab` and `lab-proposal`, excluding `docs/plans/`, dated `docs/lab/{PROPOSALS,RESEARCH}/` files, and earlier changelog entries → no hits. The `2.10.0` changelog section has neither string.
- Judgement: `docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `docs/design/system-architecture.md`, and `README.md` describe one `workflow` plugin plus maintainer skills at `.claude/skills/`. Invariant 7 reads "Core never depends on maintainer skills". The README lede still said the marketplace was split across a core plugin and a local lab plugin; this close rewrites that sentence so the judgement holds.
- Cursor cloud agents started after the skills were on disk did not list the six. Their skill paths were under `~/.cursor` and the plugin cache, not `/workspace`. Temporary per-skill `.cursor/skills/` symlinks (not committed; removed before this record) also did not appear. Cursor's skill docs say the IDE loads `.claude/skills/` for compatibility. This cloud runtime did not, and the IDE skills panel was not exercised. The design's command is Claude Code, which did load the six.

Departure: `claude -p "/skills"` cannot list skills in this environment. The observable it was meant to prove — Claude loads exactly `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, and `workflow-tuning` as repo-local project skills, and the marketplaces list only `workflow` — holds by the loader trace and slash resolution above.

`artifact_feedback` on the brief and the report: unreachable. No `~/.cache/workflow` binary. `tools/workflow/go.mod` requires go 1.27.1 and this machine has go 1.22.2.

## Closed

Phase 1 outcome holds, with the print-mode departure recorded above.

### Carried

None.

## Phase 2: Runtime units become packages

Refine: Proceed. Commit `f51e6f0`. Six units. 2-01 first. Then 2-02, 2-03, 2-04, and 2-05 alongside. Then 2-06. Phase 1 Carried was none. Coarse check of phases 1–7 found no bounce. `artifact_feedback` unreachable: Workflow MCP tool discovery failed.

Decision 1 gate passed: `origin/master` contains `docs/plans/12-analytics-dashboard-overhaul.md`.

### 2-01-package-renames

Brief: `docs/plans/13-monorepo-restructure/briefs/2-01-package-renames.md`.
Report: `docs/plans/13-monorepo-restructure/reports/2-01-package-renames.md`.
Worker: Composer (`composer-2.5`), agent `bc-64c761b1-1ff6-5ea0-a68c-29e55e90ba5c`. The harness did not report turns or final context.
Commits: `cff6f64` (rename only, 119 files, 0 insertions, 0 deletions), `c758796` (the unit report). The report is not inside the rename commit because that commit must stay content-free.

Built: `tools/workflow` → `packages/workflow`, `tools/hooklog` → `packages/hooklog`, `tools/quality/criteria.json` and `tools/quality/checks/` → `packages/workflow/catalogue/`. Other `tools/quality/` files stayed.

Surfaces: the brief's owned paths.

Deviations: none in the report. The report lives in a following commit so the rename commit stays empty of content edits.

`artifact_feedback` on this report: not yet called.

### Phase 2

Module-path rewrite (Decision 1 rebase protocol), from repo root:

```bash
find packages/workflow -type f \( -name '*.go' -o -name go.mod \) -exec sed -i 's|github.com/codyhamilton/workflow-plugin/tools/workflow|github.com/codyhamilton/workflow-plugin/packages/workflow|g' {} +
```

Literal rewrites the path units applied beside that command, for the same rebase protocol:

- `tools/hooklog` → `packages/hooklog`
- `tools/workflow` → `packages/workflow` in `bin/workflow`, release scripts, and test working directories
- Catalogue reads move from `tools/quality/{criteria.json,checks}` to `packages/workflow/catalogue`. In `tools/quality` that is `ROOT / "packages/workflow/catalogue"`. In `packages/workflow` tests that used `../../../quality`, the relative form is `../../catalogue`.

### 2-02-go-workflow-package

Brief: `docs/plans/13-monorepo-restructure/briefs/2-02-go-workflow-package.md`.
Report: `docs/plans/13-monorepo-restructure/reports/2-02-go-workflow-package.md`.
Worker: Composer (`composer-2.5`), agent `bc-dea90b5f-a9ba-5d0e-b7b4-b96917f37aff`. The harness did not report turns or final context.
Commit: `d647629`, merged fast-forward onto this branch.

Built: module path `github.com/codyhamilton/workflow-plugin/packages/workflow`, internal imports, `bin/workflow` source-build from `packages/workflow`, catalogue and `pricing.json` test paths. `go test ./...` passed with GOTOOLCHAIN unset (auto 1.27.1).

Surfaces: `packages/workflow/**`, `bin/workflow`, this file's rewrite command.

Deviations: tests did not use `GOTOOLCHAIN=local` (the brief allows that when 1.27.1 will not run on the system Go). Catalogue, pricing, and `bin/workflow` edits sit outside the module `sed`.

### 2-03-hooks-and-hooklog

Brief: `docs/plans/13-monorepo-restructure/briefs/2-03-hooks-and-hooklog.md`.
Report: `docs/plans/13-monorepo-restructure/reports/2-03-hooks-and-hooklog.md`.
Worker: Composer (`composer-2.5`), agent `bc-a6e78bcf-5147-5b6f-aec7-6cefbd20a248`. The harness did not report turns or final context.
Commits: `d565791`, plus `a2f71a4` dropping a wrong commit id from the report. Merged.

Built: `hooks/{hooks,codex,cursor}.json`, hooklog README and `cursor-hooks.example.json`, and hooklog tests point at `packages/hooklog`. Hooklog unittest: 36 tests, OK.

Surfaces: `hooks/**`, `packages/hooklog/**`.

Deviations: `test_write_surfaces.py` builds from `packages/workflow`. Cursor command shape was only repointed off `tools/hooklog`.

### 2-04-python-tooling-paths

Brief: `docs/plans/13-monorepo-restructure/briefs/2-04-python-tooling-paths.md` (amended: do not re-edit `bin/workflow`).
Report: `docs/plans/13-monorepo-restructure/reports/2-04-python-tooling-paths.md`.
Worker: Composer (`composer-2.5`), agent `bc-51c3b0f1-b8f0-5c32-afee-f8bf5fde4312`. The harness did not report turns or final context.
Commit: `157401f`, merged. Its `bin/workflow` hunk matched 2-02, so the merge kept 2-02's copy.

Built: `tools/quality` and `tools/jev-variants` import `packages/hooklog` and read `packages/workflow/catalogue`. Release scripts target `packages/workflow` and `packages/hooklog`. Suites: quality 26 OK, jev-variants 43 OK, release 10 OK (Go 1.27.2, `/usr/bin/go` hidden for `test_6_no_go_no_asset`).

Surfaces: `tools/quality/**`, `tools/jev-variants/**`, `tools/release/**`.

Deviations: the worker also edited `bin/workflow`, which 2-02 owns. The brief is amended so a re-dispatch does not touch it.

### 2-05-js-and-node-consumers

Brief: `docs/plans/13-monorepo-restructure/briefs/2-05-js-and-node-consumers.md` (amended: Node version for bare `node --test`).
Report: `docs/plans/13-monorepo-restructure/reports/2-05-js-and-node-consumers.md`.
Worker: Composer (`composer-2.5`), agent `bc-fefc6e2b-b98f-593c-9660-ea15df130249`. The harness did not report turns or final context.
Commit: `ff896ac`, merged.

Built: analytics e2e and hosted setups use `packages/workflow` and `packages/workflow/catalogue`. OpenCode README, `src/index.ts` comments, and `test_hooks.mjs` use `packages/hooklog`. `node --test` on Node v22.23.3: 8 pass. System Node v22.14.0 needs `--experimental-strip-types` for the same 8 pass.

Surfaces: `packages/workflow-analytics/tests/**`, `packages/opencode-workflow-hooks/{src/index.ts,tests/test_hooks.mjs,README.md}`.

Deviations: analytics e2e not run (no `node_modules`). Orchestrator runs it at phase verification.

### 2-06-prose-docs-and-closeout-prep

Brief: `docs/plans/13-monorepo-restructure/briefs/2-06-prose-docs-and-closeout-prep.md`.
Report: `docs/plans/13-monorepo-restructure/reports/2-06-prose-docs-and-closeout-prep.md`.
Worker: Composer (`composer-2.5`), agent `bc-80045534-33ee-55a7-93f1-589d29d47c78`. The harness did not report turns or final context.
Commit: `ac82ca8`.

Built: skill catalogue citations, design docs, README hooklog links, `CHANGELOG.md` `2.11.0` (including the silent-failure note for a pasted `tools/hooklog/spool.sh` path), plugin manifests `2.11.0`.

Surfaces: the brief's owned paths. `.claude/skills/workflow-tuning/reference.md` had no old-path literals and was left unchanged.

Deviations: status `blocked` on the phase search. Two comments outside the owned paths still say `tools/hooklog` and `tools/workflow`. Fixer 2-07 owns them. Earlier changelog entries stay, as the outcome excludes them.

### 2-07-residual-path-comments

Brief: `docs/plans/13-monorepo-restructure/briefs/2-07-residual-path-comments.md`.
Report: `docs/plans/13-monorepo-restructure/reports/2-07-residual-path-comments.md`.
Worker: Composer (`composer-2.5`), agent `bc-794afd78-1b91-5d4c-beec-b8170cea5c06`. The harness did not report turns or final context.
Commit: `6e24d67`.

Built: comments in `packages/workflow/internal/ingest/normalise.go` and `packages/hooklog/hooklog.py` now name `packages/hooklog` and `packages/workflow`. `go test ./internal/ingest/` passed. Hooklog tests: 36 OK.

Surfaces: those two files.

Deviations: none.

`artifact_feedback` on this phase's briefs and reports: unreachable. Workflow MCP tool discovery failed.

### Verification

Closed on this branch at `/workspace` (not merged to master).

- `bin/workflow --version`: temporary `HOME` so `~/.cache/workflow/0.1.0` was empty, `WORKFLOW_RELEASE_URL=http://127.0.0.1:9`, Go 1.27.1 first on `PATH` because the wrapper builds with `GOTOOLCHAIN=local`. Printed `workflow 0.1.0 a1cc5fda6e13`. `bin/VERSION` is `0.1.0`, the same field as before the move. `tools/workflow` is absent; the wrapper builds from `packages/workflow`.
- Hook capture: Claude Code 2.1.302, `claude --plugin-dir /workspace -p …`, exited 1 with `Not logged in`. The session still spooled through `packages/hooklog/spool.sh`. A local `workflow serve` hosted the drain. The ledger has `SessionStart`, `UserPromptSubmit`, `MessageDisplay`, `StopFailure`, and `SessionEnd` for that session. No tool ran, so the session did not emit `PreToolUse`. The `PreToolUse` command in `hooks/hooks.json` (`bash "${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}/packages/hooklog/spool.sh" --harness claude --event PreToolUse`), with `CLAUDE_PLUGIN_ROOT` set to this checkout, wrote that event into the same queue. The hosted drain shipped it. `workflow status`: queued 0, rejected 0, endpoint reachable, exit 0.
- `tools/release/build.sh`: exit 0. `tools/release/dist` has `workflow-linux-amd64`, `workflow-linux-arm64`, `workflow-darwin-amd64`, `workflow-darwin-arm64`. `bin/SHA256SUMS` has those four names. Each binary contains `site/_app/immutable`. Sums were restored afterward so the tree does not keep generated checksums. The release suite's `test_7_build_sh` asserts the same.
- Tests, clean environment (no `WORKFLOW_QUEUE`):
  - `go test ./...` in `packages/workflow`: pass. One earlier `internal/serve` analytics summary failure passed on rerun. A later `cmd/workflow` failure was this shell's leaked `WORKFLOW_QUEUE`; a clean rerun passed (52s).
  - `packages/hooklog` 36 OK; `tools/quality` 26 OK (one suite run failed `test_hook_events_ingest_and_join` 1!=2, then the test and the suite passed); `tools/jev-variants` 43 OK; `tools/driver` 69 OK; `tools/release` 10 OK with `/usr/bin/go` hidden for `test_6_no_go_no_asset`.
  - `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs` on Node v22.23.3: 8 pass.
  - `npm run test:e2e` in `packages/workflow-analytics`: 168 pass. The first run failed `fixture.spec.ts` because conversation rows now include usage columns the fixture omitted. Those columns come from serve, not from this phase's path edits. The fixture lists them, and the suite was re-run green.
- Old paths: `rg` for `tools/workflow`, `tools/hooklog`, `tools/quality/criteria.json`, `tools/quality/checks`, and the path-segment forms, excluding `docs/plans/`, `docs/lab/`, and changelog lines from `## 2.10.0` downward, hits only `CHANGELOG.md` line 9, the new entry's old spool path, which the outcome allows.

Departure: the logged-out Claude turn did not call a tool, so `PreToolUse` was written by that hook's command rather than by a tool call inside the session. `SessionStart` came from the session. Both went through `packages/hooklog/spool.sh` into the queue, and drain to the local serve reported no failure.

## Closed

Phase 2 outcome holds, with the hook-session departure recorded above.

### Carried

None.

## Phase 3: Cursor loads `plugins/yakka` and its hooks fire

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-19d85e57-4a4c-542f-ab1e-1098ffc96187
Start: 2026-10-17T18:38:41Z

Refine skipped. DESIGN.md says Phase 3 is one unit. Brief authored inline: `docs/plans/13-monorepo-restructure/briefs/3-01-cursor-plugin.md`. Phase 2 Carried was none.

`artifact_feedback` on the brief: unreachable. Workflow MCP tool discovery failed.

### 3-01-cursor-plugin

Brief: `docs/plans/13-monorepo-restructure/briefs/3-01-cursor-plugin.md` (amended: bootstrap script stays; it only runs `install.sh`).
Report: `docs/plans/13-monorepo-restructure/reports/3-01-cursor-plugin.md`.
Worker: Composer (`composer-2.5`), agent `bc-3db3eed2-f85f-5998-9108-d0f284279cf2`. The harness did not report turns or final context.
Commits: `4d41202` (rename only), `d010965` (rewrite, scripts, report).

Built: plugin tree at `plugins/yakka`. Both marketplace `source` values are `plugins/yakka`. Cursor commands are `./script/spool.sh` and `./script/prefetch-version.sh`. Claude and Codex commands name `script/spool.sh` and `bin/workflow` under the plugin root. Manifests are `2.12.0`. `bin/VERSION` stays `0.1.0`. Cursor install copies that directory and the install-route test asserts `script/spool.sh` and the manifest hooks file.

Surfaces: the brief's owned paths.

Deviations: `test_surfaces.py` skips the `--version` stub assertion for `packages/hooklog/cursor-hooks.example.json` only. `install.sh` moved plugin-source helpers above `ensure_script_dir`. The bootstrap script was not edited; the brief is amended so a re-dispatch does not edit it.

`artifact_feedback` on the brief and the report: unreachable. Workflow MCP tool discovery failed.

### Verification

Not closed. Checked on this branch at `/workspace`.

- Both marketplace files: plugin name `workflow`, `source` string `plugins/yakka`. `plugins/yakka/.cursor-plugin/plugin.json` exists, `hooks` is `./hooks/cursor.json`, `skills/` and `hooks/cursor.json` exist, `packages/yakka` does not. Manifests are `2.12.0`. `plugins/yakka/bin/VERSION` is `0.1.0`.
- Every command in `plugins/yakka/hooks/cursor.json` starts with `./script/`. None contains `${CURSOR_PLUGIN_ROOT}`, `tools/hooklog`, or an absolute path. `script/spool.sh` and `script/prefetch-version.sh` exist.
- From cwd `plugins/yakka`, `./script/spool.sh --harness cursor --event sessionStart` with payload `session_id=phase3`, `WORKFLOW_HOOKLOG_KICK=0`, and a temp queue: exit 0, one `*.evt`, envelope `harness=cursor` `event=sessionStart`.
- Claude commands are `bash "${CLAUDE_PLUGIN_ROOT:-$PLUGIN_ROOT}/script/spool.sh" ...` (32). Codex commands are `bash "${PLUGIN_ROOT}/script/spool.sh" --harness codex` (13). None name `packages/` or `tools/`.
- `python3 -m unittest tools/driver/tests/test_install_route.py` → 21 tests, OK. The Cursor local install test asserts the copied tree has `script/spool.sh`, the hooks file named by the manifest, and Claude/Codex commands containing `script/spool.sh` and not `packages/`.
- Cursor CLI `2026.10.16` resolves a plugin `hooks` manifest field via `discoverHooksFromManifest`, and uses `hooks/hooks.json` only when that field is absent. `./hooks/cursor.json` is the file that resolver reads.
- A Cursor session that loads this marketplace entry and fires a hook did not run. `agent -p --plugin-dir plugins/yakka` exits before a session: not logged in, and `agent login` stops on a Cursor credential page. This cloud agent loaded the installed marketplace plugin at commit `70e7258` with `gitPath: "."` and `enabledCapabilities: ["static"]`. That session loaded skills and wrote no queue events. `workflow drain` / `workflow status` were not run, because no session event was produced.

The session clause of the Phase 3 outcome does not hold. No `Workflow-Phase` trailer.

### Re-dispatch verification

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-f5312021-387d-50a9-a137-726a1f40d3a6
Start: 2026-10-17T19:06:00Z

Not closed. The move was left as it is (`4d41202`, `d010965`). Checked again on this branch at `/workspace`.

- Both marketplace files still name `workflow` with `source` `plugins/yakka`. `plugins/yakka/.cursor-plugin/plugin.json` is `2.12.0` and names `./hooks/cursor.json`. `skills/` and that hooks file exist. `packages/yakka` does not. `plugins/yakka/bin/VERSION` is `0.1.0`.
- All 22 commands in `plugins/yakka/hooks/cursor.json` start with `./script/`. None contains `${CURSOR_PLUGIN_ROOT}`, `tools/hooklog`, or an absolute path. `script/spool.sh` and `script/prefetch-version.sh` exist.
- From cwd `plugins/yakka`, `./script/spool.sh --harness cursor --event sessionStart` with payload `session_id=phase3-redispatch`, `WORKFLOW_HOOKLOG_KICK=0`, and a temp queue: exit 0, one `*.evt`, envelope `harness=cursor` `event=sessionStart`.
- `python3 -m unittest tools/driver/tests/test_install_route.py` → 21 tests, OK.
- `artifact_feedback` on the brief and the report: unreachable. Workflow MCP tool discovery failed (`namespaceStatus: error`).

A Cursor session that loads `plugins/yakka` and fires a hook did not run.

- Cursor CLI `2026.10.16-e3cb207` is installed at `~/.local/bin/agent`. `agent status` is `Not logged in`. `CURSOR_API_KEY` is unset. Chrome has no Cursor cookies.
- `agent -p --trust --plugin-dir /workspace/plugins/yakka` exits 1 before a session: `Authentication required. Please run 'agent login' first, or set CURSOR_API_KEY environment variable.`
- `NO_OPEN_BROWSER=1 agent login` prints `https://cursor.com/loginDeepControl?...&mode=login&redirectTarget=cli` and waits. Nothing on this machine can complete that page.
- This cloud agent still resolved the account marketplace plugin `workflow` with `gitPath` `.`, commit `70e725836a4dde380501428bcbf4cbb61e2b7036`, and `enabledCapabilities` `["static"]`. Skills only. Hooks are not enabled. That load is not `plugins/yakka`.

`workflow drain` and `workflow status` were not run. No session event was produced.

The session clause of the Phase 3 outcome does not hold. No `Workflow-Phase` trailer.

Unblock: authenticate the Cursor CLI on a checkout of this branch, then re-dispatch this verification. Do not redo the move.

1. `curl https://cursor.com/install -fsS | bash` if `agent` is missing.
2. Either export `CURSOR_API_KEY` from Cursor Dashboard → API Keys, or run `NO_OPEN_BROWSER=1 agent login` and finish the `loginDeepControl` link in a browser signed into that Cursor account.
3. `agent status` must show logged in.
4. Start a session that loads this tree: `agent -p --trust --plugin-dir "$(pwd)/plugins/yakka" --output-format text "List the workflow skills you loaded and stop."`
5. A hook command under `plugins/yakka/script/` (`./script/spool.sh` or `./script/prefetch-version.sh`) must run, the event must land in the queue, `workflow drain` to a local `workflow serve` must ship it, and `workflow status` must report no failure.

This cloud agent cannot be that proof until the installed marketplace plugin resolves `plugins/yakka` with hooks enabled. `--plugin-dir` is the session that can load the branch before merge.

### Close

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-58053383-6150-52b5-9af5-51ae159c3b0c
Start: 2026-10-17T22:56:00Z

The user overrode the session blocker, verbatim: "no, just continue with the plan until completion and don't block on testing it, you won't be able to. that has to be manual."

The logged-in Cursor session check is carried as manual verification. This close did not run `agent login` and does not claim a Cursor session loaded `plugins/yakka` or fired a hook. The plugin move was left as it is (`4d41202`, `d010965`).

Tree checks, reconfirmed on this branch at `/workspace`:

- Both marketplace files name `workflow` with `source` `plugins/yakka`. `plugins/yakka/.cursor-plugin/plugin.json` is `2.12.0` and names `./hooks/cursor.json`. `skills/` and that hooks file exist. `packages/yakka` does not. `plugins/yakka/bin/VERSION` is `0.1.0`.
- All 22 commands in `plugins/yakka/hooks/cursor.json` start with `./script/`. None contains `${CURSOR_PLUGIN_ROOT}`, `tools/hooklog`, or an absolute path. `script/spool.sh` and `script/prefetch-version.sh` exist.
- From cwd `plugins/yakka`, `./script/spool.sh --harness cursor --event sessionStart` with payload `session_id=phase3-close`, `WORKFLOW_HOOKLOG_KICK=0`, and a temp queue: exit 0, one `*.evt`, envelope `harness=cursor` `event=sessionStart`.
- `python3 -m unittest tools/driver/tests/test_install_route.py` → 21 tests, OK.
- `artifact_feedback` on the brief and the report: unreachable. Workflow MCP tool discovery failed (`namespaceStatus: error`).

## Closed

Phase 3 outcome holds for the tree checks above. The logged-in Cursor session check — loading `plugins/yakka`, a `./script/...` hook firing, the event landing in the queue, `workflow drain` to a local `workflow serve`, and `workflow status` reporting no failure — is manual verification, carried below.

### Carried

1. Logged-in Cursor session check, manual, per the user instruction above. On a checkout of this branch: install the marketplace entry, open a Cursor session that loads `plugins/yakka`, confirm a `./script/...` hook fires and the event lands in the queue, then `workflow drain` to a local `workflow serve` ships it and `workflow status` reports no failure.

## Phase 4: The layout contract is stated and enforced

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-83baacb3-016f-585e-a573-6349677e0232
Start: 2026-10-17T23:06:10Z

Refine skipped. DESIGN.md says Phase 4 is one worker. Brief authored inline: `docs/plans/13-monorepo-restructure/briefs/4-01-layout-contract.md`.

Phase 3 Carried item 1 is a logged-in Cursor session check. It does not touch a Phase 4 contract, boundary, or outcome, so it is not absorbed and it does not bounce the phase. It stays carried for the next refinement. This phase does not run it.

`artifact_feedback` on the brief: unreachable. Workflow MCP tool discovery failed (`namespaceStatus: error`).

### 4-01-layout-contract

Brief: `docs/plans/13-monorepo-restructure/briefs/4-01-layout-contract.md`.
Report: `docs/plans/13-monorepo-restructure/reports/4-01-layout-contract.md`.
Worker: Composer (`composer-2.5`), agent `bc-359b70bd-039b-57c8-94fd-cc763c29dee9`. The harness did not report turns or final context.
Commit: `eccbb91`.

Built: `tools/release/test_layout.py` scans the repo and fails six fixtures, each naming the file and the offending path. Package READMEs carry **Consumers**, **Build**, **Test**, **Release**. `tools/README.md` and `packages/README.md` index every child directory. The OpenCode flush default and `tools/driver/jev_signal_log.py` both resolve `${XDG_STATE_HOME:-~/.local/state}/workflow/jev-signal-log.jsonl`, overridable by `WORKFLOW_JEV_SIGNAL_LOG`. The component map and the distribution Layout section state `plugins/yakka`, `packages/`, and `tools/`.

Surfaces: the brief's owned paths.

Deviations: the worker exempted `packages/*/internal/serve/site/` because the placeholder HTML named `tools/release/build.sh` and that file was outside the brief. That exemption is not in the package contract. Commit `9b988ab` removes it and rewords the placeholder so the `workflow-analytics-placeholder` marker stays and the sentence no longer contains a `tools/` path. The worker also duplicated the path resolver instead of importing the OpenCode module, which the brief required.

`artifact_feedback` on the brief and the report: unreachable. Workflow MCP tool discovery failed (`namespaceStatus: error`).

### Verification

Closed on this branch at `/workspace` (not merged to master).

- `python3 -m unittest tools/release/test_layout.py` → 7 tests, OK. The repo scan is clean. The six fixtures fail on a hook command into `tools/`, a package file containing `tools/driver/x`, a skill file containing `.claude/skills/`, a package with no README, a marketplace with two plugins, and a Cursor command using `${CURSOR_PLUGIN_ROOT}`. Each assertion checks the file and the offending path.
- `python3 -m unittest discover -s tools/release -p 'test_*.py' -v` loads those seven cases in the same run as `test_release`. The layout cases pass there.
- `python3 -m unittest packages/opencode-workflow-hooks/tests/test_batch.py tools/driver/tests/test_jev_signal_log.py` → 9 tests, OK. With the override unset, both resolvers return `~/.local/state/workflow/jev-signal-log.jsonl`. `XDG_STATE_HOME` and `WORKFLOW_JEV_SIGNAL_LOG` move both to the same path. The default does not contain `tools/driver`.
- `tools/README.md` names `cloud-env`, `driver`, `interception`, `jev-variants`, `quality`, `release`, and `transcript`. `packages/README.md` names `hooklog`, `opencode-workflow-hooks`, `workflow`, and `workflow-analytics`. Those are the directories on disk.
- Judgement: `docs/ARCHITECTURE.md`'s component map shows `plugins/yakka` as the plugin install root, `packages/`, `tools/`, and maintainer skills at `.claude/skills/`. `docs/design/05-distribution.md`'s Layout section states those three trees. The remaining "Not in this round" bullets are pinned copies and registration; the monorepo deferral is already gone.
- With Go 1.27.1 at `~/.local/go/bin/go`, `test_6_no_go_no_asset`, `test_8_bash32_lint`, and `test_10_workflow_bin` pass. `test_10` expects `WORKFLOW_ROOT` to be `plugins/yakka`. `test_1_clean_cache_build` fails before a compile: the wrapper looks for `plugins/yakka/../packages/workflow/go.mod`, and the module is at `plugins/yakka/../../packages/workflow`. That failure is carried. The four-binary `build.sh` test was not re-run.

## Closed

Phase 4 outcome holds. The layout check passes, its six fixtures fail with the file and the path named, and the signal-log default matches Assumption 11. The logged-in Cursor session check is not a Phase 4 outcome; it stays carried.

### Carried

1. Logged-in Cursor session check, still manual, from Phase 3. On a checkout of this branch: install the marketplace entry, open a Cursor session that loads `plugins/yakka`, confirm a `./script/...` hook fires and the event lands in the queue, then `workflow drain` to a local `workflow serve` ships it and `workflow status` reports no failure.
2. Root `README.md` still documents the signal log as `tools/driver/.jev-signal-log.jsonl`. The package and `tools/driver` no longer default there.
3. `plugins/yakka/bin/workflow` step 4 joins `$ROOT/../packages/workflow`. `ROOT` is the plugin directory, so the source build does not see the module. `tools/release/test_release.py` `test_1_clean_cache_build` fails with "no release asset and no Go toolchain (or module source)". The module is at `$ROOT/../../packages/workflow`. Phase 5 owns that wrapper.
