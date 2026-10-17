// Pure ECharts option builder for sparse score drift (median line, p25–p75 band, optional baseline).
import type { Bucket } from '$lib/buckets';
import type { ScoreSeriesPoint } from '$lib/types';
import type { Tokens } from './theme';

const DAY = 86_400_000;

export interface ScoreBandProps {
	points: ScoreSeriesPoint[];
	bucket: 'day' | 'week' | 'month';
	from: Date;
	to: Date;
	tz: string;
	baselineMedian?: number;
}

function pad(n: number): string {
	return String(n).padStart(2, '0');
}

function partsIn(tz: string, d: Date) {
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
	return { y: out.year, m: out.month, d: out.day, h: out.hour };
}

function offsetMs(tz: string, d: Date): number {
	const p = partsIn(tz, d);
	return Date.UTC(p.y, p.m - 1, p.d, p.h) - d.getTime();
}

function localInstant(tz: string, y: number, m: number, d: number, h = 0): Date {
	let ts = Date.UTC(y, m - 1, d, h);
	for (let i = 0; i < 3; i++) {
		const next = Date.UTC(y, m - 1, d, h) - offsetMs(tz, new Date(ts));
		if (next === ts) break;
		ts = next;
	}
	return new Date(ts);
}

/** A bucket boundary as the server emits it (RFC3339 in `tz`, `Z` for UTC). */
export function instantKey(tz: string, d: Date): string {
	const p = partsIn(tz, d);
	const off = offsetMs(tz, d);
	const date = `${p.y}-${pad(p.m)}-${pad(p.d)}T${pad(p.h)}:00:00`;
	if (off === 0) return `${date}Z`;
	const sign = off > 0 ? '+' : '-';
	const abs = Math.abs(off);
	return `${date}${sign}${pad(Math.floor(abs / 3_600_000))}:${pad(Math.floor((abs % 3_600_000) / 60_000))}`;
}

/** Every bucket start between two instants, by calendar step in `tz`. */
export function bucketStarts(tz: string, bucket: Bucket, from: Date, to: Date): number[] {
	const p0 = partsIn(tz, from);
	let cur: Date;
	if (bucket === 'hour') cur = localInstant(tz, p0.y, p0.m, p0.d, p0.h);
	else if (bucket === 'day') cur = localInstant(tz, p0.y, p0.m, p0.d);
	else if (bucket === 'week') {
		const wd = (new Date(Date.UTC(p0.y, p0.m - 1, p0.d)).getUTCDay() + 6) % 7;
		const mon = new Date(Date.UTC(p0.y, p0.m - 1, p0.d) - wd * DAY);
		cur = localInstant(tz, mon.getUTCFullYear(), mon.getUTCMonth() + 1, mon.getUTCDate());
	} else cur = localInstant(tz, p0.y, p0.m, 1);
	const out: number[] = [];
	const end = to.getTime();
	for (let guard = 0; cur.getTime() <= end && guard < 10_000; guard++) {
		out.push(cur.getTime());
		const p = partsIn(tz, cur);
		if (bucket === 'hour') cur = localInstant(tz, p.y, p.m, p.d, p.h + 1);
		else if (bucket === 'day') cur = localInstant(tz, p.y, p.m, p.d + 1);
		else if (bucket === 'week') cur = localInstant(tz, p.y, p.m, p.d + 7);
		else cur = localInstant(tz, p.m === 12 ? p.y + 1 : p.y, p.m === 12 ? 1 : p.m + 1, 1);
	}
	return out;
}

export type ScoreBandRow = {
	t: string;
	n: number | '';
	p25: number | '';
	median: number | '';
	p75: number | '';
};

/** One table row per bucket in the window; missing API points become empty cells, not zero. */
export function scoreBandTableRows(p: ScoreBandProps): ScoreBandRow[] {
	const byT = new Map(p.points.map((pt) => [pt.t, pt]));
	return bucketStarts(p.tz, p.bucket, p.from, p.to).map((ms) => {
		const t = instantKey(p.tz, new Date(ms));
		const pt = byT.get(t);
		if (!pt) return { t, n: '', p25: '', median: '', p75: '' };
		return { t, n: pt.n, p25: pt.p25, median: pt.median, p75: pt.p75 };
	});
}

export function scoreBandOption(p: ScoreBandProps, t: Tokens) {
	const byT = new Map(p.points.map((pt) => [pt.t, pt]));
	const slots = bucketStarts(p.tz, p.bucket, p.from, p.to).map((ms) => {
		const tKey = instantKey(p.tz, new Date(ms));
		const pt = byT.get(tKey);
		return { t: tKey, pt };
	});

	const p25Data = slots.map(({ t, pt }) => (pt ? [t, pt.p25] : [t, null]));
	const bandData = slots.map(({ t, pt }) => (pt ? [t, pt.p75 - pt.p25] : [t, null]));
	const medianData = slots.map(({ t, pt }) => (pt ? [t, pt.median] : [t, null]));

	const bandColor = t.series[0];
	const medianColor = t.accent;

	const series: Record<string, unknown>[] = [
		{
			name: 'p25',
			type: 'line',
			stack: 'band',
			symbol: 'none',
			lineStyle: { opacity: 0 },
			connectNulls: false,
			data: p25Data
		},
		{
			name: 'p25–p75',
			type: 'line',
			stack: 'band',
			symbol: 'none',
			lineStyle: { opacity: 0 },
			areaStyle: { color: bandColor, opacity: 0.25 },
			connectNulls: false,
			data: bandData
		},
		{
			name: 'median',
			type: 'line',
			symbol: 'circle',
			showSymbol: true,
			symbolSize: 6,
			lineStyle: { width: 2, color: medianColor },
			itemStyle: { color: medianColor },
			connectNulls: false,
			data: medianData,
			...(typeof p.baselineMedian === 'number'
				? {
						markLine: {
							silent: true,
							symbol: 'none',
							lineStyle: { type: 'dashed', color: t.danger, width: 1 },
							label: { show: false },
							data: [{ yAxis: p.baselineMedian }]
						}
					}
				: {})
		}
	];

	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 24, top: 24, bottom: 32, containLabel: false },
		tooltip: { trigger: 'axis' },
		brush: {
			brushType: 'lineX',
			brushMode: 'single',
			xAxisIndex: 0,
			throttleType: 'debounce',
			throttleDelay: 100
		},
		toolbox: { show: true, right: 8, feature: { brush: { type: ['lineX', 'clear'] } } },
		xAxis: {
			type: 'time',
			axisLabel: { color: t.muted },
			axisLine: { lineStyle: { color: t.border } }
		},
		yAxis: {
			type: 'value',
			min: 0,
			max: 1,
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		color: t.series,
		series
	};
}
