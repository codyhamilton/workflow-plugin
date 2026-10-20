package serve

import (
	"errors"
	"net"
	"net/http"
	"os"
	"strings"
	"time"
)

// Limits on the device routes. All are judgement values (design: Domain: Device grant).
const (
	deviceCodeRatePerMinute = 10
	deviceLivePerIP         = 5
	deviceLiveTotal         = 1000
	deviceUnknownPerSession = 10
	deviceUnknownWindow     = 10 * time.Minute
	deviceCodeRateWindow    = time.Minute
)

var (
	errDeviceRateLimited = errors.New("rate_limited")
	errDeviceBusy        = errors.New("busy")
)

// deviceLimits holds the effective limits and sliding-window state. Guarded by deviceGrants.mu.
type deviceLimits struct {
	ratePerMinute int
	livePerIP     int
	liveTotal     int
	unknownMax    int
	unknownWindow time.Duration
	codeHits      map[string][]time.Time // client IP -> code request times
	unknownHits   map[string][]time.Time // session ID -> unknown-code attempt times
}

func newDeviceLimits() deviceLimits {
	return deviceLimits{
		ratePerMinute: deviceCodeRatePerMinute,
		livePerIP:     deviceLivePerIP,
		liveTotal:     deviceLiveTotal,
		unknownMax:    deviceUnknownPerSession,
		unknownWindow: deviceUnknownWindow,
		codeHits:      map[string][]time.Time{},
		unknownHits:   map[string][]time.Time{},
	}
}

// recent returns the entries newer than now-window.
func recent(ts []time.Time, now time.Time, window time.Duration) []time.Time {
	i := 0
	for i < len(ts) && !ts[i].After(now.Add(-window)) {
		i++
	}
	return ts[i:]
}

func pruneHits(m map[string][]time.Time, now time.Time, window time.Duration) {
	for k, ts := range m {
		if ts = recent(ts, now, window); len(ts) == 0 {
			delete(m, k)
		} else {
			m[k] = ts
		}
	}
}

// pruneLocked drops expired window entries; called from the grant sweep.
func (l *deviceLimits) pruneLocked(now time.Time) {
	pruneHits(l.codeHits, now, deviceCodeRateWindow)
	pruneHits(l.unknownHits, now, l.unknownWindow)
}

// admitCodeLocked applies rate (429), per-IP live cap (429), then global cap (503). The attempt counts toward the rate window.
func (g *deviceGrants) admitCodeLocked(ip string, now time.Time) error {
	l := &g.limits
	hits := recent(l.codeHits[ip], now, deviceCodeRateWindow)
	limited := len(hits) >= l.ratePerMinute
	l.codeHits[ip] = append(hits, now)
	if limited {
		return errDeviceRateLimited
	}
	live := 0
	for _, gr := range g.byHash {
		if gr.clientIP == ip {
			live++
		}
	}
	if live >= l.livePerIP {
		return errDeviceRateLimited
	}
	if len(g.byHash) >= l.liveTotal {
		return errDeviceBusy
	}
	return nil
}

// deviceClientIP is Fly-Client-IP only when FLY_APP_NAME is set and the header parses, else the connection's remote address.
// X-Forwarded-For is never trusted.
func deviceClientIP(r *http.Request) string {
	if os.Getenv("FLY_APP_NAME") != "" {
		if h := strings.TrimSpace(r.Header.Get("Fly-Client-IP")); h != "" {
			if ip := net.ParseIP(h); ip != nil {
				return ip.String()
			}
		}
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}
