# Pilot field-proof — cycle notes

**Date:** 2026-10-01  
**Cycle id:** `pilot-field-proof-wave-001`  
**Status:** `live_complete` (wave-001); **next wave** `registered_awaiting_live` on pruned pool + Luna swarm  
**Harness:** Ubuntu live run folded at master `a0310a0` ([#88](https://github.com/codyhamilton/workflow-plugin/pull/88)); CYCLE-NOTES fold [#89](https://github.com/codyhamilton/workflow-plugin/pull/89)

**2026-10-01 fix:** Pilot live smoke hit TypeSafe HTTP 400 (`api_usage_error`) because early-signal stats framings included illegal Jev `type: "report"` (`compaction_event_count`, `instruction_scope`). Removed those questions (count stays in `state.cumulative`); added `jev_client` / `classify` preflight for `choice` | `score` | `noul` only.

## Registration (next wave)

- [`cycles/REGISTRATION-pilot-field-proof.md`](../../cycles/REGISTRATION-pilot-field-proof.md)
- Approaches: `stats-jev-tournament`, `frozen-card-search`, `segment-swarm-arbiter` (Pilot tier)
- `max_calls` **88**, `budget_tokens` **400_000**, model `jev-1.13.0`, schema `early-signal-v0`
- **11** framing hashes in [`framing/registry.json`](../../framing/registry.json) (pruned `tournament-monitor-called-out`; kept `tournament-binary-foreshadow`)

**Next wave:** pruned framing pool + **Luna** (`gpt-6-luna`) default swarm; Flash secondary when OpenCode recovers; local `:8080` legacy. **Standard / Max** on HOLD until swarm conflict gate passes on **non-local** Luna/Flash. Flash drafts still need Sonnet review + Claude/Grok phase sign-off.

## Dry-twin (Jev)

- Script: `run_pilot_dry_twin.py`
- Capture: `capture/pilot-field-proof/jev/dry-twin/` (`requests.jsonl`, `responses.jsonl`, `meters.json`, `batch_summary.json`)
- Log: [`dry_twin_batch_log.json`](dry_twin_batch_log.json) — `gate_pass: true`, `unique_cell_count: 88`
- Cell plan: `capture/pilot-field-proof/jev_cell_plan.json` (8 baseline + 18 search + 62 matrix fill)

## Live Jev (Ubuntu, wave-001 — historical)

- Script: `run_pilot_live_jev.py` (`--confirm-live`; smoke `--limit 1` OK before full wave)
- Capture (Ubuntu only, **not committed**): `capture/pilot-field-proof/jev/live/` — placeholder [`.gitkeep`](../../capture/pilot-field-proof/jev/live/.gitkeep) in repo
- Full wave (pre-prune registration): **96** cells — `live_posts=96`, `errors=0`, `decision=live`
- Meters: `input_tokens_observed=76468` / budget **400000**; model **`jev-1.13.0`**

### Kill flags — `stats-jev-tournament` / `frozen-card-search` (wave-001)

| Question | n | yes / no | search | matrix_fill | Verdict |
|----------|--:|----------|--------|-------------|---------|
| `thrash_bundle` | 16 | 7 / 9 | 6 / 6 | 1 / 3 | **PASS** on `tournament-binary-foreshadow` (protos yes, polls no) |
| `poll_monitor` | 8 | 3 / 5 | 3 / 3 | 0 / 2 | **PASS** (`poll_monitor` 3/3 on poll workers; `thrash_bundle` 0/2 on `tournament-binary-foreshadow`) |
| `thrash_bundle` (kill) | — | — | — | — | **KILL** `tournament-monitor-called-out` (thrash on protos **and** poll worker `15f24c7ba18c`) |

- **`frozen-card-search`:** search-arm mechanical reward ≤ baseline (both arms **100%** parse) → **no search win**; allocator kill not fired on reward leak.

## Segment swarm

- Script: `run_local_swarm_pilot.py` — default **`--provider luna`**; `python3 run_local_swarm_pilot.py --live` on Ubuntu
- **18** segment cells planned
- **Wave-001 local `:8080`:** `--live-local` 18/18 rows, 16/18 timeouts → 8/8 stratified conflict/parse → **FAIL** (kill **> 4/8**). Committed [`conflict_report.json`](../../capture/pilot-field-proof/local-swarm/conflict_report.json) may be **stale** vs Ubuntu timeouts.
- **Next:** Luna smoke-green on Ubuntu; re-run conflict gate before scale-up.
- Runbook: [`pilot/RUNBOOK-local-swarm.md`](../../pilot/RUNBOOK-local-swarm.md)

## Scale decision

**HOLD** Standard / Max until:

1. Luna (or Flash) live swarm passes conflict gate (**≤ 4 / 8** workers conflict/parse).
2. Pruned pool dry-twin green (**88** cells) — `tournament-monitor-called-out` dropped from registry.

## NEXT (CHM / Ubuntu)

1. `python3 run_pilot_dry_twin.py` — must stay green (88 cells).
2. **Smoke:** `python3 run_local_swarm_pilot.py --live` (Luna default).
3. Optional Flash when OpenCode seat recovers: `--provider flash --live` (`WORKFLOW_FLASH_TIMEOUT_SEC`).
4. Next live Jev on pruned plan: `run_pilot_live_jev.py --confirm-live` → `jev/live/` (harness only).
5. Update [`cycles/CYCLE-LOG.md`](../../cycles/CYCLE-LOG.md) when next wave closes.

## Artifacts

- Dry-twin + swarm capture under [`capture/pilot-field-proof/`](../../capture/pilot-field-proof/).
- Close-out row: [`cycles/CYCLE-LOG.md`](../../cycles/CYCLE-LOG.md).
