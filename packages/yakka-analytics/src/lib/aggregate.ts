// One request, one result: landing and analysis read through here instead of naming analytics paths.
import { bucketCount, type Bucket } from './buckets';
import { getJSON, type Slot } from './query';
import {
	apiParams,
	conversationParams,
	resolveWindow,
	scoreSeriesParams,
	scoresParams,
	type Route,
	type Window
} from './params';
import { PRESETS } from './presets';
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
import { type DimKey, type PresetId, type UrlState } from './urlstate';

const DAY = 86400000;
const SLOT: Slot = 'aggregate';

export type Dim = DimKey;

export type ClampReason = 'rest-days' | 'bucket-cap';

export interface AggregateClamp {
	reasons: ClampReason[];
}

export type ResolvedWindow = { from: string; to: string } | { all: true };

export interface AggregateWindow {
	from?: string;
	to?: string;
	tz?: string;
	preset?: string;
}

export interface AggregateFilters {
	include?: Partial<Record<Dim, string[]>>;
	exclude?: Partial<Record<Dim, string[]>>;
}

export interface TrendAsk {
	ask: 'trend';
	measure: string;
	bucket: Bucket;
	dim?: Dim;
}

export interface BreakdownAsk {
	ask: 'breakdown';
	measure: string;
	dim: Dim;
}

export interface DistributionAsk {
	ask: 'distribution';
	measure: string;
	grain: 'call' | 'conversation';
	dim?: 'model';
}

export interface QualityAsk {
	ask: 'quality';
	kind: 'design' | 'brief' | 'report';
	bucket: 'day' | 'week' | 'month';
}

export interface ConversationsAsk {
	ask: 'conversations';
}

export interface ConversationAsk {
	ask: 'conversation';
	id: string;
}

export interface ExecutionsAsk {
	ask: 'executions';
	bucket?: 'day' | 'week' | 'month';
}

export type AggregateAsk =
	| TrendAsk
	| BreakdownAsk
	| DistributionAsk
	| QualityAsk
	| ConversationsAsk
	| ConversationAsk
	| ExecutionsAsk;

export interface AggregateRequest {
	tenant?: string;
	window?: AggregateWindow;
	filters?: AggregateFilters;
	ask: AggregateAsk;
}

export interface Series {
	key: string;
	points: { t: string; v: number }[];
}

interface MetaFields {
	partial?: boolean;
	ignored_filters?: string[];
	truncated?: boolean;
}

export interface AggregateBase {
	window: ResolvedWindow;
	controls: Facets;
	clamp?: AggregateClamp;
	partial?: boolean;
	ignored_filters?: string[];
	truncated?: boolean;
}

export interface TrendResult extends AggregateBase {
	ask: 'trend';
	series?: Series[];
}

export interface BreakdownResult extends AggregateBase {
	ask: 'breakdown';
	series: Series[];
}

export interface DistributionResult extends AggregateBase {
	ask: 'distribution';
	measure: string;
	grain: string;
	dim?: string;
	rows: DistributionResponse['rows'];
}

export interface QualityResult extends AggregateBase {
	ask: 'quality';
	scores: Scores;
	baseline: Baselines;
	scoreSeries?: ScoreSeries;
}

export interface ConversationsResult extends AggregateBase {
	ask: 'conversations';
	rows: Conversations['rows'];
	next?: string;
}

export interface ConversationResult extends AggregateBase {
	ask: 'conversation';
	detail: ConversationDetail;
}

export interface ExecutionsResult extends AggregateBase {
	ask: 'executions';
	counts: Executions['counts'];
	rows: Executions['rows'];
	next?: string;
	series?: Executions['series'];
}

export type AggregateResult =
	| TrendResult
	| BreakdownResult
	| DistributionResult
	| QualityResult
	| ConversationsResult
	| ConversationResult
	| ExecutionsResult;

export type Fetcher = (slot: Slot, path: string, params: URLSearchParams) => Promise<unknown>;

export interface AggregateOptions {
	fetcher?: Fetcher;
	now?: Date;
}

const PRESET_IDS: PresetId[] = ['today', '24h', '7d', '30d', '90d', 'month', 'ytd', 'all'];

