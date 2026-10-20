import type { DistributionBin } from '$lib/types';
import { bucketStarts, instantKey } from '$lib/charts/score-series';
import { isDrillableMark } from './drill';
import type {
	BreakdownFrameData,
	DistributionFrameData,
	DistributionMeasure,
	QualityFrameData,
	TrendFrameData
} from './types';
import { type AnalysisTokens, seriesColor } from './tokens';

function trimZeros(s: string): string {
	return s.replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
}

function fmtCostEdge(v: number): string {
	if (v === 0) return '$0';
	if (v >= 1) return `$${v}`;
	if (v >= 0.01) return `$${trimZeros(v.toFixed(2))}`;
	return `$${trimZeros(v.toFixed(4))}`;
}

export function distributionBinLabel(measure: DistributionMeasure, lo: number, hi?: number): string {
	if (measure === 'cost_usd') {
		if (lo === 0 && hi === undefined) return '0';
		if (lo === 0 && hi !== undefined) return `<${fmtCostEdge(hi)}`;
		if (hi === undefined) return `≥${fmtCostEdge(lo)}`;
		return `${fmtCostEdge(lo)}–${fmtCostEdge(hi)}`;
	}
	if (lo === 0 && (hi === undefined || hi <= 1)) return '0';
	if (hi === undefined) {
		const n = lo >= 1 ? lo : 1;
		return `≥${n}`;
	}
	if (lo === 0) return `<${hi}`;
	return `${lo}–${hi}`;
}

export function trendOption(data: TrendFrameData, t: AnalysisTokens) {
	const series = (data.series ?? []).map((s, i) => ({
		name: s.name,
		type: 'line' as const,
		showSymbol: false,
		lineStyle: { width: 2, color: seriesColor(t, i) },
		itemStyle: { color: seriesColor(t, i) },
		data: (s.points ?? []).map((pt) => [pt.t, pt.v] as [string, number])
	}));
	const showLegend = series.length > 1;
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 24, top: showLegend ? 48 : 24, bottom: 32, containLabel: false },
		legend: { show: showLegend, top: 0, textStyle: { color: t.text } },
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

export function breakdownOption(data: BreakdownFrameData, t: AnalysisTokens) {
	const rows = data.rows ?? [];
	const dim = data.dim;
	const max = rows.reduce((m, r) => Math.max(m, r.value), 0);
	const clickable = (key: string) => isDrillableMark(dim, key);
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 120, right: 24, top: 8, bottom: 24, containLabel: false },
		tooltip: { trigger: 'item' },
		xAxis: {
			type: 'value',
			max: max > 0 ? max : undefined,
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		yAxis: {
			type: 'category',
			inverse: true,
			data: rows.map((r) => r.label ?? r.key),
			axisLabel: { color: t.text },
			axisLine: { lineStyle: { color: t.border } }
		},
		series: [
			{
				type: 'bar',
				data: rows.map((r) => ({
					value: r.value,
					key: r.key,
					dim,
					clickable: clickable(r.key),
					itemStyle: { color: seriesColor(t, 0) }
				})),
				emphasis: { focus: 'series' }
			}
		]
	};
}

export function distributionOption(data: DistributionFrameData, t: AnalysisTokens) {
	const labels = data.bins.map((b) => distributionBinLabel(data.measure, b.lo, b.hi));
	const counts = data.bins.map((b) => b.n);
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 16, top: 8, bottom: 72, containLabel: false },
		tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
		xAxis: {
			type: 'category',
			data: labels,
			axisLabel: { color: t.muted, rotate: labels.some((l) => l.length > 8) ? 35 : 0 },
			axisLine: { lineStyle: { color: t.border } }
		},
		yAxis: {
			type: 'value',
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		series: [
			{
				type: 'bar',
				data: counts.map((n, i) => ({
					value: n,
					bin: data.bins[i] satisfies DistributionBin,
					clickable: data.drillDim ? isDrillableMark(data.drillDim, String(i)) : false
				})),
				itemStyle: { color: seriesColor(t, 0) }
			}
		]
	};
}

/** Sparse quality score band + median line; gaps allowed (connectNulls false). */
export function qualityOption(data: QualityFrameData, t: AnalysisTokens) {
	const byT = new Map(data.points.map((p) => [p.t, p]));
	const slots = bucketStarts(data.tz, data.bucket, data.from, data.to).map((ms) => {
		const time = instantKey(data.tz, new Date(ms));
		return { time, p: byT.get(time) };
	});
	const medianData = slots.map(({ time, p }) => [time, p?.median ?? null] as [string, number | null]);
	// Stack a transparent p25 baseline under a (p75 − p25) span so the band sits on the scores,
	// not on the axis.
	const p25Data = slots.map(({ time, p }) => {
		if (!p || p.p25 === undefined) return [time, null] as [string, number | null];
		return [time, p.p25] as [string, number];
	});
	const bandData = slots.map(({ time, p }) => {
		if (!p || p.p25 === undefined || p.p75 === undefined) return [time, null] as [string, number | null];
		return [time, p.p75 - p.p25] as [string, number];
	});
	const medianSeries: Record<string, unknown> = {
		name: 'median',
		type: 'line',
		showSymbol: false,
		connectNulls: false,
		lineStyle: { width: 2, color: seriesColor(t, 0) },
		itemStyle: { color: seriesColor(t, 0) },
		data: medianData
	};
	if (data.baselineMedian !== undefined) {
		medianSeries.markLine = {
			symbol: 'none',
			lineStyle: { type: 'dashed', color: t.muted },
			data: [{ yAxis: data.baselineMedian, name: 'baseline' }]
		};
	}
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 24, top: 24, bottom: 32, containLabel: false },
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
			min: 0,
			max: 1,
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		series: [
			{
				name: 'p25',
				type: 'line',
				stack: 'band',
				showSymbol: false,
				connectNulls: false,
				lineStyle: { width: 0, opacity: 0 },
				itemStyle: { color: seriesColor(t, 1) },
				data: p25Data
			},
			{
				name: 'p25–p75',
				type: 'line',
				stack: 'band',
				showSymbol: false,
				connectNulls: false,
				lineStyle: { width: 0 },
				areaStyle: { color: seriesColor(t, 1), opacity: 0.35 },
				itemStyle: { color: seriesColor(t, 1) },
				data: bandData
			},
			medianSeries
		]
	};
}

export function optionForKind(
	kind: 'trend' | 'breakdown' | 'distribution' | 'quality',
	data: TrendFrameData | BreakdownFrameData | DistributionFrameData | QualityFrameData,
	t: AnalysisTokens
) {
	switch (kind) {
		case 'trend':
			return trendOption(data as TrendFrameData, t);
		case 'breakdown':
			return breakdownOption(data as BreakdownFrameData, t);
		case 'distribution':
			return distributionOption(data as DistributionFrameData, t);
		case 'quality':
			return qualityOption(data as QualityFrameData, t);
	}
}
