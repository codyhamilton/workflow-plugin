package main

import (
	"bytes"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestServeScorerWiring(t *testing.T) {
	tmp := t.TempDir()
	bin := filepath.Join(tmp, "workflow")
	if out, err := exec.Command("go", "build", "-o", bin, ".").CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}
	const dummy = "dummy-key-not-real-0123"
	run := func(extra ...string) (string, error, *exec.Cmd) {
		cmd := exec.Command(bin, "serve")
		cmd.Env = append(os.Environ(), "HOME="+tmp, "WORKFLOW_SERVE_DATA="+filepath.Join(tmp, "data"), "WORKFLOW_SERVE_ADDR=127.0.0.1:0",
			"WORKFLOW_QUEUE="+filepath.Join(tmp, "queue"), "WORKFLOW_CLIENT_CONFIG="+filepath.Join(tmp, "client.toml"),
			"WORKFLOW_SERVE_KEYS=a=ka", "TYPESAFE_API_KEY=", "WORKFLOW_CHECKS_DIR=")
		cmd.Env = append(cmd.Env, extra...)
		var out bytes.Buffer
		cmd.Stderr = &out
		cmd.Stdout = &out
		if err := cmd.Start(); err != nil {
			t.Fatal(err)
		}
		done := make(chan error, 1)
		go func() { done <- cmd.Wait() }()
		select {
		case err := <-done:
			return out.String(), err, cmd
		case <-time.After(1500 * time.Millisecond): // still serving
			cmd.Process.Kill()
			<-done
			return out.String(), nil, cmd
		}
	}
	out, err, _ := run()
	if err != nil || !strings.Contains(out, "scorer none; verdicts are unscreened") {
		t.Fatalf("no key: %v\n%s", err, out)
	}
	bad := filepath.Join(tmp, "badchecks")
	os.MkdirAll(bad, 0o755)
	os.WriteFile(filepath.Join(bad, "criteria.json"), []byte("{broken"), 0o644)
	out, err, _ = run("TYPESAFE_API_KEY="+dummy, "WORKFLOW_CHECKS_DIR="+bad)
	if err == nil || !strings.Contains(out, "criteria.json") || strings.Contains(out, "listening") {
		t.Fatalf("bad checks should refuse to start: %v\n%s", err, out)
	}
	if strings.Contains(out, dummy) {
		t.Fatal("output contains the key")
	}
	out, err, _ = run("TYPESAFE_API_KEY=" + dummy)
	if err != nil || !strings.Contains(out, "WORKFLOW_CHECKS_DIR is unset") || strings.Contains(out, dummy) {
		t.Fatalf("no checks dir: %v\n%s", err, out)
	}
	out, err, _ = run("TYPESAFE_API_KEY="+dummy, "WORKFLOW_CHECKS_DIR="+filepath.Join("..", "..", "..", "quality"))
	if err != nil || !strings.Contains(out, "report=5") || strings.Contains(out, dummy) {
		t.Fatalf("real checks: %v\n%s", err, out)
	}
}
