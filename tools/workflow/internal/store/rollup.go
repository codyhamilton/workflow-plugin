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

// The hourly conversations rollup (migration 7): one row per distinct (hour, harness, repo_id,
// model, conversation_id) that saw a fact, with n facts collapsed into it. The conversations
// measure is a DISTINCT count, so unlike the hook_events rollup its rows are read with
// count(DISTINCT conversation_id) rather than summed (measureDef.aggSQL): each row stands for the
// presence of one conversation, and reading whole interior hours from the rollup plus the two
// partial edge hours from base rows yields the exact base-row aggregate.

// convRollupUpsert increments the rollup row for one inserted fact. Append runs it in the same
// transaction as the fact insert, for every fact type the conversations measure counts.
const convRollupUpsert = `INSERT INTO conversations_hourly
	(hour,harness,repo_id,model,conversation_id,n) VALUES (?,?,?,?,?,1)
	ON CONFLICT(hour,harness,repo_id,model,conversation_id) DO UPDATE SET n=n+1`

// convRollupFill refills conversations_hourly from the base facts.
const convRollupFill = `INSERT INTO conversations_hourly
	SELECT CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, model, conversation_id, count(*)
	FROM facts
	GROUP BY CAST(ts/3600 AS INTEGER)*3600, harness, repo_id, model, conversation_id`

// convRollupColumns are the facts columns convRollupFill selects. A pre-migration-4 layout (which a
// test constructs) lacks model, so the fill is skipped there.
var convRollupColumns = []string{"ts", "harness", "repo_id", "model", "conversation_id"}

// convRollupFillApplies reports whether facts has every column the conversations rollup fill needs.
func (t *Tenant) convRollupFillApplies() (bool, error) {
	have, err := t.columns("facts")
	if err != nil {
		return false, err
	}
	for _, c := range convRollupColumns {
		if !have[c] {
			return false, nil
		}
	}
	return true, nil
}

// backfillConversationRollup fills conversations_hourly from base rows for a tenant that just
// gained the table. It is a no-op when facts predates the analytics columns, so migration 7 can
// stay plain SQL and this runs from open instead. The DELETE and the fill run in one transaction,
// as RebuildHookRollup's do, so a crash between them cannot leave the table empty.
func (t *Tenant) backfillConversationRollup() error {
	ok, err := t.convRollupFillApplies()
	if err != nil || !ok {
		return err
	}
	ctx := context.Background()
	tx, err := t.wdb.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `DELETE FROM conversations_hourly`); err != nil {
		tx.Rollback()
		return err
	}
	if _, err := tx.ExecContext(ctx, convRollupFill); err != nil {
		tx.Rollback()
		return err
	}
	return tx.Commit()
}

// convRollupIndexColumns are the facts columns the conversations page index reads. They are all
// migration-1 columns, so a test that reconstructs a version-1 ledger by dropping the extracted
// columns (kind among them) can still drop them: the index does not reference any of them, and the
// page's per-conversation kind set is read from the base table.
var convRollupIndexColumns = []string{"ts", "type", "conversation_id", "repo_id"}

// ensureConversationRollupIndex creates, once, the covering index the conversations page read
// (/v1/analytics/conversations) uses to group the window by conversation_id. It is ensured on every
// open rather than only when migration 7 first applies, so an index whose creation failed on an
// earlier open is still built. It is created here rather than in the migration slice because a
// pre-migration-4 test layout lacks the columns. ANALYZE runs only when this call creates the index,
// so a normal open does not re-ANALYZE; without stats the planner keeps facts_ts and a wide window
// misses the bound. It is a no-op once the index exists.
func (t *Tenant) ensureConversationRollupIndex() error {
	have, err := t.columns("facts")
	if err != nil {
		return err
	}
	for _, c := range convRollupIndexColumns {
		if !have[c] {
			return nil
		}
	}
	var n int
	if err := t.wdb.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='index' AND name='facts_conv_page'`).Scan(&n); err != nil {
		return err
	}
	if n > 0 {
		return nil
	}
	if _, err := t.wdb.Exec(`CREATE INDEX IF NOT EXISTS facts_conv_page ON facts(conversation_id, ts, type, repo_id)`); err != nil {
		return err
	}
	_, err = t.wdb.Exec(`ANALYZE facts`)
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
