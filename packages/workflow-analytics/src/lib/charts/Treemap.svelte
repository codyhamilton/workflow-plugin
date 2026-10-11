<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { treemapOption, type TreemapNode } from './options';
	import type { Tokens } from './theme';

	let {
		testid,
		root,
		onselect
	}: {
		testid: string;
		root: TreemapNode[];
		onselect?: (d: { path: string[]; shift: boolean }) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');

	const build = (t: Tokens) => treemapOption({ root }, t);

	interface Leaf {
		path: string[];
		value: number;
	}
	function collect(nodes: TreemapNode[], path: string[], out: Leaf[]) {
		for (const n of nodes) {
			const p = [...path, n.name];
			if (n.children && n.children.length) collect(n.children, p, out);
			else out.push({ path: p, value: n.value ?? 0 });
		}
	}
	const leaves = $derived.by(() => {
		const out: Leaf[] = [];
		collect(root ?? [], [], out);
		return out;
	});
	const tableRows = $derived(
		leaves.map((l) => ({ cells: [l.path.join(' / '), l.value], selectable: true }))
	);

	function pick(params: any, native: any) {
		const path = (params?.treePathInfo ?? [])
			.map((n: any) => n?.name)
			.filter((s: unknown): s is string => typeof s === 'string' && s.length > 0);
		if (path.length) onselect?.({ path, shift: !!native?.shiftKey });
	}
	function pickRow(i: number, shift: boolean) {
		const l = leaves[i];
		if (l) onselect?.({ path: l.path, shift });
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
		<DataTable testid="{testid}-table" columns={['Path', 'Value']} rows={tableRows} onrow={pickRow} />
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
		border: 1px solid var(--border, #d1d5db);
		border-radius: 4px;
		background: var(--surface, #f5f5f5);
		color: var(--text, #1a1a1a);
		cursor: pointer;
	}
</style>
