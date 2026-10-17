<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { heatmapOption, type HeatCell } from './options';
	import type { Tokens } from './theme';
	import { DIM_KEYS } from '$lib/urlstate';

	let {
		testid,
		cells,
		xLabels,
		yLabels,
		xKeys = [],
		yKeys = [],
		dims = [],
		unit,
		onpick
	}: {
		testid: string;
		cells: HeatCell[];
		xLabels: string[];
		yLabels: string[];
		xKeys?: string[];
		yKeys?: string[];
		dims?: string[];
		unit?: string;
		onpick?: (dim: string, key: string, shift: boolean) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	const build = (t: Tokens) => heatmapOption({ cells, xLabels, yLabels }, t);

	function drillX(xIndex: number, shift: boolean) {
		const dim = dims[0] ?? '';
		if (dim === 'weekday' || dim === 'hour_of_day') return;
		if (!(DIM_KEYS as readonly string[]).includes(dim)) return;
		const key = xKeys[xIndex] ?? '';
		if (key === '' || key === '__other__') return;
		onpick?.(dim, key, shift);
	}

	function pick(params: any, native: any) {
		const data = params?.data;
		if (!Array.isArray(data) || data.length < 2) return;
		drillX(Number(data[0]), !!native?.shiftKey);
	}

	function pickRow(i: number, shift: boolean) {
		const c = cells[i];
		if (c) drillX(c.x, shift);
	}

	function rowSelectable(c: HeatCell): boolean {
		const dim = dims[0] ?? '';
		if (dim === 'weekday' || dim === 'hour_of_day') return false;
		if (!(DIM_KEYS as readonly string[]).includes(dim)) return false;
		const key = xKeys[c.x] ?? '';
		return key !== '' && key !== '__other__';
	}

	const columns = $derived(['X', 'Y', 'Value']);
	const tableRows = $derived(
		cells.map((c) => ({
			cells: [xLabels[c.x] ?? c.x, yLabels[c.y] ?? c.y, c.v],
			selectable: rowSelectable(c)
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
