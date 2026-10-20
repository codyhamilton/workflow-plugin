package serve

import (
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// codeFrom posts /v1/device/code from the given remote address with optional headers.
func (e *deviceEnv) codeFrom(remote string, hdr map[string]string) (int, string) {
	e.t.Helper()
	req := httptest.NewRequest("POST", "/v1/device/code", nil)
	req.RemoteAddr = remote
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	e.h.ServeHTTP(rec, req)
	return rec.Code, rec.Body.String()
}

func TestDeviceCodeRateLimit(t *testing.T) {
	e := newDeviceEnv(t)
	e.s.grants.limits.livePerIP = 1000
	for i := 0; i < 10; i++ {
		if c, b := e.codeFrom("203.0.113.1:1000", nil); c != 200 {
			t.Fatalf("request %d: %d %s", i+1, c, b)
		}
	}
	c, b := e.codeFrom("203.0.113.1:1000", nil)
	wantErr(t, "eleventh", c, b, 429, "rate_limited")
	if c, b := e.codeFrom("203.0.113.2:1000", nil); c != 200 {
		t.Fatalf("other IP: %d %s", c, b)
	}
	e.advance(61 * time.Second)
	if c, b := e.codeFrom("203.0.113.1:1000", nil); c != 200 {
		t.Fatalf("after window: %d %s", c, b)
	}
}

func TestDeviceCodeLiveCapPerIP(t *testing.T) {
	e := newDeviceEnv(t)
	var first codeResp
	for i := 0; i < 5; i++ {
		r := e.requestCode()
		if i == 0 {
			first = r
		}
	}
	c, b, _ := doWithCookies(t, e.h, "POST", "/v1/device/code", "", "", nil)
	wantErr(t, "sixth", c, b, 429, "rate_limited")
	if c, b := e.authorize(`{"user_code":"` + first.UserCode + `","action":"deny"}`); c != 200 {
		t.Fatalf("deny: %d %s", c, b)
	}
	if c, b := e.poll(first.DeviceCode); c != 400 || !strings.Contains(b, "access_denied") {
		t.Fatalf("poll: %d %s", c, b)
	}
	e.requestCode()
	// Expiry also frees the slots.
	c, b, _ = doWithCookies(t, e.h, "POST", "/v1/device/code", "", "", nil)
	wantErr(t, "full again", c, b, 429, "rate_limited")
	e.advance(deviceGrantTTL + time.Second)
	e.requestCode()
}

func TestDeviceCodeGlobalCap(t *testing.T) {
	e := newDeviceEnv(t)
	e.s.grants.limits.liveTotal = 3
	e.s.grants.limits.livePerIP = 100
	for i, ip := range []string{"203.0.113.1:1", "203.0.113.2:1", "203.0.113.3:1"} {
		if c, b := e.codeFrom(ip, nil); c != 200 {
			t.Fatalf("grant %d: %d %s", i, c, b)
		}
	}
	c, b := e.codeFrom("203.0.113.4:1", nil)
	wantErr(t, "fourth", c, b, 503, "busy")
}

func TestDeviceClientIP(t *testing.T) {
	forge := func(i int) map[string]string {
		return map[string]string{"Fly-Client-IP": "198.51.100." + string(rune('0'+i)), "X-Forwarded-For": "198.51.100.99"}
	}
	t.Run("unset ignores header", func(t *testing.T) {
		t.Setenv("FLY_APP_NAME", "")
		e := newDeviceEnv(t)
		e.s.grants.limits.livePerIP = 1000
		for i := 0; i < 10; i++ {
			if c, b := e.codeFrom("203.0.113.1:1", forge(i)); c != 200 {
				t.Fatalf("request %d: %d %s", i, c, b)
			}
		}
		c, b := e.codeFrom("203.0.113.1:1", forge(1))
		wantErr(t, "eleventh", c, b, 429, "rate_limited")
	})
	t.Run("set uses header", func(t *testing.T) {
		t.Setenv("FLY_APP_NAME", "x")
		e := newDeviceEnv(t)
		e.s.grants.limits.ratePerMinute = 1
		if c, b := e.codeFrom("203.0.113.1:1", map[string]string{"Fly-Client-IP": "198.51.100.1"}); c != 200 {
			t.Fatalf("a: %d %s", c, b)
		}
		if c, b := e.codeFrom("203.0.113.1:1", map[string]string{"Fly-Client-IP": " 198.51.100.2 "}); c != 200 {
			t.Fatalf("b: %d %s", c, b)
		}
		c, b := e.codeFrom("203.0.113.9:1", map[string]string{"Fly-Client-IP": "198.51.100.1", "X-Forwarded-For": "1.2.3.4"})
		wantErr(t, "same header IP", c, b, 429, "rate_limited")
		// Unparseable header falls back to the remote address.
		if c, b := e.codeFrom("203.0.113.5:1", map[string]string{"Fly-Client-IP": "not-an-ip"}); c != 200 {
			t.Fatalf("fallback first: %d %s", c, b)
		}
		c, b = e.codeFrom("203.0.113.5:2", map[string]string{"Fly-Client-IP": "also-bad"})
		wantErr(t, "fallback bucket", c, b, 429, "rate_limited")
	})
}

func TestDeviceAuthorizeUnknownCodeLimit(t *testing.T) {
	e := newDeviceEnv(t)
	bad := `{"user_code":"BBBB-BBBB","action":"deny"}`
	for i := 0; i < 10; i++ {
		c, b := e.authorize(bad)
		wantErr(t, "unknown", c, b, 404, "unknown_code")
	}
	c, b := e.authorize(bad)
	wantErr(t, "eleventh", c, b, 429, "rate_limited")
	// Check order: the limit is checked before the lookup, so a valid code is also refused while limited.
	cr := e.requestCode()
	c, b = e.authorize(`{"user_code":"` + cr.UserCode + `","action":"deny"}`)
	wantErr(t, "valid while limited", c, b, 429, "rate_limited")
	// A second session is unaffected.
	gh2 := loginRemote(t, e.h, e.origin)
	if c, _, _ := doWithCookies(t, e.h, "POST", "/v1/device/authorize", e.origin, bad, gh2); c != 404 {
		t.Fatalf("second session: %d", c)
	}
	e.advance(deviceUnknownWindow + time.Second)
	c, b = e.authorize(bad)
	wantErr(t, "after window", c, b, 404, "unknown_code")
	// The grant expired with the clock jump (TTL 10 min equals the window), so use a fresh one: valid code approves again.
	cr = e.requestCode()
	if c, b := e.authorize(`{"user_code":"` + cr.UserCode + `","action":"deny"}`); c != 200 {
		t.Fatalf("valid after window: %d %s", c, b)
	}
}

func TestDeviceLimiterPrunes(t *testing.T) {
	e := newDeviceEnv(t)
	e.requestCode()
	e.authorize(`{"user_code":"BBBB-BBBB","action":"deny"}`)
	g := e.s.grants
	g.mu.Lock()
	if len(g.limits.codeHits) == 0 || len(g.limits.unknownHits) == 0 {
		g.mu.Unlock()
		t.Fatal("expected limiter state before the window passes")
	}
	g.mu.Unlock()
	e.advance(deviceUnknownWindow + time.Second)
	g.sweep()
	g.mu.Lock()
	defer g.mu.Unlock()
	if len(g.limits.codeHits) != 0 || len(g.limits.unknownHits) != 0 {
		t.Fatalf("maps not empty: %d %d", len(g.limits.codeHits), len(g.limits.unknownHits))
	}
}
