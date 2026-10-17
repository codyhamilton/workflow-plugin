import { describe, expect, it, vi } from 'vitest';
import {
	chartParamsFromQuery,
	DASHBOARDS_KEY,
	ImportError,
	reportFromPathname,
	VIEWS_KEY,
	createStore,
	viewHref,
	type SavedView
} from './views';

function fake(initial: Record<string, string> = {}) {
	const map = new Map(Object.entries(initial));
	const setItem = vi.fn((k: string, v: string) => {
		map.set(k, v);
	});
	return {
		getItem: (k: string) => (map.has(k) ? (map.get(k) as string) : null),
		setItem
	};
}

describe('reportFromPathname / chartParamsFromQuery', () => {
	it('maps site paths to report ids', () => {
		expect(reportFromPathname('/')).toBe('overview');
		expect(reportFromPathname('/usage')).toBe('usage');
		expect(reportFromPathname('/settings')).toBeNull();
	});

	it('keeps chart keys and drops window and filters', () => {
		const q = new URLSearchParams('range=7d&measure=cost_usd&repo_id=r1&from=2020-01-01');
		expect(chartParamsFromQuery('usage', q)).toEqual({ measure: 'cost_usd' });
	});

	it('stores hooks split under dim and round-trips split in viewHref', () => {
		const q = new URLSearchParams('split=tool&bucket=day');
		expect(chartParamsFromQuery('hooks', q)).toEqual({ dim: 'tool', bucket: 'day' });
		const href = viewHref({
			id: 'v1',
			name: 'H',
			report: 'hooks',
			params: { dim: 'tool', bucket: 'day' }
		});
		expect(href).toBe('/hooks?split=tool&bucket=day');
	});
});

describe('saveView', () => {
	it('replaces a view with the same name in place and keeps its id', () => {
		const s = createStore(fake());
		const a = s.saveView('Home', 'overview', {});
		const b = s.saveView('Home', 'usage', { measure: 'cost_usd' });
		expect(b.id).toBe(a.id);
		expect(s.listViews()).toHaveLength(1);
		expect(s.listViews()[0]).toEqual({
			id: a.id,
			name: 'Home',
			report: 'usage',
			params: { measure: 'cost_usd' }
		});
	});

	it('throws ImportError on invalid report or params', () => {
		const s = createStore(fake());
		expect(() => s.saveView('X', 'nope' as SavedView['report'], {})).toThrow(ImportError);
		expect(() => s.saveView('X', 'usage', { range: '7d' })).toThrow(ImportError);
		expect(s.listViews()).toHaveLength(0);
	});
});

describe('deleteView', () => {
	it('cascades into every dashboard', () => {
		const s = createStore(fake());
		const v1 = s.saveView('A', 'overview', {});
		const v2 = s.saveView('B', 'trends', {});
		const d = s.createDashboard('d');
		s.addToDashboard(d.id, v1.id);
		s.addToDashboard(d.id, v2.id);
		s.deleteView(v1.id);
		expect(s.listViews().map((v) => v.id)).toEqual([v2.id]);
		expect(s.listDashboards()[0].tiles.map((t) => t.viewId)).toEqual([v2.id]);
	});
});

