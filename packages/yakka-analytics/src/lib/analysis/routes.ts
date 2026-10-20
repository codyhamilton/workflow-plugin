/** Report routes that keep solarized tokens on filter chrome and page content until later phases. */
const LEGACY_REPORT_PREFIXES = [
	'/trends',
	'/builder',
	'/usage',
	'/repos',
	'/hooks',
	'/quality',
	'/executions',
	'/conversations',
	'/conversation',
	'/explore',
	'/dashboards'
] as const;

export function isLegacyReportPath(pathname: string): boolean {
	return LEGACY_REPORT_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
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
