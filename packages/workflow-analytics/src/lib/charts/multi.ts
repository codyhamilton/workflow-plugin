// Pure option builders and data transforms for the grouped/stacked bar and small-multiples
// builder variants. No DOM and no echarts import, so they are testable in isolation.
import { dimOrder, weekdayLabel } from '../builder';
import { timeOption } from './options';
import type { Tokens } from './theme';
import type { QueryResponse, QueryRow } from '../types';

export const MAX_PANELS = 12;
export const OTHER = '__other__';

export interface Category {
	key: string;
	label: string;
	clickable: boolean;
}
export interface BarSeries {
	name: string;
	values: number[];
}
export interface GroupedBarProps {
	categories: Category[];
	series: BarSeries[];
	stacked?: boolean;
	unit?: string;
}

export interface MultiPoint {
	t: string;
	v: number;
}
export interface MultiSeries {
	name: string;
	points: MultiPoint[];
}
export interface MultiPanel {
	key: string;
	title: string;
	series: MultiSeries[];
}
export interface MultiplesLayout {
	panels: MultiPanel[];
	yMax: number;
}

function unique(xs: string[]): string[] {
	return [...new Set(xs)];
}

function byTime(a: MultiPoint, b: MultiPoint): number {
	return a.t.localeCompare(b.t);
}

/** Order keys for a dimension via `dimOrder`, keeping any `__other__` bucket last. */
export function orderKeys(dim: string, keys: string[]): string[] {
	const ordered = dimOrder(dim, keys);
	return [...ordered.filter((k) => k !== OTHER), ...ordered.filter((k) => k === OTHER)];
}

/** A display label for a key: weekday keys become Sun..Sat, others pass through unchanged. */
export function labelFor(dim: string, key: string): string {
	return dim === 'weekday' ? weekdayLabel(key) : key;
}

/** Categories (first dimension, or the time bucket) and series (second dimension, or measure). */
export function groupedBarProps(resp: QueryResponse): GroupedBarProps {
	const dims = resp.dims ?? [];
	const catDim = dims[0];
	const serDim = dims[1];
	const rows = resp.rows ?? [];
	const catKeyOf = (r: QueryRow) => (catDim !== undefined ? (r.k[0] ?? '') : (r.t ?? ''));
	const serKeyOf = (r: QueryRow) => (serDim !== undefined ? (r.k[1] ?? '') : resp.measure);
	const catKeys = orderKeys(catDim ?? '', unique(rows.map(catKeyOf)));
	const serKeys = serDim !== undefined ? orderKeys(serDim, unique(rows.map(serKeyOf))) : [resp.measure];
	const totals = new Map<string, number>();
	for (const r of rows) {
		const k = `${serKeyOf(r)}\u0000${catKeyOf(r)}`;
		totals.set(k, (totals.get(k) ?? 0) + r.v);
	}
	const categories = catKeys.map((key) => ({
		key,
		label: labelFor(catDim ?? '', key),
		clickable: key !== OTHER
	}));
	const series = serKeys.map((name) => ({
		name,
		values: catKeys.map((ck) => totals.get(`${name}\u0000${ck}`) ?? 0)
	}));
	return { categories, series };
}

/** Column/stacked bar option: one bar series per second-dimension key. */
export function groupedBarOption(p: GroupedBarProps, t: Tokens) {
	const categories = p.categories ?? [];
	const series = (p.series ?? []).map((s, i) => ({
		name: s.name,
		type: 'bar' as const,
		stack: p.stacked === true ? 'total' : undefined,
		itemStyle: { color: t.series[i % t.series.length] },
		data: (s.values ?? []).map((v, j) => ({
			value: v,
			key: categories[j]?.key ?? '',
			clickable: categories[j]?.clickable !== false
		}))
	}));
	return {
		animation: false,
		backgroundColor: 'transparent',
		grid: { left: 48, right: 24, top: 24, bottom: 32, containLabel: false },
		legend: { show: series.length > 1, textStyle: { color: t.text } },
		tooltip: { trigger: 'axis' },
		xAxis: {
			type: 'category',
			data: categories.map((c) => c.label),
			axisLabel: { color: t.muted },
			axisLine: { lineStyle: { color: t.border } },
			axisTick: { show: false }
		},
		yAxis: {
			type: 'value',
			axisLabel: { color: t.muted },
			splitLine: { lineStyle: { color: t.border } }
		},
		color: t.series,
		series
	};
}

