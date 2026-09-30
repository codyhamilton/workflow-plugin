# Signal — durable analytics / observability sink

**Date:** 2026-09-30  
**Slug:** `durable-analytics-sink`  
**Status:** research closed; white paper [`../../PROPOSALS/2026-09-30-durable-analytics-sink.md`](../../PROPOSALS/2026-09-30-durable-analytics-sink.md) is `status: resolved`; no default hook/driver wiring

## Problem

Workflow-plugin already emits **measurable, structured events** inside the workspace (driver run record, assert log, Jev soft-signal JSONL, git trailers). That is enough for **local** agents with a persistent disk. **Cursor Cloud Agents** boot from a snapshot and lose the VM when the run ends — workspace JSONL is not a durable observability plane across runs or hosts.

The remit needs **comparable outcomes** across Claude Code, Cursor (desktop), Cursor Cloud, and OpenCode without:

- Turning soft signals into KPIs or gates (classify stays visualization; `assert_phase --deterministic` stays the kill line).
- Shipping remote sink wiring into default hooks or the driver without explicit lab/opt-in markers.

## Question

What **sink** and **envelope** should lab guidance recommend so bots and hooks can **dual-write** (local JSONL + optional remote append) with **exit 0 on sink failure**?

## Success criteria (this pack)

| Thread | Closed in |
|--------|-----------|
| Inventory of existing emitters | [`INVENTORY.md`](INVENTORY.md) |
| Sink candidate comparison | [`SINK-CANDIDATES.md`](SINK-CANDIDATES.md) |
| Minimal event envelope | [`EVENT-SCHEMA.md`](EVENT-SCHEMA.md) |
| Cloud egress (HTTPS POST) | [`FINDINGS.md`](FINDINGS.md), [`proofs/validated/egress_cloud_result.json`](proofs/validated/egress_cloud_result.json) |
| Dual-write recipe | [`DUAL-WRITE-RECIPE.md`](DUAL-WRITE-RECIPE.md), [`proofs/dual_write_sink.py`](proofs/dual_write_sink.py) |
| Recommendation | [`FINDINGS.md`](FINDINGS.md) |

## Non-goals

- Product wiring into `install.sh`, default Claude hooks, or `run.py` / `assert_phase.py` (implementation of the resolved proposal, not more research).
- A second copy of the white paper in this folder — see [`GROK-WHITEPAPER-STUB.md`](GROK-WHITEPAPER-STUB.md).

## Constraints (from Cody + Workflow System Manager)

- Soft signals remain **advisory**; deterministic assert remains **authoritative**.
- No classify-as-KPI.
- Lab docs only; opt-in env vars for remote sink.
