// Package compact rewrites an existing ledger to the Phase 1 shape in resumable batches. In one
// pass over existing hook facts it archives each body, applies the event policy (removing and
// collapsing), strips the payload and fills the analytics columns, so that history and new ingest
// agree. It is offline: the tenant must be opened with store.OpenExclusive. It neither vacuums nor
// parses flags; the caller does that.
package compact

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strconv"
	"time"

	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/archive"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/ingest"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/keys"
	"github.com/codyhamilton/workflow-plugin/tools/workflow/internal/store"
)

// Options configures a Run. Batch is the rows examined per transaction (default 5000). Progress,
// when non-nil, receives one counts-only line every 50 batches. AfterArchive runs after the
// batch's archive.Append and before its SQL commit; AfterCommit runs after the commit. A non-nil
// hook error aborts Run with that error.
type Options struct {
	Batch        int
	Progress     io.Writer
	AfterArchive func(batch int) error
	AfterCommit  func(batch int) error
}

// Stats reports what a Run did. Scanned is the rows examined this run; Removed, Collapsed,
// Stripped and Backfilled are the hook and non-hook rows handled; Archived is the archive entries
// written (a resumed run may archive a batch twice). Complete is true when the scan reached the
// end of the table and meta compaction was set to "complete".
type Stats struct {
	Scanned    int64
	Removed    int64
	Collapsed  int64
	Stripped   int64
	Archived   int64
	Backfilled int64
	Complete   bool
}

// row is one facts row loaded for a batch.
type row struct {
	rowid      int64
	rowHash    string
	typ        string
	conv       string
	harness    string
	event      string
	ts         float64
	receivedAt int64
	path       string
	raw        []byte
}

// op is one SQL change planned for a batch.
type op struct {
	kind     byte // 'd' delete, 't' retime, 'h' hook rewrite, 'b' backfill
	rowid    int64
	newHash  string
	ts       float64
	raw      []byte
	d        ingest.Derived
	kindName string
	plan     string
	source   string
	sha      string
}

// surv is a collapsed part's survivor tracked while a batch is planned.
type surv struct {
	rowid int64
	ts    float64
}

// Run compacts t (must be opened with store.OpenExclusive). It repairs the archive, resumes from
// meta compact_cursor, walks facts by rowid in batches, and records completion in meta
// compaction. It never loads the table: memory is bounded by Batch.
func Run(ctx context.Context, t *store.Tenant, o Options) (Stats, error) {
	db := t.Raw()
	if db == nil {
		return Stats{}, errors.New("compact: tenant must be opened with store.OpenExclusive")
	}
	batch := o.Batch
	if batch <= 0 {
		batch = 5000
	}
	var st Stats
	if _, err := archive.Repair(t.Dir()); err != nil {
		return st, fmt.Errorf("compact: repair archive: %w", err)
	}
	state, stateOK, err := metaValue(ctx, db, "compaction")
	if err != nil {
		return st, err
	}
	cursor := int64(0)
	if c, ok, err := metaValue(ctx, db, "compact_cursor"); err != nil {
		return st, err
	} else if ok {
		if v, perr := strconv.ParseInt(c, 10, 64); perr == nil {
			cursor = v
		}
	}
	if stateOK && state == "complete" {
		var n int
		if err := db.QueryRowContext(ctx, `SELECT COUNT(*) FROM facts
			WHERE type='hook_event' AND instr(raw,'"payload"')>0`).Scan(&n); err != nil {
			return st, err
		}
		if n == 0 {
			st.Complete = true
			return st, nil
		}
	}

	start := time.Now()
	batches := 0
	for {
		rows, err := loadBatch(ctx, db, cursor, batch)
		if err != nil {
			return st, err
		}
		if len(rows) == 0 {
			tx, err := db.BeginTx(ctx, nil)
			if err != nil {
				return st, err
			}
			if err := putMeta(ctx, tx, "compaction", "complete"); err != nil {
				tx.Rollback()
				return st, err
			}
			if err := tx.Commit(); err != nil {
				return st, err
			}
			st.Complete = true
			return st, nil
		}
		batches++
		last := rows[len(rows)-1].rowid

		tx, err := db.BeginTx(ctx, nil)
		if err != nil {
			return st, err
		}
		entries, ops, ps, err := processBatch(ctx, tx, rows)
		if err != nil {
			tx.Rollback()
			return st, err
		}
		if err := archive.Append(t.Dir(), entries); err != nil {
			tx.Rollback()
			return st, fmt.Errorf("compact: archive batch %d: %w", batches, err)
		}
		if o.AfterArchive != nil {
			if err := o.AfterArchive(batches); err != nil {
				tx.Rollback()
				return st, err
			}
		}
		if err := applyOps(ctx, tx, ops); err != nil {
			tx.Rollback()
			return st, err
		}
		if err := putMeta(ctx, tx, "compact_cursor", strconv.FormatInt(last, 10)); err != nil {
			tx.Rollback()
			return st, err
		}
		if err := tx.Commit(); err != nil {
			return st, err
		}
		st.Scanned += int64(len(rows))
		st.Removed += ps.Removed
		st.Collapsed += ps.Collapsed
		st.Stripped += ps.Stripped
		st.Backfilled += ps.Backfilled
		st.Archived += int64(len(entries))
		cursor = last

		if o.AfterCommit != nil {
			if err := o.AfterCommit(batches); err != nil {
				return st, err
			}
		}
		if batches%20 == 0 {
			_, _ = db.ExecContext(ctx, `PRAGMA wal_checkpoint(TRUNCATE)`)
		}
		if batches%50 == 0 && o.Progress != nil {
			fmt.Fprintf(o.Progress, "compact: scanned=%d removed=%d collapsed=%d archived=%d elapsed=%s\n",
				st.Scanned, st.Removed, st.Collapsed, st.Archived, time.Since(start).Round(time.Millisecond))
		}
	}
}

