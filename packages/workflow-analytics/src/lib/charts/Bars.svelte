<script lang="ts">
	import { BarChart } from 'layerchart';
	import { color } from './palette';

	// rows: one per category (`name`), one numeric column per key in `keys`.
	let {
		rows,
		keys,
		horizontal = false
	}: { rows: Record<string, string | number>[]; keys: string[]; horizontal?: boolean } = $props();

	const series = $derived(keys.map((k, i) => ({ key: k, color: color(i) })));
	const height = $derived(horizontal ? Math.max(120, rows.length * 32 + 40) : 280);
</script>

<div class="chart" style:height="{height}px" data-testid="bar-chart">
	{#if horizontal}
		<BarChart data={rows} y="name" {series} orientation="horizontal" legend={keys.length > 1} />
	{:else}
		<BarChart data={rows} x="name" {series} seriesLayout="group" legend={keys.length > 1} />
	{/if}
</div>

<style>
	.chart {
		padding: 0.5rem 1rem;
		border: 1px solid #ddd;
		border-radius: 4px;
	}
</style>
