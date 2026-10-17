// Named saved views and dashboards over localStorage, plus dashboard JSON export/import.
// Pure TypeScript: no Svelte, no $app. A view stores a report id and chart-only params;
// window and shared filters live on the dashboard URL. Every storage read and write is
// guarded, so the store keeps working in memory.

import { DIM_KEYS } from './urlstate';

export const REPORT_IDS = [
	'overview',
	'trends',
	'usage',
	'repos',
	'hooks',
	'quality',
	'executions',
	'conversations',
	'explore',
	'builder'
] as const;
export type ReportId = (typeof REPORT_IDS)[number];

export const CHART_PARAM_KEYS = new Set<string>([
	'measure',
	'dim',
	'bucket',
	'chart',
	'top',
	'kind',
	'metric',
	'group',
	'grain',
	'shape',
	'limit'
]);

const HOOKS_SPLIT_DIM = new Set(['norm_event', 'tool']);

const BUILDER_QUERY_TO_PARAM: Record<string, string> = {
	m: 'measure',
	d: 'dim',
	b: 'bucket',
	c: 'chart'
};

const BUILDER_PARAM_TO_QUERY: Record<string, string> = {
	measure: 'm',
	dim: 'd',
	bucket: 'b',
	chart: 'c'
};

const REPORT_PATH: Record<ReportId, string> = {
	overview: '/',
	trends: '/trends',
	usage: '/usage',
	repos: '/repos',
	hooks: '/hooks',
	quality: '/quality',
	executions: '/executions',
	conversations: '/conversations',
	explore: '/explore',
	builder: '/builder'
};

const MAX_DASHBOARD_TILES = 12;
const MAX_URL_LENGTH = 2000;

const WINDOW_AND_FILTER_KEYS = new Set<string>(['range', 'from', 'to']);
for (const key of DIM_KEYS) {
	WINDOW_AND_FILTER_KEYS.add(key);
	WINDOW_AND_FILTER_KEYS.add(`x.${key}`);
}

export interface SavedView {
	id: string;
	name: string;
	report: ReportId;
	params: Record<string, string | string[]>;
}

export interface DashboardTile {
	viewId: string;
	w: 1 | 2;
}

export interface Dashboard {
	id: string;
	name: string;
	tiles: DashboardTile[];
}

export interface ImportResult {
	dashboard: Dashboard;
	tilesDropped: number;
	viewsDropped: number;
}

export interface ViewStore {
	listViews(): SavedView[];
	saveView(name: string, report: ReportId, params: Record<string, string | string[]>): SavedView;
	deleteView(id: string): void;
	listDashboards(): Dashboard[];
	createDashboard(name: string): Dashboard;
	addToDashboard(dashboardId: string, viewId: string): void;
	removeFromDashboard(dashboardId: string, index: number): void;
	moveInDashboard(dashboardId: string, from: number, to: number): void;
	deleteDashboard(id: string): void;
	exportDashboard(id: string): string;
	importDashboard(json: string): ImportResult;
	subscribe(fn: () => void): () => void;
}

export class ImportError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'ImportError';
	}
}

export const VIEWS_KEY = 'workflow-analytics-views:views';
export const DASHBOARDS_KEY = 'workflow-analytics-views:dashboards';

type Backing = Pick<Storage, 'getItem' | 'setItem'>;

let counter = 0;

function newId(): string {
	const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
	if (c && typeof c.randomUUID === 'function') return c.randomUUID();
	counter += 1;
	return `id-${counter}`;
}

function isReportId(value: unknown): value is ReportId {
	return typeof value === 'string' && (REPORT_IDS as readonly string[]).includes(value);
}

/** Legacy import only: a site-relative path with bounded length. */
function isValidLegacyViewUrl(url: unknown): url is string {
	if (typeof url !== 'string') return false;
	if (url.length > MAX_URL_LENGTH) return false;
	if (!url.startsWith('/') || url.startsWith('//')) return false;
	const q = url.indexOf('?');
	const beforeQuery = q === -1 ? url : url.slice(0, q);
	if (beforeQuery.includes(':')) return false;
	return true;
}

