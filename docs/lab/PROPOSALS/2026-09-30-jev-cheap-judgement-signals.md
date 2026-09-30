---
title: Cheap conditional Jev judgements
status: resolved
disposition: recommendations accepted pending product wiring
date: 2026-09-30
updated: 2026-09-30
signal: Maps Claude 5h — 16% of subagents over the ideal band; densest window ~63M tokens, concentrated in a few fat workers.
owners: Workflow Optimiser, Cody
proofs: master 112ccfe (PR #24, squash)
---

# Cheap conditional Jev judgements

Research on these four use cases is closed. The recommendations below are accepted. Product code is not shipped: default Claude settings, the driver, `assert_phase`, and `classify.py` are unchanged. Wiring those callers is implementation. It is not another research pass.

Research pack: [`../RESEARCH/2026-09-30-jev-cheap-judgement-signals/`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/INDEX.md). Proofs: [`../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/README.md) on master `112ccfe`.

## Signal

The 2026-09-30 open-pajero-maps Claude analysis ([`evidence-maps-claude-5h.md`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/evidence-maps-claude-5h.md)) scored **150** subagents against the workflow ideal band of **50–75** API turns and **100–125k** peak context (`docs/analysis/2026-09-08-workflow-vs-field.md`).

| Metric | Value |
|--------|--------|
| Subagents analyzed | **150** |
| Over ideal | **24 (16%)** |
| Context > 125k | 17 |
| Turns > 100 | 8 |
| Worst peak/final contexts | ~160k, 156k, 154k, 145k, 143k |

Mis-sized subagents are a minority and dominate burn. Heaviest rolling 5-hour windows (tokens ≈ input + cache_creation + cache_read + output):

| Rank | Tokens | Calls | Window (AEST) |
|------|--------|-------|----------------|
| 1 | **63.35M** | 764 | 2026-09-25 10:54 → 15:54 |
| 2 | **62.87M** | 652 | 2026-09-14 18:29 → 23:29 |
| 3 | **56.95M** | 667 | 2026-09-25 09:29 → 14:29 |
| 4 | **52.66M** | 532 | 2026-09-22 20:06 → 2026-09-23 01:06 |
| 5 | **50.27M** | 586 | 2026-09-25 06:53 → 11:53 |

Active session `d006f5a0…`: wall ~**43.8h**; parent modest; **8** subagents, **778** API calls, **66.25M** of **71.53M** tokens inside subagents; **4/8** over ideal. Worker `92a48e004519`: **296** API calls, **12.7MB** JSONL, peak context **130k**, flags `OVER_TURNS` and `FAT_JSONL`. Worker `bb6165018de0` (session `bd4f6c0d…`): **154** API calls. Same-pack scale: `af9b5cb1…` has 19 subagents and **107.77M** tokens with **2/19** over ideal; `bd4f6c0d…` has **54** subagents, **194.80M** tokens, **7/54** over ideal.

Totals are deduped transcript `message.usage` and can differ from the Anthropic meter. Turn counts are deduped assistant API calls. OVER_CTX in the 125–147k band is often the compaction ceiling, so **peak** context is the sizing signal.

Phase closure already has a mechanical kill line ([`2026-09-30-jev-hook-assertion-spike.md`](2026-09-30-jev-hook-assertion-spike.md), `status: landed`). This paper is the next layer: in-session and refine / unit / phase **soft** judgements.

## Proof evidence (closed)

Runnable pack: `docs/lab/RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/run_proofs.sh`. Validated result checked in at [`proofs/validated/gate_simulation_result.json`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/validated/gate_simulation_result.json).

| Check | Result |
|-------|--------|
| `all_over_100_workers_escalate` | true |
| `smoking_gun_band_exit_before_100` | true (`92a48e004519` first `band_exit` at turn 76, first `escalate` at turn 100) |
| `smoking_gun_escalate` | true |
| Named workers | `92a48e004519` (296 turns, 130k peak, 12.7MB) and `bb6165018de0` (154 turns, 125k peak, ~3.3MB) trip `band_exit`, `handoff_signal`, `escalate`, and `jev_eligible`. Refine agent `6c87c96bd9bb` at 70 turns does not trip the gate. |
| Schemas | `test_proofs.py` dry-builds four `jev-1.13.0` requests. State JSON over **12_000** characters is rejected. Request blobs in tests stay under **16_000** characters. `phase-alignment-sanity` is a different question from `outcome-evidence`. |
| Hook probe | `post_tool_batch_signal.py` appends a row only when a gate flag is set, and exits 0. |

**LCD harness (closed, 2026-09-30).** Host `codyh-ubuntu`, checkout `112ccfe` (master after PR #24). OpenCode **1.18.33** with `deepseek/deepseek-flash` ran `run_proofs.sh`: **exit 0**. Gate simulation checks true. Unittest **6/6**. The fixture probe wrote **1** JSONL row (`kind=post_tool_batch`, `handoff_signal` and `jev_eligible`). That row matches the checked-in fixture: `fixtures/sample_transcript.jsonl` has three assistant messages and peak `input_tokens` **128_000**, which is `handoff` at 125k and `jev_eligible` at 128k, with no `band_exit` and no `escalate`.

OpenCode does not fire Claude `PostToolBatch` command hooks. It only exposes per-tool `execute` before and after. The live `tools/driver/.jev-signal-log.jsonl` path was skipped on that host. Accepted ops: live `PostToolBatch` logging runs on **Claude Code**, or on a custom OpenCode plugin that aggregates `tool.execute.after` into one batch and calls `process_hook_input`. The fixture probe (`run_proofs.sh`) is the validated stand-in on LCD.

## Problem

1. **In session.** Size shows up in archaeology. Nothing in the live loop tells an orchestrator to consider a handoff before a worker reaches 296 calls.
2. **After refine.** Briefs are emitted as a list. Nothing ranks which ones to read before `execute`.
3. **Unit complete.** The practical choice is skip review, or pay for `comprehensive-review` on every unit.
4. **Phase complete.** `assert_phase --deterministic` already kills on structural failure. A deterministic pass that still reads thin has no separate alignment rating.

## Resolved recommendations

Default for every use case: **append a JSONL row and surface it**. The worker loop, `execute` dispatch, merge, and the bot’s next phase stay unblocked. Pin `jev-1.13.0`. State sent to Jev stays inside the 12_000-character guard in [`jev_signal_schemas.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/jev_signal_schemas.py). These questions do not go through `tools/transcript/classify.py`.

Log file (gitignored, outside the plan folder): `tools/driver/.jev-signal-log.jsonl`, override `WORKFLOW_JEV_SIGNAL_LOG`. Audit file: `tools/driver/.jev-signal-audit.jsonl`.

Where a deterministic check exists on the same state, that check stays authoritative. A disagreeing Jev score is logged. It does not change an exit code.

### 1. PostToolBatch — deterministic gate, then optional Jev

**Trigger.** Claude Code `PostToolBatch`, once per model step after the parallel tool batch resolves. Stdin fields used: `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `agent_id` (subagent only), `tool_calls[]`. Turn count, peak context, and batch id are not in the payload. The hook derives them.

**Turn and size proxies** ([`post_tool_batch_signal.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/post_tool_batch_signal.py)):

