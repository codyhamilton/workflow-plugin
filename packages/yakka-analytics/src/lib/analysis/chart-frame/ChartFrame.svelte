<script lang="ts">
	import ChartHost from './ChartHost.svelte';
	import { optionForKind } from './options';
	import type { AnalysisTokens } from './tokens';
	import type {
		BreakdownFrameData,
		ChartFrameCallbacks,
		ChartFrameKind,
		DistributionFrameData,
		QualityFrameData,
		TrendFrameData
	} from './types';

	type FrameData = TrendFrameData | BreakdownFrameData | DistributionFrameData | QualityFrameData;

	let {
		kind,
		data,
		height = 280,
		testid,
		onhover,
		onbrushend,
		ondrill
	}: {
		kind: ChartFrameKind;
		data: FrameData;
		height?: number;
		testid?: string;
		onhover?: ChartFrameCallbacks['onhover'];
		onbrushend?: ChartFrameCallbacks['onbrushend'];
		ondrill?: ChartFrameCallbacks['ondrill'];
	} = $props();

	const build = (t: AnalysisTokens) => optionForKind(kind, data, t);
</script>

<ChartHost {build} {height} {testid} {onhover} {onbrushend} {ondrill} />
