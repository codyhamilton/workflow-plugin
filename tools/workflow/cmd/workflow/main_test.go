package main

import (
	"bytes"
	"encoding/json"
	"io"
	"io/fs"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
)

func freePort(t *testing.T) string {
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer l.Close()
	return l.Addr().String()
}

func TestServeOutcome(t *testing.T) {
	tmp := t.TempDir()
	bin := filepath.Join(tmp, "workflow")
	if out, err := exec.Command("go", "build", "-o", bin, ".").CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}
	data := filepath.Join(tmp, "data")
	env := append(os.Environ(), "TYPESAFE_API_KEY=", "HOME="+tmp, "WORKFLOW_SERVE_DATA="+data, "WORKFLOW_SERVE_ADDR=127.0.0.1:0",
		"WORKFLOW_QUEUE="+filepath.Join(tmp, "queue"), "WORKFLOW_CLIENT_CONFIG="+filepath.Join(tmp, "client.toml"))

	// no keys: refuses any bind that is not loopback
	noKeys := exec.Command(bin, "serve")
	noKeys.Env = append(env, "WORKFLOW_SERVE_KEYS=", "WORKFLOW_SERVE_ADDR=0.0.0.0:0")
	if err := noKeys.Run(); err == nil {
		t.Fatal("started without keys on a wildcard bind")
	}

	cmd := exec.Command(bin, "serve")
	cmd.Env = append(env, "WORKFLOW_SERVE_KEYS=a=ka,b=kb")
	errPath := filepath.Join(tmp, "serve.log")
	errFile, err := os.Create(errPath)
	if err != nil {
		t.Fatal(err)
	}
	cmd.Stderr = errFile
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { cmd.Process.Kill(); cmd.Wait() }()
	var addr string
	for i := 0; addr == ""; i++ {
		b, _ := os.ReadFile(errPath)
		if m := listenRE.FindSubmatch(b); m != nil {
			addr = string(m[1])
		} else if i > 200 {
			t.Fatal("server did not start: " + string(b))
		} else {
			time.Sleep(50 * time.Millisecond)
		}
	}
	base := "http://" + addr

	secret := "AKIA" + "IOSFODNN7" + "EXAMPLE"
	content := "# design\n"
	facts := []any{
		map[string]any{"id": "q#0", "type": "hook_event", "conversation_id": "c", "harness": "h", "event": "Stop", "ts": 1, "payload": map[string]any{"k": "v"}},
		map[string]any{"id": "q#1", "type": "artifact_version", "conversation_id": "c", "harness": "h", "event": "w", "ts": 2, "repo_id": "r",
			"path": "docs/plans/01-x/DESIGN.md", "content": content, "content_hash": keys.ContentHash([]byte(content)), "source": "worktree"},
		map[string]any{"id": "q#2", "type": "commit", "conversation_id": "c", "harness": "h", "event": "commit", "ts": 3, "repo_id": "r", "sha": "abc", "paths": []string{"a"}, "renames": []any{}},
		map[string]any{"id": "q#3", "type": "hook_event", "conversation_id": "c", "harness": "h", "event": "x", "ts": 4, "payload": map[string]any{"cmd": "export K=" + secret}},
	}
	body, _ := json.Marshal(map[string]any{"facts": facts})
	call := func(method, path, key string, b []byte) (int, string) {
		req, _ := http.NewRequest(method, base+path, bytes.NewReader(b))
		if key != "" {
			req.Header.Set("Authorization", "Bearer "+key)
		}
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			t.Fatal(err)
		}
		defer resp.Body.Close()
		out, _ := io.ReadAll(resp.Body)
		return resp.StatusCode, string(out)
	}
	for round, want := range []string{"accepted", "duplicate"} {
		code, out := call("POST", "/v1/ingest", "ka", body)
		var r struct {
			Results []struct{ ID, Status, Reason string }
		}
		if code != 200 || json.Unmarshal([]byte(out), &r) != nil || len(r.Results) != 4 {
			t.Fatal(code, out)
		}
		for i := 0; i < 3; i++ {
			if r.Results[i].Status != want {
				t.Fatalf("round %d result %d: %+v", round, i, r.Results[i])
			}
		}
		if r.Results[3].Status != "rejected" || !strings.Contains(r.Results[3].Reason, "payload.cmd") {
			t.Fatal(r.Results[3])
		}
	}
	q := "/v1/artifacts?repo_id=r&path=docs/plans/01-x/DESIGN.md"
	ok := false
	for i := 0; i < 100 && !ok; i++ {
		code, out := call("GET", q, "ka", nil)
		ok = code == 200 && strings.Contains(out, `"verdict":"unscreened"`)
		if !ok {
			time.Sleep(50 * time.Millisecond)
		}
	}
	if !ok {
		t.Fatal("artifact never unscreened")
	}
	if code, _ := call("GET", q, "kb", nil); code != 404 {
		t.Fatal("kb:", code)
	}
	if code, _ := call("GET", q, "", nil); code != 401 {
		t.Fatal("no key:", code)
	}
	if code, _ := call("GET", q, "zz", nil); code != 401 {
		t.Fatal("wrong key:", code)
	}

	cmd.Process.Signal(syscall.SIGTERM)
	cmd.Wait()
	if b, _ := os.ReadFile(errPath); bytes.Contains(b, []byte(secret)) {
		t.Fatal("secret in stderr")
	}
	filepath.WalkDir(data, func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		if b, _ := os.ReadFile(p); bytes.Contains(b, []byte(secret)) {
			t.Errorf("secret found in %s", p)
		}
		return nil
	})
}
