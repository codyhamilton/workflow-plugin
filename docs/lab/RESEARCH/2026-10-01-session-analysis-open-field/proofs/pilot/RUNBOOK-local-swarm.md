# Pilot segment swarm runbook (Flash / Luna / local)

**Registration:** [`cycles/REGISTRATION-pilot-field-proof.md`](../../cycles/REGISTRATION-pilot-field-proof.md)  
**Approach:** `segment-swarm-arbiter` workstream **A** only.

**Next wave (post-HOLD):** **Luna** (Codex `gpt-6-luna`) is the **default** Pilot swarm provider (smoke-green on Ubuntu). **Flash** (OpenCode DeepSeek) is optional/secondary when the OpenCode seat recovers (known 60s+ hangs — tune `WORKFLOW_FLASH_TIMEOUT_SEC`, default 120). Local Qwen on `:8080` is legacy. **Standard / Max** tiers stay on HOLD until the swarm conflict gate passes on a **non-local** provider.

Flash segment labels are drafts only: **Sonnet 5.5 review** plus **Claude Code or Grok** phase sign-off per [`GUIDANCE-flash-review-gate.md`](../../../../GUIDANCE-flash-review-gate.md).

## Prerequisites

- Pilot registration + dry-twin committed (`gate_pass: true`).
- **Flash:** OpenCode on PATH (`WORKFLOW_OPENCODE_BIN`, default `opencode`), model `WORKFLOW_FLASH_MODEL` default `deepseek/deepseek-flash`.
- **Luna:** Codex CLI on PATH (`WORKFLOW_CODEX_BIN`, default `codex`), model pin `WORKFLOW_LUNA_MODEL` default `gpt-6-luna`.
- **Local (legacy):** `llama.cpp` / Qwen at `WORKFLOW_LOCAL_LLM_URL` (default `http://127.0.0.1:8080/v1`).
- Shape-qual pack present (committed in repo).
- No `TYPESAFE_API_KEY` required for swarm; no live TypeSafe from cloud VM.

## Plan (no network)

```bash
cd docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs
python3 run_local_swarm_pilot.py
```

Writes segment cells under `capture/pilot-field-proof/local-swarm/` with `mode: dry-stub`.

## Live labels (Ubuntu harness)

**Codex Luna (default — smoke command):**

```bash
cd docs/lab/RESEARCH/2026-10-01-session-analysis-open-field/proofs
export WORKFLOW_CODEX_BIN="${WORKFLOW_CODEX_BIN:-codex}"
export WORKFLOW_LUNA_MODEL="${WORKFLOW_LUNA_MODEL:-gpt-6-luna}"
python3 run_local_swarm_pilot.py --live
```

Explicit provider (same as default):

```bash
python3 run_local_swarm_pilot.py --provider luna --live
```

**DeepSeek Flash (optional, when OpenCode seat recovers):**

```bash
export WORKFLOW_OPENCODE_BIN="${WORKFLOW_OPENCODE_BIN:-opencode}"
export WORKFLOW_FLASH_MODEL="${WORKFLOW_FLASH_MODEL:-deepseek/deepseek-flash}"
export WORKFLOW_FLASH_TIMEOUT_SEC="${WORKFLOW_FLASH_TIMEOUT_SEC:-120}"
python3 run_local_swarm_pilot.py --provider flash --live
```

**Local Qwen / llama.cpp (legacy):**

```bash
export WORKFLOW_LOCAL_LLM_URL="${WORKFLOW_LOCAL_LLM_URL:-http://127.0.0.1:8080/v1}"
python3 run_local_swarm_pilot.py --provider local --live
# or deprecated: python3 run_local_swarm_pilot.py --live-local
```

CLI default provider is **luna**. Override with `--provider` or `WORKFLOW_SWARM_PROVIDER=luna|flash|local`.

Each completion row uses `cache: bypass` semantics (documented on the cell; not shared with TypeSafe cache).

## Conflict → Flash arbiter

After live swarm run:

1. Group completions by `worker_id`.
2. **Stable** if all `theme_guess` agree and JSON parses.
3. **Conflict** if tags differ or parse fails.
4. If **> 4 / 8** workers conflict → kill `segment-swarm-arbiter` (pilot aggregate).
5. Otherwise Flash arbiter on conflict workers only, cap **≤ 4** Flash calls in Pilot.

Flash arbiter step is **not** automated in this stub; mount probe must pass on Ubuntu for prose (`summary-then-judge` schema).

## Artifacts

| File | Purpose |
|------|---------|
| `local-swarm/segment_cells.jsonl` | Grid of checkpoint segments |
| `local-swarm/completions.jsonl` | Provider JSON (or dry-stub) |
| `local-swarm/conflict_report.json` | Conflict worker ids (filled post-live) |
| `local-swarm/meters.json` | Completion count + `swarm_provider` |
