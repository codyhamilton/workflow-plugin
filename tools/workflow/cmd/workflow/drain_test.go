package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"

	_ "modernc.org/sqlite"
)

const apiKey = "k-test-key-9f3a"

type env struct {
	t                      *testing.T
	tmp, bin, wrapper      string
	data, queue, cfg, logs string
	home, hooklog          string
	serveCmd               *exec.Cmd
	base                   []string
}

func newEnv(t *testing.T) *env {
	t.Helper()
	tmp := t.TempDir()
	e := &env{t: t, tmp: tmp, bin: filepath.Join(tmp, "workflow")}
	if out, err := exec.Command("go", "build", "-o", e.bin, ".").CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}
	e.data, e.queue, e.cfg = filepath.Join(tmp, "data"), filepath.Join(tmp, "queue"), filepath.Join(tmp, "client.toml")
	e.logs, e.home, e.hooklog = filepath.Join(tmp, "logs"), filepath.Join(tmp, "home"), filepath.Join(tmp, "hooklog")
	for _, d := range []string{e.logs, e.home, e.hooklog} {
		os.MkdirAll(d, 0o755)
	}
	e.wrapper = filepath.Join(tmp, "wrapper.sh")
	script := fmt.Sprintf("#!/bin/bash\necho $$ >> %s/starts\nexec %s \"$@\" 2>>%s/drain.$$.log\n", e.logs, e.bin, e.logs)
	if err := os.WriteFile(e.wrapper, []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	e.base = append(os.Environ(),
		"HOME="+e.home, "WORKFLOW_QUEUE="+e.queue, "WORKFLOW_HOOKLOG_DIR="+e.hooklog,
		"WORKFLOW_CLIENT_CONFIG="+e.cfg, "WORKFLOW_BIN="+e.wrapper, "TYPESAFE_API_KEY=",
		"WORKFLOW_DRAIN_LINGER=2s", "WORKFLOW_DRAIN_BACKOFF_MAX=1s",
	)
	t.Cleanup(func() {
		if b, err := os.ReadFile(filepath.Join(e.logs, "starts")); err == nil {
			for _, f := range strings.Fields(string(b)) {
				if pid, err := strconv.Atoi(f); err == nil {
					syscall.Kill(pid, syscall.SIGKILL)
				}
			}
		}
		exec.Command("pkill", "-9", "-f", tmp).Run()
	})
	return e
}

func (e *env) writeConfig(addr string) {
	body := fmt.Sprintf("endpoint = \"http://%s\"\nkey = \"%s\"\n", addr, apiKey)
	if err := os.WriteFile(e.cfg, []byte(body), 0o600); err != nil {
		e.t.Fatal(err)
	}
}

// startServe runs `workflow serve` on addr with no WORKFLOW_CLIENT_CONFIG and no WORKFLOW_QUEUE of
// its own, so it can never host a drain.
func (e *env) startServe(addr string) {
	e.t.Helper()
	var env []string
	for _, kv := range e.base {
		if !strings.HasPrefix(kv, "WORKFLOW_CLIENT_CONFIG=") && !strings.HasPrefix(kv, "WORKFLOW_QUEUE=") {
			env = append(env, kv)
		}
	}
	cmd := exec.Command(e.bin, "serve")
	cmd.Env = append(env, "WORKFLOW_SERVE_DATA="+e.data, "WORKFLOW_SERVE_ADDR="+addr, "WORKFLOW_SERVE_KEYS=t="+apiKey)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Start(); err != nil {
		e.t.Fatal(err)
	}
	e.serveCmd = cmd
	e.t.Cleanup(func() { cmd.Process.Kill(); cmd.Wait() })
	waitFor(e.t, 10*time.Second, "serve start", func() bool {
		r, err := http.Get("http://" + addr + "/v1/health")
		if err == nil {
			r.Body.Close()
		}
		return err == nil
	})
}

func waitFor(t *testing.T, d time.Duration, what string, cond func() bool) {
	t.Helper()
	end := time.Now().Add(d)
	for !cond() {
		if time.Now().After(end) {
			t.Fatal("timed out: " + what)
		}
		time.Sleep(50 * time.Millisecond)
	}
}

