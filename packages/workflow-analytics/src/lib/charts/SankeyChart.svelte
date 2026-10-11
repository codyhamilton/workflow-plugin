<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { sankeyOption, type SankeyLink, type SankeyNode } from './sankey';
	import type { Tokens } from './theme';

	let {
		testid,
		nodes,
		links,
		onlink
	}: {
		testid: string;
		nodes: SankeyNode[];
		links: SankeyLink[];
		onlink?: (l: SankeyLink) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	const build = (t: Tokens) => sankeyOption({ nodes, links }, t);
	const tableRows = $derived(
		(links ?? []).filter((l) => l.value > 0).map((l) => ({ cells: [l.source, l.target, l.value] }))
	);

	function handleClick(params: any) {
		if (params?.dataType !== 'edge') return;
		const d = params?.data ?? {};
		onlink?.({ source: d.source, target: d.target, value: d.value });
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
		<DataTable
			testid="{testid}-table"
			columns={['source', 'target', 'value']}
			rows={tableRows}
		/>
	{:else}
		<EChart {build} bind:ready bind:theme onclick={handleClick} />
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
