import { describe, expect, it } from 'vitest';
import { scoreBandOption, scoreBandTableRows } from './score-series';
import { DEFAULT_TOKENS } from './theme';

const TOKENS = DEFAULT_TOKENS;
const TZ = 'UTC';

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

const from = new Date('2024-01-01T00:00:00.000Z');
const to = new Date('2024-01-03T23:59:59.000Z');

const sparse = {
	points: [
		{ t: '2024-01-01T00:00:00Z', n: 2, p25: 0.2, median: 0.3, p75: 0.4 },
		{ t: '2024-01-03T00:00:00Z', n: 3, p25: 0.5, median: 0.6, p75: 0.7 }
	],
	bucket: 'day' as const,
	from,
	to,
	tz: TZ
};

describe('scoreBandOption', () => {
	it('uses a time x-axis and connectNulls false on line series', () => {
		const option = scoreBandOption(sparse, TOKENS);
		expect(option.xAxis.type).toBe('time');
		for (const s of option.series) {
			if (s.type === 'line') expect(s.connectNulls).toBe(false);
		}
	});

	it('maps sparse points to median and stacked band series with null gaps', () => {
		const option = scoreBandOption(sparse, TOKENS);
		const median = option.series.find((s) => s.name === 'median');
		expect(median?.data).toEqual([
			['2024-01-01T00:00:00Z', 0.3],
			['2024-01-02T00:00:00Z', null],
			['2024-01-03T00:00:00Z', 0.6]
		]);
		const band = option.series.find((s) => s.name === 'p25–p75');
		expect(band?.stack).toBe('band');
		expect(band?.data[0]).toEqual(['2024-01-01T00:00:00Z', 0.2]);
		expect(band?.data[1]).toEqual(['2024-01-02T00:00:00Z', null]);
		expect(band?.data[2]?.[0]).toBe('2024-01-03T00:00:00Z');
		expect(band?.data[2]?.[1]).toBeCloseTo(0.2, 5);
	});

	it('adds a baseline markLine only when baselineMedian is set', () => {
		const withBase = scoreBandOption({ ...sparse, baselineMedian: 0.35 }, TOKENS);
		const median = withBase.series.find((s) => s.name === 'median');
		expect(median?.markLine?.data).toEqual([{ yAxis: 0.35 }]);
		const plain = scoreBandOption(sparse, TOKENS);
		const plainMedian = plain.series.find((s) => s.name === 'median');
		expect(plainMedian?.markLine).toBeUndefined();
	});

	it('uses only token colours', () => {
		const option = scoreBandOption({ ...sparse, baselineMedian: 0.35 }, TOKENS);
		for (const c of colors(option)) expect(TOKEN_SET.has(c)).toBe(true);
	});
});

describe('scoreBandTableRows', () => {
	it('leaves missing buckets empty, not zero', () => {
		const rows = scoreBandTableRows(sparse);
		expect(rows).toHaveLength(3);
		const gap = rows.find((r) => r.t === '2024-01-02T00:00:00Z');
		expect(gap).toEqual({ t: '2024-01-02T00:00:00Z', n: '', p25: '', median: '', p75: '' });
	});
});
