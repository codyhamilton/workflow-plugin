<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { barOption, type BarRow } from './options';
	import type { Tokens } from './theme';

	let {
		testid,
		rows,
		unit,
		selectable = true,
		onselect
	}: {
		testid: string;
		rows: BarRow[];
		unit?: string;
		selectable?: boolean;
		onselect?: (d: { key: string; shift: boolean }) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	// Fixed grid (120/24/8/24) plus 28 px per row; clickBar in the e2e helpers reads this.
	const height = $derived(Math.max(120, 28 * rows.length + 32));
	const build = (t: Tokens) => barOption({ rows, unit, selectable }, t);

	const tableRows = $derived(
		rows.map((r) => ({
			cells: [r.label ?? r.key, r.value],
			selectable: selectable && r.key !== '__other__'
		}))
	);

	function pick(params: any, native: any) {
		const key = params?.data?.key;
		if (!key || key === '__other__' || !selectable) return;
		onselect?.({ key, shift: !!native?.shiftKey });
	}
	function pickRow(i: number, shift: boolean) {
		const r = rows[i];
		if (!r || r.key === '__other__' || !selectable) return;
		onselect?.({ key: r.key, shift });
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
		<DataTable testid="{testid}-table" columns={['Label', unit ?? 'Value']} rows={tableRows} {unit} onrow={pickRow} />
	{:else}
		<EChart
			{build}
			{height}
			bind:ready
			bind:theme
			onclick={pick}
			cursorFor={(p) => (p?.data?.clickable ? 'pointer' : 'default')}
		/>
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
