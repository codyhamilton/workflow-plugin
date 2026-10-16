<script lang="ts">
	import { page } from '$app/state';
	import { bucketCount, pickBucket, type Bucket } from '$lib/buckets';
	import BarChart from '$lib/charts/BarChart.svelte';
	import type { TimeSeries } from '$lib/charts/options';
	import TimeChart from '$lib/charts/TimeChart.svelte';
	import Treemap from '$lib/charts/Treemap.svelte';
	import type { BarRow, TreemapNode } from '$lib/charts/options';
	import { label } from '$lib/format';
	import { resolveWindow } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse } from '$lib/types';
	import type { DimKey } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';

	const ORDER: Bucket[] = ['hour', 'day', 'week', 'month'];
	const CAP = 400;
	const DAY = 86_400_000;
	const SPLIT_DIMS = ['norm_event', 'tool'] as const;
	type SplitDim = (typeof SPLIT_DIMS)[number];

	// Four bars, one per dimension. The 20-key cap folds the tail into `__other__`, which every
	// chart and the table mark inert.
	const BARS: { testid: string; dim: DimKey }[] = [
		{ testid: 'hooks-harness', dim: 'harness' },
		{ testid: 'hooks-repo_id', dim: 'repo_id' },
		{ testid: 'hooks-event', dim: 'event' },
		{ testid: 'hooks-tool', dim: 'tool' }
	];
	// `/query` takes at most two dims, so the design's harness → norm_event → tool tree is two
	// linked two-level treemaps: A is harness → norm_event, B is norm_event → tool.
	const TREEMAPS: { testid: string; dims: [DimKey, DimKey] }[] = [
		{ testid: 'hooks-treemap-a', dims: ['harness', 'norm_event'] },
		{ testid: 'hooks-treemap-b', dims: ['norm_event', 'tool'] }
	];

	let bars = $state<Record<string, BarRow[]>>({});
	let trees = $state<Record<string, TreemapNode[]>>({});
	let tsData = $state<QueryResponse | null>(null);
	let failure = $state<unknown>(null);
	// Charts mount only once every request for the current view has settled, so a chart never
	// reports ready while it is still empty (`expectSettled` would otherwise pass too early).
	let loaded = $state(false);

	const splitDim = $derived.by((): SplitDim => {
		const want = page.url.searchParams.get('split') ?? 'norm_event';
		return SPLIT_DIMS.includes(want as SplitDim) ? (want as SplitDim) : 'norm_event';
	});

	const window = $derived.by(() => {
		const now = new Date();
		const q = resolveWindow(view.state, now, view.tz, 'query');
		if (q.all) {
			const r = resolveWindow(view.state, now, view.tz, 'rest');
			return r.from && r.to ? { from: r.from, to: r.to } : null;
		}
		return q.from && q.to ? { from: q.from, to: q.to } : null;
	});
	const offered = $derived.by(() =>
		window ? ORDER.filter((b) => bucketCount(b, window.from, window.to, view.tz) <= CAP) : []
	);
	const bucket = $derived.by(() => {
		if (!window) return 'day' as Bucket;
		const want = page.url.searchParams.get('bucket') as Bucket | null;
		if (want && offered.includes(want)) return want;
		return pickBucket(window.from, window.to, view.tz) ?? offered[0] ?? 'month';
	});

	const tsSeries = $derived(tsData ? buildSeries(tsData) : []);
	const chartBucket = $derived((tsData?.bucket ?? bucket) as Bucket);

	function barRows(resp: QueryResponse): BarRow[] {
		return resp.rows.map((r) => ({ key: r.k[0] ?? '', label: label(r.k[0]), value: r.v }));
	}

	// Fold the two-key rows into parent → leaf nodes, keeping first-seen order.
	function treeNodes(resp: QueryResponse): TreemapNode[] {
		const nodes = new Map<string, TreemapNode>();
		const order: string[] = [];
		for (const r of resp.rows) {
			const a = r.k[0] ?? '';
			const b = r.k[1] ?? '';
			let node = nodes.get(a);
			if (!node) {
				node = { name: a, children: [] };
				nodes.set(a, node);
				order.push(a);
			}
			node.children!.push({ name: b, value: r.v });
		}
		return order.map((a) => nodes.get(a)!);
	}

	function tsQueryParams(): URLSearchParams | null {
		const p = view.paramsFor('query', {
			measure: 'hook_events',
			dim: splitDim,
			bucket,
			top: '8'
		});
		if (!p) return null;
		if (view.state.range === 'all' && window) {
			p.delete('all');
			p.set('from', window.from.toISOString());
			p.set('to', window.to.toISOString());
		}
		return p;
	}

	function setSplit(v: string) {
		view.setParam('split', v === 'norm_event' ? null : v);
	}
	function setBucket(v: string) {
		view.setParam('bucket', v);
	}

	function pad(n: number): string {
		return String(n).padStart(2, '0');
	}

	function partsIn(tz: string, d: Date) {
		const out: Record<string, number> = {};
		for (const p of new Intl.DateTimeFormat('en-US', {
			timeZone: tz,
			hourCycle: 'h23',
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit'
		}).formatToParts(d))
			if (p.type !== 'literal') out[p.type] = Number(p.value);
		return { y: out.year, m: out.month, d: out.day, h: out.hour };
	}

	function offsetMs(tz: string, d: Date): number {
		const p = partsIn(tz, d);
		return Date.UTC(p.y, p.m - 1, p.d, p.h) - d.getTime();
	}

	function localInstant(tz: string, y: number, m: number, d: number, h = 0): Date {
		let ts = Date.UTC(y, m - 1, d, h);
		for (let i = 0; i < 3; i++) {
			const next = Date.UTC(y, m - 1, d, h) - offsetMs(tz, new Date(ts));
			if (next === ts) break;
			ts = next;
		}
		return new Date(ts);
	}

	function instantKey(tz: string, d: Date): string {
		const p = partsIn(tz, d);
		const off = offsetMs(tz, d);
		const date = `${p.y}-${pad(p.m)}-${pad(p.d)}T${pad(p.h)}:00:00`;
		if (off === 0) return `${date}Z`;
		const sign = off > 0 ? '+' : '-';
		const abs = Math.abs(off);
		return `${date}${sign}${pad(Math.floor(abs / 3_600_000))}:${pad(Math.floor((abs % 3_600_000) / 60_000))}`;
	}

	function bucketStarts(tz: string, b: Bucket, from: Date, to: Date): number[] {
		const p0 = partsIn(tz, from);
		let cur: Date;
		if (b === 'hour') cur = localInstant(tz, p0.y, p0.m, p0.d, p0.h);
		else if (b === 'day') cur = localInstant(tz, p0.y, p0.m, p0.d);
		else if (b === 'week') {
			const wd = (new Date(Date.UTC(p0.y, p0.m - 1, p0.d)).getUTCDay() + 6) % 7;
			const mon = new Date(Date.UTC(p0.y, p0.m - 1, p0.d) - wd * DAY);
			cur = localInstant(tz, mon.getUTCFullYear(), mon.getUTCMonth() + 1, mon.getUTCDate());
		} else cur = localInstant(tz, p0.y, p0.m, 1);
		const out: number[] = [];
		const end = to.getTime();
		for (let guard = 0; cur.getTime() <= end && guard < 10_000; guard++) {
			out.push(cur.getTime());
			const p = partsIn(tz, cur);
			if (b === 'hour') cur = localInstant(tz, p.y, p.m, p.d, p.h + 1);
			else if (b === 'day') cur = localInstant(tz, p.y, p.m, p.d + 1);
			else if (b === 'week') cur = localInstant(tz, p.y, p.m, p.d + 7);
			else cur = localInstant(tz, p.m === 12 ? p.y + 1 : p.y, p.m === 12 ? 1 : p.m + 1, 1);
		}
		return out;
	}

	/** Zero-fill gaps; series names use raw API keys so series drill matches `/query` filters. */
	function buildSeries(resp: QueryResponse): TimeSeries[] {
		const by = new Map<string, Map<number, { t: string; v: number }>>();
		let lo = Infinity;
		let hi = -Infinity;
		for (const r of resp.rows) {
			if (!r.t) continue;
			const e = Date.parse(r.t);
			if (Number.isNaN(e)) continue;
			lo = Math.min(lo, e);
			hi = Math.max(hi, e);
			const name = r.k.length ? (r.k[0] ?? '') : 'all';
			let m = by.get(name);
			if (!m) by.set(name, (m = new Map()));
			m.set(e, { t: r.t, v: r.v });
		}
		if (!Number.isFinite(lo)) return [];
		const starts = bucketStarts(view.tz, (resp.bucket as Bucket) ?? bucket, new Date(lo), new Date(hi));
		const out: TimeSeries[] = [];
		for (const [name, m] of by) {
			out.push({
				name: name === '' ? '(none)' : name,
				points: starts.map((e) => m.get(e) ?? { t: instantKey(view.tz, new Date(e)), v: 0 })
			});
		}
		return out;
	}

	function seriesDrillKey(display: string): string {
		return display === '(none)' ? '' : display;
	}

	// Six `/query` calls on one view change plus the time series. Facets gate the first wave so one
	// load issues each request once (the URL alone does not change under them).
	$effect(() => {
		if (!view.facets) return;
		const jobs: Promise<void>[] = [];
		for (const { testid, dim } of BARS) {
			const params = view.paramsFor('query', {
				measure: 'hook_events',
				dim,
				bucket: 'none',
				top: '20'
			});
			if (!params) continue;
			jobs.push(
				getJSON<QueryResponse>(testid, 'analytics/query', params).then(
					(resp) => {
						bars[testid] = barRows(resp);
					},
					(e) => {
						if (!(e instanceof Superseded)) failure = e;
					}
				)
			);
		}
		for (const { testid, dims } of TREEMAPS) {
			const params = view.paramsFor('query', { measure: 'hook_events', dim: dims, bucket: 'none' });
			if (!params) continue;
			jobs.push(
				getJSON<QueryResponse>(testid, 'analytics/query', params).then(
					(resp) => {
						trees[testid] = treeNodes(resp);
					},
					(e) => {
						if (!(e instanceof Superseded)) failure = e;
					}
				)
			);
		}
		const tsp = tsQueryParams();
		if (tsp) {
			jobs.push(
				getJSON<QueryResponse>('hooks-over-time', 'analytics/query', tsp).then(
					(resp) => {
						tsData = resp;
					},
					(e) => {
						if (!(e instanceof Superseded)) failure = e;
					}
				)
			);
		}
		let live = true;
		loaded = false;
		let remaining = jobs.length;
		if (remaining === 0) {
			loaded = true;
			return;
		}
		for (const job of jobs)
			job.finally(() => {
				if (live && --remaining === 0) loaded = true;
			});
		return () => {
			live = false;
		};
	});

	$effect(() => {
		if (failure) setError(failure);
		else clearError();
	});

	// A bar click drills one dimension. A treemap path drills every level; `/query` allows two dims
	// but `view.drill` navigates once per call, so the tail waits for the first navigation to land.
	type Step = { dim: DimKey; value: string; shift: boolean };
	let pending: Step[] = [];

	function drillPath(dims: DimKey[], path: string[], shift: boolean) {
		if (path.length === 0 || path.some((v) => v === '__other__')) return;
		view.drill(dims[0], path[0], { shift });
		pending = path.slice(1).map((value, i) => ({ dim: dims[i + 1], value, shift }));
	}

	$effect(() => {
		void view.state;
		if (pending.length > 0) {
			const [next, ...rest] = pending;
			pending = rest;
			view.drill(next.dim, next.value, { shift: next.shift });
		}
	});
