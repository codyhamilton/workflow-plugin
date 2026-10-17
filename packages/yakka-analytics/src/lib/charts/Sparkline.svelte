<script lang="ts">
	import EChart from './EChart.svelte';
	import type { TimePoint } from './options';
	import type { Tokens } from './theme';

	let { testid, points }: { testid: string; points: TimePoint[] } = $props();

	let ready = $state(false);
	let theme = $state('light');

	// 28 px high, no axes, no interaction.
	const build = (t: Tokens) => ({
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 0, right: 0, top: 2, bottom: 2 },
		xAxis: { type: 'time', show: false },
		yAxis: { type: 'value', show: false },
		series: [
			{
				type: 'line',
				showSymbol: false,
				silent: true,
				lineStyle: { width: 1.5, color: t.series[0] },
				areaStyle: { opacity: 0.15, color: t.series[0] },
				data: (points ?? []).map((p) => [p.t, p.v])
			}
		]
	});
</script>

<div
	class="sparkline"
	data-testid={testid}
	data-ready={ready ? 'true' : 'false'}
	data-theme={theme}
>
	<EChart {build} height={28} bind:ready bind:theme />
</div>

<style>
	.sparkline {
		height: 28px;
	}
</style>
