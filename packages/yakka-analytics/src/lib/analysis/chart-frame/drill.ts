/** Dim names that are never drill targets (design 7, Drill-down). */
export const NON_DRILL_FILTER_DIMS = new Set(['hour_of_day', 'weekday']);

export const OTHER_BUCKET = '__other__';

/**
 * Whether a mark may emit a drill intent for filter dim `dim` and value `key`.
 * `__other__`, empty keys, and hour/weekday dims are not drillable.
 */
export function isDrillableMark(dim: string | undefined, key: string): boolean {
	if (!dim) return false;
	if (NON_DRILL_FILTER_DIMS.has(dim)) return false;
	if (key === '' || key === OTHER_BUCKET) return false;
	return true;
}
