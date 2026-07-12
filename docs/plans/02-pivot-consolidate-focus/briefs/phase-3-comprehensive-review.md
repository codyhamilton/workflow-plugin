# Brief: Phase 3 — Comprehensive-review skill revision

Consumer: the implementation worker for Phase 3. Owned paths: `skills/comprehensive-review/**` only. Do not touch any other file. Do not run git commit or push — leave changes in the working tree.

## Required reading, in order

1. `docs/plans/02-pivot-consolidate-focus/PLAN.md` — the model (section "The Model" is binding; its 7 decisions are settled)
2. `docs/plans/02-pivot-consolidate-focus/DESIGN.md` — binding contracts, especially "PR Artifact Seam", "Artifact Taxonomy", and "Briefs Invariant"
3. `skills/comprehensive-review/SKILL.md` — what you are revising

## Goal

This skill becomes the centerpiece of the downstream pipeline (a cursor automation reviews PRs, runs QA, and babysits them to merge-ready). Today it defines lenses and an output format but not its inputs or where outputs land. Give it explicit inputs, artifact-placed outputs, remediation briefs, an intent/assumptions lens, a plan-sufficiency judgment, and a fallback for PRs that arrive without plan artifacts. The right-sizing philosophy (focus beats breadth, one external loop, lightest shape that protects the change) stays — it is the skill's core value.

## Changes

### Explicit inputs

The review's inputs, stated as a contract: the plan folder (located via the PR body's `Workflow-Plan:` marker line — the only mechanical location mechanism), the diff, and the plan's verbatim intent and assumption ledger. When run locally (not against a PR), inputs are the plan folder and the working-tree change.

### Output placement

- Findings land in `REVIEW.md` **in the plan folder** (committed to the PR branch when reviewing a PR), keyed to PLAN.md's acceptance criteria — each criterion assessed, plus findings outside the criteria by severity. This keying is what lets a later merge-babysitting stage treat REVIEW.md as a checklist.
- Each **structural** finding additionally becomes a remediation brief at `briefs/remediation-<NN>.md` in the plan folder: the reviewer holds the hottest context on the defect, so the reviewer authors the fix instruction — complete enough that a clean agent can execute it without reading the review conversation. Include: the defect, where it lives, why it matters, the fix approach, done evidence. Trivial findings do not get briefs; they are listed in REVIEW.md for inline fixing.
- Keep the existing output content (outcome, findings by severity, fixes applied, residual risks, final assessment) inside REVIEW.md.

### New lens: intent and assumptions

Add to the existing lenses, as a first-class lens: does the implementation match the plan's recorded verbatim intent, and do the assumption-ledger entries hold? A headless build's ledger records decisions nobody approved — challenging them is this review's unique responsibility. An assumption that fails is a finding, sized by its blast radius.

### Plan-sufficiency judgment

The review records, in REVIEW.md, a short judgment: was the plan sufficient to determine intent, place these findings, and derive a QA plan? This is the cold-reader pressure on plan quality (hypothesis H6). One-way artifact flow only: workflow-tuning harvests these judgments later; this skill never invokes or depends on workflow-tuning (core never depends on lab).

### No-artifact fallback

A PR arriving with no plan folder (a human or agent that skipped the workflow) does not break the review. The reviewer reconstructs intent from the PR description, linked issue, and commit messages into `RECOVERED-INTENT.md` inside a newly created plan folder (normal path convention, slug from the PR), notes that intent is reconstructed (and therefore lower-confidence), then proceeds uniformly — REVIEW.md and remediation briefs land in that folder as usual.

### Why-relocation

Keep the failure-mode grounding and right-sizing rules; if any prose argues the design rather than orienting the reviewer, move it to a new `skills/comprehensive-review/reference.md` (consumers: workflow-tuning and skill revisers; not loaded during normal execution — say so at its top). This skill is short; do not pad it to match the others. If nothing warrants relocation, don't create the file.

## Keep untouched in spirit

- Review shape right-sizing (one focused reviewer default; parallel focused reviewers only for cross-cutting/risky changes).
- The existing lenses (contract/correctness, failure modes, real usefulness, optional domain lenses).
- One external review loop, then fix-and-self-review; no repeated loops by default.
- "The review should challenge the intent and plan approach, not just naive implementation alignment" — this grows into the intent/assumptions lens rather than being replaced.

## Done evidence

- SKILL.md states inputs (marker-located plan folder, diff, intent + ledger), output placement (REVIEW.md keyed to acceptance criteria, in the plan folder), remediation-brief mechanics with the `briefs/remediation-<NN>.md` path, the intent/assumptions lens, the plan-sufficiency judgment with its one-way flow note, and the RECOVERED-INTENT.md fallback.
- The right-sizing rules and lens structure survive recognizably.
- No reference to workflow-tuning as an invocation — only as a later harvester.

## Report back

A short summary: what you added, any deviation from this brief and why, and any contradiction you found between this brief and the DESIGN.md contracts (report, don't silently resolve).