func (e *env) spool(harness string, payload any) error {
	b, _ := json.Marshal(payload)
	cmd := exec.Command("bash", "../../../hooklog/spool.sh", "--harness", harness)
	cmd.Env = e.base
	cmd.Stdin = bytes.NewReader(b)
	return cmd.Run()
}

func (e *env) queued() int {
	n := 0
	des, _ := os.ReadDir(e.queue)
	for _, de := range des {
		if strings.HasSuffix(de.Name(), ".evt") {
			n++
		}
	}
	return n
}

func (e *env) rejected() []string {
	var out []string
	des, _ := os.ReadDir(filepath.Join(e.queue, "rejected"))
	for _, de := range des {
		if strings.HasSuffix(de.Name(), ".evt") {
			out = append(out, de.Name())
		}
	}
	return out
}

func (e *env) ledger(query string, args ...any) int {
	db, err := sql.Open("sqlite", "file:"+filepath.Join(e.data, "t", "ledger.db")+"?mode=ro")
	if err != nil {
		return -1
	}
	defer db.Close()
	var n int
	if err := db.QueryRow(query, args...).Scan(&n); err != nil {
		return -1
	}
	return n
}

func (e *env) noSecret(secret string) {
	e.t.Helper()
	filepath.WalkDir(e.tmp, func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() || strings.HasSuffix(p, "/workflow") {
			return nil
		}
		b, _ := os.ReadFile(p)
		if !bytes.Contains(b, []byte(secret)) {
			return nil
		}
		okPlace := strings.HasSuffix(p, "DESIGN.md") || strings.HasPrefix(p, e.queue+"/") && strings.HasSuffix(p, ".evt") && !strings.HasSuffix(p, ".reason") ||
			strings.Contains(p, "/.git/objects/")
		if !okPlace {
			e.t.Errorf("secret found in %s", p)
		}
		return nil
	})
}

func TestBurst(t *testing.T) {
	e := newEnv(t)
	addr := freePort(t)
	e.startServe(addr)
	e.writeConfig(addr)
	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			p := map[string]any{"hook_event_name": "Stop", "session_id": "conv-burst", "n": i}
			if err := e.spool("claude", p); err != nil {
				t.Error(err)
			}
		}(i)
	}
	wg.Wait()
	waitFor(t, 30*time.Second, "queue empty", func() bool { return e.queued() == 0 })
	waitFor(t, 10*time.Second, "20 hook_event rows", func() bool {
		return e.ledger("SELECT count(*) FROM facts WHERE type='hook_event'") == 20
	})
	if n := len(e.rejected()); n != 0 {
		t.Fatalf("%d rejected", n)
	}
	acquired := 0
	logs, _ := filepath.Glob(filepath.Join(e.logs, "drain.*.log"))
	for _, l := range logs {
		b, _ := os.ReadFile(l)
		if strings.Contains(string(b), "acquired lock") {
			acquired++
		}
		if strings.Contains(string(b), apiKey) {
			t.Error("key in drain log")
		}
	}
	starts, _ := os.ReadFile(filepath.Join(e.logs, "starts"))
	t.Logf("wrapper starts: %d; drain logs: %d; logs that acquired the lock: %d", len(strings.Fields(string(starts))), len(logs), acquired)
	if acquired != 1 {
		t.Fatalf("%d drains acquired the lock", acquired)
	}
}

func gitRepo(t *testing.T, dir string, files map[string]string) string {
	t.Helper()
	git := func(args ...string) string {
		cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
		cmd.Env = append(os.Environ(), "GIT_AUTHOR_NAME=t", "GIT_AUTHOR_EMAIL=t@t", "GIT_COMMITTER_NAME=t", "GIT_COMMITTER_EMAIL=t@t")
		out, err := cmd.CombinedOutput()
		if err != nil {
			t.Fatalf("git %v: %v\n%s", args, err, out)
		}
		return strings.TrimSpace(string(out))
	}
	os.MkdirAll(dir, 0o755)
	git("init", "-q")
	for p, c := range files {
		os.MkdirAll(filepath.Dir(filepath.Join(dir, p)), 0o755)
		os.WriteFile(filepath.Join(dir, p), []byte(c), 0o644)
	}
	git("add", "-A")
	git("commit", "-q", "-m", "add docs")
	return git("rev-parse", "HEAD")
}

