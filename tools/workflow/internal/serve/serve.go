// Package serve is the HTTP service of design 3: per-tenant auth, ingest, advisory artifact reads
// and the pending-content worker.
package serve

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/scorer"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

const maxBody = 16 << 20

var tenantRE = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`)

// Config is the server configuration.
type Config struct {
	Addr, Data string
	Keys       []KeyPair
}

// KeyPair maps one key to one tenant.
type KeyPair struct{ Tenant, Key string }

// ConfigFromEnv reads WORKFLOW_SERVE_ADDR, WORKFLOW_SERVE_DATA and WORKFLOW_SERVE_KEYS.
func ConfigFromEnv(getenv func(string) string) (Config, error) {
	c := Config{Addr: getenv("WORKFLOW_SERVE_ADDR"), Data: getenv("WORKFLOW_SERVE_DATA")}
	if c.Addr == "" {
		c.Addr = "127.0.0.1:8770"
	}
	if c.Data == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return c, errors.New("WORKFLOW_SERVE_DATA unset and no home directory")
		}
		c.Data = filepath.Join(home, ".local/share/workflow/serve")
	}
	ks, err := ParseKeys(getenv("WORKFLOW_SERVE_KEYS"))
	c.Keys = ks
	return c, err
}

// ParseKeys parses "tenant=key[,tenant=key…]". Errors name the problem, never a key.
func ParseKeys(s string) ([]KeyPair, error) {
	if strings.TrimSpace(s) == "" {
		return nil, errors.New("WORKFLOW_SERVE_KEYS is required and is empty")
	}
	var out []KeyPair
	seenKey := map[string]string{}
	seenTenant := map[string]bool{}
	for i, part := range strings.Split(s, ",") {
		t, k, ok := strings.Cut(part, "=")
		if !ok || k == "" {
			return nil, fmt.Errorf("WORKFLOW_SERVE_KEYS entry %d is not tenant=key", i+1)
		}
		if !tenantRE.MatchString(t) {
			return nil, fmt.Errorf("WORKFLOW_SERVE_KEYS entry %d has an invalid tenant name", i+1)
		}
		if o, dup := seenKey[k]; dup {
			return nil, fmt.Errorf("WORKFLOW_SERVE_KEYS gives one key to two tenants (%q and %q)", o, t)
		}
		if seenTenant[t] {
			return nil, fmt.Errorf("WORKFLOW_SERVE_KEYS names tenant %q twice", t)
		}
		seenKey[k], seenTenant[t] = t, true
		out = append(out, KeyPair{t, k})
	}
	return out, nil
}

// Options tunes a Server.
type Options struct {
	Version       string
	DisableWorker bool          // tests: leave pending/ alone
	PollInterval  time.Duration // default 3s
	GroupWindow   time.Duration
	ScreenStep    ScreenFunc    // default: promote as unscreened
	ScreenBackoff time.Duration // first wait after an unreachable scorer; default 5s, doubles to 5 min
}

// ScreenFunc is the screen step applied to one pending hash. Phase 3 replaces it.
type ScreenFunc func(ctx context.Context, t *store.Tenant, hash string) error

func unscreened(ctx context.Context, t *store.Tenant, hash string) error {
	return t.Promote(ctx, hash, store.Screen{Verdict: "unscreened"})
}

type tenantState struct {
	t       *store.Tenant
	wake    chan struct{}
	started bool
	gaps    atomic.Int64 // screen gaps counted at worker start
}

// Server is the HTTP service.
type Server struct {
	cfg    Config
	opts   Options
	screen ScreenFunc

	mu      sync.Mutex
	tenants map[string]*tenantState
	closed  bool
	stop    chan struct{}
	wg      sync.WaitGroup
}

// New builds a Server.
func New(cfg Config, opts Options) *Server {
	if opts.PollInterval <= 0 {
		opts.PollInterval = 3 * time.Second
	}
	if opts.ScreenBackoff <= 0 {
		opts.ScreenBackoff = 5 * time.Second
	}
	if opts.Version == "" {
		opts.Version = "dev"
	}
	s := &Server{cfg: cfg, opts: opts, tenants: map[string]*tenantState{}, stop: make(chan struct{}), screen: opts.ScreenStep}
	if s.screen == nil {
		s.screen = unscreened
	}
	return s
}

// SetWorkerEnabled is not offered after start; use Options.DisableWorker. StartWorker starts the
// worker for every open tenant and any opened later (tests that began disabled).
func (s *Server) StartWorker() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.opts.DisableWorker = false
	for _, ts := range s.tenants {
		s.startWorkerLocked(ts)
	}
}

func (s *Server) startWorkerLocked(ts *tenantState) {
	if s.opts.DisableWorker || ts.started {
		return
	}
	ts.started = true
	s.wg.Add(1)
	go s.worker(ts)
}

const maxBackoff = 5 * time.Minute

func (s *Server) worker(ts *tenantState) {
	defer s.wg.Done()
	tick := time.NewTicker(s.opts.PollInterval)
	defer tick.Stop()
	reconciled := false
	var backoff time.Duration
	for {
		unreachable := false
		if !reconciled {
			var done bool
			done, unreachable = s.reconcile(ts)
			reconciled = done
		}
		if !unreachable {
			unreachable = s.drainPending(ts)
		}
		if unreachable {
			if backoff == 0 {
				backoff = s.opts.ScreenBackoff
			} else if backoff *= 2; backoff > maxBackoff {
				backoff = maxBackoff
			}
			select { // wakes are ignored while backing off
			case <-s.stop:
				return
			case <-time.After(backoff):
			}
			continue
		}
		backoff = 0
		select {
		case <-s.stop:
			return
		case <-ts.wake:
		case <-tick.C:
		}
	}
}

// reconcile runs once per tenant start: it counts screen gaps (content the ledger knows of that
// the store lost) and screens blobs that were promoted without a screens row (a crash between the
// two). done is false when the scorer was unreachable and the blobs need another try.
func (s *Server) reconcile(ts *tenantState) (done, unreachable bool) {
	ctx := context.Background()
	if n, err := ts.t.ScreenGaps(ctx); err == nil {
		ts.gaps.Store(int64(n))
	}
	blobs, err := ts.t.UnscreenedBlobs(ctx)
	if err != nil {
		return false, false
	}
	for _, h := range blobs {
		if err := s.screen(ctx, ts.t, h); err != nil {
			fmt.Fprintf(os.Stderr, "workflow serve: unscreened blob %s: %v\n", h, err)
			if errors.Is(err, scorer.ErrUnreachable) {
				return false, true
			}
		}
	}
	return true, false
}

// drainPending applies the screen step to everything pending, in order. A failure leaves the file
// pending; the next wake or poll retries it. It reports whether the scorer was unreachable, which
// ends the pass.
func (s *Server) drainPending(ts *tenantState) (unreachable bool) {
	hashes, err := ts.t.PendingHashes()
	if err != nil {
		return false
	}
	for _, h := range hashes {
		if err := s.screen(context.Background(), ts.t, h); err != nil {
			fmt.Fprintf(os.Stderr, "workflow serve: pending %s: %v\n", h, err)
			if errors.Is(err, scorer.ErrUnreachable) {
				return true
			}
		}
	}
	return false
}

func (s *Server) tenant(name string) (*tenantState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return nil, store.ErrClosed
	}
	if ts, ok := s.tenants[name]; ok {
		return ts, nil
	}
	t, err := store.Open(filepath.Join(s.cfg.Data, name), store.Options{GroupWindow: s.opts.GroupWindow})
	if err != nil {
		return nil, err
	}
	ts := &tenantState{t: t, wake: make(chan struct{}, 1)}
	s.tenants[name] = ts
	s.startWorkerLocked(ts) // the worker's first pass handles leftover pending files
	return ts, nil
}

// Close stops workers and closes every tenant.
func (s *Server) Close() error {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return nil
	}
	s.closed = true
	close(s.stop)
	s.mu.Unlock()
	s.wg.Wait()
	var first error
	for _, ts := range s.tenants {
		if err := ts.t.Close(); err != nil && first == nil {
			first = err
		}
	}
	return first
}

// Handler returns the HTTP handler.
func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/health", s.method(http.MethodGet, s.health))
	mux.HandleFunc("/v1/ingest", s.method(http.MethodPost, s.auth(s.ingest)))
	mux.HandleFunc("/v1/artifacts", s.method(http.MethodGet, s.auth(s.artifacts)))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 404, map[string]string{"error": "not found"})
	})
	return mux
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(v)
}

func (s *Server) method(m string, h http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != m {
			w.Header().Set("Allow", m)
			writeJSON(w, 405, map[string]string{"error": "method not allowed"})
			return
		}
		h(w, r)
	}
}

// tenantFor compares the bearer token against every key with no early exit.
func (s *Server) tenantFor(r *http.Request) (string, bool) {
	h := r.Header.Get("Authorization")
	tok, ok := strings.CutPrefix(h, "Bearer ")
	if !ok {
		tok = ""
	}
	found, match := "", 0
	for _, kp := range s.cfg.Keys {
		eq := subtle.ConstantTimeCompare([]byte(tok), []byte(kp.Key))
		if eq == 1 {
			found = kp.Tenant
		}
		match |= eq
	}
	return found, ok && match == 1
}

type tenantHandler func(w http.ResponseWriter, r *http.Request, name string, ts *tenantState)

func (s *Server) auth(h tenantHandler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		name, ok := s.tenantFor(r)
		if !ok {
			writeJSON(w, 401, map[string]string{"error": "unauthorized"})
			return
		}
		ts, err := s.tenant(name)
		if err != nil {
			writeJSON(w, 503, map[string]string{"error": "tenant unavailable"})
			return
		}
		h(w, r, name, ts)
	}
}

func (s *Server) health(w http.ResponseWriter, r *http.Request) {
	s.mu.Lock()
	var list []*tenantState
	for _, ts := range s.tenants {
		list = append(list, ts)
	}
	s.mu.Unlock()
	n, gaps := 0, 0
	for _, ts := range list {
		gaps += int(ts.gaps.Load())
		if h, err := ts.t.PendingHashes(); err == nil {
			n += len(h)
		}
	}
	writeJSON(w, 200, map[string]any{"ok": true, "version": s.opts.Version, "pending": n, "screen_gaps": gaps})
}

func (s *Server) ingest(w http.ResponseWriter, r *http.Request, _ string, ts *tenantState) {
	r.Body = http.MaxBytesReader(w, r.Body, maxBody)
	var req struct {
		Facts *[]json.RawMessage `json:"facts"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		var mbe *http.MaxBytesError
		if errors.As(err, &mbe) {
			writeJSON(w, 413, map[string]string{"error": "request too large"})
			return
		}
		writeJSON(w, 400, map[string]string{"error": "body is not a facts batch"})
		return
	}
	if req.Facts == nil {
		writeJSON(w, 400, map[string]string{"error": "body is not a facts batch"})
		return
	}
	res, err := ingest.Ingest(r.Context(), ts.t, *req.Facts)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "ingest failed"})
		return
	}
	if res == nil {
		res = []ingest.Result{}
	}
	select {
	case ts.wake <- struct{}{}:
	default:
	}
	writeJSON(w, 200, map[string]any{"results": res})
}

