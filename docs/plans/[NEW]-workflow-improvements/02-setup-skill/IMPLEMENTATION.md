# Implementation: 02 — Setup Skill

## What Was Built

Two file changes: new setup skill and planning skill modification.

### Files Changed

**`skills/setup/SKILL.md`** (new)
Full six-phase setup skill:
- Phase 1: Reconnaissance — reads all existing docs and source tree before speaking
- Phase 2: Permission gate — presents findings summary, asks "Shall I proceed?" Consolidation does not start until user confirms.
- Phase 3: Consolidation — reads partial docs, identifies accurate vs. stale vs. missing content. Contradictions with observed code are flagged to user before Phase 4.
- Phase 4: Guided conversation — three rounds, one question per round, waits for response. Broad purpose → components → current state/constraints.
- Phase 5: Write docs — creates `docs/OVERVIEW.md` (one paragraph), `docs/ARCHITECTURE.md` (six sections), `docs/ROADMAP.md` (four sections). Partial content merged, not duplicated.
- Phase 6: Planning hook — tells user stable docs are in place and planning can begin.

**`skills/planning/SKILL.md`** (modified)
Step 2 now suggests `/workflow:setup` when stable docs are absent or thin, with the rationale that planning on a repo with no stable docs produces degraded plans.

## Deviations from Plan

**OVERVIEW.md added to scope.** The plan specified ARCHITECTURE.md + ROADMAP.md only, but the planning skill reads OVERVIEW.md at step 2. Without OVERVIEW.md, setup would produce a broken loop: planning suggests setup, setup runs, planning still reports missing stable docs. Setup now creates OVERVIEW.md as a mandatory one-paragraph output. This extends scope by one file but is required for the acceptance criterion "planning reads the new docs without gaps."

## Tradeoffs

**Three-round fixed conversation vs. adaptive.** A fixed three-round structure trades richness for reliability. Agents asked to "ask as many questions as needed" tend to over-question. Three rounds is enough for a usable ARCHITECTURE.md on any moderately understood project. Agents can ask follow-ups within the rules if a response is genuinely ambiguous.

**Stale content flagging.** Phase 3 identifies contradictions but the fix is to flag them, not to resolve them silently. This keeps the agent honest — it surfaces what it found rather than making a call the user should make.
