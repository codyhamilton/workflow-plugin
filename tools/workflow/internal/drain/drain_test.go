package drain

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
)

func spoolFile(t testing.TB, dir, name string) {
	t.Helper()
	conv := strings.SplitN(name, "-", 2)[0]
	body := fmt.Sprintf("{\"ts\":1.5,\"harness\":\"claude\",\"event\":\"Stop\"}\n{\"hook_event_name\":\"Stop\",\"session_id\":%q}", conv)
	if err := os.MkdirAll(filepath.Join(dir, "tmp"), 0o700); err != nil {
		t.Fatal(err)
	}
	tmp := filepath.Join(dir, "tmp", name)
	if err := os.WriteFile(tmp, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Rename(tmp, filepath.Join(dir, name+".evt")); err != nil {
		t.Fatal(err)
	}
}

func count(dir, suffix string) int {
	des, _ := os.ReadDir(dir)
	n := 0
	for _, de := range des {
		if strings.HasSuffix(de.Name(), suffix) {
			n++
		}
	}
	return n
}

type call struct {
	at    time.Time
	n     int // facts
	auth  string
	seqNo int
}

// fake is an ingest endpoint whose behaviour is a function of the call.
type fake struct {
	mu    sync.Mutex
	calls []call
	h     func(c call, w http.ResponseWriter, ids []string) bool // true: handled
}

func (f *fake) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Facts []struct {
			ID string `json:"id"`
		} `json:"facts"`
	}
	json.NewDecoder(r.Body).Decode(&req)
	ids := make([]string, len(req.Facts))
	for i, x := range req.Facts {
		ids[i] = x.ID
	}
	f.mu.Lock()
	c := call{at: time.Now(), n: len(ids), auth: r.Header.Get("Authorization"), seqNo: len(f.calls)}
	f.calls = append(f.calls, c)
	f.mu.Unlock()
	if f.h != nil && f.h(c, w, ids) {
		return
	}
	ok(w, ids, nil)
}

func ok(w http.ResponseWriter, ids []string, rej map[string]string) {
	res := []ingest.Result{}
	for _, id := range ids {
		if r, bad := rej[id]; bad {
			res = append(res, ingest.Result{ID: id, Status: "rejected", Reason: r})
		} else {
			res = append(res, ingest.Result{ID: id, Status: "accepted"})
		}
	}
	json.NewEncoder(w).Encode(map[string]any{"results": res})
}

func (f *fake) n() int { f.mu.Lock(); defer f.mu.Unlock(); return len(f.calls) }

func opts(dir, url string) Options {
	return Options{
		Dir: dir, Window: 30 * time.Millisecond, Linger: 150 * time.Millisecond, Poll: 10 * time.Millisecond,
		BackoffMin: 40 * time.Millisecond, BackoffMax: 400 * time.Millisecond, GiveUp: time.Hour,
		Sink: func() (Sink, error) { return &HTTPSink{Endpoint: url, Key: "k"}, nil },
	}
}

func run(t *testing.T, o Options) string {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	reason, err := Run(ctx, o)
	if err != nil {
		t.Fatal(err)
	}
	return reason
}

func TestDeliveryResults(t *testing.T) {
	dir := t.TempDir()
	for _, n := range []string{"a-1", "b-2", "c-3"} {
		spoolFile(t, dir, n)
	}
	srv := httptest.NewServer(&fake{h: func(c call, w http.ResponseWriter, ids []string) bool {
		ok(w, ids, map[string]string{"b-2.evt#0": "payload.x looks like a secret"})
		return true
	}})
	defer srv.Close()
	if r := run(t, opts(dir, srv.URL)); r != ReasonIdle {
		t.Fatal(r)
	}
	if count(dir, ".evt") != 0 || count(filepath.Join(dir, "rejected"), ".evt") != 1 {
		t.Fatalf("queue %d rejected %d", count(dir, ".evt"), count(filepath.Join(dir, "rejected"), ".evt"))
	}
	b, err := os.ReadFile(filepath.Join(dir, "rejected", "b-2.evt.reason"))
	if err != nil || string(b) != "b-2.evt#0: payload.x looks like a secret\n" {
		t.Fatalf("%q %v", b, err)
	}
}

func TestDeliveryAuthHeader(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	f := &fake{}
	srv := httptest.NewServer(f)
	defer srv.Close()
	run(t, opts(dir, srv.URL))
	if f.calls[0].auth != "Bearer k" {
		t.Fatal(f.calls[0].auth)
	}
}

