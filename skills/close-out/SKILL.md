---
name: close-out
description: End a plan by collapsing its folder to a single PLAN.md with an appended Outcome section — what was built, what changed against plan wording, how review resolved, and where follow-ups went. Use when a plan's work is finished: dispatched by `execute` at the end of a terminal-posture run, or invoked directly after a pipeline-posture PR has merged.
---

# Close-Out

Use this skill to end a plan. A plan folder accretes: `PLAN.md`, `DESIGN.md`, `PROVENANCE.md`,
`briefs/`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, remediation briefs. Every one of those is
written for a consumer inside the run. When the run is over the consumers are gone, and what remains
is a pile a future reader has to sift to answer one question: what did this change do, and why.

Close-out answers that question once, in `PLAN.md`, and removes the obligation to sift.

**The enabling principle: the branch history and the PR are the archive; the plan folder is the
record.** Nothing deleted here is lost. Every brief, every review, every provenance turn stays in
the commits that introduced them, reachable by `git log` forever. What close-out removes is not the
information — it is the requirement that every future reader wade through it.

This skill exists to prevent common failures:

- Plans that simply stop, leaving a folder that looks like work in progress years later.
- A reader who has to reconstruct the actual outcome by diffing the plan against the implementation
  notes against the review.
- Interim artifacts kept "just in case", which is how a plan folder becomes a second, worse copy of
  the git history.
- Deletion of artifacts that were still load-bearing — closing out a run that had not finished, or
  that still had open blockers.
- An outcome record that restates the plan instead of recording what actually happened.

## Postures

Which posture applies is determined by where the change is in its life, not by preference.

- **Terminal.** `execute` ran terminal review posture: the review happened in-run, the change is
  complete on the branch, and nothing downstream will read these artifacts. Close out as the last
  commit before the PR is opened or updated. The PR then shows the whole change, plan folder already
  collapsed.
- **Pipeline.** A downstream stage (`post-build` or an equivalent) reviewed the PR. Close out
  **after the PR has merged**, on the default branch, as its own docs-only commit. Never during the
  stage and never on the PR branch: `REVIEW.md` and `QA.md` are live inputs to the stage's remaining
  phases, and a commit added to the branch after testing would make the merged commit a commit
  nobody tested. The stage reports merge-readiness and stops; close-out is what ends the change
  afterwards.

If you have been asked to close out a PR branch that a pipeline stage is still working, or that has
not merged, stop and say so. Waiting is free; an untested merge commit is not.

## Preconditions

Refuse and report, rather than closing out, when any of these hold:

- **The work is unfinished.** `IMPLEMENTATION.md` is the resume path for a killed or paused run.
  Deleting it mid-flight destroys exactly the recoverability it exists for. Unfinished work stays
  open.
- **A `blocker` or `high` finding still stands.** An open finding is live state; an Outcome section
  cannot absorb it. Remediate or hand off first.
- **The change has not landed and is not being abandoned.** A plan folder for work still in review
  is not finished, whatever its artifacts look like.
- **You cannot establish what actually happened.** If the artifacts do not let you write an honest
  Outcome, say what is missing instead of writing a vague one.

Abandoned work is closed out, not left. Either write an Outcome section that says the work was
abandoned, how far it got, and why — or delete the folder outright when nothing was built. What it
must not do is sit there looking like work in progress forever.

## What survives

- **`PLAN.md`** — always, with `## Outcome` appended. This is the record.
- **`DESIGN.md`** — promoted to `docs/design/` when it reifies contracts that outlive this change
  (a shape other work will implement against, an ownership boundary, a target architecture). Deleted
  when it was scaffolding for this change alone. Promote by moving the file and generalising its
  framing out of this plan's tense; leave a pointer to it in the Outcome section.
- **Follow-ups** — non-blocking findings and deferred work do not survive as files. Each goes to a
  tracker issue or a design-intent doc in `docs/design/`, and the Outcome section records where.

Everything else is consumed: `PROVENANCE.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, `briefs/`
including remediation briefs, `RECOVERED-INTENT.md`, and any child plan folders. Delete them.

## The Outcome section

Append to `PLAN.md`, after everything else. It records the **actual**, and it is written for someone
who has never seen this change and is not going to read the git history:

```markdown
## Outcome

<One paragraph: what was built and whether it did what the plan set out to do.>

**Changed:** <files, modules, and surfaces touched — enough to locate the change, not a file list.>

**Deviations:** <where the implementation differed from the plan's wording, and why. "None" is a
valid answer and should be rare.>

**Review:** <verdict, what was found, how each blocking finding resolved. Where review happened
(in-run, or the pipeline stage on PR #N).>

**QA:** <what was exercised and the result — or the honest skip and its reason. In pipeline posture
the executed results live in the PR and the automation output; point at them rather than restating
them.>

**Residual risks:** <what is known to be unproven or fragile, or "none identified".>

**Follow-ups:** <each non-blocking item and where it went — issue number, design doc path — or
"none".>
```

Write it from the artifacts, not from memory, and do not restate the plan. If a section would just
repeat what `PLAN.md` already says above it, the honest content is "as planned".

## Workflow

1. Establish posture and check the preconditions. Stop and report if any fails.
2. Read the artifacts you are about to consume: `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`,
   `PROVENANCE.md`, and the briefs. This is the only time they will be read as a set; read them
   before deleting anything.
3. Append `## Outcome` to `PLAN.md`.
4. Resolve `DESIGN.md`: promote to `docs/design/` or delete, and record which in the Outcome.
5. Move each non-blocking follow-up to a tracker issue or a design-intent doc, and record where.
6. Delete the consumed artifacts.
7. Commit as one close-out commit — the plan update and the deletions together, so the commit is a
   single legible "closed out X" in the history.

## Rules

- The branch history and the PR are the archive; the plan folder is the record. Delete confidently,
  and never delete anything that is not already committed.
- One commit. A close-out split across commits makes the history harder to read, which defeats it.
- Never close out unfinished work, or work with an open `blocker`/`high` finding.
- Never close out a PR branch a pipeline stage is working, or one that has not merged — that is the
  trailing-commit rule, and it is absolute.
- The Outcome records the actual, not the intent. Deviations are the most valuable line in it; do
  not smooth them away.
- No status field, no completion marker, no date stamp, no version. A closed plan folder is not
  *marked* closed — it has an Outcome section and no interim files, and that is the whole signal.
- Do not rename or renumber the plan folder.
- Do not copy credentials, tokens, URLs with embedded secrets, or large dumps into the Outcome.
