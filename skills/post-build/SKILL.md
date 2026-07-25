---
name: post-build
description: Orchestrate the post-build pipeline stage against a PR produced by execute — independent review with in-place fixes, remediation only for briefed structural findings, conditional QA with exact-SHA deploy proof, a single end-of-work required-checks gate, and a merge-readiness report. Right-sizes the stage to change classification (plan presence, functional surface, size). Use when picking up a PR after the build stage, or when an automation triggers the post-build workflow.
---

# Post-Build Pipeline Stage

Use this skill to take a PR from "build finished" to "provably ready to merge". It is the downstream orchestrated review stage that execute's **pipeline** posture declares exists; when this stage runs, `REVIEW.md`, `QA.md`, and remediation briefs are its property, not the build's.

This skill exists to prevent common post-build failures:

- Review runs against the diff alone, unanchored from the plan's intent and acceptance criteria.
- Findings a reviewer could fix in place ride a full dispatch loop — separate fixer, then re-review — multiplying agents for one-line defects.
- Findings reach a fixing agent as an orchestrator's paraphrase instead of the reviewer's own brief, and worker prompts are re-derived long-hand each run instead of naming the versioned worker skills.
- Remediation quietly widens beyond the accepted findings, or the reviewer who raised a finding rubber-stamps the delegated fix for it.
- QA runs before review has settled the code, drives a deployment never proven to be the candidate commit, or runs against changes it cannot actually test.
- QA results are committed after testing, so the merged commit is not the tested commit.
- Required checks are polled and babysat throughout the run, and failing checks on trivial or non-functional changes burn fix cycles that belong to a human.
- Fix loops run unbounded, or a stuck run guesses instead of stopping with a specific handoff.
- Plan discovery is ambiguous and the stage picks a folder by number, recency, or vibes.
- A one-size-fits-all full stage burns budget on trivial or non-functional changes, or invents plan ceremony where none is needed.

The orchestrator running this stage **coordinates by default**: it discovers, classifies, delegates, checks handoffs between phases, and emits the final report. It does not edit functional code, perform independent review of functional changes, drive a browser, or prove a deploy itself — those phases are dispatched workers. **Exception:** for trivial or small non-functional changes, the orchestrator may absorb the entire stage (see Change Classification).

## Portable vs. Adapter

This skill owns the portable stage semantics. Everything repo-specific comes from a **repo adapter skill** that the triggering automation or operator loads alongside it. The adapter must supply:

- **Production boundaries**: which branches, deploy targets, and data surfaces are production and must never be touched.
- **Deploy-proof mechanics**: the commands that push, wait for a deployment, prove a deployment corresponds to an exact commit SHA, and health-check the deployed URL.
- **Required checks**: which CI / required status checks must pass on the candidate SHA before merge-readiness. Absent an explicit set, use the platform's required checks for the PR; if none are knowable, say so in the report and do not invent green.
- **QA environment**: how the deployed URL is derived, seeded/committed test identities and their sign-in routes, required environment setup, and environment caveats QA prompts must state.
- **Worker routing**: which agent types or models run each phase in the local harness.

