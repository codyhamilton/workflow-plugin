<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { binLabel, distributionOption, type DistributionMeasure } from './distribution';
	import type { DistributionBin } from '$lib/types';
	import type { Tokens } from './theme';

	let {
		testid,
		measure,
		bins
	}: {
		testid: string;
		measure: DistributionMeasure;
		bins: DistributionBin[];
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	const build = (t: Tokens) => distributionOption({ measure, bins }, t);
	const tableRows = $derived(
		bins.map((b) => ({
			cells: [binLabel(measure, b.lo, b.hi), b.n]
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
		<DataTable testid="{testid}-table" columns={['Bin', 'Calls']} rows={tableRows} />
	{:else}
		<EChart {build} bind:ready bind:theme height={280} />
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
