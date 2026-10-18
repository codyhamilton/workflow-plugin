// Histogram option builder for GET /v1/analytics/distribution bins (fixed server edges).
import type { DistributionBin } from '$lib/types';
import type { Tokens } from './theme';

export type DistributionMeasure =
	| 'cost_usd'
	| 'tokens_in'
	| 'tokens_out'
	| 'tokens_cache_read'
	| 'tokens_cache_write'
	| 'tokens_reasoning';

export interface DistributionProps {
	measure: DistributionMeasure;
	bins: DistributionBin[];
}

function trimZeros(s: string): string {
	return s.replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
}

function fmtCostEdge(v: number): string {
	if (v === 0) return '$0';
	if (v >= 1) return `$${v}`;
	if (v >= 0.01) return `$${trimZeros(v.toFixed(2))}`;
	return `$${trimZeros(v.toFixed(4))}`;
}

/** Human-readable bin interval from API lo/hi (cost uses powers of ten; tokens use powers of two). */
export function binLabel(measure: DistributionMeasure, lo: number, hi?: number): string {
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

export function distributionOption(p: DistributionProps, t: Tokens) {
	const labels = p.bins.map((b) => binLabel(p.measure, b.lo, b.hi));
	const counts = p.bins.map((b) => b.n);
	const max = counts.reduce((m, n) => Math.max(m, n), 0);
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 16, top: 8, bottom: 72, containLabel: false },
		tooltip: {
			trigger: 'axis',
			axisPointer: { type: 'shadow' }
		},
		xAxis: {
			type: 'category',
			data: labels,
			axisLabel: { color: t.muted, rotate: 45, fontSize: 10 },
			axisLine: { lineStyle: { color: t.border } },
			axisTick: { show: false }
		},
		yAxis: {
			type: 'value',
			max: max > 0 ? undefined : 1,
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		series: [
			{
				type: 'bar',
				data: counts,
				itemStyle: { color: t.series[0] },
				emphasis: { itemStyle: { color: t.accent } }
			}
		]
	};
}
