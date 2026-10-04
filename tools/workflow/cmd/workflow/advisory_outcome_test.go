package main

import (
	"bufio"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"

	_ "modernc.org/sqlite"
)

// advRPC is a minimal JSON-RPC line client over a `workflow mcp` child.
type advRPC struct {
	t     *testing.T
	in    io.WriteCloser
	lines chan string
	id    int
}

func advStartMCP(e *env, dir string) *advRPC {
	e.t.Helper()
	cmd := exec.Command(e.bin, "mcp")
	cmd.Dir = dir
	cmd.Env = append(append([]string{}, e.base...), "TYPESAFE_API_KEY=")
	in, err := cmd.StdinPipe()
	if err != nil {
		e.t.Fatal(err)
	}
	out, err := cmd.StdoutPipe()
	if err != nil {
		e.t.Fatal(err)
	}
	errf, _ := os.Create(filepath.Join(e.logs, "mcp.stderr.log"))
	cmd.Stderr = errf
	if err := cmd.Start(); err != nil {
		e.t.Fatal(err)
	}
	c := &advRPC{t: e.t, in: in, lines: make(chan string, 64)}
	go func() {
		sc := bufio.NewScanner(out)
		sc.Buffer(make([]byte, 1<<20), 1<<20)
		for sc.Scan() {
			c.lines <- sc.Text()
		}
		close(c.lines)
	}()
	e.t.Cleanup(func() { in.Close(); cmd.Process.Kill(); cmd.Wait(); errf.Close() })
	return c
}

// call sends one request and returns the matching reply object; every stdout line must be JSON.
func (c *advRPC) call(method string, params any) map[string]any {
	c.t.Helper()
	c.id++
	req, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": c.id, "method": method, "params": params})
	if _, err := c.in.Write(append(req, '\n')); err != nil {
		c.t.Fatal(err)
	}
	deadline := time.After(10 * time.Second)
	for {
		select {
		case l, ok := <-c.lines:
			if !ok {
				c.t.Fatal("mcp stdout closed")
			}
			var m map[string]any
			if err := json.Unmarshal([]byte(l), &m); err != nil {
				c.t.Fatalf("non-JSON line on stdout: %.80q", l)
			}
			if id, _ := m["id"].(float64); int(id) == c.id {
				return m
			}
		case <-deadline:
			c.t.Fatalf("no reply to %s within 10s", method)
		}
	}
}

// tool calls a tool and returns the text, isError, and whether the reply had a JSON-RPC error member.
func (c *advRPC) tool(name string, args map[string]any) (text string, isErr, rpcErr bool) {
	c.t.Helper()
	m := c.call("tools/call", map[string]any{"name": name, "arguments": args})
	if _, has := m["error"]; has {
		return "", false, true
	}
	res, _ := m["result"].(map[string]any)
	isErr, _ = res["isError"].(bool)
	content, _ := res["content"].([]any)
	if len(content) > 0 {
		first, _ := content[0].(map[string]any)
		text, _ = first["text"].(string)
	}
	return text, isErr, false
}

func advFirstLines(s string, n int) string {
	l := strings.Split(s, "\n")
	if len(l) > n {
		l = l[:n]
	}
	return strings.Join(l, " | ")
}