export function reportFromPathname(path: string): ReportId | null {
	const p = path.replace(/\/$/, '') || '/';
	if (p === '/') return 'overview';
	for (const id of REPORT_IDS) {
		if (id === 'overview') continue;
		if (p === `/${id}`) return id;
	}
	return null;
}

function canonicalChartKey(urlKey: string): string | null {
	if (CHART_PARAM_KEYS.has(urlKey)) return urlKey;
	return BUILDER_QUERY_TO_PARAM[urlKey] ?? null;
}

/** Chart-only params from a page query; window and shared filter keys are omitted. */
export function chartParamsFromQuery(
	report: ReportId,
	searchParams: URLSearchParams
): Record<string, string | string[]> {
	const params: Record<string, string | string[]> = {};
	const seen = new Set<string>();
	for (const urlKey of searchParams.keys()) {
		if (seen.has(urlKey)) continue;
		seen.add(urlKey);
		if (WINDOW_AND_FILTER_KEYS.has(urlKey)) continue;
		if (report === 'hooks' && urlKey === 'split') {
			const v = searchParams.get(urlKey);
			if (v !== null) params.dim = v;
			continue;
		}
		const canonical = canonicalChartKey(urlKey);
		if (!canonical) continue;
		if (canonical === 'dim') {
			const values = searchParams.getAll(urlKey);
			params.dim = values.length === 1 ? values[0] : values;
		} else {
			const v = searchParams.get(urlKey);
			if (v !== null) params[canonical] = v;
		}
	}
	return params;
}

function paramsToSearchParams(report: ReportId, params: Record<string, string | string[]>): URLSearchParams {
	const out = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (!CHART_PARAM_KEYS.has(key)) continue;
		let urlKey =
			report === 'builder' && BUILDER_PARAM_TO_QUERY[key] ? BUILDER_PARAM_TO_QUERY[key] : key;
		if (
			report === 'hooks' &&
			key === 'dim' &&
			typeof value === 'string' &&
			HOOKS_SPLIT_DIM.has(value)
		) {
			urlKey = 'split';
		}
		if (Array.isArray(value)) {
			for (const v of value) out.append(urlKey, v);
		} else {
			out.set(urlKey, value);
		}
	}
	return out;
}

/** Navigable site path for a saved view: report route plus chart params only. */
export function viewHref(view: SavedView): string {
	const path = REPORT_PATH[view.report];
	const q = paramsToSearchParams(view.report, view.params).toString();
	return q ? `${path}?${q}` : path;
}

function viewFromLegacyUrl(url: string): { report: ReportId; params: Record<string, string | string[]> } | null {
	if (!isValidLegacyViewUrl(url)) return null;
	const qIdx = url.indexOf('?');
	const path = qIdx === -1 ? url : url.slice(0, qIdx);
	const report = reportFromPathname(path);
	if (!report) return null;
	const search = qIdx === -1 ? '' : url.slice(qIdx + 1);
	return { report, params: chartParamsFromQuery(report, new URLSearchParams(search)) };
}

function normalizeParams(raw: unknown): Record<string, string | string[]> | null {
	if (typeof raw !== 'object' || raw === null) return null;
	const out: Record<string, string | string[]> = {};
	for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
		if (!CHART_PARAM_KEYS.has(key)) continue;
		if (typeof value === 'string') out[key] = value;
		else if (Array.isArray(value) && value.every((v) => typeof v === 'string')) out[key] = value;
		else return null;
	}
	return out;
}

