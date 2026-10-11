package compact

import (
	"context"
	"encoding/json"
	"fmt"
	"testing"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

// rollupLedger appends a small hook_event ledger holding removable (opencode Remove-policy) and
// collapsible (opencode message.part.delta) rows as well as kept rows, so compaction both deletes
// and rewrites base rows. Append maintains the rollup, so it starts exact and compaction is what
// would drift it. Returns the hour-aligned base ts.
func rollupLedger(t *testing.T, tn *store.Tenant) int64 {
	t.Helper()
	base := int64(1791072000)
	rows := []store.FactRow{
		hookRow(t, 1, base+60, "opencode", "chat.params", "c1", map[string]any{}),
		hookRow(t, 2, base+120, "claude", "PreToolUse", "c1", map[string]any{"tool_name": "Read"}),
		hookRow(t, 3, base+3600+60, "opencode", "message.part.delta", "c1", delta("m1", "p1", "text")),
		hookRow(t, 4, base+3600+120, "opencode", "message.part.delta", "c1", delta("m1", "p1", "text")),
		hookRow(t, 5, base+7200+60, "claude", "PostToolUse", "c2", map[string]any{"tool_name": "Bash"}),
		hookRow(t, 6, base+7200+120, "opencode", "shell.env", "c2", map[string]any{}),
		hookRow(t, 7, base+60, "claude", "UserPromptSubmit", "c2", map[string]any{}),
	}
	if _, err := tn.Append(context.Background(), rows); err != nil {
		t.Fatalf("append ledger: %v", err)
	}
	return base
}

func delta(messageID, partID, field string) map[string]any {
	return map[string]any{"event": map[string]any{"properties": map[string]any{
		"messageID": messageID, "partID": partID, "field": field}}}
}

func hookRow(t *testing.T, i int, ts int64, harness, event, conv string, payload map[string]any) store.FactRow {
	t.Helper()
	raw, err := json.Marshal(map[string]any{
		"id": fmt.Sprintf("rollup-%d", i), "type": "hook_event", "conversation_id": conv,
		"harness": harness, "event": event, "ts": ts, "payload": payload,
	})
	if err != nil {
		t.Fatal(err)
	}
	return store.FactRow{RowHash: keys.ContentHash(raw), Type: "hook_event", ConversationID: conv,
		Harness: harness, Event: event, TS: float64(ts), Raw: raw}
}

// assertRollupExact checks hook_events_hourly equals the base-row hook_event aggregate in both
// directions, so no tuple is missing or double-counted.
func assertRollupExact(t *testing.T, tn *store.Tenant) {
	t.Helper()
	sel := `SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, norm_event, event, tool, conversation_id, count(*)
		FROM facts WHERE type='hook_event' GROUP BY 1,2,3,4,5,6,7`
	var diff int
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM (
		SELECT hour,harness,repo_id,norm_event,event,tool,conversation_id,n FROM hook_events_hourly
		EXCEPT ` + sel + `)`).Scan(&diff); err != nil {
		t.Fatal(err)
	}
	if diff != 0 {
		t.Fatalf("rollup has %d tuples not in the base aggregate", diff)
	}
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM (` + sel + `
		EXCEPT SELECT hour,harness,repo_id,norm_event,event,tool,conversation_id,n FROM hook_events_hourly)`).Scan(&diff); err != nil {
		t.Fatal(err)
	}
	if diff != 0 {
		t.Fatalf("base aggregate has %d tuples not in the rollup", diff)
	}
}

