// Reads the CSS custom properties in theme.css (light on :root, dark under the
// prefers-color-scheme media query) so no chart hard-codes a colour.
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

/** The light values from theme.css; used when a variable is empty and in tests. */
export const DEFAULT_TOKENS: Tokens = {
	bg: '#ffffff',
	surface: '#f5f5f5',
	text: '#1a1a1a',
	muted: '#6b7280',
	border: '#d1d5db',
	accent: '#2563eb',
	danger: '#dc2626',
	series: ['#2563eb', '#d97706', '#059669', '#db2777', '#7c3aed', '#0891b2', '#ca8a04', '#4b5563']
};

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

/** Calls `cb` whenever the system colour scheme changes; returns an unsubscribe. */
export function watchScheme(cb: () => void): () => void {
	if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return () => {};
	const mq = window.matchMedia('(prefers-color-scheme: dark)');
	const handler = () => cb();
	mq.addEventListener('change', handler);
	return () => mq.removeEventListener('change', handler);
}
