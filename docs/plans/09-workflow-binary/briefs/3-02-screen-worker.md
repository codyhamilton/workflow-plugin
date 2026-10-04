---
brief_id: 221
design_id: 209
---

# Brief: 3-02 — Screen worker, store support and `serve` wiring

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. Its output closes phase 3; the
orchestrator verifies the phase outcome against `TestScreeningOutcome`. Phase 4's advisory reads
consume the `screens`, `scores` and `rejections` rows written here.
Owned paths: `tools/workflow/internal/screen/` (new), `tools/workflow/internal/store/`,
`tools/workflow/internal/serve/`, `tools/workflow/cmd/workflow/main.go` (the `serve` wiring), and
the test files under `tools/workflow/cmd/workflow/` (only to clear `TYPESAFE_API_KEY` in child
environments), `docs/plans/09-workflow-binary/reports/3-02-screen-worker.md` (new). Touch nothing
else; `internal/scorer` belongs to 3-01 (report gaps in it, do not edit it).
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 3-01 (`internal/scorer`: `Scorer`, `ErrUnreachable`, `Fake`, `LoadChecks`, `NewJev`).
Runs alongside: nothing.
Budget: 10 files to read, about 650 lines to write including tests, 70 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — Phase 3 (lines 190-201). Then
   `IMPLEMENTATION.md` Phase 1 Carried items 1-2 (lines 70-78), repeated as Phase 2 Carried 1-2.
2. `docs/design/03-remote-service.md` — Configuration (lines 49-63), Tables (lines 127-139),
   Screening and scoring (lines 147-177), Tests item 4 (line 213). Binding.
3. `docs/plans/09-workflow-binary/reports/3-01-scorer-checks.md` and `go doc ./internal/scorer` —
   the API you consume.
4. `tools/workflow/internal/store/store.go` — migrations (lines 23-45), pending and blob helpers,
   `Promote`, `DropPending`, `AppendScores` (lines 300-475).
5. `tools/workflow/internal/serve/serve.go` — `Options`, `ScreenFunc`, `unscreened`, `worker`,
   `drainPending`, `tenant` (lines 84-200), `health` (lines 286-300).
6. `tools/workflow/internal/ingest/ingest.go` — `Ingest` (lines 165-240): `WritePending` runs on
   every artifact fact, before `Append`, including a resend.
7. `tools/workflow/cmd/workflow/main.go` — `runServe` (lines 54-105).
8. `tools/workflow/internal/serve/serve_test.go` — `newServer`, `artBody`, `TestPending`: reuse.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

Replace the phase 1 "promote as unscreened" step with screening and scoring through the `Scorer`
when `TYPESAFE_API_KEY` is set, leave `unscreened` as the no-key mode, and close the two crash and
loss gaps phase 1 left in the pending path.

## Contract

Cited, binding (design 3, Screening and scoring): "A worker per tenant takes pending content in
arrival order and asks the scorer to screen it and, for artifact kinds with checks, score it.
Pass: the content moves to `blobs/`; a `screens` row and any `scores` rows are written. Flag: the
pending content is deleted; a `rejections` row records the hash and reason. The fact stays, with no
content behind it. Scorer unreachable: the content stays pending and the worker backs off. Pending
count shows in `health`." "No `TYPESAFE_API_KEY`: the screen verdict is `unscreened` and content
moves to `blobs/` after the precheck alone. This is the expected local mode without a scorer, and
the verdict says so in every read." Configuration: "`TYPESAFE_API_KEY` | scorer credential; server
side only, never in any client config". Design 1, Ingest contract: "Artifact kind (design, brief,
report) is inferred from path convention" (`keys.Kind`).

Carried, absorbed here: phase 1 item 1, "`Promote` moves the blob before writing the `screens` row.
A crash between the two leaves a blob with no screen row. Phase 3's screen worker must retry
anything not screened when it starts." Phase 1 item 2, "A resent artifact whose pending file was
lost while its ledger row survived returns `duplicate` and is never re-written. Phase 3 should treat
a fact whose content has neither a pending file nor a blob as a screen gap."

Decisions made at refine (settled):

