import { describe, expect, it } from 'vitest';
import { builderTileSearchParams, tileExtraParams } from './dashboard-tile';
import { chartParamsFromQuery } from './views';

describe('tileExtraParams', () => {
	it('round-trips builder URL short keys through stored params to API extras', () => {
		const q = new URLSearchParams([
			['m', 'cost_usd'],
			['d', 'model'],
			['b', 'day'],
			['c', 'bar'],
			['top', '5']
		]);
		const stored = chartParamsFromQuery('builder', q);
		expect(stored).toEqual({
			measure: 'cost_usd',
			dim: 'model',
			bucket: 'day',
			chart: 'bar',
			top: '5'
		});
		expect(tileExtraParams('builder', stored)).toEqual({
			measure: 'cost_usd',
			dim: 'model',
			bucket: 'day',
			top: '5'
		});
		expect(builderTileSearchParams(stored).toString()).toBe(q.toString());
	});

	it('maps usage measure and grain from a saved query string', () => {
		const stored = chartParamsFromQuery(
			'usage',
			new URLSearchParams('measure=cost_usd&grain=conversation&range=7d')
		);
		expect(stored).toEqual({ measure: 'cost_usd', grain: 'conversation' });
		expect(tileExtraParams('usage', stored)).toEqual({
			measure: 'cost_usd',
			grain: 'conversation'
		});
	});

	it('maps hooks stored dim to split dimension in API extra', () => {
		expect(tileExtraParams('hooks', { dim: 'tool', bucket: 'week' })).toEqual({
			measure: 'hook_events',
			bucket: 'week',
			dim: 'tool'
		});
	});
});
