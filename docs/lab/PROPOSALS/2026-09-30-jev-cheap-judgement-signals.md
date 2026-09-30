---
title: Cheap conditional Jev judgements
status: draft
date: 2026-09-30
signal: Maps Claude 5h — 16% of subagents over the ideal band; densest window ~63M tokens, concentrated in a few fat workers.
owners: Workflow Optimiser, Cody
---

# Cheap conditional Jev judgements

Soft signals that sit after a deterministic check and before an expensive follow-up. Cody accepts or defers this draft. Until then it changes no hooks and no `assert_phase` behaviour.

Research pack: [`../RESEARCH/2026-09-30-jev-cheap-judgement-signals/`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md).

## Signal

The 2026-09-30 open-pajero-maps Claude analysis ([`evidence-maps-claude-5h.md`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md)) scored **150** subagents against the workflow ideal band of **50–75** API turns and **100–125k** final context (band source: `docs/analysis/2026-09-08-workflow-vs-field.md`).

| Metric | Value |
|--------|--------|
| Subagents analyzed | **150** |
| Over ideal | **24 (16%)** |
| Context > 125k | 17 |
| Turns > 100 | 8 |
| Worst peak/final contexts | ~160k, 156k, 154k, 145k, 143k |

Mis-sized subagents are a minority. They dominate burn. Heaviest rolling 5-hour windows (tokens ≈ input + cache_creation + cache_read + output):

| Rank | Tokens | Calls | Window (AEST) |
|------|--------|-------|----------------|
| 1 | **63.35M** | 764 | 2026-09-25 10:54 → 15:54 |
| 2 | **62.87M** | 652 | 2026-09-14 18:29 → 23:29 |
| 3 | **56.95M** | 667 | 2026-09-25 09:29 → 14:29 |
| 4 | **52.66M** | 532 | 2026-09-22 20:06 → 2026-09-23 01:06 |
| 5 | **50.27M** | 586 | 2026-09-25 06:53 → 11:53 |

The densest window (~**63M** tokens, 764 calls) comes from a few large contributors. Parallel overlapping fat workers outweigh per-agent thrashing as the 5-hour driver.

Active session `d006f5a0…`: wall ~**43.8h**; parent modest; **8** subagents, **778** API calls, **66.25M** of **71.53M** tokens inside subagents; **4/8** over ideal. Worker `92a48e004519`: **296** API calls, **12.7MB** JSONL, peak context **130k**, flags `OVER_TURNS` and `FAT_JSONL`, six paths re-read ≥3 times. A PostToolBatch turn gate would have had a row long before that post-hoc read.

Same pack, for scale: `af9b5cb1…` has 19 subagents and **107.77M** tokens with only **2/19** over ideal, and still shows up in top 5-hour windows when workers overlap. `bd4f6c0d…` has **54** subagents, **194.80M** tokens, **7/54** over ideal, and one worker at **154** API calls (`bb6165018de0`) across a ~54h wall clock.

Caveats from the analysis, kept so the percentages stay honest: totals are deduped transcript `message.usage` and can differ from the Anthropic meter; turn counts are deduped assistant API calls; OVER_CTX in the 125–147k band is often the compaction ceiling, so **peak** context is the sizing signal.

Phase closure already has a mechanical kill line ([`2026-09-30-jev-hook-assertion-spike.md`](2026-09-30-jev-hook-assertion-spike.md), `status: landed`; policy in [`../ANALYSIS/2026-09-30-grokbot-driver-reorient.md`](../ANALYSIS/2026-09-30-grokbot-driver-reorient.md)). This paper is the next layer: in-session and refine / unit / phase **soft** judgements. Monitoring mis-sized sessions matters because the expensive hours are concentrated, and today they are visible only after the JSONL is already fat.

## Problem

Four gaps. Each one is paid in tokens, in late human time, or in review noise.

1. **In session.** Size shows up in archaeology. Worker `92a48e004519` ran **296** API calls. In `d006f5a0…`, half the subagents left the ideal band while the parent stayed modest. Nothing in the live loop tells an orchestrator to consider a handoff.

2. **After refine.** Briefs are emitted as a list. Nothing ranks which ones are large enough to read before `execute` spawns them. The maps set already contains a long refine (`6c87c96bd9bb`, “Refine Phase 3C”, **70** turns). Under-scoped mega-briefs are the plausible upstream of the fat workers above; this paper does not claim that causal link is measured yet.

3. **Unit complete.** The practical choice is skip review, or pay for `comprehensive-review` (or another agent) on every unit. There is no compact “needs review?” confidence between those two.

