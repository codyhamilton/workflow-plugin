# Report: 2-02 — Archive tolerates and repairs a torn last frame

Status: done

## What changed
- `tools/workflow/internal/archive/archive.go`: `readFile` now decodes a file whole, and on any failure re-decodes it frame by frame (`splitFrames`, `linesOf`). A torn frame (a truncated frame that yields `io.ErrUnexpectedEOF`) is tolerated: the frames before it are delivered and `Read` returns no error; a checksum-corrupt frame, trailing garbage or a complete non-JSON line still returns an error naming the file. New `Repair(tenantDir) (Repaired, error)` (takes the package mutex) walks every `<tenantDir>/archive/*/*.jsonl.zst`, drops torn frames, and atomically rewrites (temp file in the same dir, fsync, rename) a file as one fresh zstd frame of exactly the surviving lines in order, duplicates kept. `Repaired{Files, Lines}` reports files fixed and complete lines dropped. A healthy file is never rewritten (mtime unchanged). `Append` is unchanged and does not call `Repair`.
- `tools/workflow/internal/archive/archive_test.go`: `truncate` helper and four tests (torn-last-frame tolerance; torn-then-appended recovery via `Repair`; healthy file untouched byte- and mtime-identical plus a later append/read; mid-file corruption still errors).
- Written before the code change and included in the same commit as the code: this report.

## Check output
Before (Step 1, new check against unchanged code):
```
=== RUN   TestReadToleratesTornLastFrame
    archive_test.go:231: Read errored on a torn tail: archive: /tmp/TestReadToleratesTornLastFrame1277116989/001/archive/2023-11/c.jsonl.zst: unexpected EOF
--- FAIL: TestReadToleratesTornLastFrame (0.00s)
```
After (Step 4):
```
ok  	github.com/codyhamilton/workflow-plugin/tools/workflow/internal/archive	1.685s
```
`gofmt -l internal/archive/archive.go internal/archive/archive_test.go` printed nothing (exit 0); `go vet ./internal/archive/` printed nothing (exit 0).

## Departures
- The brief's Contract says "corruption followed by good data" is an error, while its Done-evidence test says that after a torn tail a later `Append`'s frame must be recovered by `Repair` with `Read` returning the lines before the tear. These can only both hold if a *truncated* frame is treated as a torn tail even when a good frame follows it, and a *checksum-corrupt* frame is treated as corruption. That is what this unit implements (isolation is what makes the two distinguishable). Named rather than resolved silently.
- `Repaired.Lines` counts complete JSON lines that decoded from a torn frame and were then dropped; a torn fragment that decodes no complete line contributes 0 (as in the torn-then-appended test, where the torn frame's single line is unrecoverable and `Repaired.Lines` is 0).

## Contradictions
- The contract-vs-test tension named above is the cited contradiction: the contract calls "corruption followed by good data" an error, but the done-evidence requires a torn frame followed by a good frame to be recovered by `Repair` (and not surfaced by `Read`). Resolved by distinguishing truncated frames (torn) from checksum-corrupt frames (corruption) via per-frame isolation.

## Known limits and residual risk
- Until `Repair` runs, a frame appended after a torn tail is not surfaced by `Read` (Read stops at the tear). `Repair` before compaction is how it is recovered; the brief anticipated this residual risk.
- `splitFrames` locates frames by the zstd magic and is used only on files that already failed a whole-stream decode. A compressed payload that happened to contain the magic byte sequence could in principle mis-split a damaged file; the payload is JSON text and the risk is negligible, but it is not zero.
- `Repair` leaves a file it cannot safely repair (a checksum-corrupt frame that is not torn) untouched and returns the error.

## Unfinished
- None in this unit. Phase 2 unit 2-03 (compaction engine) should call `Repair` before reading/compacting.
