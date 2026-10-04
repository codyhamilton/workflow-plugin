# Plan 09 review: client, edge and distribution side

Reviewer lens: hooks, spool, kick, drain, facts, client config, the MCP shim, the wrapper and
release, per-harness configs and skills. The diff reviewed is `5726cc3^..HEAD`, restricted to
`tools/hooklog/`, `tools/workflow/internal/{drain,mcp,facts,clientconfig}`, `cmd/workflow`,
`bin/`, `tools/release/`, `packages/opencode-workflow-hooks/`, `hooks/`, `.mcp.json` and `skills/`.
It is held against DESIGN.md (phases 2, 4 shim, 5 and 6), designs 02, 04 and 05, IMPLEMENTATION.md
and `reports/`. Carried items in IMPLEMENTATION.md are not re-reported unless worse than recorded.

Verdict for this side: **PASS_WITH_FOLLOWUPS**. One fix was committed and one medium finding is
briefed. No blocker or high finding.

## Evidence run

All suites were run in `mktemp -d` dirs under `$HOME`, with `HOME`, `XDG_CACHE_HOME`,
`WORKFLOW_QUEUE`, `TMPDIR` and `GOTMPDIR` set to temp paths.

| Suite | Result |
|---|---|
| `python3 -m unittest discover -s tools/hooklog/tests` | 34 tests OK |
| `python3 -m unittest tools/release/test_release.py` | OK |
| `node --test packages/opencode-workflow-hooks/tests/test_hooks.mjs` | 6 pass |
| `go test -race -count=1 ./...` in `tools/workflow` | all packages ok, before and after the fix in 97dcd72 |

Direct probes:

- `spool.sh` takes about 20 ms per small event.
- A 3.2 MB payload whose `session_id` appears only after 64 KiB is dropped in 28 ms. The hook
  exits 0 and nothing is kicked.
- Every hook command exits 0 on all paths, including a missing binary and an unwritable queue.
- Codex's timeout of 3 s holds, because `spool.sh` never waits on the drain.

## Phase outcome assessment

| Phase | Assessment | Evidence |
|---|---|---|
| 2: spool, kick, drain, facts (client side) | **Partial on darwin; met on Linux** | 20 concurrent spools are delivered exactly once with one lock holder (hooklog and drain tests). 413 splits in halves, and a single file goes to `rejected/` with a `.reason`. Files are deleted only after a 200 whose results parse. Secret reasons carry a pattern and line, never the secret. The flock-path idle race (release, then rescan) is sound. The outcome "while serve holds the lock spools start no drain" fails on the mkdir path; see remediation 51. |
| 4: MCP shim | **Met** | Three tools over stdio JSON-RPC, with stdout kept clean (wrapper build output goes to stderr). `artifact_feedback` states are covered by tests: queued, no config, rejected, superseded, stale and not delivered. It uses a 3 s HTTP timeout and waits up to 1.5 s for the drain. |
| 5: distribution and retirement | **Met, with the Carried release gap** | The wrapper's order is `WORKFLOW_BIN`, then the cache, then a checksummed download, then a source build under a mkdir lock with an atomic `mv`. A checksum mismatch is refused and falls back to the build. Concurrent first runs are tested. BSD `date`, `head` and `find` usage is portable. All four harness configs register `spool.sh` and drop `artifact_submit.py`. `.mcp.json` registers the stdio shim. The HTTP registration for 8765 is gone. Nothing is published at `RELEASE_URL`, so every first run builds (Carried). |
| 6: skills on the advisory surface | **Met** | The design, refine and execute skills and the brief template now call `artifact_feedback(path)` and report `queued`, `unreachable` or `no config` in one line. `post_brief`, `post_design` and ID-in-frontmatter instructions are removed. A grep finds no `artifact_submit` or `8765` references left in `skills/`. |

## Findings

### Blocker

None.

### High

None.

### Medium

1. **macOS kick spawns a drain per hook while `serve` holds the lock.** In `tools/hooklog/spool.sh`
   `kick()`, the no-flock path checks only `.kick.d/pid`, never `.drain.lock`. When the lock holder
   is `serve`, the shim or OpenCode, every hook spawns a wrapper plus a Go drain that fails the
   flock and exits. No data is lost, but the phase 2 outcome is broken on darwin and the cost
   repeats per hook. **Briefed:** `docs/plans/09-workflow-binary/briefs/remediation-51.md`.
2. **Backlog during the live switch loses artifact revisions and mislinks content.** There is no
   `client.toml` on this machine yet, so the queue grows. `artifact_version` content is read at
   drain time, not at spool time. When the backlog drains, each queued event for a path carries
   that file's *current* content. Intermediate revisions are lost, and old conversations' events
   are linked to content written by later conversations. This weakens ledger Assumption 5
   ("nothing is lost") for the linked dataset, which is the point of the plan. Design 02 accepts
   drain-time reads for short windows; an unbounded backlog is outside that. **Follow-up
   (operational):** the maintainer runs `workflow init` and enables `serve` promptly. If backlogs
   are expected, consider snapshotting small artifacts at spool time.

