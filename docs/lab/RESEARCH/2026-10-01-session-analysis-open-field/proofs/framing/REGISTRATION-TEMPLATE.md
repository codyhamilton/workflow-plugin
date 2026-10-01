# Framing wave registration template

Copy this block into a committed registration **before** any live TypeSafe POST. Timestamps on artifacts must be **after** this file in git history for the wave to be valid.

## Identity

| Field | Value (fill before run) |
|-------|-------------------------|
| `registration_id` | e.g. `frozen-card-search-wave-001` |
| `approach_id` | `stats-jev-tournament` **or** `frozen-card-search` |
| `schema_id` | `early-signal-v0` |
| `model` | `jev-1.13.0` only |
| `card_hash_manifest` | Path to `manifests/card_hash_manifest.json` + per-worker hashes for scored set |
| `worker_ids` | Stratified eight (hold-out 26 untouched) |

## Framing pool

List every `slug` and `framing_id` from `framing/registry.json`. **≥8** blobs must be registered so the baseline arm can draw randomly.

| slug | framing_id | in tournament wave? | in baseline pool? |
|------|------------|---------------------|-------------------|
| *(copy rows from registry.json)* | | | |

### `unregistered_framing` behaviour

Question JSON whose canonical hash is **not** listed in this registration (or whose slug is absent from `framing/registry.json`) must not POST. Dry-run and live handlers return `decision: missing`, `reason: unregistered_framing`. Offspring prompts from evolutionary search must be registered (new slug + hash) **before** send.

## Budget split (`frozen-card-search`)

| Arm | POST budget | Rule |
|-----|------------:|------|
| **Baseline** | **8** | Random draw of registered slugs (with replacement allowed only if documented) |
| **Search** | **24** | Pre-registered matrix, e.g. 6 workers × 4 tournament framings |
| **Total** | **32** | `max_calls` default; live requires `live`, `confirm_live`, `TYPESAFE_API_KEY` |

A wave that spends all 32 on the search arm without 8 baseline cells is **void**.

## Guards (inherited)

- Default dry-run. No socket in protocol slice.
- `duplicate_post_rate` must be 0; replay POST count 0 when cache warm.
- Logs and committed JSON must not contain `TYPESAFE_API_KEY` (dummy keys used in tests must not appear in artifacts).
- `hide_outcome_suffix` true for `early-signal-v0`.
- Stats-card state only until summary cards pass fidelity.

## Kill criteria (copy from approach doc — do not paraphrase)

Paste from [`CANDIDATE-APPROACHES.md`](../CANDIDATE-APPROACHES.md) for the chosen `approach_id`.