4. **Phase complete.** `evaluate_assert()` in `tools/driver/phase_assert.py` already decides pass/fail from `deterministic_outcome_evidence`: report `closed`, trailer/slug/phase alignment, Verification and Carried headings, and either the design outcome quoted in the body or a substantive verification block. Jev question `outcome-evidence` (pin `jev-1.13.0`, log threshold **≥ 2.5**) is recorded on `--live`. When that score disagrees, `decision_source` stays `deterministic` and `jev.disagreed_with_deterministic` is set. Fail still means `stop_and_escalate`, including when the report said `closed`. A deterministic pass that still reads thin has no separate alignment rating asking the bot to dig deeper.

Always-on frontier review would bill the other ~84% of subagents and every unit. A typed question on compact state is the missing middle.

## Proposal

Default for every use case: **log a signal and surface it**. The worker loop, `execute` dispatch, merge, and the bot’s next phase stay unblocked. Pin remains `jev-1.13.0`. State sent to Jev stays compact — counts, headings, brief ids, short excerpts — the same budget rule as `jev_state_slice` (slug, phase, design outcome, closing headings and body, workflow report, trailer; not a transcript). These questions do not go through `tools/transcript/classify.py`.

Where a deterministic check exists on the same state, that check stays authoritative. A disagreeing Jev score is logged and dropped for any gate, matching `evaluate_assert()`.

### 1. PostToolBatch — progress, remaining work, overall size

**Trigger.** `PostToolBatch`, after a tool batch completes.

**Deterministic gate (no model).** Examples from the ideal band:

- API or tool turns at the **50–75** band, and signal-worthy once past ~75 (the maps “over turns” flag was >100).
- Estimated context or JSONL size in the **>125k** neighborhood, using peak context as the sizing signal.
- Optional: session metadata shows parallel fat workers overlapping.

Most batches never leave this gate, so most batches never call Jev. The driver reorient parked per-turn Jev inside worker loops. This use case asks Jev only after the mechanical gate trips.

**Optional Jev.** One Score or Choice on that compact state: progress against remaining scope, whether the session is still on the brief, and overall size. The output is a signal — a log row plus a surface to the parent or orchestrator (“consider handoff”). Someone acts. The hook does not stop the loop.

**Nearby events, not this use case’s behaviour.** `SubagentStart` can stamp brief id and a budget baseline. `Stop` can attach in-flight signals to the metrics row. Compaction handoff stays out of scope (Non-goals).

### 2. After refine — complexity per brief

**Trigger.** The `refine` skill finishes and the phase has N briefs.

**Deterministic pre-gate.** Always emit the brief list (ids, titles, line counts). Enumeration does not need Jev.

**Optional Jev.** A per-brief complexity Score, or a rank, on bounded brief text plus the DESIGN phase outcome. Surface the **top-k** largest ratings for a person or the bot to read before `execute`. Dispatch stays open.

This is the in-flow cousin of the parked P3 item (an offline evaluator–optimizer for brief quality). That offline assert stays parked.

### 3. Unit complete — “needs review?”

**Trigger.** Unit closing record and trailer, at `SubagentStop` or when the phase worker is done.

**Deterministic pre-gate.** Trailer present, required headings present, and any verifier command exit code that is already mechanical.

**Optional Jev.** A “needs review?” confidence (Score or Choice) on the compact closing record — phase-assert shape, unit scope. High confidence is permission to **consider** spawning `comprehensive-review` or a small review agent. Low confidence is log-only. The spawn is the expensive follow-up this pre-filter exists to cut.

### 4. Phase complete — alignment sanity

**Trigger.** Phase `workflow-report` closed and the git trailer is on the branch — the same window as `assert_phase`.

**Deterministic pre-gate.** `python3 tools/driver/assert_phase.py --deterministic` (landed). Exit 0 on pass, exit 2 on fail. The bot escalates on deterministic fail. `--dry-run`, missing `TYPESAFE_API_KEY`, `--live`, and `--fixture-jev` stay as they are for `outcome-evidence`.

**Optional Jev.** A separate alignment-sanity Score: does the closing narrative match the design outcome’s intent? Logged beside the existing assert. On a deterministic **pass** that scores thin, the row can recommend dig-deeper before the bot triggers the next phase. On disagreement with the deterministic result, Jev does not gate. This score does not replace `outcome-evidence` and does not move `decision_source`.

## Economics

Frontier follow-up — `comprehensive-review`, another agent, Cody reading a transcript — is the expensive step. The bot’s loop cannot hold a full session. A typed Jev question over compact JSON is the cheap step: small input, pin `jev-1.13.0`, one JSONL row.

Treat Jev as a **conditional pre-filter**:

1. A deterministic condition decides whether a judgement is worth asking (turn/size gate, unit trailer already checked, phase assert already passed).
2. The Jev answer decides whether to spend the frontier follow-up.

