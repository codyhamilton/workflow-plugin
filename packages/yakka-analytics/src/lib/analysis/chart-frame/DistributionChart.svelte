<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { ChartFrameCommonProps, DistributionFrameData } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: { data: DistributionFrameData } & ChartFrameCommonProps = $props();
</script>

<ChartFrame kind="distribution" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
