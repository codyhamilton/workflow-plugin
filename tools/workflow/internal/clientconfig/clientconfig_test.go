package clientconfig

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func write(t *testing.T, body string) {
	t.Helper()
	p := filepath.Join(t.TempDir(), "client.toml")
	if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("WORKFLOW_CLIENT_CONFIG", p)
}

func TestLoad(t *testing.T) {
	write(t, "# c\n\nendpoint = \"http://127.0.0.1:8770\"   # local\nother = \"x\"\nkey = \"k\\\"1\"\n")
	c, err := Load()
	if err != nil || c.Endpoint != "http://127.0.0.1:8770" || c.Key != `k"1` {
		t.Fatalf("got %+v %v", c, err)
	}
	if Path() != os.Getenv("WORKFLOW_CLIENT_CONFIG") {
		t.Fatal("path")
	}
}

func TestMissingFile(t *testing.T) {
	t.Setenv("WORKFLOW_CLIENT_CONFIG", filepath.Join(t.TempDir(), "none.toml"))
	c, err := Load()
	if err != nil || !c.Local || c.Endpoint != LocalEndpoint || c.Key != "" || c.Mode() != "local" {
		t.Fatalf("got %+v %v", c, err)
	}
}

func TestDefaultPath(t *testing.T) {
	t.Setenv("WORKFLOW_CLIENT_CONFIG", "")
	t.Setenv("HOME", "/h")
	if Path() != "/h/.config/workflow/client.toml" {
		t.Fatal(Path())
	}
}

func TestMalformed(t *testing.T) {
	write(t, "endpoint = \"e\"\nkey = hunter2secret\n")
	_, err := Load()
	if err == nil || !strings.Contains(err.Error(), "line 2") || strings.Contains(err.Error(), "hunter2") {
		t.Fatalf("got %v", err)
	}
	write(t, "endpoint = \"e\"\n")
	if _, err := Load(); err == nil || !strings.Contains(err.Error(), "missing key") {
		t.Fatalf("got %v", err)
	}
	write(t, "key = \"k\"\n")
	if _, err := Load(); err == nil || !strings.Contains(err.Error(), "missing endpoint") {
		t.Fatalf("got %v", err)
	}
}
