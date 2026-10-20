import { describe, expect, it, vi } from 'vitest';
import { get, list, remove, save, SAVED_ANALYSIS_KEY } from './saved-analysis';

function fakeStorage(initial: Record<string, string> = {}) {
	const map = new Map(Object.entries(initial));
	return {
		getItem: (k: string) => (map.has(k) ? (map.get(k) as string) : null),
		setItem: vi.fn((k: string, v: string) => {
			map.set(k, v);
		}),
		removeItem: vi.fn((k: string) => {
			map.delete(k);
		})
	} as Storage;
}

const sampleSpec = {
	window: { preset: '7d' as const, tz: 'UTC' },
	ask: { ask: 'trend' as const, measure: 'hook_events', bucket: 'day' as const }
};

describe('saved-analysis', () => {
	it('save/list round-trip and reopen by name', () => {
		const backing = fakeStorage();
		const a = save('My view', sampleSpec, backing);
		expect(a.name).toBe('My view');
		expect(a.spec).toEqual(sampleSpec);
		expect(list(backing)).toHaveLength(1);
		const found = list(backing).find((s) => s.name === 'My view');
		expect(found?.spec.ask).toEqual(sampleSpec.ask);
		expect(found?.spec.window).toEqual(sampleSpec.window);
	});

	it('replaces same name in place', () => {
		const backing = fakeStorage();
		const a = save('X', sampleSpec, backing);
		const b = save('X', { ...sampleSpec, ask: { ask: 'quality', kind: 'design', bucket: 'day' } }, backing);
		expect(b.id).toBe(a.id);
		expect(list(backing)).toHaveLength(1);
		expect(get(a.id, backing)?.spec.ask).toEqual({ ask: 'quality', kind: 'design', bucket: 'day' });
	});

	it('does not persist tenant', () => {
		const backing = fakeStorage();
		save('T', { ...sampleSpec, tenant: 'acme' }, backing);
		const raw = backing.getItem(SAVED_ANALYSIS_KEY);
		expect(raw).not.toContain('tenant');
	});

	it('remove drops entry', () => {
		const backing = fakeStorage();
		const a = save('gone', sampleSpec, backing);
		remove(a.id, backing);
		expect(list(backing)).toHaveLength(0);
	});
});
