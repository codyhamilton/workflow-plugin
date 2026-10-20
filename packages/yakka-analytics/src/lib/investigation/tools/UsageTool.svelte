<script lang="ts">
	import {
		aggregate,
		type AggregateRequest,
		type BreakdownResult,
		type DistributionResult,
		type Fetcher,
		type TrendResult
	} from '$lib/aggregate';
	import { getJSON } from '$lib/query';
	import { DistributionChart, TrendChart, type DistributionFrameData, type TrendFrameData } from '$lib/analysis/chart-frame';
	import { costLabel, label, num } from '$lib/format';
	import { Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import { trendFrame } from '../frames';
	import type { UsageTrendMeasure } from './registry';
	import { USAGE_TREND_MEASURES } from './registry';

	type UsageView = 'time' | 'distribution';

	let {
		request,
		primary,
		commit,
		onBrushEnd,
		onDrill
	}: {
		request: AggregateRequest;
		primary: TrendResult | DistributionResult | null;
		commit: (next: AggregateRequest, replace?: boolean) => void;
		onBrushEnd: (detail: { from?: string; to?: string }) => void;
		onDrill: (detail: { dim: string; value: string; modifiers: { shiftKey: boolean } }) => void;
	} = $props();

	let view = $state<UsageView>('time');
	let trendMeasure = $state<UsageTrendMeasure>('cost_usd');
	let tableBreakdowns = $state<Record<string, BreakdownResult | null>>({});

	const ask = $derived(request.ask);

	$effect(() => {
		if (ask.ask === 'distribution') view = 'distribution';
		else if (ask.ask === 'trend' && ask.dim === 'model') {
			view = 'time';
			if ((USAGE_TREND_MEASURES as readonly string[]).includes(ask.measure)) {
				trendMeasure = ask.measure as UsageTrendMeasure;
			}
		}
	});

	function breakdownFetcher(measure: string): Fetcher {
		return (_slot, path, params) => getJSON(`investigation-usage-${measure}`, path, params);
	}

	$effect(() => {
		const req = request;
		let live = true;
		const measures = ['model_calls', 'unpriced_calls', 'tokens_in', 'tokens_out', 'cost_usd'] as const;
		(async () => {
			const out: Record<string, BreakdownResult | null> = {};
			try {
				for (const measure of measures) {
					const result = await aggregate(
						{ ...req, ask: { ask: 'breakdown', measure, dim: 'model' } },
						{ now: new Date(), fetcher: breakdownFetcher(measure) }
					);
					if (!live) return;
					out[measure] = result as BreakdownResult;
				}
				clearError();
				tableBreakdowns = out;
			} catch (e) {
				if (!live || e instanceof Superseded) return;
				setError(e);
			}
		})();
		return () => {
			live = false;
		};
	});

	function values(result: BreakdownResult | null): Record<string, number> {
		const out: Record<string, number> = {};
		for (const s of result?.series ?? []) {
			out[s.key] = s.points.reduce((a, p) => a + p.v, 0);
		}
		return out;
	}

	const callsBy = $derived(values(tableBreakdowns.model_calls ?? null));
	const unpricedBy = $derived(values(tableBreakdowns.unpriced_calls ?? null));
	const tinBy = $derived(values(tableBreakdowns.tokens_in ?? null));
	const toutBy = $derived(values(tableBreakdowns.tokens_out ?? null));
	const costBy = $derived(values(tableBreakdowns.cost_usd ?? null));

	const models = $derived.by(() => {
		const seen = new Set<string>();
		for (const m of Object.values(tableBreakdowns)) {
			for (const s of m?.series ?? []) seen.add(s.key);
		}
		return [...seen];
	});

	const totalCalls = $derived(models.reduce((n, m) => n + (callsBy[m] ?? 0), 0));
	const totalUnpriced = $derived(models.reduce((n, m) => n + (unpricedBy[m] ?? 0), 0));

	function cell(map: Record<string, number>, key: string): string {
		return key in map ? num(map[key]) : '—';
	}

	function rowCost(m: string): string {
		const c = costBy[m] ?? 0;
		const u = unpricedBy[m] ?? 0;
		if (c === 0 && u > 0) return 'unpriced';
		return costLabel({ cost: c, unpriced: u, calls: callsBy[m] ?? 0 });
	}

	function setView(next: UsageView) {
		if (next === 'time') {
			commit({
				...request,
				ask: { ask: 'trend', measure: trendMeasure, bucket: 'day', dim: 'model' }
			});
		} else {
			commit({
				...request,
				ask: { ask: 'distribution', measure: 'cost_usd', grain: 'call', dim: 'model' }
			});
		}
	}

	function setTrendMeasure(measure: UsageTrendMeasure) {
		trendMeasure = measure;
		commit({ ...request, ask: { ask: 'trend', measure, bucket: 'day', dim: 'model' } });
	}

	const trendData = $derived.by((): TrendFrameData | null => {
		if (!primary || primary.ask !== 'trend') return null;
		const a = request.ask;
		if (a.ask !== 'trend') return null;
		return trendFrame(a.measure, a.bucket, primary as TrendResult, 'model');
	});

	const distData = $derived.by((): DistributionFrameData | null => {
		if (!primary || primary.ask !== 'distribution') return null;
		const a = request.ask;
		if (a.ask !== 'distribution') return null;
		const rows = (primary as DistributionResult).rows;
		const allBins = rows.find((r) => r.k === 'all')?.bins;
		const bins =
			allBins && allBins.length > 0
				? allBins
				: (rows.find((r) => r.bins.length > 0)?.bins ?? []);
		return { measure: a.measure, bins, drillDim: 'model' };
	});
</script>

<div class="usage-tool" data-testid="investigation-usage-tool">
	<div class="controls" role="group" aria-label="Usage view">
		<button
			type="button"
			data-testid="investigation-usage-view-time"
			aria-pressed={view === 'time'}
			onclick={() => setView('time')}>Over time</button
		>
		<button
			type="button"
			data-testid="investigation-usage-view-distribution"
			aria-pressed={view === 'distribution'}
			onclick={() => setView('distribution')}>Distribution</button
		>
	</div>

	{#if view === 'time'}
		<label class="measure">
			measure
			<select
				data-testid="investigation-usage-measure"
				value={trendMeasure}
				onchange={(e) => setTrendMeasure((e.currentTarget as HTMLSelectElement).value as UsageTrendMeasure)}
			>
				{#each USAGE_TREND_MEASURES as m (m)}<option value={m}>{m}</option>{/each}
			</select>
		</label>
	{/if}

	{#if totalUnpriced > 0}
		<p class="banner" data-testid="investigation-usage-unpriced-banner">
			{totalUnpriced} of {totalCalls} calls are unpriced
		</p>
	{/if}

	<table data-testid="investigation-usage-table">
		<thead>
			<tr>
				<th>model</th><th>calls</th><th>unpriced</th><th>tokens in</th><th>tokens out</th><th>cost</th>
			</tr>
		</thead>
		<tbody>
			{#each models as m (m)}
				<tr data-testid="investigation-usage-row-{m}">
					<th scope="row">{label(m)}</th>
					<td>{cell(callsBy, m)}</td>
					<td>{cell(unpricedBy, m)}</td>
					<td>{cell(tinBy, m)}</td>
					<td>{cell(toutBy, m)}</td>
					<td data-testid="investigation-usage-{m}-cost">{rowCost(m)}</td>
				</tr>
			{/each}
		</tbody>
	</table>

	{#if trendData}
		<section class="chart">
			<TrendChart
				data={trendData}
				testid="investigation-usage-trend"
				onbrushend={onBrushEnd}
				ondrill={onDrill}
			/>
		</section>
	{/if}

	{#if distData && distData.bins.length > 0}
		<section class="chart">
			<DistributionChart data={distData} testid="investigation-usage-distribution" ondrill={onDrill} />
		</section>
	{/if}
</div>

<style>
	.controls {
		display: flex;
		gap: 0.35rem;
		margin: 0.5rem 0;
	}
	button[aria-pressed='true'] {
		font-weight: bold;
	}
	.measure {
		display: block;
		margin-bottom: 0.5rem;
	}
	.banner {
		font-size: 0.9rem;
		color: var(--muted);
	}
	table {
		border-collapse: collapse;
		margin: 0.5rem 0 1rem;
		width: 100%;
	}
	th,
	td {
		padding: 0.2rem 0.5rem;
		text-align: right;
		border-bottom: 1px solid var(--border);
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		text-align: left;
	}
	.chart {
		margin-top: 1rem;
	}
</style>