describe('dashboards', () => {
	it('adds, moves and removes while preserving order, allowing duplicates', () => {
		const s = createStore(fake());
		const v1 = s.saveView('A', 'overview', {});
		const v2 = s.saveView('B', 'trends', {});
		const v3 = s.saveView('C', 'usage', {});
		const d = s.createDashboard('d');
		s.addToDashboard(d.id, v1.id);
		s.addToDashboard(d.id, v2.id);
		s.addToDashboard(d.id, v3.id);
		expect(s.listDashboards()[0].tiles.map((t) => t.viewId)).toEqual([v1.id, v2.id, v3.id]);

		s.moveInDashboard(d.id, 0, 2);
		expect(s.listDashboards()[0].tiles.map((t) => t.viewId)).toEqual([v2.id, v3.id, v1.id]);

		s.removeFromDashboard(d.id, 1);
		expect(s.listDashboards()[0].tiles.map((t) => t.viewId)).toEqual([v2.id, v1.id]);

		s.addToDashboard(d.id, v1.id);
		expect(s.listDashboards()[0].tiles.map((t) => t.viewId)).toEqual([v2.id, v1.id, v1.id]);
	});

	it('refuses a thirteenth tile', () => {
		const s = createStore(fake());
		const d = s.createDashboard('full');
		const ids: string[] = [];
		for (let i = 0; i < 12; i++) {
			const v = s.saveView(`v${i}`, 'overview', {});
			ids.push(v.id);
			s.addToDashboard(d.id, v.id);
		}
		const extra = s.saveView('extra', 'overview', {});
		expect(() => s.addToDashboard(d.id, extra.id)).toThrow(ImportError);
		expect(s.listDashboards()[0].tiles).toHaveLength(12);
		void ids;
	});

	it('throws a plain Error for an unknown dashboard id', () => {
		const s = createStore(fake());
		expect(() => s.addToDashboard('nope', 'v')).toThrow(Error);
		expect(() => s.exportDashboard('nope')).toThrow(Error);
		expect(() => s.exportDashboard('nope')).not.toThrow(ImportError);
	});
});

describe('viewHref', () => {
	it('builds a report path without window or filters', () => {
		const view: SavedView = {
			id: '1',
			name: 'u',
			report: 'usage',
			params: { measure: 'cost_usd' }
		};
		expect(viewHref(view)).toBe('/usage?measure=cost_usd');
	});
});

describe('export / import', () => {
	function seed() {
		const s = createStore(fake());
		const v1 = s.saveView('Alpha', 'usage', { measure: 'cost_usd' });
		const v2 = s.saveView('Beta', 'trends', { metric: 'hook_events' });
		const d = s.createDashboard('My Dash');
		s.addToDashboard(d.id, v1.id);
		s.addToDashboard(d.id, v2.id);
		return { s, json: s.exportDashboard(d.id), d };
	}

	it('serialises version 2 in dashboard tile order', () => {
		const { json } = seed();
		expect(json).toBe(
			'{"version":2,"name":"My Dash","tiles":[{"name":"Alpha","report":"usage","params":{"measure":"cost_usd"},"w":1},{"name":"Beta","report":"trends","params":{"metric":"hook_events"},"w":1}]}'
		);
	});

	it('reproduces name, order and configs in a second store', () => {
		const { json } = seed();
		const b = createStore(fake());
		const imported = b.importDashboard(json);
		expect(imported.tilesDropped).toBe(0);
		expect(imported.viewsDropped).toBe(0);
		expect(imported.dashboard.name).toBe('My Dash');
		expect(b.listDashboards()).toHaveLength(1);
		expect(b.exportDashboard(imported.dashboard.id)).toBe(json);
	});

	it('bumps a duplicate dashboard name and reuses matching views', () => {
		const { json } = seed();
		const b = createStore(fake());
		b.importDashboard(json);
		const again = b.importDashboard(json);
		expect(again.dashboard.name).toBe('My Dash (2)');
		expect(b.listDashboards()).toHaveLength(2);
		expect(b.listViews()).toHaveLength(2);
	});

	it('caps import at twelve tiles and reports tilesDropped', () => {
		const s = createStore(fake());
		const tiles = [];
		for (let i = 0; i < 13; i++) {
			tiles.push({ name: `t${i}`, report: 'overview', params: {}, w: 1 });
		}
		const json = JSON.stringify({ version: 2, name: 'big', tiles });
		const result = s.importDashboard(json);
		expect(result.tilesDropped).toBe(1);
		expect(result.dashboard.tiles).toHaveLength(12);
	});

	it('migrates v1 urls into report params', () => {
		const s = createStore(fake());
		const json =
			'{"version":1,"name":"x","views":[{"name":"u","url":"/usage?range=7d&measure=cost_usd&repo_id=r1"}]}';
		const result = s.importDashboard(json);
		expect(result.viewsDropped).toBe(0);
		const v = s.listViews()[0];
		expect(v.report).toBe('usage');
		expect(v.params).toEqual({ measure: 'cost_usd' });
		expect(result.dashboard.tiles).toHaveLength(1);
	});

	it('drops unknown report paths and counts viewsDropped', () => {
		const s = createStore(fake());
		const json = '{"version":1,"name":"x","views":[{"name":"u","url":"/settings?foo=1"}]}';
		const result = s.importDashboard(json);
		expect(result.viewsDropped).toBe(1);
		expect(s.listViews()).toHaveLength(0);
		expect(result.dashboard.tiles).toHaveLength(0);
	});
});

