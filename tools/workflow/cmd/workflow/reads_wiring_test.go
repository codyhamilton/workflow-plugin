package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// TestReadsWiring runs the built binary with no scorer key and the repository's checks, and reads
// the loaded checks back over HTTP.
func TestReadsWiring(t *testing.T) {
	tmp := t.TempDir()
	bin := filepath.Join(tmp, "workflow")
	if out, err := exec.Command("go", "build", "-o", bin, ".").CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}
	checks, err := filepath.Abs("../../../quality")
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(bin, "serve")
	cmd.Env = append(os.Environ(), "HOME="+tmp, "WORKFLOW_SERVE_DATA="+filepath.Join(tmp, "data"), "WORKFLOW_SERVE_ADDR=127.0.0.1:0",
		"WORKFLOW_QUEUE="+filepath.Join(tmp, "queue"), "WORKFLOW_CLIENT_CONFIG="+filepath.Join(tmp, "client.toml"),
		"WORKFLOW_SERVE_KEYS=a=ka", "TYPESAFE_API_KEY=", "WORKFLOW_CHECKS_DIR="+checks)
	logPath := filepath.Join(tmp, "serve.log")
	lf, err := os.Create(logPath)
	if err != nil {
		t.Fatal(err)
	}
	cmd.Stderr = lf
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { cmd.Process.Kill(); cmd.Wait(); lf.Close() })
	var bound string
	for i := 0; i < 250 && bound == ""; i++ {
		b, _ := os.ReadFile(logPath)
		if m := listenRE.FindSubmatch(b); m != nil {
			bound = string(m[1])
		} else {
			time.Sleep(40 * time.Millisecond)
		}
	}
	if bound == "" {
		t.Fatal("no listening line")
	}
	logs, _ := os.ReadFile(logPath)
	for _, want := range []string{"scorer none", "checks design=11 brief=11 report=5"} {
		if !bytes.Contains(logs, []byte(want)) {
			t.Fatalf("stderr lacks %q:\n%s", want, logs)
		}
	}
	req, _ := http.NewRequest("GET", "http://"+bound+"/v1/checks?kind=design", nil)
	req.Header.Set("Authorization", "Bearer ka")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	var got struct {
		Checks []map[string]any `json:"checks"`
		Loaded bool             `json:"loaded"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&got); err != nil {
		t.Fatal(err)
	}
	if resp.StatusCode != 200 || len(got.Checks) != 11 || !got.Loaded || !strings.Contains(string(logs), "listening") {
		t.Fatalf("checks: %d %d loaded=%v", resp.StatusCode, len(got.Checks), got.Loaded)
	}
}
