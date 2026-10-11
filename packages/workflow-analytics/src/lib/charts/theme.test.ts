import { afterEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_TOKENS, readTokens, scheme, watchScheme } from './theme';

afterEach(() => vi.unstubAllGlobals());

describe('readTokens', () => {
	it('falls back to defaults when a variable is empty', () => {
		vi.stubGlobal('getComputedStyle', () => ({
			getPropertyValue: (name: string) => (name === '--bg' ? '' : '#123456')
		}));
		const t = readTokens({} as Element);
		expect(t.bg).toBe(DEFAULT_TOKENS.bg);
		expect(t.text).toBe('#123456');
		expect(t.series).toHaveLength(8);
	});

	it('reads every series token in order', () => {
		vi.stubGlobal('getComputedStyle', () => ({
			getPropertyValue: (name: string) => `varval:${name}`
		}));
		const t = readTokens({} as Element);
		expect(t.series[0]).toBe('varval:--series-1');
		expect(t.series[7]).toBe('varval:--series-8');
	});
});

describe('scheme', () => {
	afterEach(() => vi.unstubAllGlobals());

	it('reads the system preference', () => {
		vi.stubGlobal('window', { matchMedia: (q: string) => ({ matches: q.includes('dark') }) });
		expect(scheme()).toBe('dark');
	});

	it('defaults to light without a window', () => {
		expect(scheme()).toBe('light');
	});
});

describe('watchScheme', () => {
	it('subscribes to the media query and returns an unsubscribe', () => {
		const add = vi.fn();
		const remove = vi.fn();
		vi.stubGlobal('window', {
			matchMedia: () => ({ matches: false, addEventListener: add, removeEventListener: remove })
		});
		const off = watchScheme(() => {});
		expect(add).toHaveBeenCalledTimes(1);
		off();
		expect(remove).toHaveBeenCalledTimes(1);
	});

	it('is a no-op without a window', () => {
		const off = watchScheme(() => {});
		expect(typeof off).toBe('function');
		off();
	});
});
