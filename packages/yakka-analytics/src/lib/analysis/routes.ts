/** Report routes retired in phase 5; investigation on `/` replaces them. */
const LEGACY_REPORT_PREFIXES: readonly string[] = [];

export function isLegacyReportPath(_pathname: string): boolean {
	return LEGACY_REPORT_PREFIXES.some((p) => _pathname === p || _pathname.startsWith(`${p}/`));
}

/** Routes that use analysis tokens on the document root (shell + main). */
export function isAnalysisFramePath(pathname: string): boolean {
	if (pathname === '/' || pathname.startsWith('/oauth/')) return true;
	if (
		pathname === '/login' ||
		pathname === '/profile' ||
		pathname === '/settings' ||
		pathname === '/device'
	) {
		return true;
	}
	return !isLegacyReportPath(pathname);
}
