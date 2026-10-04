// Package drain is the one-per-user queue drain of design 2: it holds an exclusive flock on
// <queue>/.drain.lock for its lifetime, waits a batch window after the first file appears, turns the
// queue's *.evt files into facts (package facts), delivers them through a Sink, deletes or rejects each
// file by its worst fact, backs off on an unreachable remote without losing anything, and exits when
// idle without stranding a file (release the lock, rescan, retake or exit).
//
// Queue layout (fixed here; the MCP shim reads it): only *.evt directly in the queue dir are work;
// tmp/ and rejected/ live inside it with mode 0700. A rejected file moves to rejected/<same name> and its
// reasons go to rejected/<same name>.reason, one line per reason, "<fact id or file name>: <reason>".
//
// Run is the loop. Standalone (RunStandalone, behind `workflow drain`) builds its sink from a fresh
// clientconfig.Load before every batch; serve hosts Run with Options.Hosted and an in-process Sink.
//
// Test-only environment for the standalone binary, as Go duration strings: WORKFLOW_DRAIN_WINDOW,
// WORKFLOW_DRAIN_LINGER, WORKFLOW_DRAIN_BACKOFF_MAX, WORKFLOW_DRAIN_GIVEUP. WORKFLOW_QUEUE sets the
// queue directory.
package drain

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/rand"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/facts"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
)

// Why Run returned.
const (
	ReasonIdle     = "idle"
	ReasonLockHeld = "lock held by another drain"
	ReasonNoConfig = "no client config"
	ReasonGaveUp   = "backoff at cap and no new file"
	ReasonStopped  = "stopped"
)

const (
	maxFiles = 500
	maxBytes = 8 << 20
)

// Response is what a Sink got back for one request.
type Response struct {
	Status     int
	RetryAfter time.Duration
	Results    []ingest.Result
}

// Sink delivers facts to an ingest endpoint. A non-nil error means no response (network error).
type Sink interface {
	Send(ctx context.Context, facts []json.RawMessage) (Response, error)
}

// SinkFunc builds the sink for the next batch, so config changes need no restart. It may return
// clientconfig.ErrNoConfig.
type SinkFunc func() (Sink, error)

// Options configure Run. Zero durations take the design defaults.
type Options struct {
	Dir        string        // queue dir (default QueueDir())
	Sink       SinkFunc      // required
	Window     time.Duration // batch window, default 1.5s
	Linger     time.Duration // empty-queue linger, default 60s
	BackoffMax time.Duration // default 5m
	BackoffMin time.Duration // first backoff step, default 500ms (at most BackoffMax)
	GiveUp     time.Duration // default 15m
	Poll       time.Duration // queue listing interval while waiting, default 250ms
	LockWait   time.Duration // blocking wait for the lock, default 1s
	Wake       <-chan struct{}
	// Hosted: never exit on linger or give-up, run until ctx ends, retry the lock every Poll.
	Hosted bool
	Log    io.Writer // default io.Discard

	afterRelease func() // test hook: runs between lock release and rescan
}

// QueueDir is $WORKFLOW_QUEUE, else ~/.local/share/workflow/queue.
func QueueDir() string {
	if d := os.Getenv("WORKFLOW_QUEUE"); d != "" {
		return d
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".local", "share", "workflow", "queue")
}

func (o *Options) defaults() {
	if o.Dir == "" {
		o.Dir = QueueDir()
	}
	def := func(d *time.Duration, v time.Duration) {
		if *d <= 0 {
			*d = v
		}
	}
	def(&o.Window, 1500*time.Millisecond)
	def(&o.Linger, 60*time.Second)
	def(&o.BackoffMax, 5*time.Minute)
	def(&o.BackoffMin, 500*time.Millisecond)
	def(&o.GiveUp, 15*time.Minute)
	def(&o.Poll, 250*time.Millisecond)
	def(&o.LockWait, time.Second)
	if o.BackoffMin > o.BackoffMax {
		o.BackoffMin = o.BackoffMax
	}
	if o.Log == nil {
		o.Log = io.Discard
	}
}

