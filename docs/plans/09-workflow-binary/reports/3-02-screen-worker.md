# Report: 3-02 screen worker, store support and serve wiring (exec 23)

## Done against the brief
- New `internal/screen`: `Step(sc)` assignable to `serve.ScreenFunc`; content from pending else blob; kinds from `keys.Kind` of the distinct artifact_version paths; flag drops content (pending via `DropPending`, blob via `DropBlob`) with a `screen`/`jev_screen` rejection; pass scores when kinds exist, then `Promote`. Scorer errors are wrapped (`errors.Is(err, scorer.ErrUnreachable)` holds). A pending hash with no fact row and a file under 1 minute old is skipped; older is screened with no kinds.
- `internal/store`: `Promote(ctx, hash, s, scores...)` writes the screen and scores in one transaction (scorer name from the screen); new `DropBlob`, `ContentFacts` (returns `ContentInfo{Paths, LatestPath, ConversationID}`), `UnscreenedBlobs`, `ScreenGaps`, `PendingModTime`, plus `HasPending` and `PendingPath` (test helpers). No migration.
- `internal/serve`: `Options.ScreenBackoff` (default 5 s, doubles to 5 min, resets on a clean pass, wakes ignored while backing off). First pass: gap count (kept per tenant), then `UnscreenedBlobs` through the step; retried if the scorer was unreachable. `/v1/health` gains `screen_gaps`.
- `cmd/workflow/main.go`: `TYPESAFE_API_KEY` and `WORKFLOW_CHECKS_DIR` wiring with the three stderr lines; bad checks refuse to start naming the file; the key is never printed. `main_test.go` sets `TYPESAFE_API_KEY=`; `drain_test.go`/`capture_test.go` already do via `e.base`. New `screen_wiring_test.go` (kept to its own file) covers the wiring.

## Evidence
- Fail first: the tests were written after the code in this unit, so there is no red run to quote (honest departure). Before the unit, `Promote` took no scores and `screen_gaps` was absent, so `TestScreeningOutcome` could not compile.
- `go vet ./... && go test -race ./...` passes, every package, including `TestServeOutcome` and `TestCaptureOutcome`.
- `TestScreeningOutcome` lines:
```
    screen_outcome_test.go:260: carried 2: resend returned duplicate; pending or blob re-created = true
    --- PASS: TestScreeningOutcome/pending_until_screened (0.02s)
    --- PASS: TestScreeningOutcome/pass (0.06s)
    --- PASS: TestScreeningOutcome/pass_kinds (0.05s)
    --- PASS: TestScreeningOutcome/flag (0.06s)
    --- PASS: TestScreeningOutcome/unreachable (0.94s)
    --- PASS: TestScreeningOutcome/no_key (0.03s)
    --- PASS: TestScreeningOutcome/crash_between_blob_and_screen_row (0.10s)
    --- PASS: TestScreeningOutcome/screen_gap (0.27s)
    --- PASS: TestScreeningOutcome/report_checks (0.00s)
```
- Carried 2 settled: a resend after deleting the pending file returns `duplicate` and the pending file is re-created (WritePending runs before Append). No ingest fix needed. The gap count still covers the no-resend case; it was 1 before the resend and 0 after restart once screened.
- Unreachable subtest: backoff 300 ms, poll 30 ms; over 700 ms the scorer was called 1 to 3 times, content stayed pending, then screened after switching to pass.
- No processes left (`pgrep` clean). No real Jev call made; tests use a fake scorer and empty/dummy keys in children.

## Departures
- Names: `ContentFacts` returns a struct, not (paths, conv). Test-only exports `HasPending`, `PendingPath` added to store.
- `TestScreeningOutcome` has an extra "pass kinds" subtest (fake records kinds `["design"]`/`["report"]`), because the pass subtest uses a switchable wrapper scorer.

## Unfinished / known problems
- `screen_gaps` is counted once at worker start, as the brief says; it does not update when a gap is later cleared until restart.
- An unreachable scorer during the blob reconcile blocks the pending pass until the backoff ends (the pass is skipped, then retried).
- No dedicated store unit tests; the new store methods are exercised through the serve and screen tests.