Authority order when they conflict: the repo's own hard limits, then the adapter, then this skill, then the triggering prompt's run context. If a required adapter capability is missing (for example there is no way to prove a deployment's SHA), skip the dependent phase explicitly and say so in the report — never fake the proof.

## Dispatching Workers

A worker's prompt has two parts, kept strictly separate:

- **Static direction** — the worker's own skill, named in the dispatch. Each phase has a registered worker skill whose description marks it as dispatch-only; the worker loads it, you never do. Do not load, inline, or paraphrase a worker skill into a prompt — the point of the split is that the instruction text never enters your context at all.
- **Dynamic context** — the few situational lines only this run knows: repository and branch, plan folder, SHAs, proven URL, finding IDs and brief paths, adapter specifics. You write exactly this part, and nothing more.

A dispatch therefore reads: "Load the `<worker skill>` skill — it is your task discipline. Situational context: …".

| Phase | Worker skill | Dynamic context |
|-------|--------------|-----------------|
| Independent review | `comprehensive-review` | PR, plan folder or no-plan note |
| Remediation fix | `post-build-fixer` | branch, plan folder, path to the reviewer's per-finding remediation brief (routed by path, never restated) |
| Remediation verification | `post-build-verifier` | branch, plan folder, reviewed SHA, new candidate SHA, findings claimed resolved |
| QA planning | `post-build-qa-planner` | branch, plan folder, adapter QA environment notes |
| Deployed QA | `post-build-qa-driver` | proven URL, candidate SHA, `QA.md` path, adapter identities/setup |

The adapter's worker routing picks the agent or model.

## Discovery

Resolve plan context before classifying or delegating:

1. **Marker first.** The PR body's `Workflow-Plan: docs/plans/<NN>-<slug>/` line is the primary and only preferred locator.
2. **Diff fallback** (markerless PR that still carries a plan folder): compute the merge base against the PR's base branch, list changed files under `docs/plans/`, and form candidates from the unique parent directories of changed `IMPLEMENTATION.md` files — or, if none, of changed `PLAN.md` files. Require exactly one candidate. Never tie-break by folder number, modification time, or lexical order — on zero or several candidates, stop and report them, requesting an explicit plan path.
3. **No plan folder at all**: classification decides the path:
   - Trivial / small **non-functional** changes: proceed without a plan folder; record `Intent source: ad-hoc` in the report.
   - **Functional** (or mixed / large ambiguous) changes: dispatch `comprehensive-review` as usual — it reconstructs intent into `RECOVERED-INTENT.md` and reviews at reduced confidence. A PR that skipped the workflow still gets a real review of functional risk.
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
| `trivial` or `small` + `non-functional` | **Absorb:** orchestrator runs the whole stage inline — light diff skim, end-of-work checks read, report. No plan folder, no delegated review, no QA, no deploy proof, and **no fixing of failing checks** — report them and leave them. Execution mode: `absorbed`. |
| `normal`/`large` + `non-functional` | Light delegated or absorbed review as appropriate; end-of-work checks read; skip QA and deploy proof; failing checks are reported, not fixed. |
| `functional` or `mixed` (any size), with or without a plan | Independent review (delegate; intent recovered if needed). End-of-work checks gate with one bounded fix cycle available on failure (non-trivial sizes only). **QA + deploy proof only if** there is at least one user-facing / driveable criterion or residual risk that requires a live UI. Internal-only functional changes still get review + the checks gate; skip browser QA unless the adapter defines a non-browser substitute. |
| Ambiguous recovered / large functional | Full stage at reduced confidence — today's thorough path. |

**Absorption limits.** Never absorb: independent review of functional or mixed changes; verification of delegated remediation; browser QA; exact-SHA deploy proof. Those stay dispatched workers when they run. Absorption is for cheap confidence on non-functional risk, not for proving contested fixes.

## Safety Invariants

- Never write to production deploy targets or production data. The adapter defines them; absent an adapter, treat every deployment target as production and stop before deploy verification.
- This stage never merges. Stop on any request or temptation toward merge, force-push, destructive git operations, or merge-state changes — merge-readiness is reported, not acted on.
- Never broaden the active plan or discard unrelated work found on the branch.
- Browser QA runs only against a deployment proven to be the candidate SHA on a non-production target — never localhost, never an assumed URL — and only when classification says QA is applicable.
- Final SHA-specific QA results and media go to the PR or automation output, never a trailing commit: a commit added after testing changes the SHA, and the merged commit must be the tested commit.

## Workflow

Order is load-bearing: review settles the code first; QA tests only settled, reviewed code; required checks are read **once**, after the last code-changing phase — never polled between phases.

1. **Preflight, discovery, and classification** (above). Stop before any delegation on a failed precondition; do not create missing plan artifacts just to keep going. On a re-triggered run, resume rather than repeat: committed artifacts already bound to the current candidate SHA count as done (a passing `REVIEW.md` for this SHA skips review; an existing `QA.md` matrix skips planning; recorded cycles count against the bounded loops). On the absorb path, skim the diff, then jump to step 6.
2. **Independent review.** Dispatch `comprehensive-review` against the PR. The reviewer assesses against `PLAN.md`'s acceptance criteria (or recovered intent), challenges the assumption ledger, **fixes straightforward findings in place**, and authors a remediation brief per structural finding it cannot safely fix. Its verdict (`PASS`, `PASS_WITH_FOLLOWUPS`, `REMEDIATE`) reflects the post-fix state — findings the reviewer resolved and verified are closed and need nothing further from this stage.
3. **Remediation** (only on `REMEDIATE`). Dispatch a `post-build-fixer` per accepted briefed finding, with dynamic context naming the branch, plan folder, and the path to the reviewer's remediation brief (routed by path, never restated). The fixer touches only its finding, runs the brief's done evidence, and records the resolution in `REVIEW.md` without erasing the original finding.
4. **Verification** (only when step 3 ran). Dispatch a fresh `post-build-verifier` — not the reviewer, not a fixer — to verify the remediation delta and update `REVIEW.md`'s verdict for the new SHA. One remediation cycle, one verification: if a `blocker` or `high` finding still stands, stop and hand off. Fixes the reviewer applied in place during step 2 do not trigger this step.
5. **QA planning** (only when QA is applicable — functional/mixed surface with at least one driveable user-facing criterion or review residual that needs a live UI). Dispatch a `post-build-qa-planner`: it derives `QA.md` from acceptance criteria and `REVIEW.md`'s residual risks and commits it now, before the candidate SHA exists. When QA is not applicable, record `QA: SKIPPED (<reason>)` — do not invent a matrix for undriveable-only or non-functional work.
6. **Required checks (single end-of-work gate).** With every artifact and fix committed, capture the candidate SHA and read the adapter's required checks on that SHA **once**; if still running, wait for them to conclude without poking, redeploying, or "helping". Then:
   - **Pass** → continue.
   - **Fail on a `functional`/`mixed`, non-trivial change, clearly caused by this PR** → one bounded fix cycle: diagnose, fix in scope, recommit, re-read checks on the new SHA. Still failing → stop with `HUMAN_ACTION_REQUIRED`.
   - **Fail on anything else** (trivial, non-functional, or not caused by this PR) → leave the checks failing; report them and downgrade the status. Do not babysit.
   - If no checks are knowable, say so explicitly and do not claim they passed.
7. **Deploy verification** (only when QA will run). Using the adapter's mechanics, prove a non-production deployment of **exactly the candidate SHA** is live, resolve its exact URL, and health-check that same URL. Branch-level "ready" signals are not SHA proof; a zero exit code is not SHA proof. Retry only inside this phase; if the SHA cannot be proven, stop before QA. When QA is skipped, record `Deploy proof: SKIPPED (<reason>)`.
8. **Deployed QA** (only when deploy proof succeeded). Dispatch a `post-build-qa-driver` against the exact proven URL with the adapter's identities and setup. One QA remediation cycle: fix only evidenced failures (a fixer per step 3's mechanics), recommit, re-read checks on the new SHA, re-prove the deployment, rerun affected and risk-adjacent cases. A failure needing a structural fix, or failures remaining after the cycle → stop and hand off.
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
Review verdict: <verdict|ABSORBED_LIGHT|SKIPPED>; in-place fixes: <n>; remediation cycles: <0|1>
Required checks: <check>: PASS|FAIL|PENDING (<evidence>) per line; fix cycle: <0|1|N/A>
Deploy proof: RUN | SKIPPED (<reason>)
QA: RUN | SKIPPED (<reason>)
QA cases: <case ID>: PASS|FAIL|NOT_RUN — <evidence> per line; QA remediation cycles: <0|1>
Remaining non-blocking findings: <IDs or none>
Blocker / human action: <specific action or none>
After merge: close out <plan folder> via the close-out skill | N/A (no plan folder)
```

Never report `PASS` while required checks are failing or still pending. Never report `PASS` while exact-SHA proof or an **applicable** QA case is missing — "applicable" means classification selected QA and a driveable case exists; skipped QA for non-functional or undriveable-only work is an honest skip, not a missing gate. Downgrade honestly.

## Rules

- Coordinate by default; absorb only for trivial/small non-functional work within the absorption limits.
- Worker prompts name the worker's skill plus orchestrator-written dynamic context; never load, template, or restate a worker skill's instructions.
- Exactly one active plan folder when one is needed, resolved marker-first; ambiguity stops the stage rather than being tie-broken. Ad-hoc non-functional work may have no plan folder.
- Review and QA are keyed to `PLAN.md` (or recovered intent) acceptance criteria when those artifacts exist, never derived from the diff alone.
- Findings the reviewer fixed and verified in place are closed — no remediation dispatch, no follow-up review. Delegated remediation always gets fresh verification.
- Remediation is finding-scoped. One remediation cycle per review, one per QA, one checks fix cycle, then stop.
- QA runs after review has settled the code, and only for applicable functional/user-facing need.
- Required checks are read once at the end of the work; failing checks are fixed only for non-trivial functional/mixed changes whose failure this PR caused — otherwise they are reported and left failing.
- `REVIEW.md` accumulates — resolutions are appended, original findings never erased.
- When QA runs, `QA.md` is committed before the candidate SHA and carries the matrix only; executed results stay external. QA targets the exact proven-SHA URL or does not run.
- `medium`/`low` findings may ride along as explicit non-blocking follow-ups; `blocker`/`high` stop the stage.
- The stage reports merge-readiness; it never merges.
- **The stage never closes out the plan folder.** `REVIEW.md` and `QA.md` are live inputs to the phases that follow them, and any commit that removed them would either break a later phase or become the trailing commit this stage exists to forbid. Close-out belongs to whoever ends the change: after the PR merges, on the default branch, via the `close-out` skill. Note it in the merge-readiness report as the remaining step; do not do it here.

## Operator guide

`docs/automation/post-build.md` in the plugin repo is the operator guide for wiring this stage into an external automation trigger — automation shape, trigger discipline, canonical prompt, and canary. It is not loaded during skill execution.
