package ingest

import (
	"encoding/json"
	"testing"
)

func TestExtractTotalsPerHarness(t *testing.T) {
	fx := loadPolicyFixture(t)
	type tot struct{ in, out, cr, cw, re int64 }
	got := map[string]tot{}
	seen := map[string]bool{}
	for _, f := range fx.Facts {
		d := Derive(f.Harness, f.Event, f.Payload)
		if d.NormEvent != "usage" {
			continue
		}
		// Derive is per fact; counting a model call once is the caller's job. Claude repeats message_id.
		if f.Harness == "claude" {
			id, _ := f.Payload["message_id"].(string)
			if seen[id] {
				continue
			}
			seen[id] = true
		}
		x := got[f.Harness]
		x.in, x.out, x.cr, x.cw, x.re = x.in+d.TokIn, x.out+d.TokOut, x.cr+d.TokCacheRead, x.cw+d.TokCacheWrite, x.re+d.TokReasoning
		got[f.Harness] = x
	}
	for h, w := range fx.ExpectTotals {
		want := tot{w.TokIn, w.TokOut, w.TokCacheRead, w.TokCacheWr, w.TokReasoning}
		if got[h] != want {
			t.Errorf("%s: got %+v want %+v", h, got[h], want)
		}
	}
}

func TestExtractCodexReadsUsageNotTotal(t *testing.T) {
	p := map[string]any{"model": "m",
		"usage": map[string]any{"input_tokens": json.Number("10"), "cached_input_tokens": json.Number("4")},
		"total": map[string]any{"input_tokens": json.Number("999")}}
	d := Derive("codex", "transcript.token_count", p)
	if d.TokIn != 10 || d.TokCacheRead != 4 || d.NormEvent != "usage" {
		t.Errorf("%+v", d)
	}
}

func TestExtractOpenCodeCost(t *testing.T) {
	mk := func(c any) map[string]any {
		return map[string]any{"modelID": "m", "providerID": "p", "cost": c, "tokens": map[string]any{}}
	}
	if Derive("opencode", "transcript.assistant_message", mk(json.Number("0"))).CostReported != nil {
		t.Error("zero cost is not reported")
	}
	if c := Derive("opencode", "transcript.assistant_message", mk(json.Number("0.25"))).CostReported; c == nil || *c != 0.25 {
		t.Errorf("cost %v", c)
	}
	if Derive("opencode", "transcript.assistant_message", mk("x")).CostReported != nil {
		t.Error("mistyped cost")
	}
	if Derive("cursor", "afterAgentResponse", map[string]any{"model": "x"}).Model != "" {
		t.Error("cursor extracts nothing")
	}
}