function resolvePresetId(preset: string): PresetId | null {
	const id = preset.toLowerCase() as PresetId;
	if (PRESET_IDS.includes(id)) return id;
	const found = PRESETS.find((p) => p.id === preset || p.label === preset);
	return found?.id ?? null;
}

function toUrlState(request: AggregateRequest, now: Date): UrlState {
	const include = request.filters?.include ?? {};
	const exclude = request.filters?.exclude ?? {};
	const w = request.window;
	if (w?.preset) {
		const id = resolvePresetId(w.preset);
		if (id) return { range: id, include, exclude };
	}
	if (w?.from !== undefined || w?.to !== undefined) {
		return { range: 'custom', from: w.from, to: w.to, include, exclude };
	}
	const to = now;
	const from = new Date(now.getTime() - 30 * DAY);
	return { range: 'custom', from: from.toISOString(), to: to.toISOString(), include, exclude };
}

function tzOf(request: AggregateRequest): string {
	return request.window?.tz ?? 'UTC';
}

function routeFor(ask: AggregateAsk): Route {
	return ask.ask === 'trend' || ask.ask === 'breakdown' ? 'query' : 'rest';
}

function mapFacets(f: Facets): Partial<Record<DimKey, string[]>> {
	return {
		repo_id: f.repos,
		harness: f.harnesses,
		kind: f.kinds,
		plan: f.plans,
		event: f.events,
		model: f.models,
		norm_event: f.norm_events,
		tool: f.tools.map((t) => t.name)
	};
}

function facetParams(win: Window, tz: string): URLSearchParams {
	const params = new URLSearchParams({ tz });
	if (win.all) params.set('all', '1');
	else {
		if (win.from !== undefined) params.set('from', win.from.toISOString());
		if (win.to !== undefined) params.set('to', win.to.toISOString());
	}
	return params;
}

function resolvedWindowField(win: Window): ResolvedWindow {
	if (win.all) return { all: true };
	return {
		from: win.from?.toISOString() ?? '',
		to: win.to?.toISOString() ?? ''
	};
}

function withTenant(params: URLSearchParams, tenant?: string): URLSearchParams {
	if (tenant) params.set('tenant', tenant);
	return params;
}

function metaFieldsFrom(source: object): MetaFields {
	const s = source as Partial<MetaFields>;
	const out: MetaFields = {};
	if (s.partial) out.partial = true;
	if (s.truncated) out.truncated = true;
	if (s.ignored_filters) out.ignored_filters = s.ignored_filters;
	return out;
}

function unionMeta(parts: MetaFields[], extraIgnored: string[] = []): MetaFields {
	const ignored = new Set(extraIgnored);
	let partial: boolean | undefined;
	let truncated: boolean | undefined;
	for (const p of parts) {
		if (p.partial) partial = true;
		if (p.truncated) truncated = true;
		if (p.ignored_filters) for (const k of p.ignored_filters) ignored.add(k);
	}
	const out: MetaFields = {};
	if (partial) out.partial = true;
	if (truncated) out.truncated = true;
	if (ignored.size > 0) out.ignored_filters = [...ignored].sort();
	return out;
}

function excludeIgnoredKeys(exclude: Partial<Record<Dim, string[]>> | undefined): string[] {
	if (!exclude?.conversation_id?.length) return [];
	return ['conversation_id'];
}

function filterKeysSet(filters?: AggregateFilters): string[] {
	const keys = new Set<string>();
	if (filters?.include) for (const k of Object.keys(filters.include)) keys.add(k);
	if (filters?.exclude) for (const k of Object.keys(filters.exclude)) keys.add(k);
	return [...keys].sort();
}

function queryToSeries(resp: QueryResponse): Series[] {
	const timed = resp.bucket !== 'none';
	const by = new Map<string, { t: string; v: number }[]>();
	for (const r of resp.rows) {
		const key = r.k.length === 0 ? 'all' : r.k.join(' / ');
		let pts = by.get(key);
		if (!pts) {
			pts = [];
			by.set(key, pts);
		}
		if (timed && r.t) pts.push({ t: r.t, v: r.v });
		else if (!timed) pts.push({ t: '', v: r.v });
	}
	return [...by.entries()].map(([key, points]) => ({ key, points }));
}

