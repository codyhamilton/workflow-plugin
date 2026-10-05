import { readFileSync } from 'node:fs';
import type { Page } from '@playwright/test';

export interface ServeState {
	local: string; // base URL of the local-mode serve (no auth)
	keyed: string; // base URL of the keyed serve (cross-origin from the preview, bearer required)
	key: string;
}

export function serveState(): ServeState {
	return JSON.parse(readFileSync(process.env.E2E_STATE!, 'utf8'));
}

/** Point the site at one of the e2e serves before any page script runs. */
export async function useServe(page: Page, which: 'local' | 'keyed') {
	const s = serveState();
	const base = which === 'local' ? s.local : s.keyed;
	const key = which === 'keyed' ? s.key : null;
	await page.addInitScript(
		([b, k]) => {
			localStorage.setItem('workflow-analytics-base', b as string);
			if (k) localStorage.setItem('workflow-analytics-key', k as string);
		},
		[base, key]
	);
}
