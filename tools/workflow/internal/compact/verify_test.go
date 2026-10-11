package compact

import (
	"bufio"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"io/fs"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/archive"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/serve"

	_ "modernc.org/sqlite"
)

// TestVerifyCopy checks a compacted ledger copy against the counts recorded
// before compaction. It runs only when WORKFLOW_VERIFY_DIR names the tenant
// directory and WORKFLOW_VERIFY_PRE names the key=value precounts file.
func TestVerifyCopy(t *testing.T) {
	dir := os.Getenv("WORKFLOW_VERIFY_DIR")
	pre := os.Getenv("WORKFLOW_VERIFY_PRE")
	if dir == "" || pre == "" {
		t.Skip("set WORKFLOW_VERIFY_DIR and WORKFLOW_VERIFY_PRE")
	}
	c := readPrecounts(t, pre)

	db, err := sql.Open("sqlite", "file:"+filepath.Join(dir, "ledger.db")+"?mode=ro")
	if err != nil {
		t.Fatalf("open ledger: %v", err)
	}
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { db.Close() })

	count := func(t *testing.T, query string, args ...any) int64 {
		t.Helper()
		var n int64
		if err := db.QueryRow(query, args...).Scan(&n); err != nil {
			t.Fatalf("query: %v", err)
		}
		return n
	}

	t.Run("a_removed_events", func(t *testing.T) {
		n := count(t, `SELECT COUNT(*) FROM facts WHERE type='hook_event' AND harness='opencode'
			AND event IN (?,?,?,?)`,
			"experimental.chat.system.transform", "chat.params", "chat.headers", "shell.env")
		t.Logf("removed opencode events remaining: %d", n)
		if n != 0 {
			t.Errorf("removed events remain: %d, want 0", n)
		}
	})

	t.Run("b_delta_rows", func(t *testing.T) {
		want := c["delta_parts"] + (c["delta_total"] - c["delta_with_key"])
		var rows, distinct int64
		if err := db.QueryRow(`SELECT COUNT(*), COUNT(DISTINCT row_hash) FROM facts
			WHERE type='hook_event' AND event='message.part.delta'`).Scan(&rows, &distinct); err != nil {
			t.Fatalf("query: %v", err)
		}
		t.Logf("delta rows=%d distinct=%d want=%d", rows, distinct, want)
		if rows != want {
			t.Errorf("delta rows = %d, want %d", rows, want)
		}
		if distinct != want {
			t.Errorf("distinct delta row_hash = %d, want %d", distinct, want)
		}
	})

	t.Run("c_no_payload", func(t *testing.T) {
		n := count(t, `SELECT COUNT(*) FROM facts WHERE type='hook_event'
			AND instr(CAST(raw AS TEXT), '"payload"') > 0`)
		t.Logf("hook_event rows still carrying a payload: %d", n)
		if n != 0 {
			t.Errorf("payload remains in %d hook rows, want 0", n)
		}
	})

	t.Run("d_archive_hashes", func(t *testing.T) {
		files, err := filepath.Glob(filepath.Join(dir, "archive", "*", "*.jsonl.zst"))
		if err != nil {
			t.Fatalf("glob archive: %v", err)
		}
		convs := map[string]struct{}{}
		for _, f := range files {
			conv, ok := unescapeName(filepath.Base(f))
			if !ok {
				t.Errorf("cannot decode archive file name %q", filepath.Base(f))
				continue
			}
			convs[conv] = struct{}{}
		}
		hashes := map[[16]byte]struct{}{}
		for conv := range convs {
			lines, err := archive.Read(dir, conv)
			if err != nil {
				t.Fatalf("archive read: %v", err)
			}
			for _, l := range lines {
				raw, err := hex.DecodeString(l.RowHash)
				if err != nil {
					t.Errorf("row_hash is not hex: %v", err)
					continue
				}
				var key [16]byte
				copy(key[:], raw)
				hashes[key] = struct{}{}
			}
		}
		want := c["expected_archive_hashes"]
		t.Logf("archive files=%d conversations=%d distinct first-16-byte row hashes=%d want=%d",
			len(files), len(convs), len(hashes), want)
		if int64(len(hashes)) != want {
			t.Errorf("distinct archive row hashes = %d, want %d", len(hashes), want)
		}
	})

	t.Run("e_serve_health", func(t *testing.T) {
		s := serve.New(serve.Config{Data: filepath.Dir(dir)}, serve.Options{DisableWorker: true})
		defer s.Close()
		h := s.Handler()
		req := httptest.NewRequest("GET", "/v1/health", nil)
		req.Host = "localhost"
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		t.Logf("GET /v1/health -> %d", rec.Code)
		if rec.Code != 200 {
			t.Fatalf("health status = %d, want 200", rec.Code)
		}
		var body struct {
			Compaction string `json:"compaction"`
		}
		if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
			t.Fatalf("health body: %v", err)
		}
		t.Logf("health compaction=%q", body.Compaction)
		if body.Compaction != "complete" {
			t.Errorf("health compaction = %q, want %q", body.Compaction, "complete")
		}
	})

	t.Run("f_facts_by_type", func(t *testing.T) {
		total := count(t, `SELECT COUNT(*) FROM facts`)
		hooks := count(t, `SELECT COUNT(*) FROM facts WHERE type='hook_event'`)
		wantTotal := c["facts_total"] - c["removed_total"] - (c["delta_total"] - c["delta_parts"])
		wantHooks := c["expected_surviving_hook_rows"]
		t.Logf("facts total=%d want=%d; hook rows=%d want=%d", total, wantTotal, hooks, wantHooks)
		if total != wantTotal {
			t.Errorf("facts total = %d, want %d", total, wantTotal)
		}
		if hooks != wantHooks {
			t.Errorf("hook rows = %d, want %d", hooks, wantHooks)
		}
		rows, err := db.Query(`SELECT type, COUNT(*) FROM facts GROUP BY type ORDER BY type`)
		if err != nil {
			t.Fatalf("group by type: %v", err)
		}
		defer rows.Close()
		for rows.Next() {
			var typ string
			var n int64
			if err := rows.Scan(&typ, &n); err != nil {
				t.Fatalf("scan type row: %v", err)
			}
			t.Logf("type %-24s %d", typ, n)
		}
		if err := rows.Err(); err != nil {
			t.Fatalf("group by type: %v", err)
		}
	})

	t.Run("g_meta", func(t *testing.T) {
		var value string
		if err := db.QueryRow(`SELECT value FROM meta WHERE key='compaction'`).Scan(&value); err != nil {
			t.Fatalf("meta query: %v", err)
		}
		t.Logf("meta compaction=%q", value)
		if value != "complete" {
			t.Errorf("meta compaction = %q, want %q", value, "complete")
		}
	})

	if fi, err := os.Stat(filepath.Join(dir, "ledger.db")); err == nil {
		t.Logf("ledger.db bytes=%d (pre=%d)", fi.Size(), c["ledger_db_bytes"])
	} else {
		t.Logf("ledger.db stat: %v", err)
	}
	var archBytes int64
	_ = filepath.WalkDir(filepath.Join(dir, "archive"), func(_ string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if fi, err := d.Info(); err == nil {
			archBytes += fi.Size()
		}
		return nil
	})
	t.Logf("archive bytes=%d", archBytes)
}

