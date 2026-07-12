---
name: post-build
description: Orchestrate the post-build pipeline stage against a PR produced by execute — independent review, bounded remediation, QA planning, exact-SHA deploy verification, deployed browser QA, and a merge-readiness report. Right-sizes the stage to change classification (plan presence, functional surface, size). Use when picking up a PR after the build stage, or when an automation triggers the post-build workflow.
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
- A one-size-fits-all full stage burns budget on trivial or non-functional changes, or invents plan ceremony where none is needed.
- Deploy babysitting runs proactively instead of waiting for required checks to conclude.

The orchestrator running this stage **coordinates by default**: it discovers, classifies, delegates, checks handoffs between phases, and emits the final report. It does not edit functional code, perform independent review of functional changes, drive a browser, or prove a deploy itself — those substantive phases are dispatched workers carrying a verbatim-routed brief. **Exception:** for trivial or small non-functional changes, the orchestrator may absorb the entire stage (see Change Classification).

## Portable vs. Adapter

This skill owns the portable stage semantics. Everything repo-specific comes from a **repo adapter skill** that the triggering automation or operator loads alongside it. The adapter must supply:

- **Production boundaries**: which branches, deploy targets, and data surfaces are production and must never be touched.
- **Deploy-proof mechanics**: the commands that push, wait for a deployment, prove a deployment corresponds to an exact commit SHA, and health-check the deployed URL.
- **Required checks**: which CI / required status checks must pass on the candidate SHA before merge-readiness (and before any deploy proof needed for QA). Absent an explicit set, use the platform's required checks for the PR; if none are knowable, say so in the report and do not invent green.
- **QA environment**: how the deployed URL is derived, seeded/committed test identities and their sign-in routes, required environment setup, and environment caveats QA prompts must state.
- **Worker routing**: which agent types or models run each phase in the local harness.

