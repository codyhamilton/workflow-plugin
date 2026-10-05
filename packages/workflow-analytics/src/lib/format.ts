/** Display text for a dimension key: the API's empty string means "missing". */
export function label(key: string | null | undefined): string {
	return key === '' || key == null ? '(none)' : key;
}

/** Whole numbers with thousands separators for tiles and tables. */
export function num(n: number): string {
	return String(n);
}