### Low

3. **Standalone drain retried forever on an invalid (not missing) `client.toml`.** The drain held
   the lock and retried every second, with no give-up, because give-up applied only on the
   delivery retry path. **Resolved:** 97dcd72, which applies the `GiveUp` window there too, with
   test `TestInvalidConfigGivesUp`.
4. **Idle-exit window on the mkdir path.** Between the drain's post-release rescan and its process
   exit, a hook sees the `.kick.d` pid alive and starts nothing. The event waits for the next hook.
   **Follow-up.** Remediation 51's pid file narrows this if the drain removes it before the
   rescan.
5. **A cold first MCP start can outrun the harness connect timeout.** The source build
   (modernc sqlite) takes tens of seconds. Design 05 relies on the detached SessionStart
   `--version` prebuild, which races the shim's own start in the same session. The first session
   after an update may show the shim as failed, and a restart fixes it. **Follow-up;** this
   disappears once a release is published (Carried).
6. **`.mcp.json` uses `${CLAUDE_PLUGIN_ROOT}`,** which is unset when this repo is opened as a
   project rather than loaded as a plugin, so the project-scope entry fails to start. It is
   unverified whether Cursor loads the plugin's `.mcp.json`; `.cursor-plugin/plugin.json` lists
   only hooks. **Follow-up:** verify per harness, and add `"mcpServers"` to the Cursor manifest if
   needed.
7. **Offline first run is slow and repeats.** The wrapper's download uses `--max-time 60`.
   Offline or with slow DNS, each kick pays this until a build succeeds, and a persistently failing
   build reruns once per kick. Hooks are not blocked, because the kick is detached. **Follow-up:**
   a short negative-cache marker in the cache dir.
8. **`artifact_feedback` re-reads the whole queue per call.** `matcher.scan` reads and parses
   every `.evt` file (through `facts.WritePaths`), and with a config it repeats this every 100 ms
   for up to 1.5 s. With today's unbounded backlog (finding 2), the call slows linearly with queue
   size, and skills call it after every artifact write. **Follow-up:** cache parsed results by
   file name (names are unique and files immutable), or scan only names first.
9. **Drain results are matched by position, not by `id`.** `apply` trusts the order of the
   results. The service is in-repo and tested, so this is not exploitable today, but a reordering
   bug there would delete or reject the wrong files. **Follow-up:** match by `id` and treat a
   mismatch as a 502.
10. **The `workflow init` unit has an unquoted `ExecStart=<root>/bin/workflow serve`.** It breaks
    if the plugin root contains spaces. **Follow-up.**
11. **Service-side note (other reviewer's paths):** `runServe` creates the data dir with mode
    0755. The ledger holds conversation payloads, so 0700 fits. **Follow-up,** for the service
    reviewer.

Counts: blocker 0, high 0, medium 2 (1 briefed, 1 follow-up), low 9 (1 resolved, 8 follow-up).

## Intent and ledger assessment

The client side keeps the design's central promise: capture never blocks or fails a harness. Every
hook exits 0, events are durable on disk before any network work, and the drain deletes only on a
parsed 200. Secret handling has the right shape: payload leaves are redacted, a secret hit in an
artifact goes to `rejected/` with a reason that never contains the secret, and network errors hide
the URL and key.

The ledger's linking assumption is the weak point in practice rather than in code (finding 2).
Until `client.toml` and `serve` exist, the queue grows, and drain-time content reads mean the
linked dataset built from that backlog misattributes artifact content. With the project goal of
building a large linked dataset first, this is worth closing operationally before more
conversations accumulate.

## Residual risks

- macOS behaviour is checked statically and by forcing the no-flock path on Linux. No test has
  run on bash 3.2 or BSD userland (Carried; finding 1 shows the class of gap).
- The live switch has not been exercised end to end with `serve` running, because the maintainer
  has not yet run `init`.
- In this session, the installed (pinned) hook copy still posts briefs to the legacy service and
  asks for `brief_id` frontmatter. The new templates drop that. The two coexist until pinned
  copies are updated, as design 05 accepts.
- The first-run source build depends on a local Go 1.27.1 toolchain until a release is published.

## Plan sufficiency

The plan was sufficient to build the client side correctly. Its outcomes were concrete enough to
test, and they caught the darwin gap only because the outcome named the serve-holds-lock case
explicitly. It under-specified two things: what happens to drain-time artifact reads under a long
backlog, and platform coverage for the mkdir path. Both belong in the next plan's assumptions
rather than being left implicit.
