package serve

import (
	"context"
	"net/url"
	"reflect"
	"testing"
	"time"

	"github.com/codyhamilton/yakka/packages/yakka/internal/keys"
	"github.com/codyhamilton/yakka/packages/yakka/internal/store"
)

const execAnalytics = "/v1/analytics/"

// executionsHTTPServer is a minimal tenant with three in-window brief shapes (complete, unreported, started).
func executionsHTTPServer(t *testing.T) (*Server, string) {
	t.Helper()
	s := New(Config{Data: t.TempDir(), Keys: []KeyPair{{"a", "ka"}}}, Options{})
	t.Cleanup(func() { s.Close() })
	ts, err := s.tenant("a")
	if err != nil {
		t.Fatal(err)
	}
	base := time.Now().UTC().Truncate(24 * time.Hour).AddDate(0, 0, -5)
	at := func(day, hh, mm int) float64 {
		return float64(base.AddDate(0, 0, day).Add(time.Duration(hh)*time.Hour + time.Duration(mm)*time.Minute).Unix())
	}
	av := func(conv, path string, ts float64) store.FactRow {
		content := "# " + path + "\n"
		raw := mustJSON(map[string]any{"type": "artifact_version", "path": path, "content": content})
		rh, _ := keys.RowHash(raw)
		return store.FactRow{RowHash: rh, Type: "artifact_version", ConversationID: conv, Harness: "h",
			Event: "Write", TS: ts, RepoID: "r1", Path: path, ContentHash: keys.ContentHash([]byte(content)), Raw: raw, Source: "worktree"}
	}
	rows := []store.FactRow{
		av("c1", "docs/plans/p1/briefs/b-complete.md", at(1, 10, 0)),
		av("c1", "docs/plans/p1/reports/b-complete.md", at(2, 10, 0)),
		{Type: "commit", ConversationID: "c1", Harness: "h", Event: "commit", TS: at(2, 11, 0), RepoID: "r1"},
		av("c2", "docs/plans/p1/briefs/b-unreported.md", at(1, 11, 0)),
		{Type: "commit", ConversationID: "c2", Harness: "h", Event: "commit", TS: at(2, 12, 0), RepoID: "r1"},
		av("c3", "docs/plans/p1/briefs/b-started.md", at(1, 12, 0)),
	}
	for i := range rows {
		if rows[i].RowHash == "" {
			raw := mustJSON(map[string]any{"type": rows[i].Type, "conversation_id": rows[i].ConversationID})
			rows[i].RowHash, _ = keys.RowHash(raw)
			rows[i].Raw = raw
		}
	}
	if _, err := ts.t.Append(context.Background(), rows); err != nil {
		t.Fatal(err)
	}
	win := "from=" + url.QueryEscape(base.Format(time.RFC3339)) + "&to=" + url.QueryEscape(time.Now().UTC().Add(time.Hour).Format(time.RFC3339))
	return s, win
}

func TestExecutionsShapeAndSeries(t *testing.T) {
	s, win := executionsHTTPServer(t)
	aerr(t, s, execAnalytics+"executions?shape=nope&"+win, 400, "unknown shape nope")
	aerr(t, s, execAnalytics+"executions?bucket=hour&"+win, 400, "bucket must be day, week, or month")

	all := aok(t, s, execAnalytics+"executions?"+win)
	cntAll := all["counts"]
	if !reflect.DeepEqual(cntAll, map[string]any{"complete": 1.0, "unreported": 1.0, "started": 1.0}) {
		t.Fatalf("counts %v", cntAll)
	}
	filtered := aok(t, s, execAnalytics+"executions?shape=complete&"+win)
	if !reflect.DeepEqual(filtered["counts"], cntAll) {
		t.Fatalf("counts with shape: %v want %v", filtered["counts"], cntAll)
	}
	allRows := rowsOf(all, "rows")
	filtRows := rowsOf(filtered, "rows")
	if len(filtRows) != 1 || len(allRows) != 3 {
		t.Fatalf("rows filtered %d all %d", len(filtRows), len(allRows))
	}
	if filtRows[0]["shape"] != "complete" {
		t.Fatalf("shape %v", filtRows[0]["shape"])
	}

	withSeries := aok(t, s, execAnalytics+"executions?bucket=day&"+win)
	if withSeries["bucket"] != "day" {
		t.Fatalf("bucket %v", withSeries["bucket"])
	}
	raw, ok := withSeries["series"].([]any)
	if !ok || len(raw) != 3 {
		t.Fatalf("series %v", withSeries["series"])
	}
	wantKeys := []string{"complete", "unreported", "started"}
	for i, key := range wantKeys {
		ent, ok := raw[i].(map[string]any)
		if !ok || ent["key"] != key {
			t.Fatalf("[%d] entry %v want key %q", i, raw[i], key)
		}
		if _, ok := ent["points"].([]any); !ok {
			t.Fatalf("[%d] points missing", i)
		}
	}

	p1 := aok(t, s, execAnalytics+"executions?limit=1&"+win)
	nx, has := p1["next"].(string)
	if !has {
		t.Fatal("expected next with limit=1 over three rows")
	}
	p2 := aok(t, s, execAnalytics+"executions?limit=1&"+win+"&cursor="+url.QueryEscape(nx))
	if !reflect.DeepEqual(p1["counts"], p2["counts"]) {
		t.Fatalf("paged counts differ")
	}
	aerr(t, s, execAnalytics+"executions?limit=1&shape=complete&"+win+"&cursor="+url.QueryEscape(nx), 400, "cursor mismatch")
}
