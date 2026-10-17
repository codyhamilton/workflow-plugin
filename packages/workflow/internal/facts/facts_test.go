package facts

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

type testRepo struct {
	dir, sha, repoID string
}

func run(t *testing.T, dir string, args ...string) string {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	cmd.Env = append(os.Environ(), "GIT_CONFIG_GLOBAL=/dev/null", "GIT_AUTHOR_NAME=t", "GIT_AUTHOR_EMAIL=t@x", "GIT_COMMITTER_NAME=t", "GIT_COMMITTER_EMAIL=t@x")
	b, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v %s", args, err, b)
	}
	return strings.TrimSpace(string(b))
}

func put(t *testing.T, dir, rel, body string) {
	t.Helper()
	p := filepath.Join(dir, rel)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}

const notes = "line one\nline two\nline three\nline four\nline five\nline six\n"

func newRepo(t *testing.T) testRepo {
	dir, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	run(t, dir, "init", "-q")
	put(t, dir, "notes/old.txt", notes)
	put(t, dir, "docs/plans/x/briefs/gone.md", "# gone\n")
	run(t, dir, "add", ".")
	run(t, dir, "commit", "-q", "-m", "first")
	put(t, dir, "docs/plans/x/DESIGN.md", "# Design\n")
	put(t, dir, "docs/plans/x/briefs/a.md", "# Brief\n")
	put(t, dir, "other.txt", "x\n")
	run(t, dir, "mv", "notes/old.txt", "notes/new.txt")
	run(t, dir, "add", ".")
	run(t, dir, "commit", "-q", "-m", "second")
	id, err := keys.RepoID(dir)
	if err != nil {
		t.Fatal(err)
	}
	return testRepo{dir: dir, sha: run(t, dir, "rev-parse", "HEAD"), repoID: id}
}

func queueFile(t *testing.T, name, harness string, payload map[string]any) File {
	t.Helper()
	b, _ := json.Marshal(payload)
	return File{Name: name, Data: []byte(fmt.Sprintf("{\"ts\":1700000000.5,\"harness\":%q,\"event\":%q}\n%s", harness, payload["hook_event_name"], b))}
}

func decode(t *testing.T, o Output) []map[string]any {
	t.Helper()
	var r []map[string]any
	for _, f := range o.Facts {
		var m map[string]any
		if err := json.Unmarshal(f, &m); err != nil {
			t.Fatal(err)
		}
		r = append(r, m)
	}
	return r
}

type fixture struct {
	Name         string         `json:"name"`
	Harness      string         `json:"harness"`
	ExpectCommit bool           `json:"expect_commit"`
	Payload      map[string]any `json:"payload"`
}

func loadFixtures(t *testing.T, file string, repl ...string) []fixture {
	b, err := os.ReadFile(filepath.Join("..", "..", "..", "hooklog", "tests", "fixtures", file))
	if err != nil {
		t.Fatal(err)
	}
	text := strings.NewReplacer(repl...).Replace(string(b))
	var list []fixture
	if err := json.Unmarshal([]byte(text), &list); err != nil {
		var obj struct {
			Fixtures []fixture `json:"fixtures"`
		}
		if err := json.Unmarshal([]byte(text), &obj); err != nil {
			t.Fatal(err)
		}
		list = obj.Fixtures
	}
	return list
}

func TestWritesFixtures(t *testing.T) {
	r := newRepo(t)
	fx := loadFixtures(t, "artifact_writes.json")
	if len(fx) != 11 {
		t.Fatalf("fixtures: %d", len(fx))
	}
	put(t, r.dir, "docs/plans/example/DESIGN.md", "# Design example\n")
	put(t, r.dir, "docs/plans/example/briefs/01.md", "# Brief example\n")
	var all []json.RawMessage
	for i, f := range fx {
		f.Payload["cwd"] = r.dir
		out := Build(context.Background(), []File{queueFile(t, fmt.Sprintf("q%d", i), f.Harness, f.Payload)})[0]
		fs := decode(t, out)
		if len(fs) != 2 || len(out.Reasons) != 0 {
			t.Fatalf("fixture %d: %d facts %v", i, len(fs), out.Reasons)
		}
		if fs[0]["type"] != "hook_event" || fs[0]["id"] != fmt.Sprintf("q%d#0", i) {
			t.Fatalf("fixture %d hook_event: %v", i, fs[0])
		}
		v := fs[1]
		path := v["path"].(string)
		body, _ := os.ReadFile(filepath.Join(r.dir, path))
		if v["type"] != "artifact_version" || v["source"] != "worktree" || v["repo_id"] != r.repoID ||
			v["content_hash"] != keys.ContentHash(body) || v["content"] != string(body) || !strings.HasPrefix(path, "docs/plans/example/") {
			t.Fatalf("fixture %d version: %v", i, v)
		}
		all = append(all, out.Facts...)
	}
	assertIngest(t, all)
}

