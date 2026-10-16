package store

import (
	"context"
	"math"
	"sort"
	"time"
)

// ScoreSeriesPoint is one bucket's percentile summary for a check.
type ScoreSeriesPoint struct {
	T       string
	N       int
	P25     float64
	Median  float64
	P75     float64
}

// ScoreSeriesCheck is sparse points for one check name.
type ScoreSeriesCheck struct {
	Name   string
	Points []ScoreSeriesPoint
}

func roundScore(v float64) float64 { return math.Round(v*1000) / 1000 }

func scoreSeriesBucketStart(ts float64, bucket string, loc *time.Location) string {
	if loc == nil {
		loc = time.UTC
	}
	tm := time.Unix(int64(ts), 0).In(loc)
	y, m, d := tm.Date()
	switch bucket {
	case "day":
		return time.Date(y, m, d, 0, 0, 0, 0, loc).Format(time.RFC3339)
	case "week":
		wd := (int(tm.Weekday()) + 6) % 7
		mon := time.Date(y, m, d, 0, 0, 0, 0, loc).AddDate(0, 0, -wd)
		return mon.Format(time.RFC3339)
	case "month":
		return time.Date(y, m, 1, 0, 0, 0, 0, loc).Format(time.RFC3339)
	default:
		return ""
	}
}

// ScoreSeries returns per-check percentile points over time buckets for artifact versions of kind.
// f.Kinds is ignored; kind comes from the route. Each bucket uses distinct content hashes with a
// version in that bucket; several versions of one hash in a bucket contribute the latest only.
func (t *Tenant) ScoreSeries(ctx context.Context, f AnalyticsFilter, kind, bucket string) ([]ScoreSeriesCheck, error) {
	f2 := f
	f2.Kinds = nil
	w, args := f2.factWhere()
	args = append([]any{kind}, args...)
	rows, err := t.rdb.QueryContext(ctx, `
		SELECT content_hash, ts FROM facts
		WHERE type='artifact_version' AND content_hash != '' AND kind=? AND `+w, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	// bucket -> hash -> max ts in that bucket
	inBucket := map[string]map[string]float64{}
	hashSet := map[string]bool{}
	for rows.Next() {
		var hash string
		var ts float64
		if err := rows.Scan(&hash, &ts); err != nil {
			return nil, err
		}
		b := scoreSeriesBucketStart(ts, bucket, f.TZ)
		m := inBucket[b]
		if m == nil {
			m = map[string]float64{}
			inBucket[b] = m
		}
		if prev, ok := m[hash]; !ok || ts > prev {
			m[hash] = ts
		}
		hashSet[hash] = true
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	if len(hashSet) == 0 {
		return nil, nil
	}
	hashes := make([]string, 0, len(hashSet))
	for h := range hashSet {
		hashes = append(hashes, h)
	}
	sort.Strings(hashes)
	placeholders := "?" + repeat(",?", len(hashes)-1)
	scRows, err := t.rdb.QueryContext(ctx, `
		WITH s AS (
			SELECT content_hash, check_name, result,
				ROW_NUMBER() OVER (PARTITION BY content_hash, check_name ORDER BY id DESC) AS rn
			FROM scores WHERE content_hash IN (`+placeholders+`))
		SELECT content_hash, check_name, result FROM s WHERE rn=1`, anyStrings(hashes)...)
	if err != nil {
		return nil, err
	}
	defer scRows.Close()
	scoreByHashCheck := map[string]map[string]float64{}
	checkNames := map[string]bool{}
	for scRows.Next() {
		var hash, check string
		var r float64
		if err := scRows.Scan(&hash, &check, &r); err != nil {
			return nil, err
		}
		m := scoreByHashCheck[hash]
		if m == nil {
			m = map[string]float64{}
			scoreByHashCheck[hash] = m
		}
		m[check] = r
		checkNames[check] = true
	}
	if err := scRows.Err(); err != nil {
		return nil, err
	}
	checks := make([]string, 0, len(checkNames))
	for c := range checkNames {
		checks = append(checks, c)
	}
	sort.Strings(checks)
	buckets := make([]string, 0, len(inBucket))
	for b := range inBucket {
		buckets = append(buckets, b)
	}
	sort.Strings(buckets)
	var out []ScoreSeriesCheck
	for _, check := range checks {
		var pts []ScoreSeriesPoint
		for _, b := range buckets {
			hashesInB := inBucket[b]
			var vals []float64
			for h := range hashesInB {
				if v, ok := scoreByHashCheck[h][check]; ok {
					vals = append(vals, v)
				}
			}
			if len(vals) == 0 {
				continue
			}
			sort.Float64s(vals)
			pts = append(pts, ScoreSeriesPoint{
				T: b, N: len(vals),
				P25: roundScore(Percentile(vals, .25)), Median: roundScore(Percentile(vals, .5)),
				P75: roundScore(Percentile(vals, .75)),
			})
		}
		if len(pts) == 0 {
			continue
		}
		out = append(out, ScoreSeriesCheck{Name: check, Points: pts})
	}
	return out, nil
}

func repeat(s string, n int) string {
	if n <= 0 {
		return ""
	}
	out := s
	for i := 1; i < n; i++ {
		out += s
	}
	return out
}

func anyStrings(ss []string) []any {
	out := make([]any, len(ss))
	for i, s := range ss {
		out[i] = s
	}
	return out
}
