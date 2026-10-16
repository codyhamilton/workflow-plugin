# Provenance: Event recording gaps — Codex apply_patch writes and Codex plugin upgrades

Interactive posture only. Headless runs carry intent, the assumption ledger, and decisions in `DESIGN.md` alone.

## Session

- Session: Initial design (October 6, 2026)
- Timestamp: 2026-10-05T15:31:51Z (2026-10-06 01:31 AEST)
- CWD: /home/codyh/workspace/workflow-plugin (HEAD `95f41f7`)

## Initial Request (verbatim)

> Check daily and make sure each harness is properly reporting events and designs and briefs and executions. If not backfill the artifacts where possible and investigate the root cause, create a design to fix and escalate for approval to fix.

## Origin

- The request is the standing Workflow Event Watch routine. The daily check found the two defects after the CHM/WSM handoff. Cody asked on 2026-10-06 for the fix design, escalated for approval.
- The invoker passed verified ground facts (Codex `apply_patch` uses `tool_input.command`, 1308/1308 facts, Codex version count of 0, the 2.9.1 directory wiped at about 13:01 AEST on 2026-10-05). It asked for two phases, with the restart being an operator step, and set the posture: interactive, checkpoint held, no build, no push, no restart.

## Design Conversation

None. No turn with Cody has happened yet. The checkpoint is held, and `DESIGN.md` Open Questions lists what Cody is asked to decide.

## Agent Decisions

- **Plan folder**: `docs/plans/11-event-recording-gaps/`. The slug covers both defects; the second is about hook liveness, not artifact versioning. Rationale: `10-workflow-analytics` was the highest existing number.
- **Scope**: the two recording defects only. Backfill is a non-goal. Rationale: the invoker's direction, and backfill needs quality on 8765, which is down.
- **Phase 2 flag**: proposed as Open. Rationale: Codex auto-upgrades on session start (openai/codex#17425), so there is no upgrade step this repo controls. The upstream refresh (openai/codex#38703) is unverified against `codex-cli 0.160.0`. Cody may make it Known.
- **artifact_feedback**: not called. Rationale: the quality service is reported down, and this run has no `artifact_feedback` tool.
- **Files left untracked**: nothing staged or committed, so Cody can approve before commit.