func TestWriteArtifactVersion(t *testing.T) {
	e := newEnv(t)
	addr := freePort(t)
	e.startServe(addr)
	e.writeConfig(addr)
	repo := filepath.Join(e.tmp, "repo")
	gitRepo(t, repo, map[string]string{"docs/plans/x/DESIGN.md": "# Design\n\nclean\n"})
	raw, err := os.ReadFile("../../../hooklog/tests/fixtures/artifact_writes.json")
	if err != nil {
		t.Fatal(err)
	}
	var fx []struct {
		Harness string
		Payload map[string]any
	}
	if err := json.Unmarshal(raw, &fx); err != nil {
		t.Fatal(err)
	}
	p := fx[0].Payload // Claude Write
	p["session_id"] = "conv-write"
	p["cwd"] = repo
	p["tool_input"] = map[string]any{"file_path": filepath.Join(repo, "docs/plans/x/DESIGN.md"), "content": "# Design\n\nclean\n"}
	if err := e.spool("claude", p); err != nil {
		t.Fatal(err)
	}
	waitFor(t, 30*time.Second, "artifact_version row", func() bool {
		return e.ledger("SELECT count(*) FROM facts WHERE type='artifact_version'") == 1
	})
	waitFor(t, 10*time.Second, "queue empty", func() bool { return e.queued() == 0 })
}

