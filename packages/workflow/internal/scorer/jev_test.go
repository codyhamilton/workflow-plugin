package scorer

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

const testKey = "sk-test-KEY-0123456789"
const secretText = "SECRET-CONTENT-MARKER"

func testChecks(t *testing.T) Checks {
	t.Helper()
	d := t.TempDir()
	write(t, d+"/criteria.json", `{"brief":{"jev":{"b.one":{"q":"Q1","levels":["a","b","c","d"],"invert":true},"b.two":{"q":"Q2","levels":["a","b","c","d"]}}},"design":{"jev":{"d.one":{"q":"D1","levels":["a","b"]}}}}`)
	cs, err := LoadChecks(d)
	if err != nil {
		t.Fatal(err)
	}
	return cs
}

type fakeAPI struct {
	srv    *httptest.Server
	calls  atomic.Int32
	last   map[string]any
	header http.Header
	method string
	path   string
	status int
	body   string // if set, returned verbatim
	screen float64
	raw    map[string]int
	marker string // when set, a snapshot holding it is answered with screen level 3
	snaps  []string
	withQs []int // question count of each request
}

func newAPI(t *testing.T) *fakeAPI {
	f := &fakeAPI{status: 200, raw: map[string]int{}}
	f.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		f.calls.Add(1)
		f.method, f.path, f.header = r.Method, r.URL.Path, r.Header.Clone()
		b, _ := io.ReadAll(r.Body)
		f.last = nil
		_ = json.Unmarshal(b, &f.last)
		snap, _ := f.last["state"].(map[string]any)["snapshot"].(string)
		qn, _ := f.last["questions"].(map[string]any)
		f.snaps = append(f.snaps, snap)
		f.withQs = append(f.withQs, len(qn))
		screenScore := f.screen
		if f.marker != "" && strings.Contains(snap, f.marker) {
			screenScore = 3
		}
		w.WriteHeader(f.status)
		if f.body != "" {
			io.WriteString(w, f.body)
			return
		}
		ans := map[string]any{"screen_credential": map[string]any{"score": screenScore}}
		for k, v := range f.raw {
			ans[k] = map[string]any{"score": v}
		}
		json.NewEncoder(w).Encode(map[string]any{"model": "jev-1.13.0", "answers": ans})
	}))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeAPI) jev(t *testing.T) *Jev {
	j := NewJev(testKey, testChecks(t))
	j.URL = f.srv.URL + "/v1/systemone"
	return j
}

