package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/login"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve"
)

var keyLineRE = regexp.MustCompile(`^key\s*=\s*("(?:[^"\\]|\\.)*")`)

func TestLoginCommandMissingEndpoint(t *testing.T) {
	cfg := filepath.Join(t.TempDir(), "client.toml")
	t.Setenv("WORKFLOW_CLIENT_CONFIG", cfg)
	if code := run([]string{"login"}); code != 1 {
		t.Fatalf("exit %d", code)
	}
}

func TestLoginDrainReadWriteAndReadOnly(t *testing.T) {
	e := newEnv(t)
	t.Setenv("WORKFLOW_CLIENT_CONFIG", e.cfg)
	os.Remove(e.cfg)
	_, port, err := net.SplitHostPort(freePort(t))
	if err != nil {
		t.Fatal(err)
	}
	bind := "0.0.0.0:" + port
	origin := "http://127.0.0.1:" + port

	if err := os.MkdirAll(e.data, 0o700); err != nil {
		t.Fatal(err)
	}

	gh := mockGitHubLogin(t, 42, "devuser", []loginEmail{{Email: "dev@example.com", Verified: true}})
	t.Cleanup(gh.Close)

	cfg := serve.Config{
		Addr:                    bind,
		Data:                    e.data,
		PublicURL:               origin,
		GitHubOAuthClientID:     "cid",
		GitHubOAuthClientSecret: "csec",
	}
	s := serve.New(cfg, serve.Options{DisableWorker: true, GitHubHTTPBase: gh.URL})
	t.Cleanup(func() { s.Close() })
	go http.Serve(mustListen(t, bind), s.Handler())
	waitFor(t, 15*time.Second, "serve up", func() bool {
		r, err := http.Get(origin + "/v1/health")
		if err == nil {
			r.Body.Close()
		}
		return err == nil
	})

	sess := oauthSession(t, s.Handler(), origin)
	remoteCreateTenantLogin(t, s.Handler(), origin, sess, "logintenant")

	runLoginFlow(t, origin, s.Handler(), sess, "logintenant", "read_write", e.cfg)

	if err := e.spool("claude", map[string]any{"hook_event_name": "Stop", "session_id": "conv-login-rw", "n": 1}); err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(e.bin, "drain")
	cmd.Env = e.base
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("drain rw: %v\n%s", err, out)
	}
	waitFor(t, 30*time.Second, "queue empty rw", func() bool { return e.queued() == 0 })

	readKey := runLoginFlow(t, origin, s.Handler(), sess, "logintenant", "read", e.cfg)
	body, _ := json.Marshal(map[string]any{"facts": []any{map[string]any{
		"id": "q#1", "type": "hook_event", "conversation_id": "c", "harness": "h", "event": "Stop", "ts": 1, "payload": map[string]any{},
	}}})
	req, _ := http.NewRequest("POST", origin+"/v1/ingest", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+readKey)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	if resp.StatusCode != 403 {
		t.Fatalf("read ingest: %d", resp.StatusCode)
	}
}

