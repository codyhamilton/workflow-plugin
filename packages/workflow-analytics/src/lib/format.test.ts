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
