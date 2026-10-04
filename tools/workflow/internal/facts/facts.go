// Package facts turns queue files into the facts design 2 says they yield (Building facts, Commit
// facts, Scrub outcome, Delivery), as pure library code for the drain.
//
// Queue file format (unit 2-01): the first line is the envelope {"ts","harness","event"}, the rest
// is the raw payload JSON object. Build returns one Output per input file, in order. Facts carry
// the wire shape of package ingest and an `id` of "<file name>#<n>" (hook_event is always #0).
// An Output with any Reasons means the drain moves that file to rejected/ after delivering its
// facts. A file that cannot be parsed, or has no conversation ID, yields no facts and a reason.
//
// hook_event: the payload with every string leaf passed through secrets.Redact; the common keys
// (conversation_id, harness, event, ts) are lifted out, the payload keeps its native shape.
//
// artifact_version (source "worktree"): for write events on the design 2 write-surface table whose
// path has a keys.Kind. The file is read once per Build and hashed raw (keys.ContentHash). A
// missing, unreadable or non-UTF-8 file produces nothing. Content is never redacted: a
// secrets.Scan hit produces no version and the reason "secret: <pattern> at line <n> in <path>".
// Repeated writes to one (conversation, repo, path) in a Build yield one version, attached to the
// last file that referred to it.
//
// commit: from a successful post-tool shell call whose command contains `git [opts] commit` and
// whose output has a "[branch sha]" line, resolved with git rev-parse; paths and renames come from
// `git diff-tree -M --name-status -r --root`. Each added/modified/renamed-to path with a kind also
// gets an artifact_version with source "commit" and an extra "sha" key, read with git show.
// A git failure skips that fact and is not a reason. git runs without a shell, 10 s per call.
package facts

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/secrets"
)

// File is one queue file: its name and raw bytes.
type File struct {
	Name string
	Data []byte
}

// Output is the result for one File.
type Output struct {
	Name    string
	Facts   []json.RawMessage
	Reasons []string
}

type parsed struct {
	name    string
	payload map[string]any
	conv    string
	harness string
	event   string
	ts      json.Number
	base    string // cwd, else workspace_roots[0]
	refs    []ref
	reasons []string
	bad     bool
}

type ref struct {
	key  string // conv|repo|rel
	abs  string
	rel  string
	repo string
}

type readResult struct {
	content string
	raw     []byte
	ok      bool
}

// Build builds the facts for a batch of queue files.
func Build(ctx context.Context, files []File) []Output {
	ps := make([]*parsed, len(files))
	for i, f := range files {
		ps[i] = parseFile(f)
	}
	reads := map[string]readResult{}
	last := map[string]int{}
	for i, p := range ps {
		if p.bad {
			continue
		}
		for _, abs := range writePaths(p) {
			r, ok := reads[abs]
			if !ok {
				r = readFile(abs)
				reads[abs] = r
			}
			if !r.ok {
				continue
			}
			top, rel, in, err := keys.RepoPath(abs)
			if err != nil || !in || keys.Kind(rel) == "" {
				continue
			}
			id, err := keys.RepoID(top)
			if err != nil {
				continue
			}
			k := p.conv + "\x00" + id + "\x00" + rel
			p.refs = append(p.refs, ref{key: k, abs: abs, rel: rel, repo: id})
			last[k] = i
		}
	}
	out := make([]Output, len(files))
	commits := map[string]bool{}
	for i, p := range ps {
		o := Output{Name: p.name}
		if p.bad {
			o.Reasons = p.reasons
			out[i] = o
			continue
		}
		add := func(v map[string]any) {
			v["id"] = fmt.Sprintf("%s#%d", p.name, len(o.Facts))
			b, _ := json.Marshal(v)
			o.Facts = append(o.Facts, b)
		}
		common := func(typ string) map[string]any {
			return map[string]any{"type": typ, "conversation_id": p.conv, "harness": p.harness, "event": p.event, "ts": p.ts}
		}
		hv := common("hook_event")
		hv["payload"] = redact(p.payload)
		add(hv)
		seen := map[string]bool{}
		for _, r := range p.refs {
			if last[r.key] != i || seen[r.key] {
				continue
			}
			seen[r.key] = true
			rd := reads[r.abs]
			if hits := secrets.Scan(rd.content); len(hits) > 0 {
				o.Reasons = append(o.Reasons, fmt.Sprintf("secret: %s at line %d in %s", hits[0].Pattern, hits[0].Line, r.rel))
				continue
			}
			v := common("artifact_version")
			v["repo_id"], v["path"], v["content_hash"], v["content"], v["source"] = r.repo, r.rel, keys.ContentHash(rd.raw), rd.content, "worktree"
			add(v)
		}
		buildCommits(ctx, p, commits, common, add, &o)
		out[i] = o
	}
	return out
}

