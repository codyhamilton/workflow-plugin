---
title: First eval scenario from a known workflow-plugin change
status: landed
updated: 2026-09-30
author: Workflow Optimiser
date: 2026-09-30
---

# First eval scenario (baseline freeze)

## Problem

`evals/README.md` defines the harness, but **`evals/scenarios/` is empty** — README operating hypotheses cannot move to eval verdicts.

## Proposal

1. Choose a **bounded task** already solved in-repo (e.g. a documented plan under `docs/plans/` with reference `IMPLEMENTATION.md` or analysis case study).
2. Create `evals/scenarios/<slug>/source.md` per schema (repo URL, pinned commit, task text, reference notes).
3. Add `reference/` artifacts (diff or `SUMMARY.md`).
4. Run one full workflow (design → refine/execute per phase) with transcript capture → `results/<slug>/<timestamp>/`.
5. Copy first candidate to `scenarios/<slug>/baseline/` and never overwrite.

## Success criteria

- Non-empty baseline folder.
- A **verifier** result (command, artifact rubric, or trailer completeness) plus cost. Classify output may be attached and does not gate the row.
- Linked from `FINDINGS.md`. Prefer a run the bot drove (status + one-phase trigger) once that path exists; a single orchestrated run is acceptable as the first row.

## Kill line

If the only quality signal is a person reading the diff, leave the scenario empty and say so in FINDINGS. Do not substitute session-kind agreement.

## Skill mapping

Exercises **`design`**, **`refine`**, **`execute`**, **`comprehensive-review`**, **`close-out`**, and **`transcript-parser`** for cost lens.

## Risks

- High variance run-to-run — document timestamp and model policy (Composer, no fast).

## Outcome (2026-09-30)

Landed as a fixture stand-in, not a live multi-phase dogfood.

- Scenario: `evals/scenarios/trailer-completeness/` (`source.md`, `reference/`, `baseline/outcome.json`).
- Verifier: `python3 evals/scenarios/trailer-completeness/verify.py` — shells out to `status.py`, `run.py --once`, and `assert_phase.py --deterministic`. Exit 0 on the reference history.
- Trailers: `trailer-completeness:1`, `trailer-completeness:2`, `trailer-completeness:done`. `other-slug:1` is present and does not close a phase.
- Cost: unavailable — no `ANTHROPIC_API_KEY` or `CURSOR_API_KEY` in the environment that recorded the row. Live provider adapters are still stubs, so a key would not have produced a dollar cost in this tree either.
- Classify was not called. A missing phase trailer fails the verifier (`--omit-trailer`).

The full design → execute dogfood in step 4 of this proposal stays out of scope until a headless provider can actually run a phase.
