package serve

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
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
	if kp, err := ParseKeys(" "); kp != nil || err != nil {
		t.Fatal("empty keys must be local mode", kp, err)
	}
	for _, bad := range []string{"a", "a=", "=k", "a=k,b=k", "a=k,a=j", "-x=k", "a b=k"} {
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

func TestLocalModeConfig(t *testing.T) {
	env := func(m map[string]string) func(string) string { return func(k string) string { return m[k] } }
	for _, addr := range []string{"", "127.0.0.1:0", "localhost:8770", "[::1]:8770", "127.0.0.2:1"} {
		c, err := ConfigFromEnv(env(map[string]string{"WORKFLOW_SERVE_ADDR": addr, "WORKFLOW_SERVE_DATA": "/d"}))
		if err != nil || !c.Local() {
			t.Errorf("%q: %v", addr, err)
		}
	}
	for _, addr := range []string{"0.0.0.0:8770", ":8770", "[::]:8770", "192.168.1.5:8770", "example.com:80"} {
		if _, err := ConfigFromEnv(env(map[string]string{"WORKFLOW_SERVE_ADDR": addr, "WORKFLOW_SERVE_DATA": "/d"})); err == nil {
			t.Errorf("%q: keyless non-loopback bind accepted", addr)
		}
	}
	if c, err := ConfigFromEnv(env(map[string]string{"WORKFLOW_SERVE_ADDR": "0.0.0.0:8770", "WORKFLOW_SERVE_DATA": "/d", "WORKFLOW_SERVE_KEYS": "a=ka"})); err != nil || c.Local() {
		t.Fatal("keyed wildcard bind refused", err)
	}
}

func TestLocalModeHTTP(t *testing.T) {
	dir := t.TempDir()
	s := New(Config{Data: dir}, Options{DisableWorker: true})
	t.Cleanup(func() { s.Close() })
	h := s.Handler()
	req := func(method, host, ctype, auth, body string) int {
		r := httptest.NewRequest(method, "http://"+host+"/v1/ingest", strings.NewReader(body))
		if ctype != "" {
			r.Header.Set("Content-Type", ctype)
		}
		if auth != "" {
			r.Header.Set("Authorization", auth)
		}
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		return w.Code
	}
	cases := []struct {
		host, ctype, auth string
		want              int
	}{
		{"127.0.0.1:8770", "application/json", "", 200},
		{"localhost:8770", "application/json; charset=utf-8", "", 200},
		{"[::1]:8770", "application/json", "Bearer anything", 200},
		{"127.0.0.1:8770", "text/plain", "", 415},
		{"127.0.0.1:8770", "", "", 415},
		{"evil.example:8770", "application/json", "", 403},
	}
	for _, c := range cases {
		if got := req("POST", c.host, c.ctype, c.auth, artBody("# local\n")); got != c.want {
			t.Errorf("%+v: got %d", c, got)
		}
	}
	if _, err := os.Stat(filepath.Join(dir, LocalTenant, "pending")); err != nil {
		t.Fatal("local tenant not used:", err)
	}
}

func TestKeyRequiredMessage(t *testing.T) {
	s, _ := newServer(t, true)
	if code, body := do(t, s.Handler(), "POST", "/v1/ingest", "", `{"facts":[]}`); code != 401 || !strings.Contains(body, "requires a key") {
		t.Fatal(code, body)
	}
	if code, body := do(t, s.Handler(), "POST", "/v1/ingest", "wrong", `{"facts":[]}`); code != 401 || strings.Contains(body, "requires a key") {
		t.Fatal(code, body)
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

// A screen error that is not "unreachable" repeats for the same input. It must be retried a
// bounded number of times, then end in a rejection the artifact read shows.
func TestPermanentScreenErrorIsBounded(t *testing.T) {
	dir := t.TempDir()
	var calls atomic.Int64
	step := func(ctx context.Context, _ *store.Tenant, _ string) error {
		calls.Add(1)
		return errors.New("scorer: HTTP 400")
	}
	s := New(Config{Data: dir, Keys: []KeyPair{{"a", "ka"}}}, Options{PollInterval: 10 * time.Millisecond, ScreenBackoff: 5 * time.Millisecond, ScreenStep: step})
	t.Cleanup(func() { s.Close() })
	if code, b := do(t, s.Handler(), "POST", "/v1/ingest", "ka", artBody("# d\n")); code != 200 {
		t.Fatal(code, b)
	}
	time.Sleep(time.Second)
	if n := calls.Load(); n > maxScreenAttempts+2 {
		t.Fatalf("screen step called %d times in 1s, want at most %d", n, maxScreenAttempts+2)
	}
	_, body := do(t, s.Handler(), "GET", "/v1/artifacts?repo_id=r&path=docs/plans/01-x/DESIGN.md", "ka", "")
	if !strings.Contains(body, `"stage":"screen"`) || !strings.Contains(body, "screen error") {
		t.Fatalf("no screen rejection in read: %s", body)
	}
	if ents, _ := os.ReadDir(filepath.Join(dir, "a", "pending")); len(ents) != 0 {
		t.Fatal("pending not cleared")
	}
}

func corsReq(h http.Handler, method, path, origin, key string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, "http://127.0.0.1:8770"+path, nil)
	if origin != "" {
		r.Header.Set("Origin", origin)
	}
	if key != "" {
		r.Header.Set("Authorization", "Bearer "+key)
	}
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	return w
}

func assertCORS(t *testing.T, w *httptest.ResponseRecorder, origin string) {
	t.Helper()
	hd := w.Header()
	if hd.Get("Access-Control-Allow-Origin") != origin ||
		hd.Get("Access-Control-Allow-Headers") != "Authorization, Content-Type" ||
		hd.Get("Access-Control-Allow-Methods") != "GET, OPTIONS" ||
		!strings.Contains(strings.Join(hd.Values("Vary"), ","), "Origin") {
		t.Errorf("origin %q: headers %v", origin, hd)
	}
	if hd.Get("Access-Control-Allow-Credentials") != "" {
		t.Error("credentials header set")
	}
}

func assertNoCORS(t *testing.T, w *httptest.ResponseRecorder, what string) {
	t.Helper()
	for k := range w.Header() {
		if strings.HasPrefix(k, "Access-Control-") {
			t.Errorf("%s: unexpected %s", what, k)
		}
	}
}

func TestCORSLocalMode(t *testing.T) {
	s := New(Config{Data: t.TempDir()}, Options{DisableWorker: true})
	t.Cleanup(func() { s.Close() })
	h := s.Handler()
	for _, o := range []string{"http://127.0.0.1:5173", "http://localhost:4000", "http://[::1]:9000"} {
		w := corsReq(h, "GET", "/v1/health", o, "")
		if w.Code != 200 {
			t.Fatal(o, w.Code)
		}
		assertCORS(t, w, o)
		w = corsReq(h, "OPTIONS", "/v1/artifacts", o, "")
		if w.Code != 204 || w.Body.Len() != 0 {
			t.Fatal(o, w.Code, w.Body.String())
		}
		assertCORS(t, w, o)
	}
	for _, o := range []string{"https://evil.example", "null", "", "http://localhost.evil.example", "ftp://127.0.0.1"} {
		assertNoCORS(t, corsReq(h, "GET", "/v1/health", o, ""), "GET "+o)
	}
	// A disallowed OPTIONS keeps today's answer.
	w := corsReq(h, "OPTIONS", "/v1/artifacts", "https://evil.example", "")
	if w.Code != 405 {
		t.Error(w.Code)
	}
	assertNoCORS(t, w, "evil OPTIONS")
}

func TestCORSKeyedMode(t *testing.T) {
	s := New(Config{Data: t.TempDir(), Keys: []KeyPair{{"a", "ka"}}, CORSOrigins: []string{"https://wf.pages.dev"}}, Options{DisableWorker: true})
	t.Cleanup(func() { s.Close() })
	h := s.Handler()
	w := corsReq(h, "GET", "/v1/checks", "https://wf.pages.dev", "ka")
	if w.Code != 200 {
		t.Fatal(w.Code)
	}
	assertCORS(t, w, "https://wf.pages.dev")
	w = corsReq(h, "OPTIONS", "/v1/artifacts", "https://wf.pages.dev", "")
	if w.Code != 204 {
		t.Fatal(w.Code)
	}
	assertCORS(t, w, "https://wf.pages.dev")
	for _, o := range []string{"https://other.pages.dev", "http://127.0.0.1:5173", "https://wf.pages.dev.evil.example", "null"} {
		assertNoCORS(t, corsReq(h, "GET", "/v1/checks", o, "ka"), o)
		w := corsReq(h, "OPTIONS", "/v1/artifacts", o, "")
		assertNoCORS(t, w, "OPTIONS "+o)
		if w.Code == 204 {
			t.Error("OPTIONS answered for", o)
		}
	}
	s2 := New(Config{Data: t.TempDir(), Keys: []KeyPair{{"a", "ka"}}}, Options{DisableWorker: true})
	t.Cleanup(func() { s2.Close() })
	assertNoCORS(t, corsReq(s2.Handler(), "GET", "/v1/checks", "https://wf.pages.dev", "ka"), "no CORSOrigins")
}

func TestCORSConfig(t *testing.T) {
	env := map[string]string{"WORKFLOW_SERVE_DATA": "/d", "WORKFLOW_SERVE_KEYS": "a=ka", "WORKFLOW_SERVE_CORS_ORIGINS": " https://a.example, ,https://b.example"}
	c, err := ConfigFromEnv(func(k string) string { return env[k] })
	if err != nil || len(c.CORSOrigins) != 2 || c.CORSOrigins[0] != "https://a.example" || c.CORSOrigins[1] != "https://b.example" {
		t.Fatal(c.CORSOrigins, err)
	}
	delete(env, "WORKFLOW_SERVE_CORS_ORIGINS")
	if c, _ := ConfigFromEnv(func(k string) string { return env[k] }); len(c.CORSOrigins) != 0 {
		t.Fatal(c.CORSOrigins)
	}
}
