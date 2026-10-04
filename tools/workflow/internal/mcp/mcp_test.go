package mcp

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"testing"
	"time"
)

const secretKey = "sk-test-KEY-0123456789abcdef"

type env struct {
	t        *testing.T
	repo, wt string
	queue    string
	cfg      string
	design   string // absolute path of the design file in repo
	stub     *httptest.Server
	hits     atomic.Int64
	drains   atomic.Int64
	mu       sync.Mutex
	artifact func() (int, any)
	baseline any
	texts    *[]string
}

func git(t *testing.T, dir string, args ...string) string {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	cmd.Env = append(os.Environ(), "GIT_CONFIG_GLOBAL=/dev/null", "TYPESAFE_API_KEY=", "GIT_AUTHOR_NAME=t", "GIT_AUTHOR_EMAIL=t@x", "GIT_COMMITTER_NAME=t", "GIT_COMMITTER_EMAIL=t@x")
	b, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v %s", args, err, b)
	}
	return strings.TrimSpace(string(b))
}

func newEnv(t *testing.T, texts *[]string) *env {
	t.Helper()
	tmp, _ := filepath.EvalSymlinks(t.TempDir())
	t.Setenv("HOME", filepath.Join(tmp, "home"))
	t.Setenv("TYPESAFE_API_KEY", "")
	e := &env{t: t, texts: texts, repo: filepath.Join(tmp, "repo"), wt: filepath.Join(tmp, "wt"),
		queue: filepath.Join(tmp, "queue"), cfg: filepath.Join(tmp, "client.toml")}
	t.Setenv("WORKFLOW_QUEUE", e.queue)
	t.Setenv("WORKFLOW_CLIENT_CONFIG", e.cfg)
	os.MkdirAll(filepath.Join(e.queue, "rejected"), 0o700)
	os.MkdirAll(filepath.Join(e.repo, "docs/plans/x"), 0o755)
	e.design = filepath.Join(e.repo, "docs/plans/x/DESIGN.md")
	os.WriteFile(e.design, []byte("# Design\n"), 0o644)
	os.WriteFile(filepath.Join(e.repo, "docs/plans/x/other.txt"), []byte("o\n"), 0o644)
	git(t, e.repo, "init", "-q")
	git(t, e.repo, "add", ".")
	git(t, e.repo, "commit", "-q", "-m", "first")
	git(t, e.repo, "worktree", "add", "-q", e.wt, "-b", "wt")
	e.artifact = func() (int, any) { return 404, map[string]string{"error": "none"} }
	e.baseline = map[string]any{"kind": "design", "checks": map[string]any{}}
	e.stub = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		e.hits.Add(1)
		if r.Header.Get("Authorization") != "Bearer "+secretKey {
			w.WriteHeader(401)
			return
		}
		e.mu.Lock()
		defer e.mu.Unlock()
		code, body := 200, any(map[string]any{})
		switch r.URL.Path {
		case "/v1/health":
			body = map[string]bool{"ok": true}
		case "/v1/artifacts":
			code, body = e.artifact()
		case "/v1/baselines":
			body = e.baseline
		case "/v1/checks":
			body = map[string]any{"loaded": true, "checks": []map[string]any{{"kind": "design", "name": "clarity", "q": "Is it clear?", "levels": []string{"no", "partly", "yes"}, "invert": false}, {"kind": "design", "name": "debt", "q": "Is there debt?", "levels": []string{"low", "high"}, "invert": true}}}
		case "/v1/search":
			body = map[string]any{"hits": []map[string]any{{"repo_id": "root:abc", "path": "docs/plans/y/DESIGN.md", "kind": "design", "content_hash": "h", "snippet": "a [match] here", "rank": -1.5}}}
		}
		w.WriteHeader(code)
		json.NewEncoder(w).Encode(body)
	}))
	t.Cleanup(e.stub.Close)
	e.writeConfig(e.stub.URL)
	return e
}

func (e *env) writeConfig(endpoint string) {
	os.WriteFile(e.cfg, []byte(fmt.Sprintf("endpoint = %q\nkey = %q\n", endpoint, secretKey)), 0o600)
}

