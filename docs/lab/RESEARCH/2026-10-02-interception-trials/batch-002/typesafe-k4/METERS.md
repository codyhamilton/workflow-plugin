# METERS — batch-002 typesafe multi-driver wave

**Generated:** 2026-10-02 09:01:03 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `typesafe`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 52, 60, 67, 75, 82, 90, 97, 105, 112, 120]`

## Counts
- n_cells: **1500**
- parse_miss: **0**; errors: **0**; fire_count: **24**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=1088858 out=85350

## Framing mix
- `H1`: 336
- `H2`: 336
- `H3`: 336
- `H4`: 324
- `H5`: 168

## Harness mix
- `claude-code`: 1500

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 1500 | 0.016 |
| 52 | 0 | None |
| 60 | 0 | None |
| 67 | 0 | None |
| 75 | 0 | None |
| 82 | 0 | None |
| 90 | 0 | None |
| 97 | 0 | None |
| 105 | 0 | None |
| 112 | 0 | None |
| 120 | 0 | None |

## Rating hist
- rating 0: 1124
- rating 1: 352
- rating 2: 23
- rating 3: 1

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

