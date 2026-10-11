import { apiGet, BASE_KEY } from './api';
import { setNotice } from './state.svelte';

/** Thrown to a caller whose request a later call on the same slot superseded. */
export class Superseded extends Error {
	constructor(message = 'superseded') {
		super(message);
		this.name = 'Superseded';
	}
}

/** One consumer on a page, e.g. `overview-kpi-cost`. A new call on a slot supersedes the old one. */
export type Slot = string;

function baseUrl(): string {
	try {
		return (localStorage.getItem(BASE_KEY) ?? '').trim().replace(/\/+$/, '');
	} catch {
		return '';
	}
}

/**
 * The cache/dedupe key for a request. Mirrors `apiGet`'s URL so the key matches the real fetch:
 * base (from localStorage) + `/v1/` + path, with params sorted by key then value and empty values
 * dropped, so any two orderings of the same params produce one key.
 */
export function normalise(path: string, params: URLSearchParams): string {
	const entries = [...params.entries()]
		.filter(([, v]) => v !== '')
		.sort((a, b) => (a[0] === b[0] ? (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0) : a[0] < b[0] ? -1 : 1));
	const qs = new URLSearchParams(entries).toString();
	const p = path.replace(/^\/+/, '');
	return `${baseUrl()}/v1/${p}${qs ? `?${qs}` : ''}`;
}

type Call = {
	slot: Slot;
	key: string;
	settled: boolean;
	resolve: (value: unknown) => void;
	reject: (reason: unknown) => void;
	timer?: ReturnType<typeof setTimeout>;
	fetch?: Fetch;
};

type Fetch = {
	key: string;
	controller: AbortController;
	promise: Promise<unknown>;
	resolve: (value: unknown) => void;
	reject: (reason: unknown) => void;
	refs: number;
};

export function createClient(
	opts: { debounceMs?: number; maxConcurrent?: number; fetcher?: typeof apiGet } = {}
) {
	const debounceMs = opts.debounceMs ?? 250;
	const maxConcurrent = opts.maxConcurrent ?? 3;
	const fetcher = opts.fetcher ?? apiGet;
	const cache = new Map<string, unknown>();
	const inflight = new Map<string, Fetch>();
	const bySlot = new Map<Slot, Call>();
	let running = 0;
	const queue: (() => void)[] = [];

	function pump() {
		while (running < maxConcurrent && queue.length) {
			running++;
			queue.shift()!();
		}
	}
	function done() {
		running--;
		pump();
	}
	function schedule(task: () => void) {
		queue.push(task);
		pump();
	}

	async function perform(f: Fetch, path: string, params: URLSearchParams) {
		try {
			if (f.controller.signal.aborted) throw new Superseded();
			const data = await fetcher(path, params, f.controller.signal);
			cache.set(f.key, data);
			f.resolve(data);
		} catch (e) {
			f.reject(e);
		} finally {
			if (inflight.get(f.key) === f) inflight.delete(f.key);
			done();
		}
	}

	// Drop one slot's interest in a shared fetch; abort it only once no slot still wants it.
	function release(f: Fetch) {
		f.refs--;
		if (f.refs <= 0) {
			if (inflight.get(f.key) === f) inflight.delete(f.key);
			f.controller.abort();
		}
	}

	function run(call: Call, path: string, params: URLSearchParams) {
		if (call.settled) return;
		let f = inflight.get(call.key);
		if (f) {
			f.refs++;
		} else {
			let resolve!: (value: unknown) => void;
			let reject!: (reason: unknown) => void;
			const promise = new Promise<unknown>((res, rej) => {
				resolve = res;
				reject = rej;
			});
			f = { key: call.key, controller: new AbortController(), promise, resolve, reject, refs: 1 };
			inflight.set(call.key, f);
			const ff = f;
			schedule(() => void perform(ff, path, params));
		}
		call.fetch = f;
		f.promise.then(
			(data) => {
				if (call.settled) return;
				call.settled = true;
				const resp = data as { partial?: boolean; ignored_filters?: string[] };
				if (resp && (resp.partial || (resp.ignored_filters && resp.ignored_filters.length > 0))) {
					setNotice(call.slot, resp);
				}
				call.resolve(data);
			},
			(e) => {
				if (call.settled) return;
				call.settled = true;
				call.reject(e);
			}
		);
	}

	function get<T>(slot: Slot, path: string, params: URLSearchParams): Promise<T> {
		return new Promise<T>((resolve, reject) => {
			const key = normalise(path, params);
			const prev = bySlot.get(slot);
			if (prev) {
				if (prev.timer != null) clearTimeout(prev.timer);
				if (!prev.settled) {
					prev.settled = true;
					prev.reject(new Superseded());
				}
				if (prev.fetch) release(prev.fetch);
			}
			const call: Call = { slot, key, settled: false, resolve: resolve as (v: unknown) => void, reject };
			bySlot.set(slot, call);
			if (cache.has(key)) {
				call.settled = true;
				const data = cache.get(key);
				const resp = data as { partial?: boolean; ignored_filters?: string[] };
				if (resp && (resp.partial || (resp.ignored_filters && resp.ignored_filters.length > 0))) {
					setNotice(slot, resp);
				}
				resolve(data as T);
				return;
			}
			call.timer = setTimeout(() => {
				call.timer = undefined;
				run(call, path, params);
			}, debounceMs);
		});
	}

	return { get, clearCache: () => cache.clear() };
}

export const client = createClient();

export function getJSON<T>(slot: Slot, path: string, params: URLSearchParams): Promise<T> {
	return client.get<T>(slot, path, params);
}
