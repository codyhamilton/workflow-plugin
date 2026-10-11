package serve

// TestAnalyticsPageSet is the env-gated page-load profiler for the two busiest dashboard pages.
// Instead of the design's route x measure x dimension matrix (analytics_bench_test.go), it issues
// exactly the request set Overview and Usage send for the 7d, 30d, 90d and All time presets against a
// copy of the large ledger, then ranks the slowest calls and explains their query plans. It is
// skipped unless WORKFLOW_BENCH_DIR names a tenant directory. The source is never opened or written:
// openBenchCopy copies ledger.db into a temp dir and the copy is opened there.
//
// The request sets mirror the site as it stands (packages/workflow-analytics/src/routes/+page.svelte
// and src/routes/usage/+page.svelte) with no filters: Overview sends one /analytics/summary, one
// /analytics/query per spark measure (bucket picked by the site's 400-bucket rule), and one heatmap
// /analytics/query (hook_events, weekday x hour_of_day, bucket none); Usage sends five by-model
// /analytics/query calls (bucket none, top 20) plus cost and tokens over time. All time is the
// 399-day clamp resolveWindow applies to both routes -- the pages do NOT send all=1 (see the report).
//
// The site's `now` is stand-in by the ledger's max ts rounded up to the next hour, with tz=UTC, so
// the windows are the same shape the page sends and the copied data is inside them.

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"net/url"
	"os"
	"slices"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"
)

const (
	pagesetTZ      = "UTC"
	pagesetRuns    = 5
	pagesetConc    = 4
	pagesetSlowN   = 8
	pagesetOutEnv  = "WORKFLOW_PAGESET_OUT"
	pagesetMaxBuck = 400
)

// The Overview spark tiles, in the order the page lists them (SPARKS in +page.svelte).
var pagesetSparkMeasures = []string{
	"conversations", "hook_events", "artifact_versions", "distinct_content",
	"commits", "model_calls", "tokens_in", "cost_usd", "unpriced_calls",
}

// The five Usage by-model measures (usage/+page.svelte).
var pagesetUsageByModel = []string{
	"cost_usd", "model_calls", "unpriced_calls", "tokens_in", "tokens_out",
}

type pageRequest struct {
	Page   string
	Preset string
	Path   string
}

func pagesetParams(path string) string {
	if i := strings.IndexByte(path, '?'); i >= 0 {
		return path[i+1:]
	}
	return ""
}

type pagesetPreset struct {
	Name     string
	From, To time.Time
}

// pagesetPresets mirrors the four presets the site resolves against `now`, rounded up to the next
// full hour (presetWindow). The brief cites 7d, 30d, 90d and All time; All time is the same 399-day
// clamp both pages substitute for all=1 on /query.
func pagesetPresets(to time.Time) []pagesetPreset {
	to = to.UTC().Truncate(time.Hour).Add(time.Hour)
	return []pagesetPreset{
		{"7d", to.Add(-7 * 24 * time.Hour), to},
		{"30d", to.Add(-30 * 24 * time.Hour), to},
		{"90d", to.Add(-90 * 24 * time.Hour), to},
		{"all", to.Add(-399 * 24 * time.Hour), to},
	}
}

// pagesetRequests is every request one Overview load and one Usage load issues for a preset.
func pagesetRequests(to time.Time) []pageRequest {
	var out []pageRequest
	for _, p := range pagesetPresets(to) {
		out = append(out, pagesetOverview(p)...)
		out = append(out, pagesetUsage(p)...)
	}
	return out
}

func pagesetWindow(v url.Values, p pagesetPreset) {
	v.Set("tz", pagesetTZ)
	v.Set("from", p.From.Format(time.RFC3339))
	v.Set("to", p.To.Format(time.RFC3339))
}

func pagesetOverview(p pagesetPreset) []pageRequest {
	var out []pageRequest
	sv := url.Values{}
	pagesetWindow(sv, p)
	out = append(out, pageRequest{"overview", p.Name, "/v1/analytics/summary?" + sv.Encode()})
	b := pagesetBucket(p.From, p.To, []string{"hour", "day", "week", "month"})
	for _, m := range pagesetSparkMeasures {
		q := url.Values{}
		pagesetWindow(q, p)
		q.Set("measure", m)
		q.Set("bucket", b)
		out = append(out, pageRequest{"overview", p.Name, "/v1/analytics/query?" + q.Encode()})
	}
	h := url.Values{}
	pagesetWindow(h, p)
	h.Set("measure", "hook_events")
	h.Add("dim", "weekday")
	h.Add("dim", "hour_of_day")
	h.Set("bucket", "none")
	out = append(out, pageRequest{"overview", p.Name, "/v1/analytics/query?" + h.Encode()})
	return out
}

