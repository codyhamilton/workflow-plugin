import { describe, expect, it } from 'vitest';
import { render } from 'svelte/server';
import BreakdownChart from './chart-frame/BreakdownChart.svelte';
import DistributionChart from './chart-frame/DistributionChart.svelte';
import QualityChart from './chart-frame/QualityChart.svelte';
import TrendChart from './chart-frame/TrendChart.svelte';
import {
	breakdownOption,
	distributionOption,
	qualityOption,
	trendOption
} from './chart-frame/options';
import { ANALYSIS_DEFAULT_TOKENS } from './chart-frame/tokens';

const SOLARIZED = new Set(['#002b36', '#fdf6e3', '#839496', '#657b83']);
const TOKENS = ANALYSIS_DEFAULT_TOKENS;

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

function expectAnalysisSeriesColors(option: unknown) {
	const found = colors(option);
	const seriesColors = found.filter((c) => TOKENS.series.map((s) => s.toLowerCase()).includes(c));
	expect(seriesColors.length).toBeGreaterThan(0);
	for (const c of found) {
		expect(SOLARIZED.has(c)).toBe(false);
	}
}

describe('chart-frame options use analysis tokens', () => {
	it('trend', () => {
		const option = trendOption(
			{
				measure: 'hook_events',
				bucket: 'day',
				series: [{ name: 'events', points: [{ t: '2024-01-01T00:00:00Z', v: 3 }] }]
			},
			TOKENS
		);
		expectAnalysisSeriesColors(option);
	});

	it('zero-fills count gaps and leaves cost sparse', () => {
		const span = {
			bucket: 'day' as const,
			tz: 'UTC',
			from: new Date('2024-01-01T00:00:00Z'),
			to: new Date('2024-01-03T00:00:00Z'),
			series: [
				{
					name: 'all',
					points: [
						{ t: '2024-01-01T00:00:00Z', v: 2 },
						{ t: '2024-01-03T00:00:00Z', v: 4 }
					]
				}
			]
		};
		const filled = trendOption({ ...span, measure: 'hook_events' }, TOKENS);
		expect((filled.series as { data: unknown[] }[])[0].data).toEqual([
			['2024-01-01T00:00:00Z', 2],
			['2024-01-02T00:00:00Z', 0],
			['2024-01-03T00:00:00Z', 4]
		]);
		const cost = trendOption({ ...span, measure: 'cost_usd' }, TOKENS);
		expect((cost.series as { data: unknown[] }[])[0].data).toEqual([
			['2024-01-01T00:00:00Z', 2],
			['2024-01-03T00:00:00Z', 4]
		]);
	});

	it('makes breakdown trend series drillable and skips __other__', () => {
		const option = trendOption(
			{
				measure: 'hook_events',
				bucket: 'day',
				breakdownDim: 'harness',
				series: [
					{ name: 'cursor', points: [{ t: '2024-01-01T00:00:00Z', v: 3 }] },
					{ name: '__other__', points: [{ t: '2024-01-01T00:00:00Z', v: 1 }] }
				]
			},
			TOKENS
		);
		const series = option.series as {
			triggerEvent?: string | boolean;
			data: { key: string; dim: string; clickable: boolean; value: [string, number] }[];
		}[];
		expect(series[0].triggerEvent).toBe('line');
		expect(option.legend).toMatchObject({ selectedMode: false });
		expect(series[0].data[0]).toEqual({
			value: ['2024-01-01T00:00:00Z', 3],
			key: 'cursor',
			dim: 'harness',
			clickable: true
		});
		expect(series[1].data[0].clickable).toBe(false);
	});

	it('breakdown', () => {
		const option = breakdownOption(
			{
				measure: 'hook_events',
				dim: 'repo_id',
				rows: [{ key: 'alpha', value: 2 }]
			},
			TOKENS
		);
		expectAnalysisSeriesColors(option);
	});

	it('distribution', () => {
		const option = distributionOption(
			{
				measure: 'cost_usd',
				bins: [{ lo: 0, n: 1 }, { lo: 0, hi: 0.01, n: 2 }]
			},
			TOKENS
		);
		expectAnalysisSeriesColors(option);
	});

	it('quality', () => {
		const option = qualityOption(
			{
				kind: 'design',
				bucket: 'day',
				points: [
					{ t: '2024-01-01T00:00:00Z', median: 0.4, p25: 0.3, p75: 0.5 },
					{ t: '2024-01-03T00:00:00Z', median: 0.6, p25: 0.5, p75: 0.7 }
				],
				baselineMedian: 0.35,
				from: new Date('2024-01-01T00:00:00Z'),
				to: new Date('2024-01-03T23:59:59Z'),
				tz: 'UTC'
			},
			TOKENS
		);
		expectAnalysisSeriesColors(option);
		const median = (option.series as { name?: string; connectNulls?: boolean; data?: unknown[] }[]).find(
			(s) => s.name === 'median'
		);
		expect(median?.connectNulls).toBe(false);
		expect(median?.data).toEqual([
			['2024-01-01T00:00:00Z', 0.4],
			['2024-01-02T00:00:00Z', null],
			['2024-01-03T00:00:00Z', 0.6]
		]);
		const series = option.series as { name?: string; stack?: string; data?: unknown[] }[];
		const baseline = series.find((s) => s.name === 'p25');
		const band = series.find((s) => s.name === 'p25–p75');
		expect(baseline?.stack).toBe('band');
		expect(band?.stack).toBe('band');
		expect(baseline?.data).toEqual([
			['2024-01-01T00:00:00Z', 0.3],
			['2024-01-02T00:00:00Z', null],
			['2024-01-03T00:00:00Z', 0.5]
		]);
		const bandData = band?.data as [string, number | null][];
		expect(bandData[0]?.[0]).toBe('2024-01-01T00:00:00Z');
		expect(bandData[0]?.[1]).toBeCloseTo(0.2);
		expect(bandData[1]).toEqual(['2024-01-02T00:00:00Z', null]);
		expect(bandData[2]?.[0]).toBe('2024-01-03T00:00:00Z');
		expect(bandData[2]?.[1]).toBeCloseTo(0.2);
	});
});

