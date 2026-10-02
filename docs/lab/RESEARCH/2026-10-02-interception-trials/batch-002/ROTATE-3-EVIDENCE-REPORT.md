# TypeSafe/Luna volume rotate #3 — Soft HOLD evidence report

**Soft HOLD only.** No behavior ship, hooks, Standard unlock, local `:8080`,
or FP/miss scoreboard claim.

## Result

Rotate #3 adds the missing review and provenance artifacts:

| Artifact | Count / status |
|---|---:|
| exact labeled checkpoint rows in blind adjudication corpus | 67 |
| opaque review IDs | 67 unique |
| independent adjudicator templates | 2 |
| reference sidecar sessions | 20 |
| reference positive keys | 4 |
| tail-gated positive keys addressed with source digest metadata | 3 |
| non-Maps controls | 25 |
| non-Maps labeled reference controls | 4 |
| non-Maps explicitly unlabeled holdouts | 21 |
| independent agreement | not run |
| empirical reference validation | not complete |

The three remaining tail-gated keys are
`ses_1a0328cd5ffe6iabFeMK@45`, `@60`, and `@75`. Their local OpenCode source
was available for digest-only tail metadata. This addresses source/evidence
availability, not the adjudication or label-validity gate.

## Blindness and adjudication

The blind bundle contains no `near_done`, `runaway_like`,
`ideal_steer_window`, `window_status`, termination, judge, or fire fields.
It contains opaque IDs, fixed checkpoint values, sanitized prefix state, and
digest-only tail metadata. A and B receive independent blank templates and
must submit before any merge with the existing sidecar.

The bundle is therefore review-ready, but not review-complete. No agreement
number is reported until two completed sheets are merged and disagreements are
retained.

## Exact-key TypeSafe/Luna join

The offline join covers the TypeSafe/Luna result streams currently present in
batch-002:

| Measure | Count |
|---|---:|
| source result rows | 53,194 |
| rows with both join-key fields | 51,191 |
| exact `(session_id, checkpoint)` joined rows | 28,738 |
| valid-key rows without exact label join | 22,453 |
| rows missing a usable join key | 2,003 |
| total unjoinable/unjoined rows | 24,456 |
| unique result keys | 346 |
| unique exact-joined keys | 67 |
| unique unjoined keys | 279 |

The 22,453 valid-key remainder includes unlabeled sessions and checkpoints
outside the fixed sidecar schedule. The 2,003 malformed-for-this-protocol
rows are retained in the meters as invalid-key rows; they are not dropped
silently. Repeated cells are not independent trials, and no rate is computed
from this join.

## Non-Maps controls

Four non-Maps representative keys already have exact sidecar labels and are
kept as a labeled reference stratum. The other 21 are explicit holdouts with
per-row rationale. They are not treated as negatives and are not scored from
judge output, missing windows, no-fire responses, or final length.

## Concerns and remaining gaps

1. Independent adjudication sheets are blank; agreement and disagreement
   retention remain open.
2. The three positive tails have digest-only source evidence, not committed
   raw captures; the source digest does not validate the first label.
3. The 21 non-Maps controls remain unlabeled by design.
4. Most joined result rows are repeated cells over the same 67 exact keys;
   session-clustered descriptive analysis is still required.
5. Unjoined result rows must not be repaired by nearest-checkpoint
   interpolation, final-length inference, or model output.

## Reproduction

```bash
python3 docs/lab/RESEARCH/2026-10-02-interception-trials/batch-002/run_rotate3_evidence.py
```

Generated files:

- `ROTATE-3-INDEPENDENT-ADJUDICATION-PROTOCOL.md`
- `rotate-3-independent-adjudication-corpus.jsonl`
- `rotate-3-blind-digest-bundle.jsonl`
- `rotate-3-adjudicator-a-template.jsonl`
- `rotate-3-adjudicator-b-template.jsonl`
- `rotate-3-tail-positive-manifest.json`
- `rotate-3-non-maps-controls.json`
- `rotate-3-result-join.jsonl`
- `rotate-3-result-join-meters.json`
- `rotate-3-adjudication-meters.json`

Flash execution remains outside this rotate-3 measurement; no Flash runner or
product path was changed. The OpenCode SQLite source was used only for local,
digest-only tail provenance.