func pagesetUsage(p pagesetPreset) []pageRequest {
	var out []pageRequest
	b := pagesetBucket(p.From, p.To, nil)
	for _, m := range pagesetUsageByModel {
		q := url.Values{}
		pagesetWindow(q, p)
		q.Set("measure", m)
		q.Set("dim", "model")
		q.Set("top", "20")
		q.Set("bucket", "none")
		out = append(out, pageRequest{"usage", p.Name, "/v1/analytics/query?" + q.Encode()})
	}
	c := url.Values{}
	pagesetWindow(c, p)
	c.Set("measure", "cost_usd")
	c.Set("dim", "model")
	c.Set("bucket", b)
	out = append(out, pageRequest{"usage", p.Name, "/v1/analytics/query?" + c.Encode()})
	tk := url.Values{}
	pagesetWindow(tk, p)
	tk.Set("measure", "tokens_out")
	tk.Set("bucket", b)
	out = append(out, pageRequest{"usage", p.Name, "/v1/analytics/query?" + tk.Encode()})
	return out
}

// pagesetBucket mirrors the site's pickBucket: the finest bucket whose upper-bound count fits 400.
func pagesetBucket(from, to time.Time, allowed []string) string {
	for _, b := range []string{"hour", "day", "week", "month"} {
		if allowed != nil && !slices.Contains(allowed, b) {
			continue
		}
		if pagesetBucketCount(b, from, to) <= pagesetMaxBuck {
			return b
		}
	}
	return "month"
}

func pagesetBucketCount(bucket string, from, to time.Time) int {
	ms := to.Sub(from)
	switch bucket {
	case "hour":
		return int(math.Ceil(float64(ms)/float64(time.Hour))) + 2
	case "day":
		return int(math.Ceil(float64(ms)/float64(24*time.Hour))) + 2
	case "week":
		return int(math.Ceil(float64(ms)/float64(7*24*time.Hour))) + 2
	case "month":
		am := time.Date(from.Year(), from.Month(), 1, 0, 0, 0, 0, from.Location())
		bm := time.Date(to.Year(), to.Month(), 1, 0, 0, 0, 0, to.Location())
		return (bm.Year()-am.Year())*12 + int(bm.Month()-am.Month()) + 3
	}
	return 0
}

type pagesetResult struct {
	path string
	d    time.Duration
	code int
}

// pagesetRunOnce issues every request of one page load with the site's concurrency of 4.
func pagesetRunOnce(t *testing.T, h *benchHarness, reqs []pageRequest) []pagesetResult {
	res := make([]pagesetResult, len(reqs))
	var wg sync.WaitGroup
	sem := make(chan struct{}, pagesetConc)
	for i := range reqs {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			start := time.Now()
			code, _ := do(t, h.h, http.MethodGet, reqs[i].Path, benchKey, "")
			res[i] = pagesetResult{reqs[i].Path, time.Since(start), code}
		}(i)
	}
	wg.Wait()
	return res
}

type pagesetTiming struct {
	page, preset, path string
	status             int
	p50, max           time.Duration
	samples            int
}

// pagesetMeasure runs a page's set pagesetRuns times, discards the first run and ranks by p50.
func pagesetMeasure(t *testing.T, h *benchHarness, reqs []pageRequest) []pagesetTiming {
	byPath := map[string][]time.Duration{}
	status := map[string]int{}
	for run := 0; run < pagesetRuns; run++ {
		for _, r := range pagesetRunOnce(t, h, reqs) {
			if run == 0 {
				continue
			}
			byPath[r.path] = append(byPath[r.path], r.d)
			status[r.path] = r.code
		}
	}
	meta := map[string]pageRequest{}
	for _, r := range reqs {
		meta[r.Path] = r
	}
	out := make([]pagesetTiming, 0, len(byPath))
	for path, ds := range byPath {
		sort.Slice(ds, func(i, j int) bool { return ds[i] < ds[j] })
		out = append(out, pagesetTiming{
			page: meta[path].Page, preset: meta[path].Preset, path: path,
			status: status[path], p50: nearestRank(ds, 0.5), max: ds[len(ds)-1], samples: len(ds),
		})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].p50 != out[j].p50 {
			return out[i].p50 > out[j].p50
		}
		return out[i].path < out[j].path
	})
	return out
}

