---
brief_id: 226
design_id: 209
---

# Brief: 5-02 — `bin/workflow` wrapper and release build

Consumer: a Sonnet worker dispatched by the plan 09 orchestrator. 5-03's spool kick, 5-04's
OpenCode kick and 5-05's configs and MCP registration all invoke `bin/workflow`.
Owned paths: new `bin/workflow` (mode 0755), new `bin/VERSION`, new `bin/RELEASE_URL`, new
`bin/SHA256SUMS`, new `tools/release/build.sh` (0755), new `tools/release/test_release.py`,
`.gitignore` (one added line), `docs/plans/09-workflow-binary/reports/5-02-wrapper-release.md`
(new). Touch nothing else; not `tools/workflow/` (5-01 owns `--version`; a defect there is
reported), not `tools/hooklog/`.
Commits: Commit to the current branch (`hooks-reconcile`) when done evidence passes. Never push.
Depends on: 5-01 (the `workflow <version> <commit>` line), committed. Read its report first.
Runs alongside: 5-03, 5-04 (disjoint paths).
Budget: 5 files to read, about 300 lines to write including tests, 45 tool turns. Past the budget,
stop: write a handoff under this brief's name in `docs/plans/09-workflow-binary/IMPLEMENTATION.md`
(done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/09-workflow-binary/DESIGN.md` — the Phase 5 section (grep `### Phase 5`): the
   outcome and the Units decisions.
2. `docs/design/05-distribution.md` — Layout (lines 11-22), Wrapper (lines 24-46), Release
   (lines 62-66).
3. `docs/plans/09-workflow-binary/reports/5-01-version-init.md` — the section on `--version` and
   the `WORKFLOW_ROOT` requirement of `init`.
4. `tools/workflow/go.mod` — lines 1-3: module path and go version.

Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in
context, and truncate long tool output.

## Goal

When this unit is done, `bin/workflow` resolves a binary for this machine (override, cache,
verified download, or a locked source build), and `tools/release/build.sh` produces the four
release binaries and their checksums.

## Contract

Cited, binding (design 5, Wrapper): the five steps in order; "Constraints: bash 3.2 compatible
(macOS), no `flock`, concurrent first runs safe because the final step is an atomic rename."
(Release): "cross-compiles with `CGO_ENABLED=0` and writes `bin/SHA256SUMS`. Publishing the release
… happens only with the maintainer's agreement." DESIGN.md Phase 5 outcome: "`bin/workflow
--version` prints `workflow <version> <commit>` from a clean temp cache by building from source,
and two concurrent first runs both succeed; `tools/release/build.sh` produces four binaries and
`bin/SHA256SUMS`".

Decisions made at refine (settled):

- **Files.** `bin/VERSION` = `0.1.0`. `bin/RELEASE_URL` =
  `https://github.com/codyhamilton/workflow-plugin/releases/download`. `bin/SHA256SUMS` is the
  output of `build.sh` at this commit, committed (no release exists yet, so downloads 404 and step
  4 is the working path). `.gitignore` gains `tools/release/dist/`.
- **Wrapper, bash 3.2.** No `[[ -v ]]`, `${x,,}`, `mapfile`, `read -N`, associative arrays,
  `EPOCHREALTIME` or `flock`. Root is the parent of the script's own directory (resolve through
  `cd "$(dirname "$0")/.." && pwd -P`); export `WORKFLOW_ROOT` before `exec` (5-01's `init` needs
  it). os from `uname -s` lowercased with `tr` (`linux`, `darwin`, else step 5); arch from `uname
  -m`: `x86_64|amd64` → `amd64`, `arm64|aarch64` → `arm64`, else step 5.
- **Order.**
  1. `WORKFLOW_BIN` set and executable → `exec "$WORKFLOW_BIN" "$@"`.
  2. `CACHE=${XDG_CACHE_HOME:-$HOME/.cache}/workflow/<VERSION>`; `$CACHE/workflow-<os>-<arch>`
     executable → exec.
  3. Download, only when `bin/SHA256SUMS` has a line for `workflow-<os>-<arch>` and no build lock
     is held: `curl -fsSL --max-time 60` (else `wget -q -T 60 -O`) from
     `${WORKFLOW_RELEASE_URL:-$(cat bin/RELEASE_URL)}/v<VERSION>/workflow-<os>-<arch>` into
     `$CACHE/tmp.$$`; hash with `sha256sum` (else `shasum -a 256`); a mismatch prints `checksum
     mismatch` on stderr, deletes the temp file and falls through to step 4; a match → chmod 0755,
     `mv` onto the final name, exec. `WORKFLOW_RELEASE_URL` exists for tests (`file://`).
  4. Build: `go` from `PATH`, else the first executable of `$HOME/.local/go/bin/go`,
     `/usr/local/go/bin/go`, `/opt/homebrew/bin/go`; and `<root>/tools/workflow/go.mod` present.
     Take the lock; build with `CGO_ENABLED=0 GOTOOLCHAIN=local go build -trimpath -ldflags "-X
     main.version=<VERSION> -X main.commit=<git -C root rev-parse --short=12 HEAD, else unknown>"
     -o "$CACHE/tmp.$$" ./cmd/workflow` (run in `tools/workflow`; existing `GOCACHE`/`GOMODCACHE`
     respected); `mv` onto the final name; release the lock; exec.
  5. Otherwise print why (`no release asset and no Go toolchain`, unsupported platform, build
     failed) on stderr, exit 1.
