# Integrate the Post-Build Pipeline Stage

The downstream stage the plugin's design had always reserved a slot for became a real core skill.
`post-build` lifted the portable stage semantics out of a repo-specific automation in
`codyhamilton/garcia-music`, leaving that repo's version as the first adapter, so any repo can adopt
the stage with a thin adapter of its own. It landed as planned, in one docs-only PR.

## Intent

User request, verbatim:

> see if you can pull the garcia—music repo, which contains an orchestration skill and pr-post work which this fits into. Those have been worked on to pick up where build leaves off - to work on the pr, review, babysit and QA. We should integrate them into this repo

## Why This Existed

The design contract already assumed a downstream pipeline stage: `execute`'s pipeline posture
declared that "a downstream orchestrated review stage exists", `comprehensive-review` wrote for "a
later merge-babysitting automation", and the PR Artifact Seam named `QA.md` and remediation briefs as
pipeline-stage contents — while the stage itself sat outside the plugin's scope. It existed in
garcia-music, written explicitly as an adapter for the shared plugin. The hole and the thing that
filled it had been built from opposite ends; this closed them together.

## What Was Built

`post-build` as a core skill owning the whole stage: marker-first plan discovery with bounded
fallbacks, independent review via `comprehensive-review`, one finding-scoped remediation cycle plus
one fresh verification, `QA.md` matrix planning, exact-SHA deploy proof, deployed browser QA with one
remediation cycle, portable safety invariants, an explicit adapter contract, and a merge-readiness
report it never acts on. `comprehensive-review` gained machine-actionable enums so the stage could
branch on its output without interpretation — verdict `PASS` / `PASS_WITH_FOLLOWUPS` / `REMEDIATE`,
severity `blocker` / `high` / `medium` / `low` — plus the rule that recording a resolution never
erases the original finding. garcia-music kept its own adapter; nothing repo-specific was ported, and
a portability grep confirmed it.

**Changed:** `skills/post-build/` (the skill, its design reference, and the automation wiring guide);
`skills/comprehensive-review/SKILL.md`; `docs/ARCHITECTURE.md` (component map, cross-skill contracts,
PR Artifact Seam, invariant 9, the post-build data flow); `docs/OVERVIEW.md`, `README.md`,
`install.sh`, and the three plugin manifests (core 2.0.0 → 2.1.0).

Readers following old paths: `skills/post-build/reference.md` was later consolidated into
`workflow-tuning/principles.md`, and `skills/post-build/automation.md` moved to
`docs/automation/post-build.md`, both in `04-workflow-refine-and-closeout`.

## Deviations

- **`QA.md` semantics were changed, superseding the previous plan's contract.** The seam had said
  executed pass/fail results are committed; this changed it to matrix-only-committed, with final
  SHA-specific results delivered externally. A results commit after testing changes the SHA, which
  would make the merged commit one nobody tested. This is the most consequential thing the change
  did.
- **Scope grew mid-PR** to include the automation wiring guide and the re-run resumability rule
  (recorded at the time as a fifth assumption): one orchestrated automation per stage, chaining only
  at stage seams through the PR, because the stage's cross-phase state is exactly the state that must
  never be committed.
- **No worker delegation and no `briefs/`.** A docs-only change with the orchestrator's context
  already hot on both repos — execute's delegation judgment, applied.

## Review

None. Executed in pipeline posture with the PR conversation standing in for the review stage, so
`REVIEW.md` was deliberately not written. Defensible for a docs-only change, but it is why the folder
then sat unfinished for weeks: nothing owned its ending. Validation was the portability grep plus a
consistency check of the skill lists across `README.md`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`,
`install.sh`, and all three manifests.

## QA

Not applicable — non-functional change, no driveable surface.

## Residual Risks

The adapter contract had exactly one implementation at the time, so its portability was asserted
rather than demonstrated. A second adapter is the real test.

## Follow-ups

None.

## Decisions Worth Keeping

- **Portable semantics here, repo mechanics in an adapter.** garcia's skills were saturated with
  deploy scripts, staging URLs, credentials, and model routing that cannot ship in a plugin; its own
  adapter already treated the shared plugin as authoritative for the portable half.
- **The stage reports merge-readiness and stops.** Merging is the one irreversible act in the
  pipeline and nothing in the request asked to automate it. If that ever changes it should be a
  declared opt-in, the same shape as postures.
- **Marker-first discovery, with a fallback anyway.** The `Workflow-Plan:` marker is the only
  mechanical locator, but a strict marker-only stage would dead-end exactly the markerless PRs that
  most need review.
