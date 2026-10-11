# 5-02 — Chart-builder config model (report)

Status: done

## What changed

Two new files, no others touched.

- `packages/workflow-analytics/src/lib/builder.ts` — the pure config model. Exports the settled types (`ChartKind`, `Bucket`, `BuilderConfig`) and `parseConfig`, `configToParams`, `defaultConfig`, `allowedDims`, `allowedBuckets`, `allowedCharts`, `dimOrder`, `weekdayLabel`, `isRangeOk`. `parseConfig` reads `m`/`d`/`b`/`c`/`top`, then sanitises against the schema and never throws. `isRangeOk` delegates to `pickBucket` from `buckets.ts` (no rules copied). No network/DOM/Svelte imports.
- `packages/workflow-analytics/src/lib/builder.test.ts` — 23 vitest cases: every chart-fit table row (dims 0/1/2 × none/day, plus dims 3), dim sanitisation against a measure that lacks the dim, round trip through `configToParams`→`parseConfig`, `allowedDims` never escaping the measure's dims for either fixture measure, `configToParams` omitting `b=none`/`top=20`, `defaultConfig`, `weekdayLabel`, `dimOrder` (incl. no mutation), `isRangeOk`, and `parseConfig` fallbacks (unknown measure, empty schema, bad bucket, bad chart, top clamp).

Key decision: the bucket param is validated against both the known five values and `schema.buckets`, falling back to `none`; the chart falls back to the first allowed kind, or `line` when `allowedCharts` is empty. This matches the brief and DESIGN.md's bucket list.

## Done evidence

- `npm test -- builder` before: `No test files found, exiting with code 1` (`filter: builder`; no module).
- `npm test -- builder` after: `✓ src/lib/builder.test.ts (23 tests)` — `Test Files 1 passed (1)`, `Tests 23 passed (23)`.
- `npm test` (all suites): `Test Files 11 passed (11)`, `Tests 97 passed (97)` (exit 0).

## Deviations from the brief

None.

## Problems / concerns

None. Vitest transpiles without typechecking, and the repo's tsconfig extends a generated `.svelte-kit/tsconfig.json` that is absent in this worktree, so no standalone typecheck was run; the brief specifies tests only.

## Unfinished work

None.
