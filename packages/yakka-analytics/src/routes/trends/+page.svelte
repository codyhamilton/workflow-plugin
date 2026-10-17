<script lang="ts">
	import { page } from '$app/state';
	import { bucketCount, pickBucket, type Bucket } from '$lib/buckets';
	import type { TimeSeries } from '$lib/charts/options';
	import TimeChart from '$lib/charts/TimeChart.svelte';
	import { label } from '$lib/format';
	import { resolveWindow } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse, Schema } from '$lib/types';
	import type { DimKey } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';

	const ORDER: Bucket[] = ['hour', 'day', 'week', 'month'];
	const CAP = 400;
	const DAY = 86_400_000;

	let schema = $state<Schema | null>(null);
	let data = $state<QueryResponse | null>(null);

	// The measure matrix and buckets, fetched once; the client caches it by slot after that.
	$effect(() => {
		let live = true;
		getJSON<Schema>('trends-schema', 'analytics/schema', new URLSearchParams()).then(
			(s) => {
				if (live) schema = s;
			},
			(e) => {
				if (live && !(e instanceof Superseded)) schema = null;
			}
		);
		return () => {
			live = false;
		};
	});

	const measures = $derived(schema?.measures ?? []);
	const metric = $derived.by(() => {
		const m = page.url.searchParams.get('metric') ?? '';
		return measures.some((x) => x.name === m) ? m : 'hook_events';
	});
	const dims = $derived(measures.find((m) => m.name === metric)?.dims ?? []);
	// A group is only offered when it is a dimension of the chosen measure, so an unsupported
	// measure x dim pairing (a server 400) cannot be selected.
	const groups = $derived(['none', ...dims]);
	const group = $derived.by(() => {
		const g = page.url.searchParams.get('group') ?? 'none';
		return groups.includes(g) ? g : 'none';
	});
	const chartStyle = $derived.by(() => {
		const c = page.url.searchParams.get('chart');
		return c === 'area' ? 'area' : 'line';
	});

	// The chart window. /query takes `all=1`, but over the whole ledger every time bucket exceeds
	// the 400-bucket cap (the server answers 400 "range too wide"), so All time uses the same
	// 399-day clamp the rest routes take. Without this the control could offer no bucket at all.
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
	// The finest bucket in range, or the bucket from the URL when it is still in range.
	const bucket = $derived.by(() => {
		if (!window) return 'day' as Bucket;
		const want = page.url.searchParams.get('bucket') as Bucket | null;
		if (want && offered.includes(want)) return want;
		return pickBucket(window.from, window.to, view.tz) ?? offered[0] ?? 'month';
	});

	function queryParams(): URLSearchParams | null {
		const extra: Record<string, string> = { measure: metric, bucket, top: '8' };
		if (group !== 'none') extra.dim = group;
		const p = view.paramsFor('query', extra);
		if (!p) return null;
		if (view.state.range === 'all' && window) {
			p.delete('all');
			p.set('from', window.from.toISOString());
			p.set('to', window.to.toISOString());
		}
		return p;
	}

	$effect(() => {
		if (!schema) return;
		const p = queryParams();
		if (!p) {
			data = null;
			return;
		}
		let live = true;
		getJSON<QueryResponse>('trends-main', 'analytics/query', p).then(
			(r) => {
				if (!live) return;
				clearError();
				data = r;
			},
			(e) => {
				if (!live || e instanceof Superseded) return;
				data = null;
				setError(e);
			}
		);
		return () => {
			live = false;
		};
	});

	const built = $derived(data ? buildSeries(data) : { series: [], drillByName: new Map<string, string>() });
	const series = $derived(built.series);
	const drillByName = $derived(built.drillByName);
	const chartBucket = $derived((data?.bucket ?? 'day') as Bucket);
	const stackedArea = $derived(chartStyle === 'area' && group !== 'none' && series.length > 1);

	function setMetric(v: string) {
		view.setParam('metric', v);
	}
	function setGroup(v: string) {
		view.setParam('group', v === 'none' ? null : v);
	}
	function setBucket(v: string) {
		view.setParam('bucket', v);
	}
	function setChartStyle(v: string) {
		view.setParam('chart', v === 'line' ? null : v);
	}

	function onSeries({ key, shift }: { key: string; shift: boolean }) {
		if (group === 'none') return;
		const raw = drillByName.get(key) ?? key;
		if (raw === '__other__' || raw === '') return;
		view.drill(group as DimKey, raw, { shift });
	}

	function pad(n: number): string {
		return String(n).padStart(2, '0');
	}

	/** The wall-clock parts of `d` in `tz`. */
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

	/** The instant at local `y-m-d` (hour h) in `tz`, by iterating the offset over DST. */
	function localInstant(tz: string, y: number, m: number, d: number, h = 0): Date {
		let ts = Date.UTC(y, m - 1, d, h);
		for (let i = 0; i < 3; i++) {
			const next = Date.UTC(y, m - 1, d, h) - offsetMs(tz, new Date(ts));
			if (next === ts) break;
			ts = next;
		}
		return new Date(ts);
	}

	/** A bucket boundary as the server emits it (RFC3339 in `tz`, `Z` for UTC). */
	function instantKey(tz: string, d: Date): string {
		const p = partsIn(tz, d);
		const off = offsetMs(tz, d);
		const date = `${p.y}-${pad(p.m)}-${pad(p.d)}T${pad(p.h)}:00:00`;
		if (off === 0) return `${date}Z`;
		const sign = off > 0 ? '+' : '-';
		const abs = Math.abs(off);
		return `${date}${sign}${pad(Math.floor(abs / 3_600_000))}:${pad(Math.floor((abs % 3_600_000) / 60_000))}`;
	}

	/** Every bucket start between two instants, by calendar step in `tz` (DST-safe). */
	function bucketStarts(tz: string, bucket: Bucket, from: Date, to: Date): number[] {
		const p0 = partsIn(tz, from);
		let cur: Date;
		if (bucket === 'hour') cur = localInstant(tz, p0.y, p0.m, p0.d, p0.h);
		else if (bucket === 'day') cur = localInstant(tz, p0.y, p0.m, p0.d);
		else if (bucket === 'week') {
			const wd = (new Date(Date.UTC(p0.y, p0.m - 1, p0.d)).getUTCDay() + 6) % 7;
			const mon = new Date(Date.UTC(p0.y, p0.m - 1, p0.d) - wd * DAY);
			cur = localInstant(tz, mon.getUTCFullYear(), mon.getUTCMonth() + 1, mon.getUTCDate());
		} else cur = localInstant(tz, p0.y, p0.m, 1);
		const out: number[] = [];
		const end = to.getTime();
		for (let guard = 0; cur.getTime() <= end && guard < 10_000; guard++) {
			out.push(cur.getTime());
			const p = partsIn(tz, cur);
			if (bucket === 'hour') cur = localInstant(tz, p.y, p.m, p.d, p.h + 1);
			else if (bucket === 'day') cur = localInstant(tz, p.y, p.m, p.d + 1);
			else if (bucket === 'week') cur = localInstant(tz, p.y, p.m, p.d + 7);
			else cur = localInstant(tz, p.m === 12 ? p.y + 1 : p.y, p.m === 12 ? 1 : p.m + 1, 1);
		}
		return out;
	}

	/**
	 * One `TimeSeries` per key, with a point for every bucket from the earliest to the latest `t`
	 * in the window. A bucket the API omits (no rows) becomes 0, so a gap reads as zero and not as
	 * a join. Keys come back top-N ordered; the empty key list is the whole-window series `all`.
	 */
	function buildSeries(resp: QueryResponse): { series: TimeSeries[]; drillByName: Map<string, string> } {
		const by = new Map<string, Map<number, { t: string; v: number }>>();
		const drillByName = new Map<string, string>();
		let lo = Infinity;
		let hi = -Infinity;
		for (const r of resp.rows) {
			if (!r.t) continue;
			const e = Date.parse(r.t);
			if (Number.isNaN(e)) continue;
			lo = Math.min(lo, e);
			hi = Math.max(hi, e);
			const name = r.k.length ? r.k.map(label).join(' / ') : 'all';
			if (r.k.length === 1) drillByName.set(name, r.k[0] ?? '');
			else if (r.k.length > 1) drillByName.set(name, r.k.join(' / '));
			let m = by.get(name);
			if (!m) by.set(name, (m = new Map()));
			m.set(e, { t: r.t, v: r.v });
		}
		if (!Number.isFinite(lo)) return { series: [], drillByName };
		const starts = bucketStarts(view.tz, (resp.bucket as Bucket) ?? 'day', new Date(lo), new Date(hi));
		const out: TimeSeries[] = [];
		for (const [name, m] of by) {
			out.push({
				name,
				points: starts.map((e) => m.get(e) ?? { t: instantKey(view.tz, new Date(e)), v: 0 })
			});
		}
		return { series: out, drillByName };
	}
