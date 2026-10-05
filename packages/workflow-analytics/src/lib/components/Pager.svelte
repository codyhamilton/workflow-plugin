<script lang="ts">
	import { apiGet } from '$lib/api';
	import { clearError, setError } from '$lib/state.svelte';

	// "Load more" for a cursor-paged route. `params` is the first page's query (shared filter plus
	// any limit); the cursor is added here and stays in memory. Hidden when `next` is absent.
	// A response that arrives after the filter changed is dropped.
	let {
		path,
		params,
		next,
		onpage
	}: {
		path: string;
		params: URLSearchParams;
		next?: string;
		onpage: (rows: any[], next: string | undefined) => void;
	} = $props();

	let busy = $state(false);

	async function more() {
		if (!next || busy) return;
		const q = new URLSearchParams(params);
		q.set('cursor', next);
		const key = params.toString();
		busy = true;
		try {
			const r = await apiGet<{ rows: any[]; next?: string }>(path, q);
			if (key !== params.toString()) return;
			clearError();
			onpage(r.rows, r.next);
		} catch (e) {
			if (key === params.toString()) setError(e);
		} finally {
			busy = false;
		}
	}
</script>

{#if next}
	<p><button type="button" onclick={more} disabled={busy}>Load more</button></p>
{/if}
