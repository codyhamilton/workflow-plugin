<script lang="ts">
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { timeOption, type TimeSeries } from './options';
	import type { Tokens } from './theme';

	let {
		testid,
		series,
		bucket,
		stacked = false,
		area = false,
		onbrush
	}: {
		testid: string;
		series: TimeSeries[];
		bucket: 'hour' | 'day' | 'week' | 'month';
		stacked?: boolean;
		area?: boolean;
		onbrush?: (d: { from: Date; to: Date }) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');
	let chart: any = null;

	const build = (t: Tokens) => timeOption({ series, bucket, stacked, area }, t);

	// Brush must be armed on mount so a horizontal drag fires brushEnd.
	function oninit(c: any) {
		chart = c;
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
		chart?.dispatchAction({ type: 'brush', command: 'clear' });
	}

	const columns = $derived(['Time', ...series.map((s) => s.name)]);
	const tableRows = $derived.by(() => {
		const times = [...new Set(series.flatMap((s) => s.points.map((p) => p.t)))].sort();
		return times.map((t) => ({
			cells: [t, ...series.map((s) => s.points.find((p) => p.t === t)?.v ?? 0)],
			selectable: false
		}));
	});
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
		<EChart {build} bind:ready bind:theme {oninit} {onbrushend} />
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
