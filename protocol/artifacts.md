# Workflow Artifact Conventions

Portable rules for plan/execute/review artifacts. These conventions are harness-agnostic — they do not depend on Cursor, Claude Code, or Codex model choices. Model recommendations live in `protocol/models.yaml`.

## Stable docs (repo-level)

| Artifact | Role |
|----------|------|
| `docs/OVERVIEW.md` | One short paragraph: what the project does, who uses it, what success looks like |
| `docs/ARCHITECTURE.md` | Concept map, stack, invariants, key data flows |
| `docs/ROADMAP.md` | Current state, active work, planned, not-in-scope |
| `docs/design/*` | Stable design-intent docs when needed |

## Plan artifacts (under `docs/plans/`)

| Artifact | Role |
|----------|------|
| `PLAN.md` | Scoped change: intent, implications, sequence, observable acceptance |
| `DESIGN.md` | Optional. Only when target shape or cross-implementor contracts need reification |
| `PROVENANCE.md` | Verbatim initial request, Q&A substance, agent decisions |
| `ROADMAP.md` | Schedule/status for linked parent programs |
| `IMPLEMENTATION.md` | What was built, deviations, session ID |
| `REVIEW.md` | Independent review outcome, findings, residual risks |
| `STATUS.md` | Optional. Partial or paused execution |

## Folder conventions

- Open parent programs: `[NEW]-<program>/`
- Implemented parent programs: numeric prefix (`01-`, `02-`, …)
- Child plans: numeric prefixes matching roadmap order
- Completion evidence stays in the plan folder; do not use folder moves as the primary completion signal

## Intent capture

- User intent in `PLAN.md` `## Intent` is verbatim, never paraphrased
- `PROVENANCE.md` records substance in the user's words; strip filler; omit credentials and large dumps
- Write provenance progressively (create on first request, append each turn, append decisions before finalize)

## Execution contracts

- Execute only from an existing plan
- Mandatory independent review after planned execution
- `ROADMAP.md` is the authority for sequencing among linked plans
- Contracts may come from `DESIGN.md`, stable docs, or `PLAN.md`; if too weak for delegation, return to plan

## Documentation economy

Prefer the minimum durable set that helps agents reason beyond what the code already shows. Do not create documentation cascades that mostly restate the code. `DESIGN.md` is optional and earns its keep only when it reifies contracts or target shape.