func (s *Server) artifacts(w http.ResponseWriter, r *http.Request, _ string, ts *tenantState) {
	repo, path := r.URL.Query().Get("repo_id"), r.URL.Query().Get("path")
	if repo == "" || path == "" {
		writeJSON(w, 400, map[string]string{"error": "repo_id and path are required"})
		return
	}
	a, err := ts.t.Artifact(r.Context(), repo, path)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "read failed"})
		return
	}
	if a == nil {
		writeJSON(w, 404, map[string]string{"error": "not found"})
		return
	}
	var screen any
	if sc := a.Latest.Screen; sc != nil {
		screen = map[string]any{"verdict": sc.Verdict, "scorer": sc.Scorer, "at": sc.At.UTC().Format(time.RFC3339)}
	}
	scores := []map[string]any{}
	for _, sc := range a.Latest.Scores {
		scores = append(scores, map[string]any{"check": sc.Check, "score": sc.Score})
	}
	writeJSON(w, 200, map[string]any{"repo_id": a.RepoID, "path": a.Path, "kind": keys.Kind(a.Path), "versions": a.Versions,
		"latest": map[string]any{"content_hash": a.Latest.ContentHash, "received_at": a.Latest.ReceivedAt.UTC().Format(time.RFC3339),
			"conversation_id": a.Latest.ConversationID, "source": a.Latest.Source, "screen": screen, "scores": scores}})
}
