# <Title>

## Intent

User request, verbatim:

> <the full prompt, or the exact relevant portion>

## Problem

<what is wrong or missing, and why it matters now>

## Solution Shape

<what exists after this change that does not exist now, in a paragraph>

### Domain: <name>

- Owns: <the source of truth or surfaces this domain owns>
- Contract: <API, schema, event, state model, file format — precise enough for a brief to cite>
- Non-goals: <what this domain does not own or solve>

### Domain: <name>

- Owns:
- Contract:
- Non-goals:

## Architectural Implications

- <stable doc or assumption affected>
- <sequencing or downstream implication>
- <boundary or ownership change>

## Decisions

<Scope-shaping decisions and the answer received, or "None". Interactive sessions also have the turn record in PROVENANCE.md.>

## Assumption Ledger

<Headless only: one entry per question that would otherwise have been asked. Interactive: "None — see PROVENANCE.md".>

### Assumption N

- Question:
- Answer chosen:
- Rationale:
- If wrong:

## Open Questions

- <what must be resolved, and what it blocks — or "None">

## Phases

<Ordered. The count is fixed at sign-off. A phase closes when its outcome is provably true. `refine` adds a Units list under a phase when it refines it; `execute` records the phase's outcome and carried items in IMPLEMENTATION.md.>

### Phase 1 — <name>

- Outcome: <entry point → action → observable result | observable statement>
- Surfaces: <files, modules, interfaces this phase changes>
- Approach: known | open
- Depends on: <earlier phase, or nothing>

### Phase 2 — <name>

- Outcome:
- Surfaces:
- Approach:
- Depends on:

## Provenance Notes

<rationale, tradeoffs, and rejected alternatives a future reader would otherwise rediscover>
