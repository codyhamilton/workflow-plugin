# Rotate #2 decision-window audit report

**Soft Standard HOLD.** Offline derived evidence only. No behavior, hooks,
Standard unlock, or local `:8080` path.

## Result

The exact-key audit passes its protocol-shape gates:

| Measure | Count |
|---|---:|
| labeled sidecar sessions | 20 |
| exact labeled `(session_id, checkpoint)` keys | 67 |
| finite-window sessions | 3 |
| `decision_window_positive` keys | 4 |
| `negative_control` keys (`near_done=no`, `runaway_like=no`) | 39 |
| `near_done_guard` keys (`near_done=yes`, `runaway_like=no`) | 24 |
| `inside_steer_window` keys | 4 |
| `outside_steer_window` keys | 11 |
| `no_steer_window` keys | 52 |
| ambiguous keys | 0 |

The 4 positive keys are the existing sidecar's four
`runaway_like=yes` checkpoints, all inside a finite labeled window. The audit
does not manufacture additional tail-bearing labels. It also does not treat
the 39 double-negative keys as automatically valid controls merely because
their window status is `no_steer_window`.

## Protocol checks

- exact session/checkpoint join: **pass**
- fixed-schedule checkpoint validation: **pass**
- duplicate exact-key detection: **pass**
- nearest-checkpoint interpolation: **false**
- final session length as input: **false**
- independence attestations: **all false**
- judge ratings/fire used as reference: **false**
- HTTP calls: **0** (offline derived audit)
- HTTP error rate, collision rate, prior-ID overlap, leak hits: **not
  applicable to this offline artifact**

The TypeSafe/Luna cell runners remain responsible for reporting those transport
and leakage meters on any subsequent cell batch. The audit's outputs are
`rotate-2-decision-window-controls.jsonl` and
`rotate-2-decision-window-audit.json`.

## What this closes

This establishes a reproducible, pre-specified negative-control and
decision-window *protocol* with measurable exact-key strata. It makes the
control denominator and the 4-key positive reference stratum explicit before
any future TypeSafe/Luna result join.

## What remains open

Empirical reference validation is **not complete**. The next required evidence
is:

1. an independent second adjudication with retained agreement;
2. immutable blind transcript-digest inputs for replay;
3. a separate exact-key join to TypeSafe/Luna results before any descriptive
   hit/miss candidate counts;
4. session-clustered aggregation that preserves repeated-cell provenance.

The three previously gated tail/state-invalid positive keys remain open for
axis 1. The 21 non-Maps keys without sidecar rows remain an unlabeled holdout
for axis 2. No favorable count in this report unlocks behavior or Soft
Standard.