func TestAdvisoryOutcome(t *testing.T) {
	e := newEnv(t)
	checksDir, err := filepath.Abs("../../../quality")
	if err != nil {
		t.Fatal(err)
	}
	e.base = append(e.base, "WORKFLOW_SERVE_DATA="+e.data, "WORKFLOW_CHECKS_DIR="+checksDir)
	repo := filepath.Join(e.tmp, "repo")
	gitRepo(t, repo, map[string]string{"README.md": "temp repo\n"})
	top, _, _, err := keys.RepoPath(filepath.Join(repo, "README.md"))
	if err != nil {
		t.Fatal(err)
	}
	repoID, err := keys.RepoID(top)
	if err != nil {
		t.Fatal(err)
	}

	bound := ""
	startServe := func() {
		bound = e.startHosted("127.0.0.1:0")
		e.writeConfig(bound)
		waitFor(t, 15*time.Second, "serve holds the lock", e.lockHeld)
	}
	stopServe := func() {
		e.serveCmd.Process.Kill()
		e.serveCmd.Wait()
	}
	get := func(path string, q url.Values) (int, map[string]any) {
		req, _ := http.NewRequest("GET", "http://"+bound+path+"?"+q.Encode(), nil)
		req.Header.Set("Authorization", "Bearer "+apiKey)
		r, err := http.DefaultClient.Do(req)
		if err != nil {
			return 0, nil
		}
		defer r.Body.Close()
		var m map[string]any
		json.NewDecoder(r.Body).Decode(&m)
		return r.StatusCode, m
	}
	design := func(n int, body string) (rel, abs string) {
		rel = fmt.Sprintf("docs/plans/%02d-adv/DESIGN.md", n)
		return rel, e.writeFile(repo, rel, body)
	}
	spoolWrite := func(session, abs, body string, extra ...string) {
		t.Helper()
		if err := e.spoolEnv(extra, "claude", writePayload(session, repo, abs, body)); err != nil {
			t.Fatal(err)
		}
	}
	delivered := func(rel, body string) {
		t.Helper()
		want := keys.ContentHash([]byte(body))
		waitFor(t, 30*time.Second, "delivered "+rel, func() bool {
			code, m := get("/v1/artifacts", url.Values{"repo_id": {repoID}, "path": {rel}})
			l, _ := m["latest"].(map[string]any)
			return code == 200 && l != nil && l["content_hash"] == want
		})
	}

	startServe()

	// Five delivered designs; the first is the target and has the distinctive word.
	const word = "zebrafinch"
	bodies := make([]string, 5)
	rels := make([]string, 5)
	for i := range bodies {
		bodies[i] = fmt.Sprintf("# Design %d\n\nclean text number %d\n", i+1, i+1)
		if i == 0 {
			bodies[i] += "the " + word + " is distinctive\n"
		}
		var abs string
		rels[i], abs = design(i+1, bodies[i])
		spoolWrite(fmt.Sprintf("conv-%d", i), abs, bodies[i])
	}
	for i := range bodies {
		delivered(rels[i], bodies[i])
	}
	_, ch := get("/v1/checks", url.Values{"kind": {"design"}})
	cl, _ := ch["checks"].([]any)
	if len(cl) < 2 {
		t.Fatalf("expected design checks, got %d", len(cl))
	}
	checkA := cl[0].(map[string]any)["name"].(string)
	checkB := cl[1].(map[string]any)["name"].(string)
	// Test setup, not a product path: scores rows for the delivered designs.
	db, err := sql.Open("sqlite", "file:"+filepath.Join(e.data, "t", "ledger.db")+"?_pragma=busy_timeout(5000)")
	if err != nil {
		t.Fatal(err)
	}
	scoresA := []float64{0.1, 0.5, 0.6, 0.7, 0.8}
	scoresB := []float64{0.9, 0.5, 0.6, 0.7, 0.8}
	for i, b := range bodies {
		h := keys.ContentHash([]byte(b))
		for name, v := range map[string]float64{checkA: scoresA[i], checkB: scoresB[i]} {
			if _, err := db.Exec(`INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`, h, name, v, "test", time.Now().Unix()); err != nil {
				t.Fatal(err)
			}
		}
	}
	db.Close()

	var outcomes []string
	step := func(name string, f func(t *testing.T)) {
		ok := t.Run(name, f)
		outcomes = append(outcomes, fmt.Sprintf("outcome %-22s %s", name, map[bool]string{true: "PASS", false: "FAIL"}[ok]))
	}
	defer func() {
		for _, l := range outcomes {
			fmt.Println(l)
		}
	}()
	answers := map[string]string{}
	var mcp *advRPC
	target := filepath.Join(repo, rels[0])

	step("reads", func(t *testing.T) {
		code, a := get("/v1/artifacts", url.Values{"repo_id": {repoID}, "path": {rels[0]}})
		l, _ := a["latest"].(map[string]any)
		if code != 200 || l == nil {
			t.Fatalf("artifacts %d %v", code, a)
		}
		for _, k := range []string{"kind", "path", "repo_id", "versions", "latest"} {
			if _, ok := a[k]; !ok {
				t.Errorf("artifact lacks %s", k)
			}
		}
		for _, k := range []string{"content_hash", "conversation_id", "received_at", "rejection", "scores", "screen", "source"} {
			if _, ok := l[k]; !ok {
				t.Errorf("latest lacks %s", k)
			}
		}
		if code, c := get("/v1/checks", url.Values{"kind": {"design"}}); code != 200 || len(c["checks"].([]any)) != 11 {
			t.Errorf("design checks: %d", code)
		}
		_, b := get("/v1/baselines", url.Values{"kind": {"design"}})
		ent, _ := b["checks"].(map[string]any)[checkA].(map[string]any)
		for _, k := range []string{"n", "p25", "median", "p75"} {
			if _, ok := ent[k]; !ok {
				t.Errorf("baseline lacks %s: %v", k, ent)
			}
		}
		_, s := get("/v1/search", url.Values{"q": {word}})
		hits, _ := s["hits"].([]any)
		if len(hits) == 0 {
			t.Fatalf("no search hits")
		}
		h := hits[0].(map[string]any)
		if h["path"] != rels[0] || !strings.Contains(fmt.Sprint(h["snippet"]), "["+word+"]") {
			t.Errorf("search hit: %v", h)
		}
	})

	mcp = advStartMCP(e, repo)
	step("initialize", func(t *testing.T) {
		m := mcp.call("initialize", map[string]any{"protocolVersion": "2025-06-18", "capabilities": map[string]any{}, "clientInfo": map[string]any{"name": "t", "version": "0"}})
		r, _ := m["result"].(map[string]any)
		si, _ := r["serverInfo"].(map[string]any)
		if r["protocolVersion"] != "2025-06-18" || si["name"] != "workflow" {
			t.Fatalf("initialize: %v", m)
		}
		mcp.in.Write([]byte(`{"jsonrpc":"2.0","method":"notifications/initialized"}` + "\n"))
	})
	step("tools-list", func(t *testing.T) {
		m := mcp.call("tools/list", map[string]any{})
		var names []string
		for _, x := range m["result"].(map[string]any)["tools"].([]any) {
			names = append(names, x.(map[string]any)["name"].(string))
		}
		sort.Strings(names)
		if strings.Join(names, ",") != "artifact_feedback,list_checks,search_artifacts" {
			t.Fatalf("tools: %v", names)
		}
	})
	step("queued", func(t *testing.T) {
		stopServe()
		waitFor(t, 15*time.Second, "lock free", func() bool { return !e.lockHeld() })
		rel, abs := design(10, "# Queued\n\nwaiting to go\n")
		spoolWrite("conv-q", abs, "# Queued\n\nwaiting to go\n", "WORKFLOW_BIN=/bin/true") // spool starts no drain; only the shim may
		waitFor(t, 15*time.Second, "lock free again", func() bool { return !e.lockHeld() })
		before := len(e.starts())
		txt, isErr, rerr := mcp.tool("artifact_feedback", map[string]any{"path": rel})
		if rerr || isErr {
			t.Fatalf("queued: rpcErr=%v isErr=%v %s", rerr, isErr, txt)
		}
		answers["queued"] = txt
		t.Logf("queued: %s", advFirstLines(txt, 3))
		if !strings.HasPrefix(txt, "state: queued") || !strings.Contains(txt, "1 events") || !strings.Contains(txt, "remote unreachable") {
			t.Errorf("queued answer:\n%s", txt)
		}
		// the default drain starter (this binary's `drain`) must have been started by the shim, not spool.sh
		waitFor(t, 5*time.Second, "shim-started drain holds the lock", e.lockHeld)
		if n := len(e.starts()); n != before {
			t.Errorf("drain started through the wrapper (%d -> %d), not by the shim", before, n)
		}
	})
	secret := "AKIA" + "IOSFODNN7EXAMPLE"
	step("rejected", func(t *testing.T) {
		startServe()
		body := "# Secret\n\nthe credential " + secret + " was pasted here\n"
		rel, abs := design(11, body)
		spoolWrite("conv-r", abs, body)
		waitFor(t, 30*time.Second, "rejected file", func() bool { return len(e.rejected()) > 0 })
		txt, isErr, rerr := mcp.tool("artifact_feedback", map[string]any{"path": rel})
		if rerr || isErr {
			t.Fatalf("rejected: rpcErr=%v isErr=%v", rerr, isErr)
		}
		answers["rejected"] = txt
		t.Logf("rejected: %s", advFirstLines(txt, 3))
		if !strings.HasPrefix(txt, "state: rejected") || !strings.Contains(txt, "aws_access_key") || !strings.Contains(txt, "Fix: rewrite") || strings.Contains(txt, secret) {
			t.Errorf("rejected answer:\n%s", strings.ReplaceAll(txt, secret, "<secret>"))
		}
		e.noSecret(secret)
	})
	step("delivered-baseline", func(t *testing.T) {
		txt, isErr, rerr := mcp.tool("artifact_feedback", map[string]any{"path": target})
		if rerr || isErr {
			t.Fatalf("delivered: rpcErr=%v isErr=%v", rerr, isErr)
		}
		answers["delivered"] = txt
		t.Logf("delivered: %s", advFirstLines(txt, 3))
		if !strings.HasPrefix(txt, "state: delivered") || !strings.Contains(txt, "screen: unscreened") {
			t.Errorf("delivered answer:\n%s", txt)
		}
		for _, l := range strings.Split(txt, "\n") {
			switch {
			case strings.HasPrefix(l, checkA+" "):
				if !strings.Contains(l, "BELOW p25") {
					t.Errorf("target check line not flagged: %s", l)
				}
			case strings.HasPrefix(l, checkB+" "):
				if strings.Contains(l, "BELOW") || !strings.Contains(l, "baseline p25") {
					t.Errorf("other check line: %s", l)
				}
			}
		}
		if !strings.Contains(txt, checkA+" 0.10") {
			t.Errorf("no line for %s:\n%s", checkA, txt)
		}
	})
	step("stale", func(t *testing.T) {
		abs := filepath.Join(repo, rels[1])
		os.WriteFile(abs, []byte(bodies[1]+"edited but not captured\n"), 0o644)
		txt, isErr, rerr := mcp.tool("artifact_feedback", map[string]any{"path": rels[1]})
		if rerr || isErr {
			t.Fatalf("stale: rpcErr=%v isErr=%v", rerr, isErr)
		}
		answers["stale"] = txt
		t.Logf("stale: %s", advFirstLines(txt, 3))
		if !strings.HasPrefix(txt, "state: stale") {
			t.Errorf("stale answer:\n%s", txt)
		}
	})
	step("distinct-answers", func(t *testing.T) {
		seen := map[string]string{}
		for _, k := range []string{"queued", "rejected", "delivered", "stale"} {
			first := strings.SplitN(answers[k], "\n", 2)[0]
			if first == "" {
				t.Errorf("no answer for %s", k)
			}
			if other, dup := seen[first]; dup {
				t.Errorf("%s and %s both start %q", k, other, first)
			}
			seen[first] = k
		}
	})
	step("tools-answer", func(t *testing.T) {
		txt, isErr, rerr := mcp.tool("list_checks", map[string]any{"kind": "report"})
		if rerr || isErr || strings.Count(txt, "[levels") != 5 {
			t.Errorf("list_checks report: %v %v\n%s", rerr, isErr, txt)
		}
		txt, isErr, rerr = mcp.tool("search_artifacts", map[string]any{"query": word})
		if rerr || isErr || !strings.Contains(txt, rels[0]) || !strings.Contains(txt, "["+word+"]") {
			t.Errorf("search_artifacts: %v %v\n%s", rerr, isErr, txt)
		}
	})
	step("service-down", func(t *testing.T) {
		stopServe()
		waitFor(t, 15*time.Second, "lock free", func() bool { return !e.lockHeld() })
		rel, abs := design(12, "# Queued again\n\nstill waiting\n")
		spoolWrite("conv-q2", abs, "# Queued again\n\nstill waiting\n", "WORKFLOW_BIN=/bin/true")
		for name, p := range map[string]string{"queued": rel, "delivered": target} {
			txt, isErr, rerr := mcp.tool("artifact_feedback", map[string]any{"path": p})
			t.Logf("down/%s: %s", name, advFirstLines(txt, 3))
			if rerr || isErr {
				t.Errorf("%s: rpcErr=%v isErr=%v", name, rerr, isErr)
			}
			if !strings.HasPrefix(txt, "state: ") || !strings.Contains(txt, "service unreachable at") {
				t.Errorf("%s answer:\n%s", name, txt)
			}
		}
		for _, c := range []struct {
			tool string
			args map[string]any
		}{{"list_checks", map[string]any{"kind": "design"}}, {"search_artifacts", map[string]any{"query": word}}} {
			txt, isErr, rerr := mcp.tool(c.tool, c.args)
			if rerr || isErr || !strings.Contains(txt, "unreachable") {
				t.Errorf("%s down: rpcErr=%v isErr=%v %s", c.tool, rerr, isErr, txt)
			}
		}
	})
}