describe('import errors', () => {
	const cases: [string, string][] = [
		['bad JSON', '{not json'],
		['missing version', '{"name":"x","tiles":[]}'],
		['unsupported version', '{"version":3,"name":"x","tiles":[]}'],
		['v1 non-array views', '{"version":1,"name":"x","views":{}}'],
		['v2 non-array tiles', '{"version":2,"name":"x","tiles":{}}'],
		['v1 url without a leading slash', '{"version":1,"name":"x","views":[{"name":"a","url":"foo"}]}'],
		['v1 url with a // prefix', '{"version":1,"name":"x","views":[{"name":"a","url":"//evil"}]}'],
		['v1 url with a colon before the query', '{"version":1,"name":"x","views":[{"name":"a","url":"/a:b?c"}]}'],
		[
			'v1 url over 2000 characters',
			`{"version":1,"name":"x","views":[{"name":"a","url":"/${'a'.repeat(2000)}"}]}`
		]
	];

	for (const [label, json] of cases) {
		it(`rejects ${label} and writes nothing`, () => {
			const st = fake();
			const s = createStore(st);
			st.setItem.mockClear();
			expect(() => s.importDashboard(json)).toThrow(ImportError);
			expect(st.setItem).not.toHaveBeenCalled();
			expect(s.listViews()).toEqual([]);
			expect(s.listDashboards()).toEqual([]);
		});
	}
});

describe('localStorage migration', () => {
	it('migrates legacy url views and viewIds dashboards on read', () => {
		const st = fake({
			[VIEWS_KEY]: JSON.stringify([{ id: 'v1', name: 'U', url: '/usage?measure=cost_usd&range=7d' }]),
			[DASHBOARDS_KEY]: JSON.stringify([{ id: 'd1', name: 'D', viewIds: ['v1'] }])
		});
		const s = createStore(st);
		expect(s.listViews()[0]).toMatchObject({ report: 'usage', params: { measure: 'cost_usd' } });
		expect(s.listDashboards()[0].tiles).toEqual([{ viewId: 'v1', w: 1 }]);
	});
});

describe('robustness', () => {
	it('keeps working in memory when storage throws', () => {
		const throwing = {
			getItem: () => {
				throw new Error('blocked');
			},
			setItem: () => {
				throw new Error('blocked');
			}
		};
		const s = createStore(throwing);
		const v = s.saveView('A', 'overview', {});
		const d = s.createDashboard('D');
		s.addToDashboard(d.id, v.id);
		expect(s.listViews()).toHaveLength(1);
		expect(s.listDashboards()[0].tiles.map((t) => t.viewId)).toEqual([v.id]);
	});

	it('reads corrupt JSON as empty', () => {
		const st = fake({ [VIEWS_KEY]: '{bad', [DASHBOARDS_KEY]: 'not-json' });
		const s = createStore(st);
		expect(s.listViews()).toEqual([]);
		expect(s.listDashboards()).toEqual([]);
	});

	it('notifies subscribers after a write until unsubscribed', () => {
		const s = createStore(fake());
		const fn = vi.fn();
		const unsubscribe = s.subscribe(fn);
		s.saveView('A', 'overview', {});
		expect(fn).toHaveBeenCalledTimes(1);
		unsubscribe();
		s.saveView('B', 'trends', {});
		expect(fn).toHaveBeenCalledTimes(1);
	});
});
