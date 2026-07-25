---
name: close-out
description: End a plan by collapsing its entire folder into a single record file at `docs/plans/<NN>-<slug>.md` — what was built, per phase, what deviated from the plan, how review and QA resolved, and where follow-ups went. The folder and every artifact in it are deleted. Use when a plan's work is finished: dispatched by `execute` at the end of a terminal-posture run, or invoked directly after a pipeline-posture PR has merged.
---

# Close-Out

Use this skill to end a plan. A plan folder accretes: `PLAN.md`, `DESIGN.md`, `PROVENANCE.md`,
`briefs/`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, remediation briefs, sometimes a tree of child
folders. Every one of those is written for a consumer inside the run. When the run is over the
consumers are gone, and what remains is a pile a future reader has to sift to answer one question:
what did this change do, and why.

Close-out answers that question once, in one file, and deletes the pile.

**The output is a single markdown file. The folder does not survive.** `docs/plans/<NN>-<slug>/`
becomes `docs/plans/<NN>-<slug>.md` — same number, same slug, `.md` appended, folder removed. One
phase or six, one child plan or five, the result is always exactly one file. If the folder still
exists when you are done, the close-out did not happen.

**The enabling principle: the branch history and the PR are the archive; the record file is the
record.** Nothing deleted here is lost. Every brief, every review, every provenance turn stays in the
commits that introduced them, reachable by `git log` forever. What close-out removes is not the
information — it is the requirement that every future reader wade through it.

This skill exists to prevent common failures:

- Plans that simply stop, leaving a folder that looks like work in progress years later.
- A collapse that only half-happens: the Outcome gets written, the folder and its interim files stay.
- A reader who has to reconstruct the actual outcome by diffing the plan against the implementation
  notes against the review.
- Interim artifacts kept "just in case", which is how a plan folder becomes a second, worse copy of
  the git history.
- A record that preserves dead conventions — `[NEW]-` prefixes, status markers, ROADMAP pointers —
  from whatever the repo's convention was when the plan was written.
- Deletion of artifacts that were still load-bearing — closing out a run that had not finished, or
  that still had open blockers.
- A record that restates the plan instead of recording what actually happened.

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
- **A `blocker` or `high` finding still stands.** An open finding is live state; a record file
  cannot absorb it. Remediate or hand off first.
- **The change has not landed and is not being abandoned.** A plan folder for work still in review
  is not finished, whatever its artifacts look like.
- **You cannot establish what actually happened.** If the artifacts do not let you write an honest
  record, say what is missing instead of writing a vague one.

Abandoned work is closed out, not left. Either write a record that says the work was abandoned, how
far it got, and why — or delete the folder outright when nothing was built. What it must not do is
sit there looking like work in progress forever.

## What survives

- **The record file** — `docs/plans/<NN>-<slug>.md`, structured as below. This is the whole output.
- **`DESIGN.md`** — promoted to `docs/design/` when it reifies contracts that outlive this change
  (a shape other work will implement against, an ownership boundary, a target architecture). Deleted
  when it was scaffolding for this change alone. Promote by moving the file and generalising its
  framing out of this plan's tense; leave a pointer to it in the record.
- **Follow-ups** — non-blocking findings and deferred work do not survive as files. Each goes to a
  tracker issue or a design-intent doc in `docs/design/`, and the record says where.

Everything else is consumed: `PLAN.md` itself (its durable content is carried into the record),
`PROVENANCE.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`, `briefs/` including remediation briefs,
`RECOVERED-INTENT.md`, `ROADMAP.md`, and every child plan folder. Delete the folder.

## The record file

One file, this structure, in this order. It is written for someone who has never seen this change
and is not going to read the git history.