func TestJev(t *testing.T) {
	ctx := context.Background()
	t.Run("request shape and one request", func(t *testing.T) {
		f := newAPI(t)
		f.raw = map[string]int{"b.one": 3, "b.two": 2, "d.one": 1}
		j := f.jev(t)
		content := []byte(strings.Repeat("x", 60000))
		v, err := j.Screen(ctx, content, []string{"brief", "design"})
		if err != nil || v.Flag {
			t.Fatalf("screen = %+v, %v", v, err)
		}
		if f.method != "POST" || f.path != "/v1/systemone" {
			t.Errorf("%s %s", f.method, f.path)
		}
		if f.header.Get("Authorization") != "Bearer "+testKey || f.header.Get("Content-Type") != "application/json" || f.header.Get("Accept") != "application/json" {
			t.Errorf("headers wrong")
		}
		if f.last["model"] != "jev-1.13.0" {
			t.Errorf("model = %v", f.last["model"])
		}
		snap := f.last["state"].(map[string]any)["snapshot"].(string)
		if !strings.HasPrefix(snap, "BRIEF:\n") || len(snap) != len("BRIEF:\n")+60000 {
			t.Errorf("snapshot prefix/truncation wrong: len %d", len(snap))
		}
		qs := f.last["questions"].(map[string]any)
		for _, n := range []string{"screen_credential", "b.one", "b.two", "d.one"} {
			q, ok := qs[n].(map[string]any)
			if !ok || q["type"] != "score" || q["instructions"] == "" || q["criteria"] == nil {
				t.Errorf("question %s wrong: %v", n, q)
			}
		}
		if len(qs) != 4 {
			t.Errorf("questions = %d", len(qs))
		}
		sc, err := j.Score(ctx, content, []string{"brief", "design"})
		if err != nil {
			t.Fatal(err)
		}
		if f.calls.Load() != 1 {
			t.Errorf("requests = %d, want 1", f.calls.Load())
		}
		got := map[string]float64{}
		for _, s := range sc {
			got[s.Check] = s.Result
		}
		if len(got) != 3 || got["b.one"] != 0 || got["b.two"] != 0.667 || got["d.one"] != 0.333 {
			t.Errorf("scores = %v", got)
		}
		// answers were removed: a second Score makes its own request
		if _, err := j.Score(ctx, content, []string{"brief", "design"}); err != nil {
			t.Fatal(err)
		}
		if f.calls.Load() != 2 {
			t.Errorf("requests = %d, want 2", f.calls.Load())
		}
	})
	t.Run("raw mapping", func(t *testing.T) {
		f := newAPI(t)
		j := f.jev(t)
		for raw, want := range map[int]float64{0: 0, 1: 0.333, 2: 0.667, 3: 1} {
			f.raw = map[string]int{"b.two": raw}
			sc, err := j.Score(ctx, []byte("c"), []string{"brief"})
			if err != nil || len(sc) != 1 || sc[0].Result != want {
				t.Errorf("raw %d: %v %v", raw, sc, err)
			}
		}
	})
	t.Run("prefixes", func(t *testing.T) {
		f := newAPI(t)
		j := f.jev(t)
		for kinds, want := range map[string]string{"design": "DESIGN DOCUMENT:\n", "report": "EXECUTION REPORT:\n", "": "DOCUMENT:\n"} {
			var ks []string
			if kinds != "" {
				ks = []string{kinds}
			}
			if _, err := j.Screen(ctx, []byte("c"), ks); err != nil {
				t.Fatal(err)
			}
			if !strings.HasPrefix(f.last["state"].(map[string]any)["snapshot"].(string), want) {
				t.Errorf("%q prefix wrong", kinds)
			}
		}
	})
	t.Run("screen levels", func(t *testing.T) {
		f := newAPI(t)
		j := f.jev(t)
		// Jev answers fractionally; the level is the nearest integer.
		for _, c := range []struct {
			raw   float64
			flag  bool
			level string
		}{{0, false, ""}, {1, false, ""}, {1.4, false, ""}, {1.5, true, "2"}, {1.9, true, "2"}, {2, true, "2"}, {3, true, "3"}} {
			f.screen = c.raw
			v, err := j.Screen(ctx, []byte("c"), nil)
			if err != nil || v.Flag != c.flag {
				t.Errorf("raw %v: %+v %v", c.raw, v, err)
			}
			if c.flag && v.Reason != "screen: jev screen_credential level "+c.level {
				t.Errorf("reason = %q", v.Reason)
			}
		}
	})
	t.Run("errors", func(t *testing.T) {
		for _, c := range []struct {
			status      int
			unreachable bool
		}{{500, true}, {503, true}, {429, true}, {401, true}, {403, true}, {400, false}} {
			f := newAPI(t)
			f.status = c.status
			f.body = `{"error":"` + secretText + testKey + `"}`
			j := f.jev(t)
			_, err := j.Screen(ctx, []byte(secretText), nil)
			if err == nil || errors.Is(err, ErrUnreachable) != c.unreachable {
				t.Errorf("status %d: err = %v", c.status, err)
			}
			if err != nil && (strings.Contains(err.Error(), testKey) || strings.Contains(err.Error(), secretText)) {
				t.Errorf("status %d: error leaks: %v", c.status, err)
			}
		}
		// malformed body, and missing screen answer
		for _, body := range []string{"not json " + secretText, `{"answers":{}}`, `{"answers":{"screen_credential":{"score":"hi"}}}`} {
			f := newAPI(t)
			f.body = body
			_, err := f.jev(t).Screen(ctx, []byte(secretText), nil)
			if err == nil || errors.Is(err, ErrUnreachable) || strings.Contains(err.Error(), secretText) {
				t.Errorf("body %q: err = %v", body, err)
			}
		}
		// closed server
		f := newAPI(t)
		j := f.jev(t)
		f.srv.Close()
		_, err := j.Screen(ctx, []byte(secretText), nil)
		if !errors.Is(err, ErrUnreachable) || strings.Contains(err.Error(), testKey) || strings.Contains(err.Error(), secretText) {
			t.Errorf("closed: %v", err)
		}
	})
	t.Run("name", func(t *testing.T) {
		if n := NewJev(testKey, Checks{}).Name(); n != "jev-1.13.0" {
			t.Errorf("name = %q", n)
		}
	})
}

