# METERS — batch-002 flash multi-driver wave

**Generated:** 2026-10-02 09:05:05 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `flash`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`

## Counts
- n_cells: **400**
- parse_miss: **10**; errors: **0**; fire_count: **179**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=0 out=0

## Framing mix
- `H1`: 85
- `H2`: 72
- `H3`: 80
- `H4`: 83
- `H5`: 80

## Harness mix
- `claude-code`: 400

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 390 | 0.459 |
| 60 | 0 | None |
| 75 | 0 | None |
| 90 | 0 | None |
| 105 | 0 | None |
| 120 | 0 | None |

## Rating hist
- rating 0: 86
- rating 1: 125
- rating 2: 35
- rating 3: 144

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

