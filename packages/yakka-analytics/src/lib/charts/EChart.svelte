<script lang="ts">
	import { onMount } from 'svelte';
	import * as echarts from 'echarts/core';
	import {
		BarChart,
		BoxplotChart,
		HeatmapChart,
		LineChart,
		SankeyChart,
		ScatterChart,
		TreemapChart
	} from 'echarts/charts';
	import {
		AriaComponent,
		BrushComponent,
		GridComponent,
		LegendComponent,
		TooltipComponent,
		VisualMapComponent
	} from 'echarts/components';
	import { SVGRenderer } from 'echarts/renderers';
	import { readTokens, scheme, watchScheme, type Tokens } from './theme';

	echarts.use([
		BarChart,
		BoxplotChart,
		HeatmapChart,
		LineChart,
		SankeyChart,
		ScatterChart,
		TreemapChart,
		AriaComponent,
		BrushComponent,
		GridComponent,
		LegendComponent,
		TooltipComponent,
		VisualMapComponent,
		SVGRenderer
	]);

	let {
		build,
		height = 280,
		oninit,
		onclick,
		onbrushend,
		cursorFor,
		ready = $bindable(false),
		theme = $bindable('light')
	}: {
		build: (t: Tokens) => unknown;
		height?: number;
		oninit?: (chart: any) => void;
		onclick?: (params: any, native: any) => void;
		onbrushend?: (params: any) => void;
		cursorFor?: (params: any) => string;
		ready?: boolean;
		theme?: string;
	} = $props();

	let el: HTMLDivElement;
	let chart: any = null;
	let inited = false;
	let stopScheme: (() => void) | undefined;

	function applyOption(option: unknown) {
		if (!chart) return;
		ready = false;
		theme = scheme();
		chart.setOption(option as any, { notMerge: true, lazyUpdate: false });
	}

	onMount(() => {
		chart = echarts.init(el, null, { renderer: 'svg' });
		chart.on('finished', () => {
			ready = true;
			if (!inited) {
				inited = true;
				oninit?.(chart);
			}
		});
		chart.on('click', (params: any) => onclick?.(params, params?.event?.event ?? params?.event));
		chart.on('brushEnd', (params: any) => onbrushend?.(params));
		if (cursorFor) {
			chart.on('mouseover', (params: any) => chart.getZr().setCursorStyle(cursorFor(params)));
			chart.on('globalout', () => chart.getZr().setCursorStyle('default'));
		}
		const ro = new ResizeObserver(() => chart && chart.resize());
		ro.observe(el);
		stopScheme = watchScheme(() => applyOption(build(readTokens(el))));
		return () => {
			ro.disconnect();
			stopScheme?.();
			chart?.dispose();
			chart = null;
		};
	});

	$effect(() => {
		const option = build(readTokens(el));
		if (chart) applyOption(option);
	});
</script>

<div class="echart" bind:this={el} style:height="{height}px"></div>

<style>
	.echart {
		width: 100%;
	}
</style>
