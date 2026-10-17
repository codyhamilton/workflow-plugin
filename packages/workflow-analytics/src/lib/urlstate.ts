// The dashboard view state lives in the page URL. These are the filter keys the API takes; the
// site resolves shift-click exclusion to the facet complement because the API has no exclude param.
// Pure functions; no browser globals.
import { KINDS } from './filters';

export const DIM_KEYS = [
	'repo_id',
	'harness',
	'kind',
	'plan',
	'norm_event',
	'event',
	'tool',
	'model',
	'source',
	'conversation_id'
] as const;
export type DimKey = (typeof DIM_KEYS)[number];

export type PresetId = 'today' | '24h' | '7d' | '30d' | '90d' | 'month' | 'ytd' | 'all';
export const PRESET_IDS: PresetId[] = ['today', '24h', '7d', '30d', '90d', 'month', 'ytd', 'all'];

export interface UrlState {
	range: PresetId | 'custom';
	from?: string;
	to?: string;
	include: Partial<Record<DimKey, string[]>>;
	exclude: Partial<Record<DimKey, string[]>>;
}

export interface Chip {
	key: DimKey;
	value: string;
	mode: 'include' | 'exclude';
}

const FILTER_PARAMS = new Set<string>(['range', 'from', 'to']);
for (const key of DIM_KEYS) {
	FILTER_PARAMS.add(key);
	FILTER_PARAMS.add(`x.${key}`);
}

function dedupe(values: string[]): string[] {
	return [...new Set(values)];
}

function readDim(q: URLSearchParams, key: DimKey, exclude: boolean): string[] {
	const name = exclude ? `x.${key}` : key;
	const values = q.getAll(name);
	return key === 'kind' ? values.filter((v) => (KINDS as readonly string[]).includes(v)) : values;
}

/** The view state a page query encodes; a missing range is 30d, from/to alone is custom. */
export function parseUrlState(q: URLSearchParams): UrlState {
	const state: UrlState = { range: '30d', include: {}, exclude: {} };
	const range = q.get('range');
	if (range !== null && (PRESET_IDS as readonly string[]).includes(range)) {
		state.range = range as PresetId;
	} else if (q.has('from') || q.has('to')) {
		state.range = 'custom';
		state.from = q.get('from') || undefined;
		state.to = q.get('to') || undefined;
	}
	for (const key of DIM_KEYS) {
		const include = readDim(q, key, false);
		if (include.length > 0) state.include[key] = include;
		const exclude = readDim(q, key, true);
		if (exclude.length > 0) state.exclude[key] = exclude;
	}
	return state;
}

/** The page query for a view state; route params in keep (metric, group, cursors) are carried over. */
export function toSearch(state: UrlState, keep?: URLSearchParams): URLSearchParams {
	const out = new URLSearchParams();
	if (keep) for (const [k, v] of keep) if (!FILTER_PARAMS.has(k)) out.append(k, v);
	if (state.range === 'custom') {
		if (state.from) out.set('from', state.from);
		if (state.to) out.set('to', state.to);
	} else {
		out.set('range', state.range);
	}
	for (const key of DIM_KEYS) for (const v of state.include[key] ?? []) out.append(key, v);
	for (const key of DIM_KEYS) for (const v of state.exclude[key] ?? []) out.append(`x.${key}`, v);
	return out;
}

/** Add or remove a drill value on one side, moving it off the other. The folded bucket and the empty key are not filters. */
export function applyDrill(state: UrlState, key: DimKey, value: string, exclude: boolean): UrlState {
	if (value === '__other__' || value === '') return state;
	const include = { ...state.include };
	const excludeMap = { ...state.exclude };
	const target = exclude ? excludeMap : include;
	const other = exclude ? include : excludeMap;
	target[key] = dedupe([...(target[key] ?? []), value]);
	const remaining = (other[key] ?? []).filter((v) => v !== value);
	if (remaining.length > 0) other[key] = remaining;
	else delete other[key];
	return { ...state, include, exclude: excludeMap };
}

/** Drop a chip value from both sides. */
export function removeChip(state: UrlState, key: DimKey, value: string): UrlState {
	const include = { ...state.include };
	const exclude = { ...state.exclude };
	for (const map of [include, exclude]) {
		const remaining = (map[key] ?? []).filter((v) => v !== value);
		if (remaining.length > 0) map[key] = remaining;
		else delete map[key];
	}
	return { ...state, include, exclude };
}

/** The active filters as chips, includes before excludes, in dimension order. */
export function chips(state: UrlState): Chip[] {
	const out: Chip[] = [];
	for (const key of DIM_KEYS) {
		for (const value of state.include[key] ?? []) out.push({ key, value, mode: 'include' });
		for (const value of state.exclude[key] ?? []) out.push({ key, value, mode: 'exclude' });
	}
	return out;
}