func TestWritesCoalesceAndMissing(t *testing.T) {
	r := newRepo(t)
	put(t, r.dir, "docs/plans/example/DESIGN.md", "# D\n")
	p1 := map[string]any{"hook_event_name": "postToolUse", "tool_name": "write", "conversation_id": "c", "cwd": r.dir,
		"tool_input": map[string]any{"file_path": "docs/plans/example/DESIGN.md"}}
	p2 := map[string]any{"hook_event_name": "afterFileEdit", "conversation_id": "c", "cwd": r.dir, "file_path": "docs/plans/example/DESIGN.md"}
	outs := Build(context.Background(), []File{queueFile(t, "a", "cursor", p1), queueFile(t, "b", "cursor", p2)})
	if len(outs[0].Facts) != 1 || len(outs[1].Facts) != 2 {
		t.Fatalf("coalesce: %d %d", len(outs[0].Facts), len(outs[1].Facts))
	}
	// A different conversation does not coalesce.
	p3 := map[string]any{"hook_event_name": "afterFileEdit", "conversation_id": "d", "cwd": r.dir, "file_path": "docs/plans/example/DESIGN.md"}
	outs = Build(context.Background(), []File{queueFile(t, "a", "cursor", p1), queueFile(t, "b", "cursor", p3)})
	if len(outs[0].Facts) != 2 || len(outs[1].Facts) != 2 {
		t.Fatal("conversations coalesced")
	}
	os.Remove(filepath.Join(r.dir, "docs/plans/example/DESIGN.md"))
	outs = Build(context.Background(), []File{queueFile(t, "a", "cursor", p1)})
	if len(outs[0].Facts) != 1 || len(outs[0].Reasons) != 0 {
		t.Fatalf("missing file: %d %v", len(outs[0].Facts), outs[0].Reasons)
	}
}

func TestBadFiles(t *testing.T) {
	outs := Build(context.Background(), []File{
		{Name: "a", Data: []byte("nope\n{}")},
		{Name: "b", Data: []byte("{\"ts\":1,\"harness\":\"claude\"}\n[1]")},
		{Name: "c", Data: []byte("{\"ts\":1,\"harness\":\"claude\"}\n{\"tool_name\":\"x\"}")},
		{Name: "d", Data: []byte("{\"ts\":1,\"harness\":\"claude\"}\n{not json")},
	})
	want := []string{"unparseable: envelope is not JSON", "unparseable: payload is not an object", "invalid: no conversation id", "unparseable: payload is not JSON"}
	for i, o := range outs {
		if len(o.Facts) != 0 || len(o.Reasons) != 1 || o.Reasons[0] != want[i] {
			t.Fatalf("%d: %+v", i, o)
		}
	}
}

func TestCommitFixtures(t *testing.T) {
	r := newRepo(t)
	fx := loadFixtures(t, "commit_calls.json", "{{DIR}}", r.dir, "{{SHA7}}", r.sha[:7])
	if len(fx) != 7 {
		t.Fatalf("fixtures %d", len(fx))
	}
	var all []json.RawMessage
	for i, f := range fx {
		out := Build(context.Background(), []File{queueFile(t, fmt.Sprintf("c%d", i), f.Harness, f.Payload)})[0]
		fs := decode(t, out)
		if !f.ExpectCommit {
			if len(fs) != 1 || fs[0]["type"] != "hook_event" {
				t.Fatalf("%s: unexpected facts %v", f.Name, fs)
			}
			continue
		}
		if len(fs) != 4 {
			t.Fatalf("%s: %d facts", f.Name, len(fs))
		}
		c := fs[1]
		if c["type"] != "commit" || c["sha"] != r.sha || c["repo_id"] != r.repoID {
			t.Fatalf("%s: commit %v", f.Name, c)
		}
		if got := fmt.Sprint(c["paths"]); got != "[docs/plans/x/DESIGN.md docs/plans/x/briefs/a.md notes/new.txt other.txt]" {
			t.Fatalf("%s: paths %s", f.Name, got)
		}
		rn := c["renames"].([]any)
		if len(rn) != 1 || rn[0].(map[string]any)["from"] != "notes/old.txt" || rn[0].(map[string]any)["to"] != "notes/new.txt" {
			t.Fatalf("%s: renames %v", f.Name, rn)
		}
		got2 := map[string]bool{}
		for _, v := range fs[2:] {
			if v["type"] != "artifact_version" || v["source"] != "commit" || v["sha"] != r.sha {
				t.Fatalf("%s: version %v", f.Name, v)
			}
			body := run(t, r.dir, "show", r.sha+":"+v["path"].(string))
			if strings.TrimSpace(v["content"].(string)) != body || v["content_hash"] != keys.ContentHash([]byte(v["content"].(string))) {
				t.Fatalf("%s: content %v", f.Name, v)
			}
			got2[v["path"].(string)] = true
		}
		if !got2["docs/plans/x/DESIGN.md"] || !got2["docs/plans/x/briefs/a.md"] || len(got2) != 2 {
			t.Fatalf("%s: catch-up %v", f.Name, got2)
		}
		all = append(all, out.Facts...)
	}
	assertIngest(t, all)
}

