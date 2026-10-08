package serve

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"testing"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/archive"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
)

type policyFact struct {
	ID             string         `json:"id"`
	Type           string         `json:"type"`
	ConversationID string         `json:"conversation_id"`
	Harness        string         `json:"harness"`
	Event          string         `json:"event"`
	TS             float64        `json:"ts"`
	Payload        map[string]any `json:"payload"`
}

type policyExpect struct {
	ID            string   `json:"id"`
	Policy        string   `json:"policy"`
	NormEvent     string   `json:"norm_event"`
	Tool          string   `json:"tool"`
	Model         string   `json:"model"`
	TokIn         int64    `json:"tok_in"`
	TokOut        int64    `json:"tok_out"`
	TokCacheRead  int64    `json:"tok_cache_read"`
	TokCacheWrite int64    `json:"tok_cache_write"`
	TokReasoning  int64    `json:"tok_reasoning"`
	CostReported  *float64 `json:"cost_reported"`
	FirstStatus   string   `json:"first_status"`
	ResendStatus  string   `json:"resend_status"`
}

type policyDispatch struct {
	Raw    json.RawMessage
	Fact   policyFact
	Expect policyExpect
}

type ingestResult struct {
	ID     string `json:"id"`
	Status string `json:"status"`
	Reason string `json:"reason"`
}

func loadIngestPolicy(t *testing.T) (string, []policyDispatch) {
	t.Helper()
	b, err := os.ReadFile(filepath.Join("..", "..", "..", "hooklog", "tests", "fixtures", "ingest_policy.json"))
	if err != nil {
		t.Fatalf("fixture: %v", err)
	}
	var fx struct {
		Facts  json.RawMessage `json:"facts"`
		Expect []policyExpect  `json:"expect"`
	}
	if err := json.Unmarshal(b, &fx); err != nil {
		t.Fatalf("fixture: %v", err)
	}
	var facts []json.RawMessage
	if err := json.Unmarshal(fx.Facts, &facts); err != nil {
		t.Fatalf("fixture facts: %v", err)
	}
	if len(facts) != len(fx.Expect) {
		t.Fatalf("fixture: %d facts, %d expect", len(facts), len(fx.Expect))
	}
	out := make([]policyDispatch, len(facts))
	for i := range facts {
		var f policyFact
		if err := json.Unmarshal(facts[i], &f); err != nil {
			t.Fatalf("fact %d: %v", i, err)
		}
		out[i] = policyDispatch{Raw: facts[i], Fact: f, Expect: fx.Expect[i]}
	}
	return `{"facts":` + string(fx.Facts) + `}`, out
}

func postPolicy(t *testing.T, h http.Handler, key, body string) []ingestResult {
	t.Helper()
	code, resp := do(t, h, "POST", "/v1/ingest", key, body)
	if code != 200 {
		t.Fatalf("ingest: %d %s", code, resp)
	}
	var out struct {
		Results []ingestResult `json:"results"`
	}
	if err := json.Unmarshal([]byte(resp), &out); err != nil {
		t.Fatalf("ingest response: %v: %.200s", err, resp)
	}
	return out.Results
}

func countFacts(t *testing.T, db *sql.DB) int {
	t.Helper()
	var n int
	if err := db.QueryRow(`SELECT count(*) FROM facts`).Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}

func readArchive(t *testing.T, dir string, ds []policyDispatch) map[string][]byte {
	t.Helper()
	seen := map[string]bool{}
	lines := map[string][]byte{}
	for _, d := range ds {
		if seen[d.Fact.ConversationID] {
			continue
		}
		seen[d.Fact.ConversationID] = true
		got, err := archive.Read(dir, d.Fact.ConversationID)
		if err != nil {
			t.Fatalf("archive.Read %s: %v", d.Fact.ConversationID, err)
		}
		for _, l := range got {
			lines[l.RowHash] = l.Fact
		}
	}
	return lines
}

