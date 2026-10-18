package compact

import (
	"context"
	"encoding/json"
	"fmt"
	"reflect"
	"testing"

	"github.com/codyhamilton/yakka/packages/yakka/internal/archive"
	"github.com/codyhamilton/yakka/packages/yakka/internal/keys"
	"github.com/codyhamilton/yakka/packages/yakka/internal/store"
)

type purgeFixture struct {
	deltaHashConv map[string]string // delta fact row hash -> conversation
	keptHashConv  map[string]string // non-delta hook row hash -> conversation
}

// purgeLedger appends a compacted-state ledger holding deltas and kept hooks across several
// conversations plus one non-hook fact, and archives every hook body. The deltas are the only rows
// of cdelta, so purging them empties that conversation from every rollup.
func purgeLedger(t *testing.T, tn *store.Tenant) purgeFixture {
	t.Helper()
	base := int64(1791072000)
	rows := []store.FactRow{
		hookRow(t, 1, base+60, "opencode", "message.part.delta", "cdelta", map[string]any{"field": "text"}),
		hookRow(t, 2, base+120, "opencode", "message.part.delta", "cdelta", map[string]any{"field": "text"}),
		hookRow(t, 3, base+180, "opencode", "message.part.delta", "cmix", map[string]any{"field": "text"}),
		hookRow(t, 4, base+240, "claude", "PreToolUse", "cmix", map[string]any{"tool_name": "Read"}),
		hookRow(t, 5, base+3600+60, "opencode", "message.part.delta", "cmix", map[string]any{"field": "text"}),
		hookRow(t, 6, base+3600+120, "claude", "PostToolUse", "cmix", map[string]any{"tool_name": "Bash"}),
		hookRow(t, 7, base+7200+60, "codex", "Stop", "cnon", map[string]any{}),
		artifactRow(t, 8, base+7200+120, "cnon"),
	}
	if _, err := tn.Append(context.Background(), rows); err != nil {
		t.Fatalf("append: %v", err)
	}
	fx := purgeFixture{deltaHashConv: map[string]string{}, keptHashConv: map[string]string{}}
	var entries []archive.Entry
	for _, r := range rows {
		if r.Type != "hook_event" {
			continue
		}
		entries = append(entries, archive.Entry{ConversationID: r.ConversationID, TS: r.TS,
			Line: archive.Line{RowHash: r.RowHash, ReceivedAt: int64(r.TS), Fact: r.Raw}})
		if r.Event == "message.part.delta" {
			fx.deltaHashConv[r.RowHash] = r.ConversationID
		} else {
			fx.keptHashConv[r.RowHash] = r.ConversationID
		}
	}
	if err := archive.Append(tn.Dir(), entries); err != nil {
		t.Fatalf("archive append: %v", err)
	}
	return fx
}

func artifactRow(t *testing.T, i int, ts int64, conv string) store.FactRow {
	t.Helper()
	raw, err := json.Marshal(map[string]any{"id": fmt.Sprintf("art-%d", i), "type": "artifact_version",
		"conversation_id": conv, "harness": "claude", "event": "", "ts": ts, "path": "docs/x.md"})
	if err != nil {
		t.Fatal(err)
	}
	return store.FactRow{RowHash: keys.ContentHash(raw), Type: "artifact_version", ConversationID: conv,
		Harness: "claude", Event: "", TS: float64(ts), Raw: raw}
}

func factStrings(t *testing.T, tn *store.Tenant, where string) []string {
	t.Helper()
	q := `SELECT row_hash,type,event,ts,raw FROM facts`
	if where != "" {
		q += " WHERE " + where
	}
	q += " ORDER BY row_hash"
	rows, err := tn.Raw().Query(q)
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var rh, typ, ev string
		var ts float64
		var raw []byte
		if err := rows.Scan(&rh, &typ, &ev, &ts, &raw); err != nil {
			t.Fatal(err)
		}
		out = append(out, fmt.Sprintf("%s|%s|%s|%v|%s", rh, typ, ev, ts, raw))
	}
	if err := rows.Err(); err != nil {
		t.Fatal(err)
	}
	return out
}

func deltaRows(t *testing.T, tn *store.Tenant) int {
	t.Helper()
	var n int
	if err := tn.Raw().QueryRow(`SELECT count(*) FROM facts
		WHERE harness='opencode' AND event='message.part.delta'`).Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}

func convWeight(t *testing.T, tn *store.Tenant, conv string) int {
	t.Helper()
	var n int
	if err := tn.Raw().QueryRow(`SELECT coalesce(sum(n),0) FROM conversations_hourly
		WHERE conversation_id=?`, conv).Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}

func archiveHashSet(t *testing.T, tn *store.Tenant, conv string) map[string]bool {
	t.Helper()
	lines, err := archive.Read(tn.Dir(), conv)
	if err != nil {
		t.Fatal(err)
	}
	m := map[string]bool{}
	for _, l := range lines {
		m[l.RowHash] = true
	}
	return m
}

