package serve

import (
	"crypto/rand"
	"strings"
	"sync"
	"time"
)

const (
	deviceUserCodeAlphabet = "BCDFGHJKLMNPQRSTVWXZ"
	deviceGrantTTL         = 600 * time.Second
	deviceBaseInterval     = 5 * time.Second
	deviceSlowDownStep     = 5 * time.Second
)

type grantStatus int

const (
	grantPending grantStatus = iota
	grantApproved
	grantDenied
)

// deviceGrant is one pending device authorization. It lives in memory only and never holds a token.
type deviceGrant struct {
	userCode  string // normalised
	status    grantStatus
	tenant    string
	scope     string
	expiresAt time.Time // chosen token expiry, set on approval
	githubID  int64
	expiry    time.Time // grant expiry
	clientIP  string
	lastPoll  time.Time
	interval  time.Duration
}

// deviceGrants is the in-memory grant table, keyed by the SHA-256 of device_code and by user code.
type deviceGrants struct {
	mu     sync.Mutex
	now    func() time.Time
	byHash map[string]*deviceGrant
	byUser map[string]*deviceGrant
}

func newDeviceGrants() *deviceGrants {
	return &deviceGrants{now: time.Now, byHash: map[string]*deviceGrant{}, byUser: map[string]*deviceGrant{}}
}

// normaliseUserCode uppercases and strips hyphens and spaces.
func normaliseUserCode(c string) string {
	c = strings.ToUpper(c)
	return strings.NewReplacer("-", "", " ", "").Replace(c)
}

func formatUserCode(n string) string { return n[:4] + "-" + n[4:] }

func generateUserCode() (string, error) {
	// 256 is not a multiple of 20; reject bytes >= 240 so every letter is equally likely.
	const limit = 256 - 256%len(deviceUserCodeAlphabet)
	out := make([]byte, 0, 8)
	var buf [16]byte
	for len(out) < 8 {
		if _, err := rand.Read(buf[:]); err != nil {
			return "", err
		}
		for _, b := range buf {
			if int(b) >= limit {
				continue
			}
			out = append(out, deviceUserCodeAlphabet[int(b)%len(deviceUserCodeAlphabet)])
			if len(out) == 8 {
				break
			}
		}
	}
	return string(out), nil
}

// sweepLocked drops grants past expiry. Called at the start of every device route; there is no background loop.
func (g *deviceGrants) sweepLocked(now time.Time) {
	for h, gr := range g.byHash {
		if !now.Before(gr.expiry) {
			delete(g.byHash, h)
			delete(g.byUser, gr.userCode)
		}
	}
}

func (g *deviceGrants) dropLocked(hash string, gr *deviceGrant) {
	delete(g.byHash, hash)
	delete(g.byUser, gr.userCode)
}

// create adds a pending grant for deviceCode and returns its formatted user code.
func (g *deviceGrants) create(deviceCode, clientIP string) (string, error) {
	g.mu.Lock()
	defer g.mu.Unlock()
	now := g.now()
	g.sweepLocked(now)
	var norm string
	for {
		c, err := generateUserCode()
		if err != nil {
			return "", err
		}
		if _, taken := g.byUser[c]; !taken {
			norm = c
			break
		}
	}
	gr := &deviceGrant{userCode: norm, clientIP: clientIP, expiry: now.Add(deviceGrantTTL), interval: deviceBaseInterval}
	g.byHash[hashDeviceCode(deviceCode)] = gr
	g.byUser[norm] = gr
	return formatUserCode(norm), nil
}

// decide sweeps, then runs under the table lock with that grant; it is not called for an unknown, expired or decided code.
func (g *deviceGrants) decide(userCode string, decide func(gr *deviceGrant) error) (found bool, err error) {
	g.mu.Lock()
	defer g.mu.Unlock()
	now := g.now()
	g.sweepLocked(now)
	gr := g.byUser[normaliseUserCode(userCode)]
	if gr == nil || gr.status != grantPending {
		return false, nil
	}
	return true, decide(gr)
}

type pollResult int

const (
	pollUnknown pollResult = iota
	pollSlowDown
	pollPending
	pollDenied
	pollApproved
)

// poll applies the poll-rate rule and reports the grant's state. On pollDenied the grant is dropped.
// On pollApproved the grant is dropped too and returned for the caller to mint from.
func (g *deviceGrants) poll(deviceCode string) (pollResult, deviceGrant) {
	g.mu.Lock()
	defer g.mu.Unlock()
	now := g.now()
	g.sweepLocked(now)
	h := hashDeviceCode(deviceCode)
	gr := g.byHash[h]
	if gr == nil {
		return pollUnknown, deviceGrant{}
	}
	tooSoon := !gr.lastPoll.IsZero() && now.Sub(gr.lastPoll) < gr.interval
	if tooSoon {
		gr.interval += deviceSlowDownStep
	}
	gr.lastPoll = now
	if tooSoon {
		return pollSlowDown, *gr
	}
	switch gr.status {
	case grantDenied:
		g.dropLocked(h, gr)
		return pollDenied, *gr
	case grantApproved:
		g.dropLocked(h, gr) // claimed here, under the lock, so a grant yields at most one token
		return pollApproved, *gr
	}
	return pollPending, *gr
}

// sweep drops expired grants; device routes that do not otherwise touch the table call it first.
func (g *deviceGrants) sweep() {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.sweepLocked(g.now())
}
