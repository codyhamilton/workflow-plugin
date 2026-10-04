package secrets

import (
	"os"
	"os/exec"
	"strconv"
	"strings"
	"testing"
)

func rep(s string, n int) string { return strings.Repeat(s, n) }

// samples are built at runtime so no source line is credential-shaped.
func samples() map[string]string {
	return map[string]string{
		"private_key_block": "-----" + "BEGIN RSA PRIVATE" + " KEY-----\nMIIB\n-----" + "END RSA PRIVATE KEY-----",
		"sk_key":            "key is sk" + "-" + rep("a1", 12),
		"github_token":      "tok gh" + "p_" + rep("A1", 12),
		"github_pat":        "tok github" + "_pat_" + rep("A1", 15),
		"aws_access_key":    "id AK" + "IA" + rep("7Q", 8),
		"slack_token":       "x xo" + "xb-" + rep("12", 8),
		"google_api_key":    "k AI" + "za" + rep("Ab_", 12)[:35],
		"stripe_key":        "k sk" + "_live_" + rep("a9", 10),
		"jwt":               "t ey" + "J" + rep("a", 12) + "." + rep("b", 12) + "." + rep("c", 12),
		"bearer_token":      "Authorization: Bear" + "er " + rep("Ab1", 8),
		"connection_string": "db postgres" + "://admin:" + "s3cr3tpass" + "@db.example:5432/x",
		"env_assignment":    "MY_API_" + "KEY=" + "abcd1234efgh",
	}
}

func TestScanPatterns(t *testing.T) {
	names := map[string]bool{}
	for _, n := range Patterns() {
		names[n] = true
	}
	for name, s := range samples() {
		if !names[name] {
			t.Errorf("pattern %s not listed in Patterns()", name)
		}
		text := "line one\nline two\n" + s + "\nline four"
		line := 3
		hits := Scan(text)
		if len(hits) != 1 || hits[0].Pattern != name || hits[0].Line != line {
			t.Errorf("%s: hits = %+v", name, hits)
			continue
		}
		red := Redact(text)
		if !strings.Contains(red, "[REDACTED:"+name+"]") || strings.Contains(red, s) {
			t.Errorf("%s: redact = %q", name, red)
		}
		if got := Scan(red); len(got) != 0 {
			t.Errorf("%s: redacted text still hits: %+v", name, got)
		}
	}
	if len(names) != len(samples()) {
		t.Errorf("patterns %v vs samples %d", Patterns(), len(samples()))
	}
}

func TestScanLinesAndOrder(t *testing.T) {
	sm := samples()
	text := sm["sk_key"] + "\n\n" + sm["jwt"] + "\nok\n" + sm["env_assignment"]
	hits := Scan(text)
	want := []Hit{{"sk_key", 1}, {"jwt", 3}, {"env_assignment", 5}}
	if len(hits) != len(want) {
		t.Fatalf("hits = %+v", hits)
	}
	for i := range want {
		if hits[i] != want[i] {
			t.Errorf("hit %d = %+v want %+v", i, hits[i], want[i])
		}
	}
	// a multi-line private key reports its header line
	pk := "a\nb\n" + sm["private_key_block"]
	if h := Scan(pk); len(h) != 1 || h[0].Line != 3 {
		t.Errorf("pk hits %+v", h)
	}
}

func TestPlaceholdersDoNotHit(t *testing.T) {
	for _, s := range []string{
		"WORKFLOW_SERVE_KEYS=a=ka,b=kb",
		"WORKFLOW_SERVE_KEYS=aaaaaaaaaaaaaaaa",
		"API_KEY=short",
		"API_KEY=$OTHER_VARIABLE",
		"API_KEY=<your-key-here>",
		"API_KEY={{ secret }}",
		"API_KEY=…",
		"API_KEY=...",
		"API_KEY=********",
		"API_KEY=xxxxxxxxxxxx",
		`API_KEY: "xxxxxxxxxxxx"`,
		"SECRET_TOKEN: <redacted-value>",
		"db://user:<password>@host/x",
		"db://user:$PASSWORD@host/x",
		"db://user:xxxxxxxx@host/x",
		"the task-force-with-a-long-name-here and ask-me-anything-about-it",
		"Bearer <token>",
		"plain prose about a token and a password",
	} {
		if h := Scan(s); len(h) != 0 {
			t.Errorf("%q hit %+v", s, h)
		}
	}
}

func TestRepoDocsClean(t *testing.T) {
	out, err := exec.Command("git", "ls-files", "-z", "*.md").Output()
	if err != nil {
		t.Skip("not inside a git repo")
	}
	top, err := exec.Command("git", "rev-parse", "--show-toplevel").Output()
	if err != nil {
		t.Skip("not inside a git repo")
	}
	root := strings.TrimSpace(string(top))
	var bad []string
	for _, f := range strings.Split(string(out), "\x00") {
		if f == "" {
			continue
		}
		b, err := os.ReadFile(root + "/" + f)
		if err != nil {
			continue
		}
		for _, h := range Scan(string(b)) {
			bad = append(bad, f+":"+strconv.Itoa(h.Line)+" "+h.Pattern)
		}
	}
	if len(bad) > 0 {
		t.Errorf("secret-shaped text in docs:\n%s", strings.Join(bad, "\n"))
	}
}
