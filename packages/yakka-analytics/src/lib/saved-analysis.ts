import type { AggregateRequest } from './aggregate';

export const SAVED_ANALYSIS_KEY = 'yakka-analytics-saved-analysis';

export interface SavedAnalysis {
	id: string;
	name: string;
	spec: AggregateRequest;
}

function stripTenant(spec: AggregateRequest): AggregateRequest {
	const { tenant: _t, ...rest } = spec;
	return rest;
}

function readAll(backing: Storage): SavedAnalysis[] {
	try {
		const raw = backing.getItem(SAVED_ANALYSIS_KEY);
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		return parsed.filter(
			(v): v is SavedAnalysis =>
				v &&
				typeof v === 'object' &&
				typeof (v as SavedAnalysis).id === 'string' &&
				typeof (v as SavedAnalysis).name === 'string' &&
				(v as SavedAnalysis).spec &&
				typeof (v as SavedAnalysis).spec === 'object'
		);
	} catch {
		return [];
	}
}

function writeAll(backing: Storage, items: SavedAnalysis[]): void {
	backing.setItem(SAVED_ANALYSIS_KEY, JSON.stringify(items));
}

function newId(): string {
	return `sa_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`;
}

export function list(backing: Storage = localStorage): SavedAnalysis[] {
	return readAll(backing);
}

export function get(id: string, backing: Storage = localStorage): SavedAnalysis | undefined {
	return readAll(backing).find((s) => s.id === id);
}

export function save(name: string, spec: AggregateRequest, backing: Storage = localStorage): SavedAnalysis {
	const trimmed = name.trim();
	if (!trimmed) throw new Error('name required');
	const stored = stripTenant(spec);
	const items = readAll(backing);
	const existing = items.find((s) => s.name === trimmed);
	const record: SavedAnalysis = existing
		? { ...existing, name: trimmed, spec: stored }
		: { id: newId(), name: trimmed, spec: stored };
	const next = existing
		? items.map((s) => (s.id === existing.id ? record : s))
		: [...items, record];
	writeAll(backing, next);
	return record;
}

export function remove(id: string, backing: Storage = localStorage): void {
	writeAll(backing, readAll(backing).filter((s) => s.id !== id));
}