If that filter skips even **~30%** of expensive follow-ups, and structural closure bugs still hit `assert_phase --deterministic` plus the eval verifier, the Jev calls pay for themselves ([`economics-jev-prefilter.md`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/economics-jev-prefilter.md)). The 30% figure is a break-even floor, not a quota. A higher skip rate is attractive only while false negatives stay visible and small.

The expensive failure mode is the inverse: a Jev score that becomes a reason to spawn review every time. That costs more than today and adds no verifier. Measurement therefore watches review-spawn count and cost per phase — already the observational targets in [`../GOALS.md`](../GOALS.md) — next to skip rate and false negatives.

In session, the maps numbers are why the **gate** matters before any model call. Sixteen percent of subagents were over ideal, and those few dominate hours of ~63M tokens. A counter that fires near 75–100 calls is cheaper than finding a 296-call, 12.7MB worker afterwards.

## Non-goals

- **Hard gates.** No default block of the worker loop, of `execute` dispatch, of merge, or of the next phase. Turning a signal into enforcement is a separate Cody decision. So is the analysis author’s hard cap near ~75 turns / ~100k context (handoff, not resume) and fresh handoff after compaction.
- **Classify as a KPI.** `tools/transcript/classify.py` stays a session-kind chart. These signals do not recalibrate it. Classify labels do not score this proposal.
- **Replacing the deterministic kill line.** Phase pass/fail stays `decision_source: deterministic`. Spike C thresholds, fixtures, and the `outcome-evidence` question stay as landed. This paper does not reopen [`2026-09-30-jev-hook-assertion-spike.md`](2026-09-30-jev-hook-assertion-spike.md).
- **Per-turn Jev inside worker loops.** Jev runs when a named condition fires, not on every tool batch.
- **Compaction policy and abnormal stops.** `PreCompact`, `PostCompact`, and `StopFailure` (for example `rate_limit`) are listed in the hook note. They are not one of the four locked use cases.
- **Offline brief-quality optimizer.** The parked P3 LangGraph-style assert for brief quality stays parked. Use case 2 is a hook signal only.

## Measurement

Session-kind accuracy is not a metric. Weekly skim reads a signal JSONL in the same family as `tools/driver/.run-record.jsonl` and `.assert-log.jsonl`, outside the plan folder. It does not read `classify.py`.

| Measure | Definition | Reading |
|---------|------------|---------|
| Skip rate | Share of candidate expensive follow-ups (review spawn, dig-deeper pass, human deep-dive) that conditional Jev marks skip | Around or above ~30% can pay for the Jev tax. Report the rate. 30% is a break-even floor, not a target to chase |
| False negatives | Skipped items that later fail a verifier, fail `assert_phase --deterministic`, or are marked by a person as “should have been reviewed” | Counted beside skip rate. A high skip rate with a high false-negative rate means the filter is too aggressive |
| Unnoticed oversize | Workers that pass 100 API turns with no PostToolBatch signal row | Fewer than the maps baseline (8 of 150 over 100 turns; the 296-call worker had none) |
| Hard-stops | New exits that kill a loop because of a Jev score | Stay at **zero** while this file is `draft` and while spikes are signal-only |
| Review spawns and cost per phase | Count of `comprehensive-review` (or equivalent) spawns, plus provider cost already on the run record | Spawns cluster on high “needs review?” units. Cost per phase does not rise from always-on review |
| Disagreement | Jev versus a deterministic check on the same state | Logged; mechanical result kept. Existing shape: `jev.disagreed_with_deterministic` |

False negatives need a verifier result or a person on a **sample of skips**. That sample is an outcome check. It is not a classify calibration set.

## Next spikes

Smallest experiments after Cody moves this file off `draft`. Backlog holds them until then. No hook code lands from this paper.

1. **PostToolBatch log only.** Append deterministic turn count and a context or JSONL size estimate to a gitignored JSONL. No Jev. No exit-code change. Answer, on the harness that actually runs workers: which events exist headless or in cloud versus local Claude Code, and how brief id, phase, and unit enter hook state without loading full skills.
2. **Jev on the gate.** One Score — progress, remaining scope, overall size — only when the gate trips. Signal row for the parent. Loop continues.
3. **Refine top-k.** Complexity Score per brief; show the largest ratings. `execute` dispatch unchanged.
4. **Unit shadow.** “Needs review?” confidence logged at unit close. Review agents stay manual until that log has both a skip rate and a false-negative read.
5. **Phase sanity score.** Alignment Score logged next to the existing assert, as a dig-deeper hint on deterministic passes. `assert_phase.py --deterministic` remains the kill line.

Spikes 1–2 also pick the JSONL path Grok Bot and weekly FINDINGS will skim. It stays outside the plan folder, same invariant as the run record.