func TestIngestPolicy(t *testing.T) {
	body, ds := loadIngestPolicy(t)
	s, root := newServer(t, true)
	h := s.Handler()
	dir := filepath.Join(root, "a")

	db, err := sql.Open("sqlite", "file:"+filepath.Join(dir, "ledger.db")+"?mode=ro")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	first := postPolicy(t, h, "ka", body)
	if len(first) != len(ds) {
		t.Fatalf("%d results, %d facts", len(first), len(ds))
	}

	t.Run("removed_events_accepted_no_fact_no_archive", func(t *testing.T) {
		removed := 0
		for i, d := range ds {
			if d.Expect.Policy != "remove" {
				continue
			}
			removed++
			if first[i].Status != "accepted" {
				t.Errorf("%s: %s, want accepted", d.Expect.ID, first[i].Status)
			}
			var n int
			if err := db.QueryRow(`SELECT count(*) FROM facts WHERE harness=? AND event=?`, d.Fact.Harness, d.Fact.Event).Scan(&n); err != nil {
				t.Fatal(err)
			}
			if n != 0 {
				t.Errorf("%s: %d facts for a removed event", d.Expect.ID, n)
			}
		}
		if removed != 4 {
			t.Fatalf("fixture has %d remove facts, want 4", removed)
		}
		lines := readArchive(t, dir, ds)
		if len(lines) != len(ds)-removed {
			t.Fatalf("%d archive lines, want %d", len(lines), len(ds)-removed)
		}
		for _, d := range ds {
			if d.Expect.Policy != "remove" {
				continue
			}
			rh, err := keys.RowHash(d.Raw)
			if err != nil {
				t.Fatal(err)
			}
			if _, ok := lines[rh]; ok {
				t.Errorf("%s: removed event archived", d.Expect.ID)
			}
		}
		for rh, fact := range lines {
			if bytes.Contains(fact, []byte("FAKE-NOT-A-SECRET")) {
				t.Errorf("archive line %s leaks a secret", rh)
			}
		}
	})

	t.Run("deltas_of_one_part_leave_one_fact", func(t *testing.T) {
		parts := map[string][]int{}
		for i, d := range ds {
			if d.Expect.Policy != "collapse" {
				continue
			}
			rh, ok := ingest.CollapseHash(d.Fact.Type, d.Fact.Harness, d.Fact.Event, d.Fact.ConversationID, d.Fact.Payload)
			if !ok {
				t.Fatalf("%s: no collapse key", d.Expect.ID)
			}
			parts[rh] = append(parts[rh], i)
			var n int
			if err := db.QueryRow(`SELECT count(*) FROM facts WHERE row_hash=?`, rh).Scan(&n); err != nil {
				t.Fatal(err)
			}
			if n != 1 {
				t.Errorf("%s: %d facts for the part, want 1", d.Expect.ID, n)
			}
		}
		if len(parts) != 2 {
			t.Fatalf("%d collapse parts, want 2", len(parts))
		}
		for rh, idxs := range parts {
			accepted := 0
			for _, i := range idxs {
				if first[i].Status == "accepted" {
					accepted++
				}
			}
			if accepted != 1 {
				t.Errorf("part %s: %d accepted of %d deltas, want 1", rh, accepted, len(idxs))
			}
		}
	})

	t.Run("kept_and_collapsed_events_have_verbatim_archive_line", func(t *testing.T) {
		lines := readArchive(t, dir, ds)
		for _, d := range ds {
			if d.Expect.Policy == "remove" {
				continue
			}
			rh, err := keys.RowHash(d.Raw)
			if err != nil {
				t.Fatal(err)
			}
			got, ok := lines[rh]
			if !ok {
				t.Errorf("%s: no archive line", d.Expect.ID)
				continue
			}
			want, err := keys.Canonical(d.Raw)
			if err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(got, want) {
				t.Errorf("%s: archived fact not verbatim\n got %s\nwant %s", d.Expect.ID, got, want)
			}
		}
	})

	t.Run("no_stored_hook_fact_raw_contains_payload", func(t *testing.T) {
		var n int
		if err := db.QueryRow(`SELECT count(*) FROM facts WHERE instr(raw,'"payload"') > 0`).Scan(&n); err != nil {
			t.Fatal(err)
		}
		if n != 0 {
			t.Fatalf("%d stored facts contain payload", n)
		}
	})

	t.Run("columns_match_fixture_expected", func(t *testing.T) {
		seenPart := map[string]bool{}
		checked := 0
		for _, d := range ds {
			if d.Expect.Policy == "remove" {
				continue
			}
			if d.Expect.Policy == "collapse" {
				rh, ok := ingest.CollapseHash(d.Fact.Type, d.Fact.Harness, d.Fact.Event, d.Fact.ConversationID, d.Fact.Payload)
				if !ok {
					t.Fatalf("%s: no collapse key", d.Expect.ID)
				}
				if seenPart[rh] {
					continue
				}
				seenPart[rh] = true
			}
			var (
				norm, tool, model            string
				tin, tout, tcr, tcw, treason int64
				cost                         sql.NullFloat64
			)
			err := db.QueryRow(`SELECT norm_event,tool,model,tok_in,tok_out,tok_cache_read,tok_cache_write,tok_reasoning,cost_reported FROM facts WHERE ts=?`, d.Fact.TS).
				Scan(&norm, &tool, &model, &tin, &tout, &tcr, &tcw, &treason, &cost)
			if err == sql.ErrNoRows {
				t.Errorf("%s: no row at ts %v", d.Expect.ID, d.Fact.TS)
				continue
			}
			if err != nil {
				t.Fatal(err)
			}
			checked++
			if norm != d.Expect.NormEvent || tool != d.Expect.Tool || model != d.Expect.Model ||
				tin != d.Expect.TokIn || tout != d.Expect.TokOut || tcr != d.Expect.TokCacheRead ||
				tcw != d.Expect.TokCacheWrite || treason != d.Expect.TokReasoning {
				t.Errorf("%s: columns %q/%q/%q %d/%d/%d/%d/%d, want %q/%q/%q %d/%d/%d/%d/%d",
					d.Expect.ID, norm, tool, model, tin, tout, tcr, tcw, treason,
					d.Expect.NormEvent, d.Expect.Tool, d.Expect.Model, d.Expect.TokIn, d.Expect.TokOut,
					d.Expect.TokCacheRead, d.Expect.TokCacheWrite, d.Expect.TokReasoning)
			}
			if d.Expect.CostReported == nil {
				if cost.Valid {
					t.Errorf("%s: cost %v, want null", d.Expect.ID, cost.Float64)
				}
			} else if !cost.Valid || cost.Float64 != *d.Expect.CostReported {
				t.Errorf("%s: cost %v, want %v", d.Expect.ID, cost.Float64, *d.Expect.CostReported)
			}
		}
		if checked != 51 {
			t.Errorf("checked %d rows, want 51", checked)
		}
	})

	t.Run("resend_returns_all_duplicate", func(t *testing.T) {
		before := countFacts(t, db)
		again := postPolicy(t, h, "ka", body)
		for i, d := range ds {
			if again[i].Status != d.Expect.ResendStatus {
				t.Errorf("%s: resend %s, want %s", d.Expect.ID, again[i].Status, d.Expect.ResendStatus)
			}
		}
		if after := countFacts(t, db); after != before {
			t.Fatalf("resend changed the fact count: %d then %d", before, after)
		}
	})
}
