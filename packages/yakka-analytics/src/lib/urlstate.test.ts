import { describe, expect, it } from 'vitest';
import { applyDrill, chips, DIM_KEYS, parseUrlState, removeChip, toSearch, type UrlState } from './urlstate';

describe('parseUrlState', () => {
	it('defaults to 30d with empty include/exclude', () => {
		expect(parseUrlState(new URLSearchParams(''))).toEqual({ range: '30d', include: {}, exclude: {} });
	});

	it('reads a preset range', () => {
		expect(parseUrlState(new URLSearchParams('range=7d')).range).toBe('7d');
	});

	it('treats from/to without range as custom', () => {
		const s = parseUrlState(new URLSearchParams('from=2025-01-01T00:00:00Z&to=2025-01-02T00:00:00Z'));
		expect(s.range).toBe('custom');
		expect(s.from).toBe('2025-01-01T00:00:00Z');
		expect(s.to).toBe('2025-01-02T00:00:00Z');
	});

	it('falls back to 30d for an unknown range', () => {
		expect(parseUrlState(new URLSearchParams('range=bogus')).range).toBe('30d');
	});

	it('parses includes and excludes and drops unknown kind values', () => {
		const q = new URLSearchParams('harness=claude&harness=cursor&x.harness=codex&kind=design&kind=bogus&x.kind=report');
		const s = parseUrlState(q);
		expect(s.include.harness).toEqual(['claude', 'cursor']);
		expect(s.exclude.harness).toEqual(['codex']);
		expect(s.include.kind).toEqual(['design']);
		expect(s.exclude.kind).toEqual(['report']);
	});

	it('exposes the dimension keys in order', () => {
		expect(DIM_KEYS).toEqual([
			'repo_id',
			'harness',
			'kind',
			'plan',
			'norm_event',
			'event',
			'tool',
			'model',
			'source',
			'conversation_id'
		]);
	});
});

describe('toSearch round-trips', () => {
	it('round-trips includes, excludes and a custom range', () => {
		const s: UrlState = {
			range: 'custom',
			from: '2025-01-01T00:00:00Z',
			to: '2025-02-01T00:00:00Z',
			include: { harness: ['claude'], kind: ['design'] },
			exclude: { model: ['gpt-4o'] }
		};
		expect(parseUrlState(toSearch(s))).toEqual(s);
	});

	it('round-trips a preset with includes', () => {
		const s: UrlState = { range: '7d', include: { harness: ['claude'] }, exclude: {} };
		expect(parseUrlState(toSearch(s))).toEqual(s);
	});

	it('carries route params that are not filter params', () => {
		const keep = new URLSearchParams('metric=commits&group=harness&range=1d&harness=claude&x.model=old&page=2');
		const out = toSearch(parseUrlState(new URLSearchParams('range=7d')), keep);
		expect(out.get('metric')).toBe('commits');
		expect(out.get('group')).toBe('harness');
		expect(out.get('page')).toBe('2');
		expect(out.get('range')).toBe('7d');
		expect(out.has('harness')).toBe(false);
		expect(out.has('x.model')).toBe(false);
	});
});

describe('applyDrill', () => {
	it('ignores __other__ and returns the same reference', () => {
		const s = parseUrlState(new URLSearchParams(''));
		expect(applyDrill(s, 'harness', '__other__', false)).toBe(s);
	});

	it('ignores the empty key and returns the same reference', () => {
		const s = parseUrlState(new URLSearchParams(''));
		expect(applyDrill(s, 'model', '', false)).toBe(s);
		expect(applyDrill(s, 'model', '', true)).toBe(s);
	});

	it('moves a value between include and exclude', () => {
		const s = parseUrlState(new URLSearchParams('harness=claude&x.harness=cursor'));
		const inc = applyDrill(s, 'harness', 'cursor', false);
		expect(inc.include.harness).toEqual(['claude', 'cursor']);
		expect(inc.exclude.harness).toBeUndefined();
		const ex = applyDrill(inc, 'harness', 'claude', true);
		expect(ex.include.harness).toEqual(['cursor']);
		expect(ex.exclude.harness).toEqual(['claude']);
	});
});

describe('removeChip', () => {
	it('removes the value from both sides', () => {
		const s = parseUrlState(new URLSearchParams('harness=claude&x.harness=cursor'));
		const out = removeChip(s, 'harness', 'claude');
		expect(out.include.harness).toBeUndefined();
		expect(out.exclude.harness).toEqual(['cursor']);
	});
});

describe('chips', () => {
	it('lists includes before excludes in dimension order', () => {
		const s = parseUrlState(new URLSearchParams('harness=claude&x.model=gpt'));
		expect(chips(s)).toEqual([
			{ key: 'harness', value: 'claude', mode: 'include' },
			{ key: 'model', value: 'gpt', mode: 'exclude' }
		]);
	});
});
