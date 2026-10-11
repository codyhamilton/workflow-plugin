// Package compact rewrites an existing ledger to the Phase 1 shape in resumable batches. In one
// pass over existing hook facts it archives each body, applies the event policy (removing and
// collapsing), strips the payload and fills the analytics columns, so that history and new ingest
// agree. It is offline: the tenant must be opened with store.OpenExclusive. It neither vacuums nor
// parses flags; the caller does that.
package compact

import (
	"errors"
	"os"
	"path/filepath"
	"syscall"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

// minFinalDB and walHeadroom bound the estimate NeedBytes makes for the compacted database and the
// WAL that VACUUM needs.
const (
	minFinalDB  = 64 << 20  // 64 MiB
	walHeadroom = 256 << 20 // 256 MiB
)

// FreeBytes reports the bytes available to unprivileged processes on the filesystem holding dir.
// It is a package variable so tests can substitute a deterministic value.
var FreeBytes = func(dir string) (uint64, error) {
	var st syscall.Statfs_t
	if err := syscall.Statfs(dir, &st); err != nil {
		return 0, err
	}
	return uint64(st.Bavail) * uint64(st.Bsize), nil
}

// NeedBytes estimates the free space a compaction of t needs in the tenant directory: a third of
// the hook payload for the archive, the database size after the payload is dropped (never below
// minFinalDB), and WAL headroom. t must be opened with store.OpenExclusive.
func NeedBytes(t *store.Tenant) (uint64, error) {
	db := t.Raw()
	if db == nil {
		return 0, errors.New("compact: tenant must be opened with store.OpenExclusive")
	}
	var hookRaw int64
	if err := db.QueryRow(
		`SELECT COALESCE(SUM(length(raw)),0) FROM facts WHERE type='hook_event'`).Scan(&hookRaw); err != nil {
		return 0, err
	}
	if hookRaw < 0 {
		hookRaw = 0
	}
	var dbSize uint64
	switch fi, err := os.Stat(filepath.Join(t.Dir(), "ledger.db")); {
	case err == nil:
		dbSize = uint64(fi.Size())
	case errors.Is(err, os.ErrNotExist):
	default:
		return 0, err
	}
	archive := uint64(hookRaw) / 3
	final := uint64(minFinalDB)
	if dbSize > uint64(hookRaw) && dbSize-uint64(hookRaw) > final {
		final = dbSize - uint64(hookRaw)
	}
	return archive + final + uint64(walHeadroom), nil
}