function paramsEqual(a: Record<string, string | string[]>, b: Record<string, string | string[]>): boolean {
	const keysA = Object.keys(a).sort();
	const keysB = Object.keys(b).sort();
	if (keysA.length !== keysB.length) return false;
	for (let i = 0; i < keysA.length; i++) {
		if (keysA[i] !== keysB[i]) return false;
		const ka = keysA[i];
		const va = a[ka];
		const vb = b[ka];
		if (Array.isArray(va) || Array.isArray(vb)) {
			const aa = Array.isArray(va) ? va : [va];
			const bb = Array.isArray(vb) ? vb : [vb];
			if (aa.length !== bb.length) return false;
			for (let j = 0; j < aa.length; j++) if (aa[j] !== bb[j]) return false;
		} else if (va !== vb) return false;
	}
	return true;
}

function copyView(v: SavedView): SavedView {
	return { id: v.id, name: v.name, report: v.report, params: { ...v.params } };
}

function copyTile(t: DashboardTile): DashboardTile {
	return { viewId: t.viewId, w: t.w };
}

function copyDashboard(d: Dashboard): Dashboard {
	return { id: d.id, name: d.name, tiles: d.tiles.map(copyTile) };
}

function migrateViewEntry(raw: unknown): SavedView | null {
	if (typeof raw !== 'object' || raw === null) return null;
	const o = raw as Record<string, unknown>;
	if (typeof o.id !== 'string' || typeof o.name !== 'string') return null;
	if (isReportId(o.report)) {
		const params = normalizeParams(o.params);
		if (params === null) return null;
		return { id: o.id, name: o.name, report: o.report, params };
	}
	if (typeof o.url === 'string') {
		const parsed = viewFromLegacyUrl(o.url);
		if (!parsed) return null;
		return { id: o.id, name: o.name, report: parsed.report, params: parsed.params };
	}
	return null;
}

function migrateDashboardEntry(raw: unknown): Dashboard | null {
	if (typeof raw !== 'object' || raw === null) return null;
	const o = raw as Record<string, unknown>;
	if (typeof o.id !== 'string' || typeof o.name !== 'string') return null;
	if (Array.isArray(o.tiles)) {
		const tiles: DashboardTile[] = [];
		for (const entry of o.tiles) {
			if (typeof entry !== 'object' || entry === null) return null;
			const t = entry as { viewId?: unknown; w?: unknown };
			if (typeof t.viewId !== 'string') return null;
			const w = t.w === 2 ? 2 : 1;
			tiles.push({ viewId: t.viewId, w });
		}
		return { id: o.id, name: o.name, tiles };
	}
	if (Array.isArray(o.viewIds)) {
		const tiles: DashboardTile[] = [];
		for (const vid of o.viewIds) {
			if (typeof vid !== 'string') return null;
			tiles.push({ viewId: vid, w: 1 });
		}
		return { id: o.id, name: o.name, tiles };
	}
	return null;
}

function memoryStorage(): Backing {
	const map = new Map<string, string>();
	return {
		getItem: (k: string) => (map.has(k) ? (map.get(k) as string) : null),
		setItem: (k: string, v: string) => {
			map.set(k, v);
		}
	};
}

function usableLocalStorage(): Storage | undefined {
	try {
		if (typeof localStorage === 'undefined') return undefined;
		const probe = 'workflow-analytics-views:probe';
		localStorage.setItem(probe, '1');
		localStorage.removeItem(probe);
		return localStorage;
	} catch {
		return undefined;
	}
}

function readArray<T>(backing: Backing, key: string, migrate: (raw: unknown) => T | null): T[] {
	try {
		const raw = backing.getItem(key);
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		const out: T[] = [];
		for (const entry of parsed) {
			const item = migrate(entry);
			if (item !== null) out.push(item);
		}
		return out;
	} catch {
		return [];
	}
}

function writeArray(backing: Backing, key: string, value: unknown): void {
	try {
		backing.setItem(key, JSON.stringify(value));
	} catch {
		// storage unavailable; the in-memory copy is the session's source of truth.
	}
}

