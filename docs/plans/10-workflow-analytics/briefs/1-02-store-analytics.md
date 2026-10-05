# Brief: 1-02 — Store analytics queries

Consumer: a Sonnet worker dispatched by the plan 10 phase 1 orchestrator. The Go API below is
consumed by 1-03, which turns it into the `/v1/analytics/*` JSON routes; 1-03 codes against the
signatures fixed here, so do not rename them without reporting it.
Owned paths: new `tools/workflow/internal/store/analytics.go`, new
`tools/workflow/internal/store/analytics_test.go`, `tools/workflow/internal/store/store.go` (only to
append one migration, see Changes), `docs/plans/10-workflow-analytics/reports/1-02-store-analytics.md`
(new). Touch nothing else; in particular not `store/reads.go`, `internal/serve/`, `internal/keys/`,
`go.mod`.
Commits: Commit to the current branch when done evidence passes, with a plain-summary title. Never push.
Report: before committing, write `docs/plans/10-workflow-analytics/reports/1-02-store-analytics.md` (a handoff; rubric in `tools/quality/checks/execution-report.json`) and include it in the commit.
Depends on: nothing.
Runs alongside: 1-01 (disjoint paths).
Budget: 7 files to read, about 650 lines to write including tests, 60 tool turns. Past the budget, stop: write a handoff under this brief's name in `docs/plans/10-workflow-analytics/IMPLEMENTATION.md` (done, not done, what you learned), commit, and report `over budget`.

## Required reading, in order

1. `docs/plans/10-workflow-analytics/DESIGN.md` — "#### Shared filter" through "#### `GET /v1/analytics/explore`" (lines 62-173). Binding for every count and ordering rule; the JSON shapes there are 1-03's job.
2. `docs/plans/10-workflow-analytics/DESIGN.md` — Assumption 3 and Assumption 6 (lines 232-258).
3. `tools/workflow/internal/store/store.go` — `migrations` (lines 23-45), `FactRow`/`Append` (lines 237-280), `insertRejection` (lines 285-292), `Promote` (scores and screens rows).
4. `tools/workflow/internal/store/reads.go` — `LatestScores` (latest-score-per-check idiom).
5. `tools/workflow/internal/ingest/ingest.go` — lines 1-15 (fact wire shape: `payload`, `source`, `sha` live only in `raw`).
6. `tools/workflow/internal/keys/keys.go` — `kindRe` and `Kind` (lines 165-186).
7. `tools/workflow/internal/store/store_test.go` — `openT`, `row` (lines 18-33).

Go is at `~/.local/go/bin` (add it to `PATH`). Run tests from `tools/workflow`. Read ranges and grep; do not read a whole file to find one section, do not re-read a file already in context, and truncate long tool output.

## Goal

Every phase 1 analytics number (summary, series, facets, window scores, executions, conversations, explore rows) is computable for one tenant from its existing `facts`, `rejections`, `screens`, and `scores`, through the Go API below, and matches a hand-counted fixture.

## Contract

Cited from DESIGN.md (settled; quote it in code comments where useful, do not reinterpret):

- Shared filter: "`repo_id`, `harness`, `kind`, `plan`: repeatable. Values within one parameter are OR; different parameters are AND." "`plan` is the single path segment in `docs/plans/<plan>/`, derived from `facts.path`." "`kind` and `plan` use the same path rules as `keys.Kind` [...] Nested brief paths have no kind [...] and fall under summary `other`." "Usage clocks use `facts.ts` (event time, Unix seconds). [...] rejection counts and rejection rows in `/explore` use `rejections.at` instead."
- Summary, series, scores, executions, conversations, explore: the definitions in each route's section (lines 85-173), including "Commit and report facts count even when their `ts` is outside the window" for executions and "taking the latest `scores` row per `(content_hash, check_name)`" for scores.

Decisions settled at refine (the contract leaves them open; do not re-derive):

