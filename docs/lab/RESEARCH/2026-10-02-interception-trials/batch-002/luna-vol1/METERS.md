# METERS — batch-002 luna multi-driver wave

**Generated:** 2026-10-02 01:46:19 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `luna`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`

## Counts
- n_cells: **200**
- parse_miss: **0**; errors: **0**; fire_count: **16**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=0 out=0

## Framing mix
- `H1`: 77
- `H2`: 84
- `H3`: 39

## Harness mix
- `claude-code`: 200

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 200 | 0.08 |
| 60 | 0 | None |
| 75 | 0 | None |
| 90 | 0 | None |
| 105 | 0 | None |
| 120 | 0 | None |

## Rating hist
- rating 0: 78
- rating 1: 106
- rating 2: 6
- rating 3: 10

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