func (e *env) hash() string {
	b, _ := os.ReadFile(e.design)
	return fmt.Sprintf("%x", sum(b))
}

// evt writes a queue file for an afterFileEdit of file, aged by age.
func (e *env) evt(dir, name, file string, age time.Duration) string {
	body := fmt.Sprintf("{\"ts\":1700000000.5,\"harness\":\"cursor\",\"event\":\"afterFileEdit\"}\n{\"hook_event_name\":\"afterFileEdit\",\"conversation_id\":\"c\",\"cwd\":%q,\"file_path\":%q}", filepath.Dir(file), file)
	p := filepath.Join(dir, name)
	if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
		e.t.Fatal(err)
	}
	old := time.Now().Add(-age)
	os.Chtimes(p, old, old)
	return p
}

type client struct {
	e  *env
	in io.WriteCloser
	r  *bufio.Reader
	id int
}

func (e *env) serve() *client {
	inR, inW := io.Pipe()
	outR, outW := io.Pipe()
	done := make(chan error, 1)
	opts := Options{Version: "test", QueueDir: e.queue, Wait: 300 * time.Millisecond,
		StartDrain: func() error { e.drains.Add(1); return nil },
		Getwd:      func() (string, error) { return e.repo, nil }}
	go func() { done <- Serve(context.Background(), inR, outW, opts); outW.Close() }()
	e.t.Cleanup(func() {
		inW.Close()
		select {
		case err := <-done:
			if err != nil {
				e.t.Errorf("Serve: %v", err)
			}
		case <-time.After(5 * time.Second):
			e.t.Error("Serve did not exit on EOF")
		}
	})
	return &client{e: e, in: inW, r: bufio.NewReader(outR)}
}

func (c *client) raw(line string) map[string]any {
	c.e.t.Helper()
	fmt.Fprintln(c.in, line)
	return c.read()
}

func (c *client) read() map[string]any {
	c.e.t.Helper()
	ch := make(chan string, 1)
	go func() { l, _ := c.r.ReadString('\n'); ch <- l }()
	select {
	case l := <-ch:
		var m map[string]any
		if err := json.Unmarshal([]byte(l), &m); err != nil {
			c.e.t.Fatalf("reply %q: %v", l, err)
		}
		return m
	case <-time.After(10 * time.Second):
		c.e.t.Fatal("no reply")
	}
	return nil
}

func (c *client) rpc(method string, params any) map[string]any {
	c.id++
	b, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": c.id, "method": method, "params": params})
	return c.raw(string(b))
}

// tool calls a tool, asserts no JSON-RPC error, and returns the text and isError.
func (c *client) tool(name string, args any) (string, bool) {
	c.e.t.Helper()
	m := c.rpc("tools/call", map[string]any{"name": name, "arguments": args})
	if m["error"] != nil {
		c.e.t.Fatalf("%s: JSON-RPC error %v", name, m["error"])
	}
	res := m["result"].(map[string]any)
	text := res["content"].([]any)[0].(map[string]any)["text"].(string)
	*c.e.texts = append(*c.e.texts, text)
	isErr, _ := res["isError"].(bool)
	return text, isErr
}

func (c *client) feedback(path string) string {
	c.e.t.Helper()
	text, isErr := c.tool("artifact_feedback", map[string]any{"path": path})
	if isErr {
		c.e.t.Fatalf("unexpected isError: %s", text)
	}
	return text
}

func want(t *testing.T, text string, subs ...string) {
	t.Helper()
	for _, s := range subs {
		if !strings.Contains(text, s) {
			t.Errorf("answer lacks %q:\n%s", s, text)
		}
	}
}

func dontWant(t *testing.T, text string, subs ...string) {
	t.Helper()
	for _, s := range subs {
		if strings.Contains(text, s) {
			t.Errorf("answer has %q:\n%s", s, text)
		}
	}
}

func errCode(m map[string]any) float64 {
	if e, ok := m["error"].(map[string]any); ok {
		return e["code"].(float64)
	}
	return 0
}

