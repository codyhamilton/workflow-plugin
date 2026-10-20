import { describe, expect, it } from 'vitest';
import { aggregate, type AggregateRequest, type Fetcher } from './aggregate';
import type {
	Baselines,
	ConversationDetail,
	Conversations,
	DistributionResponse,
	Executions,
	Facets,
	QueryResponse,
	ScoreSeries,
	Scores
} from './types';

const NOW = new Date('2025-06-15T12:00:00.000Z');
const DAY = 86400000;

const FACETS: Facets = {
	repos: ['r1'],
	harnesses: ['h1', 'h2'],
	kinds: ['design'],
	plans: [],
	events: [],
	models: ['m1'],
	norm_events: [],
	tools: [],
	checks: []
};

function facetFetcher(extra: Fetcher = defaultDataFetcher()): Fetcher {
	return (slot, path, params) => {
		if (path === 'analytics/facets') return Promise.resolve(FACETS);
		return extra(slot, path, params);
	};
}

function defaultDataFetcher(handlers: Record<string, (params: URLSearchParams) => unknown> = {}): Fetcher {
	return (_slot, path, params) => {
		const h = handlers[path];
		if (h) return Promise.resolve(h(params));
		return Promise.resolve({});
	};
}

describe('aggregate', () => {
	it('trend returns series from the query read', async () => {
		const query: QueryResponse = {
			measure: 'hook_events',
			bucket: 'day',
			dims: [],
			rows: [{ t: '2025-06-01T00:00:00Z', k: [], v: 3 }],
			partial: true
		};
		const fetcher = facetFetcher(
			defaultDataFetcher({
				'analytics/query': () => query
			})
		);
		const req: AggregateRequest = {
			window: { preset: '7d', tz: 'UTC' },
			ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
		};
		const r = await aggregate(req, { fetcher, now: NOW });
		expect(r.ask).toBe('trend');
		if (r.ask !== 'trend') return;
		expect(r.series).toEqual([{ key: 'all', points: [{ t: '2025-06-01T00:00:00Z', v: 3 }] }]);
		expect(r.partial).toBe(true);
		expect(r.controls).toEqual(FACETS);
	});

	it('breakdown returns per-dim series', async () => {
		const query: QueryResponse = {
			measure: 'cost_usd',
			bucket: 'none',
			dims: ['model'],
			rows: [{ k: ['m1'], v: 1.5 }]
		};
		const fetcher = facetFetcher(defaultDataFetcher({ 'analytics/query': () => query }));
		const r = await aggregate(
			{ window: { preset: '7d' }, ask: { ask: 'breakdown', measure: 'cost_usd', dim: 'model' } },
			{ fetcher, now: NOW }
		);
		expect(r.ask).toBe('breakdown');
		if (r.ask !== 'breakdown') return;
		expect(r.series[0]?.key).toBe('m1');
	});

	it('distribution passes rows through', async () => {
		const dist: DistributionResponse = {
			measure: 'cost_usd',
			grain: 'call',
			rows: [{ k: 'all', n: 1, unpriced: 0, min: 0, p25: 0, median: 0, p75: 0, p95: 0, max: 0, bins: [] }],
			ignored_filters: ['kind']
		};
		const fetcher = facetFetcher(defaultDataFetcher({ 'analytics/distribution': () => dist }));
		const r = await aggregate(
			{
				window: { preset: '7d' },
				ask: { ask: 'distribution', measure: 'cost_usd', grain: 'call' }
			},
			{ fetcher, now: NOW }
		);
		expect(r.ask).toBe('distribution');
		if (r.ask !== 'distribution') return;
		expect(r.rows).toEqual(dist.rows);
		expect(r.ignored_filters).toContain('kind');
	});

	it('quality composes scores, baselines, and score-series', async () => {
		const scores: Scores = { kind: 'design', checks: [] };
		const baseline: Baselines = { kind: 'design', checks: {} };
		const series: ScoreSeries = { kind: 'design', bucket: 'day', checks: [] };
		const fetcher = facetFetcher(
			defaultDataFetcher({
				'analytics/scores': () => scores,
				baselines: () => baseline,
				'analytics/score-series': () => series
			})
		);
		const r = await aggregate(
			{ window: { preset: '7d' }, ask: { ask: 'quality', kind: 'design', bucket: 'day' } },
			{ fetcher, now: NOW }
		);
		expect(r.ask).toBe('quality');
		if (r.ask !== 'quality') return;
		expect(r.scores).toBe(scores);
		expect(r.baseline).toBe(baseline);
		expect(r.scoreSeries).toBe(series);
	});

	it('conversations passes rows and next', async () => {
		const conv: Conversations = {
			rows: [{ conversation_id: 'c1', harness: 'h', repos: [], first_ts: '', last_ts: '', hook_events: 0, artifact_versions: 0, commits: 0, kinds: [], model: '', model_calls: 0, unpriced_calls: 0, cost_usd: 0, tokens_in: 0, tokens_out: 0 }],
			next: 'cursor'
		};
		const fetcher = facetFetcher(defaultDataFetcher({ 'analytics/conversations': () => conv }));
		const r = await aggregate(
			{ window: { preset: '7d' }, ask: { ask: 'conversations' } },
			{ fetcher, now: NOW }
		);
		expect(r.ask).toBe('conversations');
		if (r.ask !== 'conversations') return;
		expect(r.rows).toEqual(conv.rows);
		expect(r.next).toBe('cursor');
	});

	it('conversation passes detail and lists filter keys in ignored_filters', async () => {
		const detail: ConversationDetail = {
			conversation_id: 'c1',
			harness: 'h',
			repos: [],
			models: [],
			first_ts: '',
			last_ts: '',
			totals: {
				model_calls: 0,
				unpriced_calls: 0,
				cost_usd: 0,
				tokens_in: 0,
				tokens_out: 0,
				tokens_cache_read: 0,
				tokens_cache_write: 0,
				tokens_reasoning: 0
			},
			events: [],
			truncated: true
		};
		const fetcher = facetFetcher(defaultDataFetcher({ 'analytics/conversation': () => detail }));
		const r = await aggregate(
			{
				window: { from: '2025-06-01T00:00:00Z', to: '2025-06-15T00:00:00Z' },
				filters: { include: { harness: ['h1'] } },
				ask: { ask: 'conversation', id: 'c1' }
			},
			{ fetcher, now: NOW }
		);
		expect(r.ask).toBe('conversation');
		if (r.ask !== 'conversation') return;
		expect(r.detail).toBe(detail);
		expect(r.truncated).toBe(true);
		expect(r.ignored_filters).toContain('harness');
	});

	it('executions includes counts and optional series', async () => {
		const exec: Executions = {
			counts: { complete: 1, unreported: 0, started: 0 },
			rows: [],
			bucket: 'day',
			series: [{ key: 'complete', points: [{ t: '2025-06-01T00:00:00Z', n: 1 }] }]
		};
		const fetcher = facetFetcher(defaultDataFetcher({ 'analytics/executions': () => exec }));
		const r = await aggregate(
			{ window: { preset: '7d' }, ask: { ask: 'executions', bucket: 'day' } },
			{ fetcher, now: NOW }
		);
		expect(r.ask).toBe('executions');
		if (r.ask !== 'executions') return;
		expect(r.counts).toEqual(exec.counts);
		expect(r.series).toEqual(exec.series);
	});

	it('conversation_id exclude is ignored_filters only', async () => {
		const log: { path: string; params: URLSearchParams }[] = [];
		const inner = facetFetcher(defaultDataFetcher({ 'analytics/query': () => ({ measure: 'hook_events', bucket: 'day', dims: [], rows: [] }) }));
		const fetcher: Fetcher = (slot, path, params) => {
			log.push({ path, params: new URLSearchParams(params) });
			return inner(slot, path, params);
		};
		await aggregate(
			{
				window: { preset: '7d' },
				filters: { exclude: { conversation_id: ['c1'] } },
				ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
			},
			{ fetcher, now: NOW }
		);
		for (const { params } of log) {
			expect(params.getAll('conversation_id')).toEqual([]);
		}
		const r = await aggregate(
			{
				window: { preset: '7d' },
				filters: { exclude: { conversation_id: ['c1'] } },
				ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
			},
			{ fetcher, now: NOW }
		);
		expect(r.ignored_filters).toContain('conversation_id');
	});

	it('rest ask wider than 399 days clamps window', async () => {
		const fetcher = facetFetcher(defaultDataFetcher({ 'analytics/conversations': () => ({ rows: [] }) }));
		const from = new Date(NOW.getTime() - 500 * DAY).toISOString();
		const r = await aggregate(
			{ window: { from, to: NOW.toISOString() }, ask: { ask: 'conversations' } },
			{ fetcher, now: NOW }
		);
		expect(r.clamp?.reasons).toContain('rest-days');
		if (!('from' in r.window)) throw new Error('expected bounded window');
		expect(r.window.from).not.toBe(from);
		expect(Date.parse(r.window.to) - Date.parse(r.window.from)).toBe(399 * DAY);
	});

	it('bucket over 400 skips series read and clamps', async () => {
		const log: { path: string }[] = [];
		const inner = facetFetcher(defaultDataFetcher());
		const fetcher: Fetcher = (slot, path, params) => {
			log.push({ path });
			return inner(slot, path, params);
		};
		const from = new Date(NOW.getTime() - 500 * DAY).toISOString();
		const r = await aggregate(
			{
				window: { from, to: NOW.toISOString() },
				ask: { ask: 'trend', measure: 'hook_events', bucket: 'hour' }
			},
			{ fetcher, now: NOW }
		);
		expect(r.clamp?.reasons).toContain('bucket-cap');
		expect(log.some((l) => l.path === 'analytics/query')).toBe(false);
		if (r.ask === 'trend') expect(r.series).toBeUndefined();
	});

	it('omitted range resolves to thirty days ending at now', async () => {
		const log: { path: string; params: URLSearchParams }[] = [];
		const inner = facetFetcher(defaultDataFetcher({ 'analytics/conversations': () => ({ rows: [] }) }));
		const fetcher: Fetcher = (slot, path, params) => {
			if (path === 'analytics/conversations') log.push({ path, params: new URLSearchParams(params) });
			return inner(slot, path, params);
		};
		await aggregate({ ask: { ask: 'conversations' } }, { fetcher, now: NOW });
		const p = log[0]?.params;
		expect(p?.get('from')).toBe(new Date(NOW.getTime() - 30 * DAY).toISOString());
		expect(p?.get('to')).toBe(NOW.toISOString());
	});

	it('tenant is sent only when the request carries it', async () => {
		const log: { path: string; params: URLSearchParams }[] = [];
		const inner = facetFetcher(defaultDataFetcher({ 'analytics/conversations': () => ({ rows: [] }) }));
		const fetcher: Fetcher = (slot, path, params) => {
			log.push({ path, params: new URLSearchParams(params) });
			return inner(slot, path, params);
		};
		await aggregate({ ask: { ask: 'conversations' } }, { fetcher, now: NOW });
		for (const { params } of log) expect(params.has('tenant')).toBe(false);

		log.length = 0;
		await aggregate(
			{ tenant: 'acme', ask: { ask: 'conversations' } },
			{ fetcher, now: NOW }
		);
		for (const { params } of log) expect(params.get('tenant')).toBe('acme');
	});

	it('aggregate request strings do not name analytics paths or baselines', async () => {
		const req = JSON.stringify({
			ask: { ask: 'quality', kind: 'design', bucket: 'day' }
		});
		expect(req).not.toContain('/v1/analytics');
		expect(req).not.toContain('baselines');
	});
});