// processBatch plans the batch: it decodes each row, applies the policy, and builds the archive
// entries and SQL ops. Entries carry the in-memory original raw (the received fact verbatim). A
// survivor in an earlier batch is found with a read; survivors created within this batch are
// tracked in memory, because no SQL has been applied yet.
func processBatch(ctx context.Context, tx *sql.Tx, rows []row) ([]archive.Entry, []op, Stats, error) {
	var ps Stats
	var entries []archive.Entry
	var ops []op
	survivors := map[string]*surv{}

	minInto := func(h string, ts float64) {
		s := survivors[h]
		if s != nil && ts < s.ts {
			s.ts = ts
			ops = append(ops, op{kind: 't', rowid: s.rowid, ts: ts})
		}
	}

	for _, r := range rows {
		dec := json.NewDecoder(bytes.NewReader(r.raw))
		dec.UseNumber()
		var obj map[string]any
		if err := dec.Decode(&obj); err != nil || obj == nil {
			return nil, nil, ps, fmt.Errorf("compact: row %d: decode raw: %w", r.rowid, err)
		}
		if r.typ == "hook_event" {
			payload, _ := obj["payload"].(map[string]any)
			action := ingest.Policy(r.harness, r.event, payload)
			if action == ingest.Remove {
				ops = append(ops, op{kind: 'd', rowid: r.rowid})
				ps.Removed++
				continue
			}
			entries = append(entries, archive.Entry{
				ConversationID: r.conv,
				TS:             r.ts,
				Line:           archive.Line{RowHash: r.rowHash, ReceivedAt: r.receivedAt, Fact: r.raw},
			})
			newHash := r.rowHash
			if action == ingest.Collapse {
				if ch, ok := ingest.CollapseHash(r.typ, r.harness, r.event, r.conv, payload); ok {
					if _, ok := survivors[ch]; ok {
						ops = append(ops, op{kind: 'd', rowid: r.rowid})
						minInto(ch, r.ts)
						ps.Collapsed++
						continue
					}
					var sid int64
					var sts float64
					err := tx.QueryRowContext(ctx, `SELECT rowid,ts FROM facts WHERE row_hash=? AND rowid<>?`, ch, r.rowid).
						Scan(&sid, &sts)
					switch {
					case err == nil:
						ops = append(ops, op{kind: 'd', rowid: r.rowid})
						m := r.ts
						if sts < m {
							m = sts
						}
						survivors[ch] = &surv{rowid: sid, ts: m}
						if m < sts {
							ops = append(ops, op{kind: 't', rowid: sid, ts: m})
						}
						ps.Collapsed++
						continue
					case errors.Is(err, sql.ErrNoRows):
						newHash = ch
					default:
						return nil, nil, ps, err
					}
				}
			}
			env, err := ingest.Envelope(obj)
			if err != nil {
				return nil, nil, ps, fmt.Errorf("compact: row %d: envelope: %w", r.rowid, err)
			}
			ops = append(ops, op{kind: 'h', rowid: r.rowid, newHash: newHash, raw: env,
				d: ingest.Derive(r.harness, r.event, payload)})
			if s, ok := survivors[newHash]; ok {
				if r.ts < s.ts {
					s.ts = r.ts
				}
			} else {
				survivors[newHash] = &surv{rowid: r.rowid, ts: r.ts}
			}
			ps.Stripped++
			continue
		}
		source, _ := obj["source"].(string)
		sha, _ := obj["sha"].(string)
		ops = append(ops, op{kind: 'b', rowid: r.rowid, kindName: keys.Kind(r.path),
			plan: store.PlanOf(r.path), source: source, sha: sha})
		ps.Backfilled++
	}
	return entries, ops, ps, nil
}