function bucketOverCap(
	ask: AggregateAsk,
	win: Window,
	tz: string
): { over: boolean; bucket?: Bucket | 'day' | 'week' | 'month' } {
	let bucket: Bucket | 'day' | 'week' | 'month' | undefined;
	if (ask.ask === 'trend') bucket = ask.bucket;
	else if (ask.ask === 'quality') bucket = ask.bucket;
	else if (ask.ask === 'executions') bucket = ask.bucket;
	if (!bucket || win.all || win.from === undefined || win.to === undefined) return { over: false, bucket };
	return { over: bucketCount(bucket as Bucket, win.from, win.to, tz) > 400, bucket };
}

function buildClamp(win: Window, bucketCap: boolean): AggregateClamp | undefined {
	const reasons: ClampReason[] = [];
	if (win.clamped) reasons.push('rest-days');
	if (bucketCap) reasons.push('bucket-cap');
	if (reasons.length === 0) return undefined;
	return { reasons };
}

async function loadFacets(
	fetcher: Fetcher,
	facetWin: Window,
	tz: string,
	tenant?: string
): Promise<Facets> {
	const params = withTenant(facetParams(facetWin, tz), tenant);
	return fetcher(SLOT, 'analytics/facets', params) as Promise<Facets>;
}

function dataParams(
	state: UrlState,
	win: Window,
	facets: Partial<Record<DimKey, string[]>>,
	tz: string,
	tenant?: string
): URLSearchParams | 'empty' {
	const result = apiParams(state, win, facets, tz);
	if ('empty' in result) return 'empty';
	if (!('params' in result)) return 'empty';
	return withTenant(result.params, tenant);
}

