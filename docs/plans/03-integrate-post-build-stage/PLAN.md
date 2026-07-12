# Integrate the Post-Build Pipeline Stage

## Intent

User request, verbatim:

> see if you can pull the garcia—music repo, which contains an orchestration skill and pr-post work which this fits into. Those have been worked on to pick up where build leaves off - to work on the pr, review, babysit and QA. We should integrate them into this repo

## Why This Plan Exists

This plugin's design contract already reserves a downstream pipeline stage: execute's pipeline posture declares "a downstream orchestrated review stage exists", `comprehensive-review` writes for "a later merge-babysitting automation", and the PR Artifact Seam names `QA.md` and remediation briefs as pipeline-stage contents — but the stage itself was "outside this plugin's scope". That stage now exists: `codyhamilton/garcia-music` carries a `post-build-automation` skill (explicitly written as "the L-FANTE adapter" for "the shared workflow plugin") and an `orchestration` skill whose deploy-babysit and QA phases feed it. This plan lifts the portable stage semantics into this repo as a core skill, so any repo can adopt the stage with only a thin adapter.

## Scope

Add a `post-build` core skill owning the portable post-build stage: plan discovery from the PR, independent review via `comprehensive-review`, bounded finding-scoped remediation with fresh re-review, QA planning into `QA.md`, exact-SHA deploy verification, deployed browser QA, and a merge-readiness report. Define the adapter contract a repo must supply (garcia-music's `post-build-automation` becomes the first adapter). Reconcile `QA.md` semantics and review verdicts across the stable docs and `comprehensive-review`.

## Architectural Implications

- `docs/ARCHITECTURE.md`'s PR Artifact Seam changes: `QA.md` becomes a committed pre-deploy matrix; final SHA-specific results are external output (PR/automation), never a trailing commit. This supersedes the seam's earlier "observed result, pass/fail" wording for `QA.md` itself.
- `comprehensive-review` gains a machine-actionable verdict enum (`PASS` / `PASS_WITH_FOLLOWUPS` / `REMEDIATE`) and a severity enum (`blocker` / `high` / `medium` / `low`) so the stage can branch on review output mechanically.
- The core plugin grows from three skills to four; core remains cloud-safe (the new skill has no interactive gates).
- garcia-music's `orchestration` research/plan/implement phases map onto `plan` + `execute` and are not imported; only its post-build phases (deploy babysit, QA) inform the new skill.

## Intent Validation

- None — headless run; see Assumption Ledger.

## Assumption Ledger

### Assumption 1

- **Question:** Should `QA.md` carry executed pass/fail results (current seam wording) or be a committed matrix with results delivered externally (garcia model)?
- **Answer chosen:** Matrix committed before the candidate SHA; final results external, never a trailing commit.
- **Rationale:** A results commit after testing changes the SHA, so the merged commit is not the tested commit. The garcia automation was built and hardened against this rule, and it is the more correct invariant.
- **If wrong:** Revert the seam wording in `docs/ARCHITECTURE.md` and let the stage append a docs-only results commit; the skill's QA-planning step is unaffected.

### Assumption 2

- **Question:** New portable skill, or import garcia's two skills wholesale?
- **Answer chosen:** One new core skill (`post-build`) holding portable semantics plus a defined adapter contract; garcia keeps its repo adapter.
- **Rationale:** garcia's skills are saturated with repo specifics (Vercel/Supabase scripts, staging URLs, credentials, Grok/Composer routing) that cannot ship in a portable plugin; garcia's own adapter already declares the shared plugin authoritative for portable semantics.
- **If wrong:** The adapter-contract section is the seam to renegotiate; the stage sequence stands either way.

### Assumption 3

- **Question:** Should garcia's diff-based plan discovery survive, given this repo made the `Workflow-Plan:` marker the only mechanical locator?
- **Answer chosen:** Marker is primary; diff-based discovery is a fallback for markerless PRs, with garcia's never-tie-break rule kept; no plan folder at all falls through to `comprehensive-review`'s no-artifact fallback.
- **Rationale:** The stage must survive PRs from agents or humans that skipped the workflow; a strict-marker-only stage would dead-end exactly the PRs that most need review.
- **If wrong:** Delete the fallback subsection; the marker path is self-sufficient.

### Assumption 4

- **Question:** Does the stage merge the PR when everything passes?
- **Answer chosen:** No — it reports merge-readiness and stops; merging stays with the human or an explicitly separate automation.
- **Rationale:** garcia's adapter hard-stops on merge/merge-state changes; merging is the one irreversible act in the pipeline and no input suggests automating it.
- **If wrong:** Add a declared opt-in (same pattern as postures) rather than a default.

## Open Questions

- None.

## Execution Phases

1. Write `skills/post-build/SKILL.md` and `skills/post-build/reference.md`.
2. Reconcile `comprehensive-review` (verdict/severity enums, resolution rules, stage naming).
3. Update stable docs (`docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, `README.md`) and plugin manifests.

## Acceptance Criteria

Non-user-facing (observable statements):

- A `post-build` skill exists in core with: marker-first discovery with bounded fallbacks, review via `comprehensive-review`, one remediation cycle + one fresh re-review, `QA.md` matrix planning, exact-SHA deploy verification, deployed QA with one QA remediation cycle, portable safety invariants, a final output schema, and an explicit adapter contract — and contains no garcia-specific mechanics (no Vercel/Supabase/Wompi/model names).
- `comprehensive-review`'s output format declares the `PASS`/`PASS_WITH_FOLLOWUPS`/`REMEDIATE` verdict and `blocker`/`high`/`medium`/`low` severities, and forbids erasing original findings when recording resolutions.
- `docs/ARCHITECTURE.md`, `docs/OVERVIEW.md`, and `README.md` list the new skill and carry the reconciled `QA.md` semantics; plugin manifests name it and bump the version.

## Provenance Notes

Headless one-shot run; the Assumption Ledger above is the full decision record. Source material: `codyhamilton/garcia-music` `.claude/skills/post-build-automation/SKILL.md` (stage semantics, safety invariants, exact-SHA gate, bounded loops, output schema) and `.claude/skills/orchestration/SKILL.md` (deploy-babysit and QA phase shapes, failure-handling table).