func TestCommitCalls(t *testing.T) {
	e := newEnv(t)
	addr := freePort(t)
	e.startServe(addr)
	e.writeConfig(addr)
	repo := filepath.Join(e.tmp, "repo")
	sha := gitRepo(t, repo, map[string]string{"docs/plans/x/DESIGN.md": "# Design\n"})
	raw, err := os.ReadFile("../../../hooklog/tests/fixtures/commit_calls.json")
	if err != nil {
		t.Fatal(err)
	}
	raw = bytes.ReplaceAll(raw, []byte("{{DIR}}"), []byte(repo))
	raw = bytes.ReplaceAll(raw, []byte("{{SHA7}}"), []byte(sha[:7]))
	var doc struct {
		Fixtures []struct {
			Name         string
			ExpectCommit bool `json:"expect_commit"`
			Harness      string
			Payload      map[string]any
		}
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	for _, f := range doc.Fixtures {
		if err := e.spool(f.Harness, f.Payload); err != nil {
			t.Fatal(f.Name, err)
		}
	}
	waitFor(t, 30*time.Second, "queue empty", func() bool { return e.queued() == 0 })
	waitFor(t, 10*time.Second, "commit row", func() bool {
		return e.ledger("SELECT count(*) FROM facts WHERE type='commit'") >= 1
	})
	if n := e.ledger(`SELECT count(*) FROM facts WHERE type='artifact_version' AND instr(raw, '"source":"commit"') > 0`); n < 1 {
		t.Fatalf("commit-source versions: %d", n)
	}
}

func TestRejectedSecretArtifact(t *testing.T) {
	e := newEnv(t)
	addr := freePort(t)
	e.startServe(addr)
	e.writeConfig(addr)
	secret := "AKIA" + "IOSFODNN7" + "EXAMPLE"
	content := "# Design\n\nsome text\naws_key = " + secret + "\n"
	repo := filepath.Join(e.tmp, "repo")
	gitRepo(t, repo, map[string]string{"docs/plans/x/DESIGN.md": content})
	p := map[string]any{"hook_event_name": "PostToolUse", "tool_name": "Write", "session_id": "conv-secret", "cwd": repo,
		"tool_input": map[string]any{"file_path": filepath.Join(repo, "docs/plans/x/DESIGN.md"), "content": content}}
	if err := e.spool("claude", p); err != nil {
		t.Fatal(err)
	}
	waitFor(t, 30*time.Second, "file rejected", func() bool { return len(e.rejected()) == 1 })
	waitFor(t, 10*time.Second, "queue empty", func() bool { return e.queued() == 0 })
	name := e.rejected()[0]
	reason, err := os.ReadFile(filepath.Join(e.queue, "rejected", name+".reason"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(reason), "secret:") || !strings.Contains(string(reason), "at line 4") {
		t.Fatalf("reason: %q", reason)
	}
	time.Sleep(3 * time.Second) // let drain logs flush and the drain exit
	e.noSecret(secret)
}

func TestDownUp(t *testing.T) {
	e := newEnv(t)
	addr := freePort(t)
	e.writeConfig(addr) // nothing listens yet
	for i := 0; i < 3; i++ {
		if err := e.spool("claude", map[string]any{"hook_event_name": "Stop", "session_id": "conv-down", "n": i}); err != nil {
			t.Fatal(err)
		}
	}
	time.Sleep(4 * time.Second)
	if e.queued() != 3 {
		t.Fatalf("queued while down: %d", e.queued())
	}
	e.startServe(addr)
	waitFor(t, 30*time.Second, "queue empty after up", func() bool { return e.queued() == 0 })
	if n := e.ledger("SELECT count(*) FROM facts WHERE type='hook_event'"); n != 3 {
		t.Fatalf("hook_event rows: %d", n)
	}
	if len(e.rejected()) != 0 {
		t.Fatal("rejected files")
	}
}

func (e *env) status() (string, int) {
	cmd := exec.Command(e.bin, "status")
	cmd.Env = e.base
	out, err := cmd.CombinedOutput()
	code := 0
	if ee, ok := err.(*exec.ExitError); ok {
		code = ee.ExitCode()
	} else if err != nil {
		e.t.Fatal(err)
	}
	return string(out), code
}

func TestStatus(t *testing.T) {
	e := newEnv(t)
	os.MkdirAll(filepath.Join(e.queue, "tmp"), 0o700)
	os.MkdirAll(filepath.Join(e.queue, "rejected"), 0o700)
	for _, n := range []string{"a-1.evt", "b-2.evt"} {
		os.WriteFile(filepath.Join(e.queue, n), []byte("x"), 0o600)
	}
	os.WriteFile(filepath.Join(e.queue, "rejected", "r.evt"), []byte("x"), 0o600)
	os.WriteFile(filepath.Join(e.queue, "rejected", "r.evt.reason"), []byte("r.evt: 413\n"), 0o600)

	os.WriteFile(e.cfg, []byte("not toml\n"), 0o600)
	out, code := e.status()
	for _, want := range []string{"queue: " + e.queue, "queued: 2", "rejected: 1", "drain: not running", "config: " + e.cfg + " (invalid)", "endpoint: -"} {
		if !strings.Contains(out, want+"\n") {
			t.Errorf("missing %q in\n%s", want, out)
		}
	}
	if code != 0 {
		t.Errorf("exit %d with an invalid config", code)
	}

	// no config: local mode (probes the local endpoint with a GET; never posts)
	os.Remove(e.cfg)
	if out, _ := e.status(); !strings.Contains(out, "config: none (local mode)\nendpoint: http://127.0.0.1:8770 ") {
		t.Errorf("local mode not shown:\n%s", out)
	}

	lock, err := os.OpenFile(filepath.Join(e.queue, ".drain.lock"), os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		t.Fatal(err)
	}
	defer lock.Close()
	if err := syscall.Flock(int(lock.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		t.Fatal(err)
	}
	if out, _ := e.status(); !strings.Contains(out, "drain: running\n") {
		t.Errorf("not running while locked:\n%s", out)
	}

	// unreachable endpoint with files queued is a failure
	e.writeConfig(freePort(t))
	out, code = e.status()
	if code != 1 || !strings.Contains(out, "unreachable\n") {
		t.Errorf("exit %d\n%s", code, out)
	}
	if strings.Contains(out, apiKey) {
		t.Error("key printed")
	}

	// reachable endpoint
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write([]byte(`{"ok":true}`)) }))
	defer srv.Close()
	e.writeConfig(strings.TrimPrefix(srv.URL, "http://"))
	out, code = e.status()
	if code != 0 || !strings.Contains(out, " reachable\n") || strings.Contains(out, apiKey) {
		t.Errorf("exit %d\n%s", code, out)
	}
}
