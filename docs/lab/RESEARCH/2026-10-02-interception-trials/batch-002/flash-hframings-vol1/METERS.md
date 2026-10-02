# METERS — batch-002 flash multi-driver wave

**Generated:** 2026-10-02 01:55:37 AEST

**Soft Standard HOLD** — no hooks / product unlock. Judges = policy-under-test only.
**Driver:** `flash`  **Wave:** Wave-0-multi  **Batch:** batch-002

## Protocol
- R1: no T / progress-frac / full-session length in prompt or state
- R2: no length-derived outcome tags; window_status=unidentified (join later)
- R3: fixed schedule `[45, 60, 75, 90, 105, 120]`

## Counts
- n_cells: **800**
- parse_miss: **0**; errors: **0**; fire_count: **180**
- leak_spotcheck_hits: **0**
- usage tokens (rough): in=0 out=0

## Framing mix
- `H1`: 154
- `H2`: 168
- `H3`: 164
- `H4`: 176
- `H5`: 138

## Harness mix
- `claude-code`: 800

## Fire rate by checkpoint (among cells at t)
| t | n | fire_rate |
|---|---|-----------|
| 45 | 800 | 0.225 |
| 60 | 0 | None |
| 75 | 0 | None |
| 90 | 0 | None |
| 105 | 0 | None |
| 120 | 0 | None |

## Rating hist
- rating 0: 316
- rating 1: 304
- rating 2: 40
- rating 3: 140

## Join
Join keys: `session_id` + `checkpoint` match batch-002 Flash Wave-0 / OUTCOME-SHEET. Do **not** invent outcome labels.