func parseFile(f File) *parsed {
	p := &parsed{name: f.Name, bad: true}
	line, rest, _ := bytes.Cut(f.Data, []byte("\n"))
	var env struct {
		TS      json.Number `json:"ts"`
		Harness string      `json:"harness"`
		Event   string      `json:"event"`
	}
	d := json.NewDecoder(bytes.NewReader(line))
	d.UseNumber()
	if err := d.Decode(&env); err != nil {
		p.reasons = []string{"unparseable: envelope is not JSON"}
		return p
	}
	d = json.NewDecoder(bytes.NewReader(rest))
	d.UseNumber()
	var v any
	if err := d.Decode(&v); err != nil {
		p.reasons = []string{"unparseable: payload is not JSON"}
		return p
	}
	obj, ok := v.(map[string]any)
	if !ok {
		p.reasons = []string{"unparseable: payload is not an object"}
		return p
	}
	p.payload, p.harness, p.ts = obj, env.Harness, env.TS
	if p.ts == "" {
		p.ts = "0"
	}
	for _, k := range []string{"session_id", "conversation_id", "sessionID"} {
		if s, ok := obj[k].(string); ok && s != "" {
			p.conv = s
			break
		}
	}
	if p.conv == "" {
		p.reasons = []string{"invalid: no conversation id"}
		return p
	}
	p.event = env.Event
	if p.event == "" {
		p.event, _ = obj["hook_event_name"].(string)
	}
	if s, ok := obj["cwd"].(string); ok && s != "" {
		p.base = s
	} else if w, ok := obj["workspace_roots"].([]any); ok && len(w) > 0 {
		p.base, _ = w[0].(string)
	}
	p.bad = false
	return p
}

func redact(v any) any {
	switch x := v.(type) {
	case string:
		return secrets.Redact(x)
	case map[string]any:
		m := make(map[string]any, len(x))
		for k, e := range x {
			m[k] = redact(e)
		}
		return m
	case []any:
		a := make([]any, len(x))
		for i, e := range x {
			a[i] = redact(e)
		}
		return a
	}
	return v
}

func readFile(abs string) readResult {
	b, err := os.ReadFile(abs)
	if err != nil || !utf8.Valid(b) {
		return readResult{}
	}
	return readResult{content: string(b), raw: b, ok: true}
}

// --- write surfaces (port of tools/quality/artifact_submit.py write_paths) ---

var writeTools = map[string]bool{"write": true, "edit": true, "multiedit": true, "write_file": true,
	"edit_file": true, "create_file": true, "str_replace_editor": true, "apply_patch": true, "applypatch": true}

var patchRE = regexp.MustCompile(`(?m)^\*\*\* (?:Add File|Update File|Move to): (.+)$`)

