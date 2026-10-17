import { describe, expect, it } from 'vitest';
import { costLabel, label, num } from './format';

describe('costLabel', () => {
	it('reports all unpriced calls as unpriced', () => {
		const got = costLabel({ cost: 0, unpriced: 5, calls: 5 });
		expect(got).toBe('unpriced');
		expect(got).not.toBe('$0.00');
	});

	it('reports a mixed cost with the unpriced count', () => {
		const got = costLabel({ cost: 1.5, unpriced: 3, calls: 10 });
		expect(got).toBe('$1.50, 3 unpriced');
		expect(got).not.toBe('$0.00');
	});

	it('reports a fully priced cost', () => {
		expect(costLabel({ cost: 2, unpriced: 0, calls: 10 })).toBe('$2.00');
	});

	it('reports no calls as a dash', () => {
		expect(costLabel({ cost: 0, unpriced: 0, calls: 0 })).toBe('—');
	});

	it('uses four decimals below one cent', () => {
		expect(costLabel({ cost: 0.005, unpriced: 0, calls: 1 })).toBe('$0.0050');
	});

	it('is unpriced when calls are unknown and cost is zero', () => {
		const got = costLabel({ cost: 0, unpriced: 2 });
		expect(got).toBe('unpriced');
		expect(got).not.toBe('$0.00');
	});
});

describe('costLabel truth table', () => {
	const cases: Array<{ calls?: number; unpriced: number; cost: number; want: string; why: string }> = [
		// calls unknown: only the count can say "unpriced"; a zero cost with no unpriced calls is $0.00.
		{ calls: undefined, unpriced: 0, cost: 0, want: '$0.00', why: 'no calls, no unpriced, no cost' },
		{ calls: undefined, unpriced: 0, cost: 2, want: '$2.00', why: 'no calls, no unpriced, priced' },
		{ calls: undefined, unpriced: 3, cost: 0, want: 'unpriced', why: 'unknown calls, unpriced, no cost' },
		{ calls: undefined, unpriced: 3, cost: 1.5, want: '$1.50, 3 unpriced', why: 'unknown calls, priced plus unpriced' },
		// calls zero: a dash, never $0.00 and never unpriced.
		{ calls: 0, unpriced: 0, cost: 0, want: '—', why: 'no calls' },
		{ calls: 0, unpriced: 0, cost: 2, want: '—', why: 'no calls despite a cost' },
		// every call unpriced: unpriced, whatever the cost column holds.
		{ calls: 5, unpriced: 5, cost: 0, want: 'unpriced', why: 'all unpriced, no cost' },
		{ calls: 5, unpriced: 5, cost: 2, want: 'unpriced', why: 'all unpriced despite a cost' },
		// some unpriced, no priced cost: the count, never $0.00.
		{ calls: 10, unpriced: 3, cost: 0, want: '3 unpriced', why: 'some unpriced, priced cost zero' },
		// some unpriced with a priced cost.
		{ calls: 10, unpriced: 3, cost: 0.005, want: '$0.0050, 3 unpriced', why: 'some unpriced, sub-cent cost' },
		{ calls: 10, unpriced: 3, cost: 1.5, want: '$1.50, 3 unpriced', why: 'some unpriced, priced cost' },
		// no unpriced calls: the cost, or $0.00 when the cost is zero.
		{ calls: 10, unpriced: 0, cost: 0, want: '$0.00', why: 'none unpriced, no cost' },
		{ calls: 10, unpriced: 0, cost: 0.005, want: '$0.0050', why: 'none unpriced, sub-cent cost' },
		{ calls: 10, unpriced: 0, cost: 2, want: '$2.00', why: 'none unpriced, priced' }
	];

	for (const c of cases) {
		it(`${c.why}`, () => {
			expect(costLabel({ cost: c.cost, unpriced: c.unpriced, calls: c.calls })).toBe(c.want);
		});
	}

	it('never prints $0.00 beside unpriced calls', () => {
		for (const c of cases) {
			if (c.unpriced > 0 && (c.calls === undefined || c.unpriced < c.calls)) {
				const got = costLabel({ cost: c.cost, unpriced: c.unpriced, calls: c.calls });
				if (c.cost === 0) expect(got).not.toContain('$0.00');
			}
		}
	});
});

describe('label and num are unchanged', () => {
	it('label names the missing key', () => {
		expect(label(null)).toBe('(none)');
		expect(label('')).toBe('(none)');
		expect(label('x')).toBe('x');
	});

	it('num stringifies', () => {
		expect(num(42)).toBe('42');
	});
});
