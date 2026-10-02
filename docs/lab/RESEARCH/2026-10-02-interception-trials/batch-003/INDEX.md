# Batch-003 — adversarial-gap trial designs

**Soft Standard HOLD:** designs and offline plan tooling only. No hooks,
`:8080`, Standard/Pilot/Max unlock, live in-loop Jev, product wiring, or
scoreboard.

This package turns the open gaps from
[#115](https://github.com/codyhamilton/workflow-plugin/pull/115) into frozen
next-wave contracts. It is based on master `06776c47`; #115 was read at
`2fd769c` because it was not yet merged.

| File | Role |
|---|---|
| [`TRIAL-DESIGN.md`](TRIAL-DESIGN.md) | Cell matrices, prerequisites, driver contracts, N, success metrics, and ranked burn order |
| [`TRIAL-MATRIX.json`](TRIAL-MATRIX.json) | Machine-readable states, questions, wordings, drivers, label gates, nulls, metrics, and call counts |
| [`SESSION-STRATA.json`](SESSION-STRATA.json) | Frozen 28-session, four-harness t=45 corpus and response-blind hold-out |
| [`materialize_plan.py`](materialize_plan.py) | Offline core-cell materializer; no judge call |
| [`validate_design.py`](validate_design.py) | Offline consistency, checkpoint, cap, and Soft HOLD checks |

Run the zero-call checks:

```bash
python3 validate_design.py
python3 materialize_plan.py --driver typesafe --block B01 --summary
```

The ranking extension stays blocked until the labeled pool has at least four
runaway-like sessions with cited windows and a non-Maps hold-out. The balanced
state-sensitivity matrix remains diagnostic if that gate is not met.