func writePaths(p *parsed) []string {
	var raw []string
	payload := p.payload
	event := p.event
	if e, _ := payload["hook_event_name"].(string); e != "" {
		event = e
	} else if e, _ := payload["event"].(string); e != "" {
		event = e
	}
	if p.harness == "cursor" && event == "afterFileEdit" {
		if s, ok := payload["file_path"].(string); ok {
			raw = []string{s}
		}
	} else {
		expected := map[string]string{"claude": "PostToolUse", "codex": "PostToolUse", "cursor": "postToolUse", "opencode": "tool.execute.after"}
		if event != expected[p.harness] || payload["source"] == "bus" {
			return nil
		}
		tn, _ := payload["tool_name"].(string)
		name := strings.ToLower(tn[strings.LastIndex(tn, ".")+1:])
		if !writeTools[name] {
			return nil
		}
		isPatch := name == "apply_patch" || name == "applypatch"
		args := map[string]any{}
		switch ti := payload["tool_input"].(type) {
		case map[string]any:
			args = ti
		case string:
			if ti != "" {
				var v any
				if json.Unmarshal([]byte(ti), &v) == nil {
					m, ok := v.(map[string]any)
					if !ok {
						return nil
					}
					args = m
				} else if isPatch {
					args = map[string]any{"patch": ti}
				}
			}
		case nil:
		default:
			return nil
		}
		for _, k := range []string{"file_path", "path", "filePath", "target_file"} {
			if s, ok := args[k].(string); ok {
				raw = append(raw, s)
			}
		}
		if edits, ok := args["edits"].([]any); ok {
			for _, e := range edits {
				if m, ok := e.(map[string]any); ok {
					for _, k := range []string{"file_path", "path", "filePath"} {
						if s, ok := m[k].(string); ok {
							raw = append(raw, s)
						}
					}
				}
			}
		}
		if isPatch {
			patch, _ := args["patch"].(string)
			if patch == "" {
				patch, _ = args["input"].(string)
			}
			for _, m := range patchRE.FindAllStringSubmatch(patch, -1) {
				raw = append(raw, m[1])
			}
		}
	}
	var out []string
	seen := map[string]bool{}
	for _, r := range raw {
		abs := r
		if !filepath.IsAbs(r) {
			if p.base == "" {
				continue
			}
			abs = filepath.Join(p.base, r)
		}
		abs = filepath.Clean(abs)
		if !seen[abs] {
			seen[abs] = true
			out = append(out, abs)
		}
	}
	return out
}

// --- commits ---

var (
	gitCommitRE = regexp.MustCompile(`(?:^|[\s;&|(])git((?:\s+(?:-C\s+(?:"[^"]*"|'[^']*'|\S+)|-c\s+\S+|--[\w-]+(?:=\S+)?))*)\s+commit(?:[\s;&|)]|$)`)
	dirRE       = regexp.MustCompile(`-C\s+("[^"]*"|'[^']*'|\S+)`)
	shaRE       = regexp.MustCompile(`(?m)^\[(?:[^\]]*\s)?([0-9a-f]{7,40})\]`)
	postEvents  = map[string]bool{"PostToolUse": true, "postToolUse": true, "afterShellExecution": true, "tool.execute.after": true}
)

func asObject(v any) map[string]any {
	switch x := v.(type) {
	case map[string]any:
		return x
	case string:
		var m map[string]any
		if json.Unmarshal([]byte(x), &m) == nil {
			return m
		}
	}
	return nil
}

func commandText(payload map[string]any) string {
	var c any
	if ti := asObject(payload["tool_input"]); ti != nil {
		c = ti["command"]
	}
	if c == nil {
		c = payload["command"]
	}
	switch x := c.(type) {
	case string:
		return x
	case []any:
		var parts []string
		for _, e := range x {
			if s, ok := e.(string); ok {
				parts = append(parts, s)
			}
		}
		return strings.Join(parts, " ")
	}
	return ""
}

func nonZero(v any) bool {
	switch x := v.(type) {
	case json.Number:
		f, err := x.Float64()
		return err == nil && f != 0
	case float64:
		return x != 0
	}
	return false
}

// outputAndFailed returns the output text and whether the call failed.
func outputAndFailed(payload map[string]any) (string, bool) {
	failed := nonZero(payload["exit_code"]) || nonZero(payload["exitCode"])
	var texts []string
	for _, k := range []string{"tool_response", "tool_output", "output"} {
		v := payload[k]
		if s, ok := v.(string); ok {
			if m := asObject(s); m != nil {
				v = m
			} else {
				texts = append(texts, s)
				continue
			}
		}
		if m, ok := v.(map[string]any); ok {
			failed = failed || nonZero(m["exit_code"]) || nonZero(m["exitCode"])
			for _, f := range []string{"stdout", "output", "stderr"} {
				if s, ok := m[f].(string); ok {
					texts = append(texts, s)
				}
			}
		}
	}
	return strings.Join(texts, "\n"), failed
}

