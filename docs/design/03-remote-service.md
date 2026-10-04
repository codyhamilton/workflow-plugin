# Design Intent 3: Remote Service

The service that accepts facts from the drain, holds them, screens and scores content, and answers
the advisory shim. Part of [system-architecture.md](system-architecture.md); accepts the envelope
types in [01-event-model-and-ingest.md](01-event-model-and-ingest.md) from the drain in
[02-edge-capture.md](02-edge-capture.md).

## Problem

The current service (`tools/quality/server.py`) is a Python process tied to the agent-facing MCP
tools that are being retired, with session and lifecycle state the event model no longer has. The
replacement must run the same way on a laptop and on a server, cost as little as possible while
idle, and take a write-heavy, bursty stream without the hooks ever waiting on it.

## Runtime

One Go binary, `workflow`, with subcommands:

| Subcommand | Role | Design |
|---|---|---|
| `workflow serve` | this service, local or remote | 3 |
| `workflow drain` | the drain | 2 |
| `workflow mcp` | the stdio advisory shim | 2, 4 |
| `workflow status` | queue and drain state | 2 |

- Targets: linux and darwin, amd64 and arm64. WSL is linux. No Windows-native build.
- No cgo. SQLite is the pure-Go `modernc.org/sqlite`, so all four targets cross-compile from one
  machine and the binary is static.
- HTTP is `net/http` from the standard library. No framework, no ORM.
- Go was chosen over Python, Node and Rust for idle footprint, a static binary with nothing to
  install on the host, and one implementation for client and server. The cost is a build and
  release step, owned by [design 5](05-distribution.md).

Only `spool.sh` stays bash, because a hook must not pay a process start beyond `bash`.

## Local and remote

The same binary and code path in both. Differences are configuration only.

| | Local | Remote |
|---|---|---|
| Bind | `127.0.0.1:8770` | as configured, behind a TLS proxy |
| Data | `~/.local/share/workflow/serve` | as configured |
| Tenants | one | many |
| Drain | hosted in-process (below) | none; clients run their own |

Port 8770 avoids the legacy Python service's 8765 while both exist.

### Configuration (first round)

Server configuration is environment only:

| Variable | Meaning |
|---|---|
| `WORKFLOW_SERVE_ADDR` | listen address, default `127.0.0.1:8770` |
| `WORKFLOW_SERVE_DATA` | data directory |
| `WORKFLOW_SERVE_KEYS` | `tenant=key[,tenant=key…]`; unset or empty means keyless local mode |
| `TYPESAFE_API_KEY` | scorer credential; server side only, never in any client config |

Registration, key issue and rotation are out of scope. A key maps to exactly one tenant; the client
never names its tenant. Keys are compared in constant time and never logged.

**Local mode** is the keyless case, for one user on one machine:

- Every request maps to tenant `local`, and any key sent is ignored.
- The bind must be loopback; the service refuses to start keyless on any other address.
- Browser guards: the `Host` header must be a loopback name (stops DNS rebinding), and a POST must
  be `Content-Type: application/json` (a cross-origin form cannot send it without a preflight).

A keyed service sent no key answers 401 saying a key is required (`workflow login`).

## API

Versioned by path prefix. Within `/v1`, changes are additive only: new optional fields, new
endpoints. Unknown fields in a fact are kept in its raw payload, never rejected.

| Method and path | Auth | Purpose |
|---|---|---|
| `GET /v1/health` | none | liveness, version |
| `POST /v1/ingest` | key | a batch of facts from a drain |
| advisory reads (`/v1/artifacts`, `/v1/checks`, `/v1/baselines`, `/v1/search`) | key | defined by [design 4](04-advisory-surface.md#api) |

### Ingest

Request: `{"facts": [fact, …]}`, each fact one design 1 envelope (`hook_event`,
`artifact_version`, `commit`) carrying the drain's `id` for that fact (`<queue file name>#<n>`,
design 2 Delivery).

Response: `200` with one result per fact, in order:

```json
{"results": [{"id": "…", "status": "accepted" | "duplicate" | "rejected", "reason": "…"}]}
```

- `accepted` and `duplicate` mean delivered: the drain deletes the file.
- `rejected` is per fact: the drain moves that file only to `rejected/` with the reason. One bad
  fact never rejects its batch.
- Whole-request errors: `400` for a body that is not a facts batch, `401` for a bad key, `413` above
  the size limit (16 MB), `429` with `Retry-After`, `5xx` for retry. The drain splits on `400` and
  `413` (design 2), so a whole batch is never rejected for one file.

The row hash is computed from the envelope alone (design 1), so a resent batch is all `duplicate`.

### Deterministic precheck

On arrival, before anything touches disk, every fact's text fields and artifact content are matched
against a fixed pattern set: the client scrub's patterns plus provider key formats, JWTs,
connection strings with inline passwords, and `.env`-style assignments to names ending `KEY`,
`SECRET`, `TOKEN` or `PASSWORD`.

- A hit rejects the fact. The reason names the pattern and line, never the matched text.
- A record that a rejection happened (fact type, conversation, path, content hash, pattern name)
  is kept. The content is not.
- The rejection reaches the agent through the shim (design 2); the rewrite is the repair.

## Storage

One directory per tenant: `<data>/<tenant>/`.

