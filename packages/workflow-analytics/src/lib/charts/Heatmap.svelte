<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { heatmapOption, type HeatCell } from './options';
	import type { Tokens } from './theme';

	let {
		testid,
		cells,
		xLabels,
		yLabels
	}: {
		testid: string;
		cells: HeatCell[];
		xLabels: string[];
		yLabels: string[];
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	const build = (t: Tokens) => heatmapOption({ cells, xLabels, yLabels }, t);

	const columns = $derived(['X', 'Y', 'Value']);
	const tableRows = $derived(
		cells.map((c) => ({
			cells: [xLabels[c.x] ?? c.x, yLabels[c.y] ?? c.y, c.v],
			selectable: false
		}))
	);
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
		<DataTable testid="{testid}-table" {columns} rows={tableRows} />
	{:else}
		<EChart {build} bind:ready bind:theme />
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
		border: 1px solid var(--border, #d1d5db);
		border-radius: 4px;
		background: var(--surface, #f5f5f5);
		color: var(--text, #1a1a1a);
		cursor: pointer;
	}
</style>
