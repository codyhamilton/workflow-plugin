import type { AggregateRequest } from './aggregate';

export const SAVED_ANALYSIS_KEY = 'yakka-analytics-saved-analysis';

const MAX_SAVED = 50;
const MAX_NAME = 120;
const ASK_KINDS = new Set([
	'trend',
	'breakdown',
	'distribution',
	'quality',
	'conversations',
	'conversation',
	'executions'
]);

export interface SavedAnalysis {
	id: string;
	name: string;
	spec: AggregateRequest;
}

/** Digits from `GET /v1/me` github_id. Empty means no session identity (API-key mode). */
export function savedAnalysisOwner(githubId: unknown): string {
	if (typeof githubId === 'number' && Number.isSafeInteger(githubId) && githubId >= 0) {
		return String(githubId);
	}
	if (typeof githubId === 'string' && /^[0-9]{1,20}$/.test(githubId)) return githubId;
	return '';
}

/** Per-account key when a session identity is known, so one browser profile does not share snapshots. */
export function savedAnalysisStorageKey(owner = ''): string {
	if (owner === '') return SAVED_ANALYSIS_KEY;
	if (!/^[0-9]{1,20}$/.test(owner)) return `${SAVED_ANALYSIS_KEY}:invalid`;
	return `${SAVED_ANALYSIS_KEY}:${owner}`;
}

function cleanName(name: string): string {
	const stripped = name.replace(/[\u0000-\u001F\u007F\u202A-\u202E\u2066-\u2069]/g, '').trim();
	return stripped.slice(0, MAX_NAME);
}

function stripTenant(spec: AggregateRequest): AggregateRequest | null {
	if (!spec || typeof spec !== 'object') return null;
	const ask = spec.ask;
	if (!ask || typeof ask !== 'object' || typeof ask.ask !== 'string' || !ASK_KINDS.has(ask.ask)) return null;
	const { tenant: _t, ...rest } = spec;
	return rest;
}

function readAll(backing: Storage, owner = ''): SavedAnalysis[] {
	try {
		const raw = backing.getItem(savedAnalysisStorageKey(owner));
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		const out: SavedAnalysis[] = [];
		for (const v of parsed) {
			if (!v || typeof v !== 'object') continue;
			const id = (v as SavedAnalysis).id;
			const name = cleanName(typeof (v as SavedAnalysis).name === 'string' ? (v as SavedAnalysis).name : '');
			const spec = stripTenant((v as SavedAnalysis).spec);
			if (typeof id !== 'string' || id === '' || name === '' || !spec) continue;
			out.push({ id, name, spec });
		}
		return out;
	} catch {
		return [];
	}
}

function writeAll(backing: Storage, items: SavedAnalysis[], owner = ''): void {
	backing.setItem(savedAnalysisStorageKey(owner), JSON.stringify(items));
}

function newId(): string {
	return `sa_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`;
}

export function list(backing: Storage = localStorage, owner = ''): SavedAnalysis[] {
	return readAll(backing, owner);
}

export function get(id: string, backing: Storage = localStorage, owner = ''): SavedAnalysis | undefined {
	return readAll(backing, owner).find((s) => s.id === id);
}

export function save(
	name: string,
	spec: AggregateRequest,
	backing: Storage = localStorage,
	owner = ''
): SavedAnalysis {
	const trimmed = cleanName(name);
	if (!trimmed) throw new Error('name required');
	const stored = stripTenant(spec);
	if (!stored) throw new Error('invalid spec');
	const items = readAll(backing, owner);
	const existing = items.find((s) => s.name === trimmed);
	const record: SavedAnalysis = existing
		? { ...existing, name: trimmed, spec: stored }
		: { id: newId(), name: trimmed, spec: stored };
	const replaced = existing ? items.map((s) => (s.id === existing.id ? record : s)) : [...items, record];
	const next = replaced.length > MAX_SAVED ? replaced.slice(replaced.length - MAX_SAVED) : replaced;
	writeAll(backing, next, owner);
	return record;
}

export function remove(id: string, backing: Storage = localStorage, owner = ''): void {
	writeAll(
		backing,
		readAll(backing, owner).filter((s) => s.id !== id),
		owner
	);
}
