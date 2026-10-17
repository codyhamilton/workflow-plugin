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
