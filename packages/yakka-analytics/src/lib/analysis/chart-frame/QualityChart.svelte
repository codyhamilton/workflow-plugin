<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { ChartFrameCommonProps, QualityFrameData } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: { data: QualityFrameData } & ChartFrameCommonProps = $props();
</script>

<ChartFrame kind="quality" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