func TestBackoff503KeepsFiles(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	f := &fake{h: func(c call, w http.ResponseWriter, ids []string) bool {
		if c.seqNo < 4 {
			w.WriteHeader(503)
			return true
		}
		return false
	}}
	srv := httptest.NewServer(f)
	defer srv.Close()
	if r := run(t, opts(dir, srv.URL)); r != ReasonIdle {
		t.Fatal(r)
	}
	if f.n() != 5 || count(dir, ".evt") != 0 {
		t.Fatalf("calls %d left %d", f.n(), count(dir, ".evt"))
	}
	g1 := f.calls[1].at.Sub(f.calls[0].at)
	g3 := f.calls[3].at.Sub(f.calls[2].at)
	if g3 <= g1 {
		t.Fatalf("delay did not grow: %v then %v", g1, g3)
	}
}

func TestBackoffDroppedConnection(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	f := &fake{h: func(c call, w http.ResponseWriter, ids []string) bool {
		if c.seqNo < 2 {
			hj, _ := w.(http.Hijacker)
			conn, _, _ := hj.Hijack()
			conn.Close()
			return true
		}
		return false
	}}
	srv := httptest.NewServer(f)
	defer srv.Close()
	if r := run(t, opts(dir, srv.URL)); r != ReasonIdle {
		t.Fatal(r)
	}
	if f.n() != 3 || count(dir, ".evt") != 0 {
		t.Fatalf("calls %d left %d", f.n(), count(dir, ".evt"))
	}
}

func TestBackoffUnauthorizedKeepsFiles(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	srv := httptest.NewServer(&fake{h: func(c call, w http.ResponseWriter, ids []string) bool { w.WriteHeader(401); return true }})
	defer srv.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 700*time.Millisecond)
	defer cancel()
	reason, _ := Run(ctx, opts(dir, srv.URL))
	if reason != ReasonStopped || count(dir, ".evt") != 1 || count(filepath.Join(dir, "rejected"), "") != 0 {
		t.Fatalf("%s left %d", reason, count(dir, ".evt"))
	}
}

func TestBackoffGivesUpAtCap(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	srv := httptest.NewServer(&fake{h: func(c call, w http.ResponseWriter, ids []string) bool { w.WriteHeader(500); return true }})
	defer srv.Close()
	o := opts(dir, srv.URL)
	o.GiveUp = 300 * time.Millisecond
	if r := run(t, o); r != ReasonGaveUp {
		t.Fatal(r)
	}
	if count(dir, ".evt") != 1 {
		t.Fatal("file lost")
	}
}

func TestRetryAfter429(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	f := &fake{h: func(c call, w http.ResponseWriter, ids []string) bool {
		if c.seqNo == 0 {
			w.Header().Set("Retry-After", "1")
			w.WriteHeader(429)
			return true
		}
		return false
	}}
	srv := httptest.NewServer(f)
	defer srv.Close()
	run(t, opts(dir, srv.URL))
	if f.n() != 2 || count(dir, ".evt") != 0 {
		t.Fatalf("calls %d", f.n())
	}
	if d := f.calls[1].at.Sub(f.calls[0].at); d < 950*time.Millisecond || d > 1600*time.Millisecond {
		t.Fatalf("waited %v", d)
	}
}

func TestSplit413(t *testing.T) {
	dir := t.TempDir()
	for _, n := range []string{"a-1", "b-2", "c-3", "d-4"} {
		spoolFile(t, dir, n)
	}
	f := &fake{h: func(c call, w http.ResponseWriter, ids []string) bool {
		if len(ids) > 1 {
			w.WriteHeader(413)
			return true
		}
		return false
	}}
	srv := httptest.NewServer(f)
	defer srv.Close()
	run(t, opts(dir, srv.URL))
	if count(dir, ".evt") != 0 || count(filepath.Join(dir, "rejected"), ".evt") != 0 {
		t.Fatal("split did not deliver everything")
	}
	if f.n() != 1+2+4 {
		t.Fatalf("calls %d", f.n())
	}
}

func TestSplitSingleFileRejected(t *testing.T) {
	dir := t.TempDir()
	for _, n := range []string{"a-1", "b-2", "c-3"} {
		spoolFile(t, dir, n)
	}
	srv := httptest.NewServer(&fake{h: func(c call, w http.ResponseWriter, ids []string) bool {
		for _, id := range ids {
			if strings.HasPrefix(id, "b-2") {
				w.WriteHeader(413)
				return true
			}
		}
		return false
	}})
	defer srv.Close()
	run(t, opts(dir, srv.URL))
	rej := filepath.Join(dir, "rejected")
	if count(dir, ".evt") != 0 || count(rej, ".evt") != 1 {
		t.Fatalf("left %d rejected %d", count(dir, ".evt"), count(rej, ".evt"))
	}
	b, _ := os.ReadFile(filepath.Join(rej, "b-2.evt.reason"))
	if string(b) != "b-2.evt: 413\n" {
		t.Fatalf("%q", b)
	}
}

