# Implementation

Tool: Cursor cloud agent
Run: https://cursor.com/agents/bc-6567db80-03ab-533d-8a33-89e515bdc24d
Start: 2026-10-17T17:15:00Z

## Phase 1: Lab collapses into maintainer skills

Refine skipped. DESIGN.md says Phase 1 is one worker. Assumption 9's check, which that skipped refine would have made, is settled in the brief: Cursor's current skills doc loads `.claude/skills/` for compatibility, so this phase adds no `.cursor/skills/` symlinks.

### 1-01-lab-collapse

Brief: `docs/plans/13-monorepo-restructure/briefs/1-01-lab-collapse.md`. Not yet dispatched.

`artifact_feedback` on the brief: unreachable. `bin/workflow` has no cached binary, the v0.1.0 release asset returns 404, and source build stops because `go.mod` requires go 1.27.1 while this machine has go 1.22.2 (`GOTOOLCHAIN=local`).
