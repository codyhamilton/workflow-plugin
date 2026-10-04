package main

import (
	"bytes"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func buildBin(t *testing.T, ldflags string) string {
	t.Helper()
	bin := filepath.Join(t.TempDir(), "workflow")
	args := []string{"build"}
	if ldflags != "" {
		args = append(args, "-ldflags", ldflags)
	}
	args = append(args, "-o", bin, ".")
	if out, err := exec.Command("go", args...).CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}
	return bin
}

func TestVersion(t *testing.T) {
	bin := buildBin(t, "-X main.version=9.9.9 -X main.commit=abc123")
	for _, arg := range []string{"--version", "version"} {
		out, err := exec.Command(bin, arg).Output()
		if err != nil {
			t.Fatalf("%s: %v", arg, err)
		}
		if string(out) != "workflow 9.9.9 abc123\n" {
			t.Errorf("%s printed %q", arg, out)
		}
	}
}

type initRun struct {
	stdout, stderr string
	code           int
}

func runInitBin(t *testing.T, bin, home, root, path string) initRun {
	t.Helper()
	cmd := exec.Command(bin, "init")
	cmd.Env = []string{"HOME=" + home, "XDG_CONFIG_HOME=" + filepath.Join(home, ".config"), "PATH=" + path,
		"TYPESAFE_API_KEY=sentinel-not-a-key"}
	if root != "" {
		cmd.Env = append(cmd.Env, "WORKFLOW_ROOT="+root)
	}
	var so, se bytes.Buffer
	cmd.Stdout, cmd.Stderr = &so, &se
	err := cmd.Run()
	code := 0
	if ee, ok := err.(*exec.ExitError); ok {
		code = ee.ExitCode()
	} else if err != nil {
		t.Fatal(err)
	}
	return initRun{so.String(), se.String(), code}
}

func mustRead(t *testing.T, p string) string {
	t.Helper()
	b, err := os.ReadFile(p)
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}

func mode(t *testing.T, p string) os.FileMode {
	t.Helper()
	fi, err := os.Stat(p)
	if err != nil {
		t.Fatal(err)
	}
	return fi.Mode().Perm()
}

func keyOf(t *testing.T, toml string) string {
	t.Helper()
	for _, l := range strings.Split(toml, "\n") {
		if strings.HasPrefix(l, "key") {
			return strings.Trim(strings.TrimSpace(strings.SplitN(l, "=", 2)[1]), `"`)
		}
	}
	t.Fatal("no key in client.toml")
	return ""
}

func TestInit(t *testing.T) {
	bin := buildBin(t, "")
	path := os.Getenv("PATH")
	cfgDir := func(home string) string { return filepath.Join(home, ".config", "workflow") }

	t.Run("writes", func(t *testing.T) {
		home := t.TempDir()
		r := runInitBin(t, bin, home, "/x/root", path)
		if r.code != 0 {
			t.Fatalf("exit %d: %s", r.code, r.stderr)
		}
		toml := filepath.Join(cfgDir(home), "client.toml")
		env := filepath.Join(cfgDir(home), "serve.env")
		unit := filepath.Join(home, ".config", "systemd", "user", "workflow-serve.service")
		for _, p := range []string{toml, env, unit} {
			if m := mode(t, p); m != 0o600 {
				t.Errorf("%s mode %o", p, m)
			}
			if m := mode(t, filepath.Dir(p)); m != 0o700 {
				t.Errorf("%s mode %o", filepath.Dir(p), m)
			}
		}
		tc, ec, uc := mustRead(t, toml), mustRead(t, env), mustRead(t, unit)
		if !strings.Contains(tc, `endpoint = "http://127.0.0.1:8770"`) {
			t.Errorf("endpoint: %q", tc)
		}
		key := keyOf(t, tc)
		if len(key) != 64 {
			t.Errorf("key length %d", len(key))
		}
		if !strings.Contains(ec, "WORKFLOW_SERVE_KEYS=local="+key+"\n") || !strings.Contains(ec, "WORKFLOW_CHECKS_DIR=/x/root/tools/quality\n") {
			t.Errorf("serve.env wrong")
		}
		for _, w := range []string{"ExecStart=/x/root/bin/workflow serve", "EnvironmentFile=" + env, "EnvironmentFile=-" + filepath.Join(cfgDir(home), "serve.secrets.env")} {
			if !strings.Contains(uc, w) {
				t.Errorf("unit missing %q", w)
			}
		}
		for _, c := range []string{tc, ec, uc} {
			if strings.Contains(c, "sentinel-not-a-key") || strings.Contains(c, "TYPESAFE_API_KEY=") {
				t.Errorf("secret leaked into a file")
			}
		}
		if strings.Contains(r.stdout+r.stderr, key) {
			t.Errorf("key printed")
		}
		want := "systemctl --user daemon-reload && systemctl --user enable --now workflow-serve.service"
		if !strings.HasSuffix(strings.TrimSpace(r.stdout), want) {
			t.Errorf("stdout does not end with systemctl command:\n%s", r.stdout)
		}
		if strings.Count(r.stdout, "wrote") != 3 {
			t.Errorf("want 3 wrote:\n%s", r.stdout)
		}

		before := []string{tc, ec, uc}
		r2 := runInitBin(t, bin, home, "/x/root", path)
		if r2.code != 0 || strings.Count(r2.stdout, "kept") != 3 || strings.Contains(r2.stdout, "wrote") {
			t.Errorf("second run:\n%s", r2.stdout)
		}
		for i, p := range []string{toml, env, unit} {
			if mustRead(t, p) != before[i] {
				t.Errorf("%s changed", p)
			}
		}
	})

	t.Run("existing client.toml", func(t *testing.T) {
		home := t.TempDir()
		os.MkdirAll(cfgDir(home), 0o700)
		toml := filepath.Join(cfgDir(home), "client.toml")
		orig := "endpoint = \"http://example.invalid\"\nkey = \"K-existing\"\n"
		os.WriteFile(toml, []byte(orig), 0o600)
		r := runInitBin(t, bin, home, "/x/root", path)
		if r.code != 0 {
			t.Fatalf("exit %d: %s", r.code, r.stderr)
		}
		if mustRead(t, toml) != orig {
			t.Error("client.toml changed")
		}
		if !strings.Contains(mustRead(t, filepath.Join(cfgDir(home), "serve.env")), "WORKFLOW_SERVE_KEYS=local=K-existing\n") {
			t.Error("serve.env lacks existing key")
		}
	})

	t.Run("no root", func(t *testing.T) {
		home := t.TempDir()
		r := runInitBin(t, bin, home, "", path)
		if r.code != 2 {
			t.Errorf("exit %d", r.code)
		}
		if !strings.Contains(r.stderr, "WORKFLOW_ROOT unset") {
			t.Errorf("stderr %q", r.stderr)
		}
		if ents, _ := os.ReadDir(home); len(ents) != 0 {
			t.Errorf("wrote %d entries", len(ents))
		}
	})

	t.Run("no systemctl", func(t *testing.T) {
		home, fake := t.TempDir(), t.TempDir()
		marker := filepath.Join(fake, "marker")
		os.WriteFile(filepath.Join(fake, "systemctl"), []byte("#!/bin/sh\ntouch "+marker+"\n"), 0o755)
		r := runInitBin(t, bin, home, "/x/root", fake+":"+path)
		if r.code != 0 {
			t.Fatalf("exit %d", r.code)
		}
		if _, err := os.Stat(marker); err == nil {
			t.Error("systemctl was executed")
		}
	})
}
