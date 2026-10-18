// Reads the CSS custom properties in theme.css (`data-theme` on the document root)
// so no chart hard-codes a colour.
export interface Tokens {
	bg: string;
	surface: string;
	text: string;
	muted: string;
	border: string;
	accent: string;
	danger: string;
	series: string[];
}

const LIGHT_SERIES = [
	'#268bd2',
	'#859900',
	'#b58900',
	'#cb4b16',
	'#dc322f',
	'#d33682',
	'#6c71c4',
	'#2aa198'
];

/** The light values from theme.css; used when a variable is empty and in tests. */
export const DEFAULT_TOKENS: Tokens = {
	bg: '#fdf6e3',
	surface: '#eee8d5',
	text: '#657b83',
	muted: '#586e75',
	border: '#93a1a1',
	accent: '#268bd2',
	danger: '#dc322f',
	series: LIGHT_SERIES
};

export const THEME_KEY = 'yakka-analytics-theme';

export type ThemePreference = 'system' | 'light' | 'dark';

const SIMPLE: [keyof Omit<Tokens, 'series'>, string][] = [
	['bg', '--bg'],
	['surface', '--surface'],
	['text', '--text'],
	['muted', '--muted'],
	['border', '--border'],
	['accent', '--accent'],
	['danger', '--danger']
];

const SERIES_VARS = DEFAULT_TOKENS.series.map((_, i) => `--series-${i + 1}`);

/** Reads the live token values for `el`, falling back to the light defaults. */
export function readTokens(el: Element | null | undefined): Tokens {
	const cs =
		el && typeof globalThis.getComputedStyle === 'function' ? globalThis.getComputedStyle(el) : null;
	const read = (name: string, fallback: string) => {
		const v = cs ? cs.getPropertyValue(name).trim() : '';
		return v || fallback;
	};
	const out = {} as Tokens;
	for (const [key, name] of SIMPLE) out[key] = read(name, DEFAULT_TOKENS[key]);
	out.series = SERIES_VARS.map((name, i) => read(name, DEFAULT_TOKENS.series[i]));
	return out;
}

/** The current system colour scheme. */
export function scheme(): 'light' | 'dark' {
	if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return 'light';
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function getThemePreference(): ThemePreference {
	if (typeof localStorage === 'undefined') return 'system';
	try {
		const v = localStorage.getItem(THEME_KEY);
		if (v === 'light' || v === 'dark' || v === 'system') return v;
	} catch {
		/* private mode */
	}
	return 'system';
}

function resolvedTheme(pref: ThemePreference): 'light' | 'dark' {
	if (pref === 'light') return 'light';
	if (pref === 'dark') return 'dark';
	return scheme();
}

/** Sets `data-theme` from a preference (defaults to the stored value). */
export function applyTheme(pref?: ThemePreference): void {
	if (typeof document === 'undefined') return;
	document.documentElement.dataset.theme = resolvedTheme(pref ?? getThemePreference());
}

/** Writes the preference and updates `data-theme`. */
export function setThemePreference(pref: ThemePreference): void {
	try {
		localStorage.setItem(THEME_KEY, pref);
	} catch {
		/* private mode */
	}
	applyTheme(pref);
}

/** Applies the stored theme and follows OS changes while preference is `system`. */
export function initTheme(): () => void {
	applyTheme();
	const mq = window.matchMedia('(prefers-color-scheme: dark)');
	const handler = () => {
		if (getThemePreference() === 'system') applyTheme('system');
	};
	mq.addEventListener('change', handler);
	return () => mq.removeEventListener('change', handler);
}

/** Calls `cb` when the system scheme or `data-theme` changes; returns an unsubscribe. */
export function watchScheme(cb: () => void): () => void {
	if (typeof window === 'undefined') return () => {};
	const cleanups: (() => void)[] = [];
	if (typeof window.matchMedia === 'function') {
		const mq = window.matchMedia('(prefers-color-scheme: dark)');
		const handler = () => cb();
		mq.addEventListener('change', handler);
		cleanups.push(() => mq.removeEventListener('change', handler));
	}
	if (typeof MutationObserver === 'function' && typeof document !== 'undefined') {
		const obs = new MutationObserver((records) => {
			if (records.some((r) => r.type === 'attributes' && r.attributeName === 'data-theme')) cb();
		});
		obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
		cleanups.push(() => obs.disconnect());
	}
	return () => {
		for (const off of cleanups) off();
	};
}
