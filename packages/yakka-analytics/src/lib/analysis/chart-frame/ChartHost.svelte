<script lang="ts">
	import { onMount } from 'svelte';
	import * as echarts from 'echarts/core';
	import { BarChart, LineChart } from 'echarts/charts';
	import {
		AriaComponent,
		BrushComponent,
		GridComponent,
		LegendComponent,
		TooltipComponent
	} from 'echarts/components';
	import { SVGRenderer } from 'echarts/renderers';
	import { readAnalysisTokens, type AnalysisTokens } from './tokens';
	import type {
		ChartBrushEndDetail,
		ChartDrillDetail,
		ChartHoverDetail,
		ChartPointerModifiers
	} from './types';

	echarts.use([
		BarChart,
		LineChart,
		AriaComponent,
		BrushComponent,
		GridComponent,
		LegendComponent,
		TooltipComponent,
		SVGRenderer
	]);

	let {
		build,
		height = 280,
		onhover,
		onbrushend,
		ondrill,
		ready = $bindable(false),
		testid
	}: {
		build: (t: AnalysisTokens) => unknown;
		height?: number;
		onhover?: (detail: ChartHoverDetail) => void;
		onbrushend?: (detail: ChartBrushEndDetail) => void;
		ondrill?: (detail: ChartDrillDetail) => void;
		ready?: boolean;
		testid?: string;
	} = $props();

	let el: HTMLDivElement;
	let chart: echarts.ECharts | null = null;

	function modifiers(native: MouseEvent | undefined): ChartPointerModifiers {
		return {
			shiftKey: native?.shiftKey ?? false,
			altKey: native?.altKey ?? false,
			metaKey: native?.metaKey ?? false,
			ctrlKey: native?.ctrlKey ?? false
		};
	}

	function applyOption(option: unknown) {
		if (!chart) return;
		ready = false;
		chart.setOption(option as echarts.EChartsCoreOption, { notMerge: true, lazyUpdate: false });
	}

	function parseBrushRange(params: any): ChartBrushEndDetail {
		const areas = params?.areas ?? [];
		const range = areas[0]?.coordRange ?? areas[0]?.range;
		if (Array.isArray(range) && range.length >= 2) {
			const [from, to] = range;
			return {
				from: typeof from === 'number' ? new Date(from).toISOString() : String(from),
				to: typeof to === 'number' ? new Date(to).toISOString() : String(to),
				raw: params
			};
		}
		return { raw: params };
	}

	onMount(() => {
		chart = echarts.init(el, null, { renderer: 'svg' });
		chart.on('finished', () => {
			ready = true;
		});
		chart.on('brushEnd', (params) => onbrushend?.(parseBrushRange(params)));
		chart.on('mouseover', (params) => {
			onhover?.({
				seriesName: params.seriesName,
				category: params.name,
				value: params.value,
				raw: params
			});
		});
		chart.on('click', (params) => {
			const data = params.data as { key?: string; dim?: string; clickable?: boolean } | undefined;
			const native = (params?.event?.event ?? params?.event) as MouseEvent | undefined;
			if (!data?.clickable || !data.dim || data.key === undefined) return;
			ondrill?.({
				dim: data.dim,
				value: data.key,
				modifiers: modifiers(native),
				raw: params
			});
		});
		const ro = new ResizeObserver(() => chart?.resize());
		ro.observe(el);
		const onTheme = () => applyOption(build(readAnalysisTokens(el)));
		const mq = window.matchMedia('(prefers-color-scheme: dark)');
		mq.addEventListener('change', onTheme);
		const obs = new MutationObserver(onTheme);
		obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
		applyOption(build(readAnalysisTokens(el)));
		return () => {
			ro.disconnect();
			mq.removeEventListener('change', onTheme);
			obs.disconnect();
			chart?.dispose();
			chart = null;
		};
	});

	$effect(() => {
		const option = build(readAnalysisTokens(el));
		if (chart) applyOption(option);
	});
</script>

<div
	class="analysis-chart-host"
	bind:this={el}
	style:height="{height}px"
	data-testid={testid}
	data-ready={ready ? 'true' : 'false'}
></div>

<style>
	.analysis-chart-host {
		width: 100%;
	}
</style>
