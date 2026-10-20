import type { MeFetchResult } from './session-gate';

/** Layout gate state for this document load (mutate fields; do not reassign the object). */
export const sessionGate = $state({
	ready: false,
	me: null as MeFetchResult | null
});

export function beginSessionGate(): void {
	sessionGate.ready = false;
	sessionGate.me = null;
}

export function finishSessionGate(me: MeFetchResult): void {
	sessionGate.me = me;
	sessionGate.ready = true;
}
