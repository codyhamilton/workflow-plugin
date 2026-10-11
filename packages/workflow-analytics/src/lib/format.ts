/** Display text for a dimension key: the API's empty string means "missing". */
export function label(key: string | null | undefined): string {
	return key === '' || key == null ? '(none)' : key;
}

/** Whole numbers with thousands separators for tiles and tables. */
export function num(n: number): string {
	return String(n);
}

/** Cost text that never shows $0.00 while calls are unpriced. */
export function costLabel({ cost, unpriced, calls }: { cost: number; unpriced: number; calls?: number }): string {
	if (
		(calls !== undefined && calls > 0 && unpriced >= calls) ||
		(calls === undefined && unpriced > 0 && cost === 0)
	)
		return 'unpriced';
	if (cost > 0) {
		const s = cost < 0.01 ? `$${cost.toFixed(4)}` : `$${cost.toFixed(2)}`;
		return unpriced > 0 ? `${s}, ${unpriced} unpriced` : s;
	}
	if (calls === 0) return '—';
	return '$0.00';
}
