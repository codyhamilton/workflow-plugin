package drain

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/clientconfig"
)

// RunStandalone is `workflow drain`: exit 0 when idle-exited, lock held by another, no config or stopped.
func RunStandalone(ctx context.Context, stderr io.Writer) int {
	o := Options{Sink: ConfigSink, Log: stderr, Poll: 250 * time.Millisecond}
	for env, dst := range map[string]*time.Duration{
		"WORKFLOW_DRAIN_WINDOW":      &o.Window,
		"WORKFLOW_DRAIN_LINGER":      &o.Linger,
		"WORKFLOW_DRAIN_BACKOFF_MAX": &o.BackoffMax,
		"WORKFLOW_DRAIN_GIVEUP":      &o.GiveUp,
	} {
		if v := os.Getenv(env); v != "" {
			d, err := time.ParseDuration(v)
			if err != nil {
				fmt.Fprintf(stderr, "workflow drain: %s: %v\n", env, err)
				return 2
			}
			*dst = d
		}
	}
	if o.BackoffMax > 0 && o.BackoffMax < 500*time.Millisecond {
		o.BackoffMin = o.BackoffMax
	}
	reason, err := Run(ctx, o)
	if err != nil {
		fmt.Fprintln(stderr, "workflow drain:", err)
		return 1
	}
	fmt.Fprintf(stderr, "drain: exit: %s\n", reason)
	return 0
}

// Status is the queue report of `workflow status`.
type Status struct {
	Dir       string
	Queued    int
	OldestAge time.Duration // -1 when the queue is empty
	Rejected  int
	Running   bool
}

// QueueStatus inspects the queue without creating anything.
func QueueStatus(dir string) Status {
	st := Status{Dir: dir, OldestAge: -1, Running: Running(dir)}
	es := list(dir)
	st.Queued = len(es)
	if len(es) > 0 {
		st.OldestAge = time.Since(es[0].mod)
	}
	if des, err := os.ReadDir(dir + "/rejected"); err == nil {
		for _, de := range des {
			if strings.HasSuffix(de.Name(), ".evt") {
				st.Rejected++
			}
		}
	}
	return st
}

// RunStatus is `workflow status`. Exit 1 only when the endpoint is unreachable and files are queued.
func RunStatus(w io.Writer) int {
	st := QueueStatus(QueueDir())
	fmt.Fprintf(w, "queue: %s\n", st.Dir)
	fmt.Fprintf(w, "queued: %d\n", st.Queued)
	if st.OldestAge < 0 {
		fmt.Fprintln(w, "oldest: -")
	} else {
		fmt.Fprintf(w, "oldest: %d\n", int(st.OldestAge.Seconds()))
	}
	fmt.Fprintf(w, "rejected: %d\n", st.Rejected)
	if st.Running {
		fmt.Fprintln(w, "drain: running")
	} else {
		fmt.Fprintln(w, "drain: not running")
	}
	cfg, err := clientconfig.Load()
	switch {
	case errors.Is(err, clientconfig.ErrNoConfig):
		fmt.Fprintln(w, "config: missing")
		fmt.Fprintln(w, "endpoint: -")
		return 0
	case err != nil:
		fmt.Fprintf(w, "config: %s (invalid)\n", clientconfig.Path())
		fmt.Fprintln(w, "endpoint: -")
		return 0
	}
	fmt.Fprintf(w, "config: %s\n", clientconfig.Path())
	reach := "unreachable"
	c := &http.Client{Timeout: 2 * time.Second}
	if resp, err := c.Get(strings.TrimRight(cfg.Endpoint, "/") + "/v1/health"); err == nil {
		resp.Body.Close()
		if resp.StatusCode/100 == 2 {
			reach = "reachable"
		}
	}
	fmt.Fprintf(w, "endpoint: %s %s\n", cfg.Endpoint, reach)
	if reach == "unreachable" && st.Queued > 0 {
		return 1
	}
	return 0
}