func rollupN(t *testing.T, tn *store.Tenant) (rollup, base int) {
	t.Helper()
	if err := tn.Raw().QueryRow(`SELECT coalesce(sum(n),0) FROM hook_events_hourly`).Scan(&rollup); err != nil {
		t.Fatal(err)
	}
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM facts WHERE type='hook_event'`).Scan(&base); err != nil {
		t.Fatal(err)
	}
	return
}

// facetBaseAggregate mirrors facetRollupFill exactly: 8 UNION ALL branches producing (dim, hour,
// value, count(*)) for every dimension, the tool branch restricted to hook_event.
const facetBaseAggregate = `SELECT 'repo_id', CAST(ts/3600 AS INTEGER)*3600, repo_id, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'harness', CAST(ts/3600 AS INTEGER)*3600, harness, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'plan', CAST(ts/3600 AS INTEGER)*3600, plan, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'event', CAST(ts/3600 AS INTEGER)*3600, event, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'model', CAST(ts/3600 AS INTEGER)*3600, model, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'norm_event', CAST(ts/3600 AS INTEGER)*3600, norm_event, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'kind', CAST(ts/3600 AS INTEGER)*3600, kind, count(*) FROM facts GROUP BY 2,3
	UNION ALL SELECT 'tool', CAST(ts/3600 AS INTEGER)*3600, tool, count(*) FROM facts WHERE type='hook_event' GROUP BY 2,3`

// exceptBothEmpty reports whether two row sets are identical in both directions, swallowing errors
// (the boolean variant used by allRollupsExact).
func exceptBothEmpty(tn *store.Tenant, rollupSel, baseSel string) bool {
	var d int
	sub := func(s string) string { return "SELECT * FROM (" + s + ")" }
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM (` + sub(rollupSel) + ` EXCEPT ` + sub(baseSel) + `)`).Scan(&d); err != nil {
		return false
	}
	if d != 0 {
		return false
	}
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM (` + sub(baseSel) + ` EXCEPT ` + sub(rollupSel) + `)`).Scan(&d); err != nil {
		return false
	}
	return d == 0
}

// allRollupsExact reports whether hook_events_hourly, conversations_hourly and facets_hourly each
// equal their base-row aggregate in both directions.
func allRollupsExact(tn *store.Tenant) bool {
	hook := exceptBothEmpty(tn,
		`SELECT hour,harness,repo_id,norm_event,event,tool,conversation_id,n FROM hook_events_hourly`,
		`SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, norm_event, event, tool, conversation_id, count(*) FROM facts WHERE type='hook_event' GROUP BY 1,2,3,4,5,6,7`)
	conv := exceptBothEmpty(tn,
		`SELECT hour,harness,repo_id,model,conversation_id,n FROM conversations_hourly`,
		`SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, model, conversation_id, count(*) FROM facts GROUP BY 1,2,3,4,5`)
	facet := exceptBothEmpty(tn, `SELECT dim,hour,value,n FROM facets_hourly`, facetBaseAggregate)
	return hook && conv && facet
}

// assertConvRollupExact checks conversations_hourly equals the base-row aggregate in both
// directions, so no tuple is missing or double-counted.
func assertConvRollupExact(t *testing.T, tn *store.Tenant) {
	t.Helper()
	exceptBothWays(t, tn,
		`SELECT hour,harness,repo_id,model,conversation_id,n FROM conversations_hourly`,
		`SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, model, conversation_id, count(*) FROM facts GROUP BY 1,2,3,4,5`,
		"conversations")
}

// assertFacetRollupExact checks facets_hourly equals the base-row aggregate in both directions.
func assertFacetRollupExact(t *testing.T, tn *store.Tenant) {
	t.Helper()
	exceptBothWays(t, tn, `SELECT dim,hour,value,n FROM facets_hourly`, facetBaseAggregate, "facets")
}

func exceptBothWays(t *testing.T, tn *store.Tenant, rollupSel, baseSel, name string) {
	t.Helper()
	var diff int
	sub := func(s string) string { return "SELECT * FROM (" + s + ")" }
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM (` + sub(rollupSel) + ` EXCEPT ` + sub(baseSel) + `)`).Scan(&diff); err != nil {
		t.Fatal(err)
	}
	if diff != 0 {
		t.Fatalf("%s rollup has %d tuples not in the base aggregate", name, diff)
	}
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM (` + sub(baseSel) + ` EXCEPT ` + sub(rollupSel) + `)`).Scan(&diff); err != nil {
		t.Fatal(err)
	}
	if diff != 0 {
		t.Fatalf("%s base aggregate has %d tuples not in the rollup", name, diff)
	}
}

// assertAllRollupsExact checks hook_events_hourly, conversations_hourly and facets_hourly each equal
// their base-row aggregate in both directions.
func assertAllRollupsExact(t *testing.T, tn *store.Tenant) {
	t.Helper()
	assertRollupExact(t, tn)
	assertConvRollupExact(t, tn)
	assertFacetRollupExact(t, tn)
}

// allRollupsLedger appends a ledger whose first rows (lowest rowids) change under compaction: row 1
// is a remove-listed opencode chat.params and the only row of conversation cdrop, and row 2 is a
// kept opencode transcript.assistant_message carrying a modelID, so compaction fills its model and
// norm_event. The rest are kept hooks varying harness/event so the hook rollup is exercised too.
// Append maintains every rollup, so it starts exact and compaction is what would drift it.
func allRollupsLedger(t *testing.T, tn *store.Tenant) int64 {
	t.Helper()
	base := int64(1791072000)
	rows := []store.FactRow{
		hookRow(t, 1, base+60, "opencode", "chat.params", "cdrop", map[string]any{"cwd": "/x"}),
		hookRow(t, 2, base+120, "opencode", "transcript.assistant_message", "ckeep", map[string]any{"modelID": "m1"}),
		hookRow(t, 3, base+3600+60, "claude", "PreToolUse", "ckeep", map[string]any{"tool_name": "Read"}),
		hookRow(t, 4, base+3600+120, "codex", "PostToolUse", "c2", map[string]any{"tool_name": "Bash"}),
		hookRow(t, 5, base+7200+60, "claude", "Stop", "ckeep", map[string]any{}),
	}
	if _, err := tn.Append(context.Background(), rows); err != nil {
		t.Fatalf("append ledger: %v", err)
	}
	return base
}

// TestCompactRebuildsRollup runs one compaction over a ledger that contains removable and
// collapsible hooks and asserts the rollup is back to the base-row aggregate afterwards.
func TestCompactRebuildsRollup(t *testing.T) {
	tn := openExclusive(t)
	rollupLedger(t, tn)
	assertRollupExact(t, tn) // Append kept it exact before compaction

	st, err := Run(context.Background(), tn, Options{})
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	if !st.Complete || st.Removed == 0 || st.Collapsed == 0 {
		t.Fatalf("compaction did not do the expected work: %+v", st)
	}
	assertRollupExact(t, tn)
	if rollup, base := rollupN(t, tn); rollup != base {
		t.Fatalf("rollup sum %d != base %d after compaction", rollup, base)
	}
}

// TestCompactRebuildsRollupOnResume interrupts after the first committed batch (leaving the rollup
// drifted, since the deletes bypass Append), resumes, and asserts the resumed run ends exact.
func TestCompactRebuildsRollupOnResume(t *testing.T) {
	tn := openExclusive(t)
	rollupLedger(t, tn)

	_, err := Run(context.Background(), tn, Options{Batch: 2, AfterCommit: func(batch int) error {
		if batch == 1 {
			return errStop
		}
		return nil
	}})
	if err != errStop {
		t.Fatalf("first run = %v, want errStop", err)
	}
	if rollup, base := rollupN(t, tn); rollup == base {
		t.Fatalf("interrupted run left no drift (rollup %d, base %d); test proves nothing", rollup, base)
	}

	st, err := Run(context.Background(), tn, Options{Batch: 2})
	if err != nil {
		t.Fatalf("resume: %v", err)
	}
	if !st.Complete {
		t.Fatalf("resume did not complete: %+v", st)
	}
	assertRollupExact(t, tn)
}

// TestCompactRebuildsAllRollups runs one compaction over a ledger where compaction both removes a
// conversation's only row and fills a kept row's model, and asserts every rollup table equals its
// base-row aggregate both before and after.
func TestCompactRebuildsAllRollups(t *testing.T) {
	tn := openExclusive(t)
	allRollupsLedger(t, tn)
	assertAllRollupsExact(t, tn) // Append kept them exact before compaction

	st, err := Run(context.Background(), tn, Options{})
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	if !st.Complete || st.Removed == 0 {
		t.Fatalf("compaction did not do the expected work: %+v", st)
	}
	assertAllRollupsExact(t, tn)

	var n int
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM facts WHERE conversation_id='cdrop'`).Scan(&n); err != nil {
		t.Fatal(err)
	}
	if n != 0 {
		t.Fatalf("%d cdrop facts remain in base after compaction", n)
	}
	if err := tn.Raw().QueryRow(`SELECT coalesce(sum(n),0) FROM conversations_hourly WHERE conversation_id='cdrop'`).Scan(&n); err != nil {
		t.Fatal(err)
	}
	if n != 0 {
		t.Fatalf("emptied conversation remains in conversations_hourly with weight %d", n)
	}
}

// TestCompactRebuildsAllRollupsOnResume interrupts after the first committed batch, whose two
// changing rows drift every rollup (deletes and model fills bypass Append), asserts the drift
// exists, then resumes and asserts the resumed run ends with every rollup exact.
func TestCompactRebuildsAllRollupsOnResume(t *testing.T) {
	tn := openExclusive(t)
	allRollupsLedger(t, tn)

	_, err := Run(context.Background(), tn, Options{Batch: 2, AfterCommit: func(batch int) error {
		if batch == 1 {
			return errStop
		}
		return nil
	}})
	if err != errStop {
		t.Fatalf("first run = %v, want errStop", err)
	}
	if allRollupsExact(tn) {
		t.Fatalf("interrupted run left no drift; test proves nothing")
	}

	st, err := Run(context.Background(), tn, Options{Batch: 2})
	if err != nil {
		t.Fatalf("resume: %v", err)
	}
	if !st.Complete {
		t.Fatalf("resume did not complete: %+v", st)
	}
	assertAllRollupsExact(t, tn)
}
