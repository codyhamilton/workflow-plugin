# TypeSafe lever-wave outcome join — batch-002

**Soft Standard HOLD.** Derived evidence only: no hooks, product wiring, Standard unlock, or FP/miss board.

This report joins committed TypeSafe `Wave-0-multi` lever rows to the independent outcome sidecar on exact `session_id` + `checkpoint`. It does not read or aggregate judge ratings/fire decisions and does not rewrite source `results.jsonl` files.

## Coverage meters

- Result rows: **5420**
- Exact joined rows: **5420** (100.0%)
- Unjoined committed rows: **0**
- Result sessions: **20**; labeled: **20**
- Unique `(session_id, checkpoint)` keys: **67**; exact: **67**

| Stream | result rows | exact join | unjoined | sessions | unique keys |
|---|---:|---:|---:|---:|---:|
| `typesafe` | 180 | 180 | 0 | 20 | 67 |
| `typesafe-h25` | 240 | 240 | 0 | 10 | 10 |
| `typesafe-k1` | 2500 | 2500 | 0 | 3 | 3 |
| `typesafe-k2` | 2500 | 2500 | 0 | 3 | 3 |

## Unlabeled remainder

None among committed TypeSafe lever-wave result rows: every row has an exact labeled checkpoint in `outcome-labels.jsonl`.

Meter-only waves are a separate remainder: they are not counted as unlabeled rows because no committed row-level join keys exist.

| Stream | meter-reported cells | reason |
|---|---:|---|
| `typesafe-k4` | 1500 | results.jsonl is not committed, so session_id + checkpoint join coverage cannot be measured |

## Scope boundaries

- `joined.jsonl` contains only `label_join_exact` rows and preserves source path + row identity.
- Repeated lever cells are coverage rows, not independent trials; the 20 sessions and 67 unique join keys are the non-replicated coverage denominators.
- Window status, near-done, and runaway-like values are copied or derived only from the validated sidecar. Missing labels are never interpolated.
- Scenario-sweep and review-check streams are outside this lever-wave join. Scenario coverage remains documented in [`WINDOW-STATUS-JOIN.md`](../../../2026-10-02-interception-steer-to-stop/WINDOW-STATUS-JOIN.md).

## Reproduce

```bash
python3 tools/interception/typesafe_lever_join.py --require-complete
python3 -m unittest discover -s tools/interception/tests -p 'test_*.py'
```

Generated artifacts: `joined.jsonl` (exact joins only) and `coverage.json` (coverage and remainder meters).