func allArchive(t *testing.T, tn *store.Tenant, convs []string) map[string][]string {
	t.Helper()
	out := map[string][]string{}
	for _, c := range convs {
		lines, err := archive.Read(tn.Dir(), c)
		if err != nil {
			t.Fatal(err)
		}
		var hs []string
		for _, l := range lines {
			hs = append(hs, l.RowHash)
		}
		out[c] = hs
	}
	return out
}

// TestPurgeDeltasRemovesAllDeltas purges a compacted-state ledger and checks the delta facts and
// archive lines are gone while every other row is byte-identical and every rollup stays exact.
func TestPurgeDeltasRemovesAllDeltas(t *testing.T) {
	tn := openExclusive(t)
	fx := purgeLedger(t, tn)
	if len(fx.deltaHashConv) != 4 {
		t.Fatalf("fixture deltas = %d, want 4", len(fx.deltaHashConv))
	}
	beforeNon := factStrings(t, tn, "NOT (harness='opencode' AND event='message.part.delta')")
	assertAllRollupsExact(t, tn) // Append maintained every rollup before purge
	if convWeight(t, tn, "cdelta") == 0 {
		t.Fatal("cdelta absent from conversations_hourly before purge; test proves nothing")
	}

	st, err := PurgeDeltas(context.Background(), tn, Options{})
	if err != nil {
		t.Fatalf("PurgeDeltas: %v", err)
	}
	if st.FactsDeleted != int64(len(fx.deltaHashConv)) {
		t.Fatalf("FactsDeleted = %d, want %d", st.FactsDeleted, len(fx.deltaHashConv))
	}
	if st.ArchiveDropped != len(fx.deltaHashConv) || st.FilesRewritten != 1 || st.FilesDeleted != 1 {
		t.Fatalf("archive stats = %+v", st)
	}
	if n := deltaRows(t, tn); n != 0 {
		t.Fatalf("%d delta facts remain", n)
	}
	if after := factStrings(t, tn, "NOT (harness='opencode' AND event='message.part.delta')"); !reflect.DeepEqual(beforeNon, after) {
		t.Fatalf("non-delta facts changed:\nbefore %v\nafter  %v", beforeNon, after)
	}
	assertAllRollupsExact(t, tn)
	if convWeight(t, tn, "cdelta") != 0 {
		t.Fatalf("cdelta still in conversations_hourly after purge")
	}
	for hash, conv := range fx.keptHashConv {
		if !archiveHashSet(t, tn, conv)[hash] {
			t.Fatalf("kept archive line %s in %s missing", hash, conv)
		}
	}
	for hash, conv := range fx.deltaHashConv {
		if archiveHashSet(t, tn, conv)[hash] {
			t.Fatalf("delta archive line %s in %s survived", hash, conv)
		}
	}
}

// TestPurgeDeltasResumesAndConverges interrupts after the first committed batch, resumes to
// completion, checks the result equals an uninterrupted run, and checks a third run is a no-op.
func TestPurgeDeltasResumesAndConverges(t *testing.T) {
	convs := []string{"cdelta", "cmix", "cnon"}

	ref := openExclusive(t)
	purgeLedger(t, ref)
	if _, err := PurgeDeltas(context.Background(), ref, Options{}); err != nil {
		t.Fatalf("reference purge: %v", err)
	}
	wantFacts := factStrings(t, ref, "")
	wantArchive := allArchive(t, ref, convs)

	tn := openExclusive(t)
	purgeLedger(t, tn)
	_, err := PurgeDeltas(context.Background(), tn, Options{Batch: 1, AfterCommit: func(b int) error {
		if b == 1 {
			return errStop
		}
		return nil
	}})
	if err != errStop {
		t.Fatalf("first run = %v, want errStop", err)
	}
	if deltaRows(t, tn) == 0 {
		t.Fatal("first run deleted every delta; test proves nothing")
	}

	if _, err := PurgeDeltas(context.Background(), tn, Options{}); err != nil {
		t.Fatalf("resume: %v", err)
	}
	if got := factStrings(t, tn, ""); !reflect.DeepEqual(got, wantFacts) {
		t.Fatalf("resumed facts differ:\ngot  %v\nwant %v", got, wantFacts)
	}
	if got := allArchive(t, tn, convs); !reflect.DeepEqual(got, wantArchive) {
		t.Fatalf("resumed archive differs:\ngot  %v\nwant %v", got, wantArchive)
	}
	assertAllRollupsExact(t, tn)

	st, err := PurgeDeltas(context.Background(), tn, Options{})
	if err != nil {
		t.Fatalf("third run: %v", err)
	}
	if st != (PurgeStats{}) {
		t.Fatalf("third run changed something: %+v", st)
	}
}
