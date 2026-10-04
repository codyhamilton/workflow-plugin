# Workflow binary implementation

Tool: Claude Code (Opus 5.5 orchestrator, subagent workers), on `hooks-reconcile`.
Run identity: session https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp, starting HEAD
`9e79ede`.
Started: 2026-10-05 (Australia/Brisbane).

Unattended run: the maintainer asked for designs 3 to 5 and execution of everything designed, with
no stops, on this branch. No push, tag, release publish or PR. Go 1.27.1 was installed to
`~/.local/go` for the build (no system Go existed).

Execution logging uses the legacy `workflow-quality` service on 8765 while it is still the live
ledger; phase 5 retires that requirement.

## Phase 1 — Service core

Refined into three sequential units (briefs 210–212, design_id 209), committed in `dc64539`.
Refine decisions the later phases rely on: the fact JSON keys are fixed in brief 1-03; the row hash
excludes `id` and `content`; a resent rejected fact is rejected again, not `duplicate`.

### 1-01-module-keys-secrets (execution 14)

- Built: the Go module `tools/workflow`, `internal/keys` (repo_id, repo path, content and row
  hashes) and `internal/secrets` (one shared pattern set), with tests. A test scans every tracked
  `.md` file and finds no hits.
- Commit: `ae37ae0`. `go vet` and `go test ./...` pass.
- Deviations: none. Known limits are in its report: the `.env`-style pattern is loose, and
  `RepoPath` errors for a directory that does not exist.
- Agent: Sonnet, 10 tool calls, about 53k tokens.

### 1-02-store (execution 15)

- Built: `internal/store`: tenant directories, `ledger.db` (WAL), blobs and pending, the facts,
  rejections, screens and scores tables, and one group-commit writer per tenant.
- Commit: `8024966`. `go test ./...` passes, and the race tests pass with 50 concurrent appenders
  and no `SQLITE_BUSY`.
- Writer burst (8 tenants, 4,800 facts, 20-fact requests): p50 11 ms, p99 20–30 ms, ledger 6 MB.
  Reported only; there is no threshold.
- Deviations: an empty `Raw` errors explicitly, because `INSERT OR IGNORE` swallows the NOT NULL
  violation; a `tmp/` directory was added to each tenant directory; index names are the worker's
  own.
- Agent: Sonnet, 9 tool calls, about 58k tokens.

### 1-03-ingest-serve (execution 16)

- Built: `internal/ingest` (fact types, validation, precheck, row hash, pending write, batch
  append), `internal/serve` (auth, `/v1/health`, `/v1/ingest`, `/v1/artifacts`, the promotion
  worker), and `cmd/workflow` (`serve`, `version`).
- Commit: `497fa69`. `go vet` and `go test -race ./...` pass across six packages.
- Deviations: worker control is `Options.DisableWorker` plus `Server.StartWorker()`; a missing `ts`
  is stored as 0, and a mistyped `ts`, `harness` or `event` is `invalid:`; a `version` subcommand
  was added; no `429` this phase.
- Agent: Sonnet, 10 tool calls, about 65k tokens.

### Phase 1 verification

The orchestrator built the binary and ran `serve` with `WORKFLOW_SERVE_KEYS=a=ka,b=kb` on a temp
data dir and port 18771, then posted a three-fact batch: a hook event, a design, and a brief
containing an AWS-format key.