func applyOps(ctx context.Context, tx *sql.Tx, ops []op) error {
	for _, o := range ops {
		var err error
		switch o.kind {
		case 'd':
			_, err = tx.ExecContext(ctx, `DELETE FROM facts WHERE rowid=?`, o.rowid)
		case 't':
			_, err = tx.ExecContext(ctx, `UPDATE facts SET ts=? WHERE rowid=?`, o.ts, o.rowid)
		case 'h':
			_, err = tx.ExecContext(ctx, `UPDATE facts SET row_hash=?, raw=?, norm_event=?, tool=?, model=?,
				tok_in=?, tok_out=?, tok_cache_read=?, tok_cache_write=?, tok_reasoning=?, cost_reported=?
				WHERE rowid=?`,
				o.newHash, o.raw, o.d.NormEvent, o.d.Tool, o.d.Model,
				o.d.TokIn, o.d.TokOut, o.d.TokCacheRead, o.d.TokCacheWrite, o.d.TokReasoning, o.d.CostReported,
				o.rowid)
		case 'b':
			_, err = tx.ExecContext(ctx, `UPDATE facts SET kind=?, plan=?, source=?, sha=? WHERE rowid=?`,
				o.kindName, o.plan, o.source, o.sha, o.rowid)
		}
		if err != nil {
			return err
		}
	}
	return nil
}

func loadBatch(ctx context.Context, db *sql.DB, after int64, limit int) ([]row, error) {
	rs, err := db.QueryContext(ctx, `SELECT rowid,row_hash,type,conversation_id,harness,event,ts,
		received_at,path,raw FROM facts WHERE rowid > ? ORDER BY rowid LIMIT ?`, after, limit)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []row
	for rs.Next() {
		var r row
		if err := rs.Scan(&r.rowid, &r.rowHash, &r.typ, &r.conv, &r.harness, &r.event, &r.ts,
			&r.receivedAt, &r.path, &r.raw); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rs.Err()
}

func metaValue(ctx context.Context, db *sql.DB, key string) (string, bool, error) {
	var v string
	err := db.QueryRowContext(ctx, `SELECT value FROM meta WHERE key=?`, key).Scan(&v)
	if errors.Is(err, sql.ErrNoRows) {
		return "", false, nil
	}
	if err != nil {
		return "", false, err
	}
	return v, true, nil
}

func putMeta(ctx context.Context, tx *sql.Tx, key, value string) error {
	_, err := tx.ExecContext(ctx, `INSERT INTO meta(key,value) VALUES(?,?)
		ON CONFLICT(key) DO UPDATE SET value=excluded.value`, key, value)
	return err
}
