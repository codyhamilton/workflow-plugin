# [NEW] Workflow Improvements — Roadmap

## Parent Program Overview

Three linked child plans to improve the workflow-plugin by adding:
1. Provenance capture (transcript-based intent recording)
2. Setup skill (bootstrap missing stable docs)
3. Eval system (variant testing and prompt validation)

These are foundational improvements that enable reliable iteration on the workflow itself.

## Status: In Progress

Child 01 complete. Child 02 next.

## Child Plans

| Order | Plan | Purpose | Status | Dependencies |
|-------|------|---------|--------|--------------|
| 1 | 01-provenance-capture | Add PROVENANCE.md template and progressive writing guidance to planning skill | complete | none |
| 2 | 02-setup-skill | Create setup skill for bootstrapping docs/ARCHITECTURE.md + docs/ROADMAP.md | pending | 01 (provenance) |
| 3 | 03-eval-system | Extend workflow-tuning with e2e eval capability: scenarios, cost+quality lenses, results format | pending | 01 + 02 (provenance + setup for fixtures) |

## Sequencing Rationale

**01 first**: Provenance is the smallest scope and is foundational. Every plan written after 01 completes will have PROVENANCE.md, so 02 and 03 will benefit from better fixtures.

**02 second**: Setup is a new skill and builds on provenance. The setup skill can be tested using the workflow's own planning → execution → review loop.

**03 third**: Evals depend on having provenance (for faithful fixtures) and setup scenarios (to test against). This is the most complex of the three and benefits from the others being in place.

## Current Blockers

None. All three plans are ready to begin when execution starts.

## Dogfooding Notes

This parent program and its child plans are being written and executed using the workflow-plugin's own planning, execution, and review tools. This serves as:
- Proof that the workflow can handle self-modification
- Source of real plan artifacts (PLAN.md, PROVENANCE.md, IMPLEMENTATION.md, REVIEW.md) that become eval fixtures
- Validation that the setup skill produces usable stable docs

After this program completes, `docs/plans/[NEW]-workflow-improvements/01-*/` folders will be archived as `01-` provenance and used as reference examples and eval fixtures.
