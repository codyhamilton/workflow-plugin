import { describe, expect, it } from 'vitest';
import { fillBuckets } from './series';

describe('fillBuckets', () => {
	it('fills missing days with 0 across all series', () => {
		const out = fillBuckets(
			[
				{ key: 'a', points: [{ t: '2026-10-01', n: 2 }, { t: '2026-10-04', n: 1 }] },
				{ key: 'b', points: [{ t: '2026-10-02', n: 3 }] }
			],
			'day'
		);
		expect(out[0].points).toEqual([
			{ t: '2026-10-01', n: 2 },
			{ t: '2026-10-02', n: 0 },
			{ t: '2026-10-03', n: 0 },
			{ t: '2026-10-04', n: 1 }
		]);
		expect(out[1].points.map((p) => p.n)).toEqual([0, 3, 0, 0]);
	});

	it('steps weeks from Monday to Monday', () => {
		const out = fillBuckets([{ key: 'all', points: [{ t: '2026-09-14', n: 1 }, { t: '2026-09-28', n: 4 }] }], 'week');
		expect(out[0].points).toEqual([
			{ t: '2026-09-14', n: 1 },
			{ t: '2026-09-21', n: 0 },
			{ t: '2026-09-28', n: 4 }
		]);
	});

	it('leaves an empty response alone', () => {
		expect(fillBuckets([{ key: 'all', points: [] }], 'day')).toEqual([{ key: 'all', points: [] }]);
	});
});