func unquote(s string) string {
	if len(s) >= 2 && (s[0] == '"' || s[0] == '\'') && s[len(s)-1] == s[0] {
		return s[1 : len(s)-1]
	}
	return s
}

func git(ctx context.Context, dir string, args ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, "git", append([]string{"-C", dir}, args...)...)
	cmd.Env = append(os.Environ(), "GIT_TERMINAL_PROMPT=0")
	return cmd.Output()
}

func buildCommits(ctx context.Context, p *parsed, done map[string]bool, common func(string) map[string]any, add func(map[string]any), o *Output) {
	event, _ := p.payload["hook_event_name"].(string)
	if event == "" {
		event = p.event
	}
	if !postEvents[event] {
		return
	}
	cmdText := commandText(p.payload)
	matches := gitCommitRE.FindAllStringSubmatch(cmdText, -1)
	if len(matches) == 0 {
		return
	}
	text, failed := outputAndFailed(p.payload)
	if failed {
		return
	}
	sm := shaRE.FindStringSubmatch(text)
	if sm == nil {
		return
	}
	for _, m := range matches {
		dir := p.base
		for _, d := range dirRE.FindAllStringSubmatch(m[1], -1) {
			c := unquote(d[1])
			if filepath.IsAbs(c) {
				dir = c
			} else if dir != "" {
				dir = filepath.Join(dir, c)
			} else {
				dir = ""
			}
		}
		if dir == "" {
			continue
		}
		b, err := git(ctx, dir, "rev-parse", "--verify", sm[1]+"^{commit}")
		if err != nil {
			continue
		}
		sha := strings.TrimSpace(string(b))
		repo, err := keys.RepoID(dir)
		if err != nil {
			continue
		}
		dk := p.conv + "\x00" + repo + "\x00" + sha
		if done[dk] {
			return
		}
		b, err = git(ctx, dir, "diff-tree", "-M", "--name-status", "-r", "--root", "--no-commit-id", "-z", sha)
		if err != nil {
			continue
		}
		done[dk] = true
		paths := []string{}
		renames := []map[string]string{}
		var catchup []string
		toks := strings.Split(string(b), "\x00")
		for i := 0; i < len(toks); i++ {
			st := toks[i]
			if st == "" {
				continue
			}
			switch st[0] {
			case 'R', 'C':
				if i+2 >= len(toks) {
					i = len(toks)
					break
				}
				from, to := toks[i+1], toks[i+2]
				i += 2
				paths = append(paths, to)
				if st[0] == 'R' {
					renames = append(renames, map[string]string{"from": from, "to": to})
					catchup = append(catchup, to)
				}
			default:
				if i+1 >= len(toks) {
					i = len(toks)
					break
				}
				path := toks[i+1]
				i++
				paths = append(paths, path)
				if st[0] == 'A' || st[0] == 'M' || st[0] == 'T' {
					catchup = append(catchup, path)
				}
			}
		}
		c := common("commit")
		c["repo_id"], c["sha"], c["paths"], c["renames"] = repo, sha, paths, renames
		add(c)
		for _, path := range catchup {
			if keys.Kind(path) == "" {
				continue
			}
			blob, err := git(ctx, dir, "show", sha+":"+path)
			if err != nil || !utf8.Valid(blob) {
				continue
			}
			if hits := secrets.Scan(string(blob)); len(hits) > 0 {
				o.Reasons = append(o.Reasons, "secret: "+hits[0].Pattern+" at line "+strconv.Itoa(hits[0].Line)+" in "+path)
				continue
			}
			v := common("artifact_version")
			v["repo_id"], v["path"], v["content_hash"], v["content"], v["source"], v["sha"] = repo, path, keys.ContentHash(blob), string(blob), "commit", sha
			add(v)
		}
		return
	}
}
