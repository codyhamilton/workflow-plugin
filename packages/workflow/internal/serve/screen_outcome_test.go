package serve

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	_ "modernc.org/sqlite"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/scorer"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/screen"
)

const (
	designPath = "docs/plans/01-x/DESIGN.md"
	reportPath = "docs/plans/01-x/reports/1-01-a.md"
)

// modeScorer is a scorer.Fake whose behaviour the test can switch while the worker runs.
type modeScorer struct {
	mu   sync.Mutex
	mode string // "pass", "flag", "down"
	n    int
	fake scorer.Fake
}

func (m *modeScorer) set(mode string) { m.mu.Lock(); m.mode = mode; m.mu.Unlock() }
func (m *modeScorer) Name() string    { return "fake" }
func (m *modeScorer) Screen(ctx context.Context, c []byte, k []string) (scorer.Verdict, error) {
	m.mu.Lock()
	mode := m.mode
	m.n++
	m.mu.Unlock()
	switch mode {
	case "down":
		return scorer.Verdict{}, fmt.Errorf("fake: %w", scorer.ErrUnreachable)
	case "flag":
		return m.fake.Verdict, nil
	}
	return scorer.Verdict{}, nil
}
func (m *modeScorer) Score(ctx context.Context, c []byte, k []string) ([]scorer.Score, error) {
	return []scorer.Score{{Check: "x.one", Result: 0.5}, {Check: "x.two", Result: 1}}, nil
}

func (m *modeScorer) calls() int { m.mu.Lock(); defer m.mu.Unlock(); return m.n }

func artBodyAt(path, content string) string {
	b, _ := json.Marshal(map[string]any{"facts": []any{map[string]any{"id": "q#0", "type": "artifact_version", "conversation_id": "c", "harness": "h",
		"event": "w", "ts": 1, "repo_id": "r", "path": path, "content": content, "content_hash": keys.ContentHash([]byte(content)), "source": "worktree"}}})
	return string(b)
}

func queryInt(t *testing.T, dir, q string, args ...any) int {
	t.Helper()
	db, err := sql.Open("sqlite", "file:"+filepath.Join(dir, "a", "ledger.db")+"?mode=ro")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var n int
	if err := db.QueryRow(q, args...).Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}

