---
design_id: 209
---

# Workflow binary: capture, service and advisory shim

## Intent

User request, verbatim:

> Ok for now keep registration out of scope because this is a little more involved. We just will set tenant and key by env for first round. Write design then kick off executions for what we have designed so far. Also use your judgement for remaining phases of what we have discussed and design/execute that too.
>
> Don't stop or ask, I'll be returning in the morning and can review and redirect then. Make all the changes on this branch

## Problem

Capture today is a Python drain that posts to a Python service whose agent-facing tools ask the
agent to report state, which is what the architecture removes. Designs 1 to 5 in `docs/design/`
fix the replacement: hooks spool, one drain per user delivers facts, a service that runs the same
locally and remotely holds them, screens and scores content, and a local stdio shim answers the
agent. None of it is built.

## Solution Shape

After this change, one Go binary `workflow` (built from `tools/workflow/`, reached through
`bin/workflow`) provides `serve`, `drain`, `mcp` and `status`. Every harness spools hook events with
a literal harness name into one queue per user; the drain (or a local `serve`) turns them into
`hook_event`, `artifact_version` and `commit` facts and delivers them; the service stores them per
tenant, screens and scores artifact content through Jev, and answers three read-only advisory tools.
The skills stop requiring the agent to post or log anything.

The binding contracts are the design-intent docs. This design cites them and adds no contract of
its own.

### Domain: Service (`workflow serve`)

- Owns: the tenant data directories, the `/v1` API, the precheck, screening and scoring.
- Contract: [03-remote-service.md](../../design/03-remote-service.md) — Runtime, Local and remote,
  Configuration, API (Ingest, Deterministic precheck), Storage (Writer, Tables, Behind an
  interface), Screening and scoring, Local serve hosts the drain.
- Non-goals: registration, key issue, Postgres, Litestream, derived execution views beyond what
  the advisory reads need.

### Domain: Capture (`spool.sh`, `workflow drain`, `workflow status`)

- Owns: the queue directory, `rejected/`, the drain lock, the client config file.
- Contract: [02-edge-capture.md](../../design/02-edge-capture.md) — Spool, Drain (all
  subsections), Config, Write surfaces; fact shapes and keys from
  [01-event-model-and-ingest.md](../../design/01-event-model-and-ingest.md) — Facts, Keys, Ingest
  contract.
- Non-goals: the legacy service, local archives, a queue cap.

### Domain: Advisory (`workflow mcp`)

- Owns: the stdio MCP and its three tools.
- Contract: [04-advisory-surface.md](../../design/04-advisory-surface.md) — Shape,
  `artifact_feedback`, Scores and baselines, Unreachable service.
- Non-goals: any write tool; maintainer operations.

### Domain: Distribution and cutover

- Owns: `bin/`, `tools/release/`, the per-harness hook and MCP configs, the skill text that names
  retired tools.
- Contract: [05-distribution.md](../../design/05-distribution.md) — Layout, Wrapper, Release,
  Per-harness configs, Retired; [04-advisory-surface.md](../../design/04-advisory-surface.md) —
  What changes in the skills.
- Non-goals: publishing a release, the monorepo reorganisation, pinned plugin copies.

## Architectural Implications

- Principle 8 is amended (design 3): the drain and ingest are separated by a module boundary, and a
  local `serve` may host the drain.
- The legacy Python service and its ledger stay running and unmigrated; nothing writes to it once
  the configs are cut over in phase 5. Skills change in phase 6.
- Until a release is published, the wrapper builds from source, so a Go toolchain is needed on
  machines that run the new hooks.

## Decisions

- Go over Python, Node and Rust (conversation, recorded in design 3 Runtime).
- Targets linux and darwin only (conversation).
- Local `serve` hosts the drain (conversation).
- Registration out of scope; tenant and key by env for the first round (Intent).
- `git diff-tree` runs in the drain, not the hook (design 2, Commit facts).
- Default local port 8770, beside the legacy 8765 (design 3).
- One key per tenant for read and write (design 3, Configuration).

## Assumption Ledger

### Assumption 1

- Question: "Tenant and key by env" — server only, or the client too?
- Answer chosen: server only (`WORKFLOW_SERVE_KEYS`). The client keeps `~/.config/workflow/client.toml`,
  written once by `workflow init` (design 5, Local bootstrap).
- Rationale: design 2 rejected env for the client because the drain inherits whichever hook's
  environment started it, which differs per harness.
- If wrong: the client reads endpoint and key from env as well; a few lines in the config loader.

### Assumption 2

