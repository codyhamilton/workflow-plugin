package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"

	_ "modernc.org/sqlite"
)

var listenRE = regexp.MustCompile(`serve: listening on (\S+)`)

// startHosted runs `workflow serve` with the queue and client config visible (so it can host the
// drain), on addr ("127.0.0.1:0" for any port). stderr goes to a file under logs/. It returns the
// bound address read from the "listening on" line.
func (e *env) startHosted(addr string) string {
	e.t.Helper()
	logPath := filepath.Join(e.logs, fmt.Sprintf("serve.%d.log", time.Now().UnixNano()))
	lf, err := os.Create(logPath)
	if err != nil {
		e.t.Fatal(err)
	}
	cmd := exec.Command(e.bin, "serve")
	cmd.Env = append(append([]string{}, e.base...), "WORKFLOW_SERVE_DATA="+e.data, "WORKFLOW_SERVE_ADDR="+addr,
		"WORKFLOW_SERVE_KEYS=t="+apiKey, "WORKFLOW_SERVE_POLL=500ms")
	cmd.Stderr = lf
	if err := cmd.Start(); err != nil {
		e.t.Fatal(err)
	}
	e.serveCmd = cmd
	e.t.Cleanup(func() { cmd.Process.Kill(); cmd.Wait(); lf.Close() })
	var bound string
	waitFor(e.t, 10*time.Second, "serve listening line", func() bool {
		b, _ := os.ReadFile(logPath)
		if m := listenRE.FindSubmatch(b); m != nil {
			bound = string(m[1])
		}
		return bound != ""
	})
	return bound
}

// lockHeld reports whether something holds the queue's drain lock.
func (e *env) lockHeld() bool {
	f, err := os.OpenFile(filepath.Join(e.queue, ".drain.lock"), os.O_RDWR, 0)
	if err != nil {
		return false
	}
	defer f.Close()
	if syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB) != nil {
		return true
	}
	syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
	return false
}

func (e *env) spoolEnv(extra []string, harness string, payload any) error {
	b, _ := json.Marshal(payload)
	cmd := exec.Command("bash", "../../../hooklog/spool.sh", "--harness", harness)
	cmd.Env = append(append([]string{}, e.base...), extra...)
	cmd.Stdin = bytes.NewReader(b)
	return cmd.Run()
}

func (e *env) starts() []string {
	b, _ := os.ReadFile(filepath.Join(e.logs, "starts"))
	return strings.Fields(string(b))
}

func git(t *testing.T, dir string, args ...string) string {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	cmd.Env = append(os.Environ(), "GIT_AUTHOR_NAME=t", "GIT_AUTHOR_EMAIL=t@t", "GIT_COMMITTER_NAME=t", "GIT_COMMITTER_EMAIL=t@t")
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v\n%s", args, err, out)
	}
	return strings.TrimSpace(string(out))
}

func (e *env) writeFile(repo, rel, content string) string {
	p := filepath.Join(repo, rel)
	os.MkdirAll(filepath.Dir(p), 0o755)
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		e.t.Fatal(err)
	}
	return p
}

func writePayload(session, repo, path, content string) map[string]any {
	return map[string]any{"hook_event_name": "PostToolUse", "tool_name": "Write", "session_id": session, "cwd": repo,
		"tool_input": map[string]any{"file_path": path, "content": content}}
}

const joinQuery = `SELECT a.path, json_extract(CAST(c.raw AS TEXT), '$.sha'), c.conversation_id
FROM facts a JOIN facts c ON c.type = 'commit' AND c.repo_id = a.repo_id
 AND EXISTS (SELECT 1 FROM json_each(CAST(c.raw AS TEXT), '$.paths') j WHERE j.value = a.path)
WHERE a.type = 'artifact_version' AND a.path = ?`

