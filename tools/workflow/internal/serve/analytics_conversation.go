package serve

import "net/http"

// analyticsConversation returns one conversation's timeline and totals (DESIGN.md plan 12). The
// id is required; an id with no facts is a 404. Facts are returned in time order, capped by the
// store, with no bodies.
func (s *Server) analyticsConversation(w http.ResponseWriter, r *http.Request, _ string, ts *tenantState) {
	id := r.URL.Query().Get("id")
	if id == "" {
		errJSON(w, 400, "id required")
		return
	}
	d, ok, err := ts.t.Conversation(r.Context(), id)
	if err != nil {
		readFailed(w)
		return
	}
	if !ok {
		errJSON(w, 404, "conversation not found")
		return
	}
	events := make([]map[string]any, 0, len(d.Events))
	for _, e := range d.Events {
		m := map[string]any{"ts": rfc(e.TS), "type": e.Type, "norm_event": e.NormEvent, "event": e.Event,
			"tool": e.Tool, "model": e.Model, "path": e.Path, "kind": e.Kind, "source": e.Source, "sha": e.SHA}
		if e.Tokens != nil {
			m["tokens"] = map[string]any{"in": e.Tokens.In, "out": e.Tokens.Out, "cache_read": e.Tokens.CacheRead,
				"cache_write": e.Tokens.CacheWrite, "reasoning": e.Tokens.Reasoning}
		}
		if e.CostUSD != nil {
			m["cost_usd"] = *e.CostUSD
		}
		events = append(events, m)
	}
	out := map[string]any{
		"conversation_id": d.ConversationID,
		"harness":         d.Harness,
		"repos":           nz(d.Repos),
		"models":          nz(d.Models),
		"first_ts":        rfc(d.FirstTS),
		"last_ts":         rfc(d.LastTS),
		"totals": map[string]any{
			"model_calls":        d.Totals.ModelCalls,
			"tokens_in":          d.Totals.TokensIn,
			"tokens_out":         d.Totals.TokensOut,
			"tokens_cache_read":  d.Totals.TokensCacheRead,
			"tokens_cache_write": d.Totals.TokensCacheWrite,
			"tokens_reasoning":   d.Totals.TokensReasoning,
			"cost_usd":           d.Totals.CostUSD,
			"unpriced_calls":     d.Totals.UnpricedCalls,
		},
		"events": events,
	}
	if d.Truncated {
		out["truncated"] = true
	}
	writeJSON(w, 200, out)
}
