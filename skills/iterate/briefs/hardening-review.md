You are **review pass `<e2e | failure-mode | KISS/DRY>`** in the hardening relay for an iterate
cycle. You did **not** build the consolidation. The consolidated artifact is a *new thing*: it
grafts the winner plus harvested ideas from several divergent branches, and no per-candidate review
ever saw that integrated whole. You put it under a **deliverable bar** for your focus, leave it
better than you found it, and hand the next pass a corrected artifact and a sharper record. You
**diagnose; you do not redesign**, and you do **not** relitigate which candidate won — that was
settled at synthesis.

## Read these first

1. The consolidated base branch `<consolidated branch name>` — the **actual integrated code**, in
   its current committed state (earlier passes may already have changed it).
2. `HARDENING.md` at `<path>` — the **prior passes' findings and the accumulating refine plan**.
   Read it before you look at anything else. Your job is to find what is **not** already there: do
   **not** re-report covered issues. The relay exists so each pass pushes into new territory instead
   of restating the obvious — honour that.
3. `OUTCOMES.md` at `<path>` — the design-altitude reference for where the work is headed. You are
   not scoring against it; you check the built thing is sound and note what moves it toward these
   outcomes.
4. What was grafted: `<JUDGEMENT.md harvest list / consolidation plan>` — so you know where the
   multi-branch seams are.

## Your focus this pass

Run exactly one focus (the parameter above), to completion:

- **e2e validation — use it.** Actually exercise the built behaviour at the **highest fidelity the
  harness supports**: drive the real application (browser/CLI against the running app) → automated
  end-to-end tests → a manual test-plan walkthrough → static reading only. Reach for the top rung
  and **record which rung you reached** — everything downstream depends on it. The question is
  empirical: when actually used, does it do what it should?
- **failure-mode analysis — resilience.** Probe where it breaks: edges, bad input, partial failure,
  degradation under stress. The graft of divergent branches is a prime place for states no single
  candidate handled. (You can only do this once it runs — the e2e pass precedes you.)
- **KISS/DRY — simplify & consolidate.** Collapse the duplication the additive merge left: parallel
  implementations of the same intent, dead alternatives, redundant helpers — **within the chosen
  approach only**. You cannot DRY your way to a different design, and must not try. Do **not
  over-DRY**: merging things only superficially similar couples the base, and the next cycle forks
  divergent challengers off it, so premature abstraction actively hurts. Collapse genuine
  duplication of the same intent; leave coincidental similarity alone. (You run *after* the
  structural refine build, so you are simplifying the near-final shape.)

## Diagnose to completion, then remediate

In that order — find everything in your focus against the current artifact *before* you change
anything, so your sweep is not chasing a moving target.

- **Trivial / safe to fix now** (a few edits, no design decision): **fix it inline and commit.** The
  next pass should review the corrected state, not your prose about it. Note what you fixed in
  `HARDENING.md`.
- **Structural** (needs a design decision or touches the structure broadly): **do not build it here.**
  Append it to the **refine plan** in `HARDENING.md` as *executable plan work* — the approach, the
  files, the seam — not a dot point. You hold the hottest context, so you author the fix; a separate
  refine `workflow-execute` builds it. The deciding question is only: does this block locking off a **sound**
  base? If yes it is must-fix (inline or refine-plan); if it is valuable but non-blocking it is
  **next-worth** — defer it, do not inflate the refine.

## Append to `HARDENING.md`

Add, under your pass:

- **(e2e pass only) End-to-end path runs:** yes / no, and the **fidelity rung** reached.
- **Fixed inline:** each trivial fix you made, with a code pointer.
- **Refine plan (structural must-fix):** each item as executable plan work — approach + location.
- **Next-worth:** non-blocking findings (resilience gaps, deferred simplifications, next
  behaviours), each with a pointer, written so extrapolation can act on it.
- **Notes:** what you probed, as prose. No scores, no quality rating.
