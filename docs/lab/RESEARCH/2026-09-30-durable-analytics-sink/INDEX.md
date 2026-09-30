# Research pack — durable analytics / observability sink

**Date:** 2026-09-30  
**Slug:** `durable-analytics-sink`  
**Triage question:** How should workflow-plugin emit **durable** observability for local and cloud agents without blocking workflows or promoting classify to KPI?  
**White paper:** [`../../PROPOSALS/2026-09-30-durable-analytics-sink.md`](../../PROPOSALS/2026-09-30-durable-analytics-sink.md) (`status: resolved` — recommendations accepted pending product wiring). Written from this pack’s proofs on `1bff769` (PR #27). Product wiring is implementation, not a further research pass. Stub: [`GROK-WHITEPAPER-STUB.md`](GROK-WHITEPAPER-STUB.md).

## How this maps to the resolved proposal

| Proposal section | Pack note |
|------------------|-----------|
| Signal | [`SIGNAL.md`](SIGNAL.md), [`INVENTORY.md`](INVENTORY.md) |
| Proof evidence | [`proofs/README.md`](proofs/README.md), [`proofs/validated/`](proofs/validated/) |
| Problem | [`SIGNAL.md`](SIGNAL.md), [`SINK-CANDIDATES.md`](SINK-CANDIDATES.md) |
| Resolved recommendations | [`FINDINGS.md`](FINDINGS.md), [`EVENT-SCHEMA.md`](EVENT-SCHEMA.md), [`DUAL-WRITE-RECIPE.md`](DUAL-WRITE-RECIPE.md) |
| Guidance, skills, invariants | White paper section. Helper and schema are guidance; skills stay unchanged; exit-code and kill-line rules are invariants. |
| Economics | [`SINK-CANDIDATES.md`](SINK-CANDIDATES.md) |
| Non-goals | [`SIGNAL.md`](SIGNAL.md) |
| Measurement | White paper section. Local JSONL skim plus collector health. Classify stays out. |
| Product wiring | White paper section. Shared opt-in helper; collector is ops. |

## Closed threads

| # | Thread | Answer |
|---|--------|--------|
| 1 | Inventory | [`INVENTORY.md`](INVENTORY.md) |
| 2 | Sink candidates | [`SINK-CANDIDATES.md`](SINK-CANDIDATES.md) — **HTTP append + local JSONL** |
| 3 | Event schema | [`EVENT-SCHEMA.md`](EVENT-SCHEMA.md) |
| 4 | Cloud egress | [`FINDINGS.md`](FINDINGS.md) + [`proofs/validated/egress_cloud_result.json`](proofs/validated/egress_cloud_result.json) |
| 5 | Dual-write recipe | [`DUAL-WRITE-RECIPE.md`](DUAL-WRITE-RECIPE.md) + [`proofs/dual_write_sink.py`](proofs/dual_write_sink.py) |
| 6 | Repo indexes | `docs/lab/BACKLOG.md`, `docs/lab/FINDINGS.md`, [`../INDEX.md`](../INDEX.md) |

## Proofs

**Status: closed** — `./proofs/run_proofs.sh` (unittest, mock HTTP sink, HTTPS egress probe).

## Pack files

| File | Role |
|------|------|
| [`SIGNAL.md`](SIGNAL.md) | Problem, constraints, success criteria |
| [`FINDINGS.md`](FINDINGS.md) | Dated closed answers (this pack) |
| [`INVENTORY.md`](INVENTORY.md) | Emitters today |
| [`SINK-CANDIDATES.md`](SINK-CANDIDATES.md) | Comparison table |
| [`EVENT-SCHEMA.md`](EVENT-SCHEMA.md) | Envelope v1 |
| [`DUAL-WRITE-RECIPE.md`](DUAL-WRITE-RECIPE.md) | Opt-in env vars and behaviour |
| [`GROK-WHITEPAPER-STUB.md`](GROK-WHITEPAPER-STUB.md) | Pointer to the resolved proposal |

## Links

- Jev soft signals (related JSONL): [`../2026-09-30-jev-cheap-judgement-signals/INDEX.md`](../2026-09-30-jev-cheap-judgement-signals/INDEX.md)
- Driver policy: [`../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md)
- Parent index: [`../INDEX.md`](../INDEX.md)
