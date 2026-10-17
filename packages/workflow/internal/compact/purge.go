// This file adds PurgeDeltas, a sibling of Run. Run rewrites history to the Phase 1 shape;
// PurgeDeltas applies the later design amendment (DESIGN "Amendments after sign-off": deltas are
// dropped at the source) to history, removing every message.part.delta fact and archive line and
// rebuilding the rollups. It neither vacuums nor parses flags; the caller does that.

package compact

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/codyhamilton/workflow-plugin/packages/workflow/internal/archive"
	"github.com/codyhamilton/workflow-plugin/packages/workflow/internal/store"
)

// PurgeStats reports what a PurgeDeltas did: the count of message.part.delta facts deleted and the
// archive lines dropped, files rewritten and files deleted by the archive filter.
type PurgeStats struct {
	FactsDeleted   int64
	ArchiveDropped int
	FilesRewritten int
	FilesDeleted   int
}

// PurgeDeltas deletes every message.part.delta fact (opencode harness) from t and every delta line
// from its archive, then rebuilds every rollup. t must be opened with store.OpenExclusive, so the
// command is offline and holds the tenant's exclusive lock.
//
// The steps run in this order: archive.Repair, then the facts delete in batches of o.Batch (default
// 5000) by rowid with one transaction per batch, then the archive filter, then RebuildRollups. A
// kill between steps leaves a consistent partial state. A rerun converges because every step is
// idempotent and re-derivable from the data: Repair leaves a healthy archive untouched; the delete
// finds no delta row once they are gone; the filter drops only delta lines, so it drops none once
// they are gone; and RebuildRollups recomputes each rollup from base rows rather than adjusting it,
// so it is exact whether or not this run changed a row. The delete precedes the filter and the
// rebuild is last so a partial run leaves no delta fact behind a stale archive line and ends with
// rollups matching whatever base rows remain. ctx is checked between batches and before the filter.
func PurgeDeltas(ctx context.Context, t *store.Tenant, o Options) (st PurgeStats, err error) {
	db := t.Raw()
	if db == nil {
		return st, errors.New("compact: tenant must be opened with store.OpenExclusive")
	}
	if _, err := archive.Repair(t.Dir()); err != nil {
		return st, fmt.Errorf("compact: repair archive: %w", err)
	}
	if err := purgeDeltaFacts(ctx, db, o, &st); err != nil {
		return st, err
	}
	if err := ctx.Err(); err != nil {
		return st, err
	}
	fs, err := archive.Filter(t.Dir(), func(l archive.Line) bool { return !isDeltaLine(l) })
	if err != nil {
		return st, fmt.Errorf("compact: filter archive: %w", err)
	}
	st.ArchiveDropped = fs.Dropped
	st.FilesRewritten = fs.Rewritten
	st.FilesDeleted = fs.Deleted
	// RebuildRollups recomputes every rollup from base rows, so it is exact even when nothing was
	// deleted (as compact.Run does); a run that dies before it leaves the work for the next run.
	if err := t.RebuildRollups(ctx); err != nil {
		return st, err
	}
	return st, nil
}

// purgeDeltaFacts deletes the delta facts by rowid range, one transaction per batch, and advances a
// cursor so a kill leaves the earlier batches committed.
func purgeDeltaFacts(ctx context.Context, db *sql.DB, o Options, st *PurgeStats) error {
	batch := o.Batch
	if batch <= 0 {
		batch = 5000
	}
	cursor := int64(0)
	for n := 1; ; n++ {
		if err := ctx.Err(); err != nil {
			return err
		}
		ids, last, err := deltaBatch(ctx, db, cursor, batch)
		if err != nil {
			return err
		}
		if len(ids) == 0 {
			return nil
		}
		tx, err := db.BeginTx(ctx, nil)
		if err != nil {
			return err
		}
		res, err := tx.ExecContext(ctx, `DELETE FROM facts
			WHERE harness='opencode' AND event='message.part.delta' AND rowid > ? AND rowid <= ?`,
			cursor, last)
		if err != nil {
			tx.Rollback()
			return err
		}
		deleted, _ := res.RowsAffected()
		if err := tx.Commit(); err != nil {
			return err
		}
		st.FactsDeleted += deleted
		cursor = last
		if o.AfterCommit != nil {
			if err := o.AfterCommit(n); err != nil {
				return err
			}
		}
		if len(ids) < batch {
			return nil
		}
	}
}

// deltaBatch returns the rowids of up to limit delta facts after the cursor, and the highest one.
func deltaBatch(ctx context.Context, db *sql.DB, after int64, limit int) (ids []int64, last int64, err error) {
	rs, err := db.QueryContext(ctx, `SELECT rowid FROM facts
		WHERE rowid > ? AND harness='opencode' AND event='message.part.delta'
		ORDER BY rowid LIMIT ?`, after, limit)
	if err != nil {
		return nil, 0, err
	}
	defer rs.Close()
	for rs.Next() {
		var id int64
		if err := rs.Scan(&id); err != nil {
			return nil, 0, err
		}
		ids = append(ids, id)
		last = id
	}
	return ids, last, rs.Err()
}

// isDeltaLine reports whether an archived line is a message.part.delta hook fact. It decodes only
// the envelope fields it needs and never requires the payload to parse; an undecodable fact is kept.
func isDeltaLine(l archive.Line) bool {
	var env struct {
		Event string `json:"event"`
	}
	if err := json.Unmarshal(l.Fact, &env); err != nil {
		return false
	}
	return env.Event == "message.part.delta"
}
