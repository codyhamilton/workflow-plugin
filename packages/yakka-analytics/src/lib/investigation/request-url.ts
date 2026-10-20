import type {
	AggregateAsk,
	AggregateFilters,
	AggregateRequest,
	AggregateWindow
} from '../aggregate';
import type { Bucket } from '../buckets';
import { DIM_KEYS, parseUrlState, PRESET_IDS, type DimKey } from '../urlstate';

const ASK_KINDS = [
	'trend',
	'breakdown',
	'distribution',
	'quality',
	'conversations',
	'conversation',
	'executions'
] as const;

const BUCKETS: Bucket[] = ['hour', 'day', 'week', 'month'];
const QUALITY_KINDS = ['design', 'brief', 'report'] as const;
const QUALITY_BUCKETS = ['day', 'week', 'month'] as const;
const GRAINS = ['call', 'conversation'] as const;

export class InvestigationUrlError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'InvestigationUrlError';
	}
}

export function isInvestigationQuery(params: URLSearchParams): boolean {
	const ask = params.get('ask');
	return ask !== null && ask !== '';
}

function parseWindow(params: URLSearchParams): AggregateWindow | undefined {
	const tz = params.get('tz');
	const range = params.get('range');
	const from = params.get('from');
	const to = params.get('to');
	const window: AggregateWindow = {};
	let hasWindow = false;

	if (tz) {
		window.tz = tz;
		hasWindow = true;
	}
	if (range !== null && (PRESET_IDS as readonly string[]).includes(range)) {
		window.preset = range;
		hasWindow = true;
		return window;
	}
	if (from !== null || to !== null) {
		if (from) window.from = from;
		if (to) window.to = to;
		hasWindow = true;
		return window;
	}
	return hasWindow ? window : undefined;
}

function parseFilters(params: URLSearchParams, qualityKind?: string): AggregateFilters | undefined {
	const state = parseUrlState(params);
	if (qualityKind !== undefined) {
		delete state.include.kind;
		delete state.exclude.kind;
	}
	const include = state.include;
	const exclude = state.exclude;
	const hasInclude = Object.keys(include).length > 0;
	const hasExclude = Object.keys(exclude).length > 0;
	if (!hasInclude && !hasExclude) return undefined;
	return {
		...(hasInclude ? { include } : {}),
		...(hasExclude ? { exclude } : {})
	};
}

function requireParam(params: URLSearchParams, name: string, ask: string): string {
	const value = params.get(name);
	if (value === null || value === '') {
		throw new InvestigationUrlError(`missing ${name} for ask=${ask}`);
	}
	return value;
}

