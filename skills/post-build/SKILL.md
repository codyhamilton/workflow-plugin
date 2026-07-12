---
name: post-build
description: Orchestrate the post-build pipeline stage against a PR produced by execute — independent review, bounded remediation, QA planning, exact-SHA deploy verification, deployed browser QA, and a merge-readiness report. Use when picking up a PR after the build stage, or when an automation triggers the post-build workflow.
---

# Post-Build Pipeline Stage

Use this skill to take a PR from "build finished" to "provably ready to merge". It is the downstream orchestrated review stage that execute's **pipeline** posture declares exists; when this stage runs, `REVIEW.md`, `QA.md`, and remediation briefs are its property, not the build's.

This skill exists to prevent common post-build failures:

- Review runs against the diff alone, unanchored from the plan's intent and acceptance criteria.
- Findings reach the fixing agent as an orchestrator's paraphrase instead of the reviewer's own brief.
- Remediation quietly widens beyond the accepted findings.
- The reviewer who raised the findings verifies its own fixes and rubber-stamps them.
- QA drives a deployment that was never proven to be the candidate commit.
- QA results are committed after testing, so the merged commit is not the tested commit.
- Fix loops run unbounded, or a stuck run guesses instead of stopping with a specific handoff.
- Plan discovery is ambiguous and the stage picks a folder by number, recency, or vibes.

The orchestrator running this stage **coordinates only**: it discovers, delegates, checks handoffs between phases, and emits the final report. It does not edit code, review, test, drive a browser, or babysit a deploy itself — every substantive phase is a dispatched worker carrying a verbatim-routed brief.

## Portable vs. Adapter

This skill owns the portable stage semantics. Everything repo-specific comes from a **repo adapter skill** that the triggering automation or operator loads alongside it. The adapter must supply:

- **Production boundaries**: which branches, deploy targets, and data surfaces are production and must never be touched.
- **Deploy-proof mechanics**: the commands that push, wait for a deployment, prove a deployment corresponds to an exact commit SHA, and health-check the deployed URL.
- **QA environment**: how the deployed URL is derived, seeded/committed test identities and their sign-in routes, required environment setup, and environment caveats QA prompts must state.
- **Worker routing**: which agent types or models run each phase in the local harness.