type StorageHost = {
	window?: {
		addEventListener(type: 'storage', listener: () => void): void;
		removeEventListener(type: 'storage', listener: () => void): void;
	};
};

function validateSaveParams(params: Record<string, string | string[]>): void {
	for (const key of Object.keys(params)) {
		if (!CHART_PARAM_KEYS.has(key)) throw new ImportError(`Invalid chart param: ${key}`);
	}
}

function findMatchingView(
	views: SavedView[],
	name: string,
	report: ReportId,
	params: Record<string, string | string[]>
): SavedView | undefined {
	return views.find((v) => v.name === name && v.report === report && paramsEqual(v.params, params));
}

export function createStore(storage?: Backing): ViewStore {
	const backing: Backing = storage ?? usableLocalStorage() ?? memoryStorage();
	const views: SavedView[] = readArray(backing, VIEWS_KEY, migrateViewEntry);
	const dashboards: Dashboard[] = readArray(backing, DASHBOARDS_KEY, migrateDashboardEntry);
	const listeners = new Set<() => void>();

	function persistViews(): void {
		writeArray(backing, VIEWS_KEY, views);
	}

	function persistDashboards(): void {
		writeArray(backing, DASHBOARDS_KEY, dashboards);
	}

	function notify(): void {
		for (const fn of listeners) fn();
	}

	function findDashboard(id: string): Dashboard {
		const d = dashboards.find((entry) => entry.id === id);
		if (!d) throw new Error(`Unknown dashboard: ${id}`);
		return d;
	}

	return {
		listViews() {
			return views.map(copyView);
		},

		saveView(name, report, params) {
			if (!isReportId(report)) throw new ImportError(`Invalid report: ${String(report)}`);
			validateSaveParams(params);
			const existing = views.find((v) => v.name === name);
			if (existing) {
				existing.report = report;
				existing.params = { ...params };
				persistViews();
				notify();
				return copyView(existing);
			}
			const view: SavedView = { id: newId(), name, report, params: { ...params } };
			views.push(view);
			persistViews();
			notify();
			return copyView(view);
		},

		deleteView(id) {
			const i = views.findIndex((v) => v.id === id);
			if (i !== -1) views.splice(i, 1);
			for (const d of dashboards) {
				d.tiles = d.tiles.filter((t) => t.viewId !== id);
			}
			persistViews();
			persistDashboards();
			notify();
		},

		listDashboards() {
			return dashboards.map(copyDashboard);
		},

		createDashboard(name) {
			const dashboard: Dashboard = { id: newId(), name, tiles: [] };
			dashboards.push(dashboard);
			persistDashboards();
			notify();
			return copyDashboard(dashboard);
		},

		addToDashboard(dashboardId, viewId) {
			const d = findDashboard(dashboardId);
			if (d.tiles.length >= MAX_DASHBOARD_TILES) {
				throw new ImportError(`Dashboard cannot have more than ${MAX_DASHBOARD_TILES} tiles`);
			}
			d.tiles.push({ viewId, w: 1 });
			persistDashboards();
			notify();
		},

		removeFromDashboard(dashboardId, index) {
			const d = findDashboard(dashboardId);
			d.tiles.splice(index, 1);
			persistDashboards();
			notify();
		},

		moveInDashboard(dashboardId, from, to) {
			const d = findDashboard(dashboardId);
			if (from < 0 || from >= d.tiles.length) return;
			const [item] = d.tiles.splice(from, 1);
			const target = Math.max(0, Math.min(to, d.tiles.length));
			d.tiles.splice(target, 0, item);
			persistDashboards();
			notify();
		},

		deleteDashboard(id) {
			const i = dashboards.findIndex((d) => d.id === id);
			if (i !== -1) dashboards.splice(i, 1);
			persistDashboards();
			notify();
		},

		exportDashboard(id) {
			const d = findDashboard(id);
			const tiles = d.tiles
				.map((t) => {
					const v = views.find((view) => view.id === t.viewId);
					if (!v) return null;
					return { name: v.name, report: v.report, params: v.params, w: t.w };
				})
				.filter((t): t is NonNullable<typeof t> => t !== null);
			return JSON.stringify({ version: 2, name: d.name, tiles });
		},

		importDashboard(json) {
			let parsed: unknown;
			try {
				parsed = JSON.parse(json);
			} catch {
				throw new ImportError('Invalid JSON');
			}
			if (typeof parsed !== 'object' || parsed === null) throw new ImportError('Invalid dashboard');
			const obj = parsed as { version?: unknown; name?: unknown; views?: unknown; tiles?: unknown };
			const version = obj.version;
			if (version !== 1 && version !== 2) throw new ImportError('Unsupported dashboard version');

			type IncomingTile = {
				name: string;
				report: ReportId;
				params: Record<string, string | string[]>;
				w: 1 | 2;
			};

			const incoming: IncomingTile[] = [];
			let viewsDropped = 0;

			if (version === 1) {
				if (!Array.isArray(obj.views)) throw new ImportError('Dashboard views must be an array');
				for (const entry of obj.views) {
					if (typeof entry !== 'object' || entry === null) throw new ImportError('Invalid view');
					const e = entry as { name?: unknown; url?: unknown };
					if (!isValidLegacyViewUrl(e.url)) throw new ImportError(`Invalid view url: ${String(e.url)}`);
					const converted = viewFromLegacyUrl(e.url);
					if (!converted) {
						viewsDropped += 1;
						continue;
					}
					incoming.push({
						name: typeof e.name === 'string' ? e.name : '',
						report: converted.report,
						params: converted.params,
						w: 1
					});
				}
			} else {
				if (!Array.isArray(obj.tiles)) throw new ImportError('Dashboard tiles must be an array');
				for (const entry of obj.tiles) {
					if (typeof entry !== 'object' || entry === null) throw new ImportError('Invalid tile');
					const e = entry as {
						name?: unknown;
						report?: unknown;
						params?: unknown;
						w?: unknown;
					};
					if (!isReportId(e.report)) {
						viewsDropped += 1;
						continue;
					}
					const params = normalizeParams(e.params ?? {});
					if (params === null) throw new ImportError('Invalid tile params');
					validateSaveParams(params);
					const w = e.w === 2 ? 2 : 1;
					incoming.push({
						name: typeof e.name === 'string' ? e.name : '',
						report: e.report,
						params,
						w
					});
				}
			}

			const tilesDropped = Math.max(0, incoming.length - MAX_DASHBOARD_TILES);
			const kept = incoming.slice(0, MAX_DASHBOARD_TILES);

			const baseName = typeof obj.name === 'string' ? obj.name : '';
			let name = baseName;
			let n = 2;
			while (dashboards.some((d) => d.name === name)) {
				name = `${baseName} (${n})`;
				n += 1;
			}

			const tileRefs: DashboardTile[] = [];
			for (const { name: viewName, report, params, w } of kept) {
				let view = findMatchingView(views, viewName, report, params);
				if (!view) {
					view = { id: newId(), name: viewName, report, params: { ...params } };
					views.push(view);
				}
				tileRefs.push({ viewId: view.id, w });
			}

			const dashboard: Dashboard = { id: newId(), name, tiles: tileRefs };
			dashboards.push(dashboard);
			persistViews();
			persistDashboards();
			notify();
			return { dashboard: copyDashboard(dashboard), tilesDropped, viewsDropped };
		},

		subscribe(fn) {
			listeners.add(fn);
			const win = (globalThis as StorageHost).window;
			const onStorage = () => fn();
			if (win) win.addEventListener('storage', onStorage);
			return () => {
				listeners.delete(fn);
				if (win) win.removeEventListener('storage', onStorage);
			};
		}
	};
}

export const store: ViewStore = createStore();
