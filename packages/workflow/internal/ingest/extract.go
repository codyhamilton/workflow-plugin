package ingest

import (
	"encoding/json"
	"strings"
)

func strField(m map[string]any, k string) string {
	s, _ := m[k].(string)
	return s
}

func objField(m map[string]any, k string) map[string]any {
	o, _ := m[k].(map[string]any)
	return o
}

// num reads a JSON number (json.Number, or a float/int from a payload decoded another way).
func num(m map[string]any, k string) (float64, bool) {
	switch x := m[k].(type) {
	case json.Number:
		f, err := x.Float64()
		return f, err == nil
	case float64:
		return x, true
	case int:
		return float64(x), true
	case int64:
		return float64(x), true
	}
	return 0, false
}

func i64(m map[string]any, k string) int64 {
	f, _ := num(m, k)
	return int64(f)
}

// extractClaude reads transcript.assistant_message. It reports whether a usage object was present.
// Token fields are stored as reported. Claude repeats a message_id on a few lines; Derive is
// per fact and cannot dedupe, so read-side dedupe by message_id is the caller's job.
func extractClaude(d *Derived, p map[string]any) bool {
	d.Model = strField(p, "model")
	u := objField(p, "usage")
	if u == nil {
		return false
	}
	d.TokIn = i64(u, "input_tokens")
	d.TokOut = i64(u, "output_tokens")
	d.TokCacheRead = i64(u, "cache_read_input_tokens")
	d.TokCacheWrite = i64(u, "cache_creation_input_tokens")
	d.TokReasoning = i64(objField(u, "output_tokens_details"), "thinking_tokens")
	return true
}

// extractCodex reads transcript.token_count. `usage` is the per-call figure; `total` is
// cumulative and is never read. Codex input_tokens already INCLUDES cached_input_tokens: the
// values are stored as reported and cached input is not subtracted, so cost computation must not
// charge cached input twice.
func extractCodex(d *Derived, p map[string]any) {
	d.Model = strField(p, "model")
	u := objField(p, "usage")
	d.TokIn = i64(u, "input_tokens")
	d.TokOut = i64(u, "output_tokens")
	d.TokCacheRead = i64(u, "cached_input_tokens")
	d.TokCacheWrite = i64(u, "cache_write_input_tokens")
	d.TokReasoning = i64(u, "reasoning_output_tokens")
}

// extractOpenCode reads transcript.assistant_message: model as provider/model (bare modelID when
// providerID is empty), tokens.{input,output,reasoning,cache.read,cache.write}, and cost. A cost
// of 0 (local models report 0) is treated as not reported: CostReported stays nil unless cost > 0.
// It reports whether a tokens object was present.
func extractOpenCode(d *Derived, p map[string]any) bool {
	model := strField(p, "modelID")
	if prov := strField(p, "providerID"); prov != "" && model != "" {
		model = prov + "/" + model
	}
	d.Model = strings.TrimSpace(model)
	if c, ok := num(p, "cost"); ok && c > 0 {
		d.CostReported = &c
	}
	t := objField(p, "tokens")
	if t == nil {
		return false
	}
	d.TokIn = i64(t, "input")
	d.TokOut = i64(t, "output")
	d.TokReasoning = i64(t, "reasoning")
	cache := objField(t, "cache")
	d.TokCacheRead = i64(cache, "read")
	d.TokCacheWrite = i64(cache, "write")
	return true
}
