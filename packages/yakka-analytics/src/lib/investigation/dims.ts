import type { Facets } from '../types';
import { DIM_KEYS, type DimKey } from '../urlstate';

const FACET_DIMS: { key: DimKey; values: (f: Facets) => string[] }[] = [
	{ key: 'repo_id', values: (f) => f.repos },
	{ key: 'harness', values: (f) => f.harnesses },
	{ key: 'kind', values: (f) => f.kinds },
	{ key: 'plan', values: (f) => f.plans },
	{ key: 'norm_event', values: (f) => f.norm_events },
	{ key: 'event', values: (f) => f.events },
	{ key: 'tool', values: (f) => f.tools.map((t) => t.name) },
	{ key: 'model', values: (f) => f.models }
];

/** Breakdown dimensions that have facet values in the current window. */
export function breakdownDims(controls: Facets): DimKey[] {
	const out: DimKey[] = [];
	for (const { key, values } of FACET_DIMS) {
		if (values(controls).some((v) => v !== '')) out.push(key);
	}
	return out;
}

export function isDimKey(s: string): s is DimKey {
	return (DIM_KEYS as readonly string[]).includes(s);
}

const EXTRA_DIMS: DimKey[] = ['conversation_id'];

/** Dims offered in the investigation selector (facets plus conversation grain). */
export function explorationDims(controls: Facets): DimKey[] {
	const fromFacets = breakdownDims(controls);
	return [...new Set([...fromFacets, ...EXTRA_DIMS])];
}
