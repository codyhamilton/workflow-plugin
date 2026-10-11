<script lang="ts">
	import { untrack } from 'svelte';
	import { pickBucket } from '$lib/buckets';
	import BarChart from '$lib/charts/BarChart.svelte';
	import TimeChart from '$lib/charts/TimeChart.svelte';
	import type { TimeSeries } from '$lib/charts/options';
	import { costLabel, label, num } from '$lib/format';
	import { resolveWindow } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse } from '$lib/types';
	import { view } from '$lib/view.svelte';

	/** One measure's rows as a `model -> value` map (the only dim this page asks for). */
	function values(resp: QueryResponse | null): Record<string, number> {
		const out: Record<string, number> = {};
		for (const row of resp?.rows ?? []) out[row.k[0] ?? ''] = row.v;
		return out;
	}

	/** `{t, k, v}` rows as time series, one per dimension key (or `fallback` when there is none). */
	function points(resp: QueryResponse | null, fallback = 'value'): TimeSeries[] {
		const byName = new Map<string, { t: string; v: number }[]>();
		for (const row of resp?.rows ?? []) {
			if (!row.t) continue;
			const name = row.k[0] || fallback;
			const list = byName.get(name) ?? [];
			list.push({ t: row.t, v: row.v });
			byName.set(name, list);
		}
		return [...byName].map(([name, pts]) => ({ name, points: pts }));
	}

	let costResp = $state<QueryResponse | null>(null);
	let callsResp = $state<QueryResponse | null>(null);
	let unpricedResp = $state<QueryResponse | null>(null);
	let tinResp = $state<QueryResponse | null>(null);
	let toutResp = $state<QueryResponse | null>(null);
	let costTimeResp = $state<QueryResponse | null>(null);
	let tokensTimeResp = $state<QueryResponse | null>(null);

	// Over the whole ledger every time bucket exceeds the API's 400-bucket cap, so All time uses the
	// same 399-day clamp the rest routes take (as Trends does): `all` becomes explicit from/to.
	const qwin = $derived.by(() => {
		const now = new Date();
		const q = resolveWindow(view.state, now, view.tz, 'query');
		if (q.all) {
			const r = resolveWindow(view.state, now, view.tz, 'rest');
			return r.from && r.to ? { from: r.from, to: r.to, all: true } : null;
		}
		return q.from && q.to ? { from: q.from, to: q.to, all: false } : null;
	});
	const bucket = $derived(qwin ? (pickBucket(qwin.from, qwin.to, view.tz) ?? 'month') : 'month');

	$effect(() => {
		const bkt = bucket;
		const win = qwin;
		// Wait for facets of the current window when an exclude needs their complement (as Overview
		// does); `view.paramsFor` is otherwise read untracked so a late facet response cannot re-run
		// this effect and supersede queries already in flight.
		const needsFacets = Object.keys(view.state.exclude).length > 0;
		if (needsFacets && !view.facetsReady) return;
		let live = true;
		const run = (slot: string, extra: Record<string, string>, set: (r: QueryResponse) => void) => {
			const params = untrack(() => view.paramsFor('query', extra));
			if (!params) return;
			if (win?.all) {
				params.delete('all');
				params.set('from', win.from.toISOString());
				params.set('to', win.to.toISOString());
			}
			getJSON<QueryResponse>(slot, 'analytics/query', params).then(
				(r) => {
					if (!live) return;
					clearError();
					set(r);
				},
				(e) => {
					if (live && !(e instanceof Superseded)) setError(e);
				}
			);
		};
		const byModel = { dim: 'model', top: '100', bucket: 'none' };
		run('usage-by-model-cost', { measure: 'cost_usd', ...byModel }, (r) => (costResp = r));
		run('usage-by-model-calls', { measure: 'model_calls', ...byModel }, (r) => (callsResp = r));
		run('usage-by-model-unpriced', { measure: 'unpriced_calls', ...byModel }, (r) => (unpricedResp = r));
		run('usage-by-model-tokens-in', { measure: 'tokens_in', ...byModel }, (r) => (tinResp = r));
		run('usage-by-model-tokens-out', { measure: 'tokens_out', ...byModel }, (r) => (toutResp = r));
		run('usage-over-time', { measure: 'cost_usd', dim: 'model', bucket: bkt }, (r) => (costTimeResp = r));
		run('usage-tokens-over-time', { measure: 'tokens_out', bucket: bkt }, (r) => (tokensTimeResp = r));
		return () => {
			live = false;
		};
	});

	const costBy = $derived(values(costResp));
	const callsBy = $derived(values(callsResp));
	const unpricedBy = $derived(values(unpricedResp));
	const tinBy = $derived(values(tinResp));
	const toutBy = $derived(values(toutResp));

	const models = $derived.by(() => {
		const seen = new Set<string>();
		for (const resp of [costResp, callsResp, unpricedResp, tinResp, toutResp])
			for (const row of resp?.rows ?? []) seen.add(row.k[0] ?? '');
		return [...seen];
	});

	const totalCalls = $derived(models.reduce((n, m) => n + (callsBy[m] ?? 0), 0));
	const totalUnpriced = $derived(models.reduce((n, m) => n + (unpricedBy[m] ?? 0), 0));

	const costRows = $derived(
		models.map((m) => {
			const cost = costBy[m] ?? 0;
			const unpriced = unpricedBy[m] ?? 0;
			return { key: m, label: cost === 0 && unpriced > 0 ? `${m} (unpriced)` : m, value: cost };
		})
	);
	const OTHER = '__other__';

	/** A per-measure cell: an absent key means zero/not-applicable for that measure, shown as `—`. */
	function cell(map: Record<string, number>, key: string): string {
		return key in map ? num(map[key]) : '—';
	}

	/** `__other__` (the folded tail) and the empty key are display-only, never drill targets. */
	function rowLabel(key: string): string {
		return key === OTHER ? 'other models' : label(key);
	}
	function rowInert(key: string): boolean {
		return key === OTHER || key === '';
	}
	const costSeries = $derived(points(costTimeResp));
	const tokenSeries = $derived(points(tokensTimeResp, 'tokens_out'));

	function pick(key: string, shift: boolean) {
		if (key === '__other__') return;
		// A bar with no priced cost is unpriced, not free: it does not filter.
		if ((costBy[key] ?? 0) === 0 && (unpricedBy[key] ?? 0) > 0) return;
		view.drill('model', key, { shift });
	}

	function cost(m: string): string {
		const c = costBy[m] ?? 0;
		const u = unpricedBy[m] ?? 0;
		// costLabel only says "unpriced" when unpriced >= calls; a folded `__other__` row can have
		// fewer unpriced than calls and would otherwise read `$0.00`. Guard that here (format.ts is
		// owned by 5-14).
		if (c === 0 && u > 0) return 'unpriced';
		return costLabel({ cost: c, unpriced: u, calls: callsBy[m] ?? 0 });
	}
