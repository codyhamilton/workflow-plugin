import { describe, expect, it } from 'vitest';
import type { AggregateRequest } from '../aggregate';
import {
	investigationRequestToSearch,
	isInvestigationQuery,
	InvestigationUrlError,
	parseInvestigationRequest
} from './request-url';

function roundTrip(request: AggregateRequest): AggregateRequest {
	const params = investigationRequestToSearch(request);
	return parseInvestigationRequest(params);
}

describe('isInvestigationQuery', () => {
	it('is false for empty query', () => {
		expect(isInvestigationQuery(new URLSearchParams(''))).toBe(false);
	});

	it('is true when ask is set', () => {
		expect(isInvestigationQuery(new URLSearchParams('ask=trend&measure=hook_events&bucket=day'))).toBe(
			true
		);
	});
});

describe('parseInvestigationRequest', () => {
	it('rejects missing ask', () => {
		expect(() => parseInvestigationRequest(new URLSearchParams(''))).toThrow(InvestigationUrlError);
	});

	it('missing range is the 30d preset', () => {
		const req = parseInvestigationRequest(
			new URLSearchParams('ask=trend&measure=hook_events&bucket=day')
		);
		expect(req.window?.preset).toBe('30d');
		expect(req.window?.from).toBeUndefined();
	});

	it('rejects unknown ask', () => {
		expect(() => parseInvestigationRequest(new URLSearchParams('ask=overview'))).toThrow(
			InvestigationUrlError
		);
	});
});

describe('investigation round-trip', () => {
	it('trend hook_events', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('trend cost_usd', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'trend', measure: 'cost_usd', bucket: 'week' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('trend with breakdown dim model', () => {
		const req: AggregateRequest = {
			window: { preset: '30d' },
			ask: { ask: 'trend', measure: 'cost_usd', bucket: 'day', dim: 'model' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('breakdown on repo_id', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'breakdown', measure: 'cost_usd', dim: 'repo_id' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('distribution cost_usd grain call', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'distribution', measure: 'cost_usd', grain: 'call' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('quality kind design', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'quality', kind: 'design', bucket: 'day' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('conversations', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'conversations' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('conversation with id', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'conversation', id: 'conv-1' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('executions with optional bucket', () => {
		const withBucket: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'executions', bucket: 'week' }
		};
		expect(roundTrip(withBucket)).toEqual(withBucket);
		const bare: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'executions' }
		};
		expect(roundTrip(bare)).toEqual(bare);
	});

	it('include and exclude filters', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			filters: {
				include: { harness: ['claude'], repo_id: ['r1'] },
				exclude: { model: ['gpt-4o'] }
			},
			ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
		};
		expect(roundTrip(req)).toEqual(req);
	});

	it('preset 7d window', () => {
		const req: AggregateRequest = {
			window: { preset: '7d' },
			ask: { ask: 'breakdown', measure: 'hook_events', dim: 'harness' }
		};
		const params = investigationRequestToSearch(req);
		expect(params.get('range')).toBe('7d');
		expect(roundTrip(req)).toEqual(req);
	});

	it('drops a tz that is not an IANA zone', () => {
		const req = parseInvestigationRequest(
			new URLSearchParams('ask=trend&measure=hook_events&bucket=day&range=7d&tz=Not/AZone')
		);
		expect(req.window?.preset).toBe('7d');
		expect(req.window?.tz).toBeUndefined();
		const injected = parseInvestigationRequest(
			new URLSearchParams('ask=trend&measure=hook_events&bucket=day&range=7d&tz=UTC%0d%0aX')
		);
		expect(injected.window?.tz).toBeUndefined();
	});

	it('custom from/to window', () => {
		const req: AggregateRequest = {
			window: {
				from: '2025-01-01T00:00:00.000Z',
				to: '2025-02-01T00:00:00.000Z',
				tz: 'America/New_York'
			},
			ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
		};
		const params = investigationRequestToSearch(req);
		expect(params.get('from')).toBe(req.window?.from);
		expect(params.get('to')).toBe(req.window?.to);
		expect(params.get('tz')).toBe('America/New_York');
		expect(roundTrip(req)).toEqual(req);
	});

	it('does not read legacy report keys', () => {
		const q = new URLSearchParams(
			'ask=trend&measure=hook_events&bucket=day&metric=commits&m=cost_usd&group=harness&report=usage'
		);
		const req = parseInvestigationRequest(q);
		expect(req.ask).toEqual({ ask: 'trend', measure: 'hook_events', bucket: 'day' });
		const out = investigationRequestToSearch(req);
		expect(out.has('metric')).toBe(false);
		expect(out.has('m')).toBe(false);
		expect(out.has('group')).toBe(false);
		expect(out.has('report')).toBe(false);
	});
});
