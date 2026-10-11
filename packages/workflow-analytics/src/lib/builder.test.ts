import { describe, expect, it } from 'vitest';
import {
	allowedBuckets,
	allowedCharts,
	allowedDims,
	configToParams,
	defaultConfig,
	dimOrder,
	isRangeOk,
	parseConfig,
	weekdayLabel,
	type BuilderConfig
} from './builder';
import type { Schema } from './types';

const schema: Schema = {
	measures: [
		{ name: 'cost_usd', unit: 'usd', dims: ['harness', 'repo_id', 'model', 'conversation_id', 'hour_of_day', 'weekday'] },
		{ name: 'rejections', unit: 'count', dims: ['stage', 'hour_of_day', 'weekday'] }
	],
	buckets: ['none', 'hour', 'day', 'week', 'month']
};

describe('allowedCharts', () => {
	it('dims 0: a single number without a bucket, line/area/bar with one', () => {
		expect(allowedCharts(0, 'none')).toEqual([]);
		expect(allowedCharts(0, 'day')).toEqual(['line', 'area', 'bar']);
	});

	it('dims 1: bar/treemap without a bucket, line/area/bar/stackedbar/heatmap with one', () => {
		expect(allowedCharts(1, 'none')).toEqual(['bar', 'treemap']);
		expect(allowedCharts(1, 'day')).toEqual(['line', 'area', 'bar', 'stackedbar', 'heatmap']);
	});

	it('dims 2: heatmap/treemap/bar/stackedbar without a bucket, multiples/line/area with one', () => {
		expect(allowedCharts(2, 'none')).toEqual(['heatmap', 'treemap', 'bar', 'stackedbar']);
		expect(allowedCharts(2, 'day')).toEqual(['multiples', 'line', 'area']);
	});

	it('other dimension counts fit nothing', () => {
		expect(allowedCharts(3, 'day')).toEqual([]);
	});
});

describe('parseConfig', () => {
	it('falls back to the first measure when the measure is absent or unknown', () => {
		expect(parseConfig(new URLSearchParams(), schema).measure).toBe('cost_usd');
		expect(parseConfig(new URLSearchParams([['m', 'nope']]), schema).measure).toBe('cost_usd');
	});

	it('returns an empty measure when the schema has none', () => {
		expect(parseConfig(new URLSearchParams(), { measures: [], buckets: [] }).measure).toBe('');
	});

	it('drops dims the measure does not carry, deduplicates and keeps order, capping at two', () => {
		const q = new URLSearchParams([
			['m', 'rejections'],
			['d', 'harness'],
			['d', 'stage'],
			['d', 'stage'],
			['d', 'weekday']
		]);
		expect(parseConfig(q, schema).dims).toEqual(['stage', 'weekday']);
	});

	it('turns an absent or unknown bucket into none', () => {
		expect(parseConfig(new URLSearchParams(), schema).bucket).toBe('none');
		expect(parseConfig(new URLSearchParams([['b', 'nope']]), schema).bucket).toBe('none');
		expect(parseConfig(new URLSearchParams([['b', 'week']]), schema).bucket).toBe('week');
	});

	it('turns an illegal chart into the first allowed kind, or line when there are none', () => {
		const q = new URLSearchParams([
			['m', 'cost_usd'],
			['d', 'model'],
			['d', 'harness'],
			['c', 'line']
		]);
		expect(parseConfig(q, schema).chart).toBe('heatmap');
		expect(parseConfig(new URLSearchParams(), schema).chart).toBe('line');
	});

	it('clamps top to [1,100], defaulting to 20 when absent or NaN', () => {
		expect(parseConfig(new URLSearchParams(), schema).top).toBe(20);
		expect(parseConfig(new URLSearchParams([['top', 'abc']]), schema).top).toBe(20);
		expect(parseConfig(new URLSearchParams([['top', '42']]), schema).top).toBe(42);
		expect(parseConfig(new URLSearchParams([['top', '0']]), schema).top).toBe(1);
		expect(parseConfig(new URLSearchParams([['top', '500']]), schema).top).toBe(100);
	});
});

