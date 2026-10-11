import { describe, expect, it } from 'vitest';
import { sankeyOption, type SankeyLink, type SankeyNode } from './sankey';
import { DEFAULT_TOKENS } from './theme';

const TOKENS = DEFAULT_TOKENS;

function colors(value: unknown, out: string[] = []): string[] {
	if (typeof value === 'string') {
		if (/^#[0-9a-fA-F]{3,8}$/.test(value)) out.push(value.toLowerCase());
	} else if (Array.isArray(value)) {
		for (const v of value) colors(v, out);
	} else if (value && typeof value === 'object') {
		for (const v of Object.values(value)) colors(v, out);
	}
	return out;
}

const TOKEN_SET = new Set(
	[
		TOKENS.bg,
		TOKENS.surface,
		TOKENS.text,
		TOKENS.muted,
		TOKENS.border,
		TOKENS.accent,
		TOKENS.danger,
		...TOKENS.series
	].map((c) => c.toLowerCase())
);

const nodes: SankeyNode[] = [{ name: 'a', label: 'Alpha' }, { name: 'b' }];
const links: SankeyLink[] = [
	{ source: 'a', target: 'b', value: 3 },
	{ source: 'b', target: 'a', value: 0 },
	{ source: 'a', target: 'b', value: -2 }
];

describe('sankeyOption', () => {
	it('maps nodes and links into the single sankey series', () => {
		const option = sankeyOption({ nodes, links }, TOKENS);
		expect(option.series).toHaveLength(1);
		expect(option.series[0].type).toBe('sankey');
		expect(option.series[0].data.map((n) => n.name)).toEqual(['a', 'b']);
		expect(option.series[0].data[0].label).toEqual({ formatter: 'Alpha' });
		expect(option.series[0].links).toHaveLength(1);
		expect(option.series[0].links[0]).toEqual({ source: 'a', target: 'b', value: 3 });
	});

	it('drops links whose value is not positive', () => {
		const option = sankeyOption({ nodes, links }, TOKENS);
		expect(option.series[0].links.every((l) => l.value > 0)).toBe(true);
	});

	it('sets adjacency emphasis and a translucent token line colour', () => {
		const option = sankeyOption({ nodes, links }, TOKENS);
		expect(option.series[0].emphasis).toEqual({ focus: 'adjacency' });
		expect(TOKEN_SET.has(option.series[0].lineStyle.color.toLowerCase())).toBe(true);
		expect(option.series[0].lineStyle.opacity).toBeGreaterThan(0);
	});

	it('uses only token colours', () => {
		const option = sankeyOption({ nodes, links }, TOKENS);
		for (const c of colors(option)) expect(TOKEN_SET.has(c)).toBe(true);
	});
});
