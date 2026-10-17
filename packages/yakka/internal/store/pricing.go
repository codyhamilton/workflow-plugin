package store

import (
	_ "embed"
	"encoding/json"
	"strings"
)

//go:embed pricing_table.json
var pricingJSON []byte

type rates struct {
	Input      float64 `json:"input"`
	CacheWrite float64 `json:"cache_write"`
	CacheRead  float64 `json:"cache_read"`
	Output     float64 `json:"output"`
}

// pricing maps model name to USD-per-million-token rates, parsed from the embedded copy of
// tools/transcript/pricing.json (the "_meta" key is skipped).
var pricing = loadPricing()

func loadPricing() map[string]rates {
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(pricingJSON, &raw); err != nil {
		panic("store: bad pricing_table.json: " + err.Error())
	}
	out := make(map[string]rates, len(raw))
	for k, v := range raw {
		if k == "_meta" {
			continue
		}
		var r rates
		if err := json.Unmarshal(v, &r); err != nil {
			panic("store: bad pricing entry " + k + ": " + err.Error())
		}
		out[k] = r
	}
	return out
}

// Tokens is one call's token columns as stored.
type Tokens struct{ In, Out, CacheRead, CacheWrite, Reasoning int64 }

func lookupRates(model string) (rates, bool) {
	if model == "" {
		return rates{}, false
	}
	if r, ok := pricing[model]; ok {
		return r, true
	}
	if _, after, found := strings.Cut(model, "/"); found {
		if r, ok := pricing[after]; ok {
			return r, true
		}
	}
	return rates{}, false
}

// PricedModel reports whether model has a price in the embedded table (exact, or the text after
// the first "/").
func PricedModel(model string) bool {
	_, ok := lookupRates(model)
	return ok
}

// Cost returns a call's USD cost. A positive reported cost wins; 0 or negative counts as not
// reported. Otherwise tokens are priced from the table; priced is false when the model is unknown.
// Codex input_tokens include cached input, so cache reads are subtracted from fresh input there.
// Reasoning tokens are inside Out and are not charged separately.
func Cost(harness, model string, tok Tokens, reported *float64) (usd float64, priced bool) {
	if reported != nil && *reported > 0 {
		return *reported, true
	}
	r, ok := lookupRates(model)
	if !ok {
		return 0, false
	}
	fresh := tok.In
	if harness == "codex" {
		fresh = max(tok.In-tok.CacheRead, 0)
	}
	usd = (float64(fresh)*r.Input + float64(tok.CacheRead)*r.CacheRead +
		float64(tok.CacheWrite)*r.CacheWrite + float64(tok.Out)*r.Output) / 1e6
	return usd, true
}
