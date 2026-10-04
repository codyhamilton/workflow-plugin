---
brief_id: 212
design_id: 209
---

# Brief: 1-03 — Ingest, precheck and `workflow serve`

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its output closes phase 1; the
orchestrator verifies the phase outcome against it. Phase 2's drain sends the fact shape defined
here and calls `Ingest` in process; phase 3 replaces the screen step; phase 4 adds advisory reads.
Owned paths: `tools/workflow/internal/ingest/`, `tools/workflow/internal/serve/`,
`tools/workflow/cmd/workflow/`, `tools/workflow/go.mod`, `tools/workflow/go.sum`,
`docs/plans/09-workflow-binary/reports/1-03-ingest-serve.md`. Touch nothing else.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 1-01 and 1-02.
Runs alongside: nothing.
Budget: 8 files to read, about 1,100 lines to write including tests, 70 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 1 outcome (lines 141-153). This is what the
   orchestrator will check.
2. `docs/design/03-remote-service.md` — Runtime, Local and remote, Configuration (lines 15-63), API,
   Ingest, Deterministic precheck (lines 65-107), Screening and scoring (lines 147-177), Tests 1-2
   (lines 208-211). Binding.
3. `docs/design/01-event-model-and-ingest.md` — Facts (lines 17-26), Ingest contract (lines 120-127),
   Decision 4 (lines 148-151). Binding.
4. `docs/design/02-edge-capture.md` — Delivery (lines 89-107): how the drain reads each status.
5. `docs/design/04-advisory-surface.md` — API, `/v1/artifacts` row (lines 56-58). Binding shape.
6. `go doc` of `./internal/keys`, `./internal/secrets`, `./internal/store` — the APIs you build on.
7. `docs/plans/09-workflow-binary/reports/1-01-module-keys-secrets.md` and `reports/1-02-store.md` —
   departures from their briefs.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Make the phase 1 outcome true: `workflow serve` authenticates per tenant, prechecks every fact
before anything touches disk, stores accepted facts through the tenant writer, sends artifact
content through `pending/` and promotes it as `unscreened`, and answers `GET /v1/artifacts` scoped to
the key's tenant.

## Contract

