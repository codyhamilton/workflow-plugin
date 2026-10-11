// Named saved views and dashboards over localStorage, plus dashboard JSON export/import.
// Pure TypeScript: no Svelte, no $app. A view URL is a site-relative "/path?query" string;
// saveView validates it with the same rule as import, so every stored url is safe as an
// iframe src. Every storage read and write is guarded, so the store keeps working in memory.

export interface SavedView {
	id: string;
	name: string;
	url: string;
}

export interface Dashboard {
	id: string;
	name: string;
	viewIds: string[];
}

export interface ViewStore {
	listViews(): SavedView[];
	saveView(name: string, url: string): SavedView;
	deleteView(id: string): void;
	listDashboards(): Dashboard[];
	createDashboard(name: string): Dashboard;
	addToDashboard(dashboardId: string, viewId: string): void;
	removeFromDashboard(dashboardId: string, index: number): void;
	moveInDashboard(dashboardId: string, from: number, to: number): void;
	deleteDashboard(id: string): void;
	exportDashboard(id: string): string;
	importDashboard(json: string): Dashboard;
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

const MAX_URL_LENGTH = 2000;

type Backing = Pick<Storage, 'getItem' | 'setItem'>;

let counter = 0;

function newId(): string {
	const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
	if (c && typeof c.randomUUID === 'function') return c.randomUUID();
	counter += 1;
	return `id-${counter}`;
}

/** A site-relative path: single leading slash, no scheme colon before the query, bounded length. */
export function isValidViewUrl(url: unknown): url is string {
	if (typeof url !== 'string') return false;
	if (url.length > MAX_URL_LENGTH) return false;
	if (!url.startsWith('/') || url.startsWith('//')) return false;
	const q = url.indexOf('?');
	const beforeQuery = q === -1 ? url : url.slice(0, q);
	if (beforeQuery.includes(':')) return false;
	return true;
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

function readArray<T>(backing: Backing, key: string): T[] {
	try {
		const raw = backing.getItem(key);
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		return Array.isArray(parsed) ? (parsed as T[]) : [];
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

function copyView(v: SavedView): SavedView {
	return { id: v.id, name: v.name, url: v.url };
}

function copyDashboard(d: Dashboard): Dashboard {
	return { id: d.id, name: d.name, viewIds: [...d.viewIds] };
}

type StorageHost = {
	window?: {
		addEventListener(type: 'storage', listener: () => void): void;
		removeEventListener(type: 'storage', listener: () => void): void;
	};
};

export function createStore(storage?: Backing): ViewStore {
	const backing: Backing = storage ?? usableLocalStorage() ?? memoryStorage();
	const views: SavedView[] = readArray<SavedView>(backing, VIEWS_KEY);
	const dashboards: Dashboard[] = readArray<Dashboard>(backing, DASHBOARDS_KEY);
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

		saveView(name, url) {
			if (!isValidViewUrl(url)) throw new ImportError(`Invalid view url: ${String(url)}`);
			const existing = views.find((v) => v.name === name);
			if (existing) {
				existing.url = url;
				persistViews();
				notify();
				return copyView(existing);
			}
			const view: SavedView = { id: newId(), name, url };
			views.push(view);
			persistViews();
			notify();
			return copyView(view);
		},

		deleteView(id) {
			const i = views.findIndex((v) => v.id === id);
			if (i !== -1) views.splice(i, 1);
			for (const d of dashboards) {
				d.viewIds = d.viewIds.filter((vid) => vid !== id);
			}
			persistViews();
			persistDashboards();
			notify();
		},

		listDashboards() {
			return dashboards.map(copyDashboard);
		},

		createDashboard(name) {
			const dashboard: Dashboard = { id: newId(), name, viewIds: [] };
			dashboards.push(dashboard);
			persistDashboards();
			notify();
			return copyDashboard(dashboard);
		},

		addToDashboard(dashboardId, viewId) {
			const d = findDashboard(dashboardId);
			d.viewIds.push(viewId);
			persistDashboards();
			notify();
		},

		removeFromDashboard(dashboardId, index) {
			const d = findDashboard(dashboardId);
			d.viewIds.splice(index, 1);
			persistDashboards();
			notify();
		},

		moveInDashboard(dashboardId, from, to) {
			const d = findDashboard(dashboardId);
			if (from < 0 || from >= d.viewIds.length) return;
			const [item] = d.viewIds.splice(from, 1);
			const target = Math.max(0, Math.min(to, d.viewIds.length));
			d.viewIds.splice(target, 0, item);
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
			const out = {
				version: 1,
				name: d.name,
				views: d.viewIds
					.map((vid) => views.find((v) => v.id === vid))
					.filter((v): v is SavedView => v !== undefined)
					.map((v) => ({ name: v.name, url: v.url }))
			};
			return JSON.stringify(out);
		},

		importDashboard(json) {
			let parsed: unknown;
			try {
				parsed = JSON.parse(json);
			} catch {
				throw new ImportError('Invalid JSON');
			}
			if (typeof parsed !== 'object' || parsed === null) throw new ImportError('Invalid dashboard');
			const obj = parsed as { version?: unknown; name?: unknown; views?: unknown };
			if (obj.version !== 1) throw new ImportError('Unsupported dashboard version');
			if (!Array.isArray(obj.views)) throw new ImportError('Dashboard views must be an array');

			const incoming: { name: string; url: string }[] = [];
			for (const entry of obj.views) {
				if (typeof entry !== 'object' || entry === null) throw new ImportError('Invalid view');
				const e = entry as { name?: unknown; url?: unknown };
				if (!isValidViewUrl(e.url)) throw new ImportError(`Invalid view url: ${String(e.url)}`);
				incoming.push({ name: typeof e.name === 'string' ? e.name : '', url: e.url });
			}

			const baseName = typeof obj.name === 'string' ? obj.name : '';
			let name = baseName;
			let n = 2;
			while (dashboards.some((d) => d.name === name)) {
				name = `${baseName} (${n})`;
				n += 1;
			}

			const viewIds: string[] = [];
			for (const { name: viewName, url } of incoming) {
				let view = views.find((v) => v.name === viewName && v.url === url);
				if (!view) {
					view = { id: newId(), name: viewName, url };
					views.push(view);
				}
				viewIds.push(view.id);
			}

			const dashboard: Dashboard = { id: newId(), name, viewIds };
			dashboards.push(dashboard);
			persistViews();
			persistDashboards();
			notify();
			return copyDashboard(dashboard);
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
