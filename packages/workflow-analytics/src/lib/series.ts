import type { Series } from './types';

const DAY = 86_400_000;

/**
 * The API's series are sparse: a bucket with no rows has no point, which is a count of 0.
 * Returns each series with a point for every bucket from the earliest to the latest `t` in the
 * response (step 1 day or 7 days), missing buckets as n = 0, so a line drops to zero instead of
 * interpolating across an empty day or week.
 */
export function fillBuckets(series: Series['series'], bucket: Series['bucket']): Series['series'] {
	const all = series.flatMap((s) => s.points.map((p) => Date.parse(`${p.t}T00:00:00Z`))).filter((n) => !Number.isNaN(n));
	if (all.length === 0) return series;
	const step = bucket === 'week' ? 7 * DAY : DAY;
	const lo = Math.min(...all);
	const hi = Math.max(...all);
	const ts: string[] = [];
	for (let t = lo; t <= hi; t += step) ts.push(new Date(t).toISOString().slice(0, 10));
	return series.map((s) => {
		const by = new Map(s.points.map((p) => [p.t, p.n]));
		return { key: s.key, points: ts.map((t) => ({ t, n: by.get(t) ?? 0 })) };
	});
}
