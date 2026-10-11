<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { panelOption, type MultiPanel } from './multi';
	import type { Tokens } from './theme';

	let {
		testid,
		panels,
		yMax,
		bucket,
		onbrush
	}: {
		testid: string;
		panels: MultiPanel[];
		yMax: number;
		bucket: 'hour' | 'day' | 'week' | 'month';
		onbrush?: (d: { from: Date; to: Date }) => void;
	} = $props();

	let showTable = $state(false);

	// Brush must be armed on mount so a horizontal drag fires brushEnd.
	function oninit(c: any) {
		c.dispatchAction({
			type: 'takeGlobalCursor',
			key: 'brush',
			brushOption: { brushType: 'lineX' }
		});
	}
	function onbrushend(params: any) {
		const range = params?.areas?.[0]?.coordRange;
		if (Array.isArray(range) && range.length === 2) {
			onbrush?.({ from: new Date(range[0]), to: new Date(range[1]) });
		}
	}

	const columns = $derived(['Panel', 'Series', 'Time', 'Value']);
	const tableRows = $derived.by(() => {
		const out: { cells: (string | number)[]; selectable: boolean }[] = [];
		for (const p of panels) {
			for (const s of p.series) {
				for (const pt of s.points) {
					out.push({ cells: [p.title, s.name, pt.t, pt.v], selectable: false });
				}
			}
		}
		return out;
	});
</script>

<div class="multiples">
	<button
		type="button"
		class="toggle"
		data-testid="{testid}-table-toggle"
		onclick={() => (showTable = !showTable)}
	>
		{showTable ? 'Charts' : 'Table'}
	</button>
	{#if showTable}
		<DataTable testid="{testid}-table" {columns} rows={tableRows} />
	{:else}
		<div class="grid">
			{#each panels as panel (panel.key)}
				<div class="panel" data-testid="{testid}-panel">
					<h4>{panel.title}</h4>
					<EChart
						build={(t: Tokens) => panelOption(panel, yMax, bucket, t)}
						height={200}
						{oninit}
						{onbrushend}
					/>
				</div>
			{/each}
		</div>
		{#if panels.length === 0}
			<p class="empty">No data</p>
		{/if}
	{/if}
</div>

<style>
	.multiples {
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
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 0.75rem;
	}
	.panel h4 {
		margin: 0 0 0.25rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text, #1a1a1a);
	}
	.empty {
		color: var(--muted, #6b7280);
	}
</style>
