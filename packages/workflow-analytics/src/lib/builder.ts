// The pure model behind the chart builder: the URL form of a chart configuration, the pairings and
// chart kinds the shape allows, and the schema constraints. Reuses buckets.ts for the range check.
import { pickBucket } from './buckets';
import type { Window } from './params';
import type { Schema } from './types';

export type ChartKind = 'line' | 'area' | 'bar' | 'stackedbar' | 'heatmap' | 'treemap' | 'multiples';
export type Bucket = 'none' | 'hour' | 'day' | 'week' | 'month';

export interface BuilderConfig {
	measure: string;
	dims: string[];
	bucket: Bucket;
	chart: ChartKind;
	top: number;
}

const BUCKETS: Bucket[] = ['none', 'hour', 'day', 'week', 'month'];
const CHART_KINDS: ChartKind[] = ['line', 'area', 'bar', 'stackedbar', 'heatmap', 'treemap', 'multiples'];
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function isBucket(v: string): v is Bucket {
	return (BUCKETS as string[]).includes(v);
}

function isChartKind(v: string): v is ChartKind {
	return (CHART_KINDS as string[]).includes(v);
}

/** The chart kinds that fit a dimension count and bucket. */
export function allowedCharts(dims: number, bucket: Bucket): ChartKind[] {
	if (dims === 0) return bucket === 'none' ? [] : ['line', 'area', 'bar'];
	if (dims === 1) return bucket === 'none' ? ['bar', 'treemap'] : ['line', 'area', 'bar', 'stackedbar', 'heatmap'];
	if (dims === 2)
		return bucket === 'none' ? ['heatmap', 'treemap', 'bar', 'stackedbar'] : ['multiples', 'line', 'area'];
	return [];
}

/** The schema's buckets, restricted to the five known values. */
export function allowedBuckets(schema: Schema): Bucket[] {
	return schema.buckets.filter(isBucket);
}

/** The dimensions that may still be chosen for a measure, in schema order. */
export function allowedDims(schema: Schema, measure: string, chosen: string[]): string[] {
	if (chosen.length >= 2) return [];
	const m = schema.measures.find((x) => x.name === measure);
	if (m === undefined) return [];
	return m.dims.filter((d) => !chosen.includes(d));
}

/** The default chart configuration: first measure, no dims, day, line. */
export function defaultConfig(schema: Schema): BuilderConfig {
	return { measure: schema.measures[0]?.name ?? '', dims: [], bucket: 'day', chart: 'line', top: 20 };
}

/** Parse and sanitise a chart configuration from the URL query, never throwing. */
export function parseConfig(q: URLSearchParams, schema: Schema): BuilderConfig {
	const measure = schema.measures.find((m) => m.name === q.get('m'))?.name ?? schema.measures[0]?.name ?? '';
	const m = schema.measures.find((x) => x.name === measure);
	const allowed = m?.dims ?? [];
	const dims: string[] = [];
	for (const d of q.getAll('d')) {
		if (dims.length >= 2) break;
		if (allowed.includes(d) && !dims.includes(d)) dims.push(d);
	}
	const rawBucket = q.get('b') ?? '';
	const bucket: Bucket =
		rawBucket !== '' && isBucket(rawBucket) && schema.buckets.includes(rawBucket) ? rawBucket : 'none';
	const kinds = allowedCharts(dims.length, bucket);
	const rawChart = q.get('c') ?? '';
	const chart: ChartKind =
		rawChart !== '' && isChartKind(rawChart) && kinds.includes(rawChart) ? rawChart : (kinds[0] ?? 'line');
	const rawTop = q.get('top');
	const parsed = rawTop === null ? NaN : Number.parseInt(rawTop, 10);
	const top = Number.isNaN(parsed) ? 20 : Math.min(100, Math.max(1, parsed));
	return { measure, dims, bucket, chart, top };
}

/** Serialise a chart configuration to URL params, omitting the defaults `b=none` and `top=20`. */
export function configToParams(cfg: BuilderConfig): URLSearchParams {
	const p = new URLSearchParams();
	p.set('m', cfg.measure);
	for (const d of cfg.dims) p.append('d', d);
	if (cfg.bucket !== 'none') p.set('b', cfg.bucket);
	p.set('c', cfg.chart);
	if (cfg.top !== 20) p.set('top', String(cfg.top));
	return p;
}

/** Sort category keys: `hour_of_day` and `weekday` numerically, everything else by name. */
export function dimOrder(dim: string, keys: string[]): string[] {
	const out = [...keys];
	if (dim === 'hour_of_day' || dim === 'weekday') out.sort((a, b) => Number(a) - Number(b));
	else out.sort((a, b) => a.localeCompare(b));
	return out;
}

/** Map a `strftime('%w')` weekday key to Sun..Sat, returning the key unchanged otherwise. */
export function weekdayLabel(k: string): string {
	return /^[0-6]$/.test(k) ? WEEKDAYS[Number(k)] : k;
}

/** True when the bucket fits the window within the 400-bucket cap. */
export function isRangeOk(win: Window, bucket: Bucket, tz: string): boolean {
	if (bucket === 'none') return true;
	if (win.from === undefined || win.to === undefined) return true;
	return pickBucket(win.from, win.to, tz, [bucket], 400) === bucket;
}
