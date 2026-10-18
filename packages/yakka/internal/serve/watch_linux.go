package serve

import (
	"context"

	"golang.org/x/sys/unix"
)

// watchQueue sends on wake when a file appears in dir (IN_MOVED_TO, IN_CREATE) until ctx ends. If
// inotify is unavailable it returns at once and the drain's poll covers the queue.
func watchQueue(ctx context.Context, dir string, wake chan<- struct{}) {
	fd, err := unix.InotifyInit1(unix.IN_CLOEXEC | unix.IN_NONBLOCK)
	if err != nil {
		return
	}
	defer unix.Close(fd)
	if _, err := unix.InotifyAddWatch(fd, dir, unix.IN_MOVED_TO|unix.IN_CREATE); err != nil {
		return
	}
	buf := make([]byte, 4096)
	for ctx.Err() == nil {
		fds := []unix.PollFd{{Fd: int32(fd), Events: unix.POLLIN}}
		n, err := unix.Poll(fds, 200)
		if err != nil && err != unix.EINTR {
			return
		}
		if n <= 0 {
			continue
		}
		if _, err := unix.Read(fd, buf); err == nil {
			select {
			case wake <- struct{}{}:
			default:
			}
		}
	}
}
