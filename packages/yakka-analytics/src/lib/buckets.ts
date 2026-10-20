// Bucket sizing for series charts: the finest bucket that fits the API's 400-bucket cap. The count
// is an upper bound (one partial edge bucket each side plus one DST day). Pure; tz via Intl only.
export type Bucket = 'hour' | 'day' | 'week' | 'month';

/** Series reads wider than this are not requested. */
export const BUCKET_CAP = 400;

const ORDER: Bucket[] = ['hour', 'day', 'week', 'month'];
const HOUR = 3600000;
const DAY = 86400000;

function ymd(tz: string, d: Date): { year: number; month: number; day: number } {
	const out: Record<string, number> = {};
	for (const p of new Intl.DateTimeFormat('en-US', {
		timeZone: tz,
		year: 'numeric',
		month: '2-digit',
		day: '2-digit'
	}).formatToParts(d))
		if (p.type !== 'literal') out[p.type] = Number(p.value);
	return { year: out.year, month: out.month, day: out.day };
}

/** An upper bound on the bucket count for a window in `tz`. */
export function bucketCount(bucket: Bucket, from: Date, to: Date, tz: string): number {
	const ms = to.getTime() - from.getTime();
	if (bucket === 'hour') return Math.ceil(ms / HOUR) + 2;
	if (bucket === 'day') return Math.ceil(ms / DAY) + 2;
	if (bucket === 'week') return Math.ceil(ms / (7 * DAY)) + 2;
	const a = ymd(tz, from);
	const b = ymd(tz, to);
	return (b.year - a.year) * 12 + (b.month - a.month) + 1 + 2;
}

/** The finest allowed bucket within the cap, or null when none fits. */
export function pickBucket(
	from: Date,
	to: Date,
	tz: string,
	allowed: Bucket[] = ['hour', 'day', 'week', 'month'],
	cap = BUCKET_CAP
): Bucket | null {
	for (const bucket of ORDER) {
		if (!allowed.includes(bucket)) continue;
		if (bucketCount(bucket, from, to, tz) <= cap) return bucket;
	}
	return null;
}
