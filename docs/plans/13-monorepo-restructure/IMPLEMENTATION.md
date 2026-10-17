# Implementation

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-6567db80-03ab-533d-8a33-89e515bdc24d
Start: 2026-10-17T17:15:00Z

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

Not closed. One outcome command did not produce its required result.

- `test ! -e plugins` → exit 0. `plugins/` is gone.
- `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json` plugin names → `['workflow']`.
- `.claude/skills/` is exactly the six names. Each `SKILL.md` `name:` matches the directory.
- `python3 tools/transcript/find.py --help` at the repo root → exit 0.
- `python3 -m unittest tools/driver/tests/test_check_skills.py tools/driver/tests/test_install_route.py` → 32 tests, OK. `WORKFLOW_INSTALL_LAB=1` is in the shared test env. Claude local, Cursor cloud, OpenCode, and both bootstrap tests assert each `MAINTAINER_SKILLS` name is absent. Cursor local (`test_interactive_cursor_core_install_ignores_install_lab`) asserts `~/.cursor/plugins/local/workflow-lab` is not created.
- Live search for `plugins/workflow-lab` and `lab-proposal`, excluding `docs/plans/`, dated `docs/lab/{PROPOSALS,RESEARCH}/` files, and earlier changelog entries → no hits. The `2.10.0` changelog section has neither string.
- Judgement: `docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `docs/design/system-architecture.md`, and `README.md` describe one `workflow` plugin plus maintainer skills at `.claude/skills/`. Invariant 7 reads "Core never depends on maintainer skills".
- `claude -p "/skills"` at the repo root, Claude Code 2.1.302, stdout: `/skills isn't available in this environment.` Exit 0. It did not list the six project skills. Print mode does not register that slash command (the binary's fallback for an unregistered slash command). An interactive start stops on the first-run theme picker, so the menu was not reached. The design says this command, on master, lists exactly those six names. That result is not in hand.

## Not closed

Phase 1 has no `Workflow-Phase: 13-monorepo-restructure:1` trailer. The remaining check is `claude -p "/skills"` listing exactly `iterate`, `jev-variants`, `setup`, `transcript-parser`, `white-paper`, `workflow-tuning`.
