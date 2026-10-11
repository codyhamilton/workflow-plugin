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