1. **Filter rows that lack a dimension.** A row with no value for a filtered dimension has the value `""` and matches only if `""` is requested (never, for `kind`). So a `kind` or `plan` filter keeps only facts whose path has a kind; `repo_id` or `harness` filters exclude every rejection row (rejections have no such columns). Rejection `kind` and `plan` come from `rejections.path`.
2. **Plan derivation.** `plan` is the `<plan>` segment only when `keys.Kind(path) != ""`; otherwise `""`. Implement both as SQLite scalar functions registered once in an `init()` with `sqlite.RegisterDeterministicScalarFunction` (`modernc.org/sqlite` v1.60.1 has it): `wf_kind(path)` calls `keys.Kind`, `wf_plan(path)` applies the same three patterns and returns the segment. `store` may import `internal/keys` (no cycle).
3. **Clocks.** `facts.ts` is REAL Unix seconds; `rejections.at` is INTEGER Unix nanoseconds. The window is inclusive at both ends in each unit. Day bucket: `strftime('%Y-%m-%d', ts, 'unixepoch')`. ISO week bucket (Monday, UTC): `date(ts, 'unixepoch', 'weekday 0', '-6 days')`. Rejections use `at/1e9`.
4. **Executions.** Report and commit must be in the same conversation and the same `repo_id` as the brief ("that conversation has at least one `commit` [...] and an `artifact_version` of [the report]"). The report path pairs by stem: `docs/plans/<plan>/briefs/<stem>.md` → `docs/plans/<plan>/reports/<stem>.md`. Row `TS` is the earliest in-window brief `ts`; row `Harness` is the harness of that earliest fact (ties by rowid). Filters apply to the brief facts only; a `kind` filter without `brief` yields no rows.
5. **Conversations.** `Repos` keeps `""` when an in-window fact has an empty `repo_id` (the contract omits empty only from `kinds`); both lists sorted ascending. Harness tie → lexicographically smaller.
6. **Facets.** `Repos`, `Harnesses`, `Plans`, `Events`: every distinct value including `""`, ascending. `Kinds`: distinct non-empty kinds in `design`, `brief`, `report` order. `Tools`: `payload.tool_name` of `hook_event` facts, missing or `""` omitted, count descending then name ascending, at most 100.
7. **Summary screens.** Over distinct `content_hash` of the filtered in-window `artifact_version` rows, the latest `screens` row by `id`: count verdict `pass` and verdict `unscreened`; anything else (no screen yet, other verdicts) counts in neither.
8. **Ordering and paging.** The store returns complete, sorted row sets for executions and conversations; 1-03 pages them. Executions sort: `TS` descending, `ConversationID` ascending, `BriefPath` ascending, `RepoID` ascending. Conversations: `LastTS` descending, `ConversationID` ascending. Explore: newest first by `ts` (rejections by `at`), ties broken by a stable key of your choice (say which), at most `limit+1` rows read so the caller can set `truncated`.

## Changes

Add `analytics.go` with this API (names and fields are the contract with 1-03; add helpers freely):

```go
type AnalyticsFilter struct {
	From, To                       time.Time // inclusive
	Repos, Harnesses, Kinds, Plans []string  // empty = no constraint
}
type ToolCount struct{ Name string; N int }
type Facets struct{ Repos, Harnesses, Kinds, Plans, Events []string; Tools []ToolCount }
type Summary struct {
	Conversations, HookEvents, ArtifactVersions, DistinctContent int
	ByKind     map[string]int // keys design, brief, report, other — all four always present
	BySource   map[string]int // keys worktree, commit — both always present
	Commits    int
	Rejections map[string]int // keys precheck, screen — both always present
	Screens    map[string]int // keys pass, unscreened — both always present
}
type SeriesPoint struct{ Key, T string; N int } // T is YYYY-MM-DD
type ExecRow struct{ RepoID, Plan, ConversationID, BriefPath, Harness, Shape string; TS float64 }
type ConvRow struct {
	ConversationID, Harness             string
	Repos, Kinds                        []string
	FirstTS, LastTS                     float64
	HookEvents, ArtifactVersions, Commits int
}
type ExploreRow struct {
	Type string; TS float64
	Harness, RepoID, Plan, Kind, Event, Tool, Path, ConversationID, Source, SHA, ScreenVerdict, RejectionStage string
}

func (t *Tenant) Facets(ctx context.Context, f AnalyticsFilter) (Facets, error)
func (t *Tenant) Summary(ctx context.Context, f AnalyticsFilter) (Summary, error)
// metric: hook_events|artifact_versions|commits|conversations|rejections; bucket: day|week;
// group: none|harness|repo_id|event|tool|kind|plan|source|stage. The caller validates pairings.
// group none → Key "all". Points only for buckets with N>0, ordered by Key then T.
func (t *Tenant) Series(ctx context.Context, f AnalyticsFilter, metric, bucket, group string) ([]SeriesPoint, error)
// Latest score per (content_hash, check) over distinct content_hash of filtered in-window
// artifact_version rows of kind (f.Kinds is ignored); values per check sorted ascending.
func (t *Tenant) WindowScores(ctx context.Context, f AnalyticsFilter, kind string) (map[string][]float64, error)
func (t *Tenant) Executions(ctx context.Context, f AnalyticsFilter) ([]ExecRow, error)
func (t *Tenant) Conversations(ctx context.Context, f AnalyticsFilter) ([]ConvRow, error)
func (t *Tenant) Explore(ctx context.Context, f AnalyticsFilter, limit int) (rows []ExploreRow, truncated bool, err error)
```

