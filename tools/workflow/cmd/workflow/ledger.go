// Command workflow is the single binary of plan 09: serve, drain, mcp, status. ledger compact is
// the offline, resumable reclaim command of plan 12 Phase 2.
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/compact"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

// newCompactSession returns the context and Options for one compaction run. It is a package
// variable so tests can install a cancellable context and batch hooks.
var newCompactSession = func() (context.Context, context.CancelFunc, compact.Options) {
	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	return ctx, cancel, compact.Options{Progress: os.Stdout}
}

// runLedger dispatches `workflow ledger ...`. Only `compact` exists.
func runLedger(args []string) int {
	if len(args) == 0 || args[0] != "compact" {
		fmt.Fprint(os.Stderr, usage)
		return 2
	}
	fs := flag.NewFlagSet("ledger compact", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	fs.Usage = func() { fmt.Fprint(os.Stderr, usage) }
	var dir string
	fs.StringVar(&dir, "tenant-dir", "", "tenant directory (required)")
	if err := fs.Parse(args[1:]); err != nil || dir == "" || fs.NArg() != 0 {
		if err == nil {
			fmt.Fprint(os.Stderr, usage)
		}
		return 2
	}
	return compactTenant(dir)
}

// compactTenant runs the offline compaction of the tenant at dir and reports rows and bytes before
// and after. It refuses safely (exit 1) when locked, short of space, or interrupted.
func compactTenant(dir string) int {
	tn, err := store.OpenExclusive(dir, store.Options{})
	if err != nil {
		fmt.Fprintln(os.Stderr, "workflow ledger compact:", err)
		return 1
	}
	defer tn.Close()

	start := time.Now()
	before, err := ledgerCounts(tn)
	if err != nil {
		fmt.Fprintln(os.Stderr, "workflow ledger compact:", err)
		return 1
	}
	fmt.Printf("before: %s\n", before)

	complete := tn.CompactionState() == "complete"
	if !complete {
		need, err := compact.NeedBytes(tn)
		if err != nil {
			fmt.Fprintln(os.Stderr, "workflow ledger compact:", err)
			return 1
		}
		free, err := compact.FreeBytes(dir)
		if err != nil {
			fmt.Fprintln(os.Stderr, "workflow ledger compact:", err)
			return 1
		}
		fmt.Printf("space: need %d MiB, have %d MiB\n", need>>20, free>>20)
		if free < need {
			fmt.Fprintf(os.Stderr, "workflow ledger compact: need %d MiB, have %d MiB\n", need>>20, free>>20)
			return 1
		}

		ctx, cancel, opts := newCompactSession()
		_, runErr := compact.Run(ctx, tn, opts)
		interrupted := ctx.Err() != nil &&
			(runErr == nil || errors.Is(runErr, context.Canceled) || errors.Is(runErr, context.DeadlineExceeded))
		cancel()
		if runErr != nil {
			if interrupted {
				fmt.Fprintln(os.Stderr, "workflow ledger compact: interrupted; rerun the same command to resume")
			} else {
				fmt.Fprintln(os.Stderr, "workflow ledger compact:", runErr)
			}
			return 1
		}
	}

	if err := vacuum(tn); err != nil {
		fmt.Fprintln(os.Stderr, "workflow ledger compact:", err)
		return 1
	}

	after, err := ledgerCounts(tn)
	if err != nil {
		fmt.Fprintln(os.Stderr, "workflow ledger compact:", err)
		return 1
	}
	fmt.Printf("after: %s elapsed=%s\n", after, time.Since(start).Round(time.Millisecond))
	return 0
}

func vacuum(tn *store.Tenant) error {
	db := tn.Raw()
	if db == nil {
		return errors.New("compact: tenant must be opened with store.OpenExclusive")
	}
	if _, err := db.Exec(`VACUUM`); err != nil {
		return err
	}
	_, err := db.Exec(`PRAGMA wal_checkpoint(TRUNCATE)`)
	return err
}

// ledgerCounts renders the facts row counts (total and by type) and the bytes of ledger.db,
// ledger.db-wal and the archive directory. Counts and sizes only; never row content.
func ledgerCounts(tn *store.Tenant) (string, error) {
	db := tn.Raw()
	if db == nil {
		return "", errors.New("compact: tenant must be opened with store.OpenExclusive")
	}
	var total int64
	if err := db.QueryRow(`SELECT COUNT(*) FROM facts`).Scan(&total); err != nil {
		return "", err
	}
	rows, err := db.Query(`SELECT type, COUNT(*) FROM facts GROUP BY type ORDER BY type`)
	if err != nil {
		return "", err
	}
	defer rows.Close()
	var parts []string
	for rows.Next() {
		var typ string
		var n int64
		if err := rows.Scan(&typ, &n); err != nil {
			return "", err
		}
		parts = append(parts, fmt.Sprintf("%s:%d", typ, n))
	}
	if err := rows.Err(); err != nil {
		return "", err
	}
	dir := tn.Dir()
	return fmt.Sprintf("rows=%d types=%s ledger.db=%d ledger.db-wal=%d archive=%d",
		total, strings.Join(parts, ","),
		fileSize(filepath.Join(dir, "ledger.db")),
		fileSize(filepath.Join(dir, "ledger.db-wal")),
		dirBytes(filepath.Join(dir, "archive"))), nil
}

func fileSize(path string) int64 {
	fi, err := os.Stat(path)
	if err != nil {
		return 0
	}
	return fi.Size()
}

func dirBytes(root string) int64 {
	var total int64
	_ = filepath.WalkDir(root, func(_ string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		if fi, err := d.Info(); err == nil {
			total += fi.Size()
		}
		return nil
	})
	return total
}
