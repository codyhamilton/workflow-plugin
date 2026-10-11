# Review: Analytics Dashboard Overhaul

Verdict: PASS_WITH_FOLLOWUPS
Reviewed SHA: 48cee06 (plus the report-text fix recorded below)

Three focused read-only reviewers ran in parallel (Go backend; dashboard site; intent, security and phase outcomes). Go `vet` and `test` were clean, site `npm test` passed 161 of 161 with a clean build, and the plugin hook tests passed 8 of 8. No blocker or high finding stands that is both in scope and non-architectural.

## Phase outcome assessment

| Phase | Assessment | Evidence |
|---|---|---|
| 1 Event policy, archive, slim ingest | Met | `TestIngestPolicy` through the real ingest handler; plugin tests pass; remove-list equality test parses the plugin block. |
| 2 Compaction and reclaim | Met on a copy | 11.6 GB to 296 MB; removed events, deltas and payloads at 0; archive hashes match. The live ledger is not compacted. |
| 3 Fast analytics API, usage and cost | Partial | 2,063 benchmark cases, max p95 464 ms (thin headroom); cost mostly unpriced because rates are missing. |
| 4 Shell, filters, drill-down | Met after Phase 5 fixes | Phase 4's own verification missed the 1 s target; Phase 5 re-timed under 1 s (max 597 ms). |
| 5 Builder and dashboards | Met | Builder, heatmap, small multiples, save, export, import and sankey covered by e2e. |

## Findings

### blocker
None.

### high
- Live Claude usage rows are not deduplicated by message id (`store/usage.go`, `ingest/extract.go:40`). Reviewer rated high. Re-rated medium on verification: brief 3-05 records it as a known limit, and the local ledger shows 8 of 13,612 message ids repeating (about 0.06%). It needs a message-id column at ingest, so it is architectural. Follow-up.
- Live server not cut over (operational, not code): the live ledger is neither compacted nor migrated, and first open of a large ledger pays one-time index and backfill cost. Needs an offline `ledger compact` plus `purge-deltas` during a maintenance stop. Follow-up.

### medium
- Resolved in review: `internal/secrets` `TestEnvAssignmentCorpus` failed on `reports/4-04-echarts-components.md:26`, which quoted dummy `NAME=value` assignments. The line now describes the command without the values; the test passes with `-count=1`.
- Follow-up: pricing rates for Claude and Codex are missing from `tools/transcript/pricing.json` and `internal/store/pricing_table.json`, so about 74 to 85% of calls are unpriced (shown as unpriced, never $0). Data supplied by the user.
- Follow-up: usage measures aggregate in Go over every kept row (`store/usage.go`); an All-time window is unbounded in memory. Fix: SQL `GROUP BY` or a usage rollup.
- Follow-up: archive `Read` stops at a torn frame until compaction runs `Repair` (`archive/archive.go`).
- Follow-up: compaction re-archives already-slim rows as lossy lines (`compact/compact.go` `processBatch`); the `complete` shortcut can skip rows before `compact_cursor`.
- Follow-up: the `config` OpenCode hook is captured and is not on the remove list; it can carry provider keys. It was captured before this plan and now lands only in the redacted archive. Decide whether to add it to both remove lists.
- Follow-up: builder can render a pairing with zero dimensions and bucket `none` (`routes/builder/+page.svelte`, `lib/builder.ts`); dashboard import bypasses the 12-tile cap; a fragment in a saved URL drops `embed=1` in `tileSrc`.
- Follow-up: the serve binary built from HEAD reports "analytics bundle not embedded" unless the site build runs before `go build`.
- Follow-up: benchmark headroom is thin (max p95 464 ms of 500 ms).

### low (follow-up)
- `partial` is emitted only by `/query`; conversation totals cover only the 5,000 returned events; compact disk check ignores the VACUUM copy; no production `time/tzdata` import and `Local` is accepted; filter values and `top` are not bounded; the 503 on a locked tenant echoes the tenant path.
- Saved-view store does not validate stored entries on read; imported names and duplicates are loose; recursive dashboard embedding is possible only by hand-editing storage; the query cache is unbounded; saving a view overwrites by name silently; notices can go stale.
- Builder `data-ready` is true while the chart is stale; `/dashboards` has no settle signal; Hooks y-axis gutter is not clickable; the Executions sankey filters client-side over the first page; `artifact_feedback` returned not delivered for all artifacts because the workflow MCP server fails to start (ENOENT), so briefs and reports were never scored.

## Intent and ledger assessment

Intent is met: quick date presets, persistent filters, drill-down to one conversation, ECharts with light and dark themes, configurable multi-dimension charts, and a sub-second site on the large copy. The assumption ledger is empty. The Amendment (deltas removed, not collapsed) is implemented in both the plugin and ingest, and compaction and purge remove the historical deltas. Removed events (`chat.headers`, `shell.env`, system transform, `chat.params`, `message.part.delta`) reach no store or archive; no credentials, dumps or database files were found in the diff.

## Plan sufficiency

Sufficient. The design mapped each Intent clause to a provable outcome and benchmark bound, and the build placed every defect found by verification into a numbered unit. Gaps were in verification reach (copies only, no scorer, no feedback service), not in the design.

## Residual risks

Cutover cost on the live ledger; thin API headroom; unpriced cost totals; undeduplicated live Claude usage.
