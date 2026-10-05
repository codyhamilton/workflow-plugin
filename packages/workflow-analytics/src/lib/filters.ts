// The shared filter lives in the page URL. These are the same keys the API takes, so the page query
// and the API query are interchangeable. Pure functions; no browser globals.
export const KINDS = ['design', 'brief', 'report'] as const;
export type Kind = (typeof KINDS)[number];

export interface Filter {
	from?: string;
	to?: string;
	repo_id: string[];
	harness: string[];
	kind: Kind[];
	plan: string[];
}

export const FILTER_KEYS = ['from', 'to', 'repo_id', 'harness', 'kind', 'plan'] as const;

export function parseFilter(q: URLSearchParams): Filter {
	return {
		from: q.get('from') || undefined,
		to: q.get('to') || undefined,
		repo_id: q.getAll('repo_id'),
		harness: q.getAll('harness'),
		kind: q.getAll('kind').filter((k): k is Kind => (KINDS as readonly string[]).includes(k)),
		plan: q.getAll('plan')
	};
}

/** The API query for a filter: only the shared keys, repeatable ones repeated. */
export function filterParams(f: Filter): URLSearchParams {
	const p = new URLSearchParams();
	if (f.from) p.set('from', f.from);
	if (f.to) p.set('to', f.to);
	for (const k of ['repo_id', 'harness', 'kind', 'plan'] as const) for (const v of f[k]) p.append(k, v);
	return p;
}

/** The page query after a filter change: route-specific params (metric, group, ...) are kept. */
export function mergeQuery(current: URLSearchParams, f: Filter): URLSearchParams {
	const out = new URLSearchParams();
	for (const [k, v] of current) if (!(FILTER_KEYS as readonly string[]).includes(k)) out.append(k, v);
	for (const [k, v] of filterParams(f)) out.append(k, v);
	return out;
}

/** A date input value (YYYY-MM-DD) to an RFC3339 window edge, and back. */
export function dateToFrom(d: string): string | undefined {
	return d ? `${d}T00:00:00Z` : undefined;
}
export function dateToTo(d: string): string | undefined {
	return d ? `${d}T23:59:59Z` : undefined;
}
export function toDate(ts?: string): string {
	return ts ? ts.slice(0, 10) : '';
}
