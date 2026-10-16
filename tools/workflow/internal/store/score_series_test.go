package store

import (
	"context"
	"math"
	"testing"
	"time"
)

func scoreSeriesFixture(t *testing.T) (*Tenant, AnalyticsFilter) {
	t.Helper()
	tn := openT(t, Options{})
	day := ad(10, 1, 0, 0) // 2026-10-01
	addFacts(t, tn,
		afx{typ: "artifact_version", conv: "c1", harness: "h", event: "artifact", ts: day.Add(9 * time.Hour),
			repo: "repoA", path: "docs/plans/p1/DESIGN.md", hash: hx("dup"), source: "worktree"},
		afx{typ: "artifact_version", conv: "c1", harness: "h", event: "artifact", ts: day.Add(11 * time.Hour),
			repo: "repoA", path: "docs/plans/p1/DESIGN.md", hash: hx("dup"), source: "worktree"},
		afx{typ: "artifact_version", conv: "c2", harness: "h", event: "artifact", ts: day.Add(10 * time.Hour),
			repo: "repoA", path: "docs/plans/p1/DESIGN.md", hash: hx("solo"), source: "worktree"},
		afx{typ: "artifact_version", conv: "c3", harness: "h", event: "artifact", ts: ad(10, 3, 0, 0),
			repo: "repoA", path: "docs/plans/p1/DESIGN.md", hash: hx("other"), source: "worktree"},
	)
	mustExec(t, tn, `INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`,
		hx("dup"), "d.x", 0.2, "s", 1)
	mustExec(t, tn, `INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`,
		hx("dup"), "d.x", 0.9, "s", 1)
	mustExec(t, tn, `INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`,
		hx("solo"), "d.x", 0.5, "s", 1)
	mustExec(t, tn, `INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`,
		hx("other"), "d.x", 1.0, "s", 1)
	return tn, AnalyticsFilter{From: ad(10, 1, 0, 0), To: ad(10, 3, 12, 0)}
}

func TestScoreSeriesLatestInBucket(t *testing.T) {
	tn, f := scoreSeriesFixture(t)
	ctx := context.Background()
	got, err := tn.ScoreSeries(ctx, f, "design", "day")
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Name != "d.x" {
		t.Fatalf("checks: %#v", got)
	}
	pts := got[0].Points
	if len(pts) != 2 {
		t.Fatalf("points: %#v", pts)
	}
	// 2026-10-01: dup (latest score 0.9) + solo 0.5 → n=2, median 0.7
	if pts[0].T != "2026-10-01T00:00:00Z" {
		t.Fatalf("t[0]: %q", pts[0].T)
	}
	if pts[0].N != 2 || math.Abs(pts[0].Median-0.7) > 1e-9 {
		t.Fatalf("day1: n=%d median=%v want 2/0.7", pts[0].N, pts[0].Median)
	}
	// 2026-10-03 only other hash
	if pts[1].T != "2026-10-03T00:00:00Z" || pts[1].N != 1 || pts[1].Median != 1 {
		t.Fatalf("day3: %#v", pts[1])
	}
}

func TestScoreSeriesOmitsEmptyBucket(t *testing.T) {
	tn, f := scoreSeriesFixture(t)
	ctx := context.Background()
	got, err := tn.ScoreSeries(ctx, f, "design", "day")
	if err != nil {
		t.Fatal(err)
	}
	for _, p := range got[0].Points {
		if p.T == "2026-10-02T00:00:00Z" {
			t.Fatal("empty bucket 2026-10-02 must not appear")
		}
	}
}

func TestScoreSeriesFromMainFixture(t *testing.T) {
	tn, f := fixture(t)
	ctx := context.Background()
	got, err := tn.ScoreSeries(ctx, f, "brief", "week")
	if err != nil {
		t.Fatal(err)
	}
	if len(got) == 0 {
		t.Fatal("expected brief checks")
	}
	var bx *ScoreSeriesCheck
	for i := range got {
		if got[i].Name == "b.x" {
			bx = &got[i]
			break
		}
	}
	if bx == nil {
		t.Fatal("b.x missing")
	}
	if len(bx.Points) == 0 {
		t.Fatal("no points")
	}
}
