# Report: 1-01 — Event archive package

Status: done

## What changed
- New `tools/workflow/internal/archive/archive.go`: `Line`, `Entry`, `Append(tenantDir, entries)`, `Read(tenantDir, conversationID)` with the names and signatures from the brief.
- New `archive_test.go` (6 tests); `go.mod`/`go.sum` gain `github.com/klauspost/compress v1.20.1`.
- Append groups entries by (UTC month of `TS`, conversation), writes one zstd frame per file with `O_APPEND` (files 0600, dirs 0700), fsyncs, all under a package mutex. Existing files are never rewritten.
- File name: bytes outside `[A-Za-z0-9._-]` and a leading `.` become `%XX`; the empty ID maps to `%` (unambiguous, since a literal `%` is always escaped to `%25`). Same function in Append and Read.
- Read globs `archive/????-??/<name>`, decodes concatenated frames, dedups by `row_hash` (first wins), stable-sorts by the fact's `ts` (parsed from `fact.ts`), so arrival order breaks ties. No archive gives an empty non-nil slice and nil error.

## Evidence
- Before: `go test ./internal/archive/` failed to compile (`undefined: Entry, Line, Append, Read`).
- After: `go test -race ./internal/archive/` passes. The tests cover:
  - two Appends decoded by the system `zstd -dc` in order, plus file mode 0600;
  - a month boundary (2026-01-31 23:59:59 and the next second land in `2026-01` and `2026-02`);
  - dedup and ordering;
  - the missing-conversation case;
  - hostile IDs (`../x`, `a/b`, `.hidden`, empty, `..`, `%`, `a%2Fb`, backslash, NUL), which stay inside `archive/`, produce no hidden files or collisions, and round-trip;
  - 8 goroutines x 20 appends, 160 lines read back with no torn lines.
- `go build ./...` and `go vet ./internal/archive/` are clean.

## Departures
None. Note the first test draft failed on its own fixtures (invalid JSON from `%q`, a walk that included the root); both were test bugs, fixed.

## Known limits / unfinished
- Cross-process locking is not done (Phase 2 owns it). A crash mid-write could leave a torn final frame; Read then returns a decode error for that conversation rather than skipping it. Unit 1-05 should decide whether it wants tolerance.
- `Read` takes ordering from `fact.ts` and treats a missing `ts` as 0.
- Nothing is wired to any caller (unit 1-05).
