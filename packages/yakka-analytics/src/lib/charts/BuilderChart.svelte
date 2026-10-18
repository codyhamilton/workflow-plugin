<script lang="ts">
	import GroupedBar from './GroupedBar.svelte';
	import Heatmap from './Heatmap.svelte';
	import SmallMultiples from './SmallMultiples.svelte';
	import TimeChart from './TimeChart.svelte';
	import Treemap from './Treemap.svelte';
	import {
		groupedBarProps,
		heatmapProps,
		lineSeries,
		multiplesLayout,
		treemapNodes
	} from './multi';
	import type { BuilderConfig } from '../builder';
	import type { QueryResponse } from '../types';
	import { costLabel } from '$lib/format';

	let {
		testid,
		config,
		resp,
		unit,
		onpick,
		onbrush
	}: {
		testid: string;
		config: BuilderConfig;
		resp: QueryResponse | null;
		unit?: string;
		onpick?: (dim: string, key: string, shift: boolean) => void;
		onbrush?: (d: { from: Date; to: Date }) => void;
	} = $props();

	const empty = $derived(resp === null || (resp.rows?.length ?? 0) === 0);
	const scalarValue = $derived((resp?.rows ?? []).reduce((s, r) => s + r.v, 0));
	const timeBucket = $derived(
		(['hour', 'day', 'week', 'month'].includes(resp?.bucket ?? '')
			? resp!.bucket
			: 'day') as 'hour' | 'day' | 'week' | 'month'
	);

	function formatScalar(v: number): string {
		if (unit === 'usd') return costLabel({ cost: v, unpriced: v === 0 ? 1 : 0 });
		if (unit === 'tokens' || unit === 'count') return v.toLocaleString('en-US');
		return String(v);
	}

	function treemapPick(d: { path: string[]; shift: boolean }) {
		const key = d.path[d.path.length - 1];
		if (key === undefined || key === '' || key === '__other__') return;
		onpick?.(config.dims[d.path.length - 1] ?? config.dims[config.dims.length - 1] ?? '', key, d.shift);
	}
</script>

<div
	class="builder-chart"
	data-testid={testid}
	data-kind={config.chart}
	data-ready={config.chart === 'scalar' && !empty ? 'true' : undefined}
>
	{#if empty}
		<p class="empty">No data</p>
	{:else if config.chart === 'scalar'}
		<p class="scalar" data-testid="{testid}-scalar" data-value={scalarValue}>{formatScalar(scalarValue)}</p>
	{:else if config.chart === 'line' || config.chart === 'area'}
		<TimeChart
			testid="{testid}-chart"
			series={lineSeries(resp!)}
			bucket={timeBucket}
			area={config.chart === 'area'}
			{onbrush}
		/>
	{:else if config.chart === 'bar' || config.chart === 'stackedbar'}
		<GroupedBar
			testid="{testid}-chart"
			dim={config.dims[0] ?? ''}
			{...groupedBarProps(resp!)}
			stacked={config.chart === 'stackedbar'}
			{unit}
			{onpick}
		/>
	{:else if config.chart === 'heatmap'}
		{@const hp = heatmapProps(resp!)}
		<Heatmap
			testid="{testid}-chart"
			{...hp}
			dims={resp!.dims ?? []}
			{unit}
			{onpick}
		/>
	{:else if config.chart === 'treemap'}
		<Treemap testid="{testid}-chart" root={treemapNodes(resp!)} onselect={treemapPick} />
	{:else if config.chart === 'multiples'}
		<SmallMultiples testid={testid} {...multiplesLayout(resp!)} bucket={timeBucket} {onbrush} />
	{/if}
</div>

<style>
	.builder-chart {
		position: relative;
	}
	.empty {
		color: var(--muted);
	}
	.scalar {
		font-size: 2.5rem;
		font-weight: 600;
		margin: 1.5rem 0;
	}
</style>
