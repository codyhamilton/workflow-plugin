---
title: First eval scenario from a known workflow-plugin change
status: proposed
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
- `cost-comparison.md` and `quality-comparison.md` for the first run.
- Linked from `FINDINGS.md` and `GOALS.md` success metrics table.

## Skill mapping

Exercises **`design`**, **`refine`**, **`execute`**, **`comprehensive-review`**, **`close-out`**, and **`transcript-parser`** for cost lens.

## Risks

- High variance run-to-run — document timestamp and model policy (Composer, no fast).
