# Iterate — Reference

Not loaded during normal execution. Consumers: `workflow-tuning`, and anyone revising this skill
later. Holds the prose that argues iterate's design is *correct*, as distinct from `SKILL.md`,
which holds only what changes an executing agent's behavior in an unspecified situation.

## Reasoning

The whole skill mirrors how developers build things too big to hold in their heads: you put a first
version in code to reify your model, then challenge it *there*, against something concrete, not
against your imagination. Four ideas carry it.

- **Prior builds are the functional spec.** A challenger is never told to "do something different"
  in the abstract; it is handed the previous build(s) as a working contract and told to find a
  genuinely different approach using the lessons those builds made legible. This is why candidates
  are sequential, never parallel, and why they receive real code rather than a paraphrase — that
  sequencing is what makes this more than best-of-n.

- **The divergence bar** is the load-bearing gate, and it works against the grain of how agents
  behave: asked to "find a materially different approach," an agent will always return one and
  rationalize it. Two moves give the gate teeth. First, **invert the default** — the burden of
  proof is on building a challenger, not on stopping; "I cannot find a genuine fork" is the
  expected, valid, and frequently correct answer, and is itself the signal that this layer of
  exploration is exhausted. Second, **split generation from acceptance** across two agents: the
  planner gets wide license (criteria given to a generator become a target it games — reframing a
  fine problem just to clear a bar), while the clean approver holds the tests (criteria given to a
  filter stay a filter). Clearing the bar only earns the right to be built; the candidate must
  still win synthesis. The three tests and the approver's contract live in
  `briefs/divergence-approver.md`; the generative license in `briefs/challenger-license.md` — the
  split between those two files *is* the split between acceptance and generation.

- **The criteria are discovered, not declared.** Synthesis does not score candidates against a
  checklist written before anything existed. It reads the built candidates and surfaces the
  criteria *they* revealed to matter — refining the long-horizon `OUTCOMES.md` — then selects
  against those. This is the "get in the car and drive it before you can assess what counts" step,
  made concrete; the outcomes are a moving target the cycle sharpens, not a spec fixed at step 0.

- **Synthesis is design-altitude, not code review.** Each candidate already received code-level
  review inside its `execute` pass; re-running that misses the point. The question is which approach
  is the better *foundation to keep building on*, not which implementation is most polished — a
  rough build of a superior approach beats a polished build of a dead end, because consolidation
  fixes roughness but cannot fix a bad foundation. The synthesis agent's full remit and its
  load-bearing output ordering (yardstick before selection, so selection cannot be bent to fit a
  favorite) live in `briefs/synthesis.md`. A null result is valid and common — do not invent a
  winner's superiority because a selection was requested.

- **Consolidation is the only convergent phase, so it must verify, not just capture.** Everything
  before it opens options; this is where they close and the gain is banked into the base the next
  cycle forks from. Capture (step 5) is additive — it grafts the winner and the harvest — but the
  grafted whole is a new thing no per-candidate review ever saw, and the multi-branch seam is
  exactly where integration breakage and duplication live. So harden (step 6) is the skill's own
  build→clean-review→repair pattern promoted from the candidate level to the integration level: a
  clean reviewer applies a **deliverable** bar — does it work end-to-end, is it resilient, is it
  free of the graft's duplication — that `OUTCOMES.md`, deliberately design-altitude, does not. The
  bar self-limits: KISS/DRY can only collapse duplication *within* the chosen approach, never
  rearchitect, so the reviewer cannot relitigate selection. A soft base compounds — every later
  sprint builds on it — and the review's findings are also the empirical fuel for extrapolation,
  which is why harden precedes step 7.

- **Harden is a sequential relay, for the same reason candidates are.** Parallel reviewers with
  separate focuses are best-of-n sampling with no divergence pressure: they mode-collapse onto the
  same obvious subset and miss the long tail. Hand each pass the prior passes' findings and tell it
  to push past them, and the reviewers diverge by construction — the *building* thesis (prior as
  spec, find what's different) pointed at *verifying*. Sequential committed passes also buy what
  parallel cannot: no write contention, a refine plan that accumulates safely, and each pass
  reviewing the *corrected* state its predecessors left. The cost is reloading the artifact per pass
  (volume × N) — the same speed-for-coverage trade the skill already accepts for candidates, and
  worth it: N restatements of the obvious is the failure being bought out of. The relay is finite by
  design; "review until clean" is the looping this skill exists to prevent. (The one ordering subtlety:
  DRY runs *after* the structural refine build, because it targets the final shape.)

**Branch isolation and provenance.** Each candidate lives on its own branch off the shared base, so
the candidates are directly comparable; sequential builds mean separate branches suffice — no
worktrees. Never build a challenger by mutating a prior build in place — that destroys the spec.
Losing branches are never deleted: they are the reified alternatives and the richest provenance the
cycle produces, and the spec for any future divergence.
