# 01 — Provenance Capture: Transcript-Based Intent Recording

## Intent

User request, verbatim (from parent):

> We need to improve the way we record user intent. We should capture user inputs into a doc as provenance. Specific user inputs (sanitised). These could be pulled from chat transcripts, the harnesses we support all create these. provenance should be exact user inputs (initial/followups/questions responses) along with summary of agent relevant context, e.g. the questions agent asked or a brief of what the agent decided based on that

## Why This Plan Exists

PLAN.md captures verbatim user intent in the `## Intent` section by agent convention, but followup responses, question turns, and agent decision rationale are not recorded. Later agents must reconstruct intent from agent memory rather than transcript evidence. This plan adds PROVENANCE.md as a durable transcript-based provenance document.

## Scope

Add PROVENANCE.md template and progressive writing guidance to the planning skill. The approach is simple: the agent writes to PROVENANCE.md at the moment each input arrives, not retroactively from a transcript.

The planning skill is modified to:
1. Create the plan directory and write the initial PROVENANCE.md immediately after capturing the verbatim request — before reading stable docs or asking any questions
2. Append each Q&A turn to PROVENANCE.md as soon as the user responds, before continuing
3. Append agent decisions at the point they are made

This treats PROVENANCE.md as a running log, not a post-hoc extraction. Writing immediately prevents information from going stale in context before it is recorded. Each write also acts as a progressive summarisation checkpoint — a natural refresh point for both the agent and future readers.

**What to record vs. what to omit**: The goal is intent in the user's words, not a full transcript. The agent should extract the substance of what the user said — the decision, preference, or direction — while stripping tone, filler, conversational asides, and anything not intended for persistence. If a user's response is mostly affirmation with a refinement buried in it, record the refinement. Do not copy everything said verbatim unless the exact phrasing carries meaningful intent that a paraphrase would lose.

PROVENANCE.md is a new artifact written alongside PLAN.md in every plan folder.

## Architectural Implications

- **New artifact**: PROVENANCE.md added to all plan folders (parent and child)
- **Progressive writing model**: Provenance is written incrementally during the planning conversation, not extracted after the fact
- **No external dependencies**: No JSONL transcript parsing or session identification required
- **No breaking change**: PLAN.md `## Intent` section remains; PROVENANCE.md is additive
- **Foundational for evals**: Faithful fixture corpus depends on captured intent for eval scenario definition

## Intent Validation

No scope-shaping questions. The design is deliberately simple: write what the agent just received, when the agent receives it. No transcript mechanics, no extraction step, no session identification.

## Open Questions

None.

## Execution Phases

1. Create `skills/planning/templates/PROVENANCE.md` — template with sections: Session, Initial Request, Planning Conversation, Agent Decisions. Structure supports progressive appending (each section can grow independently).
2. Modify `skills/planning/SKILL.md` — add three provenance writing instructions to the Workflow section:
   - After step 1 (capture verbatim request): create plan directory immediately and write PROVENANCE.md with the Session header and Initial Request section. Do this before reading stable docs.
   - After each Q&A turn: append the turn to the Planning Conversation section immediately upon receiving the user's response, before proceeding.
   - Before finalizing the plan: append the Agent Decisions section.
3. Modify `skills/planning/templates/PLAN.md` — update `## Provenance Notes` to reference PROVENANCE.md as the companion transcript record.
4. Test: Run planning on a new work item, verify PROVENANCE.md appears early and grows correctly across question turns.

## Acceptance Criteria

- **Template exists**: skills/planning/templates/PROVENANCE.md has the four sections and supports progressive appending
- **Early creation**: PROVENANCE.md is written to disk before the agent reads any stable docs (not at the end)
- **Turn-by-turn recording**: Each Q&A turn appears in PROVENANCE.md immediately after the user responds, not batched at the end
- **Agent decisions recorded**: Final agent decisions section shows what was decided and why
- **Intent over transcript**: Recorded content captures the user's decision or direction in their words, not a verbatim copy of everything said. Tone, filler, and conversational asides are stripped.
- **Intentional persistence only**: Content not intended for permanence (casual remarks, throwaway questions) is omitted. If in doubt, omit.
- **No credentials leak**: Agent does not copy API keys, tokens, or large file dumps into provenance

## Provenance Notes

This is the foundational child plan. The progressive writing model is simpler than transcript extraction and more reliable: the agent controls what it writes rather than parsing an external log. The PROVENANCE.md written during this plan's execution is itself an example of the correct output shape.
