import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { apiGet } from './api';
import { Superseded, createClient, normalise } from './query';

let store: Record<string, string>;

beforeEach(() => {
	store = {};
	vi.stubGlobal('localStorage', {
		getItem: (k: string) => (k in store ? store[k] : null),
		setItem: (k: string, v: string) => void (store[k] = v)
	});
	vi.useFakeTimers();
});

afterEach(() => {
	vi.useRealTimers();
	vi.unstubAllGlobals();
});

type Fetch = typeof apiGet;

describe('normalise', () => {
	it('sorts by key then value and drops empty values', () => {
		const a = normalise('analytics/query', new URLSearchParams('b=2&a=1&z=&a=0'));
		const b = normalise('analytics/query', new URLSearchParams('a=0&b=2&a=1'));
		expect(a).toBe(b);
		expect(a).toBe('/v1/analytics/query?a=0&a=1&b=2');
	});

	it('uses the stored base and strips leading slashes from the path', () => {
		store['workflow-analytics-base'] = 'https://api.example.com/';
		expect(normalise('/analytics/query', new URLSearchParams('a=1'))).toBe(
			'https://api.example.com/v1/analytics/query?a=1'
		);
	});
});

describe('createClient.get', () => {
	it('a burst of five calls on one slot fires once with the last params and supersedes the rest', async () => {
		const fetcher = vi.fn(() => Promise.resolve({ ok: true }));
		const c = createClient({ debounceMs: 250, fetcher: fetcher as unknown as Fetch });
		const ps = [1, 2, 3, 4, 5].map((i) =>
			c.get<{ ok: boolean }>('slot', 'analytics/summary', new URLSearchParams(`a=${i}`))
		);
		const superseded = ps.slice(0, 4).map((p) => p.catch((e) => e));
		await vi.advanceTimersByTimeAsync(250);
		await expect(ps[4]).resolves.toEqual({ ok: true });
		expect(fetcher).toHaveBeenCalledTimes(1);
		expect((fetcher.mock.calls[0][1] as URLSearchParams).get('a')).toBe('5');
		for (const e of await Promise.all(superseded)) expect(e).toBeInstanceOf(Superseded);
	});

	it('aborts the in-flight fetch signal when the slot is superseded mid-flight', async () => {
		let signal: AbortSignal | undefined;
		const fetcher = vi.fn((_path: string, _p?: URLSearchParams | string, s?: AbortSignal) => {
			signal = s;
			return new Promise<never>(() => {});
		});
		const c = createClient({ debounceMs: 250, fetcher: fetcher as unknown as Fetch });
		const first = c.get('slot', 'analytics/summary', new URLSearchParams('a=1'));
		const firstErr = first.catch((e) => e);
		await vi.advanceTimersByTimeAsync(250);
		expect(fetcher).toHaveBeenCalledTimes(1);
		expect(signal?.aborted).toBe(false);

		const second = c.get('slot', 'analytics/summary', new URLSearchParams('a=2'));
		second.catch(() => {});
		expect(signal?.aborted).toBe(true);
		expect(await firstErr).toBeInstanceOf(Superseded);

		await vi.advanceTimersByTimeAsync(250);
		expect(fetcher).toHaveBeenCalledTimes(2);
	});

	it('serves a repeated identical call from cache without another fetch', async () => {
		const fetcher = vi.fn(() => Promise.resolve({ v: 1 }));
		const c = createClient({ debounceMs: 250, fetcher: fetcher as unknown as Fetch });
		const first = c.get('slot', 'analytics/summary', new URLSearchParams('a=1'));
		await vi.advanceTimersByTimeAsync(250);
		await expect(first).resolves.toEqual({ v: 1 });

		const second = c.get('slot', 'analytics/summary', new URLSearchParams('a=1'));
		await expect(second).resolves.toEqual({ v: 1 });
		expect(fetcher).toHaveBeenCalledTimes(1);
	});

	it('shares one fetch between two slots with the same normalised key', async () => {
		let release!: (v: unknown) => void;
		const fetcher = vi.fn(
			() =>
				new Promise<unknown>((res) => {
					release = res;
				})
		);
		const c = createClient({ debounceMs: 250, fetcher: fetcher as unknown as Fetch });
		const a = c.get('slotA', 'analytics/summary', new URLSearchParams('a=1'));
		const b = c.get('slotB', 'analytics/summary', new URLSearchParams('a=1'));
		await vi.advanceTimersByTimeAsync(250);
		expect(fetcher).toHaveBeenCalledTimes(1);
		release({ v: 42 });
		await expect(a).resolves.toEqual({ v: 42 });
		await expect(b).resolves.toEqual({ v: 42 });
		expect(fetcher).toHaveBeenCalledTimes(1);
	});

	it('never runs more than maxConcurrent fetches at once', async () => {
		let active = 0;
		let peak = 0;
		const pending: Array<() => void> = [];
		const fetcher = vi.fn(() => {
			active++;
			peak = Math.max(peak, active);
			return new Promise<unknown>((res) => {
				pending.push(() => {
					active--;
					res({});
				});
			});
		});
		const c = createClient({ debounceMs: 0, maxConcurrent: 2, fetcher: fetcher as unknown as Fetch });
		const ps = [1, 2, 3, 4, 5].map((i) =>
			c.get('slot' + i, 'analytics/summary', new URLSearchParams(`a=${i}`))
		);
		await vi.advanceTimersByTimeAsync(0);
		expect(fetcher).toHaveBeenCalledTimes(2);
		expect(peak).toBe(2);

		while (pending.length) {
			pending.shift()!();
			await vi.advanceTimersByTimeAsync(0);
		}
		await Promise.all(ps);
		expect(fetcher).toHaveBeenCalledTimes(5);
		expect(peak).toBe(2);
	});

	it('defaults to four concurrent fetches', async () => {
		let active = 0;
		let peak = 0;
		const pending: Array<() => void> = [];
		const fetcher = vi.fn(() => {
			active++;
			peak = Math.max(peak, active);
			return new Promise<unknown>((res) => {
				pending.push(() => {
					active--;
					res({});
				});
			});
		});
		const c = createClient({ debounceMs: 0, fetcher: fetcher as unknown as Fetch });
		const ps = [1, 2, 3, 4, 5, 6, 7, 8].map((i) =>
			c.get('slot' + i, 'analytics/summary', new URLSearchParams(`a=${i}`))
		);
		await vi.advanceTimersByTimeAsync(0);
		expect(fetcher).toHaveBeenCalledTimes(4);
		expect(peak).toBe(4);
		while (pending.length) {
			pending.shift()!();
			await vi.advanceTimersByTimeAsync(0);
		}
		await Promise.all(ps);
		expect(fetcher).toHaveBeenCalledTimes(8);
		expect(peak).toBe(4);
	});

	it('does not cache an error', async () => {
		let fail = true;
		const fetcher = vi.fn(() => (fail ? Promise.reject(new Error('boom')) : Promise.resolve({ v: 1 })));
		const c = createClient({ debounceMs: 250, fetcher: fetcher as unknown as Fetch });
		const firstErr = c.get('slot', 'analytics/summary', new URLSearchParams('a=1')).catch((e) => e);
		await vi.advanceTimersByTimeAsync(250);
		const err = await firstErr;
		expect(err).toBeInstanceOf(Error);
		expect((err as Error).message).toBe('boom');

		fail = false;
		const second = c.get('slot', 'analytics/summary', new URLSearchParams('a=1'));
		await vi.advanceTimersByTimeAsync(250);
		await expect(second).resolves.toEqual({ v: 1 });
		expect(fetcher).toHaveBeenCalledTimes(2);
	});
});