// EnsureDirs creates the queue dir with tmp/ and rejected/ (mode 0700).
func EnsureDirs(dir string) error {
	for _, d := range []string{dir, filepath.Join(dir, "tmp"), filepath.Join(dir, "rejected")} {
		if err := os.MkdirAll(d, 0o700); err != nil {
			return err
		}
	}
	return nil
}

func lockPath(dir string) string { return filepath.Join(dir, ".drain.lock") }

func tryLock(dir string) (*os.File, error) {
	f, err := os.OpenFile(lockPath(dir), os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return nil, err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		f.Close()
		return nil, err
	}
	return f, nil
}

// acquire waits up to wait for the lock (a hook's probe holds it for an instant); with retry it keeps
// trying every poll until ctx ends.
func acquire(ctx context.Context, dir string, wait, poll time.Duration, forever bool) (*os.File, error) {
	deadline := time.Now().Add(wait)
	step := 20 * time.Millisecond
	if forever {
		step = poll
	}
	for {
		f, err := tryLock(dir)
		if err == nil {
			return f, nil
		}
		if !errors.Is(err, syscall.EWOULDBLOCK) {
			return nil, err
		}
		if !forever && time.Now().After(deadline) {
			return nil, err
		}
		if !sleep(ctx, step) {
			return nil, ctx.Err()
		}
	}
}

func release(f *os.File) {
	if f != nil {
		syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
		f.Close()
	}
}

// Running reports whether a drain holds the lock, probing with a non-blocking flock that it releases.
func Running(dir string) bool {
	f, err := os.OpenFile(lockPath(dir), os.O_RDWR, 0)
	if err != nil {
		return false
	}
	defer f.Close()
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		return errors.Is(err, syscall.EWOULDBLOCK)
	}
	syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
	return false
}

func sleep(ctx context.Context, d time.Duration) bool {
	if d <= 0 {
		return ctx.Err() == nil
	}
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-ctx.Done():
		return false
	case <-t.C:
		return true
	}
}

type entry struct {
	name string
	mod  time.Time
}

func list(dir string) []entry {
	des, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var out []entry
	for _, de := range des {
		n := de.Name()
		if de.IsDir() || strings.HasPrefix(n, ".") || !strings.HasSuffix(n, ".evt") {
			continue
		}
		if info, err := de.Info(); err == nil && info.Mode().IsRegular() {
			out = append(out, entry{n, info.ModTime()})
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if !out[i].mod.Equal(out[j].mod) {
			return out[i].mod.Before(out[j].mod)
		}
		return out[i].name < out[j].name
	})
	return out
}

type runner struct {
	o       Options
	seen    map[string]bool
	lastNew time.Time
}

func (r *runner) logf(format string, a ...any) { fmt.Fprintf(r.o.Log, "drain: "+format+"\n", a...) }

// scan lists the queue and records when a file last newly appeared.
func (r *runner) scan() []entry {
	es := list(r.o.Dir)
	cur := make(map[string]bool, len(es))
	for _, e := range es {
		cur[e.name] = true
		if !r.seen[e.name] {
			r.lastNew = time.Now()
		}
	}
	r.seen = cur
	return es
}

