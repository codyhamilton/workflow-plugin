package store

import (
	"context"
	"database/sql"
	"fmt"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
)

// hook rolls up one hook_event fact at second ts.
func hook(i int, ts int64, harness, repo, norm, event, tool, conv string) FactRow {
	raw := []byte(fmt.Sprintf(`{"rollup":%d}`, i))
	return FactRow{RowHash: keys.ContentHash(raw), Type: "hook_event", ConversationID: conv,
		Harness: harness, Event: event, NormEvent: norm, Tool: tool, RepoID: repo, TS: float64(ts), Raw: raw}
}

func rollupFixture(t *testing.T) (*Tenant, []FactRow, int64) {
	t.Helper()
	return rollupFixtureOn(t, openT(t, Options{}))
}

// baseHookAgg is the base-row oracle: counts by one dimension over [from,to], dim "" for total.
func baseHookAgg(t *testing.T, tn *Tenant, from, to int64, dim string) map[string]float64 {
	t.Helper()
	sel := "''"
	if dim != "" {
		sel = dim
	}
	q := "SELECT " + sel + " AS k, count(*) FROM facts WHERE type='hook_event' AND ts>=? AND ts<=? GROUP BY k"
	rows, err := tn.rdb.Query(q, float64(from), float64(to))
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	out := map[string]float64{}
	if dim == "" {
		out[""] = 0 // an ungrouped count is 0, not absent, over an empty window
	}
	for rows.Next() {
		var k string
		var v float64
		if err := rows.Scan(&k, &v); err != nil {
			t.Fatal(err)
		}
		out[k] = v
	}
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	return out
}

func queryHookAgg(t *testing.T, tn *Tenant, from, to int64, dim string) map[string]float64 {
	t.Helper()
	var dims []string
	if dim != "" {
		dims = []string{dim}
	}
	res, err := tn.Query(context.Background(),
		AnalyticsFilter{From: time.Unix(from, 0).UTC(), To: time.Unix(to, 0).UTC()},
		QueryParams{Measure: "hook_events", Dims: dims, Top: 100})
	if err != nil {
		t.Fatalf("query from=%d to=%d dim=%q: %v", from, to, dim, err)
	}
	out := map[string]float64{}
	for _, r := range res.Rows {
		k := ""
		if dim != "" {
			k = r.K[0]
		}
		out[k] = r.V
	}
	return out
}

// TestRollupEqualsBaseRows drives the rolled-up read path over windows that start and end mid-hour
// and compares it, dimension by dimension, with an aggregate over base rows alone.
func TestRollupEqualsBaseRows(t *testing.T) {
	tn, _, base := rollupFixture(t)
	windows := []struct {
		name     string
		from, to int64
	}{
		{"whole hours", base, base + 3*3600 + 3599},
		{"mid start", base + 1800, base + 3*3600 + 1800},
		{"mid end", base, base + 2*3600 + 1800},
		{"single hour mid", base + 3600 + 600, base + 3600 + 3000},
		{"exact hour edges", base + 3600, base + 2*3600},
		{"one second in", base + 1, base + 3600 - 1},
		{"all", 0, base + 10*3600},
	}
	dims := []string{"", "harness", "repo_id", "norm_event", "event", "tool", "conversation_id"}
	for _, w := range windows {
		for _, d := range dims {
			want := baseHookAgg(t, tn, w.from, w.to, d)
			got := queryHookAgg(t, tn, w.from, w.to, d)
			if !reflect.DeepEqual(got, want) {
				t.Fatalf("window %q dim %q: rollup %v != base %v", w.name, d, got, want)
			}
		}
	}
}

// TestRollupEqualsBaseSQL asserts the rollup table is exactly the base aggregate, in both
// directions, so no tuple is missing or double-counted.
func TestRollupEqualsBaseSQL(t *testing.T) {
	tn, _, _ := rollupFixture(t)
	sel := `SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, norm_event, event, tool, conversation_id, count(*)
		FROM facts WHERE type='hook_event' GROUP BY 1,2,3,4,5,6,7`
	var diff int
	if err := tn.rdb.QueryRow(`SELECT count(*) FROM (
		SELECT hour,harness,repo_id,norm_event,event,tool,conversation_id,n FROM hook_events_hourly
		EXCEPT ` + sel + `)`).Scan(&diff); err != nil {
		t.Fatal(err)
	}
	if diff != 0 {
		t.Fatalf("rollup has %d tuples not in the base aggregate", diff)
	}
	if err := tn.rdb.QueryRow(`SELECT count(*) FROM (` + sel + `
		EXCEPT SELECT hour,harness,repo_id,norm_event,event,tool,conversation_id,n FROM hook_events_hourly)`).Scan(&diff); err != nil {
		t.Fatal(err)
	}
	if diff != 0 {
		t.Fatalf("base aggregate has %d tuples not in the rollup", diff)
	}
}