- Reads use `t.rdb`, parameterised SQL only (filter values are bound, never concatenated).
- `tool` is `json_extract(raw,'$.payload.tool_name')` on `hook_event` facts, `source` is `$.source`, `sha` is `$.sha` (set on `commit` facts and on artifact versions that carry it). Missing → `""`.
- Explore `ScreenVerdict` is the latest `screens` verdict (by `id`) for the row's `content_hash`, `""` when none; rejection rows use `Type` `rejection`, `RejectionStage` = `stage`, `Harness`/`RepoID`/`Event`/`Tool`/`Source`/`SHA` empty. No payload, raw, content, or scores leave the store.
- `store.go`: you may append migration 3, `CREATE INDEX facts_ts ON facts(ts);`. Never edit earlier migrations. `TestMigrationsVersioned` checks `user_version == len(migrations)` and keeps passing.

### Keep untouched

Every existing exported function, the existing migrations, `reads.go`, and the existing tests.

## Done evidence

Write the failing tests first (`analytics_test.go`, a fixture built with `Append` at chosen `ts` values and rejections/screens/scores rows inserted with chosen `at` via `t.wdb` in-package) and report their output before and after. Why: these are the edges the site's numbers silently go wrong on. Window edges and `at`-vs-`ts` decide whether a chart's totals agree with the summary. The week boundary decides bucket labels. Out-of-window commits and reports decide whether a finished brief reads as `started`. Latest-score selection decides whether `/quality` compares against stale scores.

- `go test ./internal/store/ -run Analytics -v` → passes, with assertions on fixture numbers for: summary (each field, including `other` for a nested brief path and `rejections` honouring `at` not `ts`); a window edge (a fact at exactly `From` and one at exactly `To` counted, one a second outside not); repo/kind/plan filters (OR within, AND across, kind filter dropping hook events); series day and week buckets (a Sunday and the following Monday land in different weeks, `t` is the Monday) and `conversations` counting distinct ids; series `tool` group with an empty key; `WindowScores` using the latest score row and only in-window hashes; executions `complete` / `unreported` / `started` including a commit and a report whose `ts` is outside the window, a report in a different conversation not counting, and two briefs in one conversation with only one report; conversations harness tie-break, `Repos`/`Kinds` and in-window-only counts; facets tool ordering and the 100 cap; explore order, `truncated` true at `limit` exceeded and false at exactly `limit`.
- `go vet ./... && go test ./...` from `tools/workflow` → all pass.

## Report back

Under 1,500 tokens. Status: `done` | `done with concerns` | `blocked` | `needs context` | `over budget`. Then what changed, the check output before and after, any deviation from this brief and why (especially any API signature change, which 1-03 must hear about), and any contradiction between this brief and the contracts it cites. Never resolve a contradiction silently.

A non-trivial bug outside your done evidence: report symptom, location, and root cause if found. Do not fix it here.

Do not spawn agents beyond read-only research helpers. If this unit needs one, it was mis-sized: report `blocked` and say so.