func pagesetMS(d time.Duration) float64 { return float64(d) / float64(time.Millisecond) }

// TestAnalyticsPageSet is the env-gated profiler (skipped unless WORKFLOW_BENCH_DIR is set).
func TestAnalyticsPageSet(t *testing.T) {
	src := os.Getenv("WORKFLOW_BENCH_DIR")
	if src == "" {
		t.Skip("set WORKFLOW_BENCH_DIR to a tenant directory to profile the page request sets")
	}
	if err := benchLiveRefused(src); err != nil {
		t.Fatal(err)
	}
	h := openBenchCopy(t, src)
	to := benchMaxTS(t, h.db)
	if to.IsZero() {
		t.Skip("ledger has no facts")
	}
	reqs := pagesetRequests(to)
	timings := pagesetMeasure(t, h, reqs)

	t.Logf("page request-set profile: %d distinct requests, %d timed runs each, concurrency %d, source %s",
		len(timings), pagesetRuns-1, pagesetConc, src)
	for _, tm := range timings {
		t.Logf("%-8s %-4s p50=%7.1fms max=%7.1fms status=%d %s",
			tm.page, tm.preset, pagesetMS(tm.p50), pagesetMS(tm.max), tm.status, tm.path)
		if tm.status != 200 {
			t.Errorf("%s %s returned %d: %s", tm.page, tm.preset, tm.status, tm.path)
		}
	}

	type pagesetJSON struct {
		Path   string   `json:"path"`
		Params string   `json:"params"`
		Page   string   `json:"page"`
		Preset string   `json:"preset"`
		P50MS  float64  `json:"p50_ms"`
		MaxMS  float64  `json:"max_ms"`
		Status int      `json:"status"`
		Plan   []string `json:"explain_query_plan,omitempty"`
	}
	base := make([]pagesetJSON, 0, len(timings))
	for _, tm := range timings {
		base = append(base, pagesetJSON{tm.path, pagesetParams(tm.path), tm.page, tm.preset, pagesetMS(tm.p50), pagesetMS(tm.max), tm.status, nil})
	}
	n := pagesetSlowN
	if n > len(base) {
		n = len(base)
	}
	slowest := make([]pagesetJSON, n)
	copy(slowest, base[:n])
	for i := range slowest {
		plan, err := pagesetExplain(h.db, slowest[i].Path)
		if err != nil {
			t.Errorf("explain %s: %v", slowest[i].Path, err)
			continue
		}
		slowest[i].Plan = plan
		t.Logf("plan %s:\n  %s", slowest[i].Path, strings.Join(plan, "\n  "))
	}

	if out := os.Getenv(pagesetOutEnv); out != "" {
		doc := struct {
			Generated string        `json:"generated"`
			Presets   []string      `json:"presets"`
			Requests  []pagesetJSON `json:"requests"`
			Slowest   []pagesetJSON `json:"slowest"`
		}{
			Generated: time.Now().UTC().Format(time.RFC3339),
			Presets:   []string{"7d", "30d", "90d", "all"},
			Requests:  base,
			Slowest:   slowest,
		}
		b, err := json.MarshalIndent(doc, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(out, append(b, '\n'), 0o644); err != nil {
			t.Fatalf("write %s: %v", pagesetOutEnv, err)
		}
		t.Logf("wrote %s", out)
	}
}

// TestAnalyticsPageSetSmoke is the ungated self-test: on the small bench fixture it asserts the
// request list is non-empty and every request the pages send returns 200, so this file cannot rot.
func TestAnalyticsPageSetSmoke(t *testing.T) {
	src := benchFixtureSource(t)
	h := openBenchCopy(t, src)
	to := benchMaxTS(t, h.db)
	if to.IsZero() {
		t.Fatal("fixture has no facts")
	}
	reqs := pagesetRequests(to)
	if len(reqs) == 0 {
		t.Fatal("page request set is empty")
	}
	for _, r := range reqs {
		code, body := do(t, h.h, http.MethodGet, r.Path, benchKey, "")
		if code != 200 {
			t.Errorf("%s %s: status %d: %s", r.Page, r.Path, code, body)
		}
	}
}

// The EXPLAIN helpers reproduce, for the slowest requests only, the SQL the store runs so its plan
// can be read. They mirror query.go's measureDef.source (interior rollup hours plus the two base-row
// edge hours), usage.go's usageRowsWhere CTE and the rollup path of analytics.go's Summary.

type pagesetDef struct {
	table, pred, distinct, rollup, rollupType string
	rollupCols                                []string
	weighted                                  bool
}

func pagesetDefOf(name string) (pagesetDef, bool) {
	switch name {
	case "hook_events":
		return pagesetDef{table: "facts", pred: "type='hook_event'", rollup: "hook_events_hourly", rollupType: "hook_event",
			rollupCols: []string{"harness", "repo_id", "norm_event", "event", "tool", "conversation_id"}, weighted: true}, true
	case "conversations":
		return pagesetDef{table: "facts", distinct: "conversation_id", rollup: "conversations_hourly",
			rollupCols: []string{"harness", "repo_id", "model", "conversation_id"}}, true
	case "artifact_versions":
		return pagesetDef{table: "facts", pred: "type='artifact_version'"}, true
	case "distinct_content":
		return pagesetDef{table: "facts", pred: "type='artifact_version'", distinct: "content_hash"}, true
	case "commits":
		return pagesetDef{table: "facts", pred: "type='commit'"}, true
	}
	return pagesetDef{}, false
}

var pagesetIsUsage = map[string]bool{
	"model_calls": true, "tokens_in": true, "tokens_out": true, "tokens_cache_read": true,
	"tokens_cache_write": true, "tokens_reasoning": true, "cost_usd": true, "unpriced_calls": true,
}

var pagesetFactCol = map[string]string{
	"harness": "harness", "repo_id": "repo_id", "norm_event": "norm_event", "event": "event",
	"tool": "tool", "conversation_id": "conversation_id", "model": "model", "kind": "kind",
	"plan": "plan", "source": "source",
}

func (d pagesetDef) agg() string {
	if d.distinct != "" {
		return "count(DISTINCT " + d.distinct + ")"
	}
	if d.weighted {
		return "coalesce(sum(w),0)"
	}
	return "count(*)"
}

func (d pagesetDef) source(from, to int64) string {
	if d.rollup == "" {
		return d.table
	}
	hF := from - from%3600
	hT := to - to%3600
	proj := func(te, w string) string {
		var b strings.Builder
		if d.rollupType != "" {
			b.WriteString("'" + d.rollupType + "' AS type, ")
		}
		b.WriteString(te + " AS ts, " + strings.Join(d.rollupCols, ", "))
		if d.weighted {
			b.WriteString(", " + w + " AS w")
		}
		return b.String()
	}
	base := func(lo, hi int64) string {
		p := ""
		if d.pred != "" {
			p = d.pred + " AND "
		}
		return fmt.Sprintf("SELECT %s FROM facts WHERE %sts >= %d AND ts <= %d", proj("ts", "1"), p, lo, hi)
	}
	if hF == hT {
		return "(" + base(from, to) + ")"
	}
	b1 := fmt.Sprintf("SELECT %s FROM facts WHERE %sts >= %d AND ts < %d",
		proj("ts", "1"), pagesetPred(d.pred), from, hF+3600)
	b2 := fmt.Sprintf("SELECT %s FROM facts WHERE %sts >= %d AND ts <= %d",
		proj("ts", "1"), pagesetPred(d.pred), hT, to)
	roll := fmt.Sprintf("SELECT %s FROM %s WHERE hour > %d AND hour < %d", proj("hour", "n"), d.rollup, hF, hT)
	return "(" + b1 + " UNION ALL " + b2 + " UNION ALL " + roll + ")"
}

func pagesetPred(pred string) string {
	if pred == "" {
		return ""
	}
	return pred + " AND "
}

func pagesetBucketExpr(bucket string) string {
	switch bucket {
	case "hour":
		return "strftime('%Y-%m-%dT%H:00:00', ts, 'unixepoch') || 'Z'"
	case "day":
		return "strftime('%Y-%m-%dT00:00:00', ts, 'unixepoch') || 'Z'"
	case "week":
		return "date(ts, 'unixepoch', 'weekday 0', '-6 days') || 'T00:00:00Z'"
	case "month":
		return "strftime('%Y-%m-01T00:00:00', ts, 'unixepoch') || 'Z'"
	}
	return "''"
}

func pagesetQueryExplain(d pagesetDef, dims []string, bucket string, from, to int64) string {
	src := d.source(from, to)
	where := fmt.Sprintf("ts >= %d AND ts <= %d", from, to)
	var sel, grp []string
	for i, dim := range dims {
		var e string
		switch dim {
		case "hour_of_day":
			e = "strftime('%H', ts, 'unixepoch')"
		case "weekday":
			e = "strftime('%w', ts, 'unixepoch')"
		default:
			e = pagesetFactCol[dim]
		}
		al := fmt.Sprintf("k%d", i)
		sel = append(sel, e+" AS "+al)
		grp = append(grp, al)
	}
	if bucket != "" && bucket != "none" {
		sel = append(sel, pagesetBucketExpr(bucket)+" AS t")
		grp = append(grp, "t")
	}
	sel = append(sel, d.agg()+" AS v")
	query := "SELECT " + strings.Join(sel, ", ") + " FROM " + src + " WHERE " + where
	if len(grp) > 0 {
		query += " GROUP BY " + strings.Join(grp, ", ")
	}
	return query
}

func pagesetUsageExplain(from, to int64) string {
	mid := "CASE WHEN harness = 'claude' THEN json_extract(raw, '$.backfill.ref') END"
	where := fmt.Sprintf("ts >= %d AND ts <= %d", from, to)
	return "WITH usage_u AS (SELECT *, " + mid + " AS _mid FROM facts WHERE type = 'hook_event' AND norm_event = 'usage' AND " + where + "), " +
		"kept AS (SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY conversation_id, _mid ORDER BY tok_out DESC, row_hash ASC) AS _rn FROM usage_u) WHERE _mid IS NULL OR _mid = '' OR _rn = 1) " +
		"SELECT count(*) FROM kept"
}

func pagesetSummaryExplain(from, to int64) string {
	hF := from - from%3600
	hT := to - to%3600
	if hF == hT {
		return fmt.Sprintf("SELECT count(*) FROM facts WHERE type='hook_event' AND ts >= %d AND ts <= %d", from, to)
	}
	return fmt.Sprintf("SELECT COALESCE(SUM(n),0) FROM ("+
		"SELECT n FROM hook_events_hourly WHERE hour > %d AND hour < %d "+
		"UNION ALL SELECT count(*) FROM facts WHERE type='hook_event' AND ts >= %d AND ts < %d "+
		"UNION ALL SELECT count(*) FROM facts WHERE type='hook_event' AND ts >= %d AND ts <= %d)",
		hF, hT, from, hF+3600, hT, to)
}

type pagesetStmt struct {
	label, sql string
}

func pagesetExplain(db *sql.DB, path string) ([]string, error) {
	u, err := url.Parse(path)
	if err != nil {
		return nil, err
	}
	q := u.Query()
	from, err := time.Parse(time.RFC3339, q.Get("from"))
	if err != nil {
		return nil, err
	}
	to, err := time.Parse(time.RFC3339, q.Get("to"))
	if err != nil {
		return nil, err
	}
	f, tt := from.Unix(), to.Unix()
	var stmts []pagesetStmt
	switch {
	case strings.HasSuffix(u.Path, "/summary"):
		// Summary runs several statements; the two dominant ones are shown. The rollup/edge union
		// answers the classification question; the usage CTE is the same base-row dedupe the usage
		// queries run.
		stmts = append(stmts,
			pagesetStmt{"summary.hook_events", pagesetSummaryExplain(f, tt)},
			pagesetStmt{"summary.usage", pagesetUsageExplain(f, tt)})
	case pagesetIsUsage[q.Get("measure")]:
		stmts = append(stmts, pagesetStmt{"usage", pagesetUsageExplain(f, tt)})
	default:
		def, ok := pagesetDefOf(q.Get("measure"))
		if !ok {
			return nil, fmt.Errorf("no definition for measure %q", q.Get("measure"))
		}
		stmts = append(stmts, pagesetStmt{"query", pagesetQueryExplain(def, q["dim"], q.Get("bucket"), f, tt)})
	}
	var out []string
	for _, st := range stmts {
		rows, err := db.Query("EXPLAIN QUERY PLAN " + st.sql)
		if err != nil {
			return nil, fmt.Errorf("%v: %s", err, st.sql)
		}
		for rows.Next() {
			var id, parent, notused int
			var detail string
			if err := rows.Scan(&id, &parent, &notused, &detail); err != nil {
				rows.Close()
				return nil, err
			}
			out = append(out, st.label+": "+strings.TrimSpace(detail))
		}
		if err := rows.Err(); err != nil {
			rows.Close()
			return nil, err
		}
		rows.Close()
	}
	return out, nil
}