- `ledger.db`: SQLite in WAL mode, `synchronous=NORMAL`.
- `blobs/<aa>/<hash>`: content stored by SHA-256, written once. Rows hold the hash, never the bytes.
- `pending/<hash>`: content awaiting the screen (below).

Per-tenant files mean writes for different tenants never share a lock, and deleting a tenant is
deleting a directory.

### Writer

Each open tenant has one writer goroutine. Ingest requests hand their facts to it and wait. The
writer takes everything queued within a few milliseconds into one transaction (group commit), and
each request is answered after its commit. There are no concurrent writers, so no `SQLITE_BUSY`.
Readers use separate connections and run alongside under WAL.

### Tables

Ingest is append-only (principle 6): `INSERT OR IGNORE` keyed by row hash, never `UPDATE` on facts.

| Table | Holds |
|---|---|
| `facts` | row hash, type, conversation ID, harness, event, ts, received at, repo ID, path, content hash, raw envelope JSON |
| `rejections` | the precheck and screen rejections described above |
| `screens` | content hash, verdict, scorer, at |
| `scores` | content hash, check, result, scorer, at |

Derived views (execution, gaps, moves) are built by a reader into separate tables and never on the
ingest path. Their definition belongs to design 4 and the lab.

### Behind an interface

`Store` exposes appending facts and the reads the API needs. SQLite is its only implementation.
Postgres replaces it if the service ever needs more than one app host; until then backups of a
remote are file copies of the tenant directory (Litestream later).

## Screening and scoring

Jev, through TypeSafe System One, is the last secret check before content is persisted (design 1,
decision 6), and the artifact scorer.

- Artifact content that passes the precheck is written to `pending/`, and its fact is stored with
  the content hash. The ingest reply does not wait for Jev.
- A worker per tenant takes pending content in arrival order and asks the scorer to screen it and,
  for artifact kinds with checks, score it.
  - Pass: the content moves to `blobs/`; a `screens` row and any `scores` rows are written.
  - Flag: the pending content is deleted; a `rejections` row records the hash and reason. The fact
    stays, with no content behind it.
  - Scorer unreachable: the content stays pending and the worker backs off. Pending count shows in
    `health`.
- Sending content to Jev for the screen means a secret the precheck missed does reach TypeSafe in
  that request. Jev is the last check before persistence, not before transmission (principle 9).
- No `TYPESAFE_API_KEY`: the screen verdict is `unscreened` and content moves to `blobs/` after
  the precheck alone. This is the expected local mode without a scorer, and the verdict says so in
  every read.
- The scorer sits behind a `Scorer` interface (`Screen`, `Score`). The model behind Jev is not part
  of any contract here.

The Jev implementation makes one System One request per content hash (`POST
https://api.typesafe.ai/v1/systemone`, as `tools/transcript/lib/jev_client.py` does today): the
kind's checks as `score` questions, plus one screen question asking whether the text contains a
credential. A screen score at or above its flag level is a flag.

Checks are the existing check definitions (`tools/quality/criteria.json` plus
`tools/quality/checks/*.json`), loaded from files at start; the execution report kind takes the
candidate checks in design 1. Rubric wording for the
execution report is defined once and shared with the skill (design 1).

## Local serve hosts the drain

In local mode `workflow serve` also drains the user's queue, as a long-lived drain.

- It takes `queue/.drain.lock` and holds it while running, so hooks find the lock held and start
  nothing.
- No hook kicks it, so it watches the queue directory (inotify on Linux, kqueue on macOS) with a
  slow poll as a fallback. The design 2 batch window still applies.
- It runs the same drain module as `workflow drain`, with an in-process sink in place of HTTP. The
  sink calls the same ingest function as the handler, so the precheck and screening apply. In
  process never means unchecked.
- It drains only when the client config's endpoint is this server (same host and port). Otherwise
  the queue is addressed elsewhere and it leaves it alone. Its tenant is the one the client config's
  key maps to.
- If it stops, the lock is released, the next hook starts a standalone drain, and that drain posts
  to the endpoint with backoff until `serve` returns.

This amends principle 8: the drain never starts or manages the service; the drain and ingest are
separated by a module boundary, not a process boundary, and a local service may host the drain.

## The legacy service

`tools/quality/server.py` and its ledger stay as they are, unmigrated and readable by the lab. The
agent-facing MCP tools it serves are retired by design 4. Nothing in this design writes to it.

## Tests

Cheap, in temp directories, never the live queue or data.

1. Ingest: a batch with one secret-bearing fact returns per-fact results; only that fact is
   rejected, with a reason that does not contain the secret; a resend is all `duplicate`.
2. Auth: no key, wrong key, and a key for tenant B never see tenant A's artifacts.
3. Writer: replay N tenants each sending bursts of about 20 facts; record p99 commit latency and
   database size with content stored by hash.
4. Screening: scorer pass, flag and unreachable each leave the stated state; no key gives
   `unscreened`.
5. Local hosting: while `serve` holds the lock, 20 concurrent spools start no drain; kill `serve`
   and a standalone drain delivers the rest; with the endpoint pointing elsewhere `serve` leaves the
   queue alone.
6. Idle footprint: RSS and cold start of `workflow serve` and `workflow mcp`.
