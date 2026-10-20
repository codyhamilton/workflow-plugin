<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { ChartFrameCommonProps, TrendFrameData } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: { data: TrendFrameData } & ChartFrameCommonProps = $props();
</script>

<ChartFrame kind="trend" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
