# Plan 09 review: service side

**Scope:** `tools/workflow/internal/{serve,ingest,store,screen,scorer,keys,secrets}` and
`cmd/workflow` (`serve`, `init`). The diff is `git diff 5726cc3^..HEAD -- tools/workflow`. It is
held against DESIGN.md (intent, assumption ledger, phases 1, 3 and 4 service side, and the phase 5
`init` clause), designs 01, 03 and 04, IMPLEMENTATION.md and `reports/`. Carried items are not
re-reported unless they are worse than recorded.

**Verdict for this side: REMEDIATE.** Two high findings and one medium finding are briefed. Two
findings were fixed in place.

## Phase outcome assessment

| Phase | Assessment | Evidence |
|---|---|---|
| 1. Ingest, store, tenant isolation | **Met** | See below. |
| 3. Screening | **Met, with caveats** | See below. |
| 4. Advisory reads (service side) | **Met** | See below. |
| 5. `init` clause | **Met** | See below. |

**Phase 1: met.**

- Tests: the `ingest` tests, `serve_test` tenant isolation, and the store p99 burst at
  `store_test.go:353`.
- A manual end-to-end run (temp `HOME`, port 18779, keys `a=ka,b=kb`):
  - The secret-bearing fact was rejected with `precheck: github_token in payload.x line 1`.
  - On resend, the artifact fact came back `duplicate`.
  - The artifact was promoted `unscreened` with no scorer key.
  - Tenant B's key got 404 on tenant A's content, and a bad key got 401.
  - The secret appeared in neither the data dir nor the log.

**Phase 3: met, with caveats.**

- Evidence: `TestScreeningOutcome` and the live Jev run recorded in IMPLEMENTATION.md.
- Caveats:
  - permanent scorer errors loop forever (remediation-01);
  - only the first 60k runes are screened (remediation-03).

**Phase 4: met.** `TestAdvisoryReads` covers artifacts, baselines and search, with tenant B
isolation.

**Phase 5 (`init`): met.** `init_test` checks:

- files 0600 and directories 0700;
- the key matches between files and never appears in output;
- no `TYPESAFE_API_KEY` is written;
- a fake `systemctl` is never executed;
- a rerun keeps every file.

## Findings

### High

1. **Permanent scorer errors are retried on every poll, forever.** Briefed:
   `docs/plans/09-workflow-binary/briefs/remediation-01.md`.
   - Location: `serve.go` `drainPending` and `reconcile`, and `scorer/jev.go` `ask`.
   - Only `ErrUnreachable` backs off. A 400 or 413, a malformed body or a missing screen answer is
     re-sent on every 3 s poll and every wake, about 28,800 paid calls a day per stuck item.
   - The item never reaches a terminal state the reads can show.
   - A probe made 21 calls in 600 ms at a 30 ms poll.
2. **`env_assignment` precheck rejects ordinary plan prose.** This is worse than the recorded
   "loose" limit. Briefed: `docs/plans/09-workflow-binary/briefs/remediation-02.md`.
   - Location: `secrets.go:37`. The pattern is case-insensitive, has no anchor and accepts `:`.
   - Scanning this repo's plan docs, 8 of 57 would be rejected, about 6 of them benign. One is the
     shim's own rejection text ("secret: aws_access_key at line 3"), quoted in the 4-02 report.
   - The pattern set is shared with the client scrub, so the fix touches both sides.

### Medium

3. **Jev screens the first 60,000 runes and records `pass` for the whole content.** Briefed:
   `docs/plans/09-workflow-binary/briefs/remediation-03.md`.
   - The tail is persisted under a clean verdict.
   - The truncation was known (3-01 report), but its security consequence was not.
4. **`Close` waited out in-flight Jev calls, up to 120 s each.** Resolved in **4ac5e94**.
   - `Server` now owns a context that `Close` cancels.
   - `drainPending` stops between hashes.
   - `TestCloseCancelsInFlightScreen` failed with "Close took 1m0s" before the fix and passes after.

### Low

5. **Tenant key comparison leaked key length through timing.** `subtle.ConstantTimeCompare`
   returns early on a length mismatch. Resolved in **bb8594f**: SHA-256 digests are compared over
   every key with no early exit.
6. **Jev's kept-score cache is shared across tenants, keyed by content.** Concurrent identical
   content with different kinds could pick up the other request's scores. Follow-up.
7. **An orphan pending file (left after a failed Append) is screened with no kinds.** It is never
   quality-scored. Follow-up.
8. **The data root is created 0755 in `runServe`.** Tenant dirs are 0700, so nothing is exposed,
   but listing the root reveals tenant names. Follow-up.
9. **`http.Server` sets only `ReadHeaderTimeout`.** With no `ReadTimeout` or `IdleTimeout`, slow
   bodies can hold connections. This matters once remote mode is exposed. Follow-up.
10. **Ingest 500 and tenant-open 503 errors are not logged server side.** The cause reaches only
    the client. Follow-up.
11. **Blobs promoted `unscreened` are never re-screened once a scorer key is added.** Follow-up.
12. **Map keys in facts are not prechecked; only string leaves are.** Follow-up.
13. **A retry after an ingest 500 can write duplicate rejection rows.** Rejections are not
    deduplicated by row hash. Follow-up.
14. **`init` silently keeps an existing `serve.env` whose key no longer matches `client.toml`.**
    The result is 401s with no hint. Follow-up: warn on mismatch.

**Client side, for the orchestrator:** none found. The wrapper finds Go at `~/.local/go/bin`, so a
systemd PATH without Go is not a problem.

## Intent and ledger assessment

The implementation matches the stated intent:

- one binary;
- per-tenant SQLite ledger plus content-addressed blobs;
- validate, precheck, hash and pending before the commit;
- screening before promotion;
- the advisory reads that the MCP shim consumes.

The relevant ledger assumptions:

- **Assumption 1 (env keys server-only): holds.** `TYPESAFE_API_KEY` is read only by `serve`.
  `init` never writes it, and errors carry no key or body.
- **Assumption 3 (screen in the same System One request as scoring): holds.** Truncation
  (finding 3) weakens the claim that the screen guards persistence. The tail is never seen.

No departure in IMPLEMENTATION.md contradicts a design contract on this side.

## Residual risks

- `synchronous=NORMAL` in WAL mode can lose the last acknowledged commits on power loss. This is the
  design's choice. Client retries cover it only while the queue file still exists.
- Content is sent to TypeSafe unscrubbed beyond the regex precheck. Accepted by design.
- `screen_gaps` is recounted only on restart. This is Carried.
- A cancel between Promote and the screens-row write leaves a blob without a screen row. The next
  start re-screens it, at the cost of one call.
- The precheck stays regex-based, so false negatives on unusual credential formats rely on the Jev
  screen. Finding 3 limits that screen.

## Plan sufficiency

**Sufficient.** DESIGN.md and designs 01, 03 and 04 were enough to determine the intent and place
each finding. The plan leaves three policies unstated, and each led to a finding:

- what happens to an item the scorer rejects permanently (finding 1);
- the size limit for screening (finding 3);
- the tolerated false-positive rate for the precheck (finding 2).

A future revision should state all three.
