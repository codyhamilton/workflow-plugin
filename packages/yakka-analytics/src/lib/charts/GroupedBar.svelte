<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { groupedBarOption, type BarSeries, type Category } from './multi';
	import type { Tokens } from './theme';

	let {
		testid,
		dim = '',
		categories,
		series,
		stacked = false,
		unit,
		onpick
	}: {
		testid: string;
		dim?: string;
		categories: Category[];
		series: BarSeries[];
		stacked?: boolean;
		unit?: string;
		onpick?: (dim: string, key: string, shift: boolean) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	const build = (t: Tokens) => groupedBarOption({ categories, series, stacked, unit }, t);

	// __other__ is drawn but never picked.
	function pick(params: any, native: any) {
		const key = params?.data?.key;
		if (typeof key === 'string' && key !== '' && key !== '__other__') onpick?.(dim, key, !!native?.shiftKey);
	}

	const columns = $derived(['Category', ...series.map((s) => s.name)]);
	const tableRows = $derived(
		categories.map((c, i) => ({
			cells: [c.label, ...series.map((s) => s.values[i] ?? 0)],
			selectable: c.key !== '' && c.key !== '__other__'
		}))
	);
	function pickRow(i: number, shift: boolean) {
		const c = categories[i];
		if (c && c.key !== '' && c.key !== '__other__') onpick?.(dim, c.key, shift);
	}
</script>

<div class="chart" data-testid={testid} data-ready={ready ? 'true' : 'false'} data-theme={theme}>
	<button
		type="button"
		class="toggle"
		data-testid="{testid}-table-toggle"
		onclick={() => (showTable = !showTable)}
	>
		{showTable ? 'Chart' : 'Table'}
	</button>
	{#if showTable}
		<DataTable testid="{testid}-table" {columns} rows={tableRows} {unit} onrow={pickRow} />
	{:else}
		<EChart {build} bind:ready bind:theme onclick={pick} />
	{/if}
</div>

<style>
	.chart {
		position: relative;
	}
	.toggle {
		position: absolute;
		top: 0;
		right: 0;
		z-index: 1;
		font-size: 0.75rem;
		padding: 0.15rem 0.5rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		background: var(--surface);
		color: var(--text);
		cursor: pointer;
	}
</style>
