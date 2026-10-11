import { describe, expect, it } from 'vitest';
import { bucketCount, pickBucket } from './buckets';

const d = (s: string): Date => new Date(s);

describe('pickBucket', () => {
	it('picks the finest allowed bucket within the cap', () => {
		expect(pickBucket(d('2025-01-01T00:00:00Z'), d('2025-01-08T00:00:00Z'), 'UTC')).toBe('hour');
		expect(pickBucket(d('2025-01-01T00:00:00Z'), d('2025-04-01T00:00:00Z'), 'UTC')).toBe('day');
		expect(pickBucket(d('2022-01-01T00:00:00Z'), d('2025-01-01T00:00:00Z'), 'UTC')).toBe('week');
		expect(pickBucket(d('1995-01-01T00:00:00Z'), d('2025-01-01T00:00:00Z'), 'UTC')).toBe('month');
	});

	it('returns null when nothing is allowed within the cap', () => {
		expect(pickBucket(d('2025-01-01T00:00:00Z'), d('2025-01-31T00:00:00Z'), 'UTC', ['hour'])).toBeNull();
	});
});

describe('bucketCount', () => {
	it('is an upper bound on the number of buckets', () => {
		const from = d('2025-01-01T00:00:00Z');
		const to = d('2025-01-08T00:00:00Z');
		expect(bucketCount('hour', from, to, 'UTC')).toBeGreaterThanOrEqual(168);
		expect(bucketCount('hour', from, to, 'UTC')).toBeLessThanOrEqual(170);
		expect(bucketCount('day', from, to, 'UTC')).toBe(9);
		expect(pickBucket(from, to, 'UTC')).toBe('hour');
	});
});
