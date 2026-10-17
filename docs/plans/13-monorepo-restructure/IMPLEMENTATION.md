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