- Question: does the shim know which conversation it serves?
- Answer chosen: no; it matches by path and content hash (design 4).
- Rationale: MCP servers are not told the conversation that spawned them.
- If wrong: a harness that exposes it lets the shim narrow by conversation as well.

### Assumption 3

- Question: how is Jev's secret screen asked?
- Answer chosen: one extra `score` question in the same System One request (design 3). The content
  therefore reaches TypeSafe in the request that may flag it; Jev guards persistence, not
  transmission.
- Rationale: the client already speaks that request shape; no second call per artifact.
- If wrong: a separate screen request; the `Scorer` interface already separates `Screen` and `Score`.

### Assumption 4

- Question: do the skills change in this round, given they drive tonight's run?
- Answer chosen: yes, as the last phase. Earlier phases run under the current skills and keep
  logging to the legacy service.
- Rationale: the architecture retires the tools; leaving the skills unchanged keeps agents calling
  them.
- If wrong: revert the phase 6 commits; the binary and capture are unaffected.

### Assumption 5

- Question: how do the new capture path and the running legacy path coexist before cutover?
- Answer chosen: phase 2 changes `spool.sh` file naming and adds a kick of the Go drain only when
  `WORKFLOW_BIN` is set; otherwise it kicks `drain.py` as now. Phase 5 flips the default queue and
  kick to `bin/workflow`.
- Rationale: Cursor's live hooks run from this checkout, so an early flip would strand its events in
  a queue nothing serves overnight.
- If wrong: events captured between phases 2 and 5 sit in the legacy queue; nothing is lost.

## Open Questions

- None blocking. Settled by tests in phases: burst start count, idle-exit race, real payloads per
  harness (only where they can be captured unattended; synthesized fixtures are marked unverified).

## Phases

### Phase 1 — Service core

- Outcome: `WORKFLOW_SERVE_KEYS=a=ka,b=kb workflow serve` on a temp data dir → `POST /v1/ingest`
  with a batch containing one secret-bearing fact returns per-fact results where only that fact is
  `rejected`, with a reason that names the pattern and does not contain the secret; resending
  returns all `duplicate`; artifact content goes through `pending/` and is promoted as `unscreened`;
  `GET /v1/artifacts` with tenant B's key does not see tenant A's artifact; `go test ./...` passes,
  including a writer burst test that reports p99 commit latency (reported, no threshold).
- Surfaces: `tools/workflow/` (new module: `cmd/workflow`, `internal/store`, `internal/ingest`,
  `internal/secrets` (one pattern set, shared by the client scrub and the server precheck),
  `internal/keys` (`repo_id`, path, content and row hashes from design 1), `internal/serve`).
- Approach: known
- Depends on: nothing

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| 1-01 Go module, keys and secret patterns | [briefs/1-01-module-keys-secrets.md](briefs/1-01-module-keys-secrets.md) | nothing | nothing |
| 1-02 Tenant store and group-commit writer | [briefs/1-02-store.md](briefs/1-02-store.md) | 1-01 | nothing (shares `go.mod`) |
| 1-03 Ingest, precheck and `workflow serve` | [briefs/1-03-ingest-serve.md](briefs/1-03-ingest-serve.md) | 1-01, 1-02 | nothing |

### Phase 2 — Capture

- Outcome: in a `mktemp -d` queue with a temp `serve`, 20 concurrent `spool.sh` calls are all
  delivered exactly once with one drain holding the lock; a write to `docs/plans/x/DESIGN.md`
  produces an `artifact_version` fact; a `git commit` tool call produces a `commit` fact with
  `diff-tree` paths and a `commit`-source version of each plan artifact it touched; one query over
  the temp ledger joins artifact version → commit → conversation; a secret-bearing artifact lands
  in `rejected/` with a reason; remote down then up loses nothing; while a local `serve` holds the
  lock, spools start no drain and are still delivered; with the client endpoint elsewhere `serve`
  leaves the queue alone; killing `serve` lets a standalone drain finish; `workflow status` reports
  queue size, oldest, rejected count and whether a drain runs. Replays use the committed fixtures in
  `tools/hooklog/tests/fixtures/`.
- Surfaces: `tools/workflow/internal/drain`, `internal/facts`, `internal/clientconfig`,
  `internal/serve` (hosted drain), `cmd/workflow` (`drain`, `status`), `tools/hooklog/spool.sh`
  (conversation-ID file names; Go kick only when `WORKFLOW_BIN` is set), fixtures.
