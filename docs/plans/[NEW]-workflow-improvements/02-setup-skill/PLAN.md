# 02 — Setup Skill: Bootstrap Architecture and Roadmap Docs

## Intent

User request, verbatim (from parent):

> A setup command for the workflow. Initial setup requires ensuring a docs folder is present, and we have our docs for "architecture plus intent". This could be called architecture.md/roadmap.md? consider. Regardless, the setup command has to orchestrate a comprehensive review, look for existing docs, consolidate. It should ask the user if it should do this. If gaps, it should take the user on a guided conversation, asking a series of high level then narrowing questions to come up with architecture and roadmap views, which it documents.

## Why This Plan Exists

The planning skill reads `docs/ARCHITECTURE.md` and `docs/OVERVIEW.md` at the start of every planning session. When these docs are absent or thin, planning must guess or ask the user repeatedly about the same context. The setup skill eliminates this by proactively creating the docs before planning starts.

## Scope

Create a new skill, `workflow:setup`, that:
1. Checks for existing docs (ARCHITECTURE.md, OVERVIEW.md, ROADMAP.md, docs/design/*)
2. Asks the user for permission to proceed
3. Conducts a guided three-round conversation if docs are missing
4. Writes `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` with specified sections
5. Consolidates partial existing docs rather than creating alongside them

The skill is standalone and can be invoked before planning. It has no code coupling with planning; the dependency is filesystem presence (planning reads the docs setup creates).

## Architectural Implications

- **New skill**: Expands the four-skill set to five (planning, plan-execution, comprehensive-review, setup, workflow-tuning)
- **Stable doc creation**: setup is the only skill that creates stable docs (planning updates them, but doesn't create from scratch)
- **No coupling**: setup and planning are independent; connection is through filesystem
- **Parent program sequencing**: setup enables planning on new repos without degradation

## Intent Validation

**Key decisions clarified:**
- Setup is invoked explicitly by the user; not triggered automatically
- Setup creates `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` (not other names)
- If partial docs exist, consolidate; do not create alongside
- Guided conversation is three rounds: broad purpose → components → ownership/current state/constraints

## Open Questions

None.

## Execution Phases

1. Create `skills/setup/SKILL.md` — full skill with six phases: reconnaissance, assessment/permission, consolidation, guided conversation, write docs, planning hook
2. Modify `skills/planning/SKILL.md` — add note to step 2 suggesting setup when stable docs are absent
3. Test: On a repo with no docs/, invoke setup and verify it creates ARCHITECTURE.md and ROADMAP.md
4. Test: After setup completes, invoke planning and confirm it reads the new docs

## Acceptance Criteria

- **Skill exists**: skills/setup/SKILL.md has correct name and description frontmatter
- **Reconnaissance works**: Agent reads existing docs before speaking
- **Permission gate**: Agent presents findings and asks "Shall I proceed?"
- **Guided conversation**: Agent asks one question per round, waits for answer before next round (not all at once)
- **Docs created**: docs/ARCHITECTURE.md with Purpose/Intent, Stack, Component Map, Invariants, Key Data Flows, Stable References sections
- **Roadmap created**: docs/ROADMAP.md with Current State, Active Work, Planned, Not In Scope sections
- **Consolidation**: If partial docs exist, content is merged (not duplicated)
- **Planning integration**: After setup, planning reads the new docs without gaps

## Provenance Notes

The guided conversation is structured to go from high-level intent (purpose, problem solved, success definition) to specific structure (components, ownership, constraints). This ordering prevents premature commitment to architecture before intent is clear. The agent waits for responses between rounds rather than asking all questions at once, making the conversation feel natural and giving users time to think.

Depends on provenance capture (01) so that this planning session and its conversation can be recorded in PROVENANCE.md, providing an example of setup's behavior.