func readPrecounts(t *testing.T, path string) map[string]int64 {
	t.Helper()
	f, err := os.Open(path)
	if err != nil {
		t.Fatalf("open precounts: %v", err)
	}
	defer f.Close()
	out := map[string]int64{}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, val, ok := strings.Cut(line, "=")
		if !ok {
			t.Fatalf("precounts line %q is not key=value", line)
		}
		n, err := strconv.ParseInt(strings.TrimSpace(val), 10, 64)
		if err != nil {
			t.Fatalf("precounts %q value: %v", key, err)
		}
		out[strings.TrimSpace(key)] = n
	}
	if err := sc.Err(); err != nil {
		t.Fatalf("read precounts: %v", err)
	}
	return out
}

// unescapeName reverses archive.fileName: it trims the extension and decodes
// %XX (uppercase hex) escapes, with the bare "%" base name mapping to "".
func unescapeName(base string) (string, bool) {
	base = strings.TrimSuffix(base, ".jsonl.zst")
	if base == "%" {
		return "", true
	}
	var b strings.Builder
	for i := 0; i < len(base); i++ {
		if base[i] != '%' {
			b.WriteByte(base[i])
			continue
		}
		if i+2 >= len(base) {
			return "", false
		}
		v, err := strconv.ParseUint(base[i+1:i+3], 16, 8)
		if err != nil {
			return "", false
		}
		b.WriteByte(byte(v))
		i += 2
	}
	return b.String(), true
}
