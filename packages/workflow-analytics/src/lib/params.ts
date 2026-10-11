// Turning view state into API params. Non-/query routes reject windows wider than 399 days, so they
// are clamped; `/query` accepts all=1. Excludes become the facet complement because the API has no
// exclude parameter. Pure.
import { presetWindow } from './presets';
import { DIM_KEYS, type DimKey, type UrlState } from './urlstate';

export type Route = 'query' | 'rest';

export interface Window {
	from?: Date;
	to?: Date;
	all: boolean;
	clamped: boolean;
}

export type ApiParams = { params: URLSearchParams } | { pending: true } | { empty: true };

const DAY = 86400000;
const MAX_REST_DAYS = 399;

/** The window to request for a route: `all` on rest routes is clamped to the last 399 days. */
export function resolveWindow(state: UrlState, now: Date, tz: string, route: Route): Window {
	if (state.range === 'all') {
		if (route === 'query') return { all: true, clamped: false };
		return { from: new Date(now.getTime() - MAX_REST_DAYS * DAY), to: now, all: false, clamped: true };
	}
	let from: Date | undefined;
	let to: Date | undefined;
	if (state.range === 'custom') {
		from = state.from ? new Date(state.from) : undefined;
		to = state.to ? new Date(state.to) : undefined;
	} else {
		const w = presetWindow(state.range, now, tz);
		if (w !== null) {
			from = w.from;
			to = w.to;
		}
	}
	let clamped = false;
	if (route === 'rest' && from !== undefined && to !== undefined && to.getTime() - from.getTime() > MAX_REST_DAYS * DAY) {
		from = new Date(to.getTime() - MAX_REST_DAYS * DAY);
		clamped = true;
	}
	return { from, to, all: false, clamped };
}

/** The API query for a view state and window, or why no request can be issued yet. */
export function apiParams(
	state: UrlState,
	win: Window,
	facets: Partial<Record<DimKey, string[]>> | null,
	tz: string
): ApiParams {
	const params = new URLSearchParams();
	params.set('tz', tz);
	if (win.all) {
		params.set('all', '1');
	} else {
		if (win.from !== undefined) params.set('from', win.from.toISOString());
		if (win.to !== undefined) params.set('to', win.to.toISOString());
	}
	for (const key of DIM_KEYS) {
		const exclude = state.exclude[key];
		const include = state.include[key];
		if (key === 'conversation_id') continue;
		if (exclude !== undefined && exclude.length > 0 && !(include !== undefined && include.length > 0) && facets == null)
			return { pending: true };
	}
	for (const key of DIM_KEYS) {
		const include = state.include[key] ?? [];
		const exclude = state.exclude[key] ?? [];
		if (key === 'conversation_id') {
			for (const v of include) params.append(key, v);
			continue;
		}
		if (exclude.length === 0) {
			for (const v of include) params.append(key, v);
			continue;
		}
		const list =
			include.length > 0
				? include.filter((v) => !exclude.includes(v))
				: (facets?.[key] ?? []).filter((v) => !exclude.includes(v));
		if (list.length === 0) return { empty: true };
		for (const v of list) params.append(key, v);
	}
	return { params };
}

/** The same query narrowed to one kind, for the scores route. */
export function scoresParams(params: URLSearchParams, kind: string): URLSearchParams {
	const out = new URLSearchParams(params);
	out.delete('kind');
	out.set('kind', kind);
	return out;
}
