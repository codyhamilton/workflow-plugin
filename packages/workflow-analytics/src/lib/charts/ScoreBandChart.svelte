<script lang="ts">
	import type { ScoreSeriesPoint } from '$lib/types';
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { scoreBandOption, scoreBandTableRows } from './score-series';
	import type { Tokens } from './theme';

	let {
		testid,
		title,
		points,
		bucket,
		from,
		to,
		tz,
		baselineMedian,
		onbrush
	}: {
		testid: string;
		title: string;
		points: ScoreSeriesPoint[];
		bucket: 'day' | 'week' | 'month';
		from: Date;
		to: Date;
		tz: string;
		baselineMedian?: number;
		onbrush?: (d: { from: Date; to: Date }) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');
	let chart: any = null;

	const props = $derived({ points, bucket, from, to, tz, baselineMedian });
	const build = (t: Tokens) => scoreBandOption(props, t);
	const tableRows = $derived(
		scoreBandTableRows(props).map((r) => ({
			cells: [r.t, r.n, r.p25, r.median, r.p75] as (string | number)[],
			selectable: false
		}))
	);

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
</script>

<section class="panel">
	<h2>{title}</h2>
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
				columns={['Time', 'n', 'p25', 'median', 'p75']}
				rows={tableRows}
			/>
		{:else}
			<EChart {build} bind:ready bind:theme {oninit} {onbrushend} />
		{/if}
	</div>
</section>

<style>
	.panel {
		margin-bottom: 1.5rem;
	}
	h2 {
		font-size: 1rem;
		font-weight: 600;
		margin: 0 0 0.5rem;
	}
	.chart {
		position: relative;
		min-height: 240px;
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
