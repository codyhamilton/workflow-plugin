---
brief_id: 240
design_id: 209
---

# Remediation 51: without flock(1) (macOS), every hook spawns a drain while `serve` holds the lock

Severity: medium. Source: client-side review (`review-client.md`).
Owned paths: `tools/hooklog/spool.sh`, `tools/hooklog/tests/`, and the lock-holder code in
`tools/workflow/internal/drain/drain.go` if the pid-file approach is chosen.

## Defect

`spool.sh` `kick()` has two paths. With `flock(1)` it probes `.drain.lock` and starts nothing when
the lock is held. Without `flock(1)` (stock macOS, or `WORKFLOW_SPOOL_NOFLOCK=1`) it uses a mkdir
lock under `<queue>/.kick.d` holding the pid of the drain *it* started. It never looks at
`.drain.lock`.

When the lock is held by a process the kick did not start (a hosted drain in `workflow serve`, or a
drain started by the MCP shim or OpenCode plugin), `.kick.d/pid` names a dead process or is absent.
Each hook then removes the stale lock and starts `bin/workflow drain`, which fails to take the
flock and exits.

## Why it matters

The phase 2 outcome in DESIGN.md says "while a local `serve` holds the lock, spools start no
drain". On darwin that is false: each hook event forks a detached bash wrapper plus a Go process.
Nothing is lost or duplicated, because the drain's flock(2) is still the singleton, so this is
waste and a broken stated outcome rather than a correctness defect. It also hides a regression
the Linux tests cannot see, since they take the flock path unless forced.

## Fix approach

Preferred: have the drain write its pid to `<queue>/.drain.pid` after taking the flock (hosted and
standalone) and remove it on release. In the mkdir path, `kick()` first reads `.drain.pid` and
returns if `kill -0` succeeds. A stale pid file is harmless because the spawned drain still
flocks.

Alternative: probe `.drain.lock` with perl, which ships with macOS:
`perl -MFcntl=:flock -e 'open F,"<",shift or exit 0; exit(flock(F,LOCK_EX|LOCK_NB)?0:1)' "$dir/.drain.lock"`.
Keep it bash 3.2 compatible and under the hook's time budget.

## Done evidence

- A hooklog test with `WORKFLOW_SPOOL_NOFLOCK=1`: a held `.drain.lock` (from a helper process, or
  a Go hosted drain in a temp queue) plus N spool calls start zero drains. Count with a stub
  `WORKFLOW_BIN` that records invocations. The event files must still be present for the holder.
- The existing concurrent-spool and kick tests still pass on both paths.
- `python3 -m unittest discover -s tools/hooklog/tests` and `go test -race ./...` in `tools/workflow` pass.
