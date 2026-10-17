// Pure helpers for dashboard tiles: map saved chart params to API extras and URL chart keys.
import { parseConfig, type BuilderConfig } from './builder';
import type { ReportId } from './views';
import type { Schema } from './types';

const HOOKS_SPLIT = new Set(['norm_event', 'tool']);

/** API query keys chart tiles may set; cleared before merging tile params in `paramsForTile`. */
export const TILE_API_CHART_KEYS = [
	'measure',
	'dim',
	'bucket',
	'top',
	'grain',
	'kind',
	'shape',
	'limit',
	'metric',
	'group',
	'split'
] as const;

/** Builder saved params → URL short keys (for `parseConfig` round-trip). */
export function builderTileSearchParams(params: Record<string, string | string[]>): URLSearchParams {
	const q = new URLSearchParams();
	const measure = params.measure;
	if (typeof measure === 'string') q.set('m', measure);
	const dim = params.dim;
	if (Array.isArray(dim)) {
		for (const d of dim) q.append('d', d);
	} else if (typeof dim === 'string') q.append('d', dim);
	const bucket = params.bucket;
	if (typeof bucket === 'string') q.set('b', bucket);
	const chart = params.chart;
	if (typeof chart === 'string') q.set('c', chart);
	const top = params.top;
	if (typeof top === 'string') q.set('top', top);
	return q;
}

/** Saved builder chart params → sanitised `BuilderConfig` once schema is loaded. */
export function builderConfigFromTileParams(
	params: Record<string, string | string[]>,
	schema: Schema
): BuilderConfig {
	const hasMeasure = typeof params.measure === 'string' && params.measure !== '';
	const q = builderTileSearchParams(params);
	if (!hasMeasure) return parseConfig(new URLSearchParams(), schema);
	return parseConfig(q, schema);
}

/** Hooks saved `dim` is the time-series split (`norm_event` | `tool`). */
export function hooksSplitFromTileParams(params: Record<string, string | string[]>): 'norm_event' | 'tool' {
	const raw = params.dim;
	const want = Array.isArray(raw) ? raw[0] : raw;
	return typeof want === 'string' && HOOKS_SPLIT.has(want) ? (want as 'norm_event' | 'tool') : 'norm_event';
}

function appendParam(
	out: Record<string, string | string[]>,
	key: string,
	value: string | string[] | undefined
): void {
	if (value === undefined) return;
	out[key] = value;
}

/**
 * Map stored contract chart params to the `extra` record for `view.paramsFor` / route fetches.
 */
export function tileExtraParams(
	report: ReportId,
	params: Record<string, string | string[]>
): Record<string, string | string[]> {
	switch (report) {
		case 'builder': {
			const out: Record<string, string | string[]> = {};
			appendParam(out, 'measure', params.measure);
			appendParam(out, 'dim', params.dim);
			appendParam(out, 'bucket', params.bucket);
			appendParam(out, 'top', params.top);
			return out;
		}
		case 'usage': {
			const out: Record<string, string | string[]> = {};
			appendParam(out, 'measure', params.measure);
			appendParam(out, 'grain', params.grain);
			return out;
		}
		case 'hooks': {
			const out: Record<string, string | string[]> = { measure: 'hook_events' };
			appendParam(out, 'bucket', params.bucket);
			const split = hooksSplitFromTileParams(params);
			out.dim = split;
			return out;
		}
		case 'trends': {
			const metric =
				typeof params.metric === 'string' && params.metric !== '' ? params.metric : 'hook_events';
			const out: Record<string, string | string[]> = { measure: metric, top: '8' };
			appendParam(out, 'bucket', params.bucket);
			const group = params.group;
			if (typeof group === 'string' && group !== '' && group !== 'none') out.dim = group;
			return out;
		}
		case 'quality': {
			const out: Record<string, string | string[]> = {};
			appendParam(out, 'kind', params.kind);
			appendParam(out, 'bucket', params.bucket);
			return out;
		}
		case 'executions': {
			const out: Record<string, string | string[]> = {};
			appendParam(out, 'shape', params.shape);
			appendParam(out, 'bucket', params.bucket);
			appendParam(out, 'limit', params.limit);
			return out;
		}
		case 'repos': {
			const out: Record<string, string | string[]> = {
				measure: typeof params.measure === 'string' ? params.measure : 'hook_events',
				dim: 'repo_id',
				top: '100',
				bucket: 'none'
			};
			return out;
		}
		case 'overview': {
			const measure =
				typeof params.measure === 'string' && params.measure !== '' ? params.measure : 'hook_events';
			return { measure, bucket: typeof params.bucket === 'string' ? params.bucket : 'day' };
		}
		case 'conversations': {
			const out: Record<string, string | string[]> = {
				measure: typeof params.measure === 'string' ? params.measure : 'cost_usd',
				grain: typeof params.grain === 'string' ? params.grain : 'conversation'
			};
			appendParam(out, 'limit', params.limit);
			return out;
		}
		case 'explore':
			return {};
		default:
			return { ...params };
	}
}
