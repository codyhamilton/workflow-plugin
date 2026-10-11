# 3-04 — Measure matrix and query engine for non-usage measures

Status: done

## What changed

New `tools/workflow/internal/store/query.go`: `MeasureSpec`, `Measures()`, `Buckets`,
`QueryParams`, `QueryRow`, `QueryResult`, `ErrUnsupported`, package var `usageQuery`,
package var `queryRowCap`, and `(*Tenant).Query`. It answers
`measure × 0..2 dims × bucket × top-N` for the six non-usage measures
(`hook_events`, `conversations`, `artifact_versions`, `distinct_content`, `commits`,
`rejections`) from the design's matrix. Usage measures return
`errors.New("measure not available")` while `usageQuery` is nil.

New `tools/workflow/internal/store/query_test.go`: 11 tests.

## Evidence

- `go test ./internal/store -run Query -v` → 11/11 PASS, `ok ... 0.089s`.
- `go test ./internal/store` → `ok ... 0.956s` (no regressions).
- `go vet ./internal/store` → no output.
- `gofmt -l internal/store` → no output.

## Departures from the brief (with reasons)

1. Executor variable is named `usageQuery`, not `usageExec`. The brief's API block
   (line 42) writes `usageExec`, but its binding prose (line 45) and brief 3-05
   (lines 17, 36) write `usageQuery`. Used `usageQuery` so 3-05 can set it.
2. Measure units are not specified by the design. Chose `count` for counts,
   `tokens` for `tokens_*`, `usd` for `cost_usd`.
3. `weekday` format is unspecified. Chose SQLite `%w` (0=Sunday..6=Saturday), which
   equals Go's `time.Weekday()`; `hour_of_day` uses `"%02d"` to match SQL `%H`.
4. Errors for an unknown measure / unknown bucket are unspecified. Chose
   `unknown measure %q` and `unknown bucket %q`; only an unsupported dimension wraps
   `ErrUnsupported`, as the brief requires.
5. A `conversation_id` filter on the `conversations` measure is ignored, because the
   design matrix lists that measure's dims as `harness`, `repo_id`, `model` only.
   This follows the "filter on a dimension the measure does not carry" rule literally.

## Unfinished / follow-ups

- Usage measures need 3-05 to set `usageQuery`.
- Non-UTC distinct measures use the slow distinct-tuple path the brief calls out;
  3-11 measures it.

## Problems

- None known.