func TestCaptureOutcome(t *testing.T) {
	e := newEnv(t)
	e.base = append(e.base, "WORKFLOW_SERVE_DATA="+e.data)
	repo := filepath.Join(e.tmp, "repo")
	os.MkdirAll(repo, 0o755)
	git(t, repo, "init", "-q")
	e.writeFile(repo, "README.md", "temp repo\n") // a root commit gives the repo its identity
	git(t, repo, "add", "-A")
	git(t, repo, "commit", "-q", "-m", "init")

	bound := e.startHosted("127.0.0.1:0")
	e.writeConfig(bound) // written after the port is known; serve decides on its tick
	waitFor(t, 10*time.Second, "serve holds the lock", e.lockHeld)

	var outcomes []string
	step := func(name string, f func(t *testing.T)) {
		ok := t.Run(name, f)
		res := map[bool]string{true: "PASS", false: "FAIL"}[ok]
		outcomes = append(outcomes, fmt.Sprintf("outcome %-22s %s", name, res))
	}
	defer func() {
		for _, l := range outcomes {
			fmt.Println(l)
		}
	}()

	step("hosted-burst", func(t *testing.T) {
		base := e.ledger("SELECT count(*) FROM facts WHERE type='hook_event'")
		if base < 0 {
			base = 0
		}
		var wg sync.WaitGroup
		for i := 0; i < 20; i++ {
			wg.Add(1)
			go func(i int) {
				defer wg.Done()
				if err := e.spool("claude", map[string]any{"hook_event_name": "Stop", "session_id": "conv-burst", "n": i}); err != nil {
					t.Error(err)
				}
			}(i)
		}
		wg.Wait()
		waitFor(t, 30*time.Second, "queue empty", func() bool { return e.queued() == 0 })
		waitFor(t, 10*time.Second, "20 more hook_event rows", func() bool {
			return e.ledger("SELECT count(*) FROM facts WHERE type='hook_event'") == base+20
		})
		if s := e.starts(); len(s) != 0 {
			t.Fatalf("%d wrapper starts, want 0", len(s))
		}
	})

	design := "# Design\n\nclean\n"
	step("write", func(t *testing.T) {
		raw, err := os.ReadFile("../../../hooklog/tests/fixtures/artifact_writes.json")
		if err != nil {
			t.Fatal(err)
		}
		var fx []struct{ Payload map[string]any }
		if err := json.Unmarshal(raw, &fx); err != nil {
			t.Fatal(err)
		}
		p := fx[0].Payload // Claude Write
		path := e.writeFile(repo, "docs/plans/x/DESIGN.md", design)
		p["session_id"], p["cwd"] = "conv-write", repo
		p["tool_input"] = map[string]any{"file_path": path, "content": design}
		if err := e.spool("claude", p); err != nil {
			t.Fatal(err)
		}
		waitFor(t, 30*time.Second, "worktree artifact_version", func() bool {
			return e.ledger(`SELECT count(*) FROM facts WHERE type='artifact_version' AND path='docs/plans/x/DESIGN.md'
				AND instr(raw, '"source":"worktree"') > 0`) == 1
		})
	})

	step("commit-and-join", func(t *testing.T) {
		git(t, repo, "add", "-A")
		git(t, repo, "commit", "-q", "-m", "add design")
		sha := git(t, repo, "rev-parse", "HEAD")
		raw, err := os.ReadFile("../../../hooklog/tests/fixtures/commit_calls.json")
		if err != nil {
			t.Fatal(err)
		}
		raw = bytes.ReplaceAll(raw, []byte("{{DIR}}"), []byte(repo))
		raw = bytes.ReplaceAll(raw, []byte("{{SHA7}}"), []byte(sha[:7]))
		var doc struct {
			Fixtures []struct {
				Harness string
				Payload map[string]any
			}
		}
		if err := json.Unmarshal(raw, &doc); err != nil {
			t.Fatal(err)
		}
		f := doc.Fixtures[0]
		f.Payload["session_id"] = "conv-commit"
		if err := e.spool(f.Harness, f.Payload); err != nil {
			t.Fatal(err)
		}
		waitFor(t, 30*time.Second, "commit row", func() bool {
			return e.ledger("SELECT count(*) FROM facts WHERE type='commit'") == 1
		})
		waitFor(t, 10*time.Second, "commit-source version", func() bool {
			return e.ledger(`SELECT count(*) FROM facts WHERE type='artifact_version'
				AND instr(raw, '"source":"commit"') > 0`) >= 1
		})
		db, err := sql.Open("sqlite", "file:"+filepath.Join(e.data, "t", "ledger.db")+"?mode=ro")
		if err != nil {
			t.Fatal(err)
		}
		defer db.Close()
		var path, gotSHA, conv string
		if err := db.QueryRow(joinQuery, "docs/plans/x/DESIGN.md").Scan(&path, &gotSHA, &conv); err != nil {
			t.Fatal(err)
		}
		t.Logf("join row: path=%s sha=%s conversation_id=%s", path, gotSHA, conv)
		if path != "docs/plans/x/DESIGN.md" || gotSHA != sha || conv == "" {
			t.Fatalf("join row: %q %q %q (want sha %s)", path, gotSHA, conv, sha)
		}
	})

	secret := "AKIA" + "IOSFODNN7" + "EXAMPLE"
	step("secret", func(t *testing.T) {
		content := "# Design\n\nsome text\naws_key = " + secret + "\n"
		path := e.writeFile(repo, "docs/plans/y/DESIGN.md", content)
		if err := e.spool("claude", writePayload("conv-secret", repo, path, content)); err != nil {
			t.Fatal(err)
		}
		waitFor(t, 30*time.Second, "file rejected", func() bool { return len(e.rejected()) == 1 })
		reason, err := os.ReadFile(filepath.Join(e.queue, "rejected", e.rejected()[0]+".reason"))
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(reason), "secret:") || !strings.Contains(string(reason), "at line 4") {
			t.Fatalf("reason: %q", reason)
		}
		time.Sleep(time.Second)
		e.noSecret(secret)
	})

	step("endpoint-elsewhere", func(t *testing.T) {
		e.serveCmd.Process.Kill()
		e.serveCmd.Wait()
		bound = e.startHosted("127.0.0.1:0")
		e.writeConfig(freePort(t))
		time.Sleep(2 * time.Second) // several hosting ticks
		for i := 0; i < 3; i++ {
			if err := e.spoolEnv([]string{"WORKFLOW_HOOKLOG_KICK=0"}, "claude", map[string]any{"hook_event_name": "Stop", "session_id": "conv-else", "n": i}); err != nil {
				t.Fatal(err)
			}
		}
		time.Sleep(2 * time.Second)
		if q := e.queued(); q != 3 {
			t.Fatalf("queued %d, want 3", q)
		}
		if e.lockHeld() {
			t.Fatal("serve holds the lock although the config points elsewhere")
		}
		if n := len(e.starts()); n != 0 {
			t.Fatalf("%d wrapper starts", n)
		}
	})

	step("kill-and-recover", func(t *testing.T) {
		e.writeConfig(bound)
		waitFor(t, 15*time.Second, "serve hosts again", e.lockHeld)
		waitFor(t, 30*time.Second, "queue emptied by serve", func() bool { return e.queued() == 0 })
		e.serveCmd.Process.Kill()
		e.serveCmd.Wait()
		waitFor(t, 5*time.Second, "lock released", func() bool { return !e.lockHeld() })
		before := e.ledger("SELECT count(*) FROM facts WHERE type='hook_event'")
		for i := 0; i < 5; i++ {
			if err := e.spool("claude", map[string]any{"hook_event_name": "Stop", "session_id": "conv-kill", "n": i}); err != nil {
				t.Fatal(err)
			}
		}
		waitFor(t, 10*time.Second, "wrapper start", func() bool { return len(e.starts()) >= 1 })
		time.Sleep(2 * time.Second)
		if q := e.queued(); q != 5 {
			t.Fatalf("queued while serve is down: %d", q)
		}
		e.startHosted(bound)
		waitFor(t, 40*time.Second, "all files delivered", func() bool { return e.queued() == 0 })
		waitFor(t, 10*time.Second, "5 more rows", func() bool {
			return e.ledger("SELECT count(*) FROM facts WHERE type='hook_event'") == before+5
		})
		waitFor(t, 30*time.Second, "standalone drains exited", func() bool {
			for _, f := range e.starts() {
				if pid, err := strconv.Atoi(f); err == nil && syscall.Kill(pid, 0) == nil {
					return false
				}
			}
			return true
		})
		waitFor(t, 15*time.Second, "serve holds the lock again", e.lockHeld)
	})

	step("status", func(t *testing.T) {
		out, code := e.status()
		for _, want := range []string{"queued: 0", "rejected: 1", "drain: running"} {
			if !strings.Contains(out, want+"\n") {
				t.Errorf("missing %q in\n%s", want, out)
			}
		}
		if code != 0 || strings.Contains(out, apiKey) {
			t.Errorf("exit %d\n%s", code, out)
		}
	})
}
