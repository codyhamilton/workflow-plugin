# METERS — batch-002 typesafe multi-driver wave

**Generated:** 2026-10-02 01:39:55 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `typesafe`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`

## Counts
- n_cells: **240**
- parse_miss: **0**; errors: **0**; fire_count: **7**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=176997 out=11760

## Framing mix
- `H1`: 80
- `H2`: 40
- `H3`: 40
- `H4`: 40
- `H5`: 40

## Harness mix
- `claude-code`: 240

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 240 | 0.0292 |
| 60 | 0 | None |
| 75 | 0 | None |
| 90 | 0 | None |
| 105 | 0 | None |
| 120 | 0 | None |

## Rating hist
- rating 0: 203
- rating 1: 30
- rating 2: 3
- rating 3: 4

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

