// Package store is the tenant store of design 3: one directory holding
// ledger.db (SQLite, WAL), blobs/ and pending/, with all ledger writes going
// through one group-commit writer goroutine per tenant.
package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"sync"
	"time"

	_ "modernc.org/sqlite"
)

// Options configures a Tenant.
type Options struct{ GroupWindow time.Duration } // default about 2 ms

// migrations is ordered; PRAGMA user_version records how many have run.
// Append new migrations; never edit earlier ones.
var migrations = []string{
	`CREATE TABLE facts (
		row_hash TEXT PRIMARY KEY, type TEXT NOT NULL, conversation_id TEXT NOT NULL,
		harness TEXT NOT NULL, event TEXT NOT NULL, ts REAL NOT NULL, received_at INTEGER NOT NULL,
		repo_id TEXT NOT NULL, path TEXT NOT NULL, content_hash TEXT NOT NULL, raw BLOB NOT NULL);
	CREATE INDEX facts_artifact ON facts(type, repo_id, path, received_at);
	CREATE INDEX facts_content ON facts(content_hash);
	CREATE INDEX facts_conv ON facts(conversation_id, ts);
	CREATE TABLE rejections (
		id INTEGER PRIMARY KEY, stage TEXT NOT NULL, fact_type TEXT NOT NULL, conversation_id TEXT NOT NULL,
		path TEXT NOT NULL, content_hash TEXT NOT NULL, pattern TEXT NOT NULL, reason TEXT NOT NULL, at INTEGER NOT NULL);
	CREATE INDEX rejections_hash ON rejections(content_hash);
	CREATE TABLE screens (
		id INTEGER PRIMARY KEY, content_hash TEXT NOT NULL, verdict TEXT NOT NULL, scorer TEXT NOT NULL, at INTEGER NOT NULL);
	CREATE INDEX screens_hash ON screens(content_hash);
	CREATE TABLE scores (
		id INTEGER PRIMARY KEY, content_hash TEXT NOT NULL, check_name TEXT NOT NULL, result REAL NOT NULL,
		scorer TEXT NOT NULL, at INTEGER NOT NULL);
	CREATE INDEX scores_hash ON scores(content_hash, check_name);`,
	// 2: full-text index of screened content, one row per content hash.
	`CREATE VIRTUAL TABLE search USING fts5(content_hash UNINDEXED, body, tokenize='porter unicode61');`,
	// 3: analytics window scans by event time.
	`CREATE INDEX IF NOT EXISTS facts_ts ON facts(ts);`,
}

var hashRE = regexp.MustCompile(`^[0-9a-f]{64}$`)

func validHash(h string) error {
	if !hashRE.MatchString(h) {
		return fmt.Errorf("store: invalid hash %q", h)
	}
	return nil
}

// ErrClosed is returned by writes after Close.
var ErrClosed = errors.New("store: tenant closed")

type request struct {
	fn   func(tx *sql.Tx) error // must be safe to run twice (group, then alone)
	done chan error
}

// Tenant is one open tenant directory.
type Tenant struct {
	dir    string
	window time.Duration
	wdb    *sql.DB // single writer connection
	rdb    *sql.DB // readers

	mu     sync.RWMutex // guards closed and sends on queue
	closed bool
	queue  chan *request
	wg     sync.WaitGroup
}

func dsn(path string) string {
	return "file:" + path + "?_pragma=journal_mode(WAL)&_pragma=synchronous(NORMAL)&_pragma=busy_timeout(5000)"
}

