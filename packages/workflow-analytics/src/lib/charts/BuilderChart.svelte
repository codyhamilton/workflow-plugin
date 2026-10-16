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

	let {
		testid,
		config,
		resp,
		onpick,
		onbrush
	}: {
		testid: string;
		config: BuilderConfig;
		resp: QueryResponse | null;
		onpick?: (dim: string, key: string, shift: boolean) => void;
		onbrush?: (d: { from: Date; to: Date }) => void;
	} = $props();

	const empty = $derived(resp === null || (resp.rows?.length ?? 0) === 0);
	const timeBucket = $derived(
		(['hour', 'day', 'week', 'month'].includes(resp?.bucket ?? '')
			? resp!.bucket
			: 'day') as 'hour' | 'day' | 'week' | 'month'
	);

	function treemapPick(d: { path: string[]; shift: boolean }) {
		const key = d.path[d.path.length - 1];
		if (key === undefined || key === '__other__') return;
		onpick?.(config.dims[d.path.length - 1] ?? config.dims[config.dims.length - 1] ?? '', key, d.shift);
	}
</script>

<div class="builder-chart" data-testid={testid} data-kind={config.chart}>
	{#if empty}
		<p class="empty">No data</p>
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
			{onpick}
		/>
	{:else if config.chart === 'heatmap'}
		<Heatmap testid="{testid}-chart" {...heatmapProps(resp!)} />
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
</style>
