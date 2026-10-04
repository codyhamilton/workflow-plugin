---
brief_id: 223
design_id: 209
---

# Brief: 4-02 — MCP shim package: protocol, three tools, queue awareness

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its package is wired to `workflow
mcp` and verified end to end against a real `serve` by 4-03; agents in every harness are the final
consumer, through the three tools.
Owned paths: `tools/workflow/internal/mcp/` (new), `tools/workflow/internal/facts/` (one exported
function and its test only), `docs/plans/09-workflow-binary/reports/4-02-mcp-shim.md` (new). Touch
nothing else; in particular not `internal/serve`, `internal/store` (4-01 owns them), `internal/drain`,
`internal/keys`, `cmd/workflow` (4-03 wires the subcommand), `go.mod` or `go.sum` (no new
dependencies: the protocol is hand-written JSON-RPC over `encoding/json`).
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: nothing. You code to the service response shapes fixed in design 4 and in 4-01's
contract (quoted below), served by an `httptest` stub; 4-03 runs you against the real thing.
Runs alongside: 4-01 (disjoint paths).
Budget: 10 files to read, about 750 lines to write including tests, 70 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/design/04-advisory-surface.md` — Shape (lines 16-29), `artifact_feedback` (lines 31-50),
   API (lines 52-65), Scores and baselines (lines 67-71), Unreachable service (lines 73-77). Binding.
2. `docs/design/02-edge-capture.md` — Config (lines 121-138) and MCP shim (lines 140-157). Binding.
3. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 4 (lines 210-220).
4. `docs/plans/09-workflow-binary/briefs/4-01-service-reads.md` — Contract only: the response
   shapes, the `rejection` and `loaded` fields, verdict names.
5. `go doc ./internal/keys` (`RepoPath`, `RepoID`, `Kind`, `ContentHash`), `go doc ./internal/drain`
   (`QueueDir`, `Running`, `QueueStatus`), `go doc ./internal/clientconfig` (`Load`, `ErrNoConfig`,
   `Path`).
6. `tools/workflow/internal/facts/facts.go` — `parseFile` and `writePaths`, and how `Build` keys an
   artifact (grep `RepoPath`).
7. `tools/workflow/internal/drain/drain.go` — `reject` (the `.reason` file format) and `list`.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, `mcp.Serve(ctx, stdin, stdout, opts)` speaks MCP over stdio and answers
`artifact_feedback`, `list_checks` and `search_artifacts`. For a file path it gives the agent one of
these distinct answers: queued (with why), rejected (with the reason and "rewrite the file"),
delivered (verdict, scores, baseline flags), stale, not delivered, not tracked, or no config. When
the service is down it still returns local state, never a protocol error.

## Contract

Cited, binding (design 4, `artifact_feedback`): "Order of answer: 1. Queued: events for this file
still in `queue/`. The shim kicks the drain and waits up to about 1.5 s first. If still queued, it
says how many, the oldest's age, and why (`no config`, `remote unreachable`, or `draining`).
2. Rejected: a `rejected/` file for this path, with its reason. The agent's fix is to rewrite the
file. 3. Delivered: the latest version the service holds, with screen verdict and scores. If the
latest stored hash differs from the file's current hash, the answer says the current content has not
been delivered yet." Design 4, Unreachable service: "the shim still answers from local state". Design
2: "Matching is by path, not conversation". Design 2, Keys: "The drain and the shim use the same
functions."

Service shapes you consume (4-01 builds them; additive fields marked):

- `GET /v1/artifacts?repo_id=&path=` → `{"repo_id","path","kind","versions","latest":{
  "content_hash","received_at","conversation_id","source","screen":{"verdict","scorer","at"}|null,
  "scores":[{"check","score"}],"rejection":{"stage","reason","at"}|null}}` or 404. `rejection` is
  additive; treat a missing field as null.
- `GET /v1/checks?kind=` → `{"checks":[{"kind","name","q","levels","invert"}],"loaded":bool}`
  (`loaded` additive; missing means true).
- `GET /v1/baselines?kind=` → `{"kind","checks":{"<name>":{"n","p25","median","p75"}}}`.
- `GET /v1/search?q=&kind=&limit=` → `{"hits":[{"repo_id","path","kind","content_hash","snippet",
  "rank"}]}`.
- Verdicts: `pass` (the code's name for design 4's `passed`) and `unscreened`; a Jev flag shows as no
  screen plus `rejection.stage` `screen`.

Decisions made at refine (settled):

- **Protocol.** JSON-RPC 2.0, one JSON object per line on stdin, one per line on stdout, nothing else
  on stdout; logs to stderr. Requests handled in order, one at a time. Exit cleanly on EOF.
  - `initialize`: reply with the client's `protocolVersion` if it is one of `2025-11-25`,
    `2025-06-18`, `2025-03-26`, `2024-11-05`, else `2025-11-25`; `capabilities`
    `{"tools":{"listChanged":false}}`; `serverInfo` `{"name":"workflow","version":<opts.Version>}`;
    `instructions` one sentence on what the tools are for.
  - Notifications (no `id`, including `notifications/initialized` and `notifications/cancelled`)
    get no reply. `ping` → `{}`.
  - `tools/list` → exactly `artifact_feedback`, `list_checks`, `search_artifacts`, each with
    `description`, `inputSchema` (JSON Schema object, `additionalProperties: false`) and
    `annotations: {"readOnlyHint": true}`. Schemas: `artifact_feedback {path: string, required}`;
    `list_checks {kind: enum design|brief|report, required}`; `search_artifacts {query: string,
    required; kind: enum design|brief|report, optional}`.
  - `tools/call` → `{"content":[{"type":"text","text":…}],"isError":bool}`.
  - JSON-RPC errors only for protocol faults: unparseable line → -32700 with `id: null`; a JSON array
    (batch) or a non-object → -32600; unknown method → -32601; `tools/call` with an unknown tool
    name or no `name` → -32602.
  - `isError: true` only for bad arguments (missing or wrong-typed `path`, `kind` outside the enum,
    empty `query`, `path` missing on disk or a directory), with the reason as text. A service that is
    down, refusing, or unconfigured is **never** `isError` and never a JSON-RPC error: the answer is
    a normal result saying so.
- **Keys.** The target is `path` resolved against the process's working directory (absolute paths
  as given), cleaned. `keys.RepoPath(abs)` → `(top, rel)`, `keys.RepoID(top)`, `keys.Kind(rel)`,
  `keys.ContentHash` of the bytes on disk: the same calls `facts.Build` makes. Outside a repo, a path
  that is not a design/brief/report, or a repo with no commit yet (no repo_id; phase 2 carried item):
  state `not tracked` with that reason and no service call.
- **Queue matching.** Export `facts.WritePaths(raw []byte) []string` (or over a read `File`; your
  choice, named in the report): the cleaned absolute write paths of an envelope, as `Build` uses
  them, nil for anything unparseable. An `.evt` in `queue/` or `queue/rejected/` matches when one of
  its write paths equals the target, or keys to the same `(repo_id, rel)` (a worktree or symlinked
  checkout of the same repo). Cache the key per absolute path within a call. Commit tool calls are not
  matched (their paths come from git at drain time); note this as a limit in the report.
- **Kick.** If matching queue files exist, client config loads, and `drain.Running(dir)` is false,
  start the drain: by default `os.Executable()` with arg `drain`, `Setsid`, stdio to `/dev/null`,
  inherited environment, reaped with `go cmd.Wait()`. When `serve` holds the lock, `Running` is true
  and nothing is started. The starter is an `Options` field so tests inject a fake. Then poll the
  matching set every 100 ms for up to `Options.Wait` (default 1500 ms), stopping early when none
  remain.
- **Answer.** Plain text, first line `state: <state>`, then `path: <rel>`, `repo: <repo_id>`,
  `content_hash: <hash>`, then the state's lines. States:
  - `queued`: `<n> events for this file still queued, oldest <age>, <why>` where why is `no config`
    (naming `clientconfig.Path()`), `remote unreachable` (a 3 s `GET /v1/health` fails), or
    `draining`.
  - `rejected`: a matching rejected `.evt` whose mtime is not older than the file's current mtime.
    Give each reason line from its `.reason` file with the leading `<name>: ` stripped, then `Fix:
    rewrite the file; the new write is the repair.` An older rejection (the file was rewritten since)
    does not set the state; later states add one `note: earlier rejection superseded by a later
    write` line.
  - `delivered`: the service's `latest.content_hash` equals the current hash. Verdict line:
    `screen: unscreened (no scorer on the service)`, `screen: pass by <scorer>`, `screen: flagged:
    <reason>` plus the rewrite fix, or `screen: awaiting screen`. Then one line per score:
    `<check> <score> (baseline p25 <p25>, median <median>, n <n>)`, with ` BELOW p25` appended when
    flagged. Then `versions: <n>`.
  - `stale`: the service holds a different latest hash: `current content not yet delivered (service
    has <short hash> from <received_at>); normally a write still in the batch window`.
  - `not delivered`: 404 and nothing local.
  - `no config`: nothing queued and no client config: `no client config at <path>; nothing is
    delivered until it exists`.
  - With the service unreachable or returning 5xx: the local state (queued, rejected or none) plus
    `service unreachable at <endpoint>`.
- **Baseline flags.** Fetch `/v1/baselines?kind=<kind>` for delivered answers. A check is flagged
  when the baseline `n ≥ 4` and its score `<` p25 (strictly; stored scores are already in 0..1
  with higher better, `invert` applied at scoring in `scorer/jev.go` `scoresOf`; do not re-invert). With `n < 4`, no flag and the line
  ends `(baseline n=<n>, too few to flag)`. A check with no baseline entry gets no flag.
- **list_checks.** Text: one line per check, `<name> [levels a/b/…] [inverted]: <q>`, or `no
  checks loaded on the service` when `loaded` is false. Service down or no config: say so, not an
  error.
- **search_artifacts.** `limit` 10. One block per hit: `<kind> <repo_id>:<path> (rank <r>)`, then
  the snippet. No hits: `no matches`. Service down or no config: say so.
- **HTTP.** Each request has a 3 s timeout and `Authorization: Bearer <key>`, with config from
  `clientconfig.Load` on each call (re-read, as the drain does). The key never appears in any text,
  log or error. The endpoint may.

## Changes

New package `internal/mcp`: `Options{Version, QueueDir, Wait, StartDrain func() error, Getwd,
HTTP *http.Client}` (shape is yours), `Serve(ctx, r io.Reader, w io.Writer, opts) error`, the
protocol loop, the three tools, the HTTP client, queue matching. Tests in the package. In
`internal/facts`: the exported `WritePaths` wrapping the existing unexported code, plus a test.

### Keep untouched

`facts.Build`'s behaviour and outputs (phase 2 tests unchanged). The drain, the queue file format, and
the `.reason` format: read them, never write them.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

Fail first: write `TestShim` (below) first and quote its failure.

- `go vet ./... && go test -race -count=1 ./...` → passes, all earlier tests unchanged.
- `go test -v -run TestShim ./internal/mcp` → drives `Serve` over `io.Pipe` with a temp git repo
  (`git init`, one commit, `t.TempDir()`), a temp queue, a client config file via
  `WORKFLOW_CLIENT_CONFIG`, an injected `StartDrain`, and an `httptest` stub of the four endpoints.
  One subtest per line, each printing PASS/FAIL:
  1. **initialize**: echoes `2025-06-18`; answers `2025-11-25` to an unknown version; a notification
     gets no reply; `ping` → `{}`.
  2. **tools/list**: exactly the three names, each with an object `inputSchema` and `required`.
  3. **protocol errors**: a bad line → -32700; `[]` → -32600; `foo/bar` → -32601; unknown tool →
     -32602; the loop keeps serving after each.
  4. **bad arguments**: missing `path`, a directory, `kind=x`, empty `query` → `isError: true`,
     with no JSON-RPC error.
  5. **queued**: two matching `.evt` files (one by absolute path, one written from a second
     checkout path of the same repo) and one for another file → `StartDrain` called once, the answer
     says `2 events` and `oldest`; with a held `queue/.drain.lock` (flock it in the test)
     `StartDrain` is not called and why is `draining`; with the stub closed, why is `remote
     unreachable`.
  6. **rejected**: a rejected `.evt` plus `.reason` (`<name>: secret: aws_access_key at line 3 in
     docs/…`) → state `rejected`, the reason without the `<name>: ` prefix, the rewrite fix; after
     touching the file to a newer mtime the state is no longer `rejected` and the note appears.
  7. **delivered**: stub hash equals the file's → verdict `unscreened`; a `pass` answer shows the
     scorer; a stub with `rejection.stage` `screen` shows `flagged` and the fix; scores with baseline
     `n` 5 and one score below p25 → exactly that line has `BELOW p25`; baseline `n` 3 → no flag and
     `too few to flag`.
  8. **stale and not delivered**: stub returns another hash → `stale`; 404 → `not delivered`.
  9. **no config and unreachable**: no config file → `no config` naming the path, no HTTP made; config
     pointing at a closed port with one queued file → `queued` and `service unreachable`, `isError`
     false, no JSON-RPC error.
  10. **not tracked**: a design path in a directory that is not a repo → `not tracked`.
  11. **no key leak**: the config key string appears in no response text across all subtests.
- `go test -run TestWritePaths ./internal/facts` → passes.

Safety: temp dirs only (`t.TempDir()`); `WORKFLOW_QUEUE`, `WORKFLOW_CLIENT_CONFIG` and `HOME` point at
temp paths in every test (`t.Setenv`). Never read or write the live queue, `~/.config/workflow` or
`~/.local/share/workflow*`. No `serve` is needed; if you start one, it listens on `127.0.0.1:0` (never
8765 or 8770) and is killed after. The default drain starter is never exercised in tests: always
inject `StartDrain`, so no real drain process can touch anything. `TYPESAFE_API_KEY` is in your
environment: any child process (git included) gets `TYPESAFE_API_KEY=` (blank); never print, log,
echo or write it (no `env`, `printenv`, `set -x`). No Jev call is made in phase 4.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 4: MCP shim package` (the
orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write `docs/plans/09-workflow-binary/reports/4-02-mcp-shim.md`
(design 1, Execution report: what was done against this brief, verifiably; departures and why;
unfinished work; known problems; nothing derivable), including the `TestShim` lines, one full answer
text per state from the tests, the exported names (`Serve`, `Options`, `WritePaths`), and the
commit-path limit, and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