// Open creates dir, blobs/, pending/, migrates ledger.db and starts the writer.
func Open(dir string, opts Options) (*Tenant, error) {
	if opts.GroupWindow <= 0 {
		opts.GroupWindow = 2 * time.Millisecond
	}
	for _, d := range []string{dir, "blobs", "pending", "tmp"} {
		p := d
		if d != dir {
			p = filepath.Join(dir, d)
		}
		if err := os.MkdirAll(p, 0o700); err != nil {
			return nil, err
		}
	}
	dbPath := filepath.Join(dir, "ledger.db")
	wdb, err := sql.Open("sqlite", dsn(dbPath))
	if err != nil {
		return nil, err
	}
	wdb.SetMaxOpenConns(1)
	rdb, err := sql.Open("sqlite", dsn(dbPath))
	if err != nil {
		wdb.Close()
		return nil, err
	}
	t := &Tenant{dir: dir, window: opts.GroupWindow, wdb: wdb, rdb: rdb, queue: make(chan *request, 1024)}
	from, err := t.migrate()
	if err == nil && from == 1 {
		err = t.reindex(context.Background()) // existing db gaining the search index; writer not started yet
	}
	if err != nil {
		wdb.Close()
		rdb.Close()
		return nil, err
	}
	_ = os.Chmod(dbPath, 0o600)
	t.wg.Add(1)
	go t.writer()
	return t, nil
}

// migrate applies pending migrations and returns the user_version it started from.
func (t *Tenant) migrate() (int, error) {
	var v int
	if err := t.wdb.QueryRow(`PRAGMA user_version`).Scan(&v); err != nil {
		return 0, err
	}
	from := v
	for i := v; i < len(migrations); i++ {
		tx, err := t.wdb.Begin()
		if err != nil {
			return from, err
		}
		if _, err := tx.Exec(migrations[i]); err != nil {
			tx.Rollback()
			return from, fmt.Errorf("store: migration %d: %w", i+1, err)
		}
		if _, err := tx.Exec(fmt.Sprintf(`PRAGMA user_version = %d`, i+1)); err != nil {
			tx.Rollback()
			return from, err
		}
		if err := tx.Commit(); err != nil {
			return from, err
		}
	}
	return from, nil
}

// Close finishes queued writes, then closes the databases.
func (t *Tenant) Close() error {
	t.mu.Lock()
	if t.closed {
		t.mu.Unlock()
		return nil
	}
	t.closed = true
	close(t.queue)
	t.mu.Unlock()
	t.wg.Wait()
	e1 := t.wdb.Close()
	e2 := t.rdb.Close()
	if e1 != nil {
		return e1
	}
	return e2
}

func (t *Tenant) writer() {
	defer t.wg.Done()
	for first := range t.queue {
		group := []*request{first}
		timer := time.NewTimer(t.window)
	collect:
		for {
			select {
			case r, ok := <-t.queue:
				if !ok {
					break collect
				}
				group = append(group, r)
			case <-timer.C:
				break collect
			}
		}
		timer.Stop()
		t.commit(group)
	}
}

func (t *Tenant) run(reqs []*request) error {
	tx, err := t.wdb.Begin()
	if err != nil {
		return err
	}
	for _, r := range reqs {
		if err := r.fn(tx); err != nil {
			tx.Rollback()
			return err
		}
	}
	return tx.Commit()
}

func (t *Tenant) commit(group []*request) {
	if err := t.run(group); err == nil {
		for _, r := range group {
			r.done <- nil
		}
		return
	}
	if len(group) == 1 {
		group[0].done <- t.run(group)
		return
	}
	for _, r := range group {
		r.done <- t.run([]*request{r})
	}
}

