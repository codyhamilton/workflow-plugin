import { describe, expect, it } from 'vitest';
import { boxOption, type BoxRow } from './box';
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

const rows: BoxRow[] = [
	{ name: 'a', min: 1, p25: 2, median: 3, p75: 4, max: 5 },
	{ name: 'b', min: 2, p25: 3, median: 4, p75: 5, max: 6 }
];

describe('boxOption', () => {
	it('puts one category per row on an inverted horizontal axis', () => {
		const option = boxOption({ rows }, TOKENS);
		expect(option.yAxis.type).toBe('category');
		expect(option.yAxis.inverse).toBe(true);
		expect(option.yAxis.data).toEqual(['a', 'b']);
		expect(option.xAxis.type).toBe('value');
	});

	it('maps each row to a [min,p25,median,p75,max] box', () => {
		const option = boxOption({ rows }, TOKENS);
		expect(option.series[0].type).toBe('boxplot');
		expect(option.series[0].data[0]).toEqual([1, 2, 3, 4, 5]);
		expect(option.series[0].data).toHaveLength(2);
	});

	it('adds no scatter series when no row has a marker', () => {
		const option = boxOption({ rows }, TOKENS);
		expect(option.series).toHaveLength(1);
		expect(option.series.filter((s) => s.type === 'scatter')).toHaveLength(0);
	});

	it('adds exactly one scatter series with only the marked rows', () => {
		const option = boxOption(
			{ rows: [{ ...rows[0], marker: 9 }, { ...rows[1] }] },
			TOKENS
		);
		const scatter = option.series.filter((s) => s.type === 'scatter');
		expect(scatter).toHaveLength(1);
		expect(scatter[0].data).toEqual([[9, 'a']]);
	});

	it('uses only token colours', () => {
		const option = boxOption({ rows: [{ ...rows[0], marker: 9 }, rows[1]] }, TOKENS);
		for (const c of colors(option)) expect(TOKEN_SET.has(c)).toBe(true);
	});
});