func TestSplit400SingleFile(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	srv := httptest.NewServer(&fake{h: func(c call, w http.ResponseWriter, ids []string) bool { w.WriteHeader(400); return true }})
	defer srv.Close()
	run(t, opts(dir, srv.URL))
	b, _ := os.ReadFile(filepath.Join(dir, "rejected", "a-1.evt.reason"))
	if string(b) != "a-1.evt: 400\n" {
		t.Fatalf("%q", b)
	}
}

func TestIdleExitRace(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	srv := httptest.NewServer(&fake{})
	defer srv.Close()
	o := opts(dir, srv.URL)
	n := 0
	o.afterRelease = func() {
		if n < 3 { // files spooled between release and rescan
			n++
			spoolFile(t, dir, fmt.Sprintf("r%d-9", n))
		}
	}
	if r := run(t, o); r != ReasonIdle {
		t.Fatal(r)
	}
	if n != 3 || count(dir, ".evt") != 0 {
		t.Fatalf("hook ran %d, left %d", n, count(dir, ".evt"))
	}
}

func TestRaceSecondDrainExits(t *testing.T) {
	dir := t.TempDir()
	srv := httptest.NewServer(&fake{})
	defer srv.Close()
	if err := EnsureDirs(dir); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan string)
	o := opts(dir, srv.URL)
	o.Linger = time.Minute
	go func() { r, _ := Run(ctx, o); done <- r }()
	for i := 0; !Running(dir); i++ {
		if i > 200 {
			t.Fatal("first drain never took the lock")
		}
		time.Sleep(10 * time.Millisecond)
	}
	start := time.Now()
	if r := run(t, opts(dir, srv.URL)); r != ReasonLockHeld {
		t.Fatal(r)
	}
	if d := time.Since(start); d > 2*time.Second {
		t.Fatalf("second drain took %v", d)
	}
	cancel()
	<-done
	if Running(dir) {
		t.Fatal("lock not released")
	}
}

func TestNoConfigExitsUntouched(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	o := opts(dir, "")
	o.Sink = func() (Sink, error) { return nil, clientconfig.ErrNoConfig }
	if r := run(t, o); r != ReasonNoConfig || count(dir, ".evt") != 1 {
		t.Fatal(r)
	}
}

func TestInvalidConfigGivesUp(t *testing.T) {
	dir := t.TempDir()
	spoolFile(t, dir, "a-1")
	o := opts(dir, "")
	o.Sink = func() (Sink, error) { return nil, errors.New("client.toml: bad endpoint") }
	o.GiveUp = 300 * time.Millisecond
	if r := run(t, o); r != ReasonGaveUp || count(dir, ".evt") != 1 {
		t.Fatal(r)
	}
	if Running(dir) {
		t.Fatal("lock not released")
	}
}

func TestHostedRetriesLockAndWakes(t *testing.T) {
	dir := t.TempDir()
	srv := httptest.NewServer(&fake{})
	defer srv.Close()
	hold, err := func() (*os.File, error) { EnsureDirs(dir); return tryLock(dir) }()
	if err != nil {
		t.Fatal(err)
	}
	wake := make(chan struct{}, 1)
	o := opts(dir, srv.URL)
	o.Hosted, o.Wake, o.Linger = true, wake, time.Millisecond
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan string)
	go func() { r, _ := Run(ctx, o); done <- r }()
	time.Sleep(200 * time.Millisecond)
	if Running(dir) != true {
		t.Fatal("expected lock held by test")
	}
	release(hold)
	time.Sleep(300 * time.Millisecond) // hosted drain took the lock and outlives the linger
	spoolFile(t, dir, "a-1")
	wake <- struct{}{}
	for i := 0; count(dir, ".evt") != 0; i++ {
		if i > 300 {
			t.Fatal("never delivered")
		}
		time.Sleep(10 * time.Millisecond)
	}
	cancel()
	if r := <-done; r != ReasonStopped {
		t.Fatal(r)
	}
}

func TestStatusData(t *testing.T) {
	dir := t.TempDir()
	EnsureDirs(dir)
	spoolFile(t, dir, "a-1")
	os.WriteFile(filepath.Join(dir, "rejected", "x.evt"), nil, 0o600)
	os.WriteFile(filepath.Join(dir, "rejected", "x.evt.reason"), nil, 0o600)
	st := QueueStatus(dir)
	if st.Queued != 1 || st.Rejected != 1 || st.Running || st.OldestAge < 0 {
		t.Fatalf("%+v", st)
	}
}