func runLoginFlow(t *testing.T, origin string, h http.Handler, sess []*http.Cookie, tenant, scope, cfgPath string) string {
	t.Helper()
	open := func(deviceURL string) error {
		u, err := url.Parse(deviceURL)
		if err != nil {
			return err
		}
		state := u.Query().Get("state")
		redirectURI := u.Query().Get("redirect_uri")
		exp := time.Now().Add(24 * time.Hour).UTC().Format(time.RFC3339)
		authBody := `{"redirect_uri":"` + redirectURI + `","state":"` + state + `","tenant":"` + tenant + `","scope":"` + scope + `","expires_at":"` + exp + `"}`
		req := httptest.NewRequest("POST", "/v1/device/authorize", strings.NewReader(authBody))
		req.Header.Set("Origin", origin)
		req.Header.Set("Content-Type", "application/json")
		for _, c := range sess {
			req.AddCookie(c)
		}
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		if rec.Code != http.StatusSeeOther {
			return fmt.Errorf("authorize %d %s", rec.Code, rec.Body.String())
		}
		loc := rec.Header().Get("Location")
		if loc == "" {
			return fmt.Errorf("no redirect")
		}
		resp, err := http.Get(loc)
		if err != nil {
			return err
		}
		resp.Body.Close()
		return nil
	}
	var stderr bytes.Buffer
	code := login.Run(context.Background(), login.Options{
		Endpoint:    origin,
		Stderr:      &stderr,
		OpenBrowser: open,
		Timeout:     30 * time.Second,
	})
	if code != 0 {
		t.Fatalf("login exit %d: %s", code, stderr.String())
	}
	if strings.Contains(stderr.String(), "wk_") {
		t.Fatalf("token in stderr: %s", stderr.String())
	}
	data, err := os.ReadFile(cfgPath)
	if err != nil {
		t.Fatal(err)
	}
	for _, line := range strings.Split(string(data), "\n") {
		m := keyLineRE.FindStringSubmatch(strings.TrimSpace(line))
		if m == nil {
			continue
		}
		key, err := strconvUnquoteKey(m[1])
		if err != nil {
			t.Fatal(err)
		}
		return key
	}
	t.Fatalf("no key in config: %s", data)
	return ""
}

func strconvUnquoteKey(s string) (string, error) {
	return strconv.Unquote(s)
}

type loginEmail struct {
	Email    string `json:"email"`
	Verified bool   `json:"verified"`
}

func mockGitHubLogin(t *testing.T, userID int64, loginName string, emails []loginEmail) *httptest.Server {
	mux := http.NewServeMux()
	mux.HandleFunc("/login/oauth/authorize", func(w http.ResponseWriter, r *http.Request) {
		state := r.URL.Query().Get("state")
		redir := r.URL.Query().Get("redirect_uri")
		http.Redirect(w, r, redir+"?code=mockcode&state="+url.QueryEscape(state), http.StatusFound)
	})
	mux.HandleFunc("/login/oauth/access_token", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{"access_token": "mock-access", "token_type": "bearer"})
	})
	mux.HandleFunc("/api/user", func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]any{"id": userID, "login": loginName})
	})
	mux.HandleFunc("/api/user/emails", func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(emails)
	})
	return httptest.NewServer(mux)
}

func oauthSession(t *testing.T, h http.Handler, origin string) []*http.Cookie {
	code, _, cookies := doCookies(t, h, "GET", "/oauth/login", "", "", nil)
	if code != http.StatusFound {
		t.Fatalf("oauth login: %d", code)
	}
	var state string
	for _, c := range cookies {
		if c.Name == "workflow_oauth_state" {
			state = c.Value
		}
	}
	code, _, cookies = doCookies(t, h, "GET", "/oauth/callback?code=mockcode&state="+url.QueryEscape(state), "", "", cookies)
	if code != http.StatusFound {
		t.Fatalf("oauth callback: %d", code)
	}
	for _, c := range cookies {
		if c.Name == "workflow_session" && c.Value != "" {
			return []*http.Cookie{c}
		}
	}
	t.Fatal("no session")
	return nil
}

func doCookies(t *testing.T, h http.Handler, method, path, origin, body string, cookies []*http.Cookie) (int, string, []*http.Cookie) {
	var rdr io.Reader
	if body != "" {
		rdr = strings.NewReader(body)
	}
	req := httptest.NewRequest(method, path, rdr)
	if origin != "" {
		req.Header.Set("Origin", origin)
	}
	if body != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	for _, c := range cookies {
		req.AddCookie(c)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec.Code, rec.Body.String(), rec.Result().Cookies()
}

func remoteCreateTenantLogin(t *testing.T, h http.Handler, origin string, sess []*http.Cookie, name string) {
	body := `{"name":"` + name + `"}`
	code, resp, _ := doCookies(t, h, "POST", "/v1/tenants", origin, body, sess)
	if code != 201 && !(code == 409 && strings.Contains(resp, name)) {
		t.Fatalf("create tenant: %d %s", code, resp)
	}
}

func mustListen(t *testing.T, addr string) net.Listener {
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		t.Fatal(err)
	}
	return ln
}