describe('configToParams', () => {
	it('always sets m and c, appends dims and omits the defaults b=none and top=20', () => {
		const p = configToParams({ measure: 'cost_usd', dims: [], bucket: 'none', chart: 'line', top: 20 });
		expect(p.get('m')).toBe('cost_usd');
		expect(p.get('c')).toBe('line');
		expect(p.has('b')).toBe(false);
		expect(p.has('top')).toBe(false);
		expect(p.getAll('d')).toEqual([]);
	});

	it('sets a non-default bucket, top and repeated dims', () => {
		const p = configToParams({ measure: 'rejections', dims: ['stage', 'weekday'], bucket: 'day', chart: 'line', top: 5 });
		expect(p.get('b')).toBe('day');
		expect(p.get('top')).toBe('5');
		expect(p.getAll('d')).toEqual(['stage', 'weekday']);
	});

	it('round trips a legal configuration', () => {
		const cfg: BuilderConfig = { measure: 'cost_usd', dims: ['model'], bucket: 'day', chart: 'stackedbar', top: 50 };
		expect(parseConfig(configToParams(cfg), schema)).toEqual(cfg);
		const noBucket: BuilderConfig = { measure: 'cost_usd', dims: ['harness', 'repo_id'], bucket: 'none', chart: 'heatmap', top: 20 };
		expect(parseConfig(configToParams(noBucket), schema)).toEqual(noBucket);
	});
});

describe('defaultConfig', () => {
	it('is the first measure, no dims, day and line', () => {
		expect(defaultConfig(schema)).toEqual({ measure: 'cost_usd', dims: [], bucket: 'day', chart: 'line', top: 20 });
		expect(defaultConfig({ measures: [], buckets: [] })).toEqual({ measure: '', dims: [], bucket: 'day', chart: 'line', top: 20 });
	});
});

describe('allowedDims', () => {
	it('never returns a dim outside the measure, for either measure', () => {
		const chosenSets = [[], ['harness'], ['stage'], ['harness', 'repo_id'], ['hour_of_day', 'weekday'], ['nope']];
		for (const m of schema.measures)
			for (const chosen of chosenSets)
				for (const d of allowedDims(schema, m.name, chosen)) expect(m.dims).toContain(d);
	});

	it('drops already-chosen dims and returns nothing once two are chosen', () => {
		expect(allowedDims(schema, 'rejections', ['stage'])).toEqual(['hour_of_day', 'weekday']);
		expect(allowedDims(schema, 'rejections', ['stage', 'weekday'])).toEqual([]);
		expect(allowedDims(schema, 'unknown', [])).toEqual([]);
	});
});

describe('allowedBuckets', () => {
	it('returns the schema buckets restricted to the known values', () => {
		expect(allowedBuckets(schema)).toEqual(['none', 'hour', 'day', 'week', 'month']);
		expect(allowedBuckets({ measures: [], buckets: ['nope', 'day'] })).toEqual(['day']);
	});
});

describe('dimOrder', () => {
	it('sorts hour_of_day and weekday numerically, everything else by name', () => {
		expect(dimOrder('hour_of_day', ['10', '2', '1'])).toEqual(['1', '2', '10']);
		expect(dimOrder('weekday', ['6', '0', '3'])).toEqual(['0', '3', '6']);
		expect(dimOrder('harness', ['b', 'a', 'c'])).toEqual(['a', 'b', 'c']);
	});

	it('does not mutate the input', () => {
		const keys = ['b', 'a'];
		expect(dimOrder('harness', keys)).toEqual(['a', 'b']);
		expect(keys).toEqual(['b', 'a']);
	});
});

describe('weekdayLabel', () => {
	it('maps 0..6 to Sun..Sat and leaves anything else unchanged', () => {
		expect(['0', '1', '6'].map(weekdayLabel)).toEqual(['Sun', 'Mon', 'Sat']);
		expect(weekdayLabel('7')).toBe('7');
		expect(weekdayLabel('x')).toBe('x');
		expect(weekdayLabel('')).toBe('');
	});
});

describe('isRangeOk', () => {
	const week = { from: new Date('2025-01-01T00:00:00Z'), to: new Date('2025-01-08T00:00:00Z'), all: false, clamped: false };

	it('is true when the bucket fits the window within the cap', () => {
		expect(isRangeOk(week, 'hour', 'UTC')).toBe(true);
	});

	it('is false when the bucket exceeds the cap', () => {
		const wide = { ...week, to: new Date('2025-06-01T00:00:00Z') };
		expect(isRangeOk(wide, 'hour', 'UTC')).toBe(false);
	});

	it('is true for the none bucket and for an open window', () => {
		expect(isRangeOk(week, 'none', 'UTC')).toBe(true);
		expect(isRangeOk({ all: true, clamped: false }, 'hour', 'UTC')).toBe(true);
	});
});
