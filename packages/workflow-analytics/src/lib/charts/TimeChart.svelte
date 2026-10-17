<script lang="ts">
	import type { DimKey } from '$lib/urlstate';
	import DataTable from './DataTable.svelte';
	import EChart from './EChart.svelte';
	import { timeOption, type TimeSeries } from './options';
	import type { Tokens } from './theme';

	const INERT_SERIES = new Set(['all', '__other__', '', '(none)']);

	let {
		testid,
		series,
		bucket,
		stacked = false,
		area = false,
		filterDim,
		onseries,
		onbrush
	}: {
		testid: string;
		series: TimeSeries[];
		bucket: 'hour' | 'day' | 'week' | 'month';
		stacked?: boolean;
		area?: boolean;
		filterDim?: DimKey;
		onseries?: (d: { key: string; shift: boolean }) => void;
		onbrush?: (d: { from: Date; to: Date }) => void;
	} = $props();

	let showTable = $state(false);
	let ready = $state(false);
	let theme = $state('light');
	let chart: any = null;

	const drillable = $derived(!!filterDim && !!onseries);

	const build = (t: Tokens) => {
		const option = timeOption({ series, bucket, stacked, area }, t);
		if (drillable && option.legend && typeof option.legend === 'object') {
			option.legend = { ...option.legend, selectedMode: false };
		}
		return option;
	};

	function pickSeries(params: any, native: any) {
		if (!drillable) return;
		const kind = params?.componentType;
		if (kind !== 'series' && kind !== 'legend') return;
		const key = params?.seriesName ?? '';
		if (INERT_SERIES.has(key)) return;
		onseries?.({ key, shift: !!native?.shiftKey });
	}

	function cursorFor(params: any) {
		if (!drillable) return 'default';
		const kind = params?.componentType;
		if (kind !== 'series' && kind !== 'legend') return 'default';
		const key = params?.seriesName ?? '';
		return INERT_SERIES.has(key) ? 'default' : 'pointer';
	}

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
		<EChart {build} bind:ready bind:theme {oninit} {onbrushend} onclick={pickSeries} {cursorFor} />
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