/** One time-series panel per distinct second-dimension key, all sharing a single y max. */
export function multiplesLayout(resp: QueryResponse, max = MAX_PANELS): MultiplesLayout {
	const dims = resp.dims ?? [];
	const seriesDim = dims[0];
	const panelDim = dims[1];
	const rows = resp.rows ?? [];
	const panelKeys = orderKeys(panelDim ?? '', unique(rows.map((r) => r.k[1] ?? '')));
	const seriesKeys = orderKeys(seriesDim ?? '', unique(rows.map((r) => r.k[0] ?? '')));
	const byPanel = new Map<string, Map<string, MultiPoint[]>>();
	let yMax = 0;
	for (const r of rows) {
		const pk = r.k[1] ?? '';
		const sk = r.k[0] ?? '';
		let panel = byPanel.get(pk);
		if (!panel) byPanel.set(pk, (panel = new Map()));
		let pts = panel.get(sk);
		if (!pts) panel.set(sk, (pts = []));
		pts.push({ t: r.t ?? '', v: r.v });
		if (r.v > yMax) yMax = r.v;
	}
	const complete = (src: Map<string, MultiPoint[]> | undefined): MultiSeries[] =>
		seriesKeys.map((name) => ({
			name,
			points: [...(src?.get(name) ?? [])].sort(byTime)
		}));
	const panels: MultiPanel[] = panelKeys
		.slice(0, max)
		.map((key) => ({ key, title: labelFor(panelDim ?? '', key), series: complete(byPanel.get(key)) }));
	const rest = panelKeys.slice(max);
	if (rest.length > 0) {
		const folded = new Map<string, Map<string, number>>();
		for (const key of rest) {
			const src = byPanel.get(key);
			if (!src) continue;
			for (const [name, pts] of src) {
				let m = folded.get(name);
				if (!m) folded.set(name, (m = new Map()));
				for (const pt of pts) m.set(pt.t, (m.get(pt.t) ?? 0) + pt.v);
			}
		}
		const series = seriesKeys.map((name) => ({
			name,
			points: [...(folded.get(name) ?? new Map()).entries()]
				.map(([t, v]) => ({ t, v }))
				.sort(byTime)
		}));
		panels.push({ key: '__more__', title: `${rest.length} more`, series });
	}
	return { panels, yMax };
}

/** A panel option with the shared y max applied. */
export function panelOption(
	panel: MultiPanel,
	yMax: number,
	bucket: 'hour' | 'day' | 'week' | 'month',
	t: Tokens
) {
	const option = timeOption({ series: panel.series, bucket, stacked: false }, t);
	(option.yAxis as { max?: number }).max = yMax;
	return option;
}

/** Time series for line/area: one per first-dimension key, or one named after the measure. */
export function lineSeries(resp: QueryResponse): MultiSeries[] {
	const dims = resp.dims ?? [];
	const rows = resp.rows ?? [];
	if (dims.length === 0) {
		return [
			{
				name: resp.measure,
				points: rows.map((r) => ({ t: r.t ?? '', v: r.v })).sort(byTime)
			}
		];
	}
	const keys = orderKeys(dims[0], unique(rows.map((r) => r.k[0] ?? '')));
	const grouped = new Map<string, Map<string, number>>();
	for (const r of rows) {
		const k = r.k[0] ?? '';
		let m = grouped.get(k);
		if (!m) grouped.set(k, (m = new Map()));
		m.set(r.t ?? '', (m.get(r.t ?? '') ?? 0) + r.v);
	}
	return keys.map((key) => ({
		name: labelFor(dims[0], key),
		points: [...(grouped.get(key) ?? new Map()).entries()]
			.map(([t, v]) => ({ t, v }))
			.sort(byTime)
	}));
}

/** Heatmap cells: x = first dimension (or time), y = second dimension (or time). */
export function heatmapProps(resp: QueryResponse): {
	cells: { x: number; y: number; v: number }[];
	xLabels: string[];
	yLabels: string[];
} {
	const dims = resp.dims ?? [];
	const rows = resp.rows ?? [];
	const xDim = dims[0];
	const yDim = dims[1];
	const xKeyOf = (r: QueryRow) => (xDim !== undefined ? (r.k[0] ?? '') : (r.t ?? ''));
	const yKeyOf = (r: QueryRow) =>
		yDim !== undefined ? (r.k[1] ?? '') : dims.length === 1 ? (r.t ?? '') : (r.k[0] ?? '');
	const xKeys = orderKeys(xDim ?? '', unique(rows.map(xKeyOf)));
	const yKeys = orderKeys(yDim ?? '', unique(rows.map(yKeyOf)));
	const cells: { x: number; y: number; v: number }[] = [];
	for (const r of rows) {
		const x = xKeys.indexOf(xKeyOf(r));
		const y = yKeys.indexOf(yKeyOf(r));
		if (x >= 0 && y >= 0) cells.push({ x, y, v: r.v });
	}
	return {
		cells,
		xLabels: xKeys.map((k) => labelFor(xDim ?? '', k)),
		yLabels: yKeys.map((k) => labelFor(yDim ?? '', k))
	};
}

/** Treemap nodes: one level (first dimension) or two levels (both dimensions). */
export function treemapNodes(resp: QueryResponse): {
	name: string;
	value?: number;
	children?: { name: string; value?: number }[];
}[] {
	const dims = resp.dims ?? [];
	const rows = resp.rows ?? [];
	if (dims.length >= 2) {
		const byCat = new Map<string, Map<string, number>>();
		for (const r of rows) {
			const a = r.k[0] ?? '';
			const b = r.k[1] ?? '';
			let m = byCat.get(a);
			if (!m) byCat.set(a, (m = new Map()));
			m.set(b, (m.get(b) ?? 0) + r.v);
		}
		return [...byCat.entries()].map(([a, m]) => ({
			name: a,
			value: [...m.values()].reduce((s, x) => s + x, 0),
			children: [...m.entries()].map(([b, v]) => ({ name: b, value: v }))
		}));
	}
	const totals = new Map<string, number>();
	for (const r of rows) {
		const a = r.k[0] ?? '';
		totals.set(a, (totals.get(a) ?? 0) + r.v);
	}
	return [...totals.entries()].map(([a, v]) => ({ name: a, value: v }));
}
