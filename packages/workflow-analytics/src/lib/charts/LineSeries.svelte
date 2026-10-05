<script lang="ts">
	import { LineChart } from 'layerchart';
	import { label } from '$lib/format';
	import type { Series } from '$lib/types';
	import { color } from './palette';

	let { series }: { series: Series['series'] } = $props();

	const lines = $derived(
		series.map((s, i) => ({
			key: label(s.key),
			color: color(i),
			data: s.points.map((p) => ({ date: new Date(`${p.t}T00:00:00Z`), n: p.n })),
			value: 'n'
		}))
	);
</script>

<div class="chart" data-testid="line-chart">
	<LineChart x="date" series={lines} legend points />
</div>

<style>
	.chart {
		height: 280px;
		padding: 0.5rem 1rem;
		border: 1px solid #ddd;
		border-radius: 4px;
	}
</style>