</script>

<h1>Hooks</h1>
{#if loaded}
	<div class="controls">
		<label>bucket
			<select data-testid="hooks-bucket" value={bucket} onchange={(e) => setBucket(e.currentTarget.value)}>
				{#each offered as b (b)}<option value={b}>{b}</option>{/each}
			</select>
		</label>
		<label>split
			<select data-testid="hooks-split" value={splitDim} onchange={(e) => setSplit(e.currentTarget.value)}>
				{#each SPLIT_DIMS as d (d)}<option value={d}>{d}</option>{/each}
			</select>
		</label>
	</div>
	{#if tsData}
		<TimeChart
			testid="hooks-over-time"
			series={tsSeries}
			bucket={chartBucket}
			filterDim={splitDim}
			onseries={({ key, shift }) => view.drill(splitDim, seriesDrillKey(key), { shift })}
			onbrush={({ from, to }) => view.setWindow(from, to)}
		/>
	{/if}
	{#each BARS as b (b.testid)}
		<h2>{b.dim}</h2>
		<BarChart
			testid={b.testid}
			rows={bars[b.testid] ?? []}
			onselect={(d) => view.drill(b.dim, d.key, { shift: d.shift })}
		/>
	{/each}
	{#each TREEMAPS as t (t.testid)}
		<h2>{t.dims[0]} → {t.dims[1]}</h2>
		<Treemap
			testid={t.testid}
			root={trees[t.testid] ?? []}
			onselect={(d) => drillPath(t.dims, d.path, d.shift)}
		/>
	{/each}
{/if}

<style>
	.controls {
		display: flex;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	.controls label {
		display: flex;
		flex-direction: column;
		font-size: 0.8rem;
		gap: 0.25rem;
	}
</style>
