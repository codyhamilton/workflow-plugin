// A small categorical palette as CSS variables with fallbacks; no colour library.
const COLORS = [
	'var(--chart-1, #2563eb)',
	'var(--chart-2, #d97706)',
	'var(--chart-3, #059669)',
	'var(--chart-4, #db2777)',
	'var(--chart-5, #7c3aed)',
	'var(--chart-6, #0891b2)'
];
export const color = (i: number) => COLORS[i % COLORS.length];