// Run drains the queue until idle (or ctx ends, or always when Hosted). It returns why it stopped.
func Run(ctx context.Context, o Options) (string, error) {
	o.defaults()
	if o.Sink == nil {
		return "", errors.New("drain: no sink")
	}
	if err := EnsureDirs(o.Dir); err != nil {
		return "", err
	}
	r := &runner{o: o, seen: map[string]bool{}, lastNew: time.Now()}
	if !o.Hosted {
		if _, err := o.Sink(); errors.Is(err, clientconfig.ErrNoConfig) {
			return ReasonNoConfig, nil
		}
	}
	lock, err := acquire(ctx, o.Dir, o.LockWait, o.Poll, o.Hosted)
	if err != nil {
		if ctx.Err() != nil {
			return ReasonStopped, nil
		}
		if errors.Is(err, syscall.EWOULDBLOCK) {
			return ReasonLockHeld, nil
		}
		return "", err
	}
	defer func() { release(lock) }()
	r.logf("acquired lock pid=%d", os.Getpid())

	fresh := true // the queue was empty (or we just started): the batch window applies
	var backoff time.Duration
	for {
		if ctx.Err() != nil {
			return ReasonStopped, nil
		}
		files := r.scan()
		if len(files) == 0 {
			fresh = true
			backoff = 0
			if !r.waitForWork(ctx) {
				if ctx.Err() != nil {
					return ReasonStopped, nil
				}
				// linger elapsed: release, rescan, retake if files exist
				release(lock)
				lock = nil
				if o.afterRelease != nil {
					o.afterRelease()
				}
				if len(r.scan()) == 0 {
					return ReasonIdle, nil
				}
				lock, err = acquire(ctx, o.Dir, o.LockWait, o.Poll, false)
				if err != nil {
					if ctx.Err() != nil {
						return ReasonStopped, nil
					}
					return ReasonLockHeld, nil
				}
				r.logf("acquired lock pid=%d", os.Getpid())
			}
			continue
		}
		if fresh {
			fresh = false
			if !sleep(ctx, o.Window) {
				return ReasonStopped, nil
			}
			files = r.scan()
		}
		sink, err := o.Sink()
		if err != nil {
			if errors.Is(err, clientconfig.ErrNoConfig) && !o.Hosted {
				return ReasonNoConfig, nil
			}
			r.logf("config unavailable; retrying")
			if !sleep(ctx, max(o.Poll, time.Second)) {
				return ReasonStopped, nil
			}
			continue
		}
		if len(files) > maxFiles {
			files = files[:maxFiles]
		}
		res := r.batch(ctx, sink, files)
		if !res.retry {
			backoff = 0
			continue
		}
		wait := res.wait
		if wait <= 0 {
			if backoff == 0 {
				backoff = o.BackoffMin
			} else {
				backoff = min(backoff*2, o.BackoffMax)
			}
			wait = backoff/2 + time.Duration(rand.Int63n(int64(backoff/2)+1))
		}
		r.scan()
		if !o.Hosted && backoff >= o.BackoffMax && time.Since(r.lastNew) >= o.GiveUp {
			return ReasonGaveUp, nil
		}
		if !sleep(ctx, wait) {
			return ReasonStopped, nil
		}
	}
}

// waitForWork blocks until a file is listed (true), the linger elapses (false, non-hosted) or ctx ends (false).
func (r *runner) waitForWork(ctx context.Context) bool {
	var linger <-chan time.Time
	if !r.o.Hosted {
		t := time.NewTimer(r.o.Linger)
		defer t.Stop()
		linger = t.C
	}
	tick := time.NewTicker(r.o.Poll)
	defer tick.Stop()
	for {
		select {
		case <-ctx.Done():
			return false
		case <-linger:
			return false
		case <-tick.C:
		case <-r.o.Wake:
		}
		if len(r.scan()) > 0 {
			return true
		}
	}
}

type item struct {
	name    string
	facts   []json.RawMessage
	reasons []string // from facts.Build
}

type result struct {
	retry bool
	wait  time.Duration // explicit wait (429); zero means backoff
}

func (r *runner) batch(ctx context.Context, sink Sink, files []entry) result {
	var in []facts.File
	for _, e := range files {
		data, err := os.ReadFile(filepath.Join(r.o.Dir, e.name))
		if err != nil {
			continue // gone (another process) or unreadable
		}
		in = append(in, facts.File{Name: e.name, Data: data})
	}
	var items []item
	for _, out := range facts.Build(ctx, in) {
		if len(out.Facts) == 0 {
			if len(out.Reasons) > 0 {
				r.reject(out.Name, prefix(out.Name, out.Reasons))
			} else {
				r.remove(out.Name)
			}
			continue
		}
		items = append(items, item{out.Name, out.Facts, out.Reasons})
	}
	for len(items) > 0 {
		n, size := 0, 0
		for n < len(items) {
			s := 0
			for _, f := range items[n].facts {
				s += len(f)
			}
			if n > 0 && size+s > maxBytes {
				break
			}
			size += s
			n++
		}
		if res := r.send(ctx, sink, items[:n]); res.retry {
			return res
		}
		items = items[n:]
	}
	return result{}
}

