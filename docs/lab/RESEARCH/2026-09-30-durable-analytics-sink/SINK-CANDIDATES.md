# Sink candidates — comparison

Evaluation lens: **workflow remit** (driver + asserts + soft signals), **cloud VM ephemerality**, **opt-in**, **no workflow blocking on sink failure**, **no classify KPI**.

| Candidate | Durability | Volume | PII risk | Latency | Auth | Evidence in pack |
|-----------|------------|--------|----------|---------|------|------------------|
| **A. Local JSONL** | Per machine / workspace until deleted | Unbounded on disk | Closing-record excerpts in assert state if mirrored; signal log mostly counters | Sync append | File permissions | Baseline; all current emitters |
| **B. Remote HTTP append** | Collector-owned | Bounded by POST size + rate | Payload must be redacted at source | Async-friendly | `WORKFLOW_ANALYTICS_URL` + optional `WORKFLOW_ANALYTICS_TOKEN` (Bearer) | [`proofs/run_proofs.sh`](proofs/run_proofs.sh), mock server |
| **C. Object storage (S3/GCS) presigned PUT** | Collector-owned | Large blobs possible | Same as B | Extra round-trip for presign | Presign URL or sidecar | **Design only** — HTTP prove sufficient for pattern |
| **D. Webhook to bot-owned collector** | Same as B | Same | Same | Same | Shared secret header | Alias of B with fixed collector contract |
| **E. Git / PR side-channel** | Durable in forge | **Poor** for high-frequency hooks | Commits expose content | Minutes; noisy | Git credentials | Trailers only at low rate |
| **F. PR trailers / comments** | Durable | Very low | Medium (human text) | Human-scale | GitHub API | Complements git trailers; not a telemetry bus |

## A. Local JSONL (baseline)

**Pros:** Zero egress; matches today's driver and lab hooks; trivial `jq` skim (see Jev weekly recipe).  
**Cons:** Useless as cross-run analytics for Cursor Cloud after VM teardown unless the user downloads artifacts.

**Verdict:** **Always write locally** in dual-write guidance.

## B. Remote HTTP append (recommended lab default)

**Contract:** `POST` body = one JSON object (envelope) per event; `Content-Type: application/json`; optional `Authorization: Bearer <token>`. Collector returns `2xx`; client **ignores failures** for workflow exit codes.

**Pros:** Works from cloud when egress allows HTTPS; collector can batch to object storage; schema versioning in envelope.  
**Cons:** Requires operator-run collector; secrets via env; must cap payload size and redact transcripts.

**Verdict:** **Default remote guidance** for lab/opt-in (`WORKFLOW_ANALYTICS_URL`). Proven with local mock + live cloud POST in this pack.

## C. Object storage direct

**Pros:** Cheap at rest; good for large attachments.  
**Cons:** SDK/credentials on agent VM; harder to make append-only without a collector; more moving parts than B.

**Verdict:** Defer; collector behind B can land to object storage without agent credentials.

## D. Webhook to bot-owned collector

Same implementation as B. Grok Bot or a small service owns validation, dedup by `event_id`, and retention policy.

## E. Git / PR side-channel

**Pros:** Trailers already durable; PR merge is the outcome record.  
**Cons:** PostToolBatch-scale events would pollute history; PII in commits; hook latency unacceptable.

**Verdict:** Keep **trailers + run record summary in PR description** for outcomes; **not** for soft-signal streams.

## F. Classify log as sink

Explicitly **out of scope** per remit (visualization POC only).

## Recommendation (lab)

1. **Dual-write:** local JSONL (existing paths per event family) + optional **HTTP append** when `WORKFLOW_ANALYTICS_URL` is set.  
2. **Unify envelope** across families (`EVENT-SCHEMA.md`) so one collector ingests driver, assert, and Jev rows.  
3. Proposal [`../../PROPOSALS/2026-09-30-durable-analytics-sink.md`](../../PROPOSALS/2026-09-30-durable-analytics-sink.md) is `status: resolved`. Default hooks and the driver stay unwired; the implementation task opts in via `WORKFLOW_ANALYTICS_URL`.
