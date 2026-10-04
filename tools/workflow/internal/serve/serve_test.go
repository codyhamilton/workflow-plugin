package serve

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

func do(t *testing.T, h http.Handler, method, url, key, body string) (int, string) {
	req := httptest.NewRequest(method, url, strings.NewReader(body))
	if key != "" {
		req.Header.Set("Authorization", "Bearer "+key)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec.Code, rec.Body.String()
}

func newServer(t *testing.T, disable bool) (*Server, string) {
	dir := t.TempDir()
	s := New(Config{Data: dir, Keys: []KeyPair{{"a", "ka"}, {"b", "kb"}}}, Options{DisableWorker: disable, PollInterval: 50 * time.Millisecond})
	t.Cleanup(func() { s.Close() })
	return s, dir
}

func artBody(content string) string {
	b, _ := json.Marshal(map[string]any{"facts": []any{map[string]any{"id": "q#0", "type": "artifact_version", "conversation_id": "c", "harness": "h",
		"event": "w", "ts": 1, "repo_id": "r", "path": "docs/plans/01-x/DESIGN.md", "content": content, "content_hash": keys.ContentHash([]byte(content)), "source": "worktree"}}})
	return string(b)
}

func TestPending(t *testing.T) {
	s, dir := newServer(t, true)
	h := s.Handler()
	content := "# hello\n"
	hash := keys.ContentHash([]byte(content))
	if code, body := do(t, h, "POST", "/v1/ingest", "ka", artBody(content)); code != 200 || !strings.Contains(body, `"accepted"`) {
		t.Fatal(code, body)
	}
	got, err := os.ReadFile(filepath.Join(dir, "a", "pending", hash))
	if err != nil || string(got) != content {
		t.Fatalf("pending: %v %q", err, got)
	}
	if _, err := os.Stat(filepath.Join(dir, "a", "blobs", hash[:2], hash)); err == nil {
		t.Fatal("blob present while worker disabled")
	}
	if _, body := do(t, h, "GET", "/v1/health", "", ""); !strings.Contains(body, `"pending":1`) {
		t.Fatal(body)
	}
	s.StartWorker()
	deadline := time.Now().Add(5 * time.Second)
	for {
		code, body := do(t, h, "GET", "/v1/artifacts?repo_id=r&path=docs/plans/01-x/DESIGN.md", "ka", "")
		if code == 200 && strings.Contains(body, `"verdict":"unscreened"`) {
			if !strings.Contains(body, `"kind":"design"`) || !strings.Contains(body, `"scores":[]`) {
				t.Fatal(body)
			}
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("never promoted", code, body)
		}
		time.Sleep(20 * time.Millisecond)
	}
	if _, err := os.Stat(filepath.Join(dir, "a", "blobs", hash[:2], hash)); err != nil {
		t.Fatal(err)
	}
	if ents, _ := os.ReadDir(filepath.Join(dir, "a", "pending")); len(ents) != 0 {
		t.Fatal("pending not empty")
	}
	if code, _ := do(t, h, "GET", "/v1/artifacts?repo_id=r&path=docs/plans/01-x/DESIGN.md", "kb", ""); code != 404 {
		t.Fatal("tenant b saw a's artifact:", code)
	}
}

func TestPendingLeftoverOnOpen(t *testing.T) {
	dir := t.TempDir()
	s := New(Config{Data: dir, Keys: []KeyPair{{"a", "ka"}}}, Options{DisableWorker: true})
	do(t, s.Handler(), "POST", "/v1/ingest", "ka", artBody("left\n"))
	s.Close()
	s = New(Config{Data: dir, Keys: []KeyPair{{"a", "ka"}}}, Options{PollInterval: time.Hour})
	defer s.Close()
	do(t, s.Handler(), "GET", "/v1/health", "", "") // no tenant open yet
	do(t, s.Handler(), "GET", "/v1/artifacts?repo_id=r&path=p", "ka", "")
	h := keys.ContentHash([]byte("left\n"))
	for i := 0; i < 200; i++ {
		if _, err := os.Stat(filepath.Join(dir, "a", "blobs", h[:2], h)); err == nil {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
	t.Fatal("leftover pending not processed on open")
}

func TestHTTPErrors(t *testing.T) {
	s, _ := newServer(t, true)
	h := s.Handler()
	cases := []struct {
		m, u, k, b string
		want       int
	}{
		{"POST", "/v1/ingest", "", `{"facts":[]}`, 401},
		{"POST", "/v1/ingest", "wrong", `{"facts":[]}`, 401},
		{"POST", "/v1/ingest", "ka", `nope`, 400},
		{"POST", "/v1/ingest", "ka", `{"x":1}`, 400},
		{"POST", "/v1/ingest", "ka", `{"facts":[]}`, 200},
		{"GET", "/v1/ingest", "ka", ``, 405},
		{"POST", "/v1/artifacts", "ka", ``, 405},
		{"GET", "/v1/artifacts?repo_id=r", "ka", ``, 400},
		{"GET", "/v1/artifacts?repo_id=r&path=p", "ka", ``, 404},
		{"POST", "/v1/ingest", "ka", `{"facts":["` + strings.Repeat("x", 17<<20) + `"]}`, 413},
	}
	for _, c := range cases {
		if code, body := do(t, h, c.m, c.u, c.k, c.b); code != c.want {
			t.Errorf("%s %s: %d want %d (%.80s)", c.m, c.u, code, c.want, body)
		}
	}
	if _, body := do(t, h, "POST", "/v1/ingest", "ka", `{"facts":[]}`); !bytes.Contains([]byte(body), []byte(`"results":[]`)) {
		t.Fatal(body)
	}
}

func TestParseKeys(t *testing.T) {
	for _, bad := range []string{"", "a", "a=", "=k", "a=k,b=k", "a=k,a=j", "-x=k", "a b=k"} {
		if _, err := ParseKeys(bad); err == nil {
			t.Errorf("%q accepted", bad)
		} else if strings.Contains(err.Error(), "=k") && bad != "" && strings.Contains(err.Error(), "k,") {
			t.Errorf("error leaks key: %v", err)
		}
	}
	if kp, err := ParseKeys("a=ka,b.c-d=kb"); err != nil || len(kp) != 2 {
		t.Fatal(kp, err)
	}
}

// Close must not wait out a scorer call in flight: the worker's context is cancelled.
func TestCloseCancelsInFlightScreen(t *testing.T) {
	dir := t.TempDir()
	started := make(chan struct{}, 1)
	step := func(ctx context.Context, _ *store.Tenant, _ string) error {
		select {
		case started <- struct{}{}:
		default:
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(30 * time.Second):
			return nil
		}
	}
	s := New(Config{Data: dir, Keys: []KeyPair{{"a", "ka"}}}, Options{PollInterval: 20 * time.Millisecond, ScreenStep: step})
	content := "# d\n"
	body := `{"facts":[{"id":"q#0","type":"artifact_version","conversation_id":"c","harness":"h","event":"w","ts":1,"repo_id":"r","path":"docs/plans/01-x/DESIGN.md","content":"# d\n","content_hash":"` + keys.ContentHash([]byte(content)) + `","source":"worktree"}]}`
	if code, b := do(t, s.Handler(), "POST", "/v1/ingest", "ka", body); code != 200 {
		t.Fatal(code, b)
	}
	select {
	case <-started:
	case <-time.After(5 * time.Second):
		t.Fatal("screen step never ran")
	}
	t0 := time.Now()
	s.Close()
	if d := time.Since(t0); d > 5*time.Second {
		t.Fatalf("Close took %v with a screen in flight", d)
	}
}