func TestCommitDedupeInBatch(t *testing.T) {
	r := newRepo(t)
	fx := loadFixtures(t, "commit_calls.json", "{{DIR}}", r.dir, "{{SHA7}}", r.sha[:7])
	a := queueFile(t, "a", fx[1].Harness, fx[1].Payload)
	b := queueFile(t, "b", fx[1].Harness, fx[1].Payload)
	outs := Build(context.Background(), []File{a, b})
	if len(outs[0].Facts) != 4 || len(outs[1].Facts) != 1 {
		t.Fatalf("%d %d", len(outs[0].Facts), len(outs[1].Facts))
	}
}

func fakeSecret() string { return "gh" + "p_" + strings.Repeat("a1B2", 9) }

func TestSecretScrub(t *testing.T) {
	r := newRepo(t)
	sec := fakeSecret()
	put(t, r.dir, "docs/plans/example/DESIGN.md", "# D\nok\ntoken: "+sec+"\n")
	p := map[string]any{"hook_event_name": "PostToolUse", "tool_name": "Write", "session_id": "s", "cwd": r.dir,
		"tool_input": map[string]any{"file_path": "docs/plans/example/DESIGN.md", "content": "token: " + sec}}
	out := Build(context.Background(), []File{queueFile(t, "q", "claude", p)})[0]
	if len(out.Facts) != 1 || len(out.Reasons) != 1 {
		t.Fatalf("%d facts %v", len(out.Facts), out.Reasons)
	}
	if !strings.Contains(out.Reasons[0], "secret: ") || !strings.Contains(out.Reasons[0], "at line 3 in docs/plans/example/DESIGN.md") {
		t.Fatalf("reason %q", out.Reasons[0])
	}
	var hv map[string]any
	json.Unmarshal(out.Facts[0], &hv)
	if hv["type"] != "hook_event" || strings.Contains(string(out.Facts[0]), sec) || !strings.Contains(string(out.Facts[0]), "[REDACTED") {
		t.Fatalf("hook_event %s", out.Facts[0])
	}
	if strings.Contains(fmt.Sprint(out.Reasons), sec) {
		t.Fatal("reason leaks secret")
	}
}

func TestSecretInCommittedBlob(t *testing.T) {
	r := newRepo(t)
	sec := fakeSecret()
	put(t, r.dir, "docs/plans/x/briefs/s.md", "key "+sec+"\n")
	run(t, r.dir, "add", ".")
	run(t, r.dir, "commit", "-q", "-m", "secret")
	sha := run(t, r.dir, "rev-parse", "HEAD")
	p := map[string]any{"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s", "cwd": r.dir,
		"tool_input": map[string]any{"command": "git commit -m secret"}, "tool_response": map[string]any{"stdout": "[main " + sha[:8] + "] secret\n"}}
	out := Build(context.Background(), []File{queueFile(t, "q", "claude", p)})[0]
	if len(out.Facts) != 2 || len(out.Reasons) != 1 || !strings.Contains(out.Reasons[0], "in docs/plans/x/briefs/s.md") {
		t.Fatalf("%d %v", len(out.Facts), out.Reasons)
	}
	for _, f := range out.Facts {
		if strings.Contains(string(f), sec) {
			t.Fatal("secret in fact")
		}
	}
}

func assertIngest(t *testing.T, facts []json.RawMessage) {
	t.Helper()
	ten, err := store.Open(t.TempDir(), store.Options{})
	if err != nil {
		t.Fatal(err)
	}
	defer ten.Close()
	res, err := ingest.Ingest(context.Background(), ten, facts)
	if err != nil {
		t.Fatal(err)
	}
	if len(res) != len(facts) {
		t.Fatalf("results %d for %d facts", len(res), len(facts))
	}
	for _, x := range res {
		if x.Status == ingest.Rejected {
			t.Fatalf("rejected: %+v", x)
		}
	}
}

func TestWritePaths(t *testing.T) {
	r := newRepo(t)
	p := map[string]any{"hook_event_name": "postToolUse", "tool_name": "write", "conversation_id": "c", "cwd": r.dir,
		"tool_input": map[string]any{"file_path": "docs/plans/x/DESIGN.md"}}
	f := queueFile(t, "a", "cursor", p)
	got := WritePaths(f.Data)
	want := filepath.Join(r.dir, "docs/plans/x/DESIGN.md")
	if len(got) != 1 || got[0] != want {
		t.Fatalf("WritePaths = %v, want [%s]", got, want)
	}
	if WritePaths([]byte("not json\n{}")) != nil || WritePaths(nil) != nil {
		t.Fatal("unparseable must give nil")
	}
	bash := queueFile(t, "b", "cursor", map[string]any{"hook_event_name": "postToolUse", "tool_name": "shell", "conversation_id": "c", "cwd": r.dir})
	if WritePaths(bash.Data) != nil {
		t.Fatal("non-write tool must give nil")
	}
}
