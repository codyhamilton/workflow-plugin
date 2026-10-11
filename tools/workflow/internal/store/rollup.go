package store

import "context"

// The hourly hook_events rollup (migration 6): one row per distinct (hour, dimension tuple) with
// the count of facts that collapsed into it. It exists because aggregating the base table for the
// hook_events measure misses the phase-3 read bound on large windows; the query package reads the
// rollup for whole interior hours and base rows for the two partial edge hours (measureDef.source).

// hookRollupUpsert increments the rollup row for one inserted fact. Append runs it in the same
// transaction as the fact insert, and only for a fact that was actually inserted, so a duplicate
// that collapses on the row-hash primary key adds nothing to either table.
const hookRollupUpsert = `INSERT INTO hook_events_hourly
	(hour,harness,repo_id,norm_event,event,tool,conversation_id,n) VALUES (?,?,?,?,?,?,?,1)
	ON CONFLICT(hour,harness,repo_id,norm_event,event,tool,conversation_id) DO UPDATE SET n=n+1`

// hookRollupFill refills hook_events_hourly from the base hook_event rows: it is the one aggregate
// whose result defines the rollup, shared by the open-time backfill and the post-compaction rebuild.
const hookRollupFill = `INSERT INTO hook_events_hourly
	SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, norm_event, event, tool, conversation_id, count(*)
	FROM facts WHERE type='hook_event'
	GROUP BY CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, norm_event, event, tool, conversation_id`

// hookRollupColumns are the facts columns hookRollupFill selects. A pre-migration-4 layout (which a
// test constructs) lacks them, so the fill is skipped there.
var hookRollupColumns = []string{"ts", "harness", "repo_id", "norm_event", "event", "tool", "conversation_id"}

// rollupFillApplies reports whether facts has every column the rollup fill needs.
func (t *Tenant) rollupFillApplies() (bool, error) {
	have, err := t.columns("facts")
	if err != nil {
		return false, err
	}
	for _, c := range hookRollupColumns {
		if !have[c] {
			return false, nil
		}
	}
	return true, nil
}

// backfillHookRollup fills hook_events_hourly from base rows for a tenant that just gained the
// table. It is a no-op when facts predates the extracted columns, which the pre-migration-4 layout
// a test constructs does, so the migration stays plain SQL and this runs from open instead.
func (t *Tenant) backfillHookRollup() error {
	ok, err := t.rollupFillApplies()
	if err != nil || !ok {
		return err
	}
	_, err = t.wdb.Exec(`DELETE FROM hook_events_hourly;` + hookRollupFill)
	return err
}

// RebuildHookRollup deletes every hook_events_hourly row and refills it from the base hook_event
// rows in one transaction, so the rollup equals the base-row aggregate again after a writer that
// bypasses Append (compaction). It is a no-op when facts predates the analytics columns.
func (t *Tenant) RebuildHookRollup(ctx context.Context) error {
	ok, err := t.rollupFillApplies()
	if err != nil || !ok {
		return err
	}
	tx, err := t.wdb.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `DELETE FROM hook_events_hourly`); err != nil {
		tx.Rollback()
		return err
	}
	if _, err := tx.ExecContext(ctx, hookRollupFill); err != nil {
		tx.Rollback()
		return err
	}
	return tx.Commit()
}

// columns returns the set of column names of a table.
func (t *Tenant) columns(table string) (map[string]bool, error) {
	rows, err := t.wdb.Query(`SELECT name FROM pragma_table_info(?)`, table)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[string]bool{}
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return nil, err
		}
		out[name] = true
	}
	return out, rows.Err()
}