</script>

<h1>Trends</h1>
<div class="controls">
	<label>metric
		<select data-testid="trends-metric" value={metric} onchange={(e) => setMetric(e.currentTarget.value)}>
			{#each measures as m (m.name)}<option value={m.name}>{m.name}</option>{/each}
		</select>
	</label>
	<label>bucket
		<select data-testid="trends-bucket" value={bucket} onchange={(e) => setBucket(e.currentTarget.value)}>
			{#each offered as b (b)}<option value={b}>{b}</option>{/each}
		</select>
	</label>
	<label>group
		<select data-testid="trends-group" value={group} onchange={(e) => setGroup(e.currentTarget.value)}>
			{#each groups as g (g)}<option value={g}>{g}</option>{/each}
		</select>
	</label>
	{#if group !== 'none' && series.length > 1}
		<label>chart
			<select
				data-testid="trends-chart-style"
				value={chartStyle}
				onchange={(e) => setChartStyle(e.currentTarget.value)}
			>
				<option value="line">line</option>
				<option value="area">stacked area</option>
			</select>
		</label>
	{/if}
</div>

{#if data}
	<TimeChart
		testid="trends-chart"
		{series}
		bucket={chartBucket}
		stacked={stackedArea}
		area={stackedArea}
		filterDim={group !== 'none' ? (group as DimKey) : undefined}
		onseries={group !== 'none' ? onSeries : undefined}
		onbrush={({ from, to }) => view.setWindow(from, to)}
	/>
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