```markdown
# <Plan Title>

<One paragraph, past tense: what this change was, what it did, and whether it did what it set out
to do. Read first by everyone; write it last.>

## Intent

User request, verbatim:

> <carried from PLAN.md's Intent section, unchanged>

## Why This Existed

<The problem this solved and why it mattered then. Past tense — the reader is in the future.>

## What Was Built

<What actually shipped: the surfaces, contracts, and behavior that now exist. This is the record of
the actual, not the plan's wording.>

**Changed:** <files, modules, and surfaces touched — enough to locate the change in the tree and in
the history, not a file list.>

### Phase N — <name>

<One per major phase, in the order they ran, only when the plan had more than one. Each: what that
phase delivered, and any deviation or discovery specific to it. A former child plan folder becomes
one of these sections. A single-phase plan has no subsections at all — the prose above is enough.>

## Deviations

<Where the implementation differed from the plan's wording, and why. This is the most valuable
section in the file; do not smooth it away. "None" is valid and should be rare.>

## Review

<Verdict, what was found, how each blocking finding resolved, and where review happened — in-run, or
the pipeline stage on PR #N.>

## QA

<What was exercised and the result — or the honest skip and its reason. In pipeline posture the
executed results live in the PR and the automation output; point at them rather than restating.>

## Residual Risks

<What is known to be unproven or fragile, or "None identified".>

## Follow-ups

<Each non-blocking item and where it went — issue number, design doc path — or "None".>

## Decisions Worth Keeping

<Rationale from PROVENANCE.md, the assumption ledger, or the run that a future reader would
otherwise have to rediscover: a tradeoff taken deliberately, an approach rejected for a reason that
still holds, an assumption that proved load-bearing. Omit the section entirely if there is nothing
of this kind — do not manufacture entries.>
```

Sections that do not apply are omitted, not filled with "N/A" — except `Deviations`, `Review`,
`Residual Risks`, and `Follow-ups`, where the absence is itself information and the explicit "None"
is the honest answer.

### Writing it

- **Carry, do not concatenate.** The record is written from the artifacts, not assembled by pasting
  them. Scope, acceptance criteria, execution phases, and the assumption ledger are not sections of
  the record — what survives of them is whatever "What Was Built", "Deviations", and "Decisions
  Worth Keeping" need to be true and legible.
- **Acceptance criteria resolve, they do not persist.** A criterion that was met is described in
  "What Was Built". A criterion that was not met is a deviation, a residual risk, or a follow-up.
  Never copy the criteria list forward.
- **Strip dead conventions.** `[NEW]` prefixes, status markers, folder-status taxonomy, `ROADMAP.md`
  pointers, parent-program language, references to child plan folders that no longer exist, and
  paths into the deleted folder — none of these appear in the record. Rewrite the sentence rather
  than leaving a dead reference. Where a dead convention is genuinely part of what happened, name it
  in the past tense as history.
- **Size.** A closed record is typically 60–150 lines. Past roughly 200 you are transcribing rather
  than recording; the archive already holds the detail.
- **Do not restate the plan.** If a section would only repeat what the plan already said, the honest
  content is that it went as planned.

## Workflow

1. Establish posture and check the preconditions. Stop and report if any fails.
2. Read everything you are about to consume: `PLAN.md`, `IMPLEMENTATION.md`, `REVIEW.md`, `QA.md`,
   `PROVENANCE.md`, the briefs, and every child folder's artifacts. This is the only time they will
   be read as a set; read them before deleting anything.
3. Resolve `DESIGN.md`: promote to `docs/design/` or drop it, and note which in the record.
4. Move each non-blocking follow-up to a tracker issue or a design-intent doc, and note where.
5. Write `docs/plans/<NN>-<slug>.md` — the structure above, phases as sections when the plan had
   more than one.
6. Delete `docs/plans/<NN>-<slug>/` entirely, children included (`git rm -r`).
7. Verify the collapse: the folder is gone, the file exists, and nothing under `docs/plans/<NN>-*`
   is a directory. Confirm no path into the deleted folder survives anywhere in the repo.
8. Commit as one close-out commit — the new record and every deletion together, so the commit reads
   as a single legible "closed out X" in the history.

## Rules

- One plan, one file. The folder is deleted, not emptied. A closed plan with a surviving directory
  is a failed close-out.
- The record file is named for the folder it replaces: same `NN`, same slug, `.md`. Never renumber,
  never re-slug — a merged PR's `Workflow-Plan:` marker must stay mechanically resolvable to it.
- The branch history and the PR are the archive; the record file is the record. Delete confidently,
  and never delete anything that is not already committed.
- One commit. A close-out split across commits makes the history harder to read, which defeats it.
- Never close out unfinished work, or work with an open `blocker`/`high` finding.
- Never close out a PR branch a pipeline stage is working, or one that has not merged — that is the
  trailing-commit rule, and it is absolute.
- The record records the actual, not the intent. Deviations are the most valuable section in it.
- The Intent block is verbatim and untouchable. Everything else in the record is rewritten prose.
- No status field, no completion marker, no date stamp, no version. A closed plan is not *marked*
  closed — it is a file instead of a folder, and that is the whole signal.
- Do not copy credentials, tokens, URLs with embedded secrets, or large dumps into the record.
