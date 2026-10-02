# Rotate #2 decision-window and negative-control protocol

**Soft Standard HOLD.** This is a derived protocol/corpus artifact for the
TypeSafe/Luna volume rotation. It does not change workflow behavior, add hooks,
unlock Standard, or use a local `:8080` path. It does not duplicate the merged
#121 336-cell diagnostic or 387-cell miss-identifiability probe.

## Purpose

The #121 probe established descriptive coverage but not a validated FP/miss
reference. This protocol freezes the next join boundary before any future
TypeSafe or Luna cell is interpreted:

1. use exact `(session_id, checkpoint)` keys from the independent outcome
   sidecar;
2. keep a checkpoint-local negative control separate from window status;
3. treat finite decision-window keys as a reference stratum, not as a judge
   hit/miss;
4. reject nearest-checkpoint interpolation, final-length inference, and judge
   output as label evidence.

The runner is
`run_rotate2_decision_window_audit.py`. It is deterministic and idempotent:
rerunning it replaces only its two derived outputs and never mutates
`outcome-labels.jsonl` or any source `results.jsonl`.

## Frozen strata

For an exact labeled key `(session_id, t)`:

| Stratum | Definition | Use |
|---|---|---|
| `negative_control` | `near_done=no` and `runaway_like=no` | control denominator candidate |
| `near_done_guard` | `near_done=yes` and `runaway_like=no` | protects against calling closing work negative |
| `decision_window_positive` | `runaway_like=yes` and `t` is inside a finite effective window | candidate reference-positive stratum |
| `outside_window_observation` | checkpoint is outside a finite window and is not otherwise classified | timing contrast only |
| `unclassified` | any remaining exact labeled combination | retain, do not coerce |

`no_steer_window` is an orthogonal window status. It is not itself a negative
control. A negative control requires both checkpoint-local labels to be `no`.
An `ambiguous` or missing label is never coerced into either control or
positive stratum.

The effective window is `ideal_steer_window_by_cp[str(t)]` when present, then
the session-level `ideal_steer_window`. A finite interval is inclusive.

## Validation gates

The derived audit must pass all structural gates before it is used to plan a
judge join:

- every sidecar session is labeled and passes the existing outcome-sheet
  schema;
- every checkpoint is one of the fixed schedule values;
- every `(session_id, checkpoint)` appears once;
- all rows are exact-key joins;
- no nearest-checkpoint interpolation is performed;
- final session length is not an input;
- all three independence attestations are `false`;
- no ratings, fire fields, result rationales, TypeSafe answers, or Luna answers
  are used as reference labels.

These are protocol-shape gates, not evidence that the labels are correct.
Empirical reference validation additionally requires a second independent
adjudication with retained agreement and an immutable blind transcript-digest
bundle. Only after those gates pass may a separate judge-result join evaluate
descriptive hit/miss candidates. That later join must remain session-clustered,
preserve repeated-cell provenance, and keep `ambiguous`, excluded, and censored
rows out of a binary denominator.

## Reproduction

From the repository root:

```bash
python3 docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/run_rotate2_decision_window_audit.py
```

Outputs:

- `rotate-2-decision-window-controls.jsonl`: one exact labeled
  session/checkpoint row, with stratum and window status;
- `rotate-2-decision-window-audit.json`: structural validation and descriptive
  counts.

No API key is needed for this offline audit. Future TypeSafe/Luna runners must
keep labels out of their request payloads and report HTTP status rates,
cell-ID collisions, prior-ID overlap, and leakage hits independently.

## Current measured result

The current 20-session sidecar yields 67 exact labeled
session/checkpoint keys:

- 3 sessions have finite windows, producing 4 keys in the
  `decision_window_positive` stratum;
- 39 keys satisfy the checkpoint-local `negative_control` definition;
- 24 keys are `near_done_guard` rows;
- window status is 4 `inside_steer_window`, 11
  `outside_steer_window`, and 52 `no_steer_window`;
- protocol-shape validation passes, but empirical reference validation is
  **not complete**.

These counts describe the sidecar population. They are not TypeSafe/Luna
accuracy, FP, miss, hit, or behavior measurements.
