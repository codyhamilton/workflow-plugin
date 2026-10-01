# Field capture layout (Pilot / Standard / Max)

Live waves must persist **raw request/response JSONL**, **framing hashes**, **worker ids**, **dry-run twins**, **timestamps**, **model pin**, and **cost meters** ([`RESOURCE-BUDGET-AGGRESSIVE.md`](../../RESOURCE-BUDGET-AGGRESSIVE.md) §Field capture).

## Tree (Pilot registration `pilot-field-proof`)

```
proofs/capture/pilot-field-proof/
  framing_hashes.json          # copy of committed registry at registration time
  jev_cell_plan.json           # 96-cell arm ordering
  local_swarm_plan.json        # segment grid for workstream A
  jev/
    dry-twin/
      requests.jsonl           # one row per cell; includes request_body
      responses.jsonl          # twin: response_body null, tokens null
      batch_summary.json
      meters.json
    live/                      # CHM fills after confirm_live run (same filenames)
      requests.jsonl
      responses.jsonl
      batch_summary.json
      meters.json
  local-swarm/
    segment_cells.jsonl        # planned cells (checkpoints ≤ 120)
    completions.jsonl          # local model outputs or dry-stub rows
    conflict_report.json
    meters.json
```

## JSONL row shape

**`jev/*/requests.jsonl`** (dry-twin and live identical keys):

| Field | Type | Notes |
|-------|------|-------|
| `ts` | ISO-8601 UTC | |
| `registration_id` | string | e.g. `pilot-field-proof-wave-001` |
| `mode` | `dry-twin` \| `live` | |
| `cell_index` | int | 0..95 for Pilot |
| `arm` | `baseline` \| `search` \| `matrix_fill` | |
| `worker_id` | string | |
| `framing_slug` | string | |
| `framing_id` | string | slug#hash |
| `segment_id` | string | |
| `schema_id` | string | |
| `model` | string | `jev-1.13.0` |
| `decision` | string | `dry_run` or live outcome |
| `cache_key` | string | body hash |
| `would_post` | bool | |
| `request_body` | object | `{model, state, questions}` — no API key |

**`jev/*/responses.jsonl`:**

| Field | Notes |
|-------|-------|
| `response_body` | Provider JSON on live; null on dry-twin |
| `input_tokens` | From provider meter when live |
| `error` | Set on failure |

**`meters.json`:** aggregate `jev_posts`, `jev_would_post`, `input_tokens_observed`, `input_tokens_budget`, `flash_calls`, `local_completions`.

Logs must **never** contain `TYPESAFE_API_KEY`.

## Generators (this pack)

| Script | Output |
|--------|--------|
| `run_pilot_dry_twin.py` | `jev/dry-twin/*`, `framing_hashes.json`, `jev_cell_plan.json` |
| `run_local_swarm_pilot.py` | `local-swarm/*`, `local_swarm_plan.json` |

Live Jev capture on Ubuntu uses the same paths under `jev/live/` after registration is committed and dry-twin `gate_pass` is logged.