export async function aggregate(
	request: AggregateRequest,
	options: AggregateOptions = {}
): Promise<AggregateResult> {
	const fetcher = options.fetcher ?? ((slot, path, params) => getJSON(slot, path, params));
	const now = options.now ?? new Date();
	const tz = tzOf(request);
	const state = toUrlState(request, now);
	const route = routeFor(request.ask);
	const win = resolveWindow(state, now, tz, route);
	const facetWin = resolveWindow(state, now, tz, 'rest');
	const extraIgnored = excludeIgnoredKeys(request.filters?.exclude);

	const facetsResp = await loadFacets(fetcher, facetWin, tz, request.tenant);
	const facetMap = mapFacets(facetsResp);
	const controls = facetsResp;

	const { over: bucketCap } = bucketOverCap(request.ask, win, tz);
	const clamp = buildClamp(win, bucketCap);
	const windowField = resolvedWindowField(win);
	const baseMeta = () => unionMeta([], extraIgnored);

	const ask = request.ask;

	if (ask.ask === 'conversation') {
		const ignored = [...filterKeysSet(request.filters), ...extraIgnored];
		const convState = { ...state, include: {}, exclude: {} };
		const params = conversationParams(ask.id, convState, tz, now);
		if (request.tenant) params.set('tenant', request.tenant);
		const detail = (await fetcher(SLOT, 'analytics/conversation', params)) as ConversationDetail;
		const meta = unionMeta([detail], ignored);
		return {
			ask: 'conversation',
			window: windowField,
			controls,
			detail,
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	const params = dataParams(state, win, facetMap, tz, request.tenant);
	if (params === 'empty') {
		const meta = baseMeta();
		return emptyResult(ask, windowField, controls, meta, clamp);
	}

	if (ask.ask === 'trend') {
		if (bucketCap) {
			const meta = baseMeta();
			return { ask: 'trend', window: windowField, controls, ...meta, ...(clamp ? { clamp } : {}) };
		}
		const p = new URLSearchParams(params);
		p.set('measure', ask.measure);
		p.set('bucket', ask.bucket);
		if (ask.dim) p.set('dim', ask.dim);
		const resp = (await fetcher(SLOT, 'analytics/query', p)) as QueryResponse;
		const meta = unionMeta([resp], extraIgnored);
		return {
			ask: 'trend',
			window: windowField,
			controls,
			series: queryToSeries(resp),
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	if (ask.ask === 'breakdown') {
		const p = new URLSearchParams(params);
		p.set('measure', ask.measure);
		p.set('dim', ask.dim);
		p.set('bucket', 'none');
		const resp = (await fetcher(SLOT, 'analytics/query', p)) as QueryResponse;
		const meta = unionMeta([resp], extraIgnored);
		return {
			ask: 'breakdown',
			window: windowField,
			controls,
			series: queryToSeries(resp),
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	if (ask.ask === 'distribution') {
		const p = new URLSearchParams(params);
		p.set('measure', ask.measure);
		p.set('grain', ask.grain);
		if (ask.dim) p.set('dim', ask.dim);
		const resp = (await fetcher(SLOT, 'analytics/distribution', p)) as DistributionResponse;
		const meta = unionMeta([resp], extraIgnored);
		return {
			ask: 'distribution',
			window: windowField,
			controls,
			measure: resp.measure,
			grain: resp.grain,
			dim: resp.dim,
			rows: resp.rows,
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	if (ask.ask === 'quality') {
		const base = new URLSearchParams(params);
		const scoresP = scoresParams(base, ask.kind);
		const baselineP = withTenant(new URLSearchParams({ kind: ask.kind }), request.tenant);
		const reads: [Promise<Scores>, Promise<Baselines>, Promise<ScoreSeries> | null] = [
			fetcher(SLOT, 'analytics/scores', scoresP) as Promise<Scores>,
			fetcher(SLOT, 'baselines', baselineP) as Promise<Baselines>,
			bucketCap
				? null
				: (fetcher(
						SLOT,
						'analytics/score-series',
						scoreSeriesParams(base, ask.kind, ask.bucket)
					) as Promise<ScoreSeries>)
		];
		const [scores, baseline, scoreSeries] = await Promise.all([
			reads[0],
			reads[1],
			reads[2] ?? Promise.resolve(undefined)
		]);
		const meta = unionMeta(
			[scores, scoreSeries].filter(Boolean) as MetaFields[],
			extraIgnored
		);
		return {
			ask: 'quality',
			window: windowField,
			controls,
			scores,
			baseline,
			...(scoreSeries ? { scoreSeries } : {}),
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	if (ask.ask === 'conversations') {
		const resp = (await fetcher(SLOT, 'analytics/conversations', params)) as Conversations;
		const meta = unionMeta([metaFieldsFrom(resp)], extraIgnored);
		return {
			ask: 'conversations',
			window: windowField,
			controls,
			rows: resp.rows,
			...(resp.next !== undefined ? { next: resp.next } : {}),
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	if (ask.ask === 'executions') {
		const p = new URLSearchParams(params);
		if (ask.bucket && !bucketCap) p.set('bucket', ask.bucket);
		const resp = (await fetcher(SLOT, 'analytics/executions', p)) as Executions;
		const meta = unionMeta([metaFieldsFrom(resp)], extraIgnored);
		return {
			ask: 'executions',
			window: windowField,
			controls,
			counts: resp.counts,
			rows: resp.rows,
			...(resp.next !== undefined ? { next: resp.next } : {}),
			...(ask.bucket && !bucketCap && resp.series ? { series: resp.series } : {}),
			...meta,
			...(clamp ? { clamp } : {})
		};
	}

	throw new Error('unreachable ask');
}

function emptyResult(
	ask: AggregateAsk,
	window: ResolvedWindow,
	controls: Facets,
	meta: MetaFields,
	clamp?: AggregateClamp
): AggregateResult {
	const base = { window, controls, ...meta, ...(clamp ? { clamp } : {}) };
	switch (ask.ask) {
		case 'trend':
			return { ask: 'trend', series: [], ...base };
		case 'breakdown':
			return { ask: 'breakdown', series: [], ...base };
		case 'distribution':
			return { ask: 'distribution', measure: ask.measure, grain: ask.grain, rows: [], ...base };
		case 'quality':
			return {
				ask: 'quality',
				scores: { kind: ask.kind, checks: [] },
				baseline: { kind: ask.kind, checks: {} },
				...base
			};
		case 'conversations':
			return { ask: 'conversations', rows: [], ...base };
		case 'executions':
			return {
				ask: 'executions',
				counts: { complete: 0, unreported: 0, started: 0 },
				rows: [],
				...base
			};
		default:
			throw new Error('empty slice not defined for ask');
	}
}
