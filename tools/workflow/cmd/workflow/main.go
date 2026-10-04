// Command workflow is the single binary of plan 09: serve, drain, mcp, status.
package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/drain"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve"
)

// Set with -ldflags -X main.version=… -X main.commit=…
var (
	version = "dev"
	commit  = "unknown"
)

const usage = "usage: workflow serve | drain | mcp | status\n"

func main() { os.Exit(run(os.Args[1:])) }

func run(args []string) int {
	if len(args) == 0 {
		fmt.Fprint(os.Stderr, usage)
		return 2
	}
	switch args[0] {
	case "serve":
		return runServe()
	case "drain":
		ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
		defer stop()
		return drain.RunStandalone(ctx, os.Stderr)
	case "status":
		return drain.RunStatus(os.Stdout)
	case "mcp":
		fmt.Fprintln(os.Stderr, "not implemented yet")
		return 2
	case "version":
		fmt.Printf("workflow %s (%s)\n", version, commit)
		return 0
	}
	fmt.Fprint(os.Stderr, usage)
	return 2
}

func runServe() int {
	cfg, err := serve.ConfigFromEnv(os.Getenv)
	if err != nil {
		fmt.Fprintln(os.Stderr, "workflow serve:", err)
		return 1
	}
	if err := os.MkdirAll(cfg.Data, 0o755); err != nil {
		fmt.Fprintln(os.Stderr, "workflow serve: data directory:", err)
		return 1
	}
	ln, err := net.Listen("tcp", cfg.Addr)
	if err != nil {
		fmt.Fprintln(os.Stderr, "workflow serve:", err)
		return 1
	}
	s := serve.New(cfg, serve.Options{Version: version})
	srv := &http.Server{Handler: s.Handler(), ReadHeaderTimeout: 10 * time.Second}
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()
	errc := make(chan error, 1)
	go func() { errc <- srv.Serve(ln) }()
	hostCtx, hostCancel := context.WithCancel(context.Background())
	hostDone := make(chan struct{})
	var hostPoll time.Duration // WORKFLOW_SERVE_POLL: test-only hosting tick
	if d, err := time.ParseDuration(os.Getenv("WORKFLOW_SERVE_POLL")); err == nil {
		hostPoll = d
	}
	go func() {
		defer close(hostDone)
		s.Host(hostCtx, serve.HostOptions{Bound: ln.Addr().String(), Poll: hostPoll, Log: os.Stderr})
	}()
	fmt.Fprintf(os.Stderr, "workflow serve: listening on %s\n", ln.Addr())
	code := 0
	select {
	case <-ctx.Done():
	case err := <-errc:
		fmt.Fprintln(os.Stderr, "workflow serve:", err)
		code = 1
	}
	hostCancel() // the hosted drain stops and releases the lock before tenants close
	<-hostDone
	sctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(sctx); err != nil && !errors.Is(err, http.ErrServerClosed) {
		fmt.Fprintln(os.Stderr, "workflow serve: shutdown:", err)
	}
	if err := s.Close(); err != nil {
		fmt.Fprintln(os.Stderr, "workflow serve: close:", err)
		code = 1
	}
	return code
}
