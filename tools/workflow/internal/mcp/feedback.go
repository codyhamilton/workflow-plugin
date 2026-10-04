package mcp

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/drain"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/facts"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
)

const fixLine = "Fix: rewrite the file; the new write is the repair."

// get makes one authenticated request. The key never leaves this function.
func (s *server) get(ctx context.Context, cfg clientconfig.Config, path string, q map[string]string, timeout time.Duration) (int, []byte, error) {
	v := url.Values{}
	for k, x := range q {
		if x != "" {
			v.Set(k, x)
		}
	}
	u := strings.TrimRight(cfg.Endpoint, "/") + path
	if len(v) > 0 {
		u += "?" + v.Encode()
	}
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	rq, err := http.NewRequestWithContext(ctx, "GET", u, nil)
	if err != nil {
		return 0, nil, errors.New("bad endpoint")
	}
	if cfg.Key != "" {
		rq.Header.Set("Authorization", "Bearer "+cfg.Key)
	}
	resp, err := s.o.HTTP.Do(rq)
	if err != nil {
		return 0, nil, errors.New("request failed")
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	return resp.StatusCode, b, nil
}

// fetch loads the config, GETs path and decodes a 200 body into out. A
// non-empty return is the full tool answer for any other outcome.
func (s *server) fetch(ctx context.Context, path string, q map[string]string, out any) string {
	cfg, err := clientconfig.Load()
	if err != nil {
		return badConfigText(err)
	}
	code, body, err := s.get(ctx, cfg, path, q, 3*time.Second)
	switch {
	case err != nil || code >= 500:
		return "service unreachable at " + cfg.Endpoint
	case code != 200:
		return fmt.Sprintf("service refused the request (HTTP %d) at %s", code, cfg.Endpoint)
	}
	if json.Unmarshal(body, out) != nil {
		return "service at " + cfg.Endpoint + " returned an unreadable answer"
	}
	return ""
}

func badConfigText(err error) string {
	return fmt.Sprintf("client config at %s is unusable: %v", clientconfig.Path(), err)
}

type qfile struct {
	name string
	mod  time.Time
	why  []string
}

// matcher finds the queue files that refer to one target.
type matcher struct {
	abs, rel, repo string
	cache          map[string][2]string // abs path -> repo, rel ("" repo when not keyed)
}

func (m *matcher) key(p string) [2]string {
	if k, ok := m.cache[p]; ok {
		return k
	}
	var k [2]string
	if top, rel, in, err := keys.RepoPath(p); err == nil && in {
		if id, err := keys.RepoID(top); err == nil {
			k = [2]string{id, rel}
		}
	}
	m.cache[p] = k
	return k
}

func (m *matcher) scan(dir string) []qfile {
	des, _ := os.ReadDir(dir)
	var out []qfile
	for _, de := range des {
		n := de.Name()
		if de.IsDir() || strings.HasPrefix(n, ".") || !strings.HasSuffix(n, ".evt") {
			continue
		}
		info, err := de.Info()
		if err != nil || !info.Mode().IsRegular() {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(dir, n))
		if err != nil {
			continue
		}
		for _, wp := range facts.WritePaths(raw) {
			if wp == m.abs {
				out = append(out, qfile{name: n, mod: info.ModTime()})
				break
			}
			if k := m.key(wp); k[0] == m.repo && k[1] == m.rel {
				out = append(out, qfile{name: n, mod: info.ModTime()})
				break
			}
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].mod.Before(out[j].mod) })
	return out
}

func reasons(path string) []string {
	b, _ := os.ReadFile(path)
	var out []string
	for _, l := range strings.Split(string(b), "\n") {
		if l = strings.TrimSpace(l); l == "" {
			continue
		}
		if _, r, ok := strings.Cut(l, ": "); ok {
			l = r
		}
		out = append(out, l)
	}
	return out
}

