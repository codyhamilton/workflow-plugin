# fix-01 — Drop `message.part.delta` at the source

Status: done

## What changed

- Plugin: added `"message.part.delta"` as a fifth `REMOVE_EVENTS` entry (`src/index.ts`); updated
  `tests/test_hooks.mjs` (remove list is five, plus a new test: a `message.part.delta` bus event
  queues nothing while `message.part.updated` still queues); updated `README.md` (five events, and
  why: streamed chunks are redundant with `message.part.updated`).
- Ingest policy: `{opencode,message.part.delta}` is now `Remove` (`policy.go`). Deleted `Collapse`,
  `collapseKey`, `CollapseHash`, the `Collapse` case in `String`, and the `CollapseHash` use in
  `ingest.go`; removed the `message.part.delta` row from `normalise.go`'s event map.
- Compact: deleted `Stats.Collapsed`, the `survivors` map, the existing-survivor SQL lookup and the
  `action == Collapse` branch in `processBatch`; the progress line no longer prints `collapsed=`.
- Tests: deleted `TestPolicyCollapseNeedsKey`, `TestPreexistingSurvivor`,
  `TestCollapseSurvivorFirstArrival`, and serve's `deltas_of_one_part_leave_one_fact`; rewrote the
  fixture-driven delta expectations to removal; `rollup_test.go` now drives rollup drift with
  `chat.params` rows instead of deltas; `verify_test.go` asserts delta rows = 0.
- Fixture `ingest_policy.json`: `fx-opencode-42..47` `expect.policy` = `remove`, both statuses
  `accepted`.
- No `store/` comment needed changing: its "collapsed" comments are about row-hash dedupe, not the
  delta mechanism.

## Checks

Before: the goal's check failed. A delta posted to ingest left a fact —
`TestIngestPolicy/deltas_of_one_part_leave_one_fact` PASS (one collapsed fact per part). The
remove-list equality was 4 = 4 (passed by construction; adding the fifth plugin entry before the
Go table would have failed it).

After:
- `cd tools/workflow && go build ./... && go vet ./... && go test ./...` — all packages ok;
  `gofmt -l .` prints nothing.
- `node --test tests/test_hooks.mjs` — 8/8 pass.
- `grep -rn "CollapseHash\|ingest.Collapse\|collapseKey" tools/workflow` — no output.
- `git diff --stat` — only owned paths (14 files, +94/−438).
- `TestRemoveListMatchesPlugin`, `TestNormaliseFixtureDerive`, `TestIngestPolicyFixture` PASS;
  `TestIngestPolicy` (removed/kept/resend subtests) PASS.

## Deviations

- Fixture delta `norm_event` set to `other` (brief named only policy/status): required because
  `TestNormaliseFixtureDerive` derives `norm_event` for every fact and the delta mapping was removed.
- `TestIngestSecretHookNotArchived` now posts `session.status` instead of a delta: a delta is
  `Remove`, so precheck no longer runs for it and the test's intent (a kept secret body is rejected
  and not archived) would otherwise be lost.
- `Policy` keeps its `(harness,event,payload)` signature; `payload` is now unused and `go vet` is
  clean.

## Problems / unfinished

- `TestVerifyCopy` (env-gated, skipped in CI) now expects total facts =
  `facts_total − removed_total − delta_total` and zero delta rows. Its precounts file is external;
  if `removed_total` already folds in deltas, the expected total must be regenerated against the
  real ledger before that verification runs.
- No contradiction found between the brief and the contracts it cites.