// Content past the first window is screened too, in overlapping screen-only windows.
func TestJevScreensPastFirstWindow(t *testing.T) {
	ctx := context.Background()
	body := func(n, at int, marker string) []byte {
		r := []rune(strings.Repeat("x", n))
		copy(r[at:], []rune(marker))
		return []byte(string(r))
	}
	const marker = "LIVE-KEY-PAST-THE-CUT"
	t.Run("marker at rune 65000 flags", func(t *testing.T) {
		f := newAPI(t)
		f.marker = marker
		v, err := f.jev(t).Screen(ctx, body(70000, 65000, marker), []string{"brief"})
		if err != nil || !v.Flag {
			t.Fatalf("verdict = %+v, %v; want flag", v, err)
		}
	})
	t.Run("marker straddling a window edge flags", func(t *testing.T) {
		f := newAPI(t)
		f.marker = marker
		// the first window ends at rune 60000; the marker spans 59990..60011
		v, err := f.jev(t).Screen(ctx, body(130000, 59990, marker), []string{"brief"})
		if err != nil || !v.Flag {
			t.Fatalf("verdict = %+v, %v; want flag", v, err)
		}
	})
	t.Run("only the first window carries checks", func(t *testing.T) {
		f := newAPI(t)
		f.raw = map[string]int{"b.one": 1, "b.two": 2}
		j := f.jev(t)
		v, err := j.Screen(ctx, body(130000, 0, ""), []string{"brief"})
		if err != nil || v.Flag {
			t.Fatalf("verdict = %+v, %v", v, err)
		}
		if len(f.withQs) < 3 || f.withQs[0] != 3 || f.withQs[1] != 1 || f.withQs[2] != 1 {
			t.Errorf("questions per request = %v, want [3 1 1 ...]", f.withQs)
		}
		if sc, err := j.Score(ctx, body(130000, 0, ""), []string{"brief"}); err != nil || len(sc) != 2 {
			t.Errorf("score = %v, %v", sc, err)
		}
	})
	t.Run("content within the first window makes one request", func(t *testing.T) {
		f := newAPI(t)
		if _, err := f.jev(t).Screen(ctx, body(60000, 0, ""), []string{"brief"}); err != nil || f.calls.Load() != 1 {
			t.Fatalf("calls = %d, %v", f.calls.Load(), err)
		}
	})
	t.Run("a later window that fails keeps the content unanswered", func(t *testing.T) {
		f := newAPI(t)
		j := f.jev(t)
		n := 0
		j.Client = &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
			if n++; n == 2 {
				return nil, errors.New("boom")
			}
			return http.DefaultTransport.RoundTrip(r)
		})}
		if _, err := j.Screen(ctx, body(70000, 0, ""), []string{"brief"}); !errors.Is(err, ErrUnreachable) {
			t.Fatalf("err = %v, want ErrUnreachable", err)
		}
	})
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestFake(t *testing.T) {
	var s Scorer = &Fake{Scores: []Score{{Check: "x", Result: 1}}}
	v, err := s.Screen(context.Background(), []byte("c"), []string{"brief"})
	if err != nil || v.Flag || s.Name() != "fake" {
		t.Fatal("fake screen")
	}
	if sc, _ := s.Score(context.Background(), []byte("c"), nil); len(sc) != 1 {
		t.Fatal("fake score")
	}
	if f := s.(*Fake); len(f.ScreenCalls) != 1 || len(f.ScoreCalls) != 1 {
		t.Fatal("calls not recorded")
	}
}

func TestJevLive(t *testing.T) {
	key := os.Getenv("TYPESAFE_API_KEY")
	if os.Getenv("WORKFLOW_JEV_LIVE") != "1" || key == "" {
		t.Skip("set WORKFLOW_JEV_LIVE=1 and TYPESAFE_API_KEY to run")
	}
	cs, err := LoadChecks(realQuality)
	if err != nil {
		t.Fatal(err)
	}
	j := NewJev(key, cs)
	doc := []byte(liveDesign)
	ctx, cancel := context.WithTimeout(context.Background(), 150*time.Second)
	defer cancel()
	v, err := j.Screen(ctx, doc, []string{"design"})
	if errors.Is(err, ErrUnreachable) {
		t.Skipf("API did not answer: %v", err)
	}
	if err != nil {
		t.Fatal(err)
	}
	if v.Flag {
		t.Fatalf("flagged: %s", v.Reason)
	}
	sc, err := j.Score(ctx, doc, []string{"design"})
	if err != nil {
		t.Fatal(err)
	}
	n := 0
	for _, s := range sc {
		t.Logf("%s = %v", s.Check, s.Result)
		if s.Result < 0 || s.Result > 1 {
			t.Errorf("%s out of range", s.Check)
		}
		if strings.HasPrefix(s.Check, "d.") {
			n++
		}
	}
	if n == 0 {
		t.Fatal("no d.* scores")
	}
	t.Logf("verdict pass, %d scores", len(sc))
}

const liveDesign = `# Design: shared notes search

## Problem
Teams keep meeting notes in a shared folder. Finding a decision from last quarter means opening
many files by hand. People ask for a way to search the notes by phrase and by date.

## Solution shape
A small indexer reads the folder on a schedule and writes a search index beside it. A command line
tool queries the index and prints matching file names with a short excerpt. The indexer owns the
index; the tool only reads it.

## Boundaries
The indexer never edits notes. The tool never writes the index. Both read the folder path from one
setting.

## Contracts
The index file is a single JSON document with one entry per note: path, modified date, and text.
The tool prints one line per match, path first.

## Phases
Phase 1: indexer builds an index for a folder of 100 notes; outcome is that a test query returns
the known note. Phase 2: tool prints matches; outcome is that a query for a known phrase prints the
expected path. Phase 3: date filter; outcome is that a date range excludes notes outside it.

## Non-goals
No web interface. No access control beyond folder permissions. No fuzzy matching in this round.

## Risks
Large folders may make indexing slow; we will measure with 10,000 notes before phase 3 and decide
whether incremental indexing is needed. This is open.
`