Authority order when they conflict: the repo's own hard limits, then the adapter, then this skill, then the triggering prompt's run context. If a required adapter capability is missing (for example there is no way to prove a deployment's SHA), skip the dependent phase explicitly and say so in the report — never fake the proof.

## Discovery

Resolve plan context before classifying or delegating:

1. **Marker first.** The PR body's `Workflow-Plan: docs/plans/<NN>-<slug>/` line is the primary and only preferred locator.
2. **Diff fallback** (markerless PR that still carries a plan folder): compute the merge base against the PR's base branch, list changed files under `docs/plans/`, and form candidates from the unique parent directories of changed `IMPLEMENTATION.md` files — or, if none, of changed `PLAN.md` files. Require exactly one candidate. Never tie-break by folder number, modification time, or lexical order — on zero or several candidates, stop and report them, requesting an explicit plan path.
3. **No plan folder at all**: do **not** invent ceremony yet. Classification decides the path:
   - Trivial / small **non-functional** changes: proceed without a plan folder; record `Intent source: ad-hoc` in the report.
   - **Functional** (or mixed / large ambiguous) changes: use `comprehensive-review`'s no-artifact fallback — reconstruct intent into `RECOVERED-INTENT.md` and proceed at reduced confidence. A PR that skipped the workflow still gets a real review of functional risk, not a rubber stamp of behavior.
   - Create a plan folder only when review or QA artifacts need a home.

Preflight alongside discovery: clean worktree, a non-default feature branch, and — when a plan folder is resolved — a diff plausibly covered by that plan. Unexplained material changes outside the plan's scope are a stop, not something to fold in.

## Change Classification

After discovery, classify the PR from the **diff and plan context** (not vibes). Record the classification in the final report. Prefer over-classifying as functional when unsure. Mixed PRs (docs + any behavioral tweak) are `functional` / `mixed` — a docs majority must not hide a behavior change.

Three dimensions:

| Dimension | Values | How to judge |
|-----------|--------|--------------|
| **Intent source** | `planned` / `recovered` / `ad-hoc` | Marker or single plan folder → `planned`; reconstructed `RECOVERED-INTENT.md` → `recovered`; no plan folder and none needed → `ad-hoc` |
| **Surface** | `functional` / `non-functional` / `mixed` | **Functional** = runtime- or user-facing behavior (app/logic/API/UI, behavior-changing config or migrations). **Non-functional** = docs, comments, skills/markdown, CI-only with no runtime impact, pure renames with no behavior delta, and similar. **Mixed** = both. |
| **Size** | `trivial` / `small` / `normal` / `large` | Lines/files touched and blast radius. Trivial ≈ one-liner / tiny localized edit; large ≈ cross-cutting or high blast radius. |

### Right-sizing from classification

| Classification | Process |
|----------------|---------|
| `trivial` or `small` + `non-functional` | **Absorb:** orchestrator may run the whole stage inline — light diff skim, wait for required checks, emit report. No plan folder, no delegated review, no QA, no deploy proof. Execution mode: `absorbed`. |
| `normal`/`large` + `non-functional` | Light delegated or absorbed review as appropriate; wait for required checks; skip QA and deploy proof. |
| `functional` or `mixed` (any size), with or without a plan | Independent review (delegate; recover intent if needed). Wait for required checks. **QA planning + deploy proof + deployed QA only if** there is at least one user-facing / driveable criterion or residual risk that requires a live UI. Internal-only functional changes still get review + green checks; skip browser QA unless the adapter defines a non-browser substitute. |
| Ambiguous recovered / large functional | Full stage at reduced confidence — today's thorough path. |

**Absorption limits.** Never absorb: independent review of functional or mixed changes; remediation verification after a delegated review; browser QA; exact-SHA deploy proof. Those stay dispatched workers when they run. Absorption is for cheap confidence on non-functional risk, not for proving contested fixes.

## Safety Invariants

- Never write to production deploy targets or production data. The adapter defines them; absent an adapter, treat every deployment target as production and stop before deploy verification.
- This stage never merges. Stop on any request or temptation toward merge, force-push, destructive git operations, or merge-state changes — merge-readiness is reported, not acted on.
- Never broaden the active plan or discard unrelated work found on the branch.
- Browser QA runs only against a deployment proven to be the candidate SHA on a non-production target — never localhost, never an assumed URL — and only when classification says QA is applicable.
- Final SHA-specific QA results and media go to the PR or automation output, never a trailing commit: a commit added after testing changes the SHA, and the merged commit must be the tested commit.

## Workflow

1. **Preflight, discovery, and classification** (above). Stop before any delegation on a failed precondition; do not create missing plan artifacts just to keep going. On a re-triggered run, resume rather than repeat: committed artifacts already bound to the current candidate SHA count as done (a passing `REVIEW.md` for this SHA skips review; an existing `QA.md` matrix skips planning; recorded cycles count against the bounded loops). If classification selects the absorb path, jump to required checks (step 6) after the light skim, then report.
2. **Independent review** (skip when absorb path already covered review). Dispatch `comprehensive-review` against the PR. It writes `REVIEW.md` keyed to `PLAN.md`'s acceptance criteria (or `RECOVERED-INTENT.md`), challenges the assumption ledger, and authors a remediation brief per structural finding. Its verdict is `PASS`, `PASS_WITH_FOLLOWUPS`, or `REMEDIATE`.
3. **Remediation** (only on `REMEDIATE`). Dispatch a clean fixer per accepted finding, its prompt the reviewer's remediation brief routed verbatim plus mechanical pointers. The fixer touches only the accepted findings, runs focused tests, updates `IMPLEMENTATION.md`, and records resolutions in `REVIEW.md` without erasing the original findings.
4. **Fresh re-review.** A clean reviewer — not the original — verifies the remediation delta plus the stable artifacts, and updates `REVIEW.md`'s verdict for the new SHA. One remediation cycle, one re-review: if a `blocker` or `high` finding still stands, stop and hand off.
5. **QA planning** (only when QA is applicable — functional/mixed surface with at least one driveable user-facing criterion or review residual that needs a live UI). A worker derives `QA.md` from `PLAN.md`/`RECOVERED-INTENT.md` acceptance criteria and `REVIEW.md`'s residual risks: one case per user-facing criterion with a stable ID, role, entry point → action → expected result, and required evidence; criteria the stage cannot drive are listed with the reason, not dropped. `QA.md` is a matrix only — no pre-execution pass/fail claims — and states that final results are external output. Commit it now, before the candidate SHA exists. When QA is not applicable, skip this step and record `QA: SKIPPED (<reason>)` — do not invent a matrix for undriveable-only or non-functional work.
6. **Required checks (wait).** With every pre-deploy artifact and fix committed (or immediately if none), capture the candidate SHA and **wait** for the adapter's required checks on that SHA to conclude. Do not proactively babysit deploys or poke the pipeline for progress while checks are pending — this phase is reactive. On failure: stop with `HUMAN_ACTION_REQUIRED` (or one bounded in-scope fix cycle if the failure is clearly caused by this PR). On pass: continue. If no checks are knowable, say so explicitly and do not claim they passed.
7. **Deploy verification** (only when QA will run and needs a live URL). Using the adapter's mechanics, prove a non-production deployment of **exactly that SHA** is live, resolve its exact URL, and health-check that same URL. Branch-level "ready" signals are not SHA proof; a zero exit code is not SHA proof. Retry only inside this phase; if the SHA cannot be proven, stop before QA. When QA is skipped, skip deploy proof and record `Deploy proof: SKIPPED (<reason>)`.
8. **Deployed QA** (only when QA is applicable and deploy proof succeeded). Dispatch the QA worker against the exact proven URL with the adapter's identities and setup, executing every applicable `QA.md` case through real UI interaction, returning pass/fail per case ID with evidence paths and console/network errors. One QA remediation cycle: fix only evidenced failures, re-review the delta, recommit, wait for checks again, redeploy, re-prove the SHA, rerun affected and risk-adjacent cases. Stop if failures remain.
9. **Report.** Emit the final output (schema below) to the PR or automation channel. Do not commit it.

A worker that returns nothing usable is relaunched once with its partial output; after a second failure, stop for human action — the orchestrator does not absorb a failed delegated phase.

## Final Output Schema

```text
Status: PASS | PASS_WITH_FOLLOWUPS | HUMAN_ACTION_REQUIRED
Plan: <docs/plans/<NN>-<slug>/ or RECOVERED or NONE>
Classification: intent=<planned|recovered|ad-hoc>; surface=<functional|non-functional|mixed>; size=<trivial|small|normal|large>
Execution mode: orchestrated | absorbed
Branch / base / merge base: <values>
Tested SHA: <sha or NOT_TESTED>
Tested URL: <url or NOT_TESTED or N/A>
Review verdict: <verdict|ABSORBED_LIGHT|SKIPPED>; remediation cycles: <0|1>
Automated checks: <waited|not-configured>; <check>: PASS|FAIL|PENDING (<evidence>) per line
Deploy proof: RUN | SKIPPED (<reason>)
QA: RUN | SKIPPED (<reason>)
QA cases: <case ID>: PASS|FAIL|NOT_RUN — <evidence> per line; QA remediation cycles: <0|1>
Remaining non-blocking findings: <IDs or none>
Blocker / human action: <specific action or none>
```

Never report `PASS` while required checks are failing or still pending. Never report `PASS` while exact-SHA proof or an **applicable** QA case is missing — "applicable" means classification selected QA and a driveable case exists; skipped QA for non-functional or undriveable-only work is an honest skip, not a missing gate. Downgrade honestly.

## Rules

- Coordinate by default; absorb only for trivial/small non-functional work within the absorption limits.
- Exactly one active plan folder when one is needed, resolved marker-first; ambiguity stops the stage rather than being tie-broken. Ad-hoc non-functional work may have no plan folder.
- Review and QA are keyed to `PLAN.md` (or recovered intent) acceptance criteria when those artifacts exist, never derived from the diff alone.
- QA and deploy proof run only for applicable functional/user-facing need; required checks are waited for reactively before merge-readiness and before any QA-driven deploy proof.
- Remediation is finding-scoped; verification is a fresh context. One remediation cycle per review, one per QA, then stop.
- `REVIEW.md` accumulates — resolutions are appended, original findings never erased.
- When QA runs, `QA.md` is committed before the candidate SHA and carries the matrix only; executed results stay external.
- QA targets the exact proven-SHA URL or does not run.
- `medium`/`low` findings may ride along as explicit non-blocking follow-ups; `blocker`/`high` stop the stage.
- The stage reports merge-readiness; it never merges.

## Reference

`automation.md`, beside this file, is the operator guide for wiring this stage into an external automation trigger — automation shape, trigger discipline, canonical prompt, and canary. `reference.md` holds the design rationale behind these rules — why the SHA gate is absolute, why results are never committed, why loops are bounded, why the stage right-sizes and waits for checks — for whoever revises this skill later. It is not loaded during normal execution.
