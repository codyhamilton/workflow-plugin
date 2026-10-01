# Proofs — offline replay plan

**Status: not run.** No manifest, no labels, no Jev cache, no metric file. **Confidence: not high.**

This directory is the contract for a future harness. It does not contain that harness. Building it is the next research task, after a transcript directory exists. Running Claude Code, installing a `PostToolBatch` hook, or editing `install.sh` is not that task.

Predecessor proofs that *have* run, and that this plan must not redo:

- `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/run_proofs.sh`
- Closed thresholds and the 12_000-character guard
- Simulation result: `92a48e004519` first `band_exit` at turn 76

Those results are baseline `B`’s definition. They are not progressive-gate results.

## What a finished proof emits

All paths relative to this directory. None of these files exist yet. Do not commit invented JSON.

| File | Stage | Hard numbers inside |
|------|-------|---------------------|
| `validated/corpus_manifest.json` | 1 | `n_workers_ge_75`, `priority_found`, sha256, `T`, bytes |
| `validated/schema_budget.json` | 2 | Per snapshot cell: median `state_chars`, max `state_chars`, `n_over_budget` |
| `validated/gold_labels.jsonl` | 3 | One row per judge per prefix |
| `validated/gold_agreement.json` | 3 | Alpha, pairwise kappa, per-worker spread, `invalid_label_rate` |
| `validated/jev_cache.jsonl` | 4 | One row per cache key, or `missing` |
| `validated/sweep_metrics.json` | 5 | Overshoot, false early, false late, `max_allowed_turns`, length bins, baselines `B` and `C` |
| `validated/LOCK.md` | 7 | Either a cell that survived the lock rule, or “no cell survived.” Absent until then |

Stage 0 of interpretation is the agreement file. If `gold_agreement.json` has `alpha < 0.40`, `sweep_metrics.json` may exist as a diagnostic and `LOCK.md` must say the sweep is not a recommendation (H5).

## Stage 1 — manifest

Input: a directory of Claude JSONL supplied at run time, not vendored here.

```
for each file:
  T = count of records with type=assistant and not isSidechain,
      deduped by message.id when present
  keep if T >= 75
write corpus_manifest.json
```

Priority lookup by id substring:

- `92a48e004519` expected `T = 296` if it is the maps file. A file with that id and a different `T` is `priority_mismatch` and is not silently relabeled.
- `bb6165018de0` expected `T = 154`, same rule.
- `6c87c96bd9bb` expected `T = 70`. It is written to `negative_control`, not to the corpus list.

If the directory is missing, the only legal output is:

```json
{
  "status": "blocked",
  "n_workers_ge_75": 0,
  "priority_found": {"92a48e004519": false, "bb6165018de0": false},
  "reason": "transcript directory not configured"
}
```

That file would be the first hard number. It is not checked in today because the directory has not been configured and an empty blocked file would look like a completed search.

## Stage 2 — schema budget

For each corpus worker and each snapshot cell in [`../TUNING-PLAN.md`](../TUNING-PLAN.md), build the state from the prefix and record `len(json.dumps(state, ensure_ascii=False))`.

Pass condition for a cell to be eligible for Jev: after the shrink order in [`../TERMS.md`](../TERMS.md) §5, `state_chars <= 12000`. Cells that still overflow are `ineligible`, with `n_over_budget` reported. No API call.

This stage can falsify “hybrid v0 fits,” which is a precondition of H2. It cannot support H1.

## Stage 3 — gold

Prompt body: the pattern definitions and the “not this” contrasts from [`../GOLD-LABEL-RUBRIC.md`](../GOLD-LABEL-RUBRIC.md), **without** the hindsight illustrations that state 296, 154, 130k, or 12.7MB. Store `judge_prompt_sha256` in `gold_agreement.json`. Store `rubric_sha256` of the full auditor file beside it. If those hashes ever match, the judge was shown the endings and the gold is invalid.

Label row:

```json
{
  "worker_id": "92a48e004519",
  "sha256": "…",
  "turn": 105,
  "judge": "grok-4.7-high",
  "judge_model_id": "…exact…",
  "view": "prefix",
  "answer": "not_yet",
  "patterns": [],
  "rationale": "…<=120 words…",
  "bundle_chars": 48000,
  "invalid_reason": null
}
```

`view` is `prefix` or `hindsight`. Hindsight rows are a second pass.

Agreement file must include `alpha`, `alpha_method` (`krippendorff`), `n_prefixes`, `n_judges_min`, `pairwise_kappa`, `h5_pass` (boolean, true only if alpha ≥ 0.40).

## Stage 4 — Jev cache

Request shape, pin `jev-1.13.0`:

```json
{
  "model": "jev-1.13.0",
  "state": {},
  "questions": {}
}
```

Questions are TERMS §6 for `Y_full` or `Y_choice_only`, and the resolved `session-progress` pair for `Y_legacy`. State is the snapshot, including `question_id: session-checkout` for the v0 sets.

Cache row:

