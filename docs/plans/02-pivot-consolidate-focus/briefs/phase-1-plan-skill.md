# Brief: Phase 1 — Plan skill revision

Consumer: the implementation worker for Phase 1. Owned paths: `skills/plan/**` only. Do not touch any other file. Do not run git commit or push — leave changes in the working tree.

## Required reading, in order

1. `docs/plans/02-pivot-consolidate-focus/PLAN.md` — the model (section "The Model" is binding; its 7 decisions are settled)
2. `docs/plans/02-pivot-consolidate-focus/DESIGN.md` — binding contracts, especially "PR Artifact Seam" and "Artifact Taxonomy"
3. `skills/plan/SKILL.md` and everything in `skills/plan/templates/` — what you are revising

## Goal

Revise the plan skill to the new model: no backlog taxonomy, both interactive and headless postures in one skill body, QA-drivable acceptance criteria, persuading-why relocated to a reference file. The skill's voice and its failure-mode grounding stay; its work-tracking machinery goes.

## Changes

### Remove (the backlog)

- All `[NEW]-` prefix rules, numeric renumbering ceremonies (including "when a [NEW]- parent is later renumbered..."), parent-program-as-provenance rules, and ROADMAP-as-canonical-schedule rules. The parent-program/child-plan structure itself goes: one plan folder per change/PR is the unit.
- Replace with the new convention, stated once: plan folders live at `docs/plans/<NN>-<slug>/`; slug is the unique key, `NN` is best-effort ordering only and nothing may locate a folder by number; a plan folder existing on a branch means the work is being built or was built; deferred or speculative work becomes a design-intent doc in `docs/design/` or a tracker issue, never a plan folder. Multi-PR programs = a stable design-intent doc each PR's plan references, plus self-contained plan-execute runs.

### Restructure the workflow

The current numbered list with letter insertions (1, 1a, 2 … 5a … 11a) becomes named phases. Suggested shape (adapt if a better cut emerges, but keep them named, not numbered-with-insertions): **Capture** (verbatim intent, first write to disk) → **Ground** (stable docs, drift/pivot check) → **Resolve** (questions or assumptions — see postures) → **Write** (PLAN.md, optional DESIGN.md) → **Challenge** (adversarial review pass) → **Checkpoint** (see postures).

### Add postures

Posture is **declared by the invoker, never inferred** (no TTY sniffing, no environment heuristics). Absent a declaration, assume a human is reachable.

- **Interactive** (default): scope-shaping questions as today, recorded as Q&A; the plan session ends at a held checkpoint where the plan and the assumption ledger are presented before any execution starts.
- **Headless** (declared): every question the skill would have asked becomes an entry in an **assumption ledger** — the question, the answer chosen, the rationale, and what would change if the assumption is wrong. The ledger is a section of PLAN.md. The checkpoint is waved through. Downstream review explicitly challenges the ledger, so assumptions must be honest, not decorative.

### Provenance

- PLAN.md always carries the verbatim intent (the triggering request, issue body, or task — whatever the human actually said). This rule is untouchable.
- PROVENANCE.md becomes optional: warranted for rich interactive sessions with real Q&A history; in headless one-shot runs the intent + assumption ledger + decisions live in PLAN.md alone. Update the templates accordingly (keep `templates/PROVENANCE.md` for the interactive case; add the assumption-ledger section to `templates/PLAN.md`).

### QA-drivable acceptance criteria

In `templates/PLAN.md` and the skill rules: acceptance criteria must be observable, and **user-facing** criteria must state entry point → action → observable result, sufficient for a downstream computer-use QA agent to derive its QA plan mechanically. Non-user-facing criteria stay as observable statements.

### The seam

The skill states the PR artifact seam facts a planner needs: the folder path convention, and that the eventual PR body will carry the marker line `Workflow-Plan: docs/plans/<NN>-<slug>/`.

### Why-relocation

- Keep in SKILL.md: the failure-mode preamble ("This skill exists to prevent…"), one-line rationale on rules where it changes behavior in unspecified situations, and named consumers of artifacts.
- Move to a new `skills/plan/reference.md`: prose that argues the design is correct rather than orienting the executing agent. Test per sentence: *if the agent already trusted the rule, would this sentence change what it does?* Yes → stays. No → reference.md. reference.md's consumers are workflow-tuning and future skill revisers; it is not loaded during normal execution — say so at its top.
- Do not gut the skill. Its density of intent is a feature; you are removing self-justification and work-tracking, not personality or grounding.

### Keep untouched in spirit

- Question discipline (ask only what materially changes scope shape, sequencing, boundaries, compatibility, non-goals, acceptance criteria) — in headless posture this same discipline governs which assumptions get ledger entries.
- Architectural-pivot detection and widening scope.
- Stable-docs grounding (OVERVIEW/ARCHITECTURE/design). The suggestion to run setup when stable docs are missing may remain as advice to a human, but must not become a hard dependency (setup is a lab skill; core never depends on lab).
- DESIGN.md optionality and its warrant conditions.
- The rule against forcing templates mechanically.

## Done evidence

- `grep -rn "\[NEW\]" skills/plan/` returns nothing; no renumbering or ROADMAP-sync rules remain.
- SKILL.md contains: named-phase workflow, both postures with the declared-not-inferred rule, the assumption ledger, the plan-folder convention, QA-drivable criteria rule, and retains its failure-mode preamble.
- `skills/plan/reference.md` exists with the relocated prose and a consumer note at the top.
- `templates/PLAN.md` has the assumption-ledger section and the entry-point→action→result shape for user-facing criteria.

## Report back

A short summary: what you removed, what you added, any place you deviated from this brief and why, and any contradiction you found between this brief and the DESIGN.md contracts (do not resolve contradictions silently — report them).