func (s *server) feedback(ctx context.Context, args map[string]any) (string, bool) {
	p, ok := strArg(args, "path")
	if !ok || strings.TrimSpace(p) == "" {
		return "path must be a non-empty string", true
	}
	abs := p
	if !filepath.IsAbs(p) {
		wd, err := s.o.Getwd()
		if err != nil {
			return "cannot resolve the working directory", true
		}
		abs = filepath.Join(wd, p)
	}
	abs = filepath.Clean(abs)
	info, err := os.Stat(abs)
	if err != nil {
		return "path does not exist: " + abs, true
	}
	if info.IsDir() {
		return "path is a directory, not a file: " + abs, true
	}
	data, err := os.ReadFile(abs)
	if err != nil {
		return "cannot read " + abs, true
	}
	hash := keys.ContentHash(data)
	top, rel, in, err := keys.RepoPath(abs)
	untracked := func(why string) (string, bool) {
		return "state: not tracked\npath: " + abs + "\n" + why + "; nothing is captured for this file", false
	}
	if err != nil || !in {
		return untracked("not inside a git repository")
	}
	if keys.Kind(rel) == "" {
		return untracked("not a design, brief or report path")
	}
	repo, err := keys.RepoID(top)
	if err != nil {
		return untracked("repository has no commit yet, so it has no repo_id")
	}
	head := fmt.Sprintf("path: %s\nrepo: %s\ncontent_hash: %s\n", rel, repo, hash)
	state := func(st string, lines ...string) (string, bool) {
		return "state: " + st + "\n" + head + strings.Join(lines, "\n"), false
	}
	m := &matcher{abs: abs, rel: rel, repo: repo, cache: map[string][2]string{}}
	dir := s.o.QueueDir
	queued := m.scan(dir)
	cfg, cfgErr := clientconfig.Load()
	if len(queued) > 0 && cfgErr == nil {
		if !drain.Running(dir) {
			if err := s.o.StartDrain(); err != nil {
				fmt.Fprintln(os.Stderr, "workflow mcp: could not start the drain:", err)
			}
		}
	}
	if len(queued) > 0 && cfgErr == nil && s.o.Wait > 0 {
		deadline := time.Now().Add(s.o.Wait)
		for len(queued) > 0 && time.Now().Before(deadline) {
			select {
			case <-ctx.Done():
			case <-time.After(100 * time.Millisecond):
			}
			queued = m.scan(dir)
		}
	}
	if len(queued) > 0 {
		why := "draining"
		var extra []string
		switch {
		case cfgErr != nil:
			why = "bad config (" + clientconfig.Path() + ")"
		default:
			if code, _, err := s.get(ctx, cfg, "/v1/health", nil, 3*time.Second); err != nil || code >= 500 {
				why = "remote unreachable"
				extra = []string{"service unreachable at " + cfg.Endpoint}
			}
		}
		age := time.Since(queued[0].mod).Round(time.Second)
		return state("queued", append([]string{fmt.Sprintf("%d events for this file still queued, oldest %s, %s", len(queued), age, why)}, extra...)...)
	}
	var rejLines []string
	superseded := false
	for _, r := range m.scan(filepath.Join(dir, "rejected")) {
		if r.mod.Before(info.ModTime()) {
			superseded = true
			continue
		}
		rejLines = append(rejLines, reasons(filepath.Join(dir, "rejected", r.name+".reason"))...)
	}
	if len(rejLines) > 0 {
		return state("rejected", append(rejLines, fixLine)...)
	}
	var note []string
	if superseded {
		note = []string{"note: earlier rejection superseded by a later write"}
	}
	if cfgErr != nil {
		return state("bad config", append([]string{badConfigText(cfgErr)}, note...)...)
	}
	code, body, err := s.get(ctx, cfg, "/v1/artifacts", map[string]string{"repo_id": repo, "path": rel}, 3*time.Second)
	switch {
	case err != nil || code >= 500:
		return state("not delivered", append([]string{"nothing queued or rejected locally", "service unreachable at " + cfg.Endpoint}, note...)...)
	case code == 404:
		return state("not delivered", append([]string{"the service has no version of this file and nothing is queued; if it was just written, wait for the hook or rewrite the file"}, note...)...)
	case code != 200:
		return state("not delivered", append([]string{fmt.Sprintf("service refused the request (HTTP %d) at %s", code, cfg.Endpoint)}, note...)...)
	}
	var a struct {
		Versions int `json:"versions"`
		Latest   struct {
			Hash       string `json:"content_hash"`
			ReceivedAt string `json:"received_at"`
			Screen     *struct {
				Verdict string `json:"verdict"`
				Scorer  string `json:"scorer"`
			} `json:"screen"`
			Scores []struct {
				Check string  `json:"check"`
				Score float64 `json:"score"`
			} `json:"scores"`
			Rejection *struct {
				Stage  string `json:"stage"`
				Reason string `json:"reason"`
			} `json:"rejection"`
		} `json:"latest"`
	}
	if json.Unmarshal(body, &a) != nil {
		return state("not delivered", "service at "+cfg.Endpoint+" returned an unreadable answer")
	}
	l := a.Latest
	if l.Hash != hash {
		short := l.Hash
		if len(short) > 12 {
			short = short[:12]
		}
		return state("stale", append([]string{fmt.Sprintf("current content not yet delivered (service has %s from %s); normally a write still in the batch window", short, l.ReceivedAt)}, note...)...)
	}
	var lines []string
	switch {
	case l.Screen != nil && l.Screen.Verdict == "unscreened":
		lines = append(lines, "screen: unscreened (no scorer on the service)")
	case l.Screen != nil && l.Screen.Verdict == "pass":
		lines = append(lines, "screen: pass by "+l.Screen.Scorer)
	case l.Screen != nil:
		lines = append(lines, "screen: "+l.Screen.Verdict)
	case l.Rejection != nil && l.Rejection.Stage == "screen":
		lines = append(lines, "screen: flagged: "+l.Rejection.Reason, fixLine)
	default:
		lines = append(lines, "screen: awaiting screen")
		if l.Rejection != nil {
			lines = append(lines, fmt.Sprintf("rejection at %s: %s", l.Rejection.Stage, l.Rejection.Reason))
		}
	}
	var bl struct {
		Checks map[string]struct {
			N      int     `json:"n"`
			P25    float64 `json:"p25"`
			Median float64 `json:"median"`
		} `json:"checks"`
	}
	if len(l.Scores) > 0 {
		if c, b, err := s.get(ctx, cfg, "/v1/baselines", map[string]string{"kind": keys.Kind(rel)}, 3*time.Second); err != nil || c != 200 || json.Unmarshal(b, &bl) != nil {
			lines = append(lines, "baselines unavailable")
		}
	}
	for _, sc := range l.Scores {
		b, has := bl.Checks[sc.Check]
		switch {
		case !has:
			lines = append(lines, fmt.Sprintf("%s %.2f (no baseline)", sc.Check, sc.Score))
		case b.N < 4:
			lines = append(lines, fmt.Sprintf("%s %.2f (baseline n=%d, too few to flag)", sc.Check, sc.Score, b.N))
		default:
			t := ""
			if sc.Score < b.P25 {
				t = " BELOW p25"
			}
			lines = append(lines, fmt.Sprintf("%s %.2f (baseline p25 %.2f, median %.2f, n %d)%s", sc.Check, sc.Score, b.P25, b.Median, b.N, t))
		}
	}
	lines = append(lines, fmt.Sprintf("versions: %d", a.Versions))
	return state("delivered", append(lines, note...)...)
}
