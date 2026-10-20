<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { ChartFrameCallbacks, TrendFrameData } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: {
		data: TrendFrameData;
		height?: number;
		testid?: string;
	} & ChartFrameCallbacks = $props();
</script>

<ChartFrame kind="trend" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
