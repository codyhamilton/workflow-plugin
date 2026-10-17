<script lang="ts">
	import { untrack } from 'svelte';
	import { bucketCount, pickBucket, type Bucket } from '$lib/buckets';
	import { isRangeOk } from '$lib/builder';
	import { builderConfigFromTileParams, hooksSplitFromTileParams } from '$lib/dashboard-tile';
	import BarChart from '$lib/charts/BarChart.svelte';
	import BoxChart from '$lib/charts/BoxChart.svelte';
	import BuilderChart from '$lib/charts/BuilderChart.svelte';
	import DistributionChart from '$lib/charts/DistributionChart.svelte';
	import type { DistributionMeasure } from '$lib/charts/distribution';
	import SankeyChart from '$lib/charts/SankeyChart.svelte';
	import type { SankeyLink } from '$lib/charts/sankey';
	import ScoreBandChart from '$lib/charts/ScoreBandChart.svelte';
	import Sparkline from '$lib/charts/Sparkline.svelte';
	import TimeChart from '$lib/charts/TimeChart.svelte';
	import Treemap from '$lib/charts/Treemap.svelte';
	import type { BarRow, TimeSeries, TreemapNode } from '$lib/charts/options';
	import { bucketStarts, instantKey } from '$lib/charts/score-series';
	import { label, num } from '$lib/format';
	import { resolveWindow, scoreSeriesParams, scoresParams } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type {
		Baselines,
		DistributionResponse,
		Executions,
		Explore,
		QueryResponse,
		Schema,
		ScoreSeries,
		Scores,
		Summary
	} from '$lib/types';
	import type { DimKey } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';
	import type { SavedView } from '$lib/views';
	import { DIM_KEYS } from '$lib/urlstate';

	let { view: saved, testid: testidSuffix = '' }: { view: SavedView; testid?: string } = $props();

	const rootTestId = $derived(testidSuffix ? `dash-tile-chart-${testidSuffix}` : 'dash-tile-chart');
	const tileParams = $derived(saved.params);
	const report = $derived(saved.report);

	// --- Hooks tile (same charts as /hooks, params from saved view) ---
	const HOOKS_BARS: { testid: string; dim: DimKey }[] = [
		{ testid: 'hooks-harness', dim: 'harness' },
		{ testid: 'hooks-repo_id', dim: 'repo_id' },
		{ testid: 'hooks-event', dim: 'event' },
		{ testid: 'hooks-tool', dim: 'tool' }
	];
	const HOOKS_TREES: { testid: string; dims: [DimKey, DimKey] }[] = [
		{ testid: 'hooks-treemap-a', dims: ['harness', 'norm_event'] },
		{ testid: 'hooks-treemap-b', dims: ['norm_event', 'tool'] }
	];
	const HOOKS_ORDER: Bucket[] = ['hour', 'day', 'week', 'month'];
	const HOOKS_CAP = 400;

	let hooksBars = $state<Record<string, BarRow[]>>({});
	let hooksTrees = $state<Record<string, TreemapNode[]>>({});
	let hooksTs = $state<QueryResponse | null>(null);
	let hooksLoaded = $state(false);

	const hooksSplit = $derived(hooksSplitFromTileParams(tileParams));
	const hooksWindow = $derived.by(() => {
		const now = new Date();
		const q = resolveWindow(view.state, now, view.tz, 'query');
		if (q.all) {
			const r = resolveWindow(view.state, now, view.tz, 'rest');
			return r.from && r.to ? { from: r.from, to: r.to } : null;
		}
		return q.from && q.to ? { from: q.from, to: q.to } : null;
	});
	const hooksOffered = $derived.by(() =>
		hooksWindow
			? HOOKS_ORDER.filter((b) => bucketCount(b, hooksWindow.from, hooksWindow.to, view.tz) <= HOOKS_CAP)
			: []
	);
	const hooksBucket = $derived.by(() => {
		if (!hooksWindow) return 'day' as Bucket;
		const want = typeof tileParams.bucket === 'string' ? tileParams.bucket : null;
		if (want && hooksOffered.includes(want as Bucket)) return want as Bucket;
		return pickBucket(hooksWindow.from, hooksWindow.to, view.tz) ?? hooksOffered[0] ?? 'month';
	});

	function hooksBarRows(resp: QueryResponse): BarRow[] {
		return resp.rows.map((r) => ({ key: r.k[0] ?? '', label: label(r.k[0]), value: r.v }));
	}
	function hooksTreeNodes(resp: QueryResponse): TreemapNode[] {
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
	function hooksBuildSeries(resp: QueryResponse, bkt: Bucket): TimeSeries[] {
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
		const starts = bucketStarts(view.tz, (resp.bucket as Bucket) ?? bkt, new Date(lo), new Date(hi));
		const out: TimeSeries[] = [];
		for (const [name, m] of by) {
			out.push({
				name: name === '' ? '(none)' : name,
				points: starts.map((e) => m.get(e) ?? { t: instantKey(view.tz, new Date(e)), v: 0 })
			});
		}
		return out;
	}
	function hooksTsParams(): URLSearchParams | null {
		const p = view.paramsFor('query', {
			measure: 'hook_events',
			dim: hooksSplit,
			bucket: hooksBucket,
			top: '8'
		});
		if (!p) return null;
		if (view.state.range === 'all' && hooksWindow) {
			p.delete('all');
			p.set('from', hooksWindow.from.toISOString());
			p.set('to', hooksWindow.to.toISOString());
		}
		return p;
	}
	type HookStep = { dim: DimKey; value: string; shift: boolean };
	let hooksPending = $state<HookStep[]>([]);
	function hooksDrillPath(dims: DimKey[], path: string[], shift: boolean) {
		if (path.length === 0 || path.some((v) => v === '__other__')) return;
		view.drill(dims[0], path[0], { shift });
		hooksPending = path.slice(1).map((value, i) => ({ dim: dims[i + 1], value, shift }));
	}
	$effect(() => {
		void view.state;
		if (hooksPending.length > 0) {
			const [next, ...rest] = hooksPending;
			hooksPending = rest;
			view.drill(next.dim, next.value, { shift: next.shift });
		}
	});
	$effect(() => {
		if (report !== 'hooks' || !view.facets) return;
		const jobs: Promise<void>[] = [];
		for (const { testid, dim } of HOOKS_BARS) {
			const params = view.paramsFor('query', {
				measure: 'hook_events',
				dim,
				bucket: 'none',
				top: '20'
			});
			if (!params) continue;
			jobs.push(
				getJSON<QueryResponse>(`tile-${testid}`, 'analytics/query', params).then(
					(resp) => {
						hooksBars[testid] = hooksBarRows(resp);
					},
					() => {}
				)
			);
		}
		for (const { testid, dims } of HOOKS_TREES) {
			const params = view.paramsFor('query', {
				measure: 'hook_events',
				dim: dims,
				bucket: 'none'
			});
			if (!params) continue;
			jobs.push(
				getJSON<QueryResponse>(`tile-${testid}`, 'analytics/query', params).then(
					(resp) => {
						hooksTrees[testid] = hooksTreeNodes(resp);
					},
					() => {}
				)
			);
		}
		const tsp = hooksTsParams();
		if (tsp) {
			jobs.push(
				getJSON<QueryResponse>('tile-hooks-over-time', 'analytics/query', tsp).then(
					(resp) => {
						hooksTs = resp;
					},
					() => {}
				)
			);
		}
		let live = true;
		hooksLoaded = false;
		let remaining = jobs.length;
		if (remaining === 0) hooksLoaded = true;
		for (const job of jobs)
			job.finally(() => {
				if (live && --remaining === 0) hooksLoaded = true;
			});
		return () => {
			live = false;
		};
	});

	// --- Builder tile ---
	let builderSchema = $state<Schema | null>(null);
	let builderData = $state<QueryResponse | null>(null);
	const builderConfig = $derived(
		builderSchema ? builderConfigFromTileParams(tileParams, builderSchema) : null
	);
	const builderWin = $derived.by(() => {
		const now = new Date();
		const q = resolveWindow(view.state, now, view.tz, 'query');
		if (q.all) {
			const r = resolveWindow(view.state, now, view.tz, 'rest');
			return r.from && r.to ? { from: r.from, to: r.to } : null;
		}
		return q.from && q.to ? { from: q.from, to: q.to } : null;
	});
	const builderRangeOk = $derived(
		builderConfig && builderWin ? isRangeOk(builderWin, builderConfig.bucket, view.tz) : true
	);
	const builderUnit = $derived(
		builderSchema && builderConfig
			? builderSchema.measures.find((m) => m.name === builderConfig.measure)?.unit
			: undefined
	);
	$effect(() => {
		if (report !== 'builder') return;
		let live = true;
		getJSON<Schema>('tile-builder-schema', 'analytics/schema', new URLSearchParams()).then(
			(s) => {
				if (live) builderSchema = s;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	$effect(() => {
		if (report !== 'builder' || !builderSchema || !builderConfig || !builderRangeOk) return;
		const cfg = builderConfig;
		const win = builderWin;
		const needsFacets = Object.keys(view.state.exclude).length > 0;
		if (needsFacets && !view.facetsReady) return;
		let live = true;
		const params = untrack(() =>
			view.paramsForTile('query', 'builder', {
				...tileParams,
				measure: cfg.measure,
				dim: cfg.dims,
				bucket: cfg.bucket,
				top: String(cfg.top)
			})
		);
		if (!params) {
			builderData = null;
			return;
		}
		if (cfg.bucket !== 'none' && win) {
			params.delete('all');
			params.set('from', win.from.toISOString());
			params.set('to', win.to.toISOString());
		}
		getJSON<QueryResponse>('tile-builder-query', 'analytics/query', params).then(
			(r) => {
				if (!live) return;
				clearError();
				builderData = r;
			},
			(e) => {
				if (!live || e instanceof Superseded) return;
				builderData = null;
				setError(e);
			}
		);
		return () => {
			live = false;
		};
	});
	function builderPick(dim: string, key: string, shift: boolean) {
		if ((DIM_KEYS as readonly string[]).includes(dim)) view.drill(dim as DimKey, key, { shift });
	}

	// --- Usage tile (primary cost chart + optional distribution from saved measure/grain) ---
	let usageCostResp = $state<QueryResponse | null>(null);
	let usageDist = $state<DistributionResponse | null>(null);
	const usageMeasure = $derived(
		typeof tileParams.measure === 'string' ? tileParams.measure : 'cost_usd'
	);
	const usageGrain = $derived(typeof tileParams.grain === 'string' ? tileParams.grain : 'call');
	const usageWin = $derived.by(() => {
		const now = new Date();
		const q = resolveWindow(view.state, now, view.tz, 'query');
		if (q.all) {
			const r = resolveWindow(view.state, now, view.tz, 'rest');
			return r.from && r.to ? { from: r.from, to: r.to, all: true } : null;
		}
		return q.from && q.to ? { from: q.from, to: q.to, all: false } : null;
	});
	$effect(() => {
		if (report !== 'usage') return;
		const win = usageWin;
		const needsFacets = Object.keys(view.state.exclude).length > 0;
		if (needsFacets && !view.facetsReady) return;
		let live = true;
		const run = (extra: Record<string, string>, set: (r: QueryResponse) => void) => {
			const params = untrack(() => view.paramsForTile('query', 'usage', { ...tileParams, ...extra }));
			if (!params) return;
			if (win?.all) {
				params.delete('all');
				params.set('from', win.from.toISOString());
				params.set('to', win.to.toISOString());
			}
			getJSON<QueryResponse>('tile-usage-query', 'analytics/query', params).then(
				(r) => {
					if (live) set(r);
				},
				() => {}
			);
		};
		run({ measure: 'cost_usd', dim: 'model', top: '100', bucket: 'none' }, (r) => (usageCostResp = r));
		const distParams = untrack(() =>
			view.paramsForTile('rest', 'usage', {
				...tileParams,
				measure: usageMeasure,
				grain: usageGrain
			})
		);
		if (distParams) {
			getJSON<DistributionResponse>('tile-usage-dist', 'analytics/distribution', distParams).then(
				(r) => {
					if (live) usageDist = r;
				},
				() => {}
			);
		}
		return () => {
			live = false;
		};
	});
	const usageCostRows = $derived(
		(usageCostResp?.rows ?? []).map((r) => ({
			key: r.k[0] ?? '',
			label: r.k[0] ?? '',
			value: r.v
		}))
	);
	const usageDistBins = $derived(usageDist?.rows.find((r) => r.k === 'all')?.bins ?? []);
	function usagePick(key: string, shift: boolean) {
		if (key === '__other__') return;
		view.drill('model', key, { shift });
	}

	// --- Trends ---
	let trendsSchema = $state<Schema | null>(null);
	let trendsData = $state<QueryResponse | null>(null);
	const trendsMetric = $derived(
		typeof tileParams.metric === 'string' ? tileParams.metric : 'hook_events'
	);
	const trendsGroup = $derived(
		typeof tileParams.group === 'string' ? tileParams.group : 'none'
	);
	const trendsChartStyle = $derived(tileParams.chart === 'area' ? 'area' : 'line');
	$effect(() => {
		if (report !== 'trends') return;
		let live = true;
		getJSON<Schema>('tile-trends-schema', 'analytics/schema', new URLSearchParams()).then(
			(s) => {
				if (live) trendsSchema = s;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	$effect(() => {
		if (report !== 'trends' || !trendsSchema) return;
		const p = view.paramsForTile('query', 'trends', tileParams);
		if (!p) return;
		let live = true;
		getJSON<QueryResponse>('tile-trends-main', 'analytics/query', p).then(
			(r) => {
				if (live) trendsData = r;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	const trendsSeries = $derived(
		trendsData
			? trendsData.rows
					.filter((r) => r.t)
					.reduce((acc: TimeSeries[], r) => {
						const name = r.k.length ? r.k.map(label).join(' / ') : 'all';
						let s = acc.find((x) => x.name === name);
						if (!s) {
							s = { name, points: [] };
							acc.push(s);
						}
						s.points.push({ t: r.t as string, v: r.v });
						return acc;
					}, [])
			: []
	);

	// --- Overview sparkline ---
	let overviewSummary = $state<Summary | null>(null);
	let overviewSpark = $state<{ t: string; v: number }[]>([]);
	const overviewMeasure = $derived(
		typeof tileParams.measure === 'string' ? tileParams.measure : 'hook_events'
	);
	$effect(() => {
		if (report !== 'overview') return;
		const needsFacets = Object.keys(view.state.exclude).length > 0;
		if (needsFacets && !view.facetsReady) return;
		let live = true;
		const rest = untrack(() => view.paramsForTile('rest', 'overview', tileParams));
		if (rest) {
			getJSON<Summary>('tile-overview-summary', 'analytics/summary', rest).then(
				(s) => {
					if (live) overviewSummary = s;
				},
				() => {}
			);
		}
		const q = untrack(() => view.paramsForTile('query', 'overview', tileParams));
		if (q) {
			getJSON<QueryResponse>('tile-overview-spark', 'analytics/query', q).then(
				(r) => {
					if (live)
						overviewSpark = r.rows.filter((x) => x.t).map((x) => ({ t: x.t as string, v: x.v }));
				},
				() => {}
			);
		}
		return () => {
			live = false;
		};
	});

	// --- Repos bar chart ---
	let reposResp = $state<QueryResponse | null>(null);
	$effect(() => {
		if (report !== 'repos' || view.facets === null) return;
		const p = view.paramsForTile('query', 'repos', tileParams);
		if (!p) return;
		let live = true;
		getJSON<QueryResponse>('tile-repos-chart', 'analytics/query', p).then(
			(r) => {
				if (live) reposResp = r;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	const reposRows = $derived(
		(reposResp?.rows ?? []).map((r) => ({
			key: r.k[0] ?? '',
			label: r.k[0] ?? '',
			value: r.v
		}))
	);

	// --- Quality ---
	let qualityScores = $state<Scores | null>(null);
	let qualitySeries = $state<ScoreSeries | null>(null);
	const qualityKind = $derived(
		(typeof tileParams.kind === 'string' ? tileParams.kind : 'design') as 'design' | 'brief' | 'report'
	);
	const qualityBucket = $derived(
		(typeof tileParams.bucket === 'string' ? tileParams.bucket : 'day') as Bucket
	);
	const qualityWindow = $derived.by(() => {
		const w = resolveWindow(view.state, new Date(), view.tz, 'rest');
		return w.from && w.to ? { from: w.from, to: w.to } : null;
	});
	$effect(() => {
		if (report !== 'quality') return;
		const base = view.paramsForTile('rest', 'quality', tileParams);
		if (!base) return;
		let live = true;
		Promise.all([
			getJSON<Scores>('tile-quality-scores', 'analytics/scores', scoresParams(base, qualityKind)),
			getJSON<ScoreSeries>(
				'tile-quality-series',
				'analytics/score-series',
				scoreSeriesParams(base, qualityKind, qualityBucket)
			)
		]).then(
			([s, ss]) => {
				if (live) {
					qualityScores = s;
					qualitySeries = ss;
				}
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	const qualityDistRows = $derived(
		(qualityScores?.checks ?? [])
			.filter((c) => c.n > 0)
			.map((c) => ({
				name: c.name,
				min: c.min,
				p25: c.p25,
				median: c.median,
				p75: c.p75,
				max: c.max
			}))
	);
	const qualityBand = $derived((qualitySeries?.checks ?? []).find((c) => c.points.length > 0));

	// --- Executions ---
	let execData = $state<Executions | null>(null);
	$effect(() => {
		if (report !== 'executions') return;
		const p = view.paramsForTile('rest', 'executions', tileParams);
		if (!p) return;
		let live = true;
		getJSON<Executions>('tile-executions', 'analytics/executions', p).then(
			(r) => {
				if (live) execData = r;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	const execSeries = $derived.by((): TimeSeries[] => {
		if (!execData?.series?.length) return [];
		return execData.series.map((s) => ({
			name: s.key,
			points: s.points.map((p) => ({ t: p.t, v: p.n }))
		}));
	});
	const EXEC_NODES = [
		{ name: 'design', label: 'design' },
		{ name: 'brief', label: 'brief' },
		{ name: 'commit', label: 'commit' },
		{ name: 'report', label: 'report' },
		{ name: 'nocommit', label: 'no commit' },
		{ name: 'noreport', label: 'no report' }
	];
	const execSankey = $derived.by((): SankeyLink[] => {
		const c = execData?.counts;
		if (!c) return [];
		return [
			{ source: 'design', target: 'brief', value: c.complete + c.unreported + c.started },
			{ source: 'brief', target: 'commit', value: c.complete + c.unreported },
			{ source: 'brief', target: 'nocommit', value: c.started },
			{ source: 'commit', target: 'report', value: c.complete },
			{ source: 'commit', target: 'noreport', value: c.unreported }
		];
	});
	function overviewKpi(summary: Summary, measure: string): number {
		if (measure in summary && typeof (summary as Record<string, unknown>)[measure] === 'number')
			return (summary as Record<string, number>)[measure];
		return summary.hook_events;
	}

	// --- Conversations distribution ---
	let convDist = $state<DistributionResponse | null>(null);
	$effect(() => {
		if (report !== 'conversations') return;
		const p = view.paramsForTile('rest', 'conversations', tileParams);
		if (!p) return;
		let live = true;
		getJSON<DistributionResponse>('tile-conversations-dist', 'analytics/distribution', p).then(
			(r) => {
				if (live) convDist = r;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
	const convDistBins = $derived(convDist?.rows.find((r) => r.k === 'all')?.bins ?? []);

	// --- Explore ---
	let exploreCount = $state<number | null>(null);
	$effect(() => {
		if (report !== 'explore') return;
		const p = view.paramsForTile('rest', 'explore', tileParams);
		if (!p) return;
		let live = true;
		getJSON<Explore>('tile-explore', 'analytics/explore', p).then(
			(r) => {
				if (live) exploreCount = r.rows?.length ?? 0;
			},
			() => {}
		);
		return () => {
			live = false;
		};
	});
</script>

<div class="dash-tile-chart" data-testid={rootTestId}>
	{#if report === 'hooks' && hooksLoaded}
		{#if hooksTs}
			<TimeChart
				testid="hooks-over-time"
				series={hooksBuildSeries(hooksTs, hooksBucket)}
				bucket={(hooksTs.bucket ?? hooksBucket) as Bucket}
				filterDim={hooksSplit}
				onseries={({ key, shift }) =>
					view.drill(hooksSplit, key === '(none)' ? '' : key, { shift })}
				onbrush={({ from, to }) => view.setWindow(from, to)}
			/>
		{/if}
		{#each HOOKS_BARS as b (b.testid)}
			<BarChart
				testid={b.testid}
				rows={hooksBars[b.testid] ?? []}
				onselect={(d) => view.drill(b.dim, d.key, { shift: d.shift })}
			/>
		{/each}
		{#each HOOKS_TREES as t (t.testid)}
			<Treemap
				testid={t.testid}
				root={hooksTrees[t.testid] ?? []}
				onselect={(d) => hooksDrillPath(t.dims, d.path, d.shift)}
			/>
		{/each}
	{:else if report === 'builder' && builderConfig && builderRangeOk}
		<BuilderChart
			testid="builder-chart"
			config={builderConfig}
			resp={builderData}
			unit={builderUnit}
			onpick={builderPick}
			onbrush={({ from, to }) => view.setWindow(from, to)}
		/>
	{:else if report === 'usage'}
		<BarChart
			testid="usage-cost-by-model"
			rows={usageCostRows}
			unit="usd"
			selectable
			onselect={({ key, shift }) => usagePick(key, shift)}
		/>
		{#if usageDistBins.length > 0}
			<DistributionChart
				testid="usage-distribution"
				measure={usageMeasure as DistributionMeasure}
				bins={usageDistBins}
			/>
		{/if}
	{:else if report === 'trends' && trendsData}
		<TimeChart
			testid="trends-chart"
			series={trendsSeries}
			bucket={(trendsData.bucket ?? 'day') as Bucket}
			stacked={trendsChartStyle === 'area' && trendsGroup !== 'none'}
			area={trendsChartStyle === 'area'}
			onbrush={({ from, to }) => view.setWindow(from, to)}
		/>
	{:else if report === 'overview'}
		{#if overviewSummary}
			<p class="tile-kpi">
				<span data-testid="summary-{overviewMeasure}">{num(overviewKpi(overviewSummary, overviewMeasure))}</span>
				{overviewMeasure}
			</p>
		{/if}
		<Sparkline testid="overview-spark-{overviewMeasure}" points={overviewSpark} />
	{:else if report === 'repos' && reposResp}
		<BarChart
			testid="repos-chart"
			rows={reposRows}
			onselect={(d) => {
				if (d.key !== '__other__') view.drill('repo_id', d.key, { shift: d.shift });
			}}
		/>
	{:else if report === 'quality'}
		{#if qualityBand && qualityWindow}
			<ScoreBandChart
				testid="quality-band-{qualityBand.name}"
				title={qualityBand.name}
				points={qualityBand.points}
				bucket={qualityBucket}
				from={qualityWindow.from}
				to={qualityWindow.to}
				tz={view.tz}
				onbrush={({ from, to }) => view.setWindow(from, to)}
			/>
		{/if}
		{#if qualityDistRows.length > 0}
			<BoxChart testid="quality-dist" rows={qualityDistRows} />
		{/if}
	{:else if report === 'executions' && execData}
		<SankeyChart testid="exec-sankey" nodes={EXEC_NODES} links={execSankey} />
		{#if execSeries.length > 0}
			<TimeChart
				testid="exec-shape-series"
				series={execSeries}
				bucket={(execData.bucket ?? 'day') as 'day' | 'week' | 'month'}
				stacked
				area
				onbrush={({ from, to }) => view.setWindow(from, to)}
			/>
		{/if}
	{:else if report === 'conversations' && convDistBins.length > 0}
		<DistributionChart testid="conversations-distribution" measure="cost_usd" bins={convDistBins} />
	{:else if report === 'explore'}
		<p data-testid="explore-count">Rows loaded: {exploreCount ?? '…'}</p>
	{:else}
		<p class="muted">Loading…</p>
	{/if}
</div>

<style>
	.dash-tile-chart {
		min-height: 4rem;
	}
	.tile-kpi {
		margin: 0 0 0.5rem;
		font-size: 0.9rem;
	}
	.muted {
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