Authority order when they conflict: the repo's own hard limits, then the adapter, then this skill, then the triggering prompt's run context. If a required adapter capability is missing (for example there is no way to prove a deployment's SHA), skip the dependent phase explicitly and say so in the report — never fake the proof.

## Discovery

Resolve exactly one active plan folder before delegating anything:

1. **Marker first.** The PR body's `Workflow-Plan: docs/plans/<NN>-<slug>/` line is the primary and only preferred locator.
2. **Diff fallback** (markerless PR that still carries a plan folder): compute the merge base against the PR's base branch, list changed files under `docs/plans/`, and form candidates from the unique parent directories of changed `IMPLEMENTATION.md` files — or, if none, of changed `PLAN.md` files. Require exactly one candidate. Never tie-break by folder number, modification time, or lexical order — on zero or several candidates, stop and report them, requesting an explicit plan path.
3. **No plan folder at all**: use `comprehensive-review`'s no-artifact fallback — reconstruct intent into `RECOVERED-INTENT.md` and proceed uniformly at reduced confidence. A PR that skipped the workflow still gets a full stage, not a rubber stamp.

Preflight alongside discovery: clean worktree, a non-default feature branch, and a diff plausibly covered by the resolved plan. Unexplained material changes outside the plan's scope are a stop, not something to fold in.

## Safety Invariants

- Never write to production deploy targets or production data. The adapter defines them; absent an adapter, treat every deployment target as production and stop before deploy verification.
- This stage never merges. Stop on any request or temptation toward merge, force-push, destructive git operations, or merge-state changes — merge-readiness is reported, not acted on.
- Never broaden the active plan or discard unrelated work found on the branch.
- Browser QA runs only against a deployment proven to be the candidate SHA on a non-production target — never localhost, never an assumed URL.
- Final SHA-specific QA results and media go to the PR or automation output, never a trailing commit: a commit added after testing changes the SHA, and the merged commit must be the tested commit.

## Workflow

1. **Preflight and discovery** (above). Stop before any delegation on a failed precondition; do not create missing plan artifacts to keep going. On a re-triggered run, resume rather than repeat: committed artifacts already bound to the current candidate SHA count as done (a passing `REVIEW.md` for this SHA skips review; an existing `QA.md` matrix skips planning; recorded cycles count against the bounded loops).
2. **Independent review.** Dispatch `comprehensive-review` against the PR. It writes `REVIEW.md` keyed to `PLAN.md`'s acceptance criteria, challenges the assumption ledger, and authors a remediation brief per structural finding. Its verdict is `PASS`, `PASS_WITH_FOLLOWUPS`, or `REMEDIATE`.
3. **Remediation** (only on `REMEDIATE`). Dispatch a clean fixer per accepted finding, its prompt the reviewer's remediation brief routed verbatim plus mechanical pointers. The fixer touches only the accepted findings, runs focused tests, updates `IMPLEMENTATION.md`, and records resolutions in `REVIEW.md` without erasing the original findings.
4. **Fresh re-review.** A clean reviewer — not the original — verifies the remediation delta plus the stable artifacts, and updates `REVIEW.md`'s verdict for the new SHA. One remediation cycle, one re-review: if a `blocker` or `high` finding still stands, stop and hand off.
5. **QA planning.** A worker derives `QA.md` from `PLAN.md`'s acceptance criteria and `REVIEW.md`'s residual risks: one case per user-facing criterion with a stable ID, role, entry point → action → expected result, and required evidence; criteria the stage cannot drive are listed with the reason, not dropped. `QA.md` is a matrix only — no pre-execution pass/fail claims — and states that final results are external output. Commit it now, before the candidate SHA exists.
6. **Deploy verification.** With every pre-deploy artifact and fix committed, push and capture the candidate SHA. Using the adapter's mechanics, prove a non-production deployment of **exactly that SHA** is live, resolve its exact URL, and health-check that same URL. Branch-level "ready" signals are not SHA proof; a zero exit code is not SHA proof. Retry only inside this phase; if the SHA cannot be proven, stop before QA.
7. **Deployed QA.** Dispatch the QA worker against the exact proven URL with the adapter's identities and setup, executing every applicable `QA.md` case through real UI interaction, returning pass/fail per case ID with evidence paths and console/network errors. One QA remediation cycle: fix only evidenced failures, re-review the delta, recommit, redeploy, re-prove the SHA, rerun affected and risk-adjacent cases. Stop if failures remain.
8. **Report.** Emit the final output (schema below) to the PR or automation channel. Do not commit it.

A worker that returns nothing usable is relaunched once with its partial output; after a second failure, stop for human action — the orchestrator does not absorb the phase.

## Final Output Schema

```text
Status: PASS | PASS_WITH_FOLLOWUPS | HUMAN_ACTION_REQUIRED
Plan: <docs/plans/<NN>-<slug>/ or RECOVERED>
Branch / base / merge base: <values>
Tested SHA: <sha or NOT_TESTED>
Tested URL: <url or NOT_TESTED>
Review verdict: <verdict>; remediation cycles: <0|1>
Automated checks: <command>: PASS|FAIL (<evidence>) per line
QA cases: <case ID>: PASS|FAIL|NOT_RUN — <evidence> per line; QA remediation cycles: <0|1>
Remaining non-blocking findings: <IDs or none>
Blocker / human action: <specific action or none>
```

Never report `PASS` while exact-SHA proof or an applicable QA case is missing — downgrade honestly.

## Rules

- Orchestrate only; every substantive phase is a delegated worker with a verbatim-routed brief.
- Exactly one active plan folder, resolved marker-first; ambiguity stops the stage rather than being tie-broken.
- Review and QA are keyed to `PLAN.md`'s acceptance criteria, never derived from the diff alone.
- Remediation is finding-scoped; verification is a fresh context. One remediation cycle per review, one per QA, then stop.
- `REVIEW.md` accumulates — resolutions are appended, original findings never erased.
- `QA.md` is committed before the candidate SHA and carries the matrix only; executed results stay external.
- QA targets the exact proven-SHA URL or does not run.
- `medium`/`low` findings may ride along as explicit non-blocking follow-ups; `blocker`/`high` stop the stage.
- The stage reports merge-readiness; it never merges.

## Reference

`automation.md`, beside this file, is the operator guide for wiring this stage into an external automation trigger — automation shape, trigger discipline, canonical prompt, and canary. `reference.md` holds the design rationale behind these rules — why the SHA gate is absolute, why results are never committed, why loops are bounded — for whoever revises this skill later. It is not loaded during normal execution.
