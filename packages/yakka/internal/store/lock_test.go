package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestLockSharedCoexistsExclusiveRefused(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "t")
	a, err := Open(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	b, err := Open(dir, Options{}) // a second shared holder in the same process
	if err != nil {
		t.Fatalf("second shared Open: %v", err)
	}
	if _, err := OpenExclusive(dir, Options{}); !errors.Is(err, ErrLocked) {
		t.Fatalf("OpenExclusive while shared: %v", err)
	}
	if err := b.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := OpenExclusive(dir, Options{}); !errors.Is(err, ErrLocked) {
		t.Fatalf("OpenExclusive while one shared remains: %v", err)
	}
	if err := a.Close(); err != nil {
		t.Fatal(err)
	}
}

func TestLockExclusiveRefusesSharedAndReleases(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "t")
	ex, err := OpenExclusive(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Open(dir, Options{}); !errors.Is(err, ErrLocked) {
		t.Fatalf("Open while exclusive: %v", err)
	}
	if err := ex.Close(); err != nil {
		t.Fatal(err)
	}
	// The lock is released after Close: a normal Open now succeeds.
	tn, err := Open(dir, Options{})
	if err != nil {
		t.Fatalf("Open after exclusive close: %v", err)
	}
	if err := tn.Close(); err != nil {
		t.Fatal(err)
	}
}

func TestLockRawExclusiveOnly(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "t")
	sh, err := Open(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if sh.Raw() != nil {
		t.Fatal("Raw() must be nil for a shared Open")
	}
	sh.Close()
	ex, err := OpenExclusive(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if ex.Raw() == nil {
		t.Fatal("Raw() must be non-nil for OpenExclusive")
	}
	ex.Close()
}

func TestMetaRoundTrip(t *testing.T) {
	tn := openT(t, Options{})
	ctx := context.Background()
	if v, ok, err := tn.Meta(ctx, "compaction"); err != nil || !ok || v != "complete" {
		t.Fatalf("migration 5 seed: %q %v %v", v, ok, err)
	}
	if v, ok, err := tn.Meta(ctx, "missing"); err != nil || ok || v != "" {
		t.Fatalf("missing key: %q %v %v", v, ok, err)
	}
	if err := tn.SetMeta(ctx, "compaction", "required"); err != nil {
		t.Fatal(err)
	}
	if v, ok, err := tn.Meta(ctx, "compaction"); err != nil || !ok || v != "required" {
		t.Fatalf("after SetMeta: %q %v %v", v, ok, err)
	}
	if err := tn.SetMeta(ctx, "compaction", "complete"); err != nil {
		t.Fatal(err)
	}
	if v, _, _ := tn.Meta(ctx, "compaction"); v != "complete" {
		t.Fatalf("upsert: %q", v)
	}
	if err := tn.SetMeta(ctx, "new", "1"); err != nil {
		t.Fatal(err)
	}
	if v, ok, _ := tn.Meta(ctx, "new"); !ok || v != "1" {
		t.Fatalf("new key: %q %v", v, ok)
	}
}

func TestCompactionStateFreshEmptyComplete(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "t")
	tn, err := Open(dir, Options{})
	if err != nil {
		t.Fatal(err)
	}
	if s := tn.CompactionState(); s != "complete" {
		t.Fatalf("open fresh: %s", s)
	}
	tn.Close()
	if s := CompactionStateOf(dir); s != "complete" {
		t.Fatalf("unopened fresh: %s", s)
	}
}

// legacyRows builds a ledger at user_version 4 (before migration 5) holding one fact.
func legacyRows(t *testing.T, dir string) string {
	t.Helper()
	if err := os.MkdirAll(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	dbPath := filepath.Join(dir, "ledger.db")
	db, err := sql.Open("sqlite", dsn(dbPath))
	if err != nil {
		t.Fatal(err)
	}
	for i, m := range migrations[:4] {
		if _, err := db.Exec(m); err != nil {
			t.Fatal(err)
		}
		if _, err := db.Exec(fmt.Sprintf(`PRAGMA user_version = %d`, i+1)); err != nil {
			t.Fatal(err)
		}
	}
	r := row(1, "x")
	if _, err := db.Exec(`INSERT INTO facts (row_hash,type,conversation_id,harness,event,ts,received_at,repo_id,path,content_hash,raw)
		VALUES (?,?,?,?,?,?,?,?,?,?,?)`, r.RowHash, r.Type, "c", "h", "e", 1.0, 1, "", "", "", r.Raw); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	return dbPath
}

func TestCompactionStateLegacyWithRowsRequired(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "t")
	dbPath := legacyRows(t, dir)

	before, err := os.Stat(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	if s := CompactionStateOf(dir); s != "required" {
		t.Fatalf("unopened legacy: %s", s)
	}
	after, err := os.Stat(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	if !before.ModTime().Equal(after.ModTime()) {
		t.Fatal("CompactionStateOf must not write to ledger.db")
	}

	tn, err := Open(dir, Options{}) // migration 5 runs with rows present: no seed
	if err != nil {
		t.Fatal(err)
	}
	defer tn.Close()
	if s := tn.CompactionState(); s != "required" {
		t.Fatalf("open legacy: %s", s)
	}
	if err := tn.SetMeta(context.Background(), "compaction", "complete"); err != nil {
		t.Fatal(err)
	}
	if s := tn.CompactionState(); s != "complete" {
		t.Fatalf("after SetMeta: %s", s)
	}
}

func TestCompactionStateOfMissingLedgerComplete(t *testing.T) {
	if s := CompactionStateOf(filepath.Join(t.TempDir(), "none")); s != "complete" {
		t.Fatalf("missing ledger: %s", s)
	}
}
