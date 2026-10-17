import { describe, expect, it } from 'vitest';
import { apiParams, resolveWindow, scoresParams } from './params';
import { parseUrlState, type UrlState } from './urlstate';

const DAY = 86400000;
const NOW = new Date('2025-01-15T05:30:00Z');

function custom(from: string, to: string): UrlState {
	return { range: 'custom', from, to, include: {}, exclude: {} };
}

describe('resolveWindow', () => {
	it('clamps all to 399 days on rest routes', () => {
		const win = resolveWindow(parseUrlState(new URLSearchParams('range=all')), NOW, 'UTC', 'rest');
		expect(win.all).toBe(false);
		expect(win.clamped).toBe(true);
		expect(win.from!.getTime()).toBe(NOW.getTime() - 399 * DAY);
		expect(win.to!.getTime()).toBe(NOW.getTime());
	});

	it('lets the query route use all', () => {
		const win = resolveWindow(parseUrlState(new URLSearchParams('range=all')), NOW, 'UTC', 'query');
		expect(win.all).toBe(true);
		expect(win.clamped).toBe(false);
		expect(win.from).toBeUndefined();
	});

	it('clamps an over-wide custom range on rest', () => {
		const win = resolveWindow(custom('2020-01-01T00:00:00Z', '2025-01-01T00:00:00Z'), NOW, 'UTC', 'rest');
		expect(win.clamped).toBe(true);
		expect(win.to!.getTime() - win.from!.getTime()).toBe(399 * DAY);
	});

	it('does not clamp a narrow preset on rest', () => {
		const win = resolveWindow(parseUrlState(new URLSearchParams('range=7d')), NOW, 'UTC', 'rest');
		expect(win.clamped).toBe(false);
		expect(win.all).toBe(false);
		expect(win.from).toBeInstanceOf(Date);
	});
});

describe('apiParams', () => {
	it('sets tz and the RFC3339 window', () => {
		const s = parseUrlState(new URLSearchParams('range=30d'));
		const win = resolveWindow(s, NOW, 'Australia/Sydney', 'query');
		const r = apiParams(s, win, {}, 'Australia/Sydney');
		if (!('params' in r)) throw new Error('expected params');
		expect(r.params.get('tz')).toBe('Australia/Sydney');
		expect(r.params.get('from')).toBe('2024-12-16T06:00:00.000Z');
		expect(r.params.get('to')).toBe('2025-01-15T06:00:00.000Z');
	});

	it('sets all=1 for the all window on query', () => {
		const s = parseUrlState(new URLSearchParams('range=all'));
		const win = resolveWindow(s, NOW, 'UTC', 'query');
		const r = apiParams(s, win, {}, 'UTC');
		if (!('params' in r)) throw new Error('expected params');
		expect(r.params.get('all')).toBe('1');
		expect(r.params.has('from')).toBe(false);
	});

	it('turns an exclude into the facet complement', () => {
		const s = parseUrlState(new URLSearchParams('x.harness=b&range=30d'));
		const win = resolveWindow(s, NOW, 'UTC', 'query');
		const r = apiParams(s, win, { harness: ['a', 'b', 'c'] }, 'UTC');
		if (!('params' in r)) throw new Error('expected params');
		expect(r.params.getAll('harness')).toEqual(['a', 'c']);
	});

	it('is pending when an exclude needs facets', () => {
		const s = parseUrlState(new URLSearchParams('x.harness=b'));
		const win = resolveWindow(s, NOW, 'UTC', 'query');
		expect(apiParams(s, win, null, 'UTC')).toEqual({ pending: true });
	});

	it('is empty when everything is excluded', () => {
		const s = parseUrlState(new URLSearchParams('x.harness=a&x.harness=b'));
		const win = resolveWindow(s, NOW, 'UTC', 'query');
		expect(apiParams(s, win, { harness: ['a', 'b'] }, 'UTC')).toEqual({ empty: true });
	});

	it('subtracts excluded values from the include list', () => {
		const s = parseUrlState(new URLSearchParams('harness=a&harness=b&x.harness=b'));
		const win = resolveWindow(s, NOW, 'UTC', 'query');
		const r = apiParams(s, win, null, 'UTC');
		if (!('params' in r)) throw new Error('expected params');
		expect(r.params.getAll('harness')).toEqual(['a']);
	});

	it('ignores conversation_id excludes but keeps the includes', () => {
		const s = parseUrlState(new URLSearchParams('conversation_id=c1&x.conversation_id=c2'));
		const win = resolveWindow(s, NOW, 'UTC', 'query');
		const r = apiParams(s, win, null, 'UTC');
		if (!('params' in r)) throw new Error('expected params');
		expect(r.params.getAll('conversation_id')).toEqual(['c1']);
	});
});

describe('scoresParams', () => {
	it('leaves exactly one kind', () => {
		const p = new URLSearchParams('kind=design&kind=report&tz=UTC');
		const out = scoresParams(p, 'brief');
		expect(out.getAll('kind')).toEqual(['brief']);
		expect(out.get('tz')).toBe('UTC');
		expect(p.getAll('kind')).toEqual(['design', 'report']);
	});
});
