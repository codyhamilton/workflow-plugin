/** Display text for a dimension key: the API's empty string means "missing". */
export function label(key: string | null | undefined): string {
	return key === '' || key == null ? '(none)' : key;
}

/** Whole numbers with thousands separators for tiles and tables. */
export function num(n: number): string {
	return String(n);
}

/** The dollar text for a known, positive cost: four decimals below one cent, else two. */
function money(cost: number): string {
	return cost < 0.01 ? `$${cost.toFixed(4)}` : `$${cost.toFixed(2)}`;
}

/** Cost text that never shows $0.00 for the part that cannot be priced. */
export function costLabel({ cost, unpriced, calls }: { cost: number; unpriced: number; calls?: number }): string {
	if (calls !== undefined) {
		if (calls === 0) return '—';
		if (unpriced >= calls) return 'unpriced'; // every call is unpriced
		if (unpriced > 0)
			// Some calls are unpriced: the priced cost is not a price for the whole group.
			return cost > 0 ? `${money(cost)}, ${unpriced} unpriced` : `${unpriced} unpriced`;
		return cost > 0 ? money(cost) : '$0.00';
	}
	// calls unknown: only the unpriced count can say "unpriced"; a zero cost with no unpriced calls is $0.00.
	if (unpriced > 0) return cost > 0 ? `${money(cost)}, ${unpriced} unpriced` : 'unpriced';
	return cost > 0 ? money(cost) : '$0.00';
}
