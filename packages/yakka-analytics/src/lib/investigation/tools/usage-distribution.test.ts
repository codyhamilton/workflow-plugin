import { describe, expect, it } from 'vitest';
import { render } from 'svelte/server';
import type { AggregateRequest, DistributionResult } from '$lib/aggregate';
import type { Facets } from '$lib/types';
import UsageTool from './UsageTool.svelte';

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

function row(k: string, n: number) {
	return {
		k,
		n,
		unpriced: 0,
		min: 0,
		p25: 0,
		median: 0,
		p75: 0,
		p95: 0,
		max: 0,
		bins: [{ lo: 0, hi: 0.01, n }]
	};
}

describe('UsageTool distribution', () => {
	it('draws one histogram per model row', () => {
		const request: AggregateRequest = {
			window: { preset: '7d', tz: 'UTC' },
			ask: { ask: 'distribution', measure: 'cost_usd', grain: 'call', dim: 'model' }
		};
		const primary: DistributionResult = {
			ask: 'distribution',
			window: { from: '2024-01-01T00:00:00.000Z', to: '2024-01-07T00:00:00.000Z' },
			controls: FACETS,
			measure: 'cost_usd',
			grain: 'call',
			dim: 'model',
			rows: [row('model-a', 1), row('model-b', 2)]
		};
		const { body } = render(UsageTool, {
			props: {
				request,
				primary,
				commit: () => {},
				onBrushEnd: () => {},
				onDrill: () => {}
			}
		});
		expect(body).toContain('data-testid="investigation-usage-distribution"');
		expect(body.match(/data-testid="investigation-usage-distribution-row"/g)?.length).toBe(2);
		expect(body).toContain('model-a');
		expect(body).toContain('model-b');
	});
});
