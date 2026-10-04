package serve

import (
	"context"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/url"
	"sync"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/drain"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
)

// HostOptions configure Host.
type HostOptions struct {
	Bound string        // the address serve is bound to (host:port)
	Queue string        // queue dir; default drain.QueueDir()
	Poll  time.Duration // hosting tick and fallback poll; default 3s
	Log   io.Writer     // default io.Discard
}

// inprocSink calls ingest.Ingest for one tenant, the same function the HTTP handler calls.
type inprocSink struct {
	s  *Server
	ts *tenantState
}

func (k inprocSink) Send(ctx context.Context, facts []json.RawMessage) (drain.Response, error) {
	res, err := ingest.Ingest(ctx, k.ts.t, facts)
	if err != nil {
		return drain.Response{Status: 500}, nil
	}
	if res == nil {
		res = []ingest.Result{}
	}
	select {
	case k.ts.wake <- struct{}{}:
	default:
	}
	return drain.Response{Status: 200, Results: res}, nil
}

func isLoopback(h string) bool {
	return h == "127.0.0.1" || h == "localhost" || h == "::1"
}

func isWildcard(h string) bool { return h == "" || h == "0.0.0.0" || h == "::" }

// pointsHere reports whether endpoint addresses the bound address: same port and the same host, or
// both loopback. A wildcard bind counts as loopback.
func pointsHere(endpoint, bound string) bool {
	u, err := url.Parse(endpoint)
	if err != nil || u.Hostname() == "" {
		return false
	}
	bh, bp, err := net.SplitHostPort(bound)
	if err != nil {
		return false
	}
	port := u.Port()
	if port == "" {
		port = map[string]string{"http": "80", "https": "443"}[u.Scheme]
	}
	if port != bp {
		return false
	}
	h := u.Hostname()
	return h == bh || (isLoopback(h) && (isLoopback(bh) || isWildcard(bh)))
}

// tenantForKey maps a key to its tenant. It compares SHA-256 digests in constant time against
// every key with no early exit, so neither the key's content nor its length shows in the timing.
func (s *Server) tenantForKey(key string) (string, bool) {
	kh := sha256.Sum256([]byte(key))
	found, match := "", 0
	for _, kp := range s.cfg.Keys {
		ph := sha256.Sum256([]byte(kp.Key))
		eq := subtle.ConstantTimeCompare(kh[:], ph[:])
		if eq == 1 {
			found = kp.Tenant
		}
		match |= eq
	}
	return found, match == 1
}

// Host runs until ctx ends. Each tick it loads the client config: when the endpoint is this server
// and the key maps to a tenant it runs the drain in process (holding the queue lock); otherwise it
// stops the hosted drain, releases the lock and leaves the queue alone. It returns after the hosted
// drain has stopped.
func (s *Server) Host(ctx context.Context, o HostOptions) {
	if o.Poll <= 0 {
		o.Poll = 3 * time.Second
	}
	if o.Queue == "" {
		o.Queue = drain.QueueDir()
	}
	if o.Log == nil {
		o.Log = io.Discard
	}
	var (
		cancel  context.CancelFunc
		done    chan struct{}
		running string // tenant being hosted
		lastMsg string
	)
	stop := func() {
		if cancel != nil {
			cancel()
			<-done
			cancel, done, running = nil, nil, ""
		}
	}
	defer stop()
	say := func(msg string) {
		if msg != lastMsg {
			lastMsg = msg
			if msg != "" {
				fmt.Fprintln(o.Log, "serve: "+msg)
			}
		}
	}
	tick := func() {
		cfg, err := clientconfig.Load()
		tenant, ok := "", false
		switch {
		case err != nil:
			say("not hosting the drain: client config unavailable")
		case !pointsHere(cfg.Endpoint, o.Bound):
			say("not hosting the drain: client config endpoint is elsewhere")
		default:
			if tenant, ok = s.tenantForKey(cfg.Key); !ok {
				say("not hosting the drain: client config key maps to no tenant")
			}
		}
		if !ok || (running != "" && running != tenant) {
			stop()
		}
		if !ok || running != "" {
			return
		}
		ts, err := s.tenant(tenant)
		if err != nil {
			say("not hosting the drain: tenant unavailable")
			return
		}
		if err := drain.EnsureDirs(o.Queue); err != nil {
			say("not hosting the drain: queue directory: " + err.Error())
			return
		}
		say("hosting the drain for tenant " + tenant)
		dctx, c := context.WithCancel(ctx)
		wake := make(chan struct{}, 1)
		var wg sync.WaitGroup
		d := make(chan struct{})
		cancel, done, running = c, d, tenant
		wg.Add(1)
		go func() { defer wg.Done(); watchQueue(dctx, o.Queue, wake) }()
		go func() {
			defer close(d)
			defer wg.Wait()
			defer c()
			drain.Run(dctx, drain.Options{
				Dir:    o.Queue,
				Sink:   func() (drain.Sink, error) { return inprocSink{s, ts}, nil },
				Hosted: true,
				Wake:   wake,
				Poll:   o.Poll,
				Log:    o.Log,
			})
		}()
	}
	t := time.NewTicker(o.Poll)
	defer t.Stop()
	for {
		tick()
		select {
		case <-ctx.Done():
			return
		case <-t.C:
		}
	}
}