- First POST: `accepted`, `accepted`, `rejected` with `precheck: aws_access_key at line 1`.
- Resend: `duplicate`, `duplicate`, `rejected` (the refine's reading of the outcome).
- `GET /v1/artifacts` with key `ka`: the design with `versions: 1` and screen verdict `unscreened`;
  its blob is in `blobs/`.
- Same request with `kb`: 404. Bad key: 401.
- The secret's text appears in neither the data directory nor the server log.

Outcome holds.

### Carried

1. `Promote` moves the blob before writing the `screens` row. A crash between the two leaves a
   blob with no screen row. Phase 3's screen worker must retry anything not screened when it starts.
2. A resent artifact whose pending file was lost while its ledger row survived returns `duplicate`
   and is never re-written. Phase 3 should treat a fact whose content has neither a pending file
   nor a blob as a screen gap.
3. The service never sends `429` yet. The drain must still honour it (design 2).
4. `TestServeOutcome` picks a free port by binding and releasing it, which is a small race.

## Phase 2 — Capture

Refined into four units (briefs 215, 217, 218 and 219), committed in `8add2a0`. 2-01 and 2-02 ran in
parallel; 2-03 and 2-04 ran after them. Refine decisions:

- Payloads without a conversation ID are still spooled on the legacy path, as `unknown-…`, until
  phase 5. The Go path drops them.
- The client-config override variable is `WORKFLOW_CLIENT_CONFIG`.
- The hook-side `mkdir` lock and kqueue are deferred.

### 2-01-spool-coexistence (execution 18)

- Built: `spool.sh` names queue files `<conversation_id>-<ts>-<pid>-<rand>.evt` and kicks
  `$WORKFLOW_BIN drain` only when `WORKFLOW_BIN` is set; otherwise it uses the legacy spool dir and
  `drain.py --daemon` as before. Adds `test_spool_queue.py`.
- Commit: `546b5d0`. 36 hooklog tests pass.
- Deviations: on the Go path the kick is skipped when the event was not spooled. The worker briefly
  copied `spool.sh` into an existing `/tmp/x` and removed the copy; that directory's other files
  are untouched.
- This change is live for Cursor at once, since Cursor's hooks run from this checkout. With
  `WORKFLOW_BIN` unset, behaviour is unchanged apart from file names.
- Agent: Sonnet, 11 tool calls, about 50k tokens.

### 2-02-facts-clientconfig (execution 19)

- Built: `internal/facts` (hook events, artifact versions from the write surfaces, commit facts
  from `git commit` tool output with `diff-tree`, commit catch-up, client scrub) and
  `internal/clientconfig`. Adds a synthesized `commit_calls.json` fixture, marked unverified.
- Commit: `87ec4b6`. `go test ./...` passes; every built fact is accepted by `ingest.Ingest`.
- Deviations: `diff-tree` runs with `-z --no-commit-id`; copies add to `paths` only; the commit fact
  goes on the first file in a batch that names a given `(conversation, repo, sha)`; a commit with no
  usable cwd gives no fact.
- Not done: the config's 0600 mode is not enforced on read; one file read per `Build` is not tested.
- Agent: Sonnet, 10 tool calls, about 73k tokens.

### 2-03-drain-status (execution 20)

- Built: `internal/drain` (lock, batch window, linger, idle exit with rescan, in-memory backoff,
  `Retry-After`, 400/413 split, `rejected/` with reasons) and `workflow drain` / `workflow status`.
- Commit: `f41ba63`. `go test -race ./...` passes. Burst: 20 spools gave 14 process starts, one lock
  holder, and 20 rows.
- Deviations: removed three lines of `TestServeOutcome` that expected a non-zero exit with no
  config and ran with the real `HOME`; 404, 3xx and a malformed 200 are retried like a 5xx;
  backoff starts at 500 ms.
- Agent: Sonnet, 13 tool calls, about 90k tokens.

### 2-04-serve-hosted-drain (execution 21)

- Built: `serve` holds the drain lock and drains the queue in process when the client endpoint is
  itself, rechecking every 3 s; `TestCaptureOutcome` has one clause per outcome item.
- Commit: `d1c177a`.
- Deviations: a wildcard bind counts as loopback; `WORKFLOW_SERVE_POLL` was added for tests; tests
  now set `WORKFLOW_QUEUE` and `WORKFLOW_CLIENT_CONFIG` to temp paths.
- Agent: Sonnet, 19 tool calls, about 81k tokens.

### Phase 2 verification

The orchestrator ran `go vet` and `go test -race -count=1 ./...` (all nine packages pass), then
`go test -v -run TestCaptureOutcome ./cmd/workflow`:

```
outcome hosted-burst           PASS
outcome write                  PASS
outcome commit-and-join        PASS
outcome secret                 PASS
outcome endpoint-elsewhere     PASS
outcome kill-and-recover       PASS
outcome status                 PASS
```

The standalone 20-spool burst and the down-then-up case pass in 2-03's binary tests. The hooklog
Python suite passes. `~/.local/share/workflow` and `~/.config/workflow` still do not exist, and no
`serve` or `drain` process is left running. Outcome holds.

### Carried

1. From phase 1: a crash in `Promote` between blob and screen row; re-screen anything not screened
   when the worker starts (phase 3).
2. From phase 1: a fact whose content has neither a pending file nor a blob is a screen gap
   (phase 3).
3. A repo with no commits has no `repo_id`, so its writes give no `artifact_version` until its
   first commit. Accepted; note it in the morning report.
4. The commit fixtures are synthesized. A real `git commit` payload per harness is still to be
   captured.
5. Deferred to phase 5: the hook-side `mkdir` lock and kqueue on macOS; dropping `unknown-`
   spooling when the default flips.
6. The client config's 0600 mode is not checked on read.

## Phase 3 — Screening and scoring

Refined into two sequential units (briefs 220 and 221), committed in `ffd33f7`. Refine decisions:

- `serve` reads `WORKFLOW_CHECKS_DIR` (the `tools/quality` folder). Without it, the key still screens
  but nothing is scored. Phase 5's `workflow init` writes it into `serve.env`.
- A Jev credential level of 2 or 3 flags. Screen rejections use stage `screen` and pattern
  `jev_screen`. Backoff for an unreachable scorer starts at 5 s and doubles to 5 min.
- Carried 1 and 2 were both absorbed into 3-02.

### 3-01-scorer-checks (execution 22)

- Built: `internal/scorer` (the `Scorer` interface, `LoadChecks`, `Jev`, `Fake`) and
  `tools/quality/checks/execution-report.json`, holding five `r.*` checks whose wording matches
  design 1 verbatim.
- Commit: `dd1588a`. The live `TestJevLive` ran: verdict pass, 11 `d.*` scores within 0..1.
- Jev answers fractionally (for example 0.583), not with 0..3 integers. The screen truncated, so a
  1.9 passed. The orchestrator changed it to round to the nearest level (`1c1d2ea`), so 1.5 and above
  flags, and added test cases.
- The legacy service never reads `checks/execution-report.json`; `load_checks.py` would reject the
  `report` kind.
- Agent: Sonnet, 7 tool calls, about 62k tokens.

### 3-02-screen-worker (execution 23)

- Built: `internal/screen` and its `Step`. `store.Promote` now writes the screen row and scores in one
  transaction. Also: the gap and blob helpers, serve backoff, re-screening unscreened blobs at worker
  start, `screen_gaps` in `/v1/health`, and `cmd` wiring of `TYPESAFE_API_KEY` and
  `WORKFLOW_CHECKS_DIR`. Every binary test blanks the key in the child process.
- Commit: `49600c5`.
- Carried 2: a resend after the pending file is lost returns `duplicate` and re-creates the pending
  file, so no ingest fix is needed.
- Deviations: tests were written after the code, so there is no failing-first output. `ContentFacts`
  returns a struct.
- Limits: `screen_gaps` is counted once at worker start; the new store methods are covered only
  through the serve and screen tests.
- Agent: Sonnet, 19 tool calls, about 84k tokens.

### Phase 3 verification

The orchestrator ran `go vet` and `go test -race -count=1 ./...` (all 11 packages pass) with the key
blank, then `go test -v -run TestScreeningOutcome ./internal/serve`: every subtest passed, covering
pending until screened, pass, pass kinds, flag, unreachable, no key, the crash between blob and
screen row, the screen gap, and the report checks.

End to end with the real key: the binary ran in a `mktemp -d` dir on port 18771 with
`WORKFLOW_CHECKS_DIR` set, and plan 09's DESIGN.md was ingested as an `artifact_version`. The result
was `accepted`, then a screen of `{"verdict":"pass","scorer":"jev-1.13.0"}` with 11 scores (for
example `d.outcomes_checkable` 0.977), and health showed `pending 0, screen_gaps 0`. The stderr
showed `checks design=11 brief=11 report=5`. The key appeared in neither the log nor the data dir.
The server was killed and the dir removed. Outcome holds.

### Carried

1. From phase 2: no `repo_id` before a repo's first commit; synthesized commit fixtures; 0600 not
   checked on read; the phase 5 items (`mkdir` lock, kqueue, dropping `unknown-`).
2. `screen_gaps` does not fall until a restart.
3. Content is sent to Jev unscrubbed, after the precheck (design 3, principle 9).

## Phase 4 — Advisory shim and reads

Refine split the phase into three units (briefs 222, 223 and 224), committed in `e31b364`. 4-01 and
4-02 ran in parallel; 4-03 ran after both. Refine settled these decisions:

- MCP is hand-written JSON-RPC 2.0, one message per line. `initialize` echoes a supported protocol
  version. A service that is down or has no config gives a normal result; `isError` marks bad
  arguments only.
- A baseline flag needs n ≥ 4 and a score strictly below p25. Quartiles use linear interpolation.
  Stored scores already have `invert` applied.
- Search is FTS5 (which modernc supports) over the latest screened version per path. The query
  becomes quoted words joined by OR. `limit` defaults to 10, maximum 50.
- Two fields were added to `/v1` responses: `latest.rejection` on `/v1/artifacts` and `loaded` on
  `/v1/checks`. The code names the passing verdict `pass`; design 4 says "passed".

### 4-01-service-reads (execution 24)

- Built: store migration 2 (the FTS5 `search` table and a backfill on upgrade), `LatestScores`,
  `Search` and `Latest.Rejection`; `/v1/checks`, `/v1/baselines`, `/v1/search` and
  `latest.rejection`. Checks now load whenever `WORKFLOW_CHECKS_DIR` is set, even without a key.
- Commit: `742c768`. `TestAdvisoryReads` (6 subtests) and `TestReadsWiring` pass.
- Departures: `DropBlob` now runs its own transaction, so the index delete and the rejection insert
  commit together. The backfill test builds its version-1 database by downgrading a current one.
- Agent: Sonnet, 23 tool calls, about 92k tokens.

### 4-02-mcp-shim (execution 25)

- Built: `internal/mcp` (the protocol, the three tools, the `artifact_feedback` states and queue
  matching) and `facts.WritePaths`.
- Commit: `2127e0e`. `TestShim` passes 11 subtests plus one extra.
- Departures: with work queued but no config, the shim neither kicks the drain nor waits.
  `(no baseline)` and `baselines unavailable` cover cases the brief left open. A single queued
  event reads `1 events`.
- Known limit: files written by commit tool calls are not matched in the queue, so a committed file
  that has not drained shows as not delivered or stale.
- Agent: Sonnet, 14 tool calls, about 86k tokens.

### 4-03-mcp-wiring-outcome (execution 26)

- Built: `workflow mcp` (stdio, signals, exit 0 on EOF, exit 2 for any argument) and
  `TestAdvisoryOutcome`, which runs against the built binary.
- Commit: `7d9aee5`. 4-02's default drain starter is exercised in the queued subtest.
- Departures: `tools-answer` runs before `service-down`. With the service down, a delivered file
  reads `not delivered` plus `service unreachable`.
- Agent: Sonnet, 16 tool calls, about 83k tokens.

### Phase 4 verification

The orchestrator ran `go vet` and `go test -race -count=1 ./...`; all 12 packages pass with the key
blank. `go test -v -run TestAdvisoryOutcome ./cmd/workflow` passed every subtest: reads,
initialize, tools-list, queued, rejected, delivered-baseline (`BELOW p25` on the lowest check
only), stale, distinct-answers, tools-answer and service-down.

A direct stdio run of the built binary in a temp `HOME` with no config answered `initialize`
(echoing 2025-06-18), listed exactly `artifact_feedback`, `list_checks` and `search_artifacts`, and
returned `state: no config` naming the file, with `isError` false. No workflow processes are left
running. The live dirs do not exist. The phase outcome holds.

### Carried

1. From phases 2 and 3:
   - no `repo_id` before a repo's first commit (the shim reports `not tracked`);
   - synthesized commit fixtures;
   - mode 0600 not checked on read;
   - the phase 5 items;
   - `screen_gaps` only falls on restart.
2. Commit-path matching in the shim's queue check.

## Phase 5 — Distribution and retirement

Refine split the phase into five units (briefs 225 to 229), committed in `eb9e954`. 5-01 and 5-04 ran
in parallel, then 5-03 and 5-02, then 5-05 last. Refine settled these decisions:

- The wrapper `bin/workflow` resolves the binary in this order:
  1. `WORKFLOW_BIN`;
  2. the cache `${XDG_CACHE_HOME:-~/.cache}/workflow/<VERSION>/`;
  3. a checksummed download from `bin/RELEASE_URL` (overridden by `WORKFLOW_RELEASE_URL`);
  4. a source build.

  Go is found on `PATH` or in `~/.local/go/bin`. Builds take an `mkdir` lock holding a pid, which
  goes stale after 10 minutes. `bin/VERSION` is 0.1.0.
- `workflow init` writes `client.toml`, `serve.env` and the user unit, mode 0600, and only files
  that are missing. The unit reads an optional `serve.secrets.env`, which the user creates to hold
  the key; `init` never writes it. `init` runs no `systemctl`.
- `spool.sh` writes only to the queue. Payloads with no conversation ID are dropped, and a missing or
  `auto` harness spools nothing. Each hook kicks `bin/workflow drain`. Without `flock`, or with
  `WORKFLOW_SPOOL_NOFLOCK=1`, the kick uses an `mkdir` lock. The script runs under bash 3.2.
- Every shipped config runs the `--version` prefetch detached at session start, registers stdio
  `bin/workflow mcp`, and drops `artifact_submit`. The units retired `drain.py`, its timer and
  `install-drain.sh`.

### 5-01-version-init (execution 27)

- Built: `--version`/`version` and `workflow init`, with `TestVersion` and `TestInit` (including a
  fake `systemctl` that must not be called).
- Commit: `102a719`. The full race suite passes.
- Departures: the `init` tests use a minimal explicit child environment.
- Agent: Sonnet.

### 5-04-opencode-plugin (execution 29)

- Built: the OpenCode plugin writes `.evt` files to the queue in the same format as `spool.sh`.
  It kicks the drain at most once per 10 s and runs the prefetch at load. The submit and spool
  helpers are removed. 6 of 6 tests pass.
- Commit: `6ba9457`.
- Departures: the envelope event is the payload's `hook_event_name`.
- Agent: Sonnet.

### 5-03-spool-flip-retire (execution 28)

- Built: the queue-only `spool.sh` with the `mkdir` lock fallback. Retired `drain.py`,
  `install-drain.sh` and the drain units. `test_spool_queue.py` passes 20 tests and
  `test_hooklog.py` passes 11.
- Commit: `122556a`.
- Departures: a stale `drain.py` mention in the `hooklog.py` docstring was out of scope. The
  orchestrator fixed it in `7e3211e`, which also routes the `hooklog.py record` shim to `spool.sh`.
  The shim had been writing to the legacy spool, which nothing drains any more.
- Agent: Sonnet, 17 tool calls, about 72k tokens.

### 5-02-wrapper-release (execution 30)

- Built: `bin/workflow`, `bin/VERSION`, `bin/RELEASE_URL`, `bin/SHA256SUMS`,
  `tools/release/build.sh` and `test_release.py`, which passes 10 tests. Every download test
  uses `file://`.
- Commit: `8dc45fa`.
- Departures: a stale lock is retaken whenever a waiter sees one, so two waiters can race. The worst
  case is a duplicate build, which is safe because the final step is an atomic rename.
- Agent: Sonnet, 7 tool calls, about 54k tokens.

### 5-05-configs-outcome (execution 31)

- Built:
  - the four hook configs on `spool.sh --harness <name>` with the prefetch;
  - stdio MCP in `.mcp.json`, plus Cursor and Codex MCP examples;
  - the README;
  - `test_surfaces.py` and `test_write_surfaces.py`, with `test_artifact_submit_surfaces.py`
    deleted;
  - `tools/release/phase5_outcome.py`.
- Commit: `4031e9f`.
- Departures: Codex configs pass no `--event`. OpenCode fixtures replay through `spool.sh`.
- Problem hit: `/tmp` is a tmpfs with a per-user quota, and it ran out mid-run, so three gate
  clauses failed with `disk quota exceeded`.
- Orchestrator fix: `test_release.py` now passes `TMPDIR` and `GOTMPDIR` through, and `goenv` asks Go
  with the real home, so its caches are not moved under a temp `HOME`. This fixes the defect
  5-05 reported.
- Agent: Sonnet, 60 tool calls, about 41k tokens.

### Phase 5 verification

- **Gate:** the orchestrator ran `python3 tools/release/phase5_outcome.py` with `TMPDIR` and
  `GOTMPDIR` in a `mktemp -d` dir under `$HOME`. All seven clauses pass: version-clean-build,
  concurrent-first-runs, release-build, init, write-replay, no-retired-refs and
  retired-files-gone.
- **Full suites:** all pass, run with the key blank and temp files off `/tmp`:
  - `go vet` and `go test -race -count=1 ./...` (12 packages);
  - the hooklog suite (34 tests);
  - `test_release.py` (cold build 0.9 s with a warm `GOCACHE`);
  - OpenCode `test_hooks.mjs` (6 of 6).
- **Processes:** no workflow processes are left running.
- **Live dirs** (read only):
  - `~/.local/share/workflow` does not exist, so nothing is queued yet.
  - `~/.cache/workflow/0.1.0/` exists but is empty. It was created at 04:11, during 5-05's runs and
    before its commit, probably by a build that hit the `/tmp` quota.
- **Feedback:** `artifact_feedback` was not run on the phase's reports. This session has no
  `client.toml` and no `serve`, so the shim answers `no config`.
- **Result:** the phase outcome holds.

### Carried

1. From phases 2 to 4:
   - no `repo_id` before a repo's first commit;
   - synthesized commit fixtures;
   - mode 0600 not checked on read;
   - `screen_gaps` only falls on restart;
   - commit-path matching in the shim's queue check.
2. No release has been published, so `bin/RELEASE_URL` points at nothing yet. Every first run builds
   from source and needs Go.
3. bash 3.2 compliance is checked statically only; no macOS run.
4. The cache key is the version, not the commit. After a code change, use `WORKFLOW_BIN` or clear
   the cache.
5. Codex hook events carry an empty `--event`. The event comes from the payload's
   `hook_event_name`.
6. One legacy spool file under `~/.local/share/workflow-plugin/hooklog/spool` will never be drained.

## Phase 6 — Skills and templates

One unit, written inline as brief 230 (`6-01-skills-templates`) and committed in `225bd32`. It ran
alongside 5-05; their paths did not overlap.

### 6-01-skills-templates (execution 32)

- **Built:**
  - `design` and `refine` call `artifact_feedback(path)` after writing. A rejection is fixed first;
    a check flagged out of norm is addressed or named. `queued`, `unreachable` or `no config` is
    reported in one line.
  - The hook-backstop bullets are removed.
  - `execute` requires each worker's report at `docs/plans/<plan>/reports/<brief-name>.md`, with
    `tools/quality/checks/execution-report.json` as the rubric. The runner calls
    `artifact_feedback` on the reports and briefs before it closes a phase.
  - Commit titles are plain summaries.
  - The templates have no frontmatter.
- **Commit:** `1bd361c`.
- **Departures:** none. The before grep found 9 lines, not the brief's 11, because some lines hold
  more than one term. `comprehensive-review`, `close-out` and `post-build` needed no change.
- **Agent:** Sonnet, 5 tool calls, about 49k tokens.

### Phase 6 verification

The orchestrator checked the phase outcome against `skills/` and `plugins/`:

- The grep for `post_design`, `post_brief`, `patch_design`, `patch_brief`, `start_execution`,
  `patch_execution`, `complete_execution`, `design_id`, `brief_id` and `[exec` returns nothing
  (exit 1).
- `skills/execute/SKILL.md` line 16 names `artifact_feedback` and requires
  `docs/plans/<plan>/reports/<brief-name>.md`.
- There are 3 `Workflow-Phase` lines before and after.

The phase outcome holds.

This run kept logging to the legacy service and kept `[exec]` titles, so its dataset stays linked.
Later runs follow the new skills.

### Carried

1. Existing plans' briefs and designs keep their `brief_id` and `design_id` frontmatter as history.
2. The skills now rely on `artifact_feedback`. It answers `no config` until `workflow init` has been
   run and `serve` is enabled.