| Input | Rule |
|-------|------|
| API turns | Count of JSONL rows with `type=assistant` and no `isSidechain`, when `transcript_path` is readable. Otherwise the per-`(session_id, agent_id)` `PostToolBatch` counter. |
| Counter state | `WORKFLOW_SIGNAL_STATE_DIR`, default `~/.cache/workflow-plugin/signal-state/<session>:<agent>.json`. |
| Peak context | Max of `input_tokens`, `cache_read_input_tokens`, and `cache_creation_input_tokens` on assistant `message.usage`. Transcript may lag the current turn. |
| Transcript bytes | `stat(transcript_path).st_size`. |

**Deterministic gate** ([`gate_thresholds.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/gate_thresholds.py)). No model.

| Level | Condition | Action |
|-------|-----------|--------|
| `band_exit` | `api_turns >= 76` | Append one `kind=post_tool_batch` row. No Jev. |
| `handoff_signal` | `api_turns >= 85` **or** `peak_ctx >= 125_000` **or** `transcript_bytes >= 3MiB` (3_145_728) | Same row. Surface to the parent: consider handoff. |
| `escalate` | `api_turns >= 100` **or** `peak_ctx >= 130_000` **or** `transcript_bytes >= 5MiB` (5_242_880) | Stronger surface on the same row. Still no block. Maps `OVER_TURNS` / early `FAT_JSONL`. |
| `jev_eligible` | `handoff_signal` **and** (`api_turns >= 85` **or** `peak_ctx >= 128_000` **or** `transcript_bytes >= 3MiB`) | One optional Jev request. The probe does not call Jev. Product wiring does. |

Append the row when any of `band_exit`, `handoff_signal`, or `escalate` is true. Batches inside the 50–75 turn band with peak context under 125k and transcript under 3MiB produce no row and no Jev call.

**Optional Jev.** Question id `session-progress`. Builder `build_session_progress_request`. State fields: `slug`, `phase`, `brief_id`, `api_turns`, `peak_ctx_tokens`, `transcript_bytes`, `last_tool_batch` (short `Tool:arg` strings), `design_outcome_line`.

| Question | Type | Use |
|----------|------|-----|
| `progress_vs_scope` | Score | Log only. |
| `handoff_recommended` | Choice `continue` \| `monitor` \| `handoff_soon` | `continue`: no parent action. `monitor`: surface the row. `handoff_soon`: parent plans a handoff or a narrower brief. |

Record the call as `kind=jev_shadow` with `jev.question_id=session-progress`, `jev.choice`, and `jev.skipped_follow_up` (`true` for `continue` and `monitor`). The hook command **exits 0**. It does not emit `decision: block`.

**Slug, phase, brief id** on the row, when product wiring adds them: `WORKFLOW_SLUG` and `WORKFLOW_PHASE` if the driver set them, otherwise the `Workflow-Phase:` trailer from `git log -1 --format=%b`. `brief_id` is the brief filename stem the driver already used to spawn the worker. The lab probe logs `session_id` and `agent_id` without those fields. That is sufficient for the gate.

**Harness.**

| Harness | Live `PostToolBatch` | Accepted path |
|---------|----------------------|----------------|
| Claude Code CLI, IDE, Desktop, cloud | Yes. Same events. Cloud sessions do not read local `~/.claude/settings.json`; seed the hook on the runner image. `CLAUDE_CODE_REMOTE=true` on the web. | Opt-in command hook in [`hooks-settings-snippet.json`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/hooks-settings-snippet.json). Timeout 10s. `python3` on `post_tool_batch_signal.py`. |
| Cursor Cloud Agent | No Claude hooks (`FINDINGS.md`: no `CLAUDECODE` / `CLAUDE_CODE_REMOTE`). | Driver or worker wrapper calls `evaluate_gate` and appends the same `post_tool_batch` row to `.jev-signal-log.jsonl`. |
| OpenCode / LCD | No `PostToolBatch` command hook. Per-tool `execute` before/after only. | Do not expect a live log. `run_proofs.sh` is the stand-in (proved on `codyh-ubuntu` @ `112ccfe`). A live row requires a custom plugin that aggregates `tool.execute.after` and calls `process_hook_input`. |

### 2. After refine — complexity ratings, review top 3

**Trigger.** The `refine` skill has finished and the phase has N briefs.

**Deterministic pre-gate.** Always write the brief list: `brief_id`, `brief_title`, `brief_line_count`. Enumeration does not call Jev. One `kind=refine_complete` row per brief may be written before the score exists.

**Optional Jev.** One request per brief. Question id `refine-brief-complexity`. Builder `build_refine_brief_request`. Score `brief_complexity`. State fields: `slug`, `phase`, `brief_id`, `brief_title`, `brief_line_count`, `brief_excerpt` (first ~1–2k characters of the brief), `design_outcome`.

**Review top 3.** Sort briefs by `brief_complexity` descending, tie-break `brief_line_count` descending. Surface **min(3, N)** to the person or the bot before `execute`. `execute` dispatch stays open at every score. The offline brief-quality optimizer on the backlog stays parked.

Refine agent `6c87c96bd9bb` (70 turns) does not trip the PostToolBatch gate. Its review path is this score, not the turn counter.

### 3. Unit complete — needs-review Choice, then maybe spawn review

**Trigger.** Unit closing record and trailer, at `SubagentStop` or when the phase worker is done. Probe: [`log_subagent_stop.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/log_subagent_stop.py) appends `kind=subagent_stop` (`session_id`, `agent_id`, `agent_type`, `agent_transcript_bytes`, `last_assistant_message_chars`) and exits 0. Same opt-in snippet as PostToolBatch.

**Deterministic pre-gate, before Jev.**

- Trailer present.
- Headings `Verification` and `Carried` present.
- If a verifier command already ran, record its exit code.

A missing trailer or missing heading is a mechanical miss: log it and do not ask Jev to bless the record. A non-zero verifier exit is already a reason to review or escalate. Jev runs when the mechanical checks passed.

**Optional Jev.** Question id `unit-needs-review`. Builder `build_unit_needs_review_request`. State fields: `slug`, `phase`, `unit_id`, `closing_headings`, `closing_body_excerpt`, `trailer`, `verifier_exit_code`. `unit_id` is the trailer `slug:phase` or the brief filename stem.

| Question | Type | Use |
|----------|------|-----|
| `needs_review` | Choice `skip` \| `maybe` \| `review` | `skip`: log only. `maybe`: include in the weekly 5-row sample; do not spawn. `review`: the parent **may** spawn `comprehensive-review` or a smaller review agent. |
| `review_confidence` | Score | Log beside the choice. The spawn decision follows the Choice. |

The hook does not spawn the reviewer. `jev.skipped_follow_up` is `true` for `skip` and `maybe`, `false` for `review`.

### 4. Phase complete — alignment sanity Score, advisory

**Trigger.** Phase `workflow-report` is `closed` and the git trailer is on the branch. Same window as `assert_phase`.

**Deterministic kill line.** `python3 tools/driver/assert_phase.py --deterministic`. Exit 0 pass, exit 2 fail. On exit 2 the bot escalates (`stop_and_escalate`), including when the report said `closed`. Do not call the alignment question to overturn that exit. `--dry-run`, missing `TYPESAFE_API_KEY`, `--live`, and `--fixture-jev` stay as they are for question `outcome-evidence` (log threshold **≥ 2.5** on `--live`). `decision_source` stays `deterministic`. `jev.disagreed_with_deterministic` on the assert log stays audit-only.

**Optional Jev, only after exit 0.** Question id `phase-alignment-sanity`. Builder `build_phase_alignment_sanity_request`. Score `alignment_sanity` only. State fields: `slug`, `phase`, `design_outcome`, `closing_headings`, `closing_body_excerpt`, `workflow_report`, `trailer`. This is not `outcome-evidence` and it does not move `decision_source`.

Log `kind=jev_shadow` with `jev.question_id=phase-alignment-sanity` and `jev.score` on `.jev-signal-log.jsonl`. A low score (narrative contradicts the design outcome, or alignment is thin) is a dig-deeper hint for the bot before it triggers the next phase. The bot may still trigger the next phase. The assert exit code stays 0.

## Economics

Frontier follow-up (`comprehensive-review`, another agent, a person reading a transcript) is the expensive step. A typed Jev question over compact JSON is the cheap step: pin `jev-1.13.0`, one JSONL row, state under 12_000 characters.

The filter is two steps. A deterministic condition decides whether a judgement is worth asking. The Jev answer decides whether to spend the frontier follow-up. Skipping about **30%** of expensive follow-ups pays for the Jev calls while `assert_phase --deterministic` and the eval verifier still catch structural closure bugs ([`economics-jev-prefilter.md`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/economics-jev-prefilter.md)). Thirty percent is a break-even floor. It is not a quota.

In session, the gate is the saving. Sixteen percent of subagents were over ideal and those few dominate windows of ~63M tokens. `band_exit` at 76 would have logged `92a48e004519` long before 296 calls and a 12.7MB JSONL.

## Non-goals

- **Hard gates from these signals.** The worker loop, `execute` dispatch, merge, and the next phase stay unblocked. `assert_phase --deterministic` remains the kill line. Hard caps near ~75 turns / ~100k context, and a fresh handoff after compaction, are outside this resolution.
- **Classify as a KPI.** `tools/transcript/classify.py` stays a visualisation POC. These signals do not recalibrate it. Classify labels do not score this paper.
- **Replacing the deterministic kill line.** Phase pass/fail stays `decision_source: deterministic`. Spike C thresholds, fixtures, and `outcome-evidence` stay as landed.
- **Per-turn Jev inside the worker loop.** Jev runs when `jev_eligible` is true, or at the refine / unit / phase points above. It does not run on every tool batch.
- **Compaction policy and abnormal stops.** `PreCompact`, `PostCompact`, and `StopFailure` are not one of the four use cases.
- **Offline brief-quality optimizer.** The parked P3 LangGraph-style assert for brief quality stays parked. Use case 2 is the in-flow score only.
- **SubagentStart budget stamps and Stop metric attachment.** Out of this resolution. Brief id comes from the driver env or the brief filename, as specified in use case 1.

## Measurement

Weekly skim is an ops rule. It reads `.jev-signal-log.jsonl`, `.assert-log.jsonl`, and `.run-record.jsonl`. It does not read `classify.py`. Recipe: [`proofs/validated/weekly_skim_recipe.sh`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/validated/weekly_skim_recipe.sh). Plan: [`proofs/false-negative-measurement-plan.md`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/false-negative-measurement-plan.md).

| Measure | Definition | Reading |
|---------|------------|---------|
| Skip rate | `skips / (skips + spawns)` for `comprehensive-review` (and the same shape for dig-deeper and human deep-dives) | Report the rate. Around or above ~30% covers the Jev tax. 30% is a floor, not a target |
| False negatives, mechanical | `needs_review=skip` and a later `assert_phase --deterministic` fail for the same `slug` + `phase` within 7 days | Count beside skip rate |
| False negatives, human | 5 random `skip` rows each week | Append `{signal_row_id, verdict: should_have_reviewed\|ok_skip}` to `tools/driver/.jev-signal-audit.jsonl` |
| Escalate rate | Share of `post_tool_batch` rows with `gate.escalate=true`, and distinct `agent_id` with `band_exit` | From the weekly recipe |
| Unnoticed oversize | Workers with `api_turns > 100` and zero `band_exit` rows before turn 100 | Maps baseline: 8 of 150 over 100 turns; `92a48e004519` had none |
| Hard-stops from a Jev score | Exits that kill a loop because of `session-progress`, `brief_complexity`, `needs_review`, or `alignment_sanity` | Stay at **zero** |
| Review spawns and cost per phase | `comprehensive-review` spawns and provider cost on the run record | Spawns cluster on Choice `review`. Cost per phase does not rise from always-on review |
| Disagreement | `jq 'select(.jev.disagreed_with_deterministic==true)' tools/driver/.assert-log.jsonl` | Audit only. Mechanical result kept |

Until the run record grows a `review_spawn` field, spawn counts are the manual figures already written in `FINDINGS.md`. The 5-row audit is an outcome check. It is not a classify calibration set.

## Accepted outcomes

| Artifact | Becomes |
|----------|---------|
| [`gate_thresholds.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/gate_thresholds.py) (`band_exit` 76, handoff 85 / 125k / 3MiB, escalate 100 / 130k / 5MiB, Jev at 85 / 128k / 3MiB) | Lab guidance. Product wiring imports these constants. The numbers are closed. |
| [`hooks-settings-snippet.json`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/hooks-settings-snippet.json), [`post_tool_batch_signal.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/post_tool_batch_signal.py), [`log_subagent_stop.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/log_subagent_stop.py) | Lab guidance, opt-in. Not default plugin settings. Exit 0. |
| [`jev_signal_schemas.py`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/jev_signal_schemas.py) | Contract for `session-progress`, `refine-brief-complexity`, `unit-needs-review`, and `phase-alignment-sanity`. |
| [`weekly_skim_recipe.sh`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/validated/weekly_skim_recipe.sh) | Ops rule for the weekly Grok Bot skim. |
| Cursor Cloud JSONL writer; OpenCode fixture stand-in | Guidance in use case 1. LCD proof on `codyh-ubuntu` @ `112ccfe` closed the harness question. |
| `classify.py` | Stays a POC chart. |
| `assert_phase.py --deterministic` | Stays the kill line. |

## Product wiring

Implementation, not research. None of this is in the default driver or plugin settings on `112ccfe`.

1. Keep `gate_thresholds.py` and `jev_signal_schemas.py` as the source of numbers and request bodies. Do not retune them from a new study.
2. Claude Code: install the opt-in snippet on the runner that should log. Command exits 0.
3. Cursor Cloud: append the same `post_tool_batch` row from the driver or a worker wrapper. There is no Claude hook on that harness.
4. OpenCode / LCD: keep `run_proofs.sh` as the check. Add a live log only with a plugin that aggregates `tool.execute.after` into one `process_hook_input` call.
5. Call Jev only at the four points above (`jev_eligible`, each refine brief, unit close after the mechanical pre-gate, phase close after deterministic exit 0). Log `jev_shadow` or `refine_complete`. Do not block.
6. Leave `evaluate_assert()`, `decision_source`, and `classify.py` unchanged.
