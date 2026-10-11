import { describe, expect, it, vi } from 'vitest';
import {
	DASHBOARDS_KEY,
	ImportError,
	VIEWS_KEY,
	createStore,
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

describe('saveView', () => {
	it('replaces a view with the same name in place and keeps its id', () => {
		const s = createStore(fake());
		const a = s.saveView('Home', '/a?range=1d');
		const b = s.saveView('Home', '/b?range=7d');
		expect(b.id).toBe(a.id);
		expect(s.listViews()).toHaveLength(1);
		expect(s.listViews()[0].url).toBe('/b?range=7d');
	});

	it('applies the import url rule and throws ImportError on a bad url', () => {
		const s = createStore(fake());
		expect(() => s.saveView('X', 'no-slash')).toThrow(ImportError);
		expect(() => s.saveView('X', '//evil')).toThrow(ImportError);
		expect(s.listViews()).toHaveLength(0);
	});
});

describe('deleteView', () => {
	it('cascades into every dashboard', () => {
		const s = createStore(fake());
		const v1 = s.saveView('A', '/a');
		const v2 = s.saveView('B', '/b');
		const d = s.createDashboard('d');
		s.addToDashboard(d.id, v1.id);
		s.addToDashboard(d.id, v2.id);
		s.deleteView(v1.id);
		expect(s.listViews().map((v) => v.id)).toEqual([v2.id]);
		expect(s.listDashboards()[0].viewIds).toEqual([v2.id]);
	});
});

describe('dashboards', () => {
	it('adds, moves and removes while preserving order, allowing duplicates', () => {
		const s = createStore(fake());
		const v1 = s.saveView('A', '/a');
		const v2 = s.saveView('B', '/b');
		const v3 = s.saveView('C', '/c');
		const d = s.createDashboard('d');
		s.addToDashboard(d.id, v1.id);
		s.addToDashboard(d.id, v2.id);
		s.addToDashboard(d.id, v3.id);
		expect(s.listDashboards()[0].viewIds).toEqual([v1.id, v2.id, v3.id]);

		s.moveInDashboard(d.id, 0, 2);
		expect(s.listDashboards()[0].viewIds).toEqual([v2.id, v3.id, v1.id]);

		s.removeFromDashboard(d.id, 1);
		expect(s.listDashboards()[0].viewIds).toEqual([v2.id, v1.id]);

		s.addToDashboard(d.id, v1.id);
		expect(s.listDashboards()[0].viewIds).toEqual([v2.id, v1.id, v1.id]);
	});

	it('throws a plain Error for an unknown dashboard id', () => {
		const s = createStore(fake());
		expect(() => s.addToDashboard('nope', 'v')).toThrow(Error);
		expect(() => s.exportDashboard('nope')).toThrow(Error);
		expect(() => s.exportDashboard('nope')).not.toThrow(ImportError);
	});
});

describe('export / import', () => {
	function seed() {
		const s = createStore(fake());
		const v1 = s.saveView('Alpha', '/path?range=7d');
		const v2 = s.saveView('Beta', '/other?kind=x');
		const d = s.createDashboard('My Dash');
		s.addToDashboard(d.id, v1.id);
		s.addToDashboard(d.id, v2.id);
		return s.exportDashboard(d.id);
	}

	it('serialises the exact format in dashboard order', () => {
		const json = seed();
		expect(json).toBe(
			'{"version":1,"name":"My Dash","views":[{"name":"Alpha","url":"/path?range=7d"},{"name":"Beta","url":"/other?kind=x"}]}'
		);
	});

	it('reproduces name, order and urls in a second store', () => {
		const json = seed();
		const b = createStore(fake());
		const imported = b.importDashboard(json);
		expect(imported.name).toBe('My Dash');
		expect(b.listDashboards()).toHaveLength(1);
		expect(b.exportDashboard(imported.id)).toBe(json);
	});

	it('bumps a duplicate dashboard name and reuses matching views', () => {
		const json = seed();
		const b = createStore(fake());
		b.importDashboard(json);
		const again = b.importDashboard(json);
		expect(again.name).toBe('My Dash (2)');
		expect(b.listDashboards()).toHaveLength(2);
		expect(b.listViews()).toHaveLength(2);
	});
});

describe('import errors', () => {
	const cases: [string, string][] = [
		['bad JSON', '{not json'],
		['missing version', '{"name":"x","views":[]}'],
		['non-1 version', '{"version":2,"name":"x","views":[]}'],
		['non-array views', '{"version":1,"name":"x","views":{}}'],
		['url without a leading slash', '{"version":1,"name":"x","views":[{"name":"a","url":"foo"}]}'],
		['url with a // prefix', '{"version":1,"name":"x","views":[{"name":"a","url":"//evil"}]}'],
		['url with a colon before the query', '{"version":1,"name":"x","views":[{"name":"a","url":"/a:b?c"}]}'],
		['url over 2000 characters', `{"version":1,"name":"x","views":[{"name":"a","url":"/${'a'.repeat(2000)}"}]}`]
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

	it('rejects a 2000-character url boundary correctly', () => {
		const s = createStore(fake());
		const ok: SavedView = s.saveView('ok', `/${'a'.repeat(1999)}`);
		expect(ok.url).toHaveLength(2000);
		expect(() => s.saveView('bad', `/${'a'.repeat(2000)}`)).toThrow(ImportError);
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
		const v = s.saveView('A', '/a?range=1d');
		const d = s.createDashboard('D');
		s.addToDashboard(d.id, v.id);
		expect(s.listViews()).toHaveLength(1);
		expect(s.listDashboards()[0].viewIds).toEqual([v.id]);
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
		s.saveView('A', '/a');
		expect(fn).toHaveBeenCalledTimes(1);
		unsubscribe();
		s.saveView('B', '/b');
		expect(fn).toHaveBeenCalledTimes(1);
	});
});
