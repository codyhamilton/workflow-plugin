---
title: Durable analytics sink
status: resolved
disposition: recommendations accepted pending product wiring
date: 2026-09-30
updated: 2026-09-30
signal: Cursor Cloud Agents drop workspace JSONL when the VM ends, so local run, assert, and Jev logs are not a cross-run observability plane.
owners: Workflow Optimiser, Cody
proofs: master 1bff769 (PR #27, squash)
---

# Durable analytics sink

Research on the sink is closed. The recommendations below are accepted. Product code is not shipped: default Claude settings, the driver, `assert_phase`, Jev probes, and `classify.py` are unchanged. Wiring an opt-in dual-write helper is implementation. It is not another research pass. Collector deployment is out-of-repo ops.

Research pack: [`../RESEARCH/2026-09-30-durable-analytics-sink/`](../RESEARCH/2026-09-30-durable-analytics-sink/INDEX.md). Proofs: [`../RESEARCH/2026-09-30-durable-analytics-sink/proofs/`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/README.md) on master `1bff769`.

## Signal

Workflow-plugin already emits structured events inside the workspace. [`INVENTORY.md`](../RESEARCH/2026-09-30-durable-analytics-sink/INVENTORY.md) catalogues them.

| Family | Path | Survives cloud VM teardown? |
|--------|------|------------------------------|
| Phase checkpoint | `Workflow-Phase:` trailers via `tools/driver/resolve.py` | Yes, once pushed |
| Run record | `tools/driver/.run-record.jsonl` (`DRIVER_RUN_RECORD` / `--record`) | No — gitignored workspace file |
| Assert log | `tools/driver/.assert-log.jsonl` | No |
| Jev soft signals | `tools/driver/.jev-signal-log.jsonl` (`WORKFLOW_JEV_SIGNAL_LOG`) | No |
| Classify chart | `tools/transcript/.classify-log.jsonl` | No, and outside this sink |

Stdout from `status.py`, MCP, and `check_skills.py` is ephemeral unless a caller persists it. Cursor Cloud Agents boot from a snapshot and lose the VM when the run ends, so those JSONL files are not comparable across runs or hosts.

Related layer, already resolved: [`2026-09-30-jev-cheap-judgement-signals.md`](2026-09-30-jev-cheap-judgement-signals.md). That paper decides **which** soft rows to append. This paper decides **where** durable copies of run, assert, and Jev rows go.

## Proof evidence (closed)

Runnable pack: `docs/lab/RESEARCH/2026-09-30-durable-analytics-sink/proofs/run_proofs.sh`. Validated artifacts checked in from the research run (session `bc-0d942d33-7e86-5b68-b969-cfcc54169a71`).

| Check | Result |
|-------|--------|
| Local append, no URL | `emit_event` writes the legacy row (`kind: trigger`) and returns `_remote_detail: skipped:no_url`, `_remote_ok: true`. |
| Mock collector | [`dual_write_result.json`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/validated/dual_write_result.json): `remote_detail` `http:204`, `event_id` `6ca9e713-188b-4fad-a1a4-a1aa933f55e0`. [`mock_sink_received.jsonl`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/validated/mock_sink_received.jsonl): `auth_present: true`, body `schema_version` 1, `kind` `driver.trigger`, `host_kind` `cloud`, `host_detail` `cursor-cloud`. |
| HTTPS egress | [`egress_cloud_result.json`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/validated/egress_cloud_result.json): `ok: true`, `http_status` 200, target `https://httpbin.org/post`, `host_kind` `cloud`, `host_detail` `cursor-cloud`, `kind` `harness.egress_probe`, recorded `2026-09-30T13:21:53.871088+00:00`. |
| Egress policy | Research pack recorded `egress.restricted: false` for environment `3a472955-b113-11f1-a3d8-362438fd9788`. This resolution run reads the same environment id and the same `egress.restricted: false`. |
| Helper boundary | `dual_write_sink.py` is not imported by `tools/driver/` on `1bff769`. |

`post_remote` never raises. HTTP 4xx/5xx, `URLError`, timeout, and `OSError` come back as `(False, detail)`. Unset `WORKFLOW_ANALYTICS_URL` is success with `skipped:no_url`. Timeout on the analytics POST is **10** seconds. The egress probe uses **15** seconds and writes the JSON artifact either way.

This resolution re-ran `run_proofs.sh`: exit 0, unittest 4/4, mock collector `http:204`, egress `ok: true` with HTTP 200 and `host_kind: cloud`. The checked-in artifacts above stay the `1bff769` capture.

## Problem

1. **Cloud runs.** Cost, assert slices, and soft-signal rows live in gitignored JSONL. After the VM is destroyed, a later session has trailers and whatever was pushed. It does not have the run record.
2. **Many emitters, no envelope.** Run record, assert log, and Jev log each have their own row shape. A collector cannot ingest them as one stream.
3. **Wrong buses for hook volume.** Git commits and PR comments are durable and too coarse for PostToolBatch-scale rows. Direct object-storage upload would put storage credentials on the agent VM.

## Resolved recommendations

Default: **append the existing local JSONL row, then optionally POST envelope v1.** Remote failure leaves hook and driver exit codes unchanged. Soft Jev rows stay advisory. `assert_phase --deterministic` stays the kill line. `classify.py` stays a visualisation POC and is not an envelope family.

### 1. Always local JSONL on the existing paths

Every accepted family keeps today's file and today's row shape.

| Family | Local path | Local row | Remote `kind` |
|--------|------------|-----------|---------------|
| Run record | `tools/driver/.run-record.jsonl` | `kind: trigger` | `driver.trigger` |
| Run record | same | `kind: assert` | `driver.assert` |
| Assert log | `tools/driver/.assert-log.jsonl` | live assert row | `assert.live` |
| Jev PostToolBatch | `tools/driver/.jev-signal-log.jsonl` | `kind: post_tool_batch` | `jev.post_tool_batch` |
| Jev SubagentStop | same | `kind: subagent_stop` | `jev.subagent_stop` |
| Jev shadow | same | `kind: jev_shadow` (cheap-Jev resolution) | `jev.shadow` |

`emit_event` writes `legacy_row` unchanged when both `local_path` and `legacy_row` are set. The POST body is the envelope. Helper fields `_remote_ok` and `_remote_detail` are on the return value. They are not part of the POST.

`emit_from_jev_signal_row` prefixes `jev.` when the local `kind` does not already start with `jev.`. That matches the schema for `post_tool_batch` and `subagent_stop`. A local `jev_shadow` row would prefix to `jev.jev_shadow`. The locked remote name is the schema's `jev.shadow`: product wiring calls `emit_event(kind="jev.shadow", ...)` or passes a row whose `kind` is `shadow` or `jev.shadow`.

`harness.check_skills` is a reserved `kind` for a future preflight row (`ok`, `missing`). `check_skills.py` still prints stdout only.

### 2. Optional remote — `WORKFLOW_ANALYTICS_URL`

When `WORKFLOW_ANALYTICS_URL` is set, POST one JSON object per event.

| Env | Role |
|-----|------|
| `WORKFLOW_ANALYTICS_URL` | HTTPS collector. Unset means local JSONL only. |
| `WORKFLOW_ANALYTICS_TOKEN` | Optional `Authorization: Bearer` token. |
| `WORKFLOW_ANALYTICS_SESSION_ID` | `session_id` when the caller does not pass one. |
| `WORKFLOW_ANALYTICS_REPO` | `repo` (canonical URL or `owner/name`). |
| `WORKFLOW_ANALYTICS_HOST_KIND` / `WORKFLOW_ANALYTICS_HOST_DETAIL` | Test override of host detection. |

Request: `Content-Type: application/json`, `User-Agent: workflow-plugin-analytics-lab/1`. Collector success is **2xx** (`204`, or `200` with `{"ok": true}`). The lab mock answers **204** and records whether `Authorization` was present.

On network error, timeout, 4xx, or 5xx the helper returns a detail string and the caller still succeeds. Hook commands **exit 0**. Driver callers keep the exit code they already had.

| Failure | `_remote_detail` | Workflow |
|---------|------------------|----------|
| Egress allow-list or DNS | `url_error:…` | Local row kept |
| TLS / MITM | `url_error:…` | Local row kept |
| Collector 401 / 403 | `http_error:401` (and the same shape for 403) | Fix the token; workflow continues |
| Payload too large | Collector **413** | Client drops that POST; workflow continues |
| Restricted egress (`egress.restricted: true`) | External POSTs fail | Trailers remain. Export the run record before the VM ends, or allow-list the collector origin. There is no in-repo bypass. |

### 3. Envelope v1

Contract: [`EVENT-SCHEMA.md`](../RESEARCH/2026-09-30-durable-analytics-sink/EVENT-SCHEMA.md), implemented by `build_envelope` in [`dual_write_sink.py`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py). `schema_version` is **1**. Collectors accept unknown fields.

| Field | Required | Rule |
|-------|----------|------|
| `schema_version` | yes | Integer `1` |
| `event_id` | yes | UUID v4; collector dedupes on it |
| `ts` | yes | ISO-8601 UTC |
| `host_kind` | yes | `local` \| `cloud` \| `opencode` |
| `host_detail` | no | `cursor-cloud`, `claude-code-remote`, `claude-code`, `desktop`, `opencode` |
| `session_id` | no | Harness session or cloud `bcId` |
| `repo` | no | From `WORKFLOW_ANALYTICS_REPO` |
| `plan` | no | Plan folder, trailing slash stripped |
| `slug` | no | Design slug |
| `phase` | no | int, or `wrap-up` / `done` |
| `kind` | yes | Namespaced string from the table above |
| `source` | no | Emitter module path |
| `payload` | yes | Family body; may be `{}` |

Host detection order in the helper:

| Condition | `host_kind` | `host_detail` |
|-----------|-------------|---------------|
| `WORKFLOW_ANALYTICS_HOST_KIND` set | that value | `WORKFLOW_ANALYTICS_HOST_DETAIL` |
| `WORKFLOW_INSTALL_MODE=opencode` | `opencode` | `opencode` |
| `CURSOR_AGENT=1` | `cloud` | `cursor-cloud` |
| `CLAUDE_CODE_REMOTE=true` | `cloud` | `claude-code-remote` |
| `CLAUDECODE` set | `local` | `claude-code` |
| else | `local` | `desktop` |

Remote `payload` stays small: soft cap **32 KiB** per POST, collector hard reject **256 KiB**. Assert payloads carry `question_id`, `state_hash`, `pass`, `jev`, and `usage`. They omit `closing_record.body` and transcript paths. The POST never includes `TYPESAFE_API_KEY`, `ANTHROPIC_API_KEY`, or `CURSOR_API_KEY`.

Existing Jev rows may be ingested as legacy (`schema_version: 0`) or wrapped. The lab proof wraps: envelope fields plus `payload` equal to the legacy row minus duplicated `ts` and `kind`. New remote writes use the wrap. Local files stay legacy-shaped.

### 4. Cloud HTTPS when egress is unrestricted

The checked-in probe POSTed `harness.egress_probe` to `https://httpbin.org/post` and received **200** with the envelope echoed back (`host_kind: cloud`, `host_detail: cursor-cloud`). That is the evidence that a cloud agent with `egress.restricted: false` can reach a public HTTPS collector. Teams that restrict egress allow-list the collector origin before they set `WORKFLOW_ANALYTICS_URL`.

### 5. One emitter path — collector behind the URL

Candidate **B** (remote HTTP append) is the remote guidance. Candidate **D** (webhook to a bot-owned collector) is the same POST with a different operator. Object storage (candidate **C**) is a backend the collector may use. The agent does not PUT objects and does not hold storage credentials. There is no second emitter path.

The collector dedupes on `event_id`, returns 413 when a body is too large, and chooses retention. Deploying that process is ops outside this repository.

### 6. Git and PR stay low-rate checkpoints

`Workflow-Phase:` trailers remain the authoritative phase checkpoint for resume. A short run-record summary in a PR description can sit beside them. Hook-scale rows (PostToolBatch, per-trigger JSONL) stay off git history and off PR comments. Those channels are durable and they are the wrong volume.

## Guidance, skills, and invariants

| Layer | Becomes | Stays out |
|-------|---------|-----------|
| **Invariants** | Rules below. Product wiring preserves them. | They are not retuned in a later study. |
| **Guidance** | This proposal, [`DUAL-WRITE-RECIPE.md`](../RESEARCH/2026-09-30-durable-analytics-sink/DUAL-WRITE-RECIPE.md), [`EVENT-SCHEMA.md`](../RESEARCH/2026-09-30-durable-analytics-sink/EVENT-SCHEMA.md), [`SINK-CANDIDATES.md`](../RESEARCH/2026-09-30-durable-analytics-sink/SINK-CANDIDATES.md), and [`dual_write_sink.py`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py) as the lab contract. | Not default plugin settings. Not imported by `tools/driver/` yet. |
| **Skills** | No skill change. Core skills (`design`, `refine`, `execute`, `comprehensive-review`, `close-out`, `post-build`) and lab skills (`setup`, `iterate`, `transcript-parser`, `workflow-tuning`, `lab-proposal`) do not call the sink and do not wait on it. | No new skill. The helper is driver and hook code when implementation lands. |

Invariants this resolution locks:

1. Soft signals stay advisory. A Jev score or a sink row does not change a phase exit, a merge, or an assert result.
2. `python3 tools/driver/assert_phase.py --deterministic` stays the kill line. Exit 0 pass, exit 2 fail, `decision_source: deterministic`.
3. Classify stays a visualisation POC. `.classify-log.jsonl` is not an envelope family.
4. Remote failure leaves the workflow exit code unchanged. `post_remote` does not raise.
5. Local JSONL on the paths above stays the on-VM record, in the existing row shape. The envelope is the remote body.
6. `Workflow-Phase:` trailers stay the low-rate git checkpoint. High-volume rows stay out of commits and PR comments.
7. Core skills do not depend on a collector. Unset `WORKFLOW_ANALYTICS_URL` is local-only success (`skipped:no_url`).
8. Logs stay outside the plan folder (architecture invariant: nothing in the repo carries status). Paths remain gitignored.

## Economics

The loss on a cloud run is the run record, the assert slice, and any soft-signal rows that never left the VM. Rebuilding them means transcripts or a re-run. The dual-write cost is the local append the emitters already pay, plus one optional HTTPS POST with a 10-second timeout that is dropped on failure.

A git or PR side-channel would spend commit latency and history on hook-scale volume. A direct object-storage client would put storage credentials on every agent and add a presign round trip. One POST to a collector the operator already runs avoids both. The collector can batch to object storage on its side.

Skipping the remote URL is free: local files and trailers behave as they do on `1bff769`.

## Non-goals

- **Default wiring.** `install.sh`, Claude settings, `run.py`, `assert_phase.py`, and the Jev probes do not gain a sink call in this resolution.
- **A sink kill line.** Remote failure is not a phase failure and is not an assert failure.
- **Classify as a KPI.** Classify labels do not score this paper and are not ingested by the default contract.
- **Replacing `assert_phase --deterministic`.** Phase pass/fail stays mechanical.
- **Promoting soft signals to gates.** The cheap-Jev resolution still applies: log and surface; the worker loop stays unblocked.
- **Git or PR comments as the telemetry bus.**
- **An agent-side object-storage emitter.**
- **A collector implementation in this repo.** Token, retention, dedupe store, and object storage are ops.
- **Rewriting local JSONL into envelope shape.** Local rows stay legacy until a later implementation chooses otherwise. This resolution keeps them legacy.

## Measurement

Weekly skim continues to read the local JSONL files ([cheap-Jev recipe](../RESEARCH/2026-09-30-jev-cheap-judgement-signals/proofs/validated/weekly_skim_recipe.sh)). The collector is an extra copy for hosts that will not keep the disk. Classify output is not an input.

| Measure | Definition | Reading |
|---------|------------|---------|
| Local durability | One new legacy line per emit on the family path, including when `_remote_detail` is not `http:2xx` | Holds for every accepted family |
| Remote acceptance | Share of envelopes with `_remote_detail` `http:2xx` while `WORKFLOW_ANALYTICS_URL` is set | Collector health |
| Sink-caused stops | Exits that change because the POST failed | Stay at **zero** |
| Classify in the collector | Envelopes whose `kind` or `source` is the classify log | Stay at **zero** |
| Kill line | `assert_phase --deterministic` on the existing fixtures | Unchanged exit codes |
| Cross-run recall | A later session reads `driver.trigger`, `driver.assert`, or `jev.*` for a finished cloud `session_id` | The remote exists for this |
| Payload hygiene | Remote bodies containing `closing_record.body` or API key material | Stay at **zero** |
| Dedupe | Collector stores one row per `event_id` | Re-posts collapse |

## Accepted outcomes

| Artifact | Becomes |
|----------|---------|
| Local paths `.run-record.jsonl`, `.assert-log.jsonl`, `.jev-signal-log.jsonl` | Invariant. Always written, legacy shape. |
| [`EVENT-SCHEMA.md`](../RESEARCH/2026-09-30-durable-analytics-sink/EVENT-SCHEMA.md) | Contract for envelope v1 and `kind` names. |
| [`dual_write_sink.py`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/dual_write_sink.py) | Lab contract (`emit_event`, `emit_from_jev_signal_row`, `post_remote`). Implementation imports this behaviour. |
| [`DUAL-WRITE-RECIPE.md`](../RESEARCH/2026-09-30-durable-analytics-sink/DUAL-WRITE-RECIPE.md) | Ops guidance. Opt-in env vars. |
| [`egress_cloud_result.json`](../RESEARCH/2026-09-30-durable-analytics-sink/proofs/validated/egress_cloud_result.json) | Closed evidence: unrestricted cloud egress can HTTPS POST. |
| Bot-owned collector, object storage | Ops behind `WORKFLOW_ANALYTICS_URL`. One emitter path. |
| Git trailers | Low-rate checkpoint. Unchanged. |
| `classify.py` | Stays a POC chart. |
| `assert_phase.py --deterministic` | Stays the kill line. |
| Core and lab `SKILL.md` files | Unchanged. |

## Product wiring

Implementation, not research. None of this is in the default driver or plugin settings on `1bff769`. Collector deployment stays outside the repo.

1. Share one helper, the behaviour of `dual_write_sink.py`, among the assert log, the Jev signal probes, and the driver run record. Keep `build_envelope` field rules and the 10-second POST timeout. Do not retune them from a new study.
2. Run record: keep `append_record` as the local write. When `WORKFLOW_ANALYTICS_URL` is set, POST `driver.trigger` or `driver.assert`. Pass `local_path` only when this call is the writer, so the legacy line is appended once.
3. Assert log: after the existing `.assert-log.jsonl` append, POST `assert.live` with hash, pass, Jev audit, and usage. Omit the closing-record body.
4. Jev probes: after the existing `.jev-signal-log.jsonl` append, post the envelope without a second local append. Use `emit_from_jev_signal_row` for `post_tool_batch` and `subagent_stop`. Emit `jev.shadow` by that schema `kind` (see the table above). The hook command still exits 0.
5. Leave `classify.py`, `evaluate_assert()`, and `decision_source` unchanged.
6. Leave `WORKFLOW_ANALYTICS_URL` unset in `install.sh`, default Claude settings, and the driver default. Setting the URL is an operator opt-in.
7. Run the collector as a separate service: HTTPS, optional bearer token, dedupe on `event_id`, 413 over the size cap, object storage only inside that service.
