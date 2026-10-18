package clientconfig

import (
	"errors"
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
	t.Setenv("YAKKA_CLIENT_CONFIG", p)
}

func TestLoad(t *testing.T) {
	write(t, "# c\n\nendpoint = \"http://127.0.0.1:8770\"   # local\nother = \"x\"\nkey = \"k\\\"1\"\n")
	c, err := Load()
	if err != nil || c.Endpoint != "http://127.0.0.1:8770" || c.Key != `k"1` {
		t.Fatalf("got %+v %v", c, err)
	}
	if Path() != os.Getenv("YAKKA_CLIENT_CONFIG") {
		t.Fatal("path")
	}
}

func TestMissingFile(t *testing.T) {
	t.Setenv("YAKKA_CLIENT_CONFIG", filepath.Join(t.TempDir(), "none.toml"))
	c, err := Load()
	if err != nil || !c.Local || c.Endpoint != LocalEndpoint || c.Key != "" || c.Mode() != "local" {
		t.Fatalf("got %+v %v", c, err)
	}
}

func TestDefaultPath(t *testing.T) {
	t.Setenv("YAKKA_CLIENT_CONFIG", "")
	t.Setenv("HOME", "/h")
	if Path() != "/h/.config/yakka/client.toml" {
		t.Fatal(Path())
	}
}

func TestEnvOverridesFile(t *testing.T) {
	write(t, "endpoint = \"http://file.example\"\nkey = \"file-key\"\n")
	t.Setenv("YAKKA_ENDPOINT", "http://env.example")
	t.Setenv("YAKKA_KEY", "env-key")
	c, err := Load()
	if err != nil || c.Local || c.Endpoint != "http://env.example" || c.Key != "env-key" {
		t.Fatalf("got %+v %v", c, err)
	}
}

func TestEnvRemoteNoFile(t *testing.T) {
	t.Setenv("YAKKA_CLIENT_CONFIG", filepath.Join(t.TempDir(), "missing.toml"))
	t.Setenv("YAKKA_ENDPOINT", "http://collector.example")
	t.Setenv("YAKKA_KEY", "wk_test")
	c, err := Load()
	if err != nil || c.Local || c.Endpoint != "http://collector.example" || c.Key != "wk_test" {
		t.Fatalf("got %+v %v", c, err)
	}
}

func TestPartialEnv(t *testing.T) {
	secret := "super-secret-key-value"
	t.Setenv("YAKKA_KEY", secret)
	_, err := Load()
	if err == nil || !errors.Is(err, ErrPartialEnv) {
		t.Fatalf("got %v", err)
	}
	if strings.Contains(err.Error(), secret) {
		t.Fatalf("error leaks key: %v", err)
	}
	t.Setenv("YAKKA_KEY", "")
	t.Setenv("YAKKA_ENDPOINT", "http://only-endpoint.example")
	_, err = Load()
	if err == nil || !errors.Is(err, ErrPartialEnv) {
		t.Fatalf("got %v", err)
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
