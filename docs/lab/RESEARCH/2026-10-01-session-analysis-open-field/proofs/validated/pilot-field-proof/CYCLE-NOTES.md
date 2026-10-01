# Pilot field-proof — cycle notes

**Date:** 2026-10-01  
**Cycle id:** `pilot-field-proof-wave-001`  
**Status:** `live_complete` (was `registered_awaiting_live`)  
**Harness:** Ubuntu live run folded at master `a0310a0` ([#88](https://github.com/codyhamilton/workflow-plugin/pull/88))

**2026-10-01 fix:** Pilot live smoke hit TypeSafe HTTP 400 (`api_usage_error`) because early-signal stats framings included illegal Jev `type: "report"` (`compaction_event_count`, `instruction_scope`). Removed those questions (count stays in `state.cumulative`); added `jev_client` / `classify` preflight for `choice` | `score` | `noul` only.

## Registration

- [`cycles/REGISTRATION-pilot-field-proof.md`](../../cycles/REGISTRATION-pilot-field-proof.md)
- Approaches: `stats-jev-tournament`, `frozen-card-search`, `segment-swarm-arbiter` (Pilot tier)
- `max_calls` **96**, `budget_tokens` **400_000**, model `jev-1.13.0`, schema `early-signal-v0`
- **12** framing hashes in [`framing/registry.json`](../../framing/registry.json) (added `pool-thrash-card-anchor`, `pool-residual-baseline`)

## Dry-twin (Jev)

- Script: `run_pilot_dry_twin.py`
- Capture: `capture/pilot-field-proof/jev/dry-twin/` (`requests.jsonl`, `responses.jsonl`, `meters.json`, `batch_summary.json`)
- Log: [`dry_twin_batch_log.json`](dry_twin_batch_log.json) — `gate_pass: true`, `unique_cell_count: 96`
- Cell plan: `capture/pilot-field-proof/jev_cell_plan.json` (8 baseline + 24 search + 64 matrix fill)

## Live Jev (Ubuntu)

- Script: `run_pilot_live_jev.py` (`--confirm-live`; smoke `--limit 1` OK before full wave)
- Capture (Ubuntu only, **not committed**): `capture/pilot-field-proof/jev/live/` (`requests.jsonl`, `responses.jsonl`, `batch_summary.json`, `meters.json`) — placeholder [`.gitkeep`](../../capture/pilot-field-proof/jev/live/.gitkeep) in repo
- Full wave: **96** cells — `live_posts=96`, `errors=0`, `decision=live`
- Meters: `input_tokens_observed=76468` / budget **400000**; response sum in **76468** out **5848**; model **`jev-1.13.0`**

### Kill flags — `stats-jev-tournament` / `frozen-card-search`

| Question | n | yes / no | search | matrix_fill | Verdict |
|----------|--:|----------|--------|-------------|---------|
| `thrash_bundle` | 16 | 7 / 9 | 6 / 6 | 1 / 3 | **PASS** on `tournament-binary-foreshadow` (protos yes, polls no) |
| `poll_monitor` | 8 | 3 / 5 | 3 / 3 | 0 / 2 | **PASS** (`poll_monitor` 3/3 on poll workers; `thrash_bundle` 0/2 on `tournament-binary-foreshadow`) |
| `thrash_bundle` (kill) | — | — | — | — | **KILL** `tournament-monitor-called-out` (thrash on protos **and** poll worker `15f24c7ba18c`) |

- **`frozen-card-search`:** search-arm mechanical reward ≤ baseline (both arms **100%** parse) → **no search win**; allocator kill not fired on reward leak.

## Local swarm (`:8080`)

- Script: `run_local_swarm_pilot.py` (`--live-local` on Ubuntu)
- **18** segment cells planned; **18/18** live-local rows attempted; **16/18** timed out
- Conflict / parse gate on stratified **8**: **8/8** workers affected → **FAIL** (kill **> 4/8** for `segment-swarm-arbiter`)
- Committed [`conflict_report.json`](../../capture/pilot-field-proof/local-swarm/conflict_report.json) may be **stale** vs Ubuntu timeouts (empty conflict lists); do not treat as authoritative until regenerated from Ubuntu `completions.jsonl`.
- Runbook: [`pilot/RUNBOOK-local-swarm.md`](../../pilot/RUNBOOK-local-swarm.md)

## Scale decision

**HOLD** Standard / Max until:

1. Local `:8080` reliability fixed (timeout rate on live-local swarm).
2. Framing pool pruned: **keep** `tournament-binary-foreshadow`; **drop / monitor** leak on `tournament-monitor-called-out`.

## Artifacts

- Dry-twin + stub capture remain under [`capture/pilot-field-proof/`](../../capture/pilot-field-proof/).
- Close-out row: [`cycles/CYCLE-LOG.md`](../../cycles/CYCLE-LOG.md).
