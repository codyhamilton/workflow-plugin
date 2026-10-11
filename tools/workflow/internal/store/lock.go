package store

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"syscall"
)

// ErrLocked is the sentinel for a tenant-directory lock held by another holder: a shared Open is
// refused while compaction holds the exclusive lock, and compaction is refused while any shared
// holder exists. Lock failures wrap it, so callers test with errors.Is.
var ErrLocked = errors.New("store: tenant directory locked")

func lockPath(dir string) string { return filepath.Join(dir, ".lock") }

func lockedErr(dir string) error {
	return fmt.Errorf("%w: %s is locked by compaction or another exclusive holder; wait for `workflow ledger compact` to finish", ErrLocked, dir)
}

// acquireLock opens (creating mode 0600) the tenant's .lock and takes it non-blocking with how
// (LOCK_SH or LOCK_EX). The flock belongs to the returned file description, so a second shared
// acquire in this process succeeds while an exclusive one is refused.
func acquireLock(dir string, how int) (*os.File, error) {
	f, err := os.OpenFile(lockPath(dir), os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return nil, err
	}
	if err := syscall.Flock(int(f.Fd()), how|syscall.LOCK_NB); err != nil {
		f.Close()
		if errors.Is(err, syscall.EWOULDBLOCK) {
			return nil, lockedErr(dir)
		}
		return nil, err
	}
	return f, nil
}

func releaseLock(f *os.File) {
	if f != nil {
		syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
		f.Close()
	}
}

// TrySharedLock takes dir's shared lock and releases it at once. It returns ErrLocked when an
// exclusive holder (compaction) holds the lock. serve.Preflight uses it to refuse to start.
func TrySharedLock(dir string) error {
	f, err := acquireLock(dir, syscall.LOCK_SH)
	if err != nil {
		return err
	}
	releaseLock(f)
	return nil
}
