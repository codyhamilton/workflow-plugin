<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { ChartFrameCallbacks, DistributionFrameData } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: {
		data: DistributionFrameData;
		height?: number;
		testid?: string;
	} & ChartFrameCallbacks = $props();
</script>

<ChartFrame kind="distribution" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
