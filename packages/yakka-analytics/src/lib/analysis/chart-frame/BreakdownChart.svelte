<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { BreakdownFrameData, ChartFrameCommonProps } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: { data: BreakdownFrameData } & ChartFrameCommonProps = $props();
</script>

<ChartFrame kind="breakdown" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
