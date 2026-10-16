<script lang="ts">
	import { untrack } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { pickBucket, type Bucket } from '$lib/buckets';
	import {
		allowedBuckets,
		allowedCharts,
		allowedDims,
		configToParams,
		defaultConfig,
		isRangeOk,
		parseConfig,
		type BuilderConfig,
		type ChartKind
	} from '$lib/builder';
	import BuilderChart from '$lib/charts/BuilderChart.svelte';
	import { resolveWindow } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse, Schema } from '$lib/types';
	import { DIM_KEYS, type DimKey } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';

	const CONFIG_KEYS = ['m', 'd', 'b', 'c', 'top'];

	let schema = $state<Schema | null>(null);
	let data = $state<QueryResponse | null>(null);

	// The measure matrix and buckets, fetched once; the client caches it by slot after that.
	$effect(() => {
		let live = true;
		getJSON<Schema>('builder-schema', 'analytics/schema', new URLSearchParams()).then(
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

	// The request window. All time takes the same 399-day clamp the rest routes take; `all=1` stays
	// only when the bucket is `none` (below), so a time bucket always has an in-range window.
	const qwin = $derived.by(() => {
		const now = new Date();
		const q = resolveWindow(view.state, now, view.tz, 'query');
		if (q.all) {
			const r = resolveWindow(view.state, now, view.tz, 'rest');
			return r.from && r.to ? { from: r.from, to: r.to } : null;
		}
		return q.from && q.to ? { from: q.from, to: q.to } : null;
	});

	// An explicit `b` (including `b=none`) wins; with no `b` the finest bucket the window allows is
	// picked, as the design's "each chart picks the finest bucket within the cap unless one is set".
	function chosenBucket(fallback: Bucket): Bucket {
		const raw = page.url.searchParams.get('b');
		if (raw !== null && raw !== '') return fallback;
		if (!qwin) return 'none';
		return pickBucket(qwin.from, qwin.to, view.tz) ?? 'none';
	}

	// Defaults when the URL has no `m`: `defaultConfig`. Otherwise `parseConfig` sanitises measure,
	// dims and chart, so a pasted pairing the shape does not allow is corrected, never sent.
	const config = $derived.by<BuilderConfig | null>(() => {
		if (!schema) return null;
		const base = page.url.searchParams.has('m')
			? parseConfig(page.url.searchParams, schema)
			: defaultConfig(schema);
		const bucket = chosenBucket(base.bucket);
		const kinds = allowedCharts(base.dims.length, bucket);
		const chart: ChartKind = kinds.includes(base.chart) ? base.chart : (kinds[0] ?? base.chart);
		return { ...base, bucket, chart };
	});

	const rangeOk = $derived(config && qwin ? isRangeOk(qwin, config.bucket, view.tz) : true);
	// Each dimension select lists only the measure's dims it may still pair with, plus `none`.
	const dims1 = $derived(
		schema && config
			? ['none', ...allowedDims(schema, config.measure, config.dims[1] ? [config.dims[1]] : [])]
			: ['none']
	);
	const dims2 = $derived(
		schema && config
			? ['none', ...allowedDims(schema, config.measure, config.dims[0] ? [config.dims[0]] : [])]
			: ['none']
	);
	const buckets = $derived(schema ? allowedBuckets(schema) : []);
	const charts = $derived(config ? allowedCharts(config.dims.length, config.bucket) : []);

	$effect(() => {
		if (!schema || !config) return;
		if (!rangeOk) {
			data = null;
			return;
		}
		const cfg = config;
		const win = qwin;
		// Wait for facets of the current window when an exclude needs their complement (as Trends
		// does); `view.paramsFor` is otherwise read untracked so a late facet response cannot re-run
		// this effect and supersede a query already in flight.
		const needsFacets = Object.keys(view.state.exclude).length > 0;
		if (needsFacets && !view.facetsReady) return;
		let live = true;
		const params = untrack(() =>
			view.paramsFor('query', {
				measure: cfg.measure,
				dim: cfg.dims,
				bucket: cfg.bucket,
				top: String(cfg.top)
			})
		);
		if (!params) {
			data = null;
			return;
		}
		// `all=1` only without a time bucket; with one, clamp to the rest window from/to.
		if (cfg.bucket !== 'none' && win) {
			params.delete('all');
			params.set('from', win.from.toISOString());
			params.set('to', win.to.toISOString());
		}
		getJSON<QueryResponse>('builder-query', 'analytics/query', params).then(
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

	// One navigation per change, keeping filter params and route params. Config params are written
	// back explicitly (including `b=none`) so the choice survives a reload.
	function navigateConfig(next: BuilderConfig) {
		const q = new URLSearchParams(page.url.searchParams);
		for (const k of CONFIG_KEYS) q.delete(k);
		const p = configToParams(next);
		if (next.bucket === 'none') p.set('b', 'none');
		for (const [k, v] of p) q.append(k, v);
		const qs = q.toString();
		const suffix = qs ? `?${qs}` : '';
		if (suffix === page.url.search) return;
		goto(`${page.url.pathname}${suffix}`, { noScroll: true, keepFocus: true });
	}

	// A pairing change re-defaults the chart to the first kind the new shape offers, so two dims on
	// a time bucket default to small multiples instead of keeping a shape that no longer fits.
	function withChart(cfg: BuilderConfig): BuilderConfig {
		const kinds = allowedCharts(cfg.dims.length, cfg.bucket);
		return { ...cfg, chart: kinds[0] ?? cfg.chart };
	}

	function setMeasure(value: string) {
		if (!schema || !config) return;
		const supported = allowedDims(schema, value, []);
		const dims = config.dims.filter((d) => supported.includes(d));
		navigateConfig(withChart({ ...config, measure: value, dims }));
	}

	function setDim(index: number, value: string) {
		if (!config) return;
		const dims = [...config.dims];
		if (value === 'none') {
			if (index < dims.length) dims.splice(index, 1);
		} else if (index === 0) {
			if (dims.length === 0) dims.push(value);
			else dims[0] = value;
		} else if (dims.length < 2) {
			dims.push(value);
		} else {
			dims[1] = value;
		}
		navigateConfig(withChart({ ...config, dims }));
	}

	function setBucket(value: string) {
		if (!config) return;
		const bucket = value as Bucket;
		const kinds = allowedCharts(config.dims.length, bucket);
		const chart = kinds.includes(config.chart) ? config.chart : (kinds[0] ?? config.chart);
		navigateConfig({ ...config, bucket, chart });
	}

	function setChart(value: string) {
		if (!config) return;
		navigateConfig({ ...config, chart: value as ChartKind });
	}

	function setTop(value: string) {
		if (!config) return;
		const parsed = Number.parseInt(value, 10);
		const top = Number.isNaN(parsed) ? 20 : Math.min(100, Math.max(1, parsed));
		navigateConfig({ ...config, top });
	}

	// A mark click filters only on a real filter key; `hour_of_day`, `weekday` and `stage` are not.
	function onpick(dim: string, key: string, shift: boolean) {
		if ((DIM_KEYS as readonly string[]).includes(dim)) view.drill(dim as DimKey, key, { shift });
	}
</script>

<h1>Builder</h1>

{#if schema && config}
	<div class="controls">
		<label>measure
			<select
				data-testid="builder-measure"
				value={config.measure}
				onchange={(e) => setMeasure(e.currentTarget.value)}
			>
				{#each schema.measures as m (m.name)}<option value={m.name}>{m.name}</option>{/each}
			</select>
		</label>
		<label>dimension
			<select
				data-testid="builder-dim-1"
				value={config.dims[0] ?? 'none'}
				onchange={(e) => setDim(0, e.currentTarget.value)}
			>
				{#each dims1 as d (d)}<option value={d}>{d}</option>{/each}
			</select>
		</label>
		<label>dimension 2
			<select
				data-testid="builder-dim-2"
				value={config.dims[1] ?? 'none'}
				onchange={(e) => setDim(1, e.currentTarget.value)}
			>
				{#each dims2 as d (d)}<option value={d}>{d}</option>{/each}
			</select>
		</label>
		<label>bucket
			<select
				data-testid="builder-bucket"
				value={config.bucket}
				onchange={(e) => setBucket(e.currentTarget.value)}
			>
				{#each buckets as b (b)}<option value={b}>{b}</option>{/each}
			</select>
		</label>
		<label>chart
			<select
				data-testid="builder-chart-type"
				value={config.chart}
				onchange={(e) => setChart(e.currentTarget.value)}
			>
				{#each charts as c (c)}<option value={c}>{c}</option>{/each}
			</select>
		</label>
		<label>top
			<input
				data-testid="builder-top"
				type="number"
				min="1"
				max="100"
				value={config.top}
				onchange={(e) => setTop(e.currentTarget.value)}
			/>
		</label>
	</div>
{/if}

{#if config && !rangeOk}
	<p class="notice" data-testid="builder-notice-range">
		This bucket is too fine for the window. Choose a coarser bucket or a narrower range.
	</p>
{/if}

{#if config && rangeOk}
	<BuilderChart
		testid="builder-chart"
		{config}
		resp={data}
		onpick={onpick}
		onbrush={({ from, to }) => view.setWindow(from, to)}
	/>
{/if}

<style>
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	.controls label {
		display: flex;
		flex-direction: column;
		font-size: 0.8rem;
		gap: 0.25rem;
	}
	.notice {
		color: var(--muted);
	}
</style>
