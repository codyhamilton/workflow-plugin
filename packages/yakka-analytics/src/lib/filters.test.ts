import { describe, expect, it } from 'vitest';
import { filterParams, mergeQuery, parseFilter } from './filters';

describe('filters', () => {
	it('round-trips repeated params', () => {
		const q = new URLSearchParams(
			'from=2026-01-01T00:00:00Z&to=2026-01-31T23:59:59Z&repo_id=r1&repo_id=r2&harness=claude&kind=design&kind=brief&plan=01-x'
		);
		const f = parseFilter(q);
		expect(f).toEqual({
			from: '2026-01-01T00:00:00Z',
			to: '2026-01-31T23:59:59Z',
			repo_id: ['r1', 'r2'],
			harness: ['claude'],
			kind: ['design', 'brief'],
			plan: ['01-x']
		});
		const out = filterParams(f);
		expect(parseFilter(out)).toEqual(f);
		expect(out.getAll('repo_id')).toEqual(['r1', 'r2']);
	});

	it('drops unknown kind values and omits empty window', () => {
		const f = parseFilter(new URLSearchParams('kind=plan&kind=report'));
		expect(f.kind).toEqual(['report']);
		expect(f.from).toBeUndefined();
		expect(filterParams(f).toString()).toBe('kind=report');
	});

	it('preserves route params when the filter changes', () => {
		const cur = new URLSearchParams('metric=commits&repo_id=r1&group=harness');
		const next = mergeQuery(cur, { ...parseFilter(cur), repo_id: ['r2'], harness: ['cursor'] });
		expect(next.get('metric')).toBe('commits');
		expect(next.get('group')).toBe('harness');
		expect(next.getAll('repo_id')).toEqual(['r2']);
		expect(next.getAll('harness')).toEqual(['cursor']);
	});
});