```json
{
  "worker_id": "…",
  "checkpoint_turn": 90,
  "snapshot_mode": "hybrid_v0",
  "snapshot_params": {"N": 8, "excerpt": 400},
  "question_set": "Y_full",
  "state_chars": 0,
  "request_chars": 0,
  "shrink_steps": [],
  "decision": "missing",
  "reason": "dry_run",
  "answers": null
}
```

`decision` becomes `continue`, `inconclusive`, or `checkout` only when `answers` is present. A dry-run stays `missing`. Downstream, missing is fail-open and is counted in `missing_rate`, not in `continue`.

Pilot budget: 23 calls (16 prefixes on the 296-turn file, 7 on the 154-turn file), one snapshot, `Y_full`. Wave 2 expands only after the pilot’s `schema_budget` rows for those calls are under 12_000.

Endpoint and key handling, if the harness is later copied from this repo, follow `tools/transcript/lib/jev_client.py` (`https://api.typesafe.ai/v1/systemone`, `TYPESAFE_API_KEY`). The harness does not add a new client in this pack.

## Stage 5 — sweep

Pure function of `gold_labels.jsonl`, `gold_agreement.json`, and `jev_cache.jsonl`. No network.

For each policy sheet (schedule × `confidence_min` × `on_uncertain`) and gold rule `A0`:

- `gate_exit`, `overshoot`, `false_early`, `false_late`, `on_time`, `within_one_interval`, `max_allowed_turns`
- the same aggregates in bins `T < 100`, `100 <= T <= 150`, `T > 150`
- smoking-gun slice repeated as its own object
- baselines `B` and `C` as sibling objects

Robustness: repeat the aggregates for `A1` and `A2`. Do not argmin over gold rules.

`sweep_metrics.json` top-level fields:

```json
{
  "status": "diagnostic",
  "h5_pass": false,
  "gold_rule_primary": "A0",
  "p0": {},
  "baselines": {"B": {}, "C": {}},
  "cells": [],
  "length_bins": {},
  "smoking_guns": {}
}
```

`status` may be `diagnostic` or `eligible_for_lock`. It is `eligible_for_lock` only when `h5_pass` is true and `missing_rate` on `P0` is 0 for the priority files (every checkpoint got an answer). A dry-run corpus is `diagnostic` forever.

## Stage 6 — negative control

On `6c87c96bd9bb` (`T = 70`), assert:

- `checkpoints(75, 15, 70)` is empty
- `checkpoints(90, 10, 70)` is empty
- `checkpoints(60, 15, 70) = [60]`
- `max_allowed_turns` under every `first_at >= 75` equals 70

A failure here is a parser bug, not a scientific result. Fix the parser before reading H1.

## Stage 7 — lock memo

`LOCK.md` is allowed to exist only when stage 5 status is `eligible_for_lock`. It applies the lock rule in the tuning plan. Outcomes:

| Outcome | Wording the memo is allowed to use |
|---------|-------------------------------------|
| No cell survives the false-early caps | “No cell survived. `P0` results are attached. The design is not high-confidence.” |
| `P0` survives and wins the sort | “`P0` is the best cell under the pre-registered rule. High confidence still requires Cody to accept behaviour; this memo does not install a hook.” |
| Another cell wins | “`P*` beat `P0` for the stated reason. Promoting `P*` is a proposal edit, not a hook change.” |

The memo includes the literature transfer table from the tuning plan, filled with the numbers from `sweep_metrics.json`. Empty cells in that table mean the memo is unfinished.

## Explicitly not a proof stage

- A Claude Code session that fires `PostToolBatch`
- Hook `additionalContext`, a parent chat message, or any other feedback channel
- Edits to `gate_thresholds.py`, `jev_signal_schemas.py`, `assert_phase.py`, `install.sh`, or default settings
- Classify agreement
- A reconstructed JSONL that imitates the maps aggregates

## Definition check the harness must unit-test without transcripts

These are pure functions. They are the only tests that can land before the corpus exists, and they still do not raise confidence in the scientific claims.

| Function | Assertion |
|----------|-----------|
| `checkpoints(75, 15, 296)` | `[75, 90, …, 285]`, length 15 |
| `checkpoints(75, 15, 154)` | `[75, 90, 105, 120, 135, 150]` |
| `checkpoints(75, 15, 70)` | `[]` |
| `R(t=3)` on choice `checkout` with confidence 2 | does not fire |
| `R(t=3)` on choice `checkout` with confidence 3 | fires |
| `R` on `inconclusive` with `on_uncertain=open` | does not fire |
| `R` on `missing` with `on_uncertain=open` | does not fire, and the row is not labeled `continue` |
| Overshoot signs | the six imagined rows in TERMS §8 |
| State guard | a dict whose JSON is 12_001 characters is rejected before POST |

A future patch may add those tests under this directory. This revision does not, because a green unit test of the arithmetic would be easy to mistake for a replay. The assertions live here so the harness author does not invent a second definition of `gate_exit`.
