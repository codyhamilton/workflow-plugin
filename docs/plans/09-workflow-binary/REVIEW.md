# Plan 09 review

Terminal review of plan 09, run as two independent reviewers. The full sections are
[`review-service.md`](review-service.md) (serve, ingest, store, screen, scorer, keys, secrets,
`init`) and [`review-client.md`](review-client.md) (hooks, spool, kick, drain, facts, client config,
MCP shim, wrapper, release, harness configs, skills). This file is the combined verdict after the
remediation pass.

## Verdict

**PASS_WITH_FOLLOWUPS.**

- **Before remediation:** the service side was REMEDIATE (2 high, 1 medium) and the client side
  was PASS_WITH_FOLLOWUPS (no blocker or high).
- **Remediation pass:** both highs and the service medium were fixed by clean agents, each in one
  pass.
- **Verification:** the orchestrator reran `go vet ./...` and `go test -race -count=1 ./...` at
  `5f91bf8`, and all 12 packages pass.
- **Left for a human:** one briefed medium (remediation 51, macOS only) and one operational medium.

## Phase outcome assessment

| Phase | Assessment |
|---|---|
| 1. Ingest, store, tenant isolation | Met |
| 2. Spool, kick, drain, facts | Met on Linux; partial on macOS (remediation 51) |
| 3. Screening | Met. The caveats (endless retries, 60k-rune limit) are resolved in `1285e1b` and `a0bc12b` |
| 4. Advisory reads and MCP shim | Met |
| 5. Distribution and retirement | Met. The release gap is Carried: nothing published, so first runs build from source |
| 6. Skills on the advisory surface | Met |

## Findings by severity

### High (both resolved)

1. **Permanent scorer errors were retried on every poll, forever.** Up to about 28,800 paid calls
   per day for each stuck item.
   - Fixed in `1285e1b` (exec 33, brief `remediation-01.md`): per-hash backoff, then a screen-stage
     rejection after 5 failures.
   - Test `TestPermanentScreenErrorIsBounded`.
2. **The `env_assignment` precheck rejected ordinary plan prose.** It would have rejected 8 of 57
   plan docs in this repo.
   - Fixed in `5f91bf8` (exec 35, brief `remediation-02.md`). The pattern is now a case-sensitive
     uppercase `NAME=` form plus an anchored colon form whose value needs 16 or more characters
     with a digit.
   - Both client scrub and server ingest pass.
   - Trade-off: a letters-only credential written as `key: value` is no longer caught by the
     precheck and relies on the Jev screen.

### Medium

3. **Jev screened only the first 60,000 runes and recorded `pass` for the whole content.**
   - Fixed in `a0bc12b` (exec 34, brief `remediation-03.md`, option 1): screen-only windows of
     60,000 runes overlapping by 200 runes; the highest score decides.
   - A failure in a later window leaves the item pending.
4. **`Close` waited out in-flight Jev calls.** Fixed in review commit `4ac5e94`.
5. **On macOS, the kick starts a drain on every hook while another holder has the lock.**
   - No data is lost, but there is one wasted process launch per hook.
   - **Open:** briefed in `briefs/remediation-51.md`, not dispatched. It is medium and needs a
     macOS check to verify honestly.
6. **The queue backlog loses artifact revisions and mislinks content.** Artifact content is read
   at drain time, and there is no `client.toml` yet.
   - **Open, operational:** run `workflow init` and enable `serve`.
   - Design question for the next plan: snapshot small artifacts at spool time.

### Low

- **Resolved:**
  - tenant-key timing leak (`bb8594f`);
  - standalone drain retrying forever on an invalid `client.toml` (`97dcd72`).
- **Follow-ups, service** (detail in `review-service.md` 6–14):
  - the cross-tenant kept-score cache;
  - orphan pending files screened with no kinds;
  - the data root created 0755 (also client 11);
  - no `ReadTimeout`/`IdleTimeout`;
  - ingest 500 and 503 not logged server side;
  - `unscreened` blobs never re-screened;
  - map keys not prechecked;
  - duplicate rejection rows on retry;
  - `init` keeping a mismatched `serve.env` key.
- **Follow-ups, client** (detail in `review-client.md` 4–10):
  - the idle-exit window on the mkdir path;
  - a cold first MCP start outrunning the connect timeout;
  - `${CLAUDE_PLUGIN_ROOT}` in `.mcp.json`, and whether Cursor loads it;
  - the offline first run repeating a 60 s download timeout;
  - `artifact_feedback` re-reading the whole queue;
  - drain results matched by position, not by `id`;
  - unquoted `ExecStart`.

## Intent and ledger

The build matches the intent:

- one binary;
- a per-tenant SQLite ledger with content-addressed blobs;
- capture that never blocks a harness;
- screening before promotion;
- advisory reads that the shim consumes;
- skills that submit by writing the file.

Ledger status:

- **Assumption 1 (keys server-only):** holds.
- **Assumption 3 (screen in the scoring request):** holds, now over all of the content.
- **Assumption 5 (nothing is lost):** holds in code but is weakened in practice until `serve` runs
  (finding 6).

## Plan sufficiency

Sufficient. Both reviewers note policies the plan left implicit, each of which produced a finding.
The next plan should state them:

- terminal handling of permanent scorer errors;
- the screening size limit;
- the precheck's tolerated false-positive rate;
- drain-time reads under a long backlog;
- platform coverage for the mkdir (macOS) path.

## Residual risks

- macOS and bash 3.2 are checked only statically, and by forcing the no-flock path on Linux.
- The live switch has not run end to end with `serve` enabled.
- No release is published, so the first run on each machine needs Go and a source build.
- The precheck is regex-based. Unusual credential formats rely on the Jev screen.
- With `synchronous=NORMAL` in WAL mode, a power loss can drop the last acknowledged commits.
- Pinned plugin copies still post to the legacy service until they are updated.