Cited, settled: design 3 Configuration (env variables, "refuses to start without" keys, "A key maps
to exactly one tenant", "compared in constant time and never logged", "Local mode still requires a
key"); design 3 API table and Ingest (request `{"facts": [...]}`, response `{"results": [{"id",
"status", "reason"}]}` in order, per-fact `rejected`, `400`/`401`/`413` (16 MB)/`5xx`); design 3
precheck ("before anything touches disk", "reason names the pattern and line, never the matched
text", a rejection record keeps "fact type, conversation, path, content hash, pattern name", not
the content); design 3 Screening "No `TYPESAFE_API_KEY`: the screen verdict is `unscreened`";
design 4 `/v1/artifacts` response shape, 404 when absent; design 1 decision 4 (every fact has a
conversation ID).

Decisions made at refine (settled; phase 2 builds the drain against them):

- **Fact wire shape.** A JSON object. Common keys: `id` (the drain's `<queue file>#<n>`, echoed in
  the result, never hashed or stored), `type` (`hook_event` | `artifact_version` | `commit`),
  `conversation_id`, `harness`, `event`, `ts` (number, Unix seconds). `hook_event` adds `payload`
  (object, already scrubbed by the client). `artifact_version` adds `repo_id`, `path`,
  `content_hash`, `content` (string, the file's UTF-8 bytes), `source` (`worktree` | `commit`).
  `commit` adds `repo_id`, `sha`, `paths` (array of strings) and `renames` (array of
  `{"from","to"}`). Column names follow design 3 Tables and design 4's JSON. Unknown keys are kept
  in `raw` (design 3 API). Define these as Go types in `internal/ingest`, documented in the package
  doc comment.
- **Per-fact validation** rejects (status `rejected`, reason prefixed `invalid:`): not an object,
  unknown `type`, empty `conversation_id`; `artifact_version` without `repo_id`, `path`,
  `content_hash` or `content`, or whose `content_hash` is not `keys.ContentHash(content)`; `commit`
  without `repo_id` or `sha`.
- **Order per fact:** validate → precheck every string in the fact (all leaves, recursively,
  including `content`) with `secrets.Scan` → row hash (`keys.RowHash`) → for `artifact_version`,
  `WritePending` unless the blob exists. Then one `Append` for the batch's accepted rows; the
  `inserted` flags give `accepted` or `duplicate`.
- **Precheck reason:** `precheck: <pattern> at line <n>` for `content`, `precheck: <pattern> in
  <json.path> line <n>` for other fields; first hit only. Record it with `AppendRejection`
  (stage `precheck`). The fact itself is not stored.
- **Resend reading of the phase outcome.** "resending returns all `duplicate`" applies to the facts
  that were accepted. A resent secret-bearing fact is prechecked again and is `rejected` again,
  because `duplicate` tells the drain the file was delivered (design 2 Delivery) and the precheck
  runs before anything touches disk.
- **Auth:** `Authorization: Bearer <key>` (the header the legacy drain sends). Compare against
  every configured key with `crypto/subtle`, no early exit. `401` with `{"error":"unauthorized"}`.
  Never log a key or the header.
- **Keys env:** `WORKFLOW_SERVE_KEYS=tenant=key[,…]`; tenant names `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`;
  an empty value, a malformed pair, or one key given to two tenants refuses to start with a message
  that names the problem, not the key.
- **Defaults:** `WORKFLOW_SERVE_ADDR` `127.0.0.1:8770`; `WORKFLOW_SERVE_DATA`
  `~/.local/share/workflow/serve`. Tenant `T` lives in `<data>/T/` via `store.Open`, opened lazily
  and kept open. Do not read `TYPESAFE_API_KEY` in this phase.
- **Pending worker:** one goroutine per open tenant, woken by ingest and by a poll of a few seconds,
  takes `PendingHashes()` in order and applies one screen step held as a single function value on
  the server. This phase's step is `Promote(hash, Screen{Verdict: "unscreened"})`. Phase 3 replaces
  only that function value. A server option disables the worker so tests can observe `pending/`.
  On tenant open, leftover `pending/` files are processed.
- **Health:** `GET /v1/health`, no auth, `{"ok":true,"version":"…","pending":<total across open
  tenants>}`.
- **In-process entry:** `ingest` exposes the same function the handler calls,
  `Ingest(ctx, tenant *store.Tenant, facts []json.RawMessage) ([]Result, error)` (an error means a
  whole-request failure, answered `5xx`), so phase 2's hosted drain can call it.
- **cmd:** `workflow serve` runs the server; `drain`, `mcp`, `status` print `not implemented yet`
  and exit 2; anything else prints usage and exits 2. `version` and `commit` are `main` package
  variables (default `dev`, `unknown`) settable by `-ldflags -X`. SIGINT/SIGTERM shut down
  gracefully: stop HTTP, finish queued writes, close tenants.

## Changes

`internal/ingest`: fact types, validation, precheck, `Ingest`. `internal/serve`: config from env,
auth, tenant registry, pending worker, handlers for `/v1/health`, `/v1/ingest`
(`http.MaxBytesReader` at 16 MB → `413`; body not `{"facts":[…]}` → `400`; empty list → `200` with
empty results), `/v1/artifacts?repo_id=&path=` (missing parameter → `400`; `kind` from `keys.Kind`;
times RFC 3339; `screen` null until promoted; `scores` `[]`), wrong method → `405`. All responses
`application/json`. `cmd/workflow`: `main.go` dispatch.

### Keep untouched

`internal/keys`, `internal/secrets`, `internal/store`: build on their APIs. If one is wrong or
missing something, report it rather than editing it, unless the fix is a one-line bug, which you
name in the report. No `/v1/checks`, `/v1/baselines`, `/v1/search` (phase 4), no scorer (phase 3),
no drain (phase 2).

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test ./...` → passes, including 1-02's `writer-burst` line (quote it).
- `go test -run 'Ingest|Precheck' -v ./internal/ingest` → a batch of hook_event, artifact_version,
  commit and one secret-bearing fact returns four results in order, only the secret one `rejected`,
  reason naming the pattern and line and not containing the secret; a resend gives `duplicate` for
  the three and `rejected` for the fourth; each `invalid:` case above is rejected per fact without
  affecting its batch.
- `go test -run 'Pending' -v ./internal/serve` → with the worker disabled, the artifact's bytes are
  in `pending/<hash>` and not in `blobs/`; after enabling it, `blobs/<aa>/<hash>` exists, `pending/`
  is empty and `/v1/artifacts` shows `"screen":{"verdict":"unscreened",…}`.
- `go test -run TestServeOutcome -v ./cmd/workflow` → builds the binary into `t.TempDir()`, starts
  it with `HOME`, `WORKFLOW_SERVE_DATA` and a free `WORKFLOW_SERVE_ADDR` in that temp dir and
  `WORKFLOW_SERVE_KEYS=a=ka,b=kb`, then over HTTP: the ingest sequence above; `GET /v1/artifacts`
  with `ka` returns the artifact with verdict `unscreened` (poll briefly); with `kb` → `404`; no key
  and a wrong key → `401`; no file under the data dir and nothing in the server's stderr contains the
  secret; a start with `WORKFLOW_SERVE_KEYS` unset exits non-zero.

Build test secrets by string concatenation at runtime so no committed source line is a
credential-shaped literal. The 1-01 test `TestRepoDocsClean` must still pass.

Safety: test only in temp dirs (`t.TempDir()` or `mktemp -d`), and always set `HOME` and
`WORKFLOW_SERVE_DATA` to temp paths when starting the binary. Never read or write
`~/.local/share/workflow*`, the live queue, or the legacy service on 8765. Never print or log
`TYPESAFE_API_KEY` or any key. Leave no server process running.

Commit: title `[exec <execution_id>] Phase 1: ingest, precheck and workflow serve` (the
orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/1-03-ingest-serve.md` (design 1, Execution report: what was
done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable) and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
