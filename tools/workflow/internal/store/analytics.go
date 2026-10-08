package store

// Analytics reads for the workflow analytics site (plan 10, phase 1). Every function reads one
// tenant's facts, rejections, screens and scores through t.rdb with parameterised SQL.
//
// Clocks: facts.ts is REAL Unix seconds; rejections.at is INTEGER Unix nanoseconds. The window is
// inclusive at both ends in each unit.

import (
	"context"
	"database/sql/driver"
	"fmt"
	"path"
	"sort"
	"strings"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"modernc.org/sqlite"
)

func init() {
	// wf_kind(path) is keys.Kind; wf_plan(path) is the <plan> segment, "" unless the path has a kind.
	sqlite.RegisterDeterministicScalarFunction("wf_kind", 1, func(_ *sqlite.FunctionContext, args []driver.Value) (driver.Value, error) {
		s, _ := args[0].(string)
		return keys.Kind(s), nil
	})
	sqlite.RegisterDeterministicScalarFunction("wf_plan", 1, func(_ *sqlite.FunctionContext, args []driver.Value) (driver.Value, error) {
		s, _ := args[0].(string)
		return planOf(s), nil
	})
}

func planOf(p string) string {
	if keys.Kind(p) == "" {
		return ""
	}
	parts := strings.Split(path.Clean(strings.ReplaceAll(p, "\\", "/")), "/")
	return parts[2] // docs/plans/<plan>/...
}

// AnalyticsFilter is the shared filter. Empty lists mean no constraint; values within a list are
// OR, different lists are AND. A row with no value for a dimension has the value "".
type AnalyticsFilter struct {
	From, To                       time.Time // inclusive
	Repos, Harnesses, Kinds, Plans []string
}

type ToolCount struct {
	Name string
	N    int
}
type Facets struct {
	Repos, Harnesses, Kinds, Plans, Events []string
	Tools                                  []ToolCount
}
type Summary struct {
	Conversations, HookEvents, ArtifactVersions, DistinctContent int
	ByKind                                                       map[string]int
	BySource                                                     map[string]int
	Commits                                                      int
	Rejections                                                   map[string]int
	Screens                                                      map[string]int
}
type SeriesPoint struct {
	Key, T string
	N      int
}
type ExecRow struct {
	RepoID, Plan, ConversationID, BriefPath, Harness, Shape string
	TS                                                      float64
}
type ConvRow struct {
	ConversationID, Harness               string
	Repos, Kinds                          []string
	FirstTS, LastTS                       float64
	HookEvents, ArtifactVersions, Commits int
}
type ExploreRow struct {
	Type                                                                                                       string
	TS                                                                                                         float64
	Harness, RepoID, Plan, Kind, Event, Tool, Path, ConversationID, Source, SHA, ScreenVerdict, RejectionStage string
}

const (
	toolExpr   = `COALESCE(CAST(json_extract(raw,'$.payload.tool_name') AS TEXT),'')`
	sourceExpr = `COALESCE(CAST(json_extract(raw,'$.source') AS TEXT),'')`
	shaExpr    = `COALESCE(CAST(json_extract(raw,'$.sha') AS TEXT),'')`
)

func inList(expr string, vals []string, args *[]any) string {
	if len(vals) == 0 {
		return ""
	}
	for _, v := range vals {
		*args = append(*args, v)
	}
	return " AND " + expr + " IN (?" + strings.Repeat(",?", len(vals)-1) + ")"
}

func seconds(t time.Time) float64 { return float64(t.UnixNano()) / 1e9 }

// factWhere is the shared filter over a facts row (unqualified columns).
func (f AnalyticsFilter) factWhere() (string, []any) {
	args := []any{seconds(f.From), seconds(f.To)}
	w := "ts >= ? AND ts <= ?"
	w += inList("repo_id", f.Repos, &args)
	w += inList("harness", f.Harnesses, &args)
	w += inList("wf_kind(path)", f.Kinds, &args)
	w += inList("wf_plan(path)", f.Plans, &args)
	return w, args
}

