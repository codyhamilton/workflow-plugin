// Pure ECharts sankey option builder. No DOM and no echarts import, so it is
// testable in isolation and the bundle only pulls the pieces EChart.svelte registers.
import type { Tokens } from './theme';

export interface SankeyNode {
	name: string;
	label?: string;
}
export interface SankeyLink {
	source: string;
	target: string;
	value: number;
}

export function sankeyOption(p: { nodes: SankeyNode[]; links: SankeyLink[] }, t: Tokens) {
	const nodes = (p.nodes ?? []).map((n) =>
		n.label ? { name: n.name, label: { formatter: n.label } } : { name: n.name }
	);
	const links = (p.links ?? [])
		.filter((l) => l.value > 0)
		.map((l) => ({ source: l.source, target: l.target, value: l.value }));
	return {
		animation: false,
		backgroundColor: 'transparent',
		tooltip: { trigger: 'item' },
		series: [
			{
				type: 'sankey',
				emphasis: { focus: 'adjacency' },
				lineStyle: { color: t.series[0], opacity: 0.35, curveness: 0.5 },
				label: { color: t.text },
				itemStyle: { borderColor: t.bg, borderWidth: 1 },
				data: nodes,
				links
			}
		]
	};
}
