# Implementation — Integrate the Post-Build Pipeline Stage

## Run

- Tool: cloud run (Claude Code remote)
- Session/Run ID or session URL: https://claude.ai/code/session_01MUCKGtThwdRX12oNQm1TFv
- Started: 2026-07-12T06:30:00Z

## What was built

- `skills/post-build/SKILL.md` — new core skill: portable post-build stage semantics (marker-first discovery with bounded diff and no-artifact fallbacks, review via `comprehensive-review`, one finding-scoped remediation cycle + one fresh re-review, `QA.md` matrix planning, exact-SHA deploy verification, deployed QA with one remediation cycle, portable safety invariants, final output schema, adapter contract).
- `skills/post-build/reference.md` — design rationale (SHA gate, uncommitted results, fresh re-review, bounded loops, no tie-breaking, no merging) and origin note pointing at garcia-music's adapter.
- `skills/comprehensive-review/SKILL.md` — output format gains the `PASS`/`PASS_WITH_FOLLOWUPS`/`REMEDIATE` verdict, reviewed SHA, `blocker`/`high`/`medium`/`low` severities, and the findings-are-never-erased rule; stage naming updated from "merge-babysitting automation" to `post-build`.
- `docs/ARCHITECTURE.md` — component map, skill responsibilities, cross-skill contracts (`execute → post-build`, `post-build → comprehensive-review`, `post-build ↔ repo adapter`), PR Artifact Seam (`QA.md` is matrix-only, committed before the candidate SHA; results are external-only), invariant 9, post-build data flow, stable references.
- `docs/OVERVIEW.md`, `README.md`, `install.sh`, plugin manifests — skill lists and counts updated; core plugin version 2.0.0 → 2.1.0.

## Tradeoffs and deviations

- `QA.md` semantics changed from the 02-pivot seam wording (executed pass/fail committed) to matrix-only-committed with external results — see PLAN.md Assumption 1.
- garcia-music's `orchestration` research/plan/implement phases were not imported (already covered by `plan`/`execute`); only its post-build phases informed the new skill. garcia-music keeps its `post-build-automation` skill as the reference repo adapter — nothing repo-specific was ported.
- No worker delegation: single-session direct implementation (docs-only change, orchestrator context already hot with both source repos — per execute's delegation judgment call). No dispatch briefs, so no `briefs/`.

## Validation

- `grep -riE "vercel|supabase|wompi|grok|composer|…" skills/post-build/SKILL.md` → no matches (portability criterion).
- Skill lists verified consistent across `README.md`, `docs/OVERVIEW.md`, `docs/ARCHITECTURE.md`, `install.sh`, and all three manifests.
- In-run review: pre-flight self-verification only (this session is itself the review conversation with the user; the PR is the review surface). `REVIEW.md` deliberately not written — the PR review stands in for the terminal stage.

## Scope extension: automation wiring (same PR)

- `skills/post-build/automation.md` — operator guide for triggering the stage: one orchestrated automation per stage (chaining only at stage seams via the PR — see PLAN.md Assumption 5), trigger-once discipline with a self-commit guard for push-only harnesses, re-run resumability, configuration steps, canonical prompt template, pre-wiring checklist, canary run.
- `skills/post-build/SKILL.md` — added the resumability rule to Workflow step 1 (artifacts bound to the current SHA count as done on re-trigger) and pointed the Reference section at `automation.md`.
- `README.md` and `docs/ARCHITECTURE.md` — link the wiring guide.
- Grounding: garcia-music's `docs/features/testing/cursor-post-build-automation.md` (the hardened single-automation setup) — its portable content was lifted; its Vercel/Supabase/seed specifics remain adapter material.