function parseAsk(params: URLSearchParams): AggregateAsk {
	const kind = params.get('ask');
	if (kind === null || kind === '') {
		throw new InvestigationUrlError('missing ask');
	}
	if (!(ASK_KINDS as readonly string[]).includes(kind)) {
		throw new InvestigationUrlError(`unknown ask: ${kind}`);
	}

	switch (kind) {
		case 'trend': {
			const measure = requireParam(params, 'measure', kind);
			const bucket = requireParam(params, 'bucket', kind);
			if (!BUCKETS.includes(bucket as Bucket)) {
				throw new InvestigationUrlError(`invalid bucket for ask=trend: ${bucket}`);
			}
			const dim = params.get('dim');
			const ask: AggregateAsk = { ask: 'trend', measure, bucket: bucket as Bucket };
			if (dim) {
				if (!(DIM_KEYS as readonly string[]).includes(dim)) {
					throw new InvestigationUrlError(`invalid dim for ask=trend: ${dim}`);
				}
				ask.dim = dim as DimKey;
			}
			return ask;
		}
		case 'breakdown': {
			const measure = requireParam(params, 'measure', kind);
			const dim = requireParam(params, 'dim', kind);
			if (!(DIM_KEYS as readonly string[]).includes(dim)) {
				throw new InvestigationUrlError(`invalid dim for ask=breakdown: ${dim}`);
			}
			return { ask: 'breakdown', measure, dim: dim as DimKey };
		}
		case 'distribution': {
			const measure = requireParam(params, 'measure', kind);
			const grain = requireParam(params, 'grain', kind);
			if (!(GRAINS as readonly string[]).includes(grain)) {
				throw new InvestigationUrlError(`invalid grain for ask=distribution: ${grain}`);
			}
			const dim = params.get('dim');
			const ask: AggregateAsk = {
				ask: 'distribution',
				measure,
				grain: grain as 'call' | 'conversation'
			};
			if (dim) {
				if (dim !== 'model') {
					throw new InvestigationUrlError(`invalid dim for ask=distribution: ${dim}`);
				}
				ask.dim = 'model';
			}
			return ask;
		}
		case 'quality': {
			const qKind = requireParam(params, 'kind', kind);
			const bucket = requireParam(params, 'bucket', kind);
			if (!(QUALITY_KINDS as readonly string[]).includes(qKind)) {
				throw new InvestigationUrlError(`invalid kind for ask=quality: ${qKind}`);
			}
			if (!(QUALITY_BUCKETS as readonly string[]).includes(bucket)) {
				throw new InvestigationUrlError(`invalid bucket for ask=quality: ${bucket}`);
			}
			return {
				ask: 'quality',
				kind: qKind as 'design' | 'brief' | 'report',
				bucket: bucket as 'day' | 'week' | 'month'
			};
		}
		case 'conversations':
			return { ask: 'conversations' };
		case 'conversation': {
			const id = requireParam(params, 'id', kind);
			return { ask: 'conversation', id };
		}
		case 'executions': {
			const bucket = params.get('bucket');
			if (bucket === null || bucket === '') return { ask: 'executions' };
			if (!(QUALITY_BUCKETS as readonly string[]).includes(bucket)) {
				throw new InvestigationUrlError(`invalid bucket for ask=executions: ${bucket}`);
			}
			return { ask: 'executions', bucket: bucket as 'day' | 'week' | 'month' };
		}
		default:
			throw new InvestigationUrlError(`unknown ask: ${kind}`);
	}
}

export function parseInvestigationRequest(
	params: URLSearchParams,
	_now?: Date
): AggregateRequest {
	const ask = parseAsk(params);
	const qualityKind = ask.ask === 'quality' ? ask.kind : undefined;
	return {
		window: parseWindow(params),
		filters: parseFilters(params, qualityKind),
		ask
	};
}

function writeWindow(out: URLSearchParams, window?: AggregateWindow): void {
	if (!window) return;
	if (window.preset) {
		out.set('range', window.preset);
	} else if (window.from !== undefined || window.to !== undefined) {
		if (window.from !== undefined) out.set('from', window.from);
		if (window.to !== undefined) out.set('to', window.to);
	}
	if (window.tz && window.tz !== 'UTC') out.set('tz', window.tz);
}

function writeFilters(out: URLSearchParams, filters?: AggregateFilters): void {
	if (!filters) return;
	for (const key of DIM_KEYS) {
		for (const v of filters.include?.[key] ?? []) out.append(key, v);
		for (const v of filters.exclude?.[key] ?? []) out.append(`x.${key}`, v);
	}
}

function writeAsk(out: URLSearchParams, ask: AggregateAsk): void {
	out.set('ask', ask.ask);
	switch (ask.ask) {
		case 'trend':
			out.set('measure', ask.measure);
			out.set('bucket', ask.bucket);
			if (ask.dim) out.set('dim', ask.dim);
			break;
		case 'breakdown':
			out.set('measure', ask.measure);
			out.set('dim', ask.dim);
			break;
		case 'distribution':
			out.set('measure', ask.measure);
			out.set('grain', ask.grain);
			if (ask.dim) out.set('dim', ask.dim);
			break;
		case 'quality':
			out.set('kind', ask.kind);
			out.set('bucket', ask.bucket);
			break;
		case 'conversation':
			out.set('id', ask.id);
			break;
		case 'executions':
			if (ask.bucket) out.set('bucket', ask.bucket);
			break;
		case 'conversations':
			break;
	}
}

export function investigationRequestToSearch(
	request: AggregateRequest,
	_now?: Date
): URLSearchParams {
	const out = new URLSearchParams();
	writeWindow(out, request.window);
	writeFilters(out, request.filters);
	writeAsk(out, request.ask);
	return out;
}
