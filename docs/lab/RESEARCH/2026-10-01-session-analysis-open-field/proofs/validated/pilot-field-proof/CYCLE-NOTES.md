# Pilot field-proof — cycle notes

**Date:** 2026-10-01  
**Cycle id:** `pilot-field-proof-wave-001`  
**Status:** `registered_awaiting_live`  
**Live TypeSafe POSTs:** **0** (cloud VM: `TYPESAFE_API_KEY` unset)

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

## Local swarm stub

- Script: `run_local_swarm_pilot.py` (no `--live-local` on cloud)
- **18** segment cells (pack checkpoints ≤ 120 on stratified 8; budget doc mid ~24)
- Capture: `capture/pilot-field-proof/local-swarm/`
- Runbook: [`pilot/RUNBOOK-local-swarm.md`](../../pilot/RUNBOOK-local-swarm.md)

## NEXT (CHM / Ubuntu)

1. Confirm TypeSafe pricing on console (direct vs gateway ×10).
2. `python3 run_pilot_dry_twin.py` — must stay green.
3. `python3 run_local_swarm_pilot.py --live-local` with `:8080` up.
4. Live Jev wave with `live` + `confirm_live` + key → write `capture/pilot-field-proof/jev/live/*.jsonl`.
5. Score thrash vs poll flags; evaluate kills in registration; update [`CYCLE-LOG.md`](../../cycles/CYCLE-LOG.md).
