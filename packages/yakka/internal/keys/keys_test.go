package keys

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestNormalizeRemote(t *testing.T) {
	for in, want := range map[string]string{
		"git@github.com:a/b.git":               "github.com/a/b",
		"https://github.com/a/b":               "github.com/a/b",
		"ssh://git@GitHub.com/a/b.git/":        "github.com/a/b",
		"https://user:pw@host.example/x/y.git": "host.example/x/y",
		"git@GitHub.com:Org/Repo.git":          "github.com/Org/Repo",
		"https://github.com/a/b.git/":          "github.com/a/b",
	} {
		if got := NormalizeRemote(in); got != want {
			t.Errorf("NormalizeRemote(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestCanonicalRowHash(t *testing.T) {
	base := `{"b":1,"a":{"y":[3,1],"x":"<&>"},"id":"q#1","content":"zzz"}`
	h0, err := RowHash([]byte(base))
	if err != nil {
		t.Fatal(err)
	}
	same := []string{
		"{ \"a\" : {\"x\":\"<&>\", \"y\":[3,1]},\n \"b\":1 }",
		`{"id":"other#9","a":{"x":"<&>","y":[3,1]},"b":1,"content":"different"}`,
		`{"a":{"x":"<&>","y":[3,1]},"b":1}`,
	}
	for _, s := range same {
		if h, _ := RowHash([]byte(s)); h != h0 {
			t.Errorf("hash changed for %s", s)
		}
	}
	for _, s := range []string{
		`{"b":2,"a":{"y":[3,1],"x":"<&>"}}`,
		`{"b":1,"a":{"y":[1,3],"x":"<&>"}}`,
		`{"b":1,"a":{"y":[3,1],"x":"<&>"},"extra":null}`,
	} {
		if h, _ := RowHash([]byte(s)); h == h0 {
			t.Errorf("hash unchanged for %s", s)
		}
	}
	c, err := Canonical([]byte(`{"n":1.700000000123456789e9,"k":"<>"}`))
	if err != nil {
		t.Fatal(err)
	}
	if string(c) != `{"k":"<>","n":1.700000000123456789e9}` {
		t.Errorf("canonical = %s", c)
	}
	for _, bad := range []string{`[1]`, `"x"`, `nope`, `{} {}`} {
		if _, err := Canonical([]byte(bad)); err == nil {
			t.Errorf("expected error for %q", bad)
		}
	}
	if ContentHash([]byte("abc")) != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad" {
		t.Error("ContentHash wrong")
	}
}

func TestKind(t *testing.T) {
	for in, want := range map[string]string{
		"docs/plans/09-x/DESIGN.md":       "design",
		"docs/plans/09-x/briefs/1-01.md":  "brief",
		"docs/plans/09-x/reports/1-01.md": "report",
		"docs/plans/09-x/briefs/sub/a.md": "",
		"docs/plans/09-x/briefs/a.txt":    "",
		"docs/plans/DESIGN.md":            "",
		"docs/design/01.md":               "",
		"x/docs/plans/09-x/DESIGN.md":     "",
	} {
		if got := Kind(in); got != want {
			t.Errorf("Kind(%q) = %q, want %q", in, got, want)
		}
	}
}

func tgit(t *testing.T, dir string, args ...string) string {
	t.Helper()
	cmd := exec.Command("git", args...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_GLOBAL=/dev/null", "GIT_CONFIG_SYSTEM=/dev/null",
		"GIT_AUTHOR_NAME=t", "GIT_AUTHOR_EMAIL=t@t", "GIT_COMMITTER_NAME=t", "GIT_COMMITTER_EMAIL=t@t")
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v\n%s", args, err, out)
	}
	return strings.TrimSpace(string(out))
}

func newRepo(t *testing.T) string {
	t.Helper()
	t.Setenv("GIT_CONFIG_GLOBAL", "/dev/null")
	t.Setenv("GIT_CONFIG_SYSTEM", "/dev/null")
	d, _ := filepath.EvalSymlinks(t.TempDir())
	tgit(t, d, "init", "-q", "-b", "main")
	tgit(t, d, "commit", "-q", "--allow-empty", "-m", "root")
	return d
}

func TestRepoID(t *testing.T) {
	a, b := newRepo(t), newRepo(t)
	tgit(t, a, "remote", "add", "origin", "git@github.com:a/b.git")
	tgit(t, b, "remote", "add", "origin", "https://github.com/a/b")
	ia, err := RepoID(a)
	if err != nil {
		t.Fatal(err)
	}
	ib, _ := RepoID(b)
	if ia != "github.com/a/b" || ia != ib {
		t.Errorf("ids %q %q", ia, ib)
	}

	// origin wins over an earlier-named remote
	tgit(t, a, "remote", "add", "aaa", "https://other.example/z")
	if id, _ := RepoID(a); id != "github.com/a/b" {
		t.Errorf("origin not preferred: %q", id)
	}

	// only upstream
	c := newRepo(t)
	tgit(t, c, "remote", "add", "upstream", "https://Up.example/u/v.git")
	if id, _ := RepoID(c); id != "up.example/u/v" {
		t.Errorf("upstream id %q", id)
	}

	// no remote
	d := newRepo(t)
	root := tgit(t, d, "rev-list", "--max-parents=0", "HEAD")
	if id, _ := RepoID(d); id != "root:"+root {
		t.Errorf("root id %q want root:%s", id, root)
	}

	// worktrees share an ID
	wt := filepath.Join(t.TempDir(), "wt")
	tgit(t, a, "worktree", "add", "-q", "-b", "other", wt)
	if id, err := RepoID(wt); err != nil || id != "github.com/a/b" {
		t.Errorf("worktree id %q %v", id, err)
	}
	e := newRepo(t)
	wt2 := filepath.Join(t.TempDir(), "wt")
	tgit(t, e, "worktree", "add", "-q", "-b", "other", wt2)
	i1, _ := RepoID(e)
	i2, _ := RepoID(wt2)
	if i1 != i2 || !strings.HasPrefix(i1, "root:") {
		t.Errorf("no-remote worktree ids %q %q", i1, i2)
	}
}

func TestRepoPath(t *testing.T) {
	d := newRepo(t)
	os.MkdirAll(filepath.Join(d, "docs", "plans", "p"), 0o755)
	f := filepath.Join(d, "docs", "plans", "p", "DESIGN.md")
	os.WriteFile(f, []byte("x"), 0o644)
	top, rel, ok, err := RepoPath(f)
	if err != nil || !ok || top != d || rel != "docs/plans/p/DESIGN.md" {
		t.Errorf("got %q %q %v %v", top, rel, ok, err)
	}
	link := filepath.Join(t.TempDir(), "link")
	os.Symlink(d, link)
	_, rel, ok, _ = RepoPath(filepath.Join(link, "docs", "plans", "p", "DESIGN.md"))
	if !ok || rel != "docs/plans/p/DESIGN.md" {
		t.Errorf("symlink: %q %v", rel, ok)
	}
	out := t.TempDir()
	os.WriteFile(filepath.Join(out, "a.md"), []byte("x"), 0o644)
	if _, _, ok, err := RepoPath(filepath.Join(out, "a.md")); ok || err != nil {
		t.Errorf("outside repo: ok=%v err=%v", ok, err)
	}
}