</script>

<h1>Usage &amp; cost</h1>

{#if totalUnpriced > 0}
	<p class="banner" data-testid="usage-unpriced-banner">
		{totalUnpriced} of {totalCalls} calls are unpriced
	</p>
{/if}

<table data-testid="usage-table">
	<thead>
		<tr>
			<th>model</th><th>calls</th><th>unpriced</th><th>tokens in</th><th>tokens out</th><th>cost</th>
		</tr>
	</thead>
	<tbody>
		{#each models as m (m)}
			<tr
				data-testid="usage-row-{m}"
				class:inert={rowInert(m)}
				onclick={(e) => {
					if (!rowInert(m)) view.drill('model', m, { shift: e.shiftKey });
				}}
			>
				<th scope="row">{rowLabel(m)}</th>
				<td data-testid="usage-{m}-calls">{cell(callsBy, m)}</td>
				<td data-testid="usage-{m}-unpriced">{cell(unpricedBy, m)}</td>
				<td data-testid="usage-{m}-tokens_in">{cell(tinBy, m)}</td>
				<td data-testid="usage-{m}-tokens_out">{cell(toutBy, m)}</td>
				<td data-testid="usage-{m}-cost">{cost(m)}</td>
			</tr>
		{/each}
	</tbody>
</table>
{#if models.includes(OTHER)}
	<p class="footnote" data-testid="usage-truncated-note">
		Table truncated to 100 models; "other models" folds the rest.
	</p>
{/if}
<p class="footnote" data-testid="usage-footnote">Claude calls captured live may be counted more than once</p>

<h2>Cost by model</h2>
<BarChart testid="usage-cost-by-model" rows={costRows} unit="usd" selectable onselect={({ key, shift }) => pick(key, shift)} />

<h2>Cost over time</h2>
<TimeChart testid="usage-over-time" series={costSeries} {bucket} stacked />

<h2>Tokens out over time</h2>
<TimeChart testid="usage-tokens-over-time" series={tokenSeries} {bucket} />

<style>
	.banner {
		margin: 0 0 0.75rem;
		padding: 0.4rem 0.75rem;
		border: 1px solid var(--border);
		background: var(--surface);
	}
	.footnote {
		color: var(--muted);
		font-size: 0.8rem;
	}
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: right;
		border-bottom: 1px solid var(--border);
		font-variant-numeric: tabular-nums;
	}
	th[scope='row'] {
		text-align: left;
	}
	tr.inert {
		color: var(--muted);
		cursor: default;
	}
</style>