- **Build lock.** `mkdir "$CACHE/.build.lock"` and write `$$` into `.build.lock/pid`. A caller that
  fails `mkdir` waits: polls every 0.5 s (`sleep 0.5`) up to 300 s for the final binary to appear
  (then exec it). The lock is stale if its pid is not alive (`kill -0`) or the directory is older
  than 10 minutes (`find … -maxdepth 0 -mmin +10`); a stale lock is removed and retaken once. A
  `trap` removes the lock and temp file on exit of the holder. After acquiring, re-check the final
  binary (another caller may have finished).
- **Known limit (record, do not fix):** the cache key is the version, not the commit; after a code
  change a developer sets `WORKFLOW_BIN` or clears the cache.
- **build.sh.** `set -eu`; from the repo root, for linux/darwin × amd64/arm64: `CGO_ENABLED=0
  GOOS GOARCH GOTOOLCHAIN=local go build -trimpath` with the same ldflags into
  `${OUT_DIR:-tools/release/dist}/workflow-<os>-<arch>`; then writes `<hash>  workflow-<os>-<arch>`
  lines sorted to `${SUMS_FILE:-bin/SHA256SUMS}`. Finds `go` like the wrapper. It never uploads.

## Changes

The files above. `test_release.py` (unittest, stdlib only) drives the wrapper and `build.sh` in
temp dirs.

### Keep untouched

`tools/workflow/` and every hook config: the wrapper is called by them in later units, not wired
here.

## Done evidence

Identify or write the failing check before changing code. Report its output before and after.

Fail first: write `test_release.py` first and quote its failure (no `bin/workflow`).

- `python3 -m unittest tools/release/test_release.py -v` → passes, with one test per item; every
  run sets `HOME` and `XDG_CACHE_HOME` to temp dirs, `PATH` with `$HOME/.local/go/bin` prepended
  only where a build is wanted, and passes the real `GOCACHE`/`GOMODCACHE` (from `go env`) so
  builds stay fast:
  1. **clean cache build**: `bin/workflow --version` → `workflow 0.1.0 <12-hex commit>`; the binary
     is at `<cache>/workflow/0.1.0/workflow-linux-amd64` (or this machine's arch); a second call
     does not rebuild (mtime unchanged).
  2. **two concurrent first runs**: two `--version` processes started together on an empty cache
     both exit 0 with the same line; no `tmp.*` or `.build.lock` remains.
  3. **stale lock**: a `.build.lock` holding a dead pid → the run succeeds.
  4. **file:// download**: a temp dir laid out as `v0.1.0/workflow-<os>-<arch>` (a copy of a
     built binary) and a temp `SHA256SUMS` matching it (copy `bin/` into a temp root to do this
     without editing the real one), `WORKFLOW_RELEASE_URL=file://…`, `PATH` without Go → runs
     from the download.
  5. **mismatch**: same with one byte flipped → stderr has `checksum mismatch`, the bad file is not
     in the cache, and without Go the exit is non-zero.
  6. **no Go, no asset** → non-zero with the reason on stderr.
  7. **build.sh**: `OUT_DIR` and `SUMS_FILE` in temp → four files, four sum lines that `sha256sum
     -c` accepts in `OUT_DIR`; `file` (or the ELF/Mach-O magic bytes) shows each target.
  8. **bash 3.2 lint**: a grep of `bin/workflow` for `read -N`, `mapfile`, `,,}`, `EPOCHREALTIME`,
     `flock`, `[[ -v` finds nothing (static; no bash 3.2 is available here).
- `bash tools/release/build.sh` with the default paths → `bin/SHA256SUMS` written; commit it. The
  dist directory is ignored.
- `grep -n 'github.com' tools/release/test_release.py` → no output: every download test uses
  `file://` and no test contacts GitHub.

Safety: temp dirs only. Never touch `~/.cache/workflow`, `~/.config/workflow` or
`~/.local/share/workflow*`. Never publish a release or push a tag. `TYPESAFE_API_KEY=` blank in
every child; never print it.

Commit: stage only your owned paths. Title `[exec <execution_id>] Phase 5: wrapper and release
build` (the orchestrator supplies the id; if none, `[exec none]`), ending with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KDbByM7cBGapWeFDD5wRAp
```

Execution report: before committing, write
`docs/plans/09-workflow-binary/reports/5-02-wrapper-release.md` (design 1, Execution report: what
was done against this brief, verifiably; departures and why; unfinished work; known problems; nothing
derivable), with the test lines and the cold-build time, and include it in the commit.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why, and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
