# 01 — Provenance Capture: Transcript-Based Intent Recording

## Intent

User request, verbatim (from parent):

> We need to improve the way we record user intent. We should capture user inputs into a doc as provenance. Specific user inputs (sanitised). These could be pulled from chat transcripts, the harnesses we support all create these. provenance should be exact user inputs (initial/followups/questions responses) along with summary of agent relevant context, e.g. the questions agent asked or a brief of what the agent decided based on that

## Why This Plan Exists

PLAN.md captures verbatim user intent in the `## Intent` section by agent convention, but followup responses, question turns, and agent decision rationale are not recorded. Later agents must reconstruct intent from agent memory rather than transcript evidence. This plan adds PROVENANCE.md as a durable transcript-based provenance document.

## Scope

Add PROVENANCE.md template and transcript extraction to the planning skill. The agent will:
1. Write the verbatim initial request in PROVENANCE.md
2. Extract conversation turns from the session JSONL transcript
3. Record agent decisions based on user responses
4. Sanitize credentials and large file dumps

PROVENANCE.md is a new artifact written alongside PLAN.md in every plan folder.

## Architectural Implications

- **New artifact**: PROVENANCE.md added to all plan folders (parent and child)
- **Stable behavior change**: planning skill workflow gains a provenance extraction step after capturing verbatim intent
- **No breaking change**: PLAN.md `## Intent` section remains; PROVENANCE.md is additive
- **Dependency on transcripts**: Relies on Claude Code session JSONL files at `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`
- **Foundational for evals**: Faithful fixture corpus depends on captured intent for eval scenario definition

## Intent Validation

No scope-shaping questions. The design is straightforward: a new template file, a transcript extraction step in the planning skill, and sanitization rules for the agent to apply.

## Open Questions

None.

## Execution Phases

1. Create `skills/planning/templates/PROVENANCE.md` — template for the provenance document
2. Modify `skills/planning/SKILL.md` — add provenance extraction step to the Workflow section (step 2a, right after verbatim intent capture)
3. Modify `skills/planning/templates/PLAN.md` — update `## Provenance Notes` to reference PROVENANCE.md
4. Test: Create a new plan and verify PROVENANCE.md appears with correct content

## Acceptance Criteria

- **Template exists**: skills/planning/templates/PROVENANCE.md contains the required sections (Session, Initial Request, Planning Conversation, Agent Decisions)
- **Extraction works**: After running planning, PROVENANCE.md appears in the plan folder with correct content
- **No credentials leak**: No API keys, tokens, or credential patterns appear in the output
- **Transcript filtering**: Only real user messages extracted (not meta, not sidechain, not slash commands)
- **Agent decisions recorded**: Conversation turns show what agent asked and what user answered

## Provenance Notes

This is the foundational child plan. Its completion enables better fixtures for the eval system (child plan 03). The transcript extraction procedure uses `jq` to filter the session JSONL; the exact filter syntax is included in the SKILL.md modification to ensure agents can replicate it reliably.

Sanitization rules are documented in the skill so the agent knows to truncate file dumps and redact credentials.
