/** Analysis frame colour tokens (`src/lib/analysis/tokens.css`). Not solarized. */
export interface AnalysisTokens {
	bg: string;
	surface: string;
	text: string;
	muted: string;
	border: string;
	accent: string;
	danger: string;
	series: string[];
}

/** Light-theme defaults from `tokens.css` (used when CSS variables are empty). */
export const ANALYSIS_DEFAULT_TOKENS: AnalysisTokens = {
	bg: '#f4f6fa',
	surface: '#ffffff',
	text: '#1a2332',
	muted: '#5c6b82',
	border: '#d5dce8',
	accent: '#4f5fd6',
	danger: '#c62828',
	series: [
		'#5b6ee1',
		'#2d9f6f',
		'#c27803',
		'#d14e6d',
		'#8b5cf6',
		'#0d9488',
		'#ea580c',
		'#65a30d'
	]
};

const SIMPLE: [keyof Omit<AnalysisTokens, 'series'>, string][] = [
	['bg', '--bg'],
	['surface', '--surface'],
	['text', '--text'],
	['muted', '--muted'],
	['border', '--border'],
	['accent', '--accent'],
	['danger', '--danger']
];

const SERIES_VARS = ANALYSIS_DEFAULT_TOKENS.series.map((_, i) => `--series-${i + 1}`);

/** Reads analysis tokens from computed styles on `el` (typically the chart host). */
export function readAnalysisTokens(el: Element | null | undefined): AnalysisTokens {
	const cs =
		el && typeof globalThis.getComputedStyle === 'function' ? globalThis.getComputedStyle(el) : null;
	const read = (name: string, fallback: string) => {
		const v = cs ? cs.getPropertyValue(name).trim() : '';
		return v || fallback;
	};
	const out = {} as AnalysisTokens;
	for (const [key, name] of SIMPLE) out[key] = read(name, ANALYSIS_DEFAULT_TOKENS[key]);
	out.series = SERIES_VARS.map((name, i) => read(name, ANALYSIS_DEFAULT_TOKENS.series[i]));
	return out;
}

export function seriesColor(t: AnalysisTokens, i: number): string {
	return t.series[i % t.series.length];
}
