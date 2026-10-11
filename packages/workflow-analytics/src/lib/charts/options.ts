// Pure ECharts option builders. No DOM and no echarts import, so they are testable
// in isolation and the bundle only pulls the pieces EChart.svelte registers.
import type { Tokens } from './theme';

export interface BarRow {
	key: string;
	label?: string;
	value: number;
}
export interface BarProps {
	rows: BarRow[];
	unit?: string;
	selectable?: boolean;
}

export interface TimePoint {
	t: string;
	v: number;
}
export interface TimeSeries {
	name: string;
	points: TimePoint[];
}
export interface TimeProps {
	series: TimeSeries[];
	bucket: 'hour' | 'day' | 'week' | 'month';
	stacked?: boolean;
}

export interface HeatCell {
	x: number;
	y: number;
	v: number;
}
export interface HeatProps {
	cells: HeatCell[];
	xLabels: string[];
	yLabels: string[];
}

export interface TreemapNode {
	name: string;
	key?: string;
	value?: number;
	children?: TreemapNode[];
}
export interface TreemapProps {
	root: TreemapNode[];
}

function seriesColor(t: Tokens, i: number): string {
	return t.series[i % t.series.length];
}

export function barOption(p: BarProps, t: Tokens) {
	const rows = p.rows ?? [];
	const selectable = p.selectable !== false;
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 120, right: 24, top: 8, bottom: 24, containLabel: false },
		tooltip: {
			trigger: 'item',
			valueFormatter: (v: number) => (p.unit ? `${v} ${p.unit}` : `${v}`)
		},
		xAxis: {
			type: 'value',
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		yAxis: {
			type: 'category',
			inverse: true,
			data: rows.map((r) => r.label ?? r.key),
			axisLabel: { color: t.text },
			axisLine: { lineStyle: { color: t.border } },
			axisTick: { show: false }
		},
		series: [
			{
				type: 'bar',
				itemStyle: { color: t.series[0] },
				emphasis: { itemStyle: { color: t.accent } },
				data: rows.map((r) => ({
					value: r.value,
					key: r.key,
					clickable: selectable && r.key !== '__other__'
				}))
			}
		]
	};
}

export function timeOption(p: TimeProps, t: Tokens) {
	const stacked = p.stacked === true;
	const series = (p.series ?? []).map((s, i) => ({
		name: s.name,
		type: stacked ? 'bar' : 'line',
		stack: stacked ? 'total' : undefined,
		showSymbol: false,
		smooth: false,
		lineStyle: { width: 2, color: seriesColor(t, i) },
		itemStyle: { color: seriesColor(t, i) },
		data: (s.points ?? []).map((pt) => [pt.t, pt.v])
	}));
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 24, top: 24, bottom: 32, containLabel: false },
		legend: { show: series.length > 1, textStyle: { color: t.text } },
		tooltip: { trigger: 'axis' },
		brush: {
			brushType: 'lineX',
			brushMode: 'single',
			xAxisIndex: 0,
			throttleType: 'debounce',
			throttleDelay: 100
		},
		toolbox: { show: true, right: 8, feature: { brush: { type: ['lineX', 'clear'] } } },
		xAxis: {
			type: 'time',
			axisLabel: { color: t.muted },
			axisLine: { lineStyle: { color: t.border } }
		},
		yAxis: {
			type: 'value',
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		color: t.series,
		series
	};
}

export function heatmapOption(p: HeatProps, t: Tokens) {
	const cells = p.cells ?? [];
	const vals = cells.map((c) => c.v);
	const min = vals.length ? Math.min(...vals) : 0;
	const max = vals.length ? Math.max(...vals) : 1;
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 24, top: 8, bottom: 48, containLabel: false },
		tooltip: { position: 'top' },
		xAxis: {
			type: 'category',
			data: p.xLabels ?? [],
			splitArea: { show: true },
			axisLabel: { color: t.muted }
		},
		yAxis: {
			type: 'category',
			data: p.yLabels ?? [],
			splitArea: { show: true },
			axisLabel: { color: t.text }
		},
		visualMap: {
			min,
			max,
			calculable: true,
			orient: 'horizontal',
			left: 'center',
			bottom: 0,
			textStyle: { color: t.text },
			inRange: { color: [t.surface, t.series[0]] }
		},
		series: [
			{
				type: 'heatmap',
				data: cells.map((c) => [c.x, c.y, c.v] as [number, number, number]),
				itemStyle: { borderColor: t.bg, borderWidth: 1 },
				emphasis: { itemStyle: { borderColor: t.text, borderWidth: 1 } }
			}
		]
	};
}

export function treemapOption(p: TreemapProps, t: Tokens) {
	return {
		animation: false,
		backgroundColor: 'transparent',
		tooltip: { trigger: 'item' },
		series: [
			{
				type: 'treemap',
				roam: false,
				nodeClick: false,
				breadcrumb: { show: false },
				label: { show: true, color: t.text },
				upperLabel: { show: false },
				itemStyle: { borderColor: t.bg, borderWidth: 1, gapWidth: 1 },
				levels: [
					{ itemStyle: { borderColor: t.bg, borderWidth: 2, gapWidth: 2 }, color: t.series },
					{
						colorSaturation: [0.35, 0.55],
						itemStyle: { borderColor: t.bg, borderWidth: 1, gapWidth: 1 }
					}
				],
				data: p.root ?? []
			}
		]
	};
}
