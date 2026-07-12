# Wiring post-build into an automation

Operator guide for triggering the `post-build` stage from an external automation. Portable; the worked example is a Cursor Automation, adapt the mechanics for other harnesses. Not loaded during skill execution.

## Shape: one orchestrated automation per stage

The pipeline chains at **stage seams**, through the PR: the build stage lands a PR carrying the `Workflow-Plan:` marker, and that PR is the entire handoff into post-build. Within the stage, run **one automation** whose parent orchestrates all phases as subagents — do not split the phases (review / remediation / QA plan / checks / deploy / QA) into separately triggered automations:

- The stage's cross-phase state — classification, candidate SHA, exact deployment URL, remediation and QA cycle counts, final results — is exactly the state that must never be committed. Chained automations hand off through commits or trigger payloads; a single run holds it in the parent.
- Bounded loops need one authority that remembers. Chained runs would reconstruct cycle counts from artifact archaeology, and a retrigger loop is one parsing bug away.
- The stage commits to the PR branch it watches. A push-triggered chain refires on its own artifact commits; a single automation triggered once has no feedback edge.
- Phase independence already exists inside the run — each phase is a fresh subagent context — so chaining adds trigger plumbing without adding independence.
- Right-sizing (absorb vs orchestrate, skip QA/deploy) is a single-run judgment; splitting phases across triggers would re-litigate classification at every hop.

Merging stays outside: the automation ends at the merge-readiness report.

## Trigger

Trigger **once per build handoff**, not on every push to the branch:

- Preferred: PR opened / marked ready-for-review by the build agent, or a dedicated label (e.g. `post-build`) the build stage applies.
- Manual/operator trigger is equally valid; garcia-music runs this way.
- If the harness only offers push triggers, add a guard to the prompt: exit immediately when the head commit is the stage's own artifact commit (`REVIEW.md`/`QA.md`/remediation), so the automation cannot feed itself.
- Pass an explicit plan-folder path in trigger context only to override discovery; normally the PR's `Workflow-Plan:` marker is sufficient.
- Trivial non-functional PRs may still enter this automation; the skill is expected to classify, wait for checks, and exit early with an absorbed report rather than running the full stage.

## Re-runs and resumability

A re-triggered run resumes; it does not repeat. During preflight, treat committed artifacts already bound to the current candidate SHA as done: a `REVIEW.md` whose recorded SHA matches HEAD and whose verdict is `PASS`/`PASS_WITH_FOLLOWUPS` skips straight past review; an existing `QA.md` matrix skips QA planning; recorded remediation cycles count against the bounded loops. Only unproven phases run. This makes a late flaky failure (usually checks, deploy, or QA) cheap to retry without weakening any gate.

## Configure the automation

1. Create one automation with an orchestrator-capable parent model, granted access to the repository's non-production branches only.
2. Make the workflow plugin's core skills available in the automation context via the plugin's documented install path — do not vendor them into the repository or guess a path.
3. Ensure the repository carries its **adapter skill** (production boundaries, required checks, deploy-proof commands, QA environment, worker routing), with `disable-model-invocation: true` so only the automation loads it.
4. Add the secrets the adapter names to the automation's environment. Pass variable names in prompts, never values.
5. Use the canonical prompt below. Add no extra workflow policy — policy lives in the skill and the adapter, where it is versioned.

## Canonical prompt template

Replace the bracketed values; keep the rest verbatim.

```text
Run the post-build workflow for <PR / current non-production branch>. Load the
workflow plugin's post-build skill for portable stage semantics and
<adapter skill path> for repository routing, safety, checks, deploy, and QA.
You are the parent: coordinate by default; absorb only trivial/small
non-functional changes per the skill. Resolve plan context from the PR's
Workflow-Plan marker (or classify as ad-hoc when none is needed); stop and
report ambiguity instead of guessing. Classify the change (intent source,
surface, size), then right-size: wait for required checks reactively; skip
QA and deploy proof when the change is non-functional or has no driveable
user-facing need; otherwise delegate independent review, bounded
finding-scoped remediation with a fresh re-review, QA planning, exact-SHA
deploy proof, and deployed browser QA per the adapter's routing. Never touch
production, never browser-test localhost, and never commit results after the
candidate SHA is tested. Resume from artifacts already bound to the current
SHA. Return the post-build final output schema.
```

## Pre-wiring checklist

- [ ] Build stage lands PRs with `Workflow-Plan: docs/plans/<NN>-<slug>/` as the first body line (ad-hoc/no-plan PRs are still handled via classification).
- [ ] Adapter skill exists and supplies: production boundaries, required checks, deploy-proof + health-check mechanics, QA identities and sign-in routes, environment setup, worker/model routing.
- [ ] Automation has the adapter's named secrets and non-production repo access.
- [ ] Trigger fires once per handoff (or carries the self-commit guard).

## Canary

Before trusting the wiring, run once against a known-good already-built PR. Expect: classification in the report; for a functional planned PR, committed `REVIEW.md` (verdict + reviewed SHA) and matrix-only `QA.md` on the branch when QA applies, required-checks wait reflected in the report, exact-SHA deployment proof only when QA ran, QA driven only against that URL, final results in the automation/PR output with **no trailing results commit**. Also canary a trivial docs-only PR: expect absorbed mode, checks waited, QA/deploy skipped, no invented plan folder. Any deviation is a wiring or adapter bug — fix it before putting the automation in the path of real PRs.
