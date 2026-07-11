# Execute — Reference

Consumers: `workflow-tuning`, anyone revising this skill, and local runs that need harness-specific mechanics. Not loaded during normal cloud execution — the skill body is self-sufficient without it.

## Per-harness model-selection hints

Starting allocations, not settled ones — treat as configuration to tune, not doctrine. Revisit when usage data justifies a change.

- **Cursor**: use Composer-2.5 except where specifically told to use another model.
- **Claude Code**: use Haiku for research and small changes, Sonnet for large changes. Do not use Opus except where directed.
- **Codex**: use GPT5.4 high for most work, mini for exploration, xhigh for review. Do not use 5.5.

Rationale (persuading-why, kept here rather than the skill body): several small models with clearly bounded scope tend to be cheaper and faster in aggregate than one larger agent carrying the whole task, provided the slices are genuinely independent — see Sizing Method in `SKILL.md` for how to tell whether they are.

## Per-harness session/run-ID capture formulas

Best-effort, for local runs where the `transcript-parser` skill needs to locate this session's transcript after execution completes. In a cloud/PR flow, record the session URL or run ID instead — there is no local transcript to parse.

- **opencode**: read `OPENCODE_RUN_ID` from the environment. If `OPENCODE` is set, use it as the session ID directly.
- **Claude Code**: find the most recently modified `.jsonl` in `~/.claude/projects/{project-hash}/` and read `sessionId` from any line. Project hash = working directory path with `/` replaced by `-`, prefixed with `-`.
- **Cursor**: find the most recently modified directory under `~/.cursor/projects/{project-name}/agent-transcripts/` and use its name as the session ID.

## Historical note

Earlier revisions of this skill synced status into a parent `ROADMAP.md`, gated execution on whether the work sat inside an open `[NEW]-` parent program, and wrote `STATUS.md` as a completion artifact for partial/paused runs. All three were removed in the pivot-consolidate-focus revision: the backlog taxonomy is gone, and status now lives only in the PR and the tracker (see `docs/plans/02-pivot-consolidate-focus/PLAN.md` and `DESIGN.md`'s Artifact Taxonomy). Partial or paused state is recovered from progressive `IMPLEMENTATION.md` alone.
