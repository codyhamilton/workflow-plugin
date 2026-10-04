# Execution report: 5-02 wrapper and release build (brief 226, exec 30)

## Done
- `bin/workflow` (0755, bash 3.2 style): override, cache, checksummed download, locked source build, else stderr + exit 1; exports `WORKFLOW_ROOT`.
- `bin/VERSION` (0.1.0), `bin/RELEASE_URL`, `bin/SHA256SUMS` (output of `bash tools/release/build.sh`).
- `tools/release/build.sh` (0755): four CGO_ENABLED=0 targets, sorted sums, `OUT_DIR`/`SUMS_FILE` overrides; never uploads.
- `tools/release/test_release.py`: 10 tests (the 8 briefed, plus Go probe of `$HOME/.local/go/bin` with Go off PATH, and `WORKFLOW_BIN`).
- `.gitignore`: `tools/release/dist/`.

## Evidence
- Before: all tests failed (no `bin/workflow`; `bash: .../bin/workflow: No such file or directory`, 8 failures, 2 errors).
- After: `python3 -m unittest tools/release/test_release.py -v` -> Ran 10 tests, OK (6.7 s).
- Cold-build time with warm GOCACHE: about 0.5 s (a truly cold Go cache was not measured).
- `grep -n github.com tools/release/test_release.py` -> no output.

## Departures
- Lock wait loop retakes a stale lock repeatedly rather than strictly once; the lock-less pid window is covered by treating a missing pid file as non-stale until the 10-minute age.
- The test-8 lint initially tripped on the word "flock" in a wrapper comment; the comment was reworded.

## Known problems
- Cache key is the version, not the commit (as briefed): after a code change use `WORKFLOW_BIN` or clear the cache.
- Two waiters that both see a stale lock can race on `rm -rf`; worst case is a duplicate build, still safe via atomic rename.
