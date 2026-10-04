// Package keys implements the identity rules of design 1 (Keys): content and
// row hashes, repo_id, repo-relative paths and the path-to-kind rule.
package keys

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os/exec"
	"path"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// ContentHash is the lowercase hex SHA-256 of b.
func ContentHash(b []byte) string {
	s := sha256.Sum256(b)
	return hex.EncodeToString(s[:])
}

// Canonical returns the canonical JSON of the object raw with the top-level
// "id" and "content" keys removed: keys sorted, no insignificant whitespace,
// no HTML escaping, numbers keep their literal text, no trailing newline.
func Canonical(raw []byte) ([]byte, error) {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var obj map[string]any
	if err := dec.Decode(&obj); err != nil {
		return nil, fmt.Errorf("keys: not a JSON object: %w", err)
	}
	if obj == nil {
		return nil, errors.New("keys: not a JSON object: null")
	}
	if _, err := dec.Token(); err != io.EOF {
		return nil, errors.New("keys: trailing data after JSON object")
	}
	delete(obj, "id")
	delete(obj, "content")
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(obj); err != nil { // map keys are sorted by encoding/json
		return nil, err
	}
	return bytes.TrimRight(buf.Bytes(), "\n"), nil
}

// RowHash is ContentHash(Canonical(raw)).
func RowHash(raw []byte) (string, error) {
	c, err := Canonical(raw)
	if err != nil {
		return "", err
	}
	return ContentHash(c), nil
}

var schemeRe = regexp.MustCompile(`^[A-Za-z][A-Za-z0-9+.-]*://`)

// NormalizeRemote applies the design 1 repo_id normalisation to a remote URL.
func NormalizeRemote(url string) string {
	u := strings.TrimSpace(url)
	if loc := schemeRe.FindStringIndex(u); loc != nil {
		u = u[loc[1]:]
	} else if i := strings.Index(u, ":"); i > 0 && !strings.Contains(u[:i], "/") {
		u = u[:i] + "/" + u[i+1:] // scp form host:path
	}
	// drop userinfo: everything up to the last '@' in the authority
	end := strings.Index(u, "/")
	if end < 0 {
		end = len(u)
	}
	if at := strings.LastIndex(u[:end], "@"); at >= 0 {
		u = u[at+1:]
		end -= at + 1
	}
	u = strings.ToLower(u[:end]) + u[end:]
	u = strings.TrimRight(u, "/")
	u = strings.TrimSuffix(u, ".git")
	return strings.TrimRight(u, "/")
}

func git(dir string, args ...string) (string, error) {
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("git %s: %w: %s", strings.Join(args, " "), err, strings.TrimSpace(stderr.String()))
	}
	return strings.TrimSpace(string(out)), nil
}

// RepoID returns the repo_id of the repository containing dir.
func RepoID(dir string) (string, error) {
	out, err := git(dir, "remote")
	if err != nil {
		return "", err
	}
	remotes := strings.Fields(out)
	if len(remotes) > 0 {
		sort.Strings(remotes)
		name := remotes[0]
		for _, r := range remotes {
			if r == "origin" {
				name = r
			}
		}
		u, err := git(dir, "remote", "get-url", name)
		if err != nil {
			return "", err
		}
		return NormalizeRemote(u), nil
	}
	out, err = git(dir, "rev-list", "--max-parents=0", "HEAD")
	if err != nil {
		return "", err
	}
	roots := strings.Fields(out)
	if len(roots) == 0 {
		return "", errors.New("keys: repository has no remote and no commits")
	}
	sort.Strings(roots)
	return "root:" + roots[0], nil
}

// RepoPath resolves file's repo top level and the slash-separated path
// relative to it. ok is false when file is outside any repository.
func RepoPath(file string) (repoTop, rel string, ok bool, err error) {
	abs, err := filepath.Abs(file)
	if err != nil {
		return "", "", false, err
	}
	dir, err := filepath.EvalSymlinks(filepath.Dir(abs))
	if err != nil {
		return "", "", false, err
	}
	if _, lerr := exec.LookPath("git"); lerr != nil {
		return "", "", false, lerr
	}
	top, gerr := git(dir, "rev-parse", "--show-toplevel")
	if gerr != nil {
		var ee *exec.ExitError
		if errors.As(gerr, &ee) {
			return "", "", false, nil
		}
		return "", "", false, nil // not a repository
	}
	if top, err = filepath.EvalSymlinks(top); err != nil {
		return "", "", false, err
	}
	full := filepath.Join(dir, filepath.Base(abs))
	if r, rerr := filepath.EvalSymlinks(full); rerr == nil {
		full = r
	}
	r, err := filepath.Rel(top, full)
	if err != nil || r == ".." || strings.HasPrefix(r, ".."+string(filepath.Separator)) {
		return "", "", false, nil
	}
	return top, filepath.ToSlash(r), true, nil
}

var kindRe = []struct {
	re   *regexp.Regexp
	kind string
}{
	{regexp.MustCompile(`^docs/plans/[^/]+/DESIGN\.md$`), "design"},
	{regexp.MustCompile(`^docs/plans/[^/]+/briefs/[^/]+\.md$`), "brief"},
	{regexp.MustCompile(`^docs/plans/[^/]+/reports/[^/]+\.md$`), "report"},
}

// Kind maps a repo-relative path to "design", "brief", "report" or "".
func Kind(rel string) string {
	rel = path.Clean(filepath.ToSlash(rel))
	for _, k := range kindRe {
		if k.re.MatchString(rel) {
			return k.kind
		}
	}
	return ""
}
