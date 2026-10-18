package login

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestMissingEndpoint(t *testing.T) {
	cfg := filepath.Join(t.TempDir(), "client.toml")
	t.Setenv("YAKKA_CLIENT_CONFIG", cfg)
	code := Run(context.Background(), Options{Stderr: io.Discard, OpenBrowser: func(string) error { return nil }})
	if code != 1 {
		t.Fatalf("exit %d", code)
	}
	if _, err := os.Stat(cfg); err == nil {
		t.Fatal("wrote config")
	}
}

func TestLoginExchangeWritesConfig(t *testing.T) {
	const plain = "wk_login_test_plain_token_0123456789ab"
	cfg := filepath.Join(t.TempDir(), "client.toml")
	t.Setenv("YAKKA_CLIENT_CONFIG", cfg)

	var redirectURI string
	var collector *httptest.Server
	collector = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/device/exchange" {
			http.NotFound(w, r)
			return
		}
		var body struct {
			Code        string `json:"code"`
			State       string `json:"state"`
			RedirectURI string `json:"redirect_uri"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "bad body", 400)
			return
		}
		if body.Code != "devcode" || body.RedirectURI != redirectURI || body.State == "" {
			http.Error(w, "bad exchange", 400)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]string{
			"endpoint": collector.URL,
			"token":    plain,
		})
	}))
	defer collector.Close()

	var stdout bytes.Buffer
	open := func(deviceURL string) error {
		u, err := url.Parse(deviceURL)
		if err != nil {
			return err
		}
		if u.Path != "/device" {
			t.Fatalf("device path: %s", u.Path)
		}
		state := u.Query().Get("state")
		redirectURI = u.Query().Get("redirect_uri")
		if state == "" || redirectURI == "" {
			t.Fatal("missing query params")
		}
		cb, err := url.Parse(redirectURI)
		if err != nil {
			return err
		}
		q := cb.Query()
		q.Set("code", "devcode")
		q.Set("state", state)
		cb.RawQuery = q.Encode()
		resp, err := http.Get(cb.String())
		if err != nil {
			return err
		}
		resp.Body.Close()
		return nil
	}

	code := Run(context.Background(), Options{
		Endpoint:    collector.URL,
		Stderr:      &stdout,
		OpenBrowser: open,
		Timeout:     15 * time.Second,
	})
	if code != 0 {
		t.Fatalf("exit %d stderr=%s", code, stdout.String())
	}
	if strings.Contains(stdout.String(), plain) || strings.Contains(stdout.String(), "wk_") {
		t.Fatalf("token leaked to stderr: %s", stdout.String())
	}
	data, err := os.ReadFile(cfg)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(data), `key = "`+plain+`"`) {
		t.Fatalf("config: %q", data)
	}
	if !strings.Contains(string(data), `endpoint = "`+collector.URL+`"`) {
		t.Fatalf("config endpoint: %q", data)
	}
	st, err := os.Stat(cfg)
	if err != nil || st.Mode().Perm() != 0o600 {
		t.Fatalf("mode: %v", st.Mode())
	}
}

func TestDevicePageURL(t *testing.T) {
	u := devicePageURL("https://collector.example", "st", "http://127.0.0.1:9/callback")
	if !strings.HasPrefix(u, "https://collector.example/device?") {
		t.Fatal(u)
	}
	parsed, err := url.Parse(u)
	if err != nil {
		t.Fatal(err)
	}
	if parsed.Query().Get("state") != "st" || parsed.Query().Get("redirect_uri") != "http://127.0.0.1:9/callback" {
		t.Fatal(parsed.Query())
	}
	pages := devicePageURL("https://api.yakka.build", "st", "http://127.0.0.1:9/callback")
	if !strings.HasPrefix(pages, "https://yakka.build/device?") {
		t.Fatal(pages)
	}
}

func TestEndpointFromExistingConfig(t *testing.T) {
	cfg := filepath.Join(t.TempDir(), "client.toml")
	t.Setenv("YAKKA_CLIENT_CONFIG", cfg)
	if err := os.WriteFile(cfg, []byte("endpoint = \"https://old.example\"\nkey = \"wk_old\"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	ep, err := resolveEndpoint("")
	if err != nil || ep != "https://old.example" {
		t.Fatalf("%q %v", ep, err)
	}
}
