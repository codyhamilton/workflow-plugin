import type { AggregateResult, BreakdownResult, TrendResult } from '../aggregate';
import type { BreakdownFrameData, TrendFrameData } from '../analysis/chart-frame';

export function sumPoints(points: { v: number }[]): number {
	return points.reduce((a, p) => a + p.v, 0);
}

export function seriesValues(
	series: { key: string; points: { v: number }[] }[] | undefined
): Record<string, number> {
	const out: Record<string, number> = {};
	for (const s of series ?? []) out[s.key] = sumPoints(s.points);
	return out;
}

export function trendFrame(
	measure: string,
	bucket: TrendFrameData['bucket'],
	result: TrendResult,
	dim?: string,
	tz?: string
): TrendFrameData {
	const w = result.window;
	const span =
		w && 'from' in w && w.from && w.to
			? { from: new Date(w.from), to: new Date(w.to), ...(tz ? { tz } : {}) }
			: {};
	return {
		measure,
		bucket,
		series: (result.series ?? []).map((s) => ({ name: s.key, points: s.points })),
		...(dim ? { breakdownDim: dim } : {}),
		...span
	};
}

export function breakdownFrame(measure: string, dim: string, result: BreakdownResult): BreakdownFrameData {
	const rows = (result.series ?? []).map((s) => ({
		key: s.key,
		label: s.key,
		value: sumPoints(s.points)
	}));
	return { measure, dim, rows };
}

export function ignoredFilters(result: AggregateResult | null): string[] {
	if (!result?.ignored_filters?.length) return [];
	return [...result.ignored_filters].sort();
}
