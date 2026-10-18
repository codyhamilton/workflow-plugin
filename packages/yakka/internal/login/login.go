// Package login implements `yakka login`: loopback callback, browser to the collector device page, token exchange, client.toml write.
package login

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/codyhamilton/yakka/packages/yakka/internal/clientconfig"
)

// Options configures a login run. OpenBrowser nil uses the system browser (or YAKKA_LOGIN_BROWSER in tests).
type Options struct {
	Endpoint    string
	Stderr      io.Writer
	OpenBrowser func(url string) error
	Timeout     time.Duration
}

var endpointLineRE = regexp.MustCompile(`^endpoint\s*=\s*("(?:[^"\\]|\\.)*")\s*(?:#.*)?$`)

// Run performs device authorization and writes client.toml. It does not print the token.
func Run(ctx context.Context, opts Options) int {
	stderr := opts.Stderr
	if stderr == nil {
		stderr = os.Stderr
	}
	timeout := opts.Timeout
	if timeout == 0 {
		timeout = 10 * time.Minute
	}
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	collector, err := resolveEndpoint(opts.Endpoint)
	if err != nil {
		fmt.Fprintln(stderr, "yakka login:", err)
		return 1
	}

	state, err := randomState()
	if err != nil {
		fmt.Fprintln(stderr, "yakka login:", err)
		return 1
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		fmt.Fprintln(stderr, "yakka login:", err)
		return 1
	}
	defer ln.Close()

	redirectURI := "http://" + ln.Addr().String() + "/callback"
	deviceURL := devicePageURL(collector, state, redirectURI)

	done := make(chan error, 1)
	mux := http.NewServeMux()
	mux.HandleFunc("/callback", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if r.URL.Query().Get("state") != state {
			http.Error(w, "invalid state", http.StatusBadRequest)
			return
		}
		code := r.URL.Query().Get("code")
		if code == "" {
			http.Error(w, "missing code", http.StatusBadRequest)
			return
		}
		token, ep, err := exchange(ctx, collector, code, state, redirectURI)
		if err != nil {
			done <- err
			http.Error(w, "exchange failed", http.StatusBadGateway)
			return
		}
		if ep == "" {
			ep = collector
		}
		path := clientconfig.Path()
		if err := writeClientConfig(path, ep, token); err != nil {
			done <- err
			http.Error(w, "config write failed", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprint(w, "<!DOCTYPE html><html><body><p>Login complete. You can close this window.</p></body></html>")
		done <- nil
	})

	srv := &http.Server{Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	go func() { _ = srv.Serve(ln) }()
	defer func() {
		shutCtx, shutCancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer shutCancel()
		_ = srv.Shutdown(shutCtx)
	}()

	open := opts.OpenBrowser
	if open == nil {
		open = defaultOpenBrowser
	}
	if err := open(deviceURL); err != nil {
		fmt.Fprintln(stderr, "yakka login: open browser:", err)
		return 1
	}

	select {
	case <-ctx.Done():
		fmt.Fprintln(stderr, "yakka login: timed out waiting for authorization")
		return 1
	case err := <-done:
		if err != nil {
			fmt.Fprintln(stderr, "yakka login:", err)
			return 1
		}
	}

	fmt.Fprintf(stderr, "yakka login: wrote %s\n", clientconfig.Path())
	return 0
}

func resolveEndpoint(flag string) (string, error) {
	flag = strings.TrimSpace(flag)
	if flag != "" {
		return normalizeOrigin(flag)
	}
	path := clientconfig.Path()
	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return "", errors.New("no collector endpoint (use --endpoint or set endpoint in client config)")
		}
		return "", fmt.Errorf("read config: %w", err)
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		m := endpointLineRE.FindStringSubmatch(line)
		if m == nil {
			continue
		}
		v, err := strconv.Unquote(m[1])
		if err != nil || v == "" {
			continue
		}
		return normalizeOrigin(v)
	}
	return "", errors.New("no collector endpoint (use --endpoint or set endpoint in client config)")
}

func normalizeOrigin(raw string) (string, error) {
	raw = strings.TrimSpace(raw)
	raw = strings.TrimRight(raw, "/")
	u, err := url.Parse(raw)
	if err != nil || u.Host == "" {
		return "", errors.New("endpoint must be a collector origin (scheme and host, no path)")
	}
	if u.Scheme != "http" && u.Scheme != "https" {
		return "", errors.New("endpoint must be a collector origin (scheme and host, no path)")
	}
	if u.Path != "" && u.Path != "/" {
		return "", errors.New("endpoint must be a collector origin (scheme and host, no path)")
	}
	return u.Scheme + "://" + u.Host, nil
}

func randomState() (string, error) {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	return hex.EncodeToString(b[:]), nil
}

func devicePageURL(collector, state, redirectURI string) string {
	q := url.Values{}
	q.Set("state", state)
	q.Set("redirect_uri", redirectURI)
	base := collector
	if u, err := url.Parse(collector); err == nil && u.Scheme == "https" && strings.EqualFold(u.Host, "api.yakka.build") {
		base = "https://yakka.build"
	}
	return base + "/device?" + q.Encode()
}

func exchange(ctx context.Context, collector, code, state, redirectURI string) (token, endpoint string, err error) {
	body, _ := json.Marshal(map[string]string{
		"code":         code,
		"state":        state,
		"redirect_uri": redirectURI,
	})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, collector+"/v1/device/exchange", bytes.NewReader(body))
	if err != nil {
		return "", "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", "", fmt.Errorf("exchange request: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return "", "", fmt.Errorf("exchange failed (%d)", resp.StatusCode)
	}
	var out struct {
		Endpoint string `json:"endpoint"`
		Token    string `json:"token"`
	}
	if err := json.Unmarshal(respBody, &out); err != nil || out.Token == "" {
		return "", "", errors.New("invalid exchange response")
	}
	return out.Token, out.Endpoint, nil
}

func writeClientConfig(path, endpoint, key string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	content := fmt.Sprintf("endpoint = %q\nkey = %q\n", endpoint, key)
	return os.WriteFile(path, []byte(content), 0o600)
}

func defaultOpenBrowser(url string) error {
	if cmd := strings.TrimSpace(os.Getenv("YAKKA_LOGIN_BROWSER")); cmd != "" {
		return exec.Command(cmd, url).Start()
	}
	switch runtime.GOOS {
	case "darwin":
		return exec.Command("open", url).Start()
	case "windows":
		return exec.Command("cmd", "/c", "start", url).Start()
	default:
		return exec.Command("xdg-open", url).Start()
	}
}