- **Step** (`internal/screen`): `screen.Step(sc scorer.Scorer) func(ctx, *store.Tenant, hash string)
  error`, assignable to `serve.ScreenFunc` (screen must not import serve). For one hash: content is
  the pending file, else the blob (the carried-1 case); kinds are `keys.Kind` of the distinct paths
  of `artifact_version` facts with that content hash, empty kinds dropped. Then `sc.Screen`; on a
  flag, delete the content (pending or blob) and append a rejection `{Stage: "screen", Pattern:
  "jev_screen", Reason: verdict.Reason, FactType: "artifact_version", ContentHash, Path and
  ConversationID from the latest such fact}`; on a pass, `sc.Score` when kinds is non-empty, then
  promote with verdict `pass`, scorer `sc.Name()`, and the scores. Errors from the scorer are
  returned wrapped, so `errors.Is(err, scorer.ErrUnreachable)` holds.
- **Fact not yet committed**: `Ingest` writes pending before `Append` commits the fact, so the poll
  can see content whose fact is not in the ledger yet. If a pending hash has no fact row and its file
  is younger than 1 minute, skip it this pass (no error). Older than that, screen it with no kinds
  (an orphan from a failed append).
- **Atomic screen and scores**: extend `Promote` to `Promote(ctx, hash, s Screen, scores ...Score)`
  and write the `screens` row and its `scores` rows in one writer transaction, so a crash cannot
  leave a screen with half its scores. Existing callers compile unchanged. Scores take the screen's
  scorer name.
- **Store additions**: `ContentFacts(ctx, hash)` (distinct paths, plus the latest fact's
  conversation ID); `DropBlob(ctx, hash, Rejection)` (the flag path for carried item 1);
  `UnscreenedBlobs(ctx) ([]string, error)` (blobs on disk with no `screens` row); `ScreenGaps(ctx)
  (int, error)` (content hashes of `artifact_version` facts with no pending file, no blob and no
  `rejections` row); the pending file's mod time for the 1-minute rule. Names may differ; say so in
  the report. No schema migration is needed; if you add an index, append a migration, never edit the
  first.
- **Worker** (`serve`): on its first pass a tenant worker applies the step to `UnscreenedBlobs`
  (carried 1), then computes `ScreenGaps` once and keeps the count (carried 2); every pass then
  handles `PendingHashes` in order as now. An error wrapping `scorer.ErrUnreachable` ends the pass
  and the worker waits a backoff before the next pass, ignoring wakes: starts at
  `Options.ScreenBackoff` (default 5 s), doubles to 5 min, resets after a pass with no unreachable
  error. Other errors are logged for that hash and the pass continues. Log lines name the hash and a
  short cause, never content, key or response body.
- **Health**: keep `pending` as now; add `screen_gaps` (sum over open tenants of the count kept at
  worker start). Nothing else changes in `/v1/health` or `/v1/artifacts`.
- **Carried 2's premise**: from the code, `Ingest` calls `WritePending` for every artifact fact,
  duplicate or not, and `WritePending` writes when neither pending nor blob exists, so a resend
  does appear to re-create a lost pending file. Settle it with a test (resend after deleting the
  pending file) and report the result; the gap count covers the case with no resend either way.
  If the test shows the resend does not re-create it, the fix belongs in `ingest`, outside your
  paths: report it, do not fix it.
- **Wiring** (`cmd/workflow` `runServe`): read `TYPESAFE_API_KEY` (trimmed) and
  `WORKFLOW_CHECKS_DIR` (the directory holding `criteria.json` and `checks/`, i.e. `tools/quality`).
  No key: `Options.ScreenStep` stays nil (verdict `unscreened`); one stderr line `workflow serve:
  scorer none; verdicts are unscreened`. Key and a checks dir: `scorer.LoadChecks` (an error refuses
  to start, naming the file), `scorer.NewJev`, `screen.Step`; one line naming the scorer and check
  counts per kind. Key and no checks dir: screen only (no checks), with a line saying scoring is off
  because `WORKFLOW_CHECKS_DIR` is unset. The key is never logged, put in `Config`'s printed form, or
  written anywhere. `WORKFLOW_CHECKS_DIR` is a refine decision (design 3 lists server configuration
  as environment only; the binary may run from a cache, so it cannot find the files by itself).
