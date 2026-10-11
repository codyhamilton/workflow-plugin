// The one reactive view the routes and the chrome share. The URL is the view: this module parses the
// page query into `UrlState`, loads the filter facets for the current window, and exposes the
// mutators that keep route params while moving the window or the filters. Routes never parse the URL
// or fan out requests themselves.
import { goto } from '$app/navigation';
import { page } from '$app/state';
import { apiParams, resolveWindow, type Route } from './params';
import { getJSON, Superseded } from './query';
import {
	applyDrill,
	parseUrlState,
	removeChip as dropChip,
	toSearch,
	type DimKey,
	type PresetId,
	type UrlState
} from './urlstate';
import type { Facets } from './types';

const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;

let facets = $state<Partial<Record<DimKey, string[]>> | null>(null);
// The facetParams key `facets` was loaded for. Facets are window-filtered, so an exclude can only be
// resolved to its complement once facets for the *current* window have arrived; `facetsReady` gates
// the route effects on that, so a stale window's facets are never used and a late facet response for
// the window in flight cannot re-trigger an effect (and supersede) requests already issued.
let facetsKey = $state<string | null>(null);

function currentState(): UrlState {
	return parseUrlState(page.url.searchParams);
}

/** Map the facets response (`analyticsFacets` in serve/analytics.go) onto the drilled dimensions. */
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

/** Facets are window-filtered (the API takes only from/to) and take `rest`'s 399-day clamp. */
function facetParams(): URLSearchParams {
	const win = resolveWindow(currentState(), new Date(), tz, 'rest');
	const params = new URLSearchParams({ tz });
	if (win.all) params.set('all', '1');
	else {
		if (win.from) params.set('from', win.from.toISOString());
		if (win.to) params.set('to', win.to.toISOString());
	}
	return params;
}

/** The key facets for the current window; stable within the hour (`presetWindow` rounds to the hour). */
function facetKey(): string {
	return facetParams().toString();
}

const facetsReady = $derived(facets !== null && facetsKey === facetKey());

// One client owns debounce/cache, so re-requesting on every window change collapses bursts.
$effect.root(() => {
	$effect(() => {
		let live = true;
		const params = facetParams();
		const key = params.toString();
		getJSON<Facets>('facets', 'analytics/facets', params).then(
			(resp) => {
				if (live) {
					facets = mapFacets(resp);
					facetsKey = key;
				}
			},
			(e) => {
				// A superseded call is not an error; a real failure keeps the last facets.
				if (live && !(e instanceof Superseded)) {
					facets = null;
					facetsKey = null;
				}
			}
		);
		return () => {
			live = false;
		};
	});
});

function navigate(next: UrlState) {
	const qs = toSearch(next, page.url.searchParams).toString();
	const suffix = qs ? `?${qs}` : '';
	if (suffix === page.url.search) return;
	goto(`${page.url.pathname}${suffix}`, { noScroll: true, keepFocus: true });
}

/** The API query for a route, or null when facets are still pending or nothing matches an exclude. */
function paramsFor(route: Route, extra?: Record<string, string | string[]>): URLSearchParams | null {
	const state = currentState();
	const win = resolveWindow(state, new Date(), tz, route);
	const result = apiParams(state, win, facets, tz);
	if (!('params' in result)) return null;
	const params = result.params;
	if (extra) {
		for (const [k, v] of Object.entries(extra)) {
			params.delete(k);
			for (const x of Array.isArray(v) ? v : [v]) params.append(k, x);
		}
	}
	return params;
}

function setPreset(id: PresetId) {
	const s = currentState();
	navigate({ range: id, include: s.include, exclude: s.exclude });
}

function setWindow(from: Date, to: Date) {
	navigate({ ...currentState(), range: 'custom', from: from.toISOString(), to: to.toISOString() });
}

function drill(key: DimKey, value: string, ev?: { shift?: boolean }) {
	navigate(applyDrill(currentState(), key, value, !!ev?.shift));
}

function setInclude(key: DimKey, values: string[]) {
	const s = currentState();
	const include = { ...s.include };
	if (values.length > 0) include[key] = values;
	else delete include[key];
	navigate({ ...s, include });
}

function removeChip(key: DimKey, value: string) {
	navigate(dropChip(currentState(), key, value));
}

function setParam(name: string, value: string | null) {
	const q = new URLSearchParams(page.url.searchParams);
	if (value === null) q.delete(name);
	else q.set(name, value);
	const qs = q.toString();
	const suffix = qs ? `?${qs}` : '';
	if (suffix === page.url.search) return;
	goto(`${page.url.pathname}${suffix}`, { noScroll: true, keepFocus: true });
}

export const view = {
	get state(): UrlState {
		return currentState();
	},
	tz,
	get facets(): Partial<Record<DimKey, string[]>> | null {
		return facets;
	},
	/** True once facets for the current window have loaded; false while they are stale or pending. */
	get facetsReady(): boolean {
		return facetsReady;
	},
	get empty(): boolean {
		return 'empty' in apiParams(currentState(), resolveWindow(currentState(), new Date(), tz, 'rest'), facets, tz);
	},
	get clamped(): boolean {
		return resolveWindow(currentState(), new Date(), tz, 'rest').clamped;
	},
	paramsFor,
	setPreset,
	setWindow,
	drill,
	setInclude,
	removeChip,
	setParam
};
