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
		const median = (option.series as { name?: string; connectNulls?: boolean }[]).find(
			(s) => s.name === 'median'
		);
		expect(median?.connectNulls).toBe(false);
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
