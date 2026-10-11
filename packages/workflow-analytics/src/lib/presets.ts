// Named time windows for the range picker. `to` is rounded up to the next full hour so navigating
// within the hour produces identical params; local midnights are found by iteration for DST days.
// Pure; time zones come only from Intl.DateTimeFormat.
import type { PresetId } from './urlstate';

export interface Preset {
	id: PresetId;
	label: string;
}

export const PRESETS: Preset[] = [
	{ id: 'today', label: 'Today' },
	{ id: '24h', label: '24h' },
	{ id: '7d', label: '7d' },
	{ id: '30d', label: '30d' },
	{ id: '90d', label: '90d' },
	{ id: 'month', label: 'This month' },
	{ id: 'ytd', label: 'YTD' },
	{ id: 'all', label: 'All time' }
];

const HOUR = 3600000;
const DAY = 86400000;

function parts(tz: string, d: Date): Record<string, number> {
	const out: Record<string, number> = {};
	for (const p of new Intl.DateTimeFormat('en-US', {
		timeZone: tz,
		hourCycle: 'h23',
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit',
		second: '2-digit'
	}).formatToParts(d))
		if (p.type !== 'literal') out[p.type] = Number(p.value);
	return out;
}

function offsetMs(tz: string, d: Date): number {
	const p = parts(tz, d);
	return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - d.getTime();
}

function localMidnight(tz: string, y: number, m: number, d: number): Date {
	let ts = Date.UTC(y, m - 1, d, 0, 0, 0);
	for (let i = 0; i < 3; i++) {
		const next = Date.UTC(y, m - 1, d, 0, 0, 0) - offsetMs(tz, new Date(ts));
		if (next === ts) break;
		ts = next;
	}
	return new Date(ts);
}

/** The window a preset covers at `now` in `tz`; `all` has none. */
export function presetWindow(id: PresetId, now: Date, tz: string): { from: Date; to: Date } | null {
	if (id === 'all') return null;
	const to = new Date(Math.ceil(now.getTime() / HOUR) * HOUR);
	if (id === 'today') {
		const p = parts(tz, now);
		return { from: localMidnight(tz, p.year, p.month, p.day), to };
	}
	if (id === 'month') {
		const p = parts(tz, now);
		return { from: localMidnight(tz, p.year, p.month, 1), to };
	}
	if (id === 'ytd') {
		const p = parts(tz, now);
		return { from: localMidnight(tz, p.year, 1, 1), to };
	}
	const spans: Record<Exclude<PresetId, 'today' | 'month' | 'ytd' | 'all'>, number> = {
		'24h': DAY,
		'7d': 7 * DAY,
		'30d': 30 * DAY,
		'90d': 90 * DAY
	};
	return { from: new Date(to.getTime() - spans[id]), to };
}