func (r *runner) send(ctx context.Context, sink Sink, items []item) result {
	var all []json.RawMessage
	for _, it := range items {
		all = append(all, it.facts...)
	}
	resp, err := sink.Send(ctx, all)
	if err != nil {
		if ctx.Err() == nil {
			r.logf("attempt failed: network error (%d files kept)", len(items))
		}
		return result{retry: true}
	}
	switch {
	case resp.Status == 200:
		return r.apply(items, all, resp)
	case resp.Status == 429:
		r.logf("attempt failed: status=429 retry-after=%s (%d files kept)", resp.RetryAfter, len(items))
		return result{retry: true, wait: max(resp.RetryAfter, time.Millisecond)}
	case resp.Status == 400 || resp.Status == 413:
		if len(items) == 1 {
			r.logf("file rejected: status=%d", resp.Status)
			it := items[0]
			r.reject(it.name, prefix(it.name, append([]string{strconv.Itoa(resp.Status)}, it.reasons...)))
			return result{}
		}
		r.logf("status=%d: splitting %d files", resp.Status, len(items))
		h := len(items) / 2
		if res := r.send(ctx, sink, items[:h]); res.retry {
			return res
		}
		return r.send(ctx, sink, items[h:])
	default: // 5xx, 401, 403, 408, and anything unexpected: keep the files
		r.logf("attempt failed: status=%d (%d files kept)", resp.Status, len(items))
		return result{retry: true}
	}
}

func (r *runner) apply(items []item, all []json.RawMessage, resp Response) result {
	if len(resp.Results) != len(all) {
		r.logf("attempt failed: %d results for %d facts (%d files kept)", len(resp.Results), len(all), len(items))
		return result{retry: true}
	}
	for _, res := range resp.Results {
		if res.Status != "accepted" && res.Status != "duplicate" && res.Status != "rejected" {
			r.logf("attempt failed: unknown result status (%d files kept)", len(items))
			return result{retry: true}
		}
	}
	i := 0
	for _, it := range items {
		var rej []string
		for range it.facts {
			res := resp.Results[i]
			i++
			if res.Status == "rejected" {
				reason := res.Reason
				if reason == "" {
					reason = "rejected"
				}
				rej = append(rej, res.ID+": "+reason)
			}
		}
		rej = append(rej, prefix(it.name, it.reasons)...)
		if len(rej) > 0 {
			r.reject(it.name, rej)
		} else {
			r.remove(it.name)
		}
	}
	return result{}
}

func prefix(name string, reasons []string) []string {
	out := make([]string, len(reasons))
	for i, s := range reasons {
		out[i] = name + ": " + s
	}
	return out
}

func (r *runner) remove(name string) {
	if err := os.Remove(filepath.Join(r.o.Dir, name)); err != nil && !os.IsNotExist(err) {
		r.logf("delete failed: %v", err)
	}
}

func (r *runner) reject(name string, reasons []string) {
	dst := filepath.Join(r.o.Dir, "rejected", name)
	var b strings.Builder
	for _, s := range reasons {
		b.WriteString(strings.NewReplacer("\r", " ", "\n", " ").Replace(s))
		b.WriteByte('\n')
	}
	if err := os.WriteFile(dst+".reason", []byte(b.String()), 0o600); err != nil {
		r.logf("reason write failed: %v", err)
	}
	if err := os.Rename(filepath.Join(r.o.Dir, name), dst); err != nil && !os.IsNotExist(err) {
		r.logf("reject move failed: %v", err)
	}
}
