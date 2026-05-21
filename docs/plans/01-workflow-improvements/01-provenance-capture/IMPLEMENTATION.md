# Implementation: 01 — Provenance Capture

## What Was Built

Three file changes implementing progressive provenance writing in the planning skill.

### Files Changed

**`skills/planning/templates/PROVENANCE.md`** (new)
Template with four sections: Session, Initial Request (verbatim), Planning Conversation (per-turn append), Agent Decisions (final cross-cutting decisions). Turn format distinguishes agent-asked from user-volunteered turns. Two-layer decisions: per-turn inline (immediate choices) vs. final section (scope-shaping decisions not obvious from PLAN.md).

**`skills/planning/SKILL.md`** (modified)
Three write points added to the Workflow section:
- Step 1a: create plan directory and write PROVENANCE.md immediately after capturing the verbatim request, before reading stable docs. Explicitly clarifies that PLAN.md is not written until step 11.
- Step 5a: append each Q&A turn to PROVENANCE.md immediately on user response, before continuing.
- Step 11a: append Agent Decisions section before finalizing the plan.

Three provenance rules added to the Rules section: progressive writing discipline (create early, append per-turn, no batching), intent-not-transcript extraction with "if in doubt, omit", and no-credentials rule.

**`skills/planning/templates/PLAN.md`** (modified)
Provenance Notes section now references PROVENANCE.md as the companion planning conversation record.

## Deviations from Plan

None. All four execution phases were completed:
1. PROVENANCE.md template created with four sections
2. SKILL.md modified with three write points (steps 1a, 5a, 11a) and three rules
3. PLAN.md template updated to reference PROVENANCE.md
4. (Test deferred — requires a live planning session; the dogfooding PROVENANCE.md for this program itself serves as a real example)

## Tradeoffs

**Behavioral compliance vs. structural guarantee.** The three write points rely on the agent following the ordered steps. There is no tool checkpoint that forces a write at each step. An agent under context pressure could batch writes at the end. This is accepted for the current scope; the eval system (child 03) is the right place to test compliance empirically.

**Two-layer decisions.** Per-turn `Agent decisions:` (immediate) and final `## Agent Decisions` (cross-cutting) serve different purposes. This was clarified in the template after a review finding — without the explanation, an agent would duplicate or drop one layer.

## Validation Notes

Review found one high-severity defect (fixed): the template label `**User responded (verbatim):**` directly contradicted the instruction to strip tone and filler. Fixed by removing "verbatim" and adding a stripping note. Review also found medium-severity gaps in step 1/1a ordering clarity and user-volunteered turn handling — both fixed.

The existing PROVENANCE.md for the parent program (`docs/plans/[NEW]-workflow-improvements/PROVENANCE.md`) serves as a real example of correct output shape.
