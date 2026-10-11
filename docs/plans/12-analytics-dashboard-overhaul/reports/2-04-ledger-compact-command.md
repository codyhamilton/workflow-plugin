# Report: 2-04 — `workflow ledger compact` command

Status: **done**

## What changed

- `tools/workflow/internal/compact/finish.go` (new): `FreeBytes` — a package variable wrapping
  `syscall.Statfs` on the tenant dir, so tests can fake it — and `NeedBytes(t)` =
  (`SUM(length(raw))` over `hook_event`) / 3 (archive) + `max(ledger.db size − hook payload,
  64 MiB)` + 256 MiB WAL headroom.
- `tools/workflow/cmd/workflow/ledger.go` (new): `runLedger` accepts only
  `ledger compact --tenant-dir <dir>` (a `flag.FlagSet`; any other shape prints `usage` and exits
  2). `compactTenant` opens exclusive (`ErrLocked` → exit 1), prints before counts/bytes, prints
  `need X MiB, have Y MiB` and refuses (exit 1) when free < need, runs `compact.Run` with stdout
  progress under a SIGINT/SIGTERM context (interrupted at a batch boundary → exit 1 with the resume
  message), runs `VACUUM` then `PRAGMA wal_checkpoint(TRUNCATE)`, prints after counts/bytes plus
  elapsed, exit 0. When meta is already `complete` it skips the check and the run and goes straight
  to VACUUM. Output is counts and sizes only; `newCompactSession` is the package-level seam tests
  use for the context and `compact.Options`.
- `tools/workflow/cmd/workflow/main.go` (edit): added the `ledger` case; the `usage` string now
  lists `ledger compact --tenant-dir <dir>`. Nothing else touched.
- `tools/workflow/internal/compact/finish_test.go` (new): exact `NeedBytes` estimate, requires an
  exclusive tenant, `FreeBytes` > 0.
- `tools/workflow/cmd/workflow/ledger_test.go` (new): success path (before/after rows and bytes,
  after counts smaller and removed-event rows gone), missing `--tenant-dir` / bare `ledger` / extra
  arg → exit 2, locked → exit 1 unchanged, faked low free space → exit 1 unchanged, interrupt then
  resume yields the same facts as an uninterrupted run, rerun on a completed ledger → exit 0. Builds
  a small legacy ledger in `t.TempDir()` by copying 2-03's helper.

## Check output, before and after

Before: the check is new. `workflow ledger compact` did not exist, `go test ./cmd/workflow/ -run
Ledger` and `go test ./internal/compact/ -run Finish` matched no tests, and bare `workflow ledger`
printed the old usage (`serve | drain | mcp | status | version`).

After:

- `go test ./cmd/workflow/ -run Ledger -v` → all 6 PASS; `ok ... cmd/workflow`.
- `go test ./internal/compact/ -run Finish -v` → all 3 PASS; `ok ... internal/compact`.
- `go build ./... && go vet ./... && go test ./...` → build and vet clean; every package `ok`, no
  FAIL (cmd/workflow 51.988s).
- `gofmt -l cmd/workflow internal/compact` → no output.
- Binary with no args and with `ledger` alone both print
  `usage: workflow serve | drain | ledger compact --tenant-dir <dir> | mcp | status | version` and
  exit 2.

## Deviations from the brief

1. Test-only, in `ledger_test.go`: `buildLegacyLedger` clears the `compaction` and `compact_cursor`
   meta keys after inserting the fixture. Copying 2-03's `insertLegacy` verbatim leaves the ledger
   with `compaction='complete'` (opening a *fresh empty* dir runs migration 5, which seeds
   `complete` for an empty ledger; the later inserts do not clear it). The command then correctly
   follows the brief ("skip the check and the run") and changes nothing. A real pre-Phase-2 ledger —
   rows present before migration 5 runs — has no such key and reads `required`, which is the state
   the brief means to exercise. The command code is unchanged and follows the brief literally.
2. Otherwise none.

## Contradiction between the brief and the contracts it cites

The brief's step 3 says to skip when meta is `complete`. `compact.Run` (2-03) does not skip in that
state: it re-runs when meta says complete but `hook_event` rows still carry a payload. So a ledger
with `compaction='complete'` *and* un-compacted payload rows would be repaired by the engine but
skipped by the command. I did not resolve this silently: I followed the brief. It is not reachable
on a genuine ledger (migration seeds `complete` only for an empty ledger, and an empty ledger has no
payload rows), so there is no practical conflict — but the brief's advice to reuse 2-03's ledger
helper is what surfaced it.

## Unfinished work

None in this unit's scope. Phase 2 continues in 2-05 (kickoff on a copy) and 2-06 (verify the copy),
neither of which depends on anything left open here.

## Known problems

No non-trivial bug found outside the done evidence. Two limitations are known and left as
specified, plus one fix applied after independent review:

- A non-existent `--tenant-dir` is created and migrated by `store.OpenExclusive` (step 1 of the
  brief), so a typo'd path prints `rows=0` and exits 0 rather than failing. Not changed, because
  the brief's step 1 mandates `OpenExclusive`; an existence check would be a deviation.
- `fileSize`/`dirBytes` treat a `stat`/`WalkDir` error as 0, so an unreadable `ledger.db` or
  `archive/` would report a plausible `0` with no diagnostic. Counts and the compaction itself are
  unaffected.
- Applied after review: `compactTenant` now reports "interrupted" only when `Run`'s error is
  genuinely context cancellation, so a real failure concurrent with a signal is not masked.