// TestRollupDuplicateAppend: re-appending the same facts (identical row hashes) inserts no row, so
// it must leave both the base aggregate and the rollup unchanged.
func TestRollupDuplicateAppend(t *testing.T) {
	tn, rows, base := rollupFixture(t)
	before := queryHookAgg(t, tn, base, base+3*3600+3599, "tool")
	ins, err := tn.Append(context.Background(), rows)
	if err != nil {
		t.Fatal(err)
	}
	for i, ok := range ins {
		if ok {
			t.Fatalf("duplicate row %d reported inserted", i)
		}
	}
	after := queryHookAgg(t, tn, base, base+3*3600+3599, "tool")
	if !reflect.DeepEqual(before, after) {
		t.Fatalf("duplicate append changed counts: %v -> %v", before, after)
	}
	// The total rollup weight must still equal the base row count.
	var rollupN, baseN int
	if err := tn.rdb.QueryRow(`SELECT sum(n) FROM hook_events_hourly`).Scan(&rollupN); err != nil {
		t.Fatal(err)
	}
	if err := tn.rdb.QueryRow(`SELECT count(*) FROM facts WHERE type='hook_event'`).Scan(&baseN); err != nil {
		t.Fatal(err)
	}
	if rollupN != baseN || baseN != len(rows) {
		t.Fatalf("rollup sum %d, base %d, fixture %d", rollupN, baseN, len(rows))
	}
}

// TestRollupBackfilledOnMigrate rewinds the ledger to before the rollup table (migration 6) and
// reopens it, asserting the open-time backfill refills the rollup from base rows.
func TestRollupBackfilledOnMigrate(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "tenant")
	tn, err := Open(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	_, rows, base := rollupFixtureOn(t, tn)
	if err := tn.Close(); err != nil {
		t.Fatal(err)
	}
	db, err := sql.Open("sqlite", "file:"+filepath.Join(dir, "ledger.db")+"?_pragma=busy_timeout(5000)")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`DELETE FROM hook_events_hourly`); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec(`PRAGMA user_version = 5`); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	tn2, err := Open(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { tn2.Close() })
	var n int
	if err := tn2.rdb.QueryRow(`SELECT count(*) FROM hook_events_hourly`).Scan(&n); err != nil {
		t.Fatal(err)
	}
	if n == 0 {
		t.Fatal("migration did not refill the rollup")
	}
	got := queryHookAgg(t, tn2, base, base+3*3600+3599, "harness")
	want := baseHookAgg(t, tn2, base, base+3*3600+3599, "harness")
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("after refill: rollup %v != base %v", got, want)
	}
	if len(rows) == 0 {
		t.Fatal("fixture empty")
	}
}

// rollupFixtureOn appends the standard fixture to an already-open tenant.
func rollupFixtureOn(t *testing.T, tn *Tenant) (*Tenant, []FactRow, int64) {
	t.Helper()
	base := time.Date(2026, 3, 4, 0, 0, 0, 0, time.UTC).Unix()
	rows := []FactRow{
		hook(1, base+15*60, "claude", "r1", "tool_post", "PostToolUse", "Read", "c1"),
		hook(2, base+45*60, "codex", "r1", "tool_post", "PostToolUse", "Bash", "c2"),
		hook(3, base+3600+5*60, "claude", "r2", "tool_pre", "PreToolUse", "Bash", "c1"),
		hook(4, base+3600+59*60, "claude", "r1", "tool_post", "PostToolUse", "Edit", "c3"),
		hook(5, base+2*3600, "codex", "r2", "tool_pre", "PreToolUse", "Read", "c1"),
		hook(6, base+2*3600+30*60, "claude", "r1", "stop", "Stop", "", "c2"),
		hook(7, base+3*3600+10*60, "codex", "r1", "tool_post", "PostToolUse", "Bash", "c4"),
	}
	if _, err := tn.Append(context.Background(), rows); err != nil {
		t.Fatal(err)
	}
	return tn, rows, base
}