- Approach: known
- Depends on: phase 1

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| 2-01 `spool.sh` conversation names and Go kick | [briefs/2-01-spool-coexistence.md](briefs/2-01-spool-coexistence.md) | nothing | 2-02 |
| 2-02 Fact building and client config | [briefs/2-02-facts-clientconfig.md](briefs/2-02-facts-clientconfig.md) | nothing | 2-01 |
| 2-03 `workflow drain` and `workflow status` | [briefs/2-03-drain-status.md](briefs/2-03-drain-status.md) | 2-01, 2-02 | nothing |
| 2-04 `serve` hosts the drain; phase outcome test | [briefs/2-04-serve-hosted-drain.md](briefs/2-04-serve-hosted-drain.md) | 2-03 | nothing |

### Phase 3 — Screening and scoring

- Outcome: with a fake scorer, accepted artifact content sits in `pending/` until screened; pass
  moves it to `blobs/` with `screens` and `scores` rows; flag deletes it and records a rejection;
  unreachable leaves it pending; with no `TYPESAFE_API_KEY` the verdict is `unscreened`; report-kind
  checks exist from design 1's rubric. A real Jev call on one design is made if the key is present
  and the API answers; otherwise it is skipped and reported.
- Surfaces: `tools/workflow/internal/scorer`, `internal/screen`, checks loading from
  `tools/quality/criteria.json` and `tools/quality/checks/`, new
  `tools/quality/checks/execution-report.json`.
- Approach: known
- Depends on: phase 1

#### Units

| Unit | Brief | Depends on | Alongside |
|---|---|---|---|
| 3-01 Scorer, check loading and execution-report checks | [briefs/3-01-scorer-checks.md](briefs/3-01-scorer-checks.md) | nothing | nothing |
| 3-02 Screen worker, store support and `serve` wiring | [briefs/3-02-screen-worker.md](briefs/3-02-screen-worker.md) | 3-01 | nothing |

### Phase 4 — Advisory shim and reads

- Outcome: `GET /v1/artifacts`, `/v1/checks`, `/v1/baselines` and `/v1/search` answer per design 4
  API against a temp `serve`; over stdio `workflow mcp` answers `initialize` and lists exactly
  `artifact_feedback`, `list_checks`, `search_artifacts`; `artifact_feedback` gives distinct
  answers for queued, rejected, delivered and stale files, with baseline flags; with the service
  down it returns local state and no MCP error.
- Surfaces: `tools/workflow/internal/mcp`, `cmd/workflow` (`mcp`), advisory reads in
  `internal/serve` and `internal/store`.
- Approach: known
- Depends on: phases 2 and 3

### Phase 5 — Distribution and cutover

- Outcome: `bin/workflow --version` prints `workflow <version> <commit>` from a clean temp cache by
  building from source, and two concurrent first runs both succeed; `tools/release/build.sh`
  produces four binaries and `bin/SHA256SUMS`; `workflow init` in a temp `HOME` writes
  `client.toml`, `serve.env` and the user unit, mode 0600, and enables nothing; replaying the write
  fixtures through each shipped hook config into a temp `serve` produces an `artifact_version`; no
  shipped config references `artifact_submit.py`, `--harness auto` or the HTTP MCP; `drain.py`, the
  systemd timer and service are gone.
- Surfaces: `bin/` (`workflow`, `VERSION`, `RELEASE_URL`, `SHA256SUMS`), `tools/release/`,
  `cmd/workflow` (`init`, `--version`), `hooks/hooks.json`, `hooks/cursor.json`, `.mcp.json`,
  `tools/hooklog/` (configs, `spool.sh` default flip, `drain.py`, timer, tests),
  `packages/opencode-workflow-hooks`.
- Approach: known
- Depends on: phases 2, 3 and 4

### Phase 6 — Skills and templates

- Outcome: a grep of `skills/` (including templates) and `plugins/` for `post_design`, `post_brief`,
  `patch_design`, `patch_brief`, `start_execution`, `patch_execution`, `complete_execution`,
  `design_id`, `brief_id` and `[exec` returns nothing; the execute skill requires each worker to
  write `docs/plans/<plan>/reports/<brief-name>.md` and names `artifact_feedback`; `Workflow-Phase:`
  trailers remain.
- Surfaces: `skills/` (design, refine, execute, comprehensive-review, close-out and their
  templates), any skill copies under `plugins/`.
- Approach: known
- Depends on: phase 4

## Provenance Notes

The design conversation that produced designs 1 to 5 is session a4e0ba81 (excluded from analysis
as live). Rejected alternatives are recorded in each design-intent doc.