func waitFor(t *testing.T, what string, f func() bool) {
	t.Helper()
	for i := 0; i < 250; i++ {
		if f() {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatalf("timed out: %s", what)
}

func blobOf(dir, content string) string {
	h := keys.ContentHash([]byte(content))
	return filepath.Join(dir, "a", "blobs", h[:2], h)
}
func pendingOf(dir, content string) string {
	return filepath.Join(dir, "a", "pending", keys.ContentHash([]byte(content)))
}
func has(p string) bool { _, err := os.Stat(p); return err == nil }

func healthField(t *testing.T, s *Server, f string) int {
	_, body := do(t, s.Handler(), "GET", "/v1/health", "", "")
	var m map[string]any
	if err := json.Unmarshal([]byte(body), &m); err != nil {
		t.Fatal(body)
	}
	return int(m[f].(float64))
}

func newScreened(t *testing.T, dir string, disable bool, sc *modeScorer, backoff time.Duration) *Server {
	opts := Options{DisableWorker: disable, PollInterval: 30 * time.Millisecond, ScreenBackoff: backoff}
	if sc != nil {
		opts.ScreenStep = screen.Step(sc)
	}
	s := New(Config{Data: dir, Keys: []KeyPair{{"a", "ka"}}}, opts)
	t.Cleanup(func() { s.Close() })
	return s
}

func post(t *testing.T, s *Server, path, content string) {
	t.Helper()
	if code, body := do(t, s.Handler(), "POST", "/v1/ingest", "ka", artBodyAt(path, content)); code != 200 || !strings.Contains(body, `"accepted"`) {
		t.Fatal(code, body)
	}
}

func openTenant(t *testing.T, s *Server) {
	do(t, s.Handler(), "GET", "/v1/artifacts?repo_id=r&path=p", "ka", "")
}

func TestScreeningOutcome(t *testing.T) {
	const dc, rc = "# design\n", "# report\n"
	t.Run("pending until screened", func(t *testing.T) {
		dir := t.TempDir()
		s := newScreened(t, dir, true, &modeScorer{mode: "pass"}, 0)
		post(t, s, designPath, dc)
		if !has(pendingOf(dir, dc)) || has(blobOf(dir, dc)) || healthField(t, s, "pending") < 1 {
			t.Fatal("content not pending")
		}
	})
	t.Run("pass", func(t *testing.T) {
		dir := t.TempDir()
		sc := &modeScorer{mode: "pass"}
		s := newScreened(t, dir, false, sc, 0)
		post(t, s, designPath, dc)
		post(t, s, reportPath, rc)
		waitFor(t, "screens", func() bool { return queryInt(t, dir, `SELECT count(*) FROM screens`) == 2 })
		h := keys.ContentHash([]byte(dc))
		if !has(blobOf(dir, dc)) || has(pendingOf(dir, dc)) || !has(blobOf(dir, rc)) {
			t.Fatal("blob/pending state wrong")
		}
		if n := queryInt(t, dir, `SELECT count(*) FROM screens WHERE content_hash=? AND verdict='pass' AND scorer='fake'`, h); n != 1 {
			t.Fatalf("screen rows %d", n)
		}
		if n := queryInt(t, dir, `SELECT count(*) FROM scores WHERE content_hash=? AND scorer='fake'`, h); n != 2 {
			t.Fatalf("score rows %d", n)
		}
	})
	t.Run("pass kinds", func(t *testing.T) {
		dir := t.TempDir()
		f := &scorer.Fake{}
		s := newScreened(t, dir, false, nil, 0)
		s.screen = screen.Step(f)
		post(t, s, designPath, dc)
		post(t, s, reportPath, rc)
		waitFor(t, "screens", func() bool { return queryInt(t, dir, `SELECT count(*) FROM screens`) == 2 })
		got := map[string][]string{}
		for _, c := range f.ScoreCalls {
			got[string(c.Content)] = c.Kinds
		}
		if !reflect.DeepEqual(got, map[string][]string{dc: {"design"}, rc: {"report"}}) {
			t.Fatalf("kinds %v", got)
		}
	})
	t.Run("flag", func(t *testing.T) {
		dir := t.TempDir()
		sc := &modeScorer{mode: "flag", fake: scorer.Fake{Verdict: scorer.Verdict{Flag: true, Reason: "jev_screen credential level 3"}}}
		s := newScreened(t, dir, false, sc, 0)
		post(t, s, designPath, dc)
		waitFor(t, "rejection", func() bool { return queryInt(t, dir, `SELECT count(*) FROM rejections WHERE stage='screen'`) == 1 })
		h := keys.ContentHash([]byte(dc))
		if has(pendingOf(dir, dc)) || has(blobOf(dir, dc)) {
			t.Fatal("content survived a flag")
		}
		if n := queryInt(t, dir, `SELECT count(*) FROM rejections WHERE stage='screen' AND content_hash=? AND reason='jev_screen credential level 3' AND path=?`, h, designPath); n != 1 {
			t.Fatal("rejection row wrong")
		}
		if n := queryInt(t, dir, `SELECT count(*) FROM facts WHERE type='artifact_version' AND content_hash=?`, h); n != 1 {
			t.Fatal("fact row gone")
		}
		if n := queryInt(t, dir, `SELECT count(*) FROM screens`); n != 0 {
			t.Fatal("flagged content has a screen row")
		}
	})
	t.Run("unreachable", func(t *testing.T) {
		dir := t.TempDir()
		sc := &modeScorer{mode: "down"}
		s := newScreened(t, dir, false, sc, 300*time.Millisecond)
		post(t, s, designPath, dc)
		time.Sleep(700 * time.Millisecond) // many poll intervals (30 ms)
		if !has(pendingOf(dir, dc)) || has(blobOf(dir, dc)) {
			t.Fatal("content left pending")
		}
		if n := sc.calls(); n < 1 || n > 3 {
			t.Fatalf("scorer called %d times in 700 ms with a 300 ms backoff", n)
		}
		sc.set("pass")
		waitFor(t, "screened after recovery", func() bool { return queryInt(t, dir, `SELECT count(*) FROM screens`) == 1 })
		if !has(blobOf(dir, dc)) {
			t.Fatal("no blob after recovery")
		}
	})
	t.Run("no key", func(t *testing.T) {
		dir := t.TempDir()
		s := newScreened(t, dir, false, nil, 0)
		post(t, s, designPath, dc)
		waitFor(t, "screens", func() bool { return queryInt(t, dir, `SELECT count(*) FROM screens WHERE verdict='unscreened'`) == 1 })
		if !has(blobOf(dir, dc)) || queryInt(t, dir, `SELECT count(*) FROM scores`) != 0 {
			t.Fatal("blob or scores wrong")
		}
	})
	t.Run("crash between blob and screen row", func(t *testing.T) {
		for _, flag := range []bool{false, true} {
			dir := t.TempDir()
			content := fmt.Sprintf("# crashed %v\n", flag)
			p := blobOf(dir, content)
			os.MkdirAll(filepath.Dir(p), 0o700)
			os.WriteFile(p, []byte(content), 0o600)
			sc := &modeScorer{mode: "pass"}
			if flag {
				sc = &modeScorer{mode: "flag", fake: scorer.Fake{Verdict: scorer.Verdict{Flag: true, Reason: "r"}}}
			}
			s := newScreened(t, dir, false, sc, 0)
			openTenant(t, s)
			if flag {
				waitFor(t, "rejection", func() bool { return queryInt(t, dir, `SELECT count(*) FROM rejections WHERE stage='screen'`) == 1 })
				if has(p) {
					t.Fatal("flagged blob survived")
				}
			} else {
				waitFor(t, "screen row", func() bool { return queryInt(t, dir, `SELECT count(*) FROM screens WHERE verdict='pass'`) == 1 })
				if !has(p) {
					t.Fatal("blob lost")
				}
			}
		}
	})
	t.Run("screen gap", func(t *testing.T) {
		dir := t.TempDir()
		s := newScreened(t, dir, true, nil, 0)
		post(t, s, designPath, dc)
		if err := os.Remove(pendingOf(dir, dc)); err != nil {
			t.Fatal(err)
		}
		s.Close()
		s = newScreened(t, dir, false, nil, 0)
		openTenant(t, s)
		waitFor(t, "gap counted", func() bool { return healthField(t, s, "screen_gaps") == 1 })
		// Carried 2: a resend of the same fact.
		if code, body := do(t, s.Handler(), "POST", "/v1/ingest", "ka", artBodyAt(designPath, dc)); code != 200 || !strings.Contains(body, `"duplicate"`) {
			t.Fatal(code, body)
		}
		recreated := has(pendingOf(dir, dc)) || has(blobOf(dir, dc))
		t.Logf("carried 2: resend returned duplicate; pending or blob re-created = %v", recreated)
		if !recreated {
			t.Fatal("resend did not re-create the content; the fix belongs in ingest")
		}
		waitFor(t, "screened", func() bool { return has(blobOf(dir, dc)) })
		s.Close()
		s = newScreened(t, dir, false, nil, 0)
		openTenant(t, s)
		time.Sleep(200 * time.Millisecond)
		if n := healthField(t, s, "screen_gaps"); n != 0 {
			t.Fatalf("gap did not clear: %d", n)
		}
	})
	t.Run("report checks", func(t *testing.T) {
		c, err := scorer.LoadChecks("../../../quality")
		if err != nil {
			t.Fatal(err)
		}
		if n := c.Count("report"); n != 5 {
			t.Fatalf("report checks %d", n)
		}
	})
}
