import { describe, expect, it } from 'vitest';
import type { AggregateRequest } from '../aggregate';
import { applyDrillToRequest } from './request-mutate';

describe('applyDrillToRequest', () => {
	it('does not add __other__ as a filter', () => {
		const req: AggregateRequest = {
			window: { tz: 'UTC', preset: '30d' },
			ask: { ask: 'breakdown', measure: 'hook_events', dim: 'harness' }
		};
		const next = applyDrillToRequest(req, 'harness', '__other__', false, new Date());
		expect(next.filters).toEqual(req.filters);
		expect(next.ask).toEqual(req.ask);
	});
});
