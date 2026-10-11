# 3-16 — Compaction keeps the hourly rollup exact

Status: **done**

## What changed

- `internal/store/rollup.go`: new exported `RebuildHookRollup(ctx)` — one transaction that
  `DELETE`s all `hook_events_hourly` rows and refills from the base `hook_event` rows. Hoisted the
  fill SQL to `hookRollupFill` and the column guard to `rollupFillApplies`, shared with
  `backfillHookRollup` (behaviour unchanged: still no-op when `facts` predates the columns).
- `internal/compact/compact.go`: `Run` now takes named returns and defers
  `t.RebuildHookRollup(ctx)` when `err == nil`, so every finished run — normal, resumed, or a
  no-op ("already complete") run — rebuilds the rollup once at the end. A run that stops on an
  error does not rebuild; the next run does. Per-batch maintenance was not added.
- `internal/compact/rollup_test.go` (new): `TestCompactRebuildsRollup` appends removable
  (opencode `chat.params`) and collapsible (`message.part.delta`) hooks plus kept rows, runs
  `compact.Run`, and asserts `hook_events_hourly` equals the base-row aggregate via `EXCEPT` in
  both directions. `TestCompactRebuildsRollupOnResume` stops after the first committed batch
  (`AfterCommit` → `errStop`), asserts the rollup is genuinely drifted, resumes with `Run`, and
  asserts exactness again.
- `internal/store/rollup_test.go`: `TestRebuildHookRollup` deletes base rows behind the rollup's
  back and asserts the exported helper restores the exact aggregate (both directions).

## Done evidence

- `go test ./internal/store ./internal/compact ./internal/serve` → `ok` for all three.
- `go vet` on the same three packages → exit 0.
- `gofmt -l` on the four changed/added Go files → empty.
- Targeted: `TestCompactRebuildsRollup`, `TestCompactRebuildsRollupOnResume`, `TestRebuildHookRollup`
  all PASS.

## Deviations

- The brief said "add an exported rebuild helper beside `backfillHookRollup`"; I also refactored
  `backfillHookRollup` to share the fill SQL and column guard with it instead of duplicating them.
  Its observable behaviour (skip when columns absent; delete+refill) is unchanged.
- `RebuildHookRollup` uses `t.wdb` directly (like `backfillHookRollup`) rather than the writer
  queue, since its only caller is offline compaction, which owns the exclusive lock and `Raw`.

## Contradictions between the brief and cited contracts

None found. The 3-12 "Concern" (compaction drifts the rollup) is exactly what this brief settles;
nothing in the brief conflicts with 3-12's rollup key or `Append` behaviour, both left unchanged.

## Known problems / unfinished

- Rebuild is a full-table aggregate: correct but O(base hook_event rows) per compaction. Fine for
  the offline path; no incremental maintenance was added (brief: "Do not maintain it per batch").
- The related 3-12 "unrepaired v6" note (backfill's `from < 6` gate commits separately from
  `migrate`'s `user_version = 6`) is untouched — out of this brief's owned paths.
