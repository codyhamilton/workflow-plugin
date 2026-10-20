<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { BreakdownFrameData, ChartFrameCallbacks } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: {
		data: BreakdownFrameData;
		height?: number;
		testid?: string;
	} & ChartFrameCallbacks = $props();
</script>

<ChartFrame kind="breakdown" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
