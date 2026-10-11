package store

import (
	"bytes"
	"math"
	"os"
	"testing"
)

func near(a, b float64) bool { return math.Abs(a-b) < 1e-12 }

func TestPricingTableMatchesTranscript(t *testing.T) {
	want, err := os.ReadFile("../../../transcript/pricing.json")
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(want, pricingJSON) {
		t.Fatal("pricing_table.json differs from tools/transcript/pricing.json; re-copy it")
	}
}

func TestCostReportedWins(t *testing.T) {
	r := 12.5
	usd, ok := Cost("claude", "kimi-k2.5", Tokens{In: 1000}, &r)
	if !ok || usd != 12.5 {
		t.Fatalf("got %v %v", usd, ok)
	}
	// Reported cost wins even for an unpriced model.
	if usd, ok := Cost("opencode", "nope", Tokens{}, &r); !ok || usd != 12.5 {
		t.Fatalf("got %v %v", usd, ok)
	}
}

func TestCostReportedZeroFallsToTokens(t *testing.T) {
	for _, z := range []float64{0, -1} {
		z := z
		usd, ok := Cost("opencode", "kimi-k2.5", Tokens{In: 1000}, &z)
		if !ok || !near(usd, 0.0006) { // 1000 * 0.6 / 1e6
			t.Fatalf("reported %v: got %v %v", z, usd, ok)
		}
	}
}

func TestCostCodexNoDoubleCharge(t *testing.T) {
	// fresh 600*0.6 + cache 400*0.1 = 400 per million.
	usd, ok := Cost("codex", "kimi-k2.5", Tokens{In: 1000, CacheRead: 400}, nil)
	if !ok || !near(usd, 0.0004) {
		t.Fatalf("got %v %v", usd, ok)
	}
	// Cache read larger than input clamps fresh to 0: 400*0.1 = 40 per million.
	usd, _ = Cost("codex", "kimi-k2.5", Tokens{In: 100, CacheRead: 400}, nil)
	if !near(usd, 0.00004) {
		t.Fatalf("clamp: got %v", usd)
	}
}

func TestCostClaudeNotReduced(t *testing.T) {
	// 1000*0.6 + 400*0.1 + 200*0.6 + 500*3.0 = 600+40+120+1500 = 2260 per million.
	usd, ok := Cost("claude", "kimi-k2.5", Tokens{In: 1000, CacheRead: 400, CacheWrite: 200, Out: 500, Reasoning: 300}, nil)
	if !ok || !near(usd, 0.00226) {
		t.Fatalf("got %v %v", usd, ok)
	}
}

func TestCostPrefixRule(t *testing.T) {
	usd, ok := Cost("opencode", "x/kimi-k2.5", Tokens{In: 1000}, nil)
	if !ok || !near(usd, 0.0006) {
		t.Fatalf("got %v %v", usd, ok)
	}
	if !PricedModel("x/kimi-k2.5") || !PricedModel("kimi-k2.5") {
		t.Fatal("PricedModel should accept exact and prefixed names")
	}
}

func TestCostUnknownModel(t *testing.T) {
	for _, m := range []string{"", "claude-sonnet-5", "a/b/kimi-k2.5", "x/unknown"} {
		if usd, ok := Cost("claude", m, Tokens{In: 1000}, nil); ok || usd != 0 {
			t.Fatalf("%q: got %v %v", m, usd, ok)
		}
		if PricedModel(m) {
			t.Fatalf("%q should not be priced", m)
		}
	}
}
