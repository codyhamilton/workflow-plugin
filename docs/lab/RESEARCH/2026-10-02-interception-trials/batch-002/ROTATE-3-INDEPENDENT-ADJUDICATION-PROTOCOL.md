# Rotate #3 independent adjudication and blind digest protocol

**Soft Standard HOLD.** This is an offline review protocol and corpus. It
does not change workflow behavior, add hooks, unlock Standard, or use a local
`:8080` path. It does not make FP/miss claims.

## Purpose

Rotate #2 froze exact `(session_id, checkpoint)` window strata but explicitly
left empirical reference validation incomplete. Rotate #3 supplies the
reviewer-facing inputs needed to validate those decisions without exposing the
first adjudication to the second:

- `rotate-3-independent-adjudication-corpus.jsonl` contains 67 exact labeled
  checkpoint keys represented by opaque `review_id` values;
- `rotate-3-blind-digest-bundle.jsonl` is the immutable, label-free digest
  copy of that corpus;
- `rotate-3-adjudicator-a-template.jsonl` and
  `rotate-3-adjudicator-b-template.jsonl` are independent blank sheets.

The generated corpus contains prefix-state projections and digest-only tail
metadata. It omits sidecar labels, window values, final session length, source
paths, project identity, judge ratings, fire fields, and termination causes.
The three OpenCode tail-gated positive keys have local source digests when the
OpenCode store is available; no raw capture is copied into git.

## Independent procedure

1. Freeze the bundle hash and distribute the same corpus to adjudicators A and
   B. Do not distribute `outcome-labels.jsonl`, the tail-positive manifest, or
   any prior adjudicator sheet with the blind bundle.
2. Each adjudicator independently fills every row in their template:
   `near_done`, `runaway_like`, `ideal_steer_window`, confidence, and a short
   rationale. `ambiguous` and `none` are valid values; blank is incomplete.
3. No adjudicator may inspect the other sheet, judge output, a model fire
   decision, final length, or a post-hoc outcome before submitting.
4. Merge only by opaque `review_id` after both sheets are frozen. Check unique
   keys, complete rows, exact checkpoint identity, and agreement separately for
   each decision field. Retain every disagreement and rationale; do not
   majority-vote it away.
5. Only after agreement is retained may the descriptive exact-key join be
   reviewed. Discordant, ambiguous, excluded, and missing rows remain outside
   any binary denominator.

Agreement is a validation gate, not a product metric. The current templates
are blank, so `independent_agreement` is **not run** and
`reference_validation` remains **not complete**.

## Tail-gated positives

The reference sidecar has four `runaway_like=yes` keys. The remaining three
are `ses_1a0328cd5ffe6iabFeMK` at checkpoints 45, 60, and 75. Rotate #3
recovers digest-only tail metadata from the local OpenCode SQLite source for
those keys; it does not copy raw transcript content or silently turn them into
validated positives. See `rotate-3-tail-positive-manifest.json`.

## Non-Maps controls

The non-Maps representative population has 25 controls:

- 4 exact sidecar-labeled reference controls;
- 21 controls with no sidecar row.

The 21 remain explicitly unlabeled. Their rationale is recorded in
`rotate-3-non-maps-controls.json`: absence of a label, a fire, a window, or a
final-length inference is not a negative label. A future independent sheet
may label them, but this artifact does not manufacture those labels.

## Exact-key TypeSafe/Luna join

`run_rotate3_evidence.py` discovers TypeSafe/Luna result streams, derives
non-destructive rows with `window_status_join.py`, and joins only on exact
`(session_id, checkpoint)`. Checkpoints outside the fixed
`45, 60, 75, 90, 105, 120` schedule are reported as unjoined rather than
interpolated. Rows without both join-key fields are reported as invalid.

Repeated result cells are repeated observations, not independent samples.
Any later descriptive read must be session-clustered and must keep the
reference labels separate from the blind adjudication result.

## Reproduction and boundaries

```bash
python3 docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/run_rotate3_evidence.py
```

The command is offline and idempotent. It writes no `raw/` files and never
calls TypeSafe, Luna, Flash, OpenCode, a hook, or a local server.

All meters are descriptive evidence only:
`soft_standard_hold=true`, `product_wiring=false`, `hooks=false`,
`standard_unlock=false`, `local_8080=false`, and `not_scoreboard=true`.