describe('chart-frame components render without throwing', () => {
	it('trend', () => {
		const { body } = render(TrendChart, {
			props: {
				testid: 'trend-frame',
				data: {
					measure: 'hook_events',
					bucket: 'day',
					series: [{ name: 'events', points: [{ t: '2024-01-01T00:00:00Z', v: 1 }] }]
				}
			}
		});
		expect(body).toContain('data-testid="trend-frame"');
		expect(body).toContain('data-ready="false"');
	});

	it('breakdown', () => {
		const { body } = render(BreakdownChart, {
			props: {
				testid: 'breakdown-frame',
				data: {
					measure: 'hook_events',
					dim: 'repo_id',
					rows: [{ key: 'alpha', value: 2 }, { key: '__other__', value: 1 }]
				}
			}
		});
		expect(body).toContain('data-testid="breakdown-frame"');
	});

	it('distribution', () => {
		const { body } = render(DistributionChart, {
			props: {
				testid: 'distribution-frame',
				data: {
					measure: 'tokens_in',
					bins: [{ lo: 0, n: 4 }, { lo: 1, hi: 2, n: 1 }]
				}
			}
		});
		expect(body).toContain('data-testid="distribution-frame"');
	});

	it('quality', () => {
		const { body } = render(QualityChart, {
			props: {
				testid: 'quality-frame',
				data: {
					kind: 'brief',
					bucket: 'week',
					points: [{ t: '2024-01-01T00:00:00Z', median: 0.5 }],
					from: new Date('2024-01-01T00:00:00Z'),
					to: new Date('2024-01-07T00:00:00Z'),
					tz: 'UTC'
				}
			}
		});
		expect(body).toContain('data-testid="quality-frame"');
	});
});