func TestShim(t *testing.T) {
	var texts []string
	t.Run("1 initialize", func(t *testing.T) {
		c := newEnv(t, &texts).serve()
		r := c.rpc("initialize", map[string]any{"protocolVersion": "2025-06-18"})["result"].(map[string]any)
		if r["protocolVersion"] != "2025-06-18" || r["serverInfo"].(map[string]any)["name"] != "workflow" || r["instructions"] == nil {
			t.Fatalf("initialize: %v", r)
		}
		r = c.rpc("initialize", map[string]any{"protocolVersion": "1999-01-01"})["result"].(map[string]any)
		if r["protocolVersion"] != "2025-11-25" {
			t.Fatalf("unknown version: %v", r)
		}
		fmt.Fprintln(c.in, `{"jsonrpc":"2.0","method":"notifications/initialized"}`)
		// a notification gets no reply: the next reply must be the ping's.
		m := c.rpc("ping", nil)
		if res, ok := m["result"].(map[string]any); !ok || len(res) != 0 || m["id"].(float64) != float64(c.id) {
			t.Fatalf("ping after notification: %v", m)
		}
	})
	t.Run("2 tools/list", func(t *testing.T) {
		c := newEnv(t, &texts).serve()
		tools := c.rpc("tools/list", nil)["result"].(map[string]any)["tools"].([]any)
		var names []string
		for _, x := range tools {
			tm := x.(map[string]any)
			names = append(names, tm["name"].(string))
			s := tm["inputSchema"].(map[string]any)
			if s["type"] != "object" || s["required"] == nil || s["additionalProperties"] != false || tm["description"] == "" ||
				tm["annotations"].(map[string]any)["readOnlyHint"] != true {
				t.Errorf("tool %v malformed: %v", tm["name"], tm)
			}
		}
		if strings.Join(names, ",") != "artifact_feedback,list_checks,search_artifacts" {
			t.Fatalf("tools = %v", names)
		}
	})
	t.Run("3 protocol errors", func(t *testing.T) {
		c := newEnv(t, &texts).serve()
		m := c.raw("{nope")
		if errCode(m) != -32700 || m["id"] != nil {
			t.Errorf("bad line: %v", m)
		}
		if errCode(c.raw("[]")) != -32600 || errCode(c.raw("5")) != -32600 {
			t.Error("batch/non-object must be -32600")
		}
		if errCode(c.rpc("foo/bar", nil)) != -32601 {
			t.Error("unknown method must be -32601")
		}
		if errCode(c.rpc("tools/call", map[string]any{"name": "nope"})) != -32602 || errCode(c.rpc("tools/call", map[string]any{})) != -32602 {
			t.Error("unknown tool must be -32602")
		}
		if _, ok := c.rpc("ping", nil)["result"]; !ok {
			t.Error("loop stopped serving")
		}
	})
	t.Run("4 bad arguments", func(t *testing.T) {
		e := newEnv(t, &texts)
		c := e.serve()
		for name, args := range map[string][2]any{
			"missing path": {"artifact_feedback", map[string]any{}},
			"wrong type":   {"artifact_feedback", map[string]any{"path": 5}},
			"directory":    {"artifact_feedback", map[string]any{"path": e.repo}},
			"missing file": {"artifact_feedback", map[string]any{"path": "nope.md"}},
			"bad kind":     {"list_checks", map[string]any{"kind": "x"}},
			"empty query":  {"search_artifacts", map[string]any{"query": ""}},
			"search kind":  {"search_artifacts", map[string]any{"query": "a", "kind": "x"}},
		} {
			text, isErr := c.tool(args[0].(string), args[1])
			if !isErr || text == "" {
				t.Errorf("%s: isError=%v text=%q", name, isErr, text)
			}
		}
	})
	t.Run("5 queued", func(t *testing.T) {
		e := newEnv(t, &texts)
		e.evt(e.queue, "a.evt", e.design, 40*time.Second)
		e.evt(e.queue, "b.evt", filepath.Join(e.wt, "docs/plans/x/DESIGN.md"), 5*time.Second)
		e.evt(e.queue, "c.evt", filepath.Join(e.repo, "docs/plans/x/other.txt"), 90*time.Second)
		c := e.serve()
		a := c.feedback("docs/plans/x/DESIGN.md")
		t.Log("\n" + a)
		want(t, a, "state: queued", "2 events", "oldest 4", "draining", "path: docs/plans/x/DESIGN.md", "repo: root:", "content_hash: "+e.hash())
		if e.drains.Load() != 1 {
			t.Errorf("StartDrain called %d times", e.drains.Load())
		}
		lock, _ := os.OpenFile(filepath.Join(e.queue, ".drain.lock"), os.O_CREATE|os.O_RDWR, 0o600)
		defer lock.Close()
		if err := syscall.Flock(int(lock.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
			t.Fatal(err)
		}
		a = c.feedback(e.design)
		want(t, a, "state: queued", "draining")
		if e.drains.Load() != 1 {
			t.Errorf("StartDrain called with the lock held: %d", e.drains.Load())
		}
		syscall.Flock(int(lock.Fd()), syscall.LOCK_UN)
		e.stub.Close()
		a = c.feedback(e.design)
		want(t, a, "state: queued", "remote unreachable", "service unreachable at "+e.stub.URL)
	})
	t.Run("6 rejected", func(t *testing.T) {
		e := newEnv(t, &texts)
		p := e.evt(filepath.Join(e.queue, "rejected"), "r.evt", e.design, time.Minute)
		os.WriteFile(p+".reason", []byte("r.evt#1: secret: aws_access_key at line 3 in docs/plans/x/DESIGN.md\n"), 0o600)
		now := time.Now()
		os.Chtimes(e.design, now.Add(-time.Hour), now.Add(-time.Hour))
		c := e.serve()
		a := c.feedback(e.design)
		t.Log("\n" + a)
		want(t, a, "state: rejected", "secret: aws_access_key at line 3 in docs/plans/x/DESIGN.md", "Fix: rewrite the file; the new write is the repair.")
		dontWant(t, a, "r.evt#1:")
		os.Chtimes(e.design, now, now)
		a = c.feedback(e.design)
		dontWant(t, a, "state: rejected")
		want(t, a, "note: earlier rejection superseded by a later write")
	})
	t.Run("7 delivered", func(t *testing.T) {
		e := newEnv(t, &texts)
		c := e.serve()
		latest := func(screen, rejection any, scores ...any) {
			e.mu.Lock()
			defer e.mu.Unlock()
			e.artifact = func() (int, any) {
				return 200, map[string]any{"repo_id": "r", "path": "p", "kind": "design", "versions": 3, "latest": map[string]any{
					"content_hash": e.hash(), "received_at": "2026-01-01T00:00:00Z", "screen": screen, "scores": scores, "rejection": rejection}}
			}
		}
		sc := func(n string, v float64) any { return map[string]any{"check": n, "score": v} }
		latest(map[string]any{"verdict": "unscreened", "scorer": "none"}, nil)
		a := c.feedback(e.design)
		t.Log("\n" + a)
		want(t, a, "state: delivered", "screen: unscreened (no scorer on the service)", "versions: 3")
		latest(map[string]any{"verdict": "pass", "scorer": "jev-1"}, nil)
		want(t, c.feedback(e.design), "screen: pass by jev-1")
		latest(nil, map[string]any{"stage": "screen", "reason": "too vague", "at": "x"})
		a = c.feedback(e.design)
		want(t, a, "screen: flagged: too vague", "Fix: rewrite the file")
		latest(nil, nil)
		want(t, c.feedback(e.design), "screen: awaiting screen")
		e.mu.Lock()
		e.baseline = map[string]any{"kind": "design", "checks": map[string]any{
			"clarity": map[string]any{"n": 5, "p25": 0.5, "median": 0.7, "p75": 0.9},
			"scope":   map[string]any{"n": 5, "p25": 0.5, "median": 0.7, "p75": 0.9},
			"few":     map[string]any{"n": 3, "p25": 0.5, "median": 0.7, "p75": 0.9}}}
		e.mu.Unlock()
		latest(map[string]any{"verdict": "pass", "scorer": "jev-1"}, nil, sc("clarity", 0.25), sc("scope", 0.5), sc("few", 0.1), sc("new", 0.2))
		a = c.feedback(e.design)
		t.Log("\n" + a)
		for _, l := range strings.Split(a, "\n") {
			below := strings.Contains(l, "BELOW p25")
			if strings.HasPrefix(l, "clarity") != below {
				t.Errorf("line %q: BELOW p25 = %v", l, below)
			}
		}
		want(t, a, "clarity 0.25 (baseline p25 0.50, median 0.70, n 5) BELOW p25", "few 0.10 (baseline n=3, too few to flag)")
	})
	t.Run("8 stale and not delivered", func(t *testing.T) {
		e := newEnv(t, &texts)
		c := e.serve()
		a := c.feedback(e.design)
		want(t, a, "state: not delivered")
		e.mu.Lock()
		e.artifact = func() (int, any) {
			return 200, map[string]any{"versions": 1, "latest": map[string]any{"content_hash": strings.Repeat("ab", 32), "received_at": "2026-01-01T00:00:00Z", "scores": []any{}}}
		}
		e.mu.Unlock()
		a = c.feedback(e.design)
		t.Log("\n" + a)
		want(t, a, "state: stale", "current content not yet delivered", "abababababab", "2026-01-01T00:00:00Z")
	})
	t.Run("9 no config and unreachable", func(t *testing.T) {
		e := newEnv(t, &texts)
		c := e.serve()
		os.Remove(e.cfg)
		before := e.hits.Load()
		a := c.feedback(e.design)
		t.Log("\n" + a)
		want(t, a, "state: no config", e.cfg)
		if e.hits.Load() != before {
			t.Error("HTTP made with no config")
		}
		e.writeConfig("http://127.0.0.1:1")
		e.evt(e.queue, "a.evt", e.design, time.Second)
		a = c.feedback(e.design)
		t.Log("\n" + a)
		want(t, a, "state: queued", "service unreachable at http://127.0.0.1:1")
		os.Remove(filepath.Join(e.queue, "a.evt"))
		a = c.feedback(e.design)
		want(t, a, "state: not delivered", "service unreachable at http://127.0.0.1:1")
		text, isErr := c.tool("list_checks", map[string]any{"kind": "design"})
		if isErr {
			t.Errorf("list_checks isError: %s", text)
		}
		want(t, text, "service unreachable")
		os.Remove(e.cfg)
		text, isErr = c.tool("search_artifacts", map[string]any{"query": "x"})
		if isErr {
			t.Errorf("search isError: %s", text)
		}
		want(t, text, "no client config")
	})
	t.Run("10 not tracked", func(t *testing.T) {
		e := newEnv(t, &texts)
		dir := filepath.Join(t.TempDir(), "docs/plans/z")
		os.MkdirAll(dir, 0o755)
		f := filepath.Join(dir, "DESIGN.md")
		os.WriteFile(f, []byte("x"), 0o644)
		before := e.hits.Load()
		c := e.serve()
		a := c.feedback(f)
		t.Log("\n" + a)
		want(t, a, "state: not tracked")
		a = c.feedback(filepath.Join(e.repo, "docs/plans/x/other.txt"))
		want(t, a, "state: not tracked")
		if e.hits.Load() != before {
			t.Error("service called for untracked path")
		}
	})
	t.Run("tools list_checks and search", func(t *testing.T) {
		c := newEnv(t, &texts).serve()
		a, _ := c.tool("list_checks", map[string]any{"kind": "design"})
		t.Log("\n" + a)
		want(t, a, "clarity [levels no/partly/yes]: Is it clear?", "debt [levels low/high] [inverted]: Is there debt?")
		a, _ = c.tool("search_artifacts", map[string]any{"query": "match"})
		t.Log("\n" + a)
		want(t, a, "design root:abc:docs/plans/y/DESIGN.md (rank -1.5)", "a [match] here")
	})
	t.Run("11 no key leak", func(t *testing.T) {
		if len(texts) < 10 {
			t.Fatalf("only %d responses recorded", len(texts))
		}
		for _, x := range texts {
			if strings.Contains(x, secretKey) {
				t.Fatal("key appears in a response")
			}
		}
	})
}

func sum(b []byte) [32]byte { return sha256.Sum256(b) }
