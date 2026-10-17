//go:build !linux

package serve

import "context"

// watchQueue is a no-op off Linux: the drain's poll covers the queue. kqueue on macOS is deferred
// to phase 5.
func watchQueue(ctx context.Context, dir string, wake chan<- struct{}) {}
