import { describe, expect, it } from 'vitest';
import { PRESETS, presetWindow, type PresetId } from './presets';

function window(id: PresetId, now: string, tz: string): { from: string; to: string } {
	const w = presetWindow(id, new Date(now), tz);
	if (w === null) throw new Error('expected a window');
	return { from: w.from.toISOString(), to: w.to.toISOString() };
}

describe('PRESETS', () => {
	it('lists the presets in order with labels', () => {
		expect(PRESETS.map((p) => p.id)).toEqual(['today', '24h', '7d', '30d', '90d', 'month', 'ytd', 'all']);
		expect(PRESETS.map((p) => p.label)).toEqual([
			'Today',
			'24h',
			'7d',
			'30d',
			'90d',
			'This month',
			'YTD',
			'All time'
		]);
	});
});

describe('presetWindow', () => {
	it('all has no window', () => {
		expect(presetWindow('all', new Date('2025-01-15T05:30:00Z'), 'UTC')).toBeNull();
	});

	it('rounds to the next full hour and subtracts the span', () => {
		const now = new Date('2025-01-15T05:30:00Z');
		const to = new Date('2025-01-15T06:00:00Z').getTime();
		const spans: [PresetId, number][] = [
			['24h', 86400000],
			['7d', 7 * 86400000],
			['30d', 30 * 86400000],
			['90d', 90 * 86400000]
		];
		for (const [id, ms] of spans) {
			const w = presetWindow(id, now, 'UTC');
			if (w === null) throw new Error('expected a window');
			expect(w.to.getTime()).toBe(to);
			expect(w.from.getTime()).toBe(to - ms);
		}
	});

	it('Sydney today/month/ytd across a DST date', () => {
		const now = new Date('2025-01-15T05:30:00Z');
		expect(window('today', now.toISOString(), 'Australia/Sydney')).toEqual({
			from: '2025-01-14T13:00:00.000Z',
			to: '2025-01-15T06:00:00.000Z'
		});
		expect(window('month', now.toISOString(), 'Australia/Sydney').from).toBe('2024-12-31T13:00:00.000Z');
		expect(window('ytd', now.toISOString(), 'Australia/Sydney').from).toBe('2024-12-31T13:00:00.000Z');
	});

	it('Sydney DST-end today/month/ytd', () => {
		const now = new Date('2025-04-06T05:30:00Z');
		expect(window('today', now.toISOString(), 'Australia/Sydney').from).toBe('2025-04-05T13:00:00.000Z');
		expect(window('month', now.toISOString(), 'Australia/Sydney').from).toBe('2025-03-31T13:00:00.000Z');
		expect(window('ytd', now.toISOString(), 'Australia/Sydney').from).toBe('2024-12-31T13:00:00.000Z');
	});

	it('New York DST-start today/month/ytd', () => {
		const now = new Date('2025-03-09T05:30:00Z');
		expect(window('today', now.toISOString(), 'America/New_York')).toEqual({
			from: '2025-03-09T05:00:00.000Z',
			to: '2025-03-09T06:00:00.000Z'
		});
		expect(window('month', now.toISOString(), 'America/New_York').from).toBe('2025-03-01T05:00:00.000Z');
		expect(window('ytd', now.toISOString(), 'America/New_York').from).toBe('2025-01-01T05:00:00.000Z');
	});

	it('New York today/month/ytd in winter', () => {
		const now = new Date('2025-01-15T05:30:00Z');
		expect(window('today', now.toISOString(), 'America/New_York')).toEqual({
			from: '2025-01-15T05:00:00.000Z',
			to: '2025-01-15T06:00:00.000Z'
		});
		expect(window('month', now.toISOString(), 'America/New_York').from).toBe('2025-01-01T05:00:00.000Z');
		expect(window('ytd', now.toISOString(), 'America/New_York').from).toBe('2025-01-01T05:00:00.000Z');
	});
});
