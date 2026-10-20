import { describe, expect, it } from 'vitest';
import { render } from 'svelte/server';
import type { AggregateRequest, QualityResult } from '$lib/aggregate';
import type { Facets } from '$lib/types';
import QualityTool from './QualityTool.svelte';

const FACETS: Facets = {
	repos: [],
	harnesses: [],
	kinds: [],
	plans: [],
	events: [],
	models: [],
	norm_events: [],
	tools: [],
	checks: []
};

describe('QualityTool series window', () => {
	it('draws the score series from the boundary window when the URL is a preset', () => {
		const request: AggregateRequest = {
			window: { preset: '7d', tz: 'UTC' },
			ask: { ask: 'quality', kind: 'design', bucket: 'day' }
		};
		const primary: QualityResult = {
			ask: 'quality',
			window: { from: '2024-01-01T00:00:00.000Z', to: '2024-01-07T00:00:00.000Z' },
			controls: FACETS,
			scores: {
				kind: 'design',
				checks: [{ name: 'd.alpha', n: 2, min: 0.1, p25: 0.2, median: 0.3, p75: 0.4, max: 0.5 }]
			},
			baseline: { kind: 'design', checks: { 'd.alpha': { n: 10, p25: 0.15, median: 0.35, p75: 0.55 } } },
			scoreSeries: {
				kind: 'design',
				bucket: 'day',
				checks: [
					{
						name: 'd.alpha',
						points: [
							{ t: '2024-01-01T00:00:00Z', n: 1, p25: 0.2, median: 0.3, p75: 0.4 },
							{ t: '2024-01-03T00:00:00Z', n: 1, p25: 0.4, median: 0.5, p75: 0.6 }
						]
					}
				]
			}
		};
		const { body } = render(QualityTool, {
			props: {
				request,
				primary,
				tz: 'UTC',
				commit: () => {},
				onBrushEnd: () => {}
			}
		});
		expect(body).toContain('data-testid="investigation-quality-series"');
		expect(body).toContain('data-testid="investigation-quality-d.alpha-w-median"');
		expect(body).toContain('>0.3<');
		expect(body).toContain('data-testid="investigation-quality-d.alpha-b-median"');
		expect(body).toContain('>0.35<');
	});
});
