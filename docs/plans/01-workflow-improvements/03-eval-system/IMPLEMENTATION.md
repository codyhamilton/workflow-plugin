# Implementation: 03 — Eval System

## What Was Built

Five file changes implementing the eval system pattern.

### Files Changed

**`evals/README.md`** (new)
Complete eval system documentation: two-lens model (cost + quality), scenario format (`source.md` schema, `reference/`, `baseline/`), results format (`cost-comparison.md` and `quality-comparison.md` schemas with templates), run instructions (7 steps), interpretation guidance (two questions, variance note), and fixture corpus model.

**`evals/scenarios/.gitkeep`** / **`evals/results/.gitkeep`** (new)
Empty placeholder files establishing the directory structure. Fixture corpus ships empty.

**`skills/workflow-tuning/SKILL.md`** (modified)
Added `## Eval Capability` section covering: when to run an eval, how to run an eval (6 steps with timestamp format, baseline immutability guard, per-agent+total tool turns), how to interpret results, and variant testing (separate timestamped result folders per candidate).

**`skills/workflow-tuning/reference.md`** (modified)
Appended `## Eval Patterns` section as a growing record of non-obvious lessons from actual eval runs. Initially seeded with guidance on what belongs there vs. what does not.

## Deviations from Plan

None. All five execution phases completed. The scope-level design (e2e eval, two lenses, relative comparison, empty corpus) was established during planning and implemented as specified.

## Tradeoffs

**Human judgment for quality.** The quality lens is intentionally loose — "significant delta?" and "same ballpark?" — rather than automated. This is a tradeoff: consistent results require human review, but automated quality rubrics for open-ended implementation tasks are either too rigid or too easy to game. The loose frame is correct for v1; automation is a future candidate once the pattern is proven.

**Per-agent + total for tool turns.** Review found a discrepancy between the README schema (total only) and SKILL.md (per agent). Fixed by documenting both — per-agent breakdown for diagnosis, total for comparison. This adds a field but removes ambiguity about what to record.

**Baseline is fixed on first run.** An unlucky first run permanently anchors all future comparisons. This is a known fragility but acceptable for v1 — the alternative (multiple baseline runs, averaged) adds complexity before the system has proven value.
