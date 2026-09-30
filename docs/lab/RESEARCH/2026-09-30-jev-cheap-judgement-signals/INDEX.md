# Research pack — Jev as cheap conditional judgements (in-session + workflow soft signals)

**Date:** 2026-09-30  
**Slug:** `jev-cheap-judgement-signals`  
**Triage question:** Where should inexpensive typed Jev judgements sit *after* deterministic phase asserts and *before* expensive human or frontier follow-up — across hooks (PostToolBatch), refine, unit complete, and phase complete?  
**Success metric (proposal):** Document 4 Cody-locked use cases with hook/event mapping, economics, and measurement that does not use session classify as a KPI.  
**White paper:** [`../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`status: resolved` — recommendations accepted pending product wiring). Rewritten after proofs on `112ccfe` (PR #24). Product wiring is implementation, not a further research pass.

## How this maps to the resolved proposal

| Proposal section | Pack note |
|------------------|-----------|
| Signal | [`evidence-maps-claude-5h.md`](evidence-maps-claude-5h.md) |
| Proof evidence | [`proofs/README.md`](proofs/README.md) (closed 4/4; LCD harness noted there) |
| Problem | [`use-cases-cody-locked.md`](use-cases-cody-locked.md), [`assert-phase-baseline.md`](assert-phase-baseline.md) |
| Resolved recommendations | [`use-cases-cody-locked.md`](use-cases-cody-locked.md), [`claude-hook-events.md`](claude-hook-events.md), [`proofs/`](proofs/README.md) |
| Economics | [`economics-jev-prefilter.md`](economics-jev-prefilter.md) |
| Non-goals | [`lineage-prior-work.md`](lineage-prior-work.md) |
| Measurement | [`proofs/false-negative-measurement-plan.md`](proofs/false-negative-measurement-plan.md), [`assert-phase-baseline.md`](assert-phase-baseline.md) |
| Accepted outcomes | White paper section. Thresholds, schemas, hook snippet, and weekly skim are guidance, contracts, and an ops rule. |

## Source notes in this folder

| File | Contents |
|------|----------|
| [`assert-phase-baseline.md`](assert-phase-baseline.md) | Landed `assert_phase` / `phase_assert` kill line; `--deterministic` vs `--live` vs no-key dry-run |
| [`claude-hook-events.md`](claude-hook-events.md) | Hook events for soft escalation (public Claude Code hooks model) |
| [`use-cases-cody-locked.md`](use-cases-cody-locked.md) | Four use cases: PostToolBatch, post-refine, unit complete, phase complete |
| [`economics-jev-prefilter.md`](economics-jev-prefilter.md) | Cheap Jev as pre-filter; ~30% fewer expensive follow-ups |
| [`evidence-maps-claude-5h.md`](evidence-maps-claude-5h.md) | open-pajero-maps Claude 5h analysis (attached uploads) |
| [`lineage-prior-work.md`](lineage-prior-work.md) | Prior spike + driver reorient; this paper is the next layer |

## Proofs (folded into the resolved white paper)

**Status: closed 4/4** — validated runnable pack under [`proofs/`](proofs/README.md) (`./proofs/run_proofs.sh`). LCD harness (`codyh-ubuntu`, OpenCode 1.18.33, checkout `112ccfe`) re-ran that script green; live `PostToolBatch` logging stays on Claude Code. The proposal is rewritten to `status: resolved`.

| Proof | Doc |
|-------|-----|
| PostToolBatch / hooks | [`proofs/post-tool-batch-hooks.md`](proofs/post-tool-batch-hooks.md) |
| Gate thresholds | [`proofs/deterministic-gate-thresholds.md`](proofs/deterministic-gate-thresholds.md) |
| Jev state schemas | [`proofs/jev-compact-state-schemas.md`](proofs/jev-compact-state-schemas.md) |
| Measurement / false negatives | [`proofs/false-negative-measurement-plan.md`](proofs/false-negative-measurement-plan.md) |

## Collect checklist (for future packs)

- [x] In-repo assert behaviour and CLI modes
- [x] Hook event names relevant to soft escalation
- [x] Locked use cases and deterministic pre-gates
- [x] Economics framing
- [x] Quantitative session evidence (maps Claude)
- [x] Lineage vs `PROPOSALS/2026-09-30-jev-hook-assertion-spike.md`
- [x] Proofs runnable (`proofs/run_proofs.sh`)

## Links

- White paper: [`../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md`](../../PROPOSALS/2026-09-30-jev-cheap-judgement-signals.md) (`status: resolved` — recommendations accepted pending product wiring)
- Landed phase assert spike: [`../../PROPOSALS/2026-09-30-jev-hook-assertion-spike.md`](../../PROPOSALS/2026-09-30-jev-hook-assertion-spike.md)
- Driver policy: [`../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../../ANALYSIS/2026-09-30-grokbot-driver-reorient.md)
- Parent index: [`../INDEX.md`](../INDEX.md)