// rejWhere is the shared filter over a rejections row: window on at (ns), repo_id and harness are
// always "", kind and plan come from path.
func (f AnalyticsFilter) rejWhere() (string, []any) {
	args := []any{f.From.UnixNano(), f.To.UnixNano()}
	w := "at >= ? AND at <= ?"
	w += inList("''", f.Repos, &args)
	w += inList("''", f.Harnesses, &args)
	w += inList("wf_kind(path)", f.Kinds, &args)
	w += inList("wf_plan(path)", f.Plans, &args)
	return w, args
}

func (t *Tenant) strings(ctx context.Context, q string, args ...any) ([]string, error) {
	rows, err := t.rdb.QueryContext(ctx, q, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var s string
		if err := rows.Scan(&s); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}

func (t *Tenant) Facets(ctx context.Context, f AnalyticsFilter) (Facets, error) {
	w, args := f.factWhere()
	var out Facets
	var err error
	for _, d := range []struct {
		dst  *[]string
		expr string
	}{{&out.Repos, "repo_id"}, {&out.Harnesses, "harness"}, {&out.Plans, "wf_plan(path)"}, {&out.Events, "event"}} {
		if *d.dst, err = t.strings(ctx, `SELECT DISTINCT `+d.expr+` AS v FROM facts WHERE `+w+` ORDER BY v`, args...); err != nil {
			return out, err
		}
	}
	ks, err := t.strings(ctx, `SELECT DISTINCT wf_kind(path) FROM facts WHERE `+w, args...)
	if err != nil {
		return out, err
	}
	have := map[string]bool{}
	for _, k := range ks {
		have[k] = true
	}
	for _, k := range []string{"design", "brief", "report"} {
		if have[k] {
			out.Kinds = append(out.Kinds, k)
		}
	}
	rows, err := t.rdb.QueryContext(ctx, `SELECT `+toolExpr+` AS tname, count(*) AS n FROM facts
		WHERE type='hook_event' AND `+w+` GROUP BY tname HAVING tname != '' ORDER BY n DESC, tname ASC LIMIT 100`, args...)
	if err != nil {
		return out, err
	}
	defer rows.Close()
	for rows.Next() {
		var c ToolCount
		if err := rows.Scan(&c.Name, &c.N); err != nil {
			return out, err
		}
		out.Tools = append(out.Tools, c)
	}
	return out, rows.Err()
}

func (t *Tenant) Summary(ctx context.Context, f AnalyticsFilter) (Summary, error) {
	s := Summary{ByKind: map[string]int{"design": 0, "brief": 0, "report": 0, "other": 0},
		BySource:   map[string]int{"worktree": 0, "commit": 0},
		Rejections: map[string]int{"precheck": 0, "screen": 0},
		Screens:    map[string]int{"pass": 0, "unscreened": 0}}
	w, args := f.factWhere()
	err := t.rdb.QueryRowContext(ctx, `SELECT count(DISTINCT conversation_id),
		COALESCE(SUM(type='hook_event'),0), COALESCE(SUM(type='artifact_version'),0),
		count(DISTINCT CASE WHEN type='artifact_version' THEN content_hash END), COALESCE(SUM(type='commit'),0)
		FROM facts WHERE `+w, args...).Scan(&s.Conversations, &s.HookEvents, &s.ArtifactVersions, &s.DistinctContent, &s.Commits)
	if err != nil {
		return s, err
	}
	rows, err := t.rdb.QueryContext(ctx, `SELECT COALESCE(NULLIF(wf_kind(path),''),'other'), `+sourceExpr+`, count(*)
		FROM facts WHERE type='artifact_version' AND `+w+` GROUP BY 1, 2`, args...)
	if err != nil {
		return s, err
	}
	for rows.Next() {
		var k, src string
		var n int
		if err := rows.Scan(&k, &src, &n); err != nil {
			rows.Close()
			return s, err
		}
		s.ByKind[k] += n
		if _, ok := s.BySource[src]; ok {
			s.BySource[src] += n
		}
	}
	rows.Close()
	rw, rargs := f.rejWhere()
	rows, err = t.rdb.QueryContext(ctx, `SELECT stage, count(*) FROM rejections WHERE `+rw+` GROUP BY stage`, rargs...)
	if err != nil {
		return s, err
	}
	for rows.Next() {
		var st string
		var n int
		if err := rows.Scan(&st, &n); err != nil {
			rows.Close()
			return s, err
		}
		if _, ok := s.Rejections[st]; ok {
			s.Rejections[st] = n
		}
	}
	rows.Close()
	// Latest screen (by id) per distinct content hash of the filtered in-window versions.
	rows, err = t.rdb.QueryContext(ctx, `SELECT v, count(*) FROM (
		SELECT (SELECT verdict FROM screens s WHERE s.content_hash=h.content_hash ORDER BY s.id DESC LIMIT 1) AS v
		FROM (SELECT DISTINCT content_hash FROM facts WHERE type='artifact_version' AND content_hash != '' AND `+w+`) h)
		WHERE v IN ('pass','unscreened') GROUP BY v`, args...)
	if err != nil {
		return s, err
	}
	defer rows.Close()
	for rows.Next() {
		var v string
		var n int
		if err := rows.Scan(&v, &n); err != nil {
			return s, err
		}
		s.Screens[v] = n
	}
	return s, rows.Err()
}

// Series: see the brief for metric/bucket/group. The caller validates pairings; an unsupported
// one is an error.
func (t *Tenant) Series(ctx context.Context, f AnalyticsFilter, metric, bucket, group string) ([]SeriesPoint, error) {
	bucketOf := func(ts string) (string, error) {
		switch bucket {
		case "day":
			return `strftime('%Y-%m-%d', ` + ts + `, 'unixepoch')`, nil
		case "week": // Monday of the ISO week, UTC
			return `date(` + ts + `, 'unixepoch', 'weekday 0', '-6 days')`, nil
		}
		return "", fmt.Errorf("store: unknown bucket %q", bucket)
	}
	b, err := bucketOf("ts")
	if err != nil {
		return nil, err
	}
	var q string
	var args []any
	if metric == "rejections" {
		if group != "none" && group != "stage" {
			return nil, fmt.Errorf("store: group %q not valid for rejections", group)
		}
		key := "'all'"
		if group == "stage" {
			key = "stage"
		}
		rb, _ := bucketOf("at/1e9")
		var w string
		w, args = f.rejWhere()
		q = `SELECT ` + key + ` AS k, ` + rb + ` AS t, count(*) FROM rejections WHERE ` + w + ` GROUP BY k, t ORDER BY k, t`
	} else {
		groups := map[string]string{"none": "'all'", "harness": "harness", "repo_id": "repo_id", "event": "event",
			"tool": toolExpr, "kind": "wf_kind(path)", "plan": "wf_plan(path)", "source": sourceExpr}
		key, ok := groups[group]
		if !ok {
			return nil, fmt.Errorf("store: unknown group %q", group)
		}
		agg, typ := "count(*)", ""
		switch metric {
		case "hook_events":
			typ = "type='hook_event' AND "
		case "artifact_versions":
			typ = "type='artifact_version' AND "
		case "commits":
			typ = "type='commit' AND "
		case "conversations":
			agg = "count(DISTINCT conversation_id)"
		default:
			return nil, fmt.Errorf("store: unknown metric %q", metric)
		}
		var w string
		w, args = f.factWhere()
		q = `SELECT ` + key + ` AS k, ` + b + ` AS t, ` + agg + ` FROM facts WHERE ` + typ + w + ` GROUP BY k, t ORDER BY k, t`
	}
	rows, err := t.rdb.QueryContext(ctx, q, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []SeriesPoint
	for rows.Next() {
		var p SeriesPoint
		if err := rows.Scan(&p.Key, &p.T, &p.N); err != nil {
			return nil, err
		}
		if p.N > 0 {
			out = append(out, p)
		}
	}
	return out, rows.Err()
}

// WindowScores returns the latest score per (content_hash, check) over distinct content hashes of
// filtered in-window artifact_version rows of kind; f.Kinds is ignored. Values sort ascending.
func (t *Tenant) WindowScores(ctx context.Context, f AnalyticsFilter, kind string) (map[string][]float64, error) {
	f.Kinds = nil
	w, args := f.factWhere()
	args = append([]any{kind}, args...)
	rows, err := t.rdb.QueryContext(ctx, `
	WITH h AS (SELECT DISTINCT content_hash FROM facts
		WHERE type='artifact_version' AND content_hash != '' AND wf_kind(path)=? AND `+w+`),
	s AS (SELECT content_hash, check_name, result,
		ROW_NUMBER() OVER (PARTITION BY content_hash, check_name ORDER BY id DESC) AS rn FROM scores)
	SELECT s.check_name, s.result FROM s JOIN h ON h.content_hash = s.content_hash
	WHERE s.rn = 1 ORDER BY s.check_name, s.result`, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[string][]float64{}
	for rows.Next() {
		var c string
		var r float64
		if err := rows.Scan(&c, &r); err != nil {
			return nil, err
		}
		out[c] = append(out[c], r)
	}
	return out, rows.Err()
}

// Executions lists one row per in-window brief (repo, conversation, path). Commit and report facts
// count whatever their ts; a report must be in the same conversation and repo as the brief.
func (t *Tenant) Executions(ctx context.Context, f AnalyticsFilter) ([]ExecRow, error) {
	w, args := f.factWhere()
	rows, err := t.rdb.QueryContext(ctx, `
	WITH b AS (
		SELECT repo_id, conversation_id, path, harness, ts,
			ROW_NUMBER() OVER (PARTITION BY repo_id, conversation_id, path ORDER BY ts, rowid) AS rn
		FROM facts WHERE type='artifact_version' AND wf_kind(path)='brief' AND `+w+`)
	SELECT repo_id, wf_plan(path), conversation_id, path, harness, ts,
		CASE WHEN EXISTS (SELECT 1 FROM facts c WHERE c.type='commit' AND c.conversation_id=b.conversation_id AND c.repo_id=b.repo_id)
			THEN CASE WHEN EXISTS (SELECT 1 FROM facts r WHERE r.type='artifact_version' AND r.conversation_id=b.conversation_id
				AND r.repo_id=b.repo_id AND r.path = 'docs/plans/' || wf_plan(b.path) || '/reports/' || substr(b.path, length('docs/plans/' || wf_plan(b.path) || '/briefs/') + 1))
				THEN 'complete' ELSE 'unreported' END
			ELSE 'started' END
	FROM b WHERE rn = 1 ORDER BY ts DESC, conversation_id, path, repo_id`, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []ExecRow
	for rows.Next() {
		var r ExecRow
		if err := rows.Scan(&r.RepoID, &r.Plan, &r.ConversationID, &r.BriefPath, &r.Harness, &r.TS, &r.Shape); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rows.Err()
}

// Conversations aggregates the filtered in-window facts per conversation.
func (t *Tenant) Conversations(ctx context.Context, f AnalyticsFilter) ([]ConvRow, error) {
	w, args := f.factWhere()
	rows, err := t.rdb.QueryContext(ctx, `SELECT conversation_id, harness, repo_id, type, ts, wf_kind(path) FROM facts WHERE `+w, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	type acc struct {
		row       ConvRow
		harness   map[string]int
		repos, ks map[string]bool
	}
	m := map[string]*acc{}
	for rows.Next() {
		var conv, h, repo, typ, kind string
		var ts float64
		if err := rows.Scan(&conv, &h, &repo, &typ, &ts, &kind); err != nil {
			return nil, err
		}
		a := m[conv]
		if a == nil {
			a = &acc{row: ConvRow{ConversationID: conv, FirstTS: ts, LastTS: ts}, harness: map[string]int{}, repos: map[string]bool{}, ks: map[string]bool{}}
			m[conv] = a
		}
		a.row.FirstTS = min(a.row.FirstTS, ts)
		a.row.LastTS = max(a.row.LastTS, ts)
		a.harness[h]++
		a.repos[repo] = true
		if kind != "" {
			a.ks[kind] = true
		}
		switch typ {
		case "hook_event":
			a.row.HookEvents++
		case "artifact_version":
			a.row.ArtifactVersions++
		case "commit":
			a.row.Commits++
		}
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	var out []ConvRow
	for _, a := range m {
		best := 0
		for h, n := range a.harness { // most frequent; ties to the smaller name
			if n > best || (n == best && h < a.row.Harness) {
				a.row.Harness, best = h, n
			}
		}
		for r := range a.repos {
			a.row.Repos = append(a.row.Repos, r)
		}
		for k := range a.ks {
			a.row.Kinds = append(a.row.Kinds, k)
		}
		sort.Strings(a.row.Repos)
		sort.Strings(a.row.Kinds)
		out = append(out, a.row)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].LastTS != out[j].LastTS {
			return out[i].LastTS > out[j].LastTS
		}
		return out[i].ConversationID < out[j].ConversationID
	})
	return out, nil
}

// Explore returns filtered in-window facts and rejections, newest first (rejections by at). Ties
// break by a stable key: row_hash for facts, "rej-<20-digit id>" for rejections, ascending (so at
// the same instant facts precede rejections). It reads at most limit+1 rows and reports whether
// more than limit matched.
func (t *Tenant) Explore(ctx context.Context, f AnalyticsFilter, limit int) ([]ExploreRow, bool, error) {
	fw, fargs := f.factWhere()
	rw, rargs := f.rejWhere()
	args := append(append(fargs, rargs...), limit+1)
	rows, err := t.rdb.QueryContext(ctx, `
	SELECT type, ts, harness, repo_id, plan, kind, event, tool, path, conversation_id, source, sha, verdict, stage FROM (
		SELECT type, ts, harness, repo_id, wf_plan(path) AS plan, wf_kind(path) AS kind, event,
			CASE WHEN type='hook_event' THEN `+toolExpr+` ELSE '' END AS tool, path, conversation_id,
			`+sourceExpr+` AS source, `+shaExpr+` AS sha,
			COALESCE((SELECT verdict FROM screens s WHERE s.content_hash=facts.content_hash AND facts.content_hash != '' ORDER BY s.id DESC LIMIT 1),'') AS verdict,
			'' AS stage, row_hash AS k
		FROM facts WHERE `+fw+`
		UNION ALL
		SELECT 'rejection', at/1e9, '', '', wf_plan(path), wf_kind(path), '', '', path, conversation_id, '', '', '', stage,
			printf('rej-%020d', id)
		FROM rejections WHERE `+rw+`)
	ORDER BY ts DESC, k ASC LIMIT ?`, args...)
	if err != nil {
		return nil, false, err
	}
	defer rows.Close()
	var out []ExploreRow
	for rows.Next() {
		var r ExploreRow
		if err := rows.Scan(&r.Type, &r.TS, &r.Harness, &r.RepoID, &r.Plan, &r.Kind, &r.Event, &r.Tool, &r.Path,
			&r.ConversationID, &r.Source, &r.SHA, &r.ScreenVerdict, &r.RejectionStage); err != nil {
			return nil, false, err
		}
		out = append(out, r)
	}
	if err := rows.Err(); err != nil {
		return nil, false, err
	}
	truncated := len(out) > limit
	if truncated {
		out = out[:limit]
	}
	return out, truncated, nil
}
