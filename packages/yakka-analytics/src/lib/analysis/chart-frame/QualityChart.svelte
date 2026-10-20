<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import type { ChartFrameCallbacks, QualityFrameData } from './types';

	let {
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: {
		data: QualityFrameData;
		height?: number;
		testid?: string;
	} & ChartFrameCallbacks = $props();
</script>

<ChartFrame kind="quality" {data} {height} {testid} {onhover} {onbrushend} {ondrill} />
