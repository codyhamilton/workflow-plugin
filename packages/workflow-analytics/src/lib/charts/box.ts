// Pure ECharts horizontal boxplot option builder. No DOM and no echarts import.
import type { Tokens } from './theme';

export interface BoxRow {
	name: string;
	min: number;
	p25: number;
	median: number;
	p75: number;
	max: number;
	marker?: number;
}

export function boxOption(p: { rows: BoxRow[] }, t: Tokens) {
	const rows = p.rows ?? [];
	const marked = rows.filter((r) => typeof r.marker === 'number');
	const series: object[] = [
		{
			type: 'boxplot',
			itemStyle: { color: t.surface, borderColor: t.series[0] },
			emphasis: { itemStyle: { borderColor: t.accent } },
			data: rows.map((r) => [r.min, r.p25, r.median, r.p75, r.max])
		}
	];
	if (marked.length > 0) {
		series.push({
			type: 'scatter',
			itemStyle: { color: t.danger },
			data: marked.map((r) => [r.marker, r.name])
		});
	}
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 120, right: 24, top: 8, bottom: 24, containLabel: false },
		tooltip: { trigger: 'item' },
		xAxis: {
			type: 'value',
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		yAxis: {
			type: 'category',
			inverse: true,
			data: rows.map((r) => r.name),
			axisLabel: { color: t.text },
			axisLine: { lineStyle: { color: t.border } },
			axisTick: { show: false }
		},
		series
	};
}
