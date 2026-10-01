# Pilot local swarm runbook (`:8080`)

**Registration:** [`cycles/REGISTRATION-pilot-field-proof.md`](../../cycles/REGISTRATION-pilot-field-proof.md)  
**Approach:** `segment-swarm-arbiter` workstream **A** only.

## Prerequisites

- `llama.cpp` / Qwen (or equivalent) listening at `WORKFLOW_LOCAL_LLM_URL` (default `http://127.0.0.1:8080/v1`).
- Shape-qual pack present (committed in repo).
- Pilot registration + dry-twin committed (`registered_awaiting_live` cleared only after live Jev wave closes).

## Plan (no network)

```bash
cd docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs
python3 run_local_swarm_pilot.py
```

Writes ~**24** segment cells under `capture/pilot-field-proof/local-swarm/` with `mode: dry-stub`.

## Live local labels

```bash
export WORKFLOW_LOCAL_LLM_URL="${WORKFLOW_LOCAL_LLM_URL:-http://127.0.0.1:8080/v1}"
python3 run_local_swarm_pilot.py --live-local
```

Each completion row uses `cache: bypass` semantics (documented on the cell; not shared with TypeSafe cache).

## Conflict → Flash arbiter

After live local run:

1. Group completions by `worker_id`.
2. **Stable** if all `theme_guess` agree and JSON parses.
3. **Conflict** if tags differ or parse fails.
4. If **> 4 / 8** workers conflict → kill `segment-swarm-arbiter` (pilot aggregate).
5. Otherwise Flash arbiter on conflict workers only, cap **≤ 4** Flash calls in Pilot.

Flash step is **not** automated in this stub; mount probe must pass on Ubuntu for prose (`summary-then-judge` schema).

## Artifacts

| File | Purpose |
|------|---------|
| `local-swarm/segment_cells.jsonl` | Grid of checkpoint segments |
| `local-swarm/completions.jsonl` | Local model JSON (or dry-stub) |
| `local-swarm/conflict_report.json` | Conflict worker ids (filled post-live) |
| `local-swarm/meters.json` | `local_completions` count |
