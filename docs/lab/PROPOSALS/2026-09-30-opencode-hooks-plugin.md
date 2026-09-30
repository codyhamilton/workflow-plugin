---
title: OpenCode hooks plugin
status: resolved
disposition: recommendations accepted pending product wiring
date: 2026-09-30
updated: 2026-09-30
signal: Cheap-Jev soft signals have no OpenCode PostToolBatch; OpenCode only exposes per-tool execute hooks.
owners: Workflow Optimiser, Cody
proofs: master d4c4da1 (PR #28); LCD codyh-ubuntu @ d4c4da1
---

# OpenCode hooks plugin

Research on an OpenCode-native soft-signal plugin is closed. The recommendations below are accepted. Product code is not shipped: no npm package, no `opencode.json` registration, no change to `install.sh`, `tools/driver/`, `assert_phase`, or `classify.py`. Wiring the package is implementation. It is not another research pass.

Research pack: [`../RESEARCH/2026-09-30-opencode-hooks-plugin/`](../RESEARCH/2026-09-30-opencode-hooks-plugin/INDEX.md). This paper is the OpenCode layer on top of the resolved cheap-Jev signals ([`2026-09-30-jev-cheap-judgement-signals.md`](2026-09-30-jev-cheap-judgement-signals.md)). It reuses those gate numbers. It does not retune them.

## Signal

The cheap-Jev resolution left three harness paths for use case 1 (session size / progress). Claude Code can run an opt-in `PostToolBatch` command hook. Cursor Cloud appends the same JSONL row from the driver. OpenCode has no `PostToolBatch` command hook. The LCD stand-in for that paper was the Jev fixture probe (`run_proofs.sh` on `codyh-ubuntu` @ `112ccfe`), which never installed a plugin.

OpenCode's plugin surface is TypeScript hooks in-process (Bun), registered from `opencode.json` or `file://`, documented in the public [opencode-plugins-manual](https://github.com/joshuadavidthomas/opencode-plugins-manual). Inventory: [`OPENCODE-PLUGIN-API.md`](../RESEARCH/2026-09-30-opencode-hooks-plugin/OPENCODE-PLUGIN-API.md). Site map: [`HOOK-SITE-MAP.md`](../RESEARCH/2026-09-30-opencode-hooks-plugin/HOOK-SITE-MAP.md).

## Problem

1. **No batch stdin.** Claude `PostToolBatch` delivers `tool_calls[]` once per model step. OpenCode fires `tool.execute.after` once per tool. A Claude command hook script does not run there.
2. **Shared thresholds need one caller.** `gate_thresholds.py` (`band_exit` at 76) is the closed cheap-Jev gate. OpenCode has to call that gate once per model step, after the tools in the step are collected.
3. **Packaging.** Putting a Bun/TS lifecycle inside `tools/driver/` or the core `workflow` plugin would ship soft signals on Claude and Cursor installs and would couple them to the skills symlink path.
4. **Phase control stays outside the plugin.** Grok Bot still drives phases with `tools/driver/`. On the OpenCode machine the harness persona `orchestrate` only delegates.

## Proof evidence (closed)

Runnable pack: `docs/lab/RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/run_proofs.sh`. It runs `python3 -m unittest discover` on `test_proofs.py`. It does not start OpenCode and does not load `plugin_sketch.ts`.

| Test | Result the code asserts |
|------|-------------------------|
| `test_seventy_six_steps_band_exit_and_log` | 76 single-tool steps, empty transcript. Last entry `api_turns_proxy` **76**, `gate.band_exit` **true**, signal log has at least one line. Turn proxy is `post_tool_batch_count` because no transcript is passed (`process_hook_input`). |
| `test_parallel_tools_one_step` | Two `tool.execute.after` events then one `flush_step`. `tool_calls_in_batch` **2**, `post_tool_batch_count` **1**. |
| `test_analytics_envelope_opencode_host` | `WORKFLOW_INSTALL_MODE=opencode`, `WORKFLOW_ANALYTICS_URL` unset, 76 steps. Local signal log still exists. |
| `test_smoking_gun_shared_thresholds` | `evaluate_gate(api_turns=296, peak_ctx_tokens=130_000, transcript_bytes=13_312_000).escalate` is true. Same module as the cheap-Jev paper (`BAND_EXIT_TURNS = 76`). |

`OpenCodeBatchAggregator.flush_step` builds a `hook_event_name: PostToolBatch` payload and calls `process_hook_input` from the Jev pack. The log row is appended only when `band_exit`, `handoff_signal`, or `escalate` is set. At turn 76 with no peak-context and no transcript bytes, `band_exit` is the flag that writes the row (`api_turns >= 76`). Handoff stays at 85 / 125k / 3MiB. The probe does not call Jev.

When a gate flag is set, `flush_step` calls `emit_from_jev_signal_row` in the sink pack (`local_path=None`, so the helper does not write a second local copy). `detect_host()` returns `host_kind: opencode`, `host_detail: opencode` when `WORKFLOW_INSTALL_MODE=opencode`. With `WORKFLOW_ANALYTICS_URL` unset, `post_remote` returns `skipped:no_url` and does not raise. The aggregator discards that return value. The unittest checks the local log, not the envelope fields.

**LCD harness (closed, 2026-09-30).** Coding Harness Manager, host `codyh-ubuntu`, checkout `d4c4da1` (master after PR #28). `run_proofs.sh` **exit 0**. Unittest **4/4**. The turn-76 simulation wrote **one** `post_tool_batch` row on the Jev signal log with `gate.band_exit=true`. **`plugin_sketch.ts` was not installed.** No `file://` plugin, no `opencode.json` registration, no live `tool.execute.after` from an OpenCode process. That host run closes the lab proofs. It does not open a follow-up spike.

`plugin_sketch.ts` is the subscription sketch: buffer `tool.execute.after`, flush on event type `message.updated` or `session.idle`, spawn `batch_flush_cli.py`. `run_proofs.sh` does not execute it. The validated contract is the Python aggregator and the stdin JSON that `batch_flush_cli.py` already accepts (`session_id`, `transcript_path`, `cwd`, `tool_calls[]`).

## Resolved recommendations

### 1. Separate npm OpenCode plugin; lab proofs stay in-tree

| Choice | Resolution |
|--------|------------|
| npm package (working name `@codyhamilton/opencode-workflow-signals`) | **Accepted** for product wiring. OpenCode loads `"plugin"` entries from `opencode.json` (npm pin or `file://`). Version pin stays independent of workflow-plugin **2.5.0**. |
| In-tree `proofs/plugin_sketch.ts`, `batch_aggregator.py`, `opencode.json.example` | **Lab only**, until that package exists. `opencode.json.example` is not installed by `install.sh`. |
| Merge into core `workflow` or `workflow-lab` manifests | **Rejected.** Soft signals stay off the default Claude and Cursor plugin install. |

### 2. Approximate PostToolBatch; no native batch event

Buffer each `tool.execute.after` (`tool`, `callID`, short output preview, cap 500 characters, matching `_SessionBatch.record`). Flush once per model step on `message.updated` or `session.idle`, then call the shared gate. OpenCode has no `PostToolBatch` event and no `tool_calls[]` stdin blob. The flush heuristic is the accepted approximation. The LCD run did not fire those events, because the sketch was not installed. Product wiring is what first runs the subscription on a host OpenCode build.

Parallel tools in one step count as one batch (`test_parallel_tools_one_step`). The row shape stays `kind: post_tool_batch` so the weekly skim can read Claude rows and OpenCode rows from `tools/driver/.jev-signal-log.jsonl` (`WORKFLOW_JEV_SIGNAL_LOG`).

### 3. Soft signals stay advisory; deterministic assert stays the kill line

The plugin logs and returns. It does not emit a blocking permission decision, does not change an exit code, and does not call `assert_phase` to overturn a result. Phase pass/fail remains:

`python3 tools/driver/assert_phase.py --deterministic`

Exit 0 pass, exit 2 fail with `stop_and_escalate`. `decision_source` stays `deterministic`. A disagreeing Jev score stays `jev.disagreed_with_deterministic` on the assert log, audit only. Optional Jev inside this plugin, when product wiring adds it, uses the cheap-Jev question `session-progress` and only when `jev_eligible` is already true. The lab proofs do not call Jev.

### 4. Optional analytics dual-write

Reuse [`dual_write_sink.py`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py). Local legacy row first. Remote POST only when `WORKFLOW_ANALYTICS_URL` is set. Bearer token `WORKFLOW_ANALYTICS_TOKEN` when present. Remote failure sets `_remote_ok: false` and must not stop the agent loop.

| Env | Envelope |
|-----|----------|
| `WORKFLOW_INSTALL_MODE=opencode` | `host_kind: opencode`, `host_detail: opencode` (`detect_host`) |
| `WORKFLOW_ANALYTICS_URL` unset | `post_remote` detail `skipped:no_url`; local signal row still written |
| Gate row `kind: post_tool_batch` | Envelope `kind: jev.post_tool_batch` via `emit_from_jev_signal_row` |

`WORKFLOW_ANALYTICS_HOST_KIND` remains the test override. Full tool stdout, `TYPESAFE_API_KEY`, and classify logs stay out of the envelope ([`ANALYTICS-INTEGRATION.md`](../RESEARCH/2026-09-30-opencode-hooks-plugin/ANALYTICS-INTEGRATION.md)). Driver `run_record.py` is unchanged.

### 5. Skills stay on the symlink path

PR #26 (`663b214`). `./install.sh --opencode-skills` or `WORKFLOW_INSTALL_MODE=opencode ./install.sh` symlinks `skills/<name>` to `~/.config/opencode/skills/<name>`. The signals plugin does not copy skills, does not call `reloadSkills`, and does not replace `check_skills.py`. Session start on OpenCode is `session.created` (observe only). Skill presence stays an install-time fact.

### 6. Orchestrate is not the phase-runner (ops)

On the OpenCode machine, harness persona **`orchestrate` is task-and-skill only**. It delegates. It does not run a phase, read the plan folder as a driver, or own trailers.

| Role | Owner on OpenCode |
|------|-------------------|
| Delegation persona | `orchestrate` (task + skills) |
| One phase, then stop | skill `execute` (`Workflow-Phase:` trailer) |
| Unattended multi-phase loop | Claude Code, or Cursor Cloud plus `tools/driver/` — OpenCode has no driver provider |
| Soft-signal log | this plugin, once wired |
| Hard kill | `assert_phase.py --deterministic` |

Built-in OpenCode `plan` stays unrelated to workflow `design`. The plugin implements none of those roles.

### 7. Flash on the build path (guidance)

Same invariant as [`../GUIDANCE-flash-review-gate.md`](../GUIDANCE-flash-review-gate.md). Guidance only. The signals plugin does not encode it. No hook, gate, installer, or `assert_phase` change.

**DeepSeek Flash is encouraged** to execute briefs and implement phase units when rationing orchestrator capacity: Claude gaps, parallel unit throughput, or cost pressure. OpenCode is the usual map. The gate does not limit whether Flash runs. It bounds who may sign the phase after Flash touched unit work.

1. **Draft.** Flash drafts and implements assigned briefs and units.
2. **Review.** Every Flash build-path pass triggers a Sonnet 5.5 review of that output (diffs, brief completion, unit reports), keyed to the phase outcome. The review is required.
3. **Hold.** Flash work does not auto-close the phase. No terminal verification, no `Workflow-Phase:` trailer, and no treating the phase as done from a Flash run. The phase stays on a review hold until Claude Code or Grok (Build Orchestrator) validates the outcome and signs.
4. **Sign-off.** Only Claude Code or Grok lands the trailer and closes the phase. They review the phase, including Sonnet’s review of the Flash work.

Pattern: **Flash draft (briefs / units) → Sonnet 5.5 review of Flash work → Claude Code or Grok phase validation and sign-off.**

`orchestrate` stays task-and-skill delegation. It does not sign and it does not release the hold. `execute` still stops after a phase close; when Flash ran on units, only Claude Code or Grok performs that close. `assert_phase --deterministic` stays the mechanical kill line on that host. The plugin does not open the hold, spawn Sonnet 5.5, or write the trailer. Flash does not replace plan-end `comprehensive-review`.

## Economics

The expensive follow-up is still a frontier review or a human reading a transcript. The cheap step is one JSONL row when `gate_thresholds.py` trips, same numbers as the cheap-Jev paper (`band_exit` 76, handoff 85 / 125k / 3MiB, escalate 100 / 130k / 5MiB). Aggregating tools into one flush per model step spends one gate evaluation per step. Evaluating on every `tool.execute.after` would multiply log rows inside a parallel batch (`test_parallel_tools_one_step` keeps the count at 1).

A separate npm package keeps that cost off Claude and Cursor installs. Those harnesses already have their accepted paths (command hook, driver JSONL). Loading a Bun plugin from the core workflow manifest would put advisory logging on hosts that do not run OpenCode.

## Non-goals

- **Drop-in Claude or Cursor hooks.** This plugin does not claim Claude stdin schemas or Cursor hook JSON. `post_tool_batch_signal.py` stays the Claude command hook. Cursor Cloud stays a driver JSONL writer (`host_kind: cloud` when `CURSOR_AGENT=1`).
- **A real `PostToolBatch` event.** The name on the synthetic payload is the shared gate's input shape. OpenCode does not emit that event.
- **`SubagentStop` / `Stop` parity.** There is no OpenCode stdin equivalent of `log_subagent_stop.py`. `session.idle` is the flush and end-of-turn signal used above. It is not a subagent-stop record (`agent_type`, `agent_transcript_bytes`, last assistant message). Unit-complete `needs_review` stays on the Claude probe until a later product decision. This resolution does not invent that mapping.
- **Moving the kill line into the plugin.** `assert_phase --deterministic` stays the CLI. Classify stays a visualisation POC.
- **Default product enablement.** No install path registers the plugin. `WORKFLOW_OPENCODE_SIGNALS=0` in the sketch is a local off switch for a file that is not installed.
- **Retuning gates.** `BAND_EXIT_TURNS` and the rest stay the cheap-Jev constants.
- **Compaction policy.** `session.compacted` can log later. It is not one of the accepted behaviours in this paper.
- **Live hook timing as further research.** `message.updated` versus `session.idle` is the accepted flush pair. The LCD run did not install the sketch, so host event order is not a remaining lab question.
- **Hook enforcement of the Flash review gate.** Flash is encouraged on briefs and units. That work does not auto-close the phase: Sonnet 5.5 reviews Flash output, and the phase stays on hold until Claude Code or Grok signs. Canonical text is [`GUIDANCE-flash-review-gate.md`](../GUIDANCE-flash-review-gate.md). It is not a plugin rule, a gate flag, or a driver branch.

## Measurement

Same weekly skim as the cheap-Jev paper: `.jev-signal-log.jsonl`, `.assert-log.jsonl`, `.run-record.jsonl`. Recipe: [`weekly_skim_recipe.sh`](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/validated/weekly_skim_recipe.sh). Classify output is not a measure.

| Measure | Reading on OpenCode |
|---------|---------------------|
| `post_tool_batch` rows with `gate.band_exit` | Present after the turn proxy hits 76. The LCD row is the fixture for that flag. |
| `api_turns_source` | `post_tool_batch_count` when the plugin has no transcript; `transcript_assistant` when `transcript_path` is a readable JSONL. |
| `tool_calls_in_batch` | Greater than 1 when one flush collected parallel tools. |
| Analytics | When `WORKFLOW_ANALYTICS_URL` is set and `WORKFLOW_INSTALL_MODE=opencode`, envelopes use `host_kind: opencode`. Unset URL is a skip, not a failure. |
| Hard-stops from this plugin | **Zero.** Soft-signal logging does not kill the loop. |
| `assert_phase --deterministic` | Unchanged exit codes. Disagreements stay audit rows. |

## Accepted outcomes

| Artifact | Becomes |
|----------|---------|
| [`RECOMMENDATION.md`](../RESEARCH/2026-09-30-opencode-hooks-plugin/RECOMMENDATION.md) | Separate npm plugin; in-tree proofs until wiring; orchestrate is not the phase-runner. |
| [`batch_aggregator.py`](../RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/batch_aggregator.py), [`batch_flush_cli.py`](../RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/batch_flush_cli.py) | Lab contract for buffer, flush, shared gate, optional dual-write. |
| [`plugin_sketch.ts`](../RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/plugin_sketch.ts), [`opencode.json.example`](../RESEARCH/2026-09-30-opencode-hooks-plugin/proofs/opencode.json.example) | Subscription sketch only. Not installed on `codyh-ubuntu`. Not loaded by `run_proofs.sh`. |
| [`HOOK-SITE-MAP.md`](../RESEARCH/2026-09-30-opencode-hooks-plugin/HOOK-SITE-MAP.md) | Gap table. `PostToolBatch` is approximate. `SubagentStop` / `Stop` have no parity. Cursor Cloud stays driver JSONL. |
| `gate_thresholds.py` | Unchanged source of numbers. |
| `assert_phase.py --deterministic` | Unchanged kill line. |
| PR #26 symlink install | Unchanged skills path. |
| [`GUIDANCE-flash-review-gate.md`](../GUIDANCE-flash-review-gate.md) | Flash encouraged for briefs/units. No auto close-out. Sonnet 5.5 reviews Flash work. Claude Code or Grok signs. Guidance only. Not hook behaviour. |

## Product wiring

Implementation, not research. None of this is on `d4c4da1` as a running plugin.

1. Publish the npm package from the lab contract. Register it in the consuming repo's `opencode.json`. Do not add it to `install.sh` or to the Claude/Cursor plugin manifests.
2. Subscribe to `tool.execute.after` and flush on `message.updated` or `session.idle`. Feed `batch_flush_cli.py` a complete stdin JSON payload, then close stdin. The sketch's spawn expression is not the tested path.
3. Keep calling `process_hook_input` / `evaluate_gate`. Do not fork the thresholds.
4. Call `emit_from_jev_signal_row` only as an optional dual-write. Leave the agent loop up when the POST fails or the URL is unset.
5. Leave skills on `./install.sh --opencode-skills`. Leave `orchestrate` as task-and-skill delegation. Leave phase closure on `execute` and the kill line on `assert_phase --deterministic`.
6. Leave Cursor Cloud on the driver JSONL writer. Leave Claude `PostToolBatch` on `post_tool_batch_signal.py`.
7. Leave the Flash review gate as operator guidance (section 7 and [`GUIDANCE-flash-review-gate.md`](../GUIDANCE-flash-review-gate.md)). Flash on briefs or units stays encouraged and does not auto-close the phase. Do not add a hook that blocks Flash, spawns Sonnet 5.5, opens the hold, or writes the phase trailer.
