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