// submit queues fn on the writer and waits for its commit.
func (t *Tenant) submit(ctx context.Context, fn func(tx *sql.Tx) error) error {
	r := &request{fn: fn, done: make(chan error, 1)}
	t.mu.RLock()
	if t.closed {
		t.mu.RUnlock()
		return ErrClosed
	}
	select {
	case t.queue <- r:
		t.mu.RUnlock()
	case <-ctx.Done():
		t.mu.RUnlock()
		return ctx.Err()
	}
	select {
	case err := <-r.done:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

// FactRow is one fact to append.
type FactRow struct {
	RowHash, Type, ConversationID, Harness, Event string
	TS                                            float64
	RepoID, Path, ContentHash                     string
	Raw                                           []byte // canonical fact JSON without id or content
}

// Append inserts rows (INSERT OR IGNORE by row hash) in one request and
// reports which were new. received_at is set here.
func (t *Tenant) Append(ctx context.Context, rows []FactRow) ([]bool, error) {
	for _, r := range rows {
		if r.ContentHash != "" {
			if err := validHash(r.ContentHash); err != nil {
				return nil, err
			}
		}
	}
	inserted := make([]bool, len(rows))
	err := t.submit(ctx, func(tx *sql.Tx) error {
		now := time.Now().UnixNano()
		st, err := tx.Prepare(`INSERT OR IGNORE INTO facts
			(row_hash,type,conversation_id,harness,event,ts,received_at,repo_id,path,content_hash,raw)
			VALUES (?,?,?,?,?,?,?,?,?,?,?)`)
		if err != nil {
			return err
		}
		defer st.Close()
		for i, r := range rows {
			if len(r.Raw) == 0 {
				// OR IGNORE would swallow the NOT NULL violation, so fail explicitly.
				return fmt.Errorf("store: fact %q has empty raw", r.RowHash)
			}
			var raw any = r.Raw
			res, err := st.Exec(r.RowHash, r.Type, r.ConversationID, r.Harness, r.Event, r.TS, now,
				r.RepoID, r.Path, r.ContentHash, raw)
			if err != nil {
				return err
			}
			n, _ := res.RowsAffected()
			inserted[i] = n > 0
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return inserted, nil
}

// Rejection records a precheck or screen rejection.
type Rejection struct{ Stage, FactType, ConversationID, Path, ContentHash, Pattern, Reason string }

func insertRejection(tx *sql.Tx, r Rejection) error {
	_, err := tx.Exec(`INSERT INTO rejections (stage,fact_type,conversation_id,path,content_hash,pattern,reason,at)
		VALUES (?,?,?,?,?,?,?,?)`, r.Stage, r.FactType, r.ConversationID, r.Path, r.ContentHash, r.Pattern, r.Reason,
		time.Now().UnixNano())
	return err
}

func (t *Tenant) AppendRejection(ctx context.Context, r Rejection) error {
	return t.submit(ctx, func(tx *sql.Tx) error { return insertRejection(tx, r) })
}

func (t *Tenant) blobPath(h string) string    { return filepath.Join(t.dir, "blobs", h[:2], h) }
func (t *Tenant) pendingPath(h string) string { return filepath.Join(t.dir, "pending", h) }

// HasBlob reports whether content is stored (false for an invalid hash).
func (t *Tenant) HasBlob(hash string) bool {
	if validHash(hash) != nil {
		return false
	}
	_, err := os.Stat(t.blobPath(hash))
	return err == nil
}

func exists(p string) bool { _, err := os.Stat(p); return err == nil }

// writeAtomic writes via a temp file in the tenant dir, fsync, rename.
func (t *Tenant) writeAtomic(dst string, content []byte) error {
	if err := os.MkdirAll(filepath.Dir(dst), 0o700); err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Join(t.dir, "tmp"), "w-*")
	if err != nil {
		return err
	}
	name := f.Name()
	ok := false
	defer func() {
		if !ok {
			os.Remove(name)
		}
	}()
	if err := f.Chmod(0o600); err != nil {
		f.Close()
		return err
	}
	if _, err := f.Write(content); err != nil {
		f.Close()
		return err
	}
	if err := f.Sync(); err != nil {
		f.Close()
		return err
	}
	if err := f.Close(); err != nil {
		return err
	}
	if err := os.Rename(name, dst); err != nil {
		return err
	}
	ok = true
	return nil
}

// WritePending stores content awaiting the screen; no-op if a blob or pending file exists.
func (t *Tenant) WritePending(hash string, content []byte) error {
	if err := validHash(hash); err != nil {
		return err
	}
	if exists(t.blobPath(hash)) || exists(t.pendingPath(hash)) {
		return nil
	}
	return t.writeAtomic(t.pendingPath(hash), content)
}

// PendingHashes lists pending content in arrival order (mtime, then name).
func (t *Tenant) PendingHashes() ([]string, error) {
	ents, err := os.ReadDir(filepath.Join(t.dir, "pending"))
	if err != nil {
		return nil, err
	}
	type e struct {
		h  string
		mt time.Time
	}
	var es []e
	for _, d := range ents {
		if validHash(d.Name()) != nil {
			continue
		}
		info, err := d.Info()
		if err != nil {
			continue
		}
		es = append(es, e{d.Name(), info.ModTime()})
	}
	sort.Slice(es, func(i, j int) bool {
		if !es[i].mt.Equal(es[j].mt) {
			return es[i].mt.Before(es[j].mt)
		}
		return es[i].h < es[j].h
	})
	out := make([]string, len(es))
	for i, x := range es {
		out[i] = x.h
	}
	return out, nil
}

func (t *Tenant) ReadPending(hash string) ([]byte, error) {
	if err := validHash(hash); err != nil {
		return nil, err
	}
	return os.ReadFile(t.pendingPath(hash))
}

func (t *Tenant) ReadBlob(hash string) ([]byte, error) {
	if err := validHash(hash); err != nil {
		return nil, err
	}
	return os.ReadFile(t.blobPath(hash))
}

// Screen is a screen verdict.
type Screen struct{ Verdict, Scorer string }

// Promote moves pending content to blobs/<aa>/<hash> and records the screen and its scores in one
// transaction (scores take the screen's scorer name). If the blob already exists it only records
// the screen (and clears any pending file).
func (t *Tenant) Promote(ctx context.Context, hash string, s Screen, scores ...Score) error {
	if err := validHash(hash); err != nil {
		return err
	}
	if !exists(t.blobPath(hash)) {
		if err := os.MkdirAll(filepath.Dir(t.blobPath(hash)), 0o700); err != nil {
			return err
		}
		if err := os.Rename(t.pendingPath(hash), t.blobPath(hash)); err != nil {
			return err
		}
	} else if err := os.Remove(t.pendingPath(hash)); err != nil && !os.IsNotExist(err) {
		return err
	}
	return t.submit(ctx, func(tx *sql.Tx) error {
		now := time.Now().UnixNano()
		if _, err := tx.Exec(`INSERT INTO screens (content_hash,verdict,scorer,at) VALUES (?,?,?,?)`,
			hash, s.Verdict, s.Scorer, now); err != nil {
			return err
		}
		for _, x := range scores {
			if _, err := tx.Exec(`INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`,
				hash, x.Check, x.Result, s.Scorer, now); err != nil {
				return err
			}
		}
		if searchable(s.Verdict) {
			return t.indexTx(tx, hash)
		}
		return nil
	})
}

// DropBlob deletes stored content and records the rejection (the flag path for a blob that was
// promoted but never screened).
func (t *Tenant) DropBlob(ctx context.Context, hash string, r Rejection) error {
	if err := validHash(hash); err != nil {
		return err
	}
	if err := os.Remove(t.blobPath(hash)); err != nil && !os.IsNotExist(err) {
		return err
	}
	if r.ContentHash == "" {
		r.ContentHash = hash
	}
	return t.submit(ctx, func(tx *sql.Tx) error {
		if _, err := tx.Exec(`DELETE FROM search WHERE content_hash=?`, hash); err != nil {
			return err
		}
		return insertRejection(tx, r)
	})
}

// PendingPath is the pending file's path (tests set its mod time).
func (t *Tenant) PendingPath(hash string) string { return t.pendingPath(hash) }

// HasPending reports whether a pending file exists for hash.
func (t *Tenant) HasPending(hash string) bool {
	return validHash(hash) == nil && exists(t.pendingPath(hash))
}

// PendingModTime is the pending file's modification time.
func (t *Tenant) PendingModTime(hash string) (time.Time, error) {
	if err := validHash(hash); err != nil {
		return time.Time{}, err
	}
	fi, err := os.Stat(t.pendingPath(hash))
	if err != nil {
		return time.Time{}, err
	}
	return fi.ModTime(), nil
}

// ContentInfo describes the artifact_version facts carrying one content hash.
type ContentInfo struct {
	Paths                      []string // distinct, in path order
	LatestPath, ConversationID string   // from the latest such fact
}

// ContentFacts reads the artifact_version facts with content hash; Paths is empty when none.
func (t *Tenant) ContentFacts(ctx context.Context, hash string) (ContentInfo, error) {
	var ci ContentInfo
	rows, err := t.rdb.QueryContext(ctx, `SELECT DISTINCT path FROM facts WHERE type='artifact_version' AND content_hash=? ORDER BY path`, hash)
	if err != nil {
		return ci, err
	}
	defer rows.Close()
	for rows.Next() {
		var p string
		if err := rows.Scan(&p); err != nil {
			return ci, err
		}
		ci.Paths = append(ci.Paths, p)
	}
	if err := rows.Err(); err != nil {
		return ci, err
	}
	if len(ci.Paths) == 0 {
		return ci, nil
	}
	err = t.rdb.QueryRowContext(ctx, `SELECT path, conversation_id FROM facts WHERE type='artifact_version' AND content_hash=?
		ORDER BY received_at DESC, rowid DESC LIMIT 1`, hash).Scan(&ci.LatestPath, &ci.ConversationID)
	return ci, err
}

// UnscreenedBlobs lists blobs on disk with no screens row (a crash between the move and the row).
func (t *Tenant) UnscreenedBlobs(ctx context.Context) ([]string, error) {
	screened := map[string]bool{}
	rows, err := t.rdb.QueryContext(ctx, `SELECT DISTINCT content_hash FROM screens`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var h string
		if err := rows.Scan(&h); err != nil {
			return nil, err
		}
		screened[h] = true
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	var out []string
	dirs, err := os.ReadDir(filepath.Join(t.dir, "blobs"))
	if err != nil {
		return nil, err
	}
	for _, d := range dirs {
		if !d.IsDir() {
			continue
		}
		ents, err := os.ReadDir(filepath.Join(t.dir, "blobs", d.Name()))
		if err != nil {
			return nil, err
		}
		for _, e := range ents {
			if validHash(e.Name()) == nil && !screened[e.Name()] {
				out = append(out, e.Name())
			}
		}
	}
	sort.Strings(out)
	return out, nil
}

// ScreenGaps counts content hashes of artifact_version facts that have no pending file, no blob
// and no rejection: content the ledger knows of but the store lost.
func (t *Tenant) ScreenGaps(ctx context.Context) (int, error) {
	rows, err := t.rdb.QueryContext(ctx, `SELECT DISTINCT content_hash FROM facts WHERE type='artifact_version'
		AND content_hash NOT IN (SELECT content_hash FROM rejections)`)
	if err != nil {
		return 0, err
	}
	defer rows.Close()
	n := 0
	for rows.Next() {
		var h string
		if err := rows.Scan(&h); err != nil {
			return 0, err
		}
		if validHash(h) == nil && !exists(t.blobPath(h)) && !exists(t.pendingPath(h)) {
			n++
		}
	}
	return n, rows.Err()
}

// DropPending deletes pending content and records the rejection (phase 3's flag path).
func (t *Tenant) DropPending(ctx context.Context, hash string, r Rejection) error {
	if err := validHash(hash); err != nil {
		return err
	}
	if err := os.Remove(t.pendingPath(hash)); err != nil && !os.IsNotExist(err) {
		return err
	}
	if r.ContentHash == "" {
		r.ContentHash = hash
	}
	return t.AppendRejection(ctx, r)
}

// Score is one check result for a content hash.
type Score struct {
	Check  string
	Result float64
	Scorer string
}

func (t *Tenant) AppendScores(ctx context.Context, hash string, s []Score) error {
	if err := validHash(hash); err != nil {
		return err
	}
	return t.submit(ctx, func(tx *sql.Tx) error {
		now := time.Now().UnixNano()
		for _, x := range s {
			if _, err := tx.Exec(`INSERT INTO scores (content_hash,check_name,result,scorer,at) VALUES (?,?,?,?,?)`,
				hash, x.Check, x.Result, x.Scorer, now); err != nil {
				return err
			}
		}
		return nil
	})
}

type ScreenRow struct {
	Verdict, Scorer string
	At              time.Time
}
type ScoreRow struct {
	Check string
	Score float64
}
type Latest struct {
	ContentHash            string
	ReceivedAt             time.Time
	ConversationID, Source string
	Screen                 *ScreenRow
	Scores                 []ScoreRow
	Rejection              *RejectionRow // most recent rejection of this content hash, or nil
}

// RejectionRow is a stored rejection as the artifact read shows it.
type RejectionRow struct {
	Stage, Reason string
	At            time.Time
}
type Artifact struct {
	RepoID, Path string
	Versions     int
	Latest       Latest
}

// Artifact reads artifact_version facts for repoID/path; nil, nil when none.
func (t *Tenant) Artifact(ctx context.Context, repoID, path string) (*Artifact, error) {
	a := &Artifact{RepoID: repoID, Path: path}
	var recv int64
	var src sql.NullString
	err := t.rdb.QueryRowContext(ctx, `SELECT content_hash, received_at, conversation_id, json_extract(raw,'$.source')
		FROM facts WHERE type='artifact_version' AND repo_id=? AND path=?
		ORDER BY received_at DESC, rowid DESC LIMIT 1`, repoID, path).
		Scan(&a.Latest.ContentHash, &recv, &a.Latest.ConversationID, &src)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	a.Latest.ReceivedAt = time.Unix(0, recv)
	a.Latest.Source = src.String
	if err := t.rdb.QueryRowContext(ctx, `SELECT count(DISTINCT content_hash) FROM facts
		WHERE type='artifact_version' AND repo_id=? AND path=?`, repoID, path).Scan(&a.Versions); err != nil {
		return nil, err
	}
	h := a.Latest.ContentHash
	var s ScreenRow
	var at int64
	err = t.rdb.QueryRowContext(ctx, `SELECT verdict, scorer, at FROM screens WHERE content_hash=?
		ORDER BY at DESC, id DESC LIMIT 1`, h).Scan(&s.Verdict, &s.Scorer, &at)
	switch {
	case err == nil:
		s.At = time.Unix(0, at)
		a.Latest.Screen = &s
	case !errors.Is(err, sql.ErrNoRows):
		return nil, err
	}
	var rj RejectionRow
	err = t.rdb.QueryRowContext(ctx, `SELECT stage, reason, at FROM rejections WHERE content_hash=?
		ORDER BY id DESC LIMIT 1`, h).Scan(&rj.Stage, &rj.Reason, &at)
	switch {
	case err == nil:
		rj.At = time.Unix(0, at)
		a.Latest.Rejection = &rj
	case !errors.Is(err, sql.ErrNoRows):
		return nil, err
	}
	rows, err := t.rdb.QueryContext(ctx, `SELECT check_name, result FROM scores WHERE content_hash=? ORDER BY id DESC`, h)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	seen := map[string]bool{}
	for rows.Next() {
		var r ScoreRow
		if err := rows.Scan(&r.Check, &r.Score); err != nil {
			return nil, err
		}
		if !seen[r.Check] {
			seen[r.Check] = true
			a.Latest.Scores = append(a.Latest.Scores, r)
		}
	}
	return a, rows.Err()
}