- **Existing binary tests**: every test that starts the `workflow` binary or calls
  `serve.ConfigFromEnv` with the real environment must set `TYPESAFE_API_KEY=` (empty) in the child
  environment, so no test content reaches TypeSafe. This is the only change allowed in the
  `cmd/workflow` test files.

## Changes

`internal/screen` (new): the step and its tests. `internal/store`: `Promote` with scores, the
reads and `DropBlob` above, tests. `internal/serve`: start-up reconcile, backoff, `screen_gaps`,
and `screen_outcome_test.go` with `TestScreeningOutcome`. `cmd/workflow/main.go`: the wiring.
`cmd/workflow/*_test.go`: the empty `TYPESAFE_API_KEY` only.

### Keep untouched

The ingest path and precheck (`internal/ingest`), auth, `/v1/ingest` and `/v1/artifacts` response
shapes, the hosted drain (`host.go`, `watch_*.go`), and `Options.DisableWorker`/`StartWorker`
semantics: phases 1 and 2's tests must pass unchanged apart from the env line above.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after. Run
from `tools/workflow` with `export PATH=$HOME/.local/go/bin:$PATH`.

- `go vet ./... && go test -race ./...` → passes, including `TestServeOutcome` and
  `TestCaptureOutcome` (which now run with `TYPESAFE_API_KEY` empty and still see `unscreened`).
- `go test -v -run TestScreeningOutcome ./internal/serve` → a `Server` on `t.TempDir()` with a
  `scorer.Fake`, posting artifacts at `docs/plans/01-x/DESIGN.md` and
  `docs/plans/01-x/reports/1-01-a.md`. One subtest per outcome clause, printing pass/fail per line:
  1. **pending until screened**: worker disabled → content in `pending/`, no blob, health
     `pending` ≥ 1.
  2. **pass**: fake passes with scores → blob present, pending gone, one `screens` row (verdict
     `pass`, scorer `fake`), `scores` rows for that content; the fake saw kinds `["design"]` (and
     `["report"]` for the report).
  3. **flag**: fake flags → pending gone, no blob, a `rejections` row with stage `screen`, the
     content hash and the fake's reason; the `artifact_version` fact row still exists.
  4. **unreachable**: fake returns `ErrUnreachable` → content stays pending across at least two
     poll intervals, the fake is called no more than the backoff allows; switch the fake to pass →
     it is screened.
  5. **no key**: no scorer → verdict `unscreened`, blob present, no `scores` rows.
  6. **crash between blob and screen row** (carried 1): content placed in `blobs/` with no
     `screens` row before the tenant opens → after the worker starts it has a `screens` row; a flag
     verdict here removes the blob and records the rejection.
  7. **screen gap** (carried 2): a fact whose pending file is deleted with the worker disabled →
     on restart, health `screen_gaps` is 1; resending the same fact → pending re-created (or the
     test records that it is not; see the decision above) and, once screened, the gap clears on the
     next start.
  8. **report checks**: `scorer.LoadChecks("../../../quality")` has 5 `report` checks (3-01's file).
- A `cmd/workflow` check that `workflow serve` with `TYPESAFE_API_KEY` empty prints the `scorer
  none` line, and with a dummy key and a bad `WORKFLOW_CHECKS_DIR` (temp dir with broken JSON)
  refuses to start; neither output contains the dummy key. Use port `127.0.0.1:0`, never 8765 or
  8770. Do not start `serve` with the real key.

Safety: temp dirs only (`t.TempDir()`), with `WORKFLOW_SERVE_DATA`, `WORKFLOW_QUEUE`, `HOME` and
`WORKFLOW_CLIENT_CONFIG` set to temp paths for any binary run. Never touch `~/.local/share/workflow*`,
`~/.config/workflow` or the legacy spool. Any `serve` you start listens on a port other than 8765 or
8770 and is killed after (`t.Cleanup`); confirm none survive with `pgrep -f '<tempdir>'` before
reporting. `TYPESAFE_API_KEY` is in your environment: never print, log, echo or write it (no `env`,
`printenv`, `set -x`), never put it in a file or config, and no test of yours reads it. The live
Jev call belongs to 3-01; this unit makes none.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 3: screen worker and serve
wiring` (the orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/3-02-screen-worker.md` (design 1, Execution report: what was
done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), including the carried-2 test result and the `TestScreeningOutcome` lines, and include it
in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
