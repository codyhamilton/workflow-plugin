<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import { filterParams, parseFilter } from '$lib/filters';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Explore } from '$lib/types';

	const COLUMNS = [
		'type',
		'ts',
		'harness',
		'repo_id',
		'plan',
		'kind',
		'event',
		'tool',
		'path',
		'conversation_id',
		'source',
		'sha',
		'screen_verdict',
		'rejection_stage'
	] as const;
	const SCHEMA = Object.fromEntries(COLUMNS.map((c) => [c, c === 'ts' ? 'datetime' : 'string']));

	type PTable = { replace(data: unknown[]): Promise<void> };
	let viewer = $state<HTMLElement | null>(null);
	let table: PTable | null = null;
	let ready = $state(false);
	let count = $state<number | null>(null);
	let truncated = $state(false);

	function toRows(rows: Explore['rows']) {
		return rows.map((r) => {
			const o: Record<string, string | number | null> = {};
			for (const c of COLUMNS) {
				if (c === 'ts') {
					const t = Date.parse(String(r.ts ?? ''));
					o.ts = Number.isNaN(t) ? null : t;
				} else o[c] = r[c] == null ? '' : String(r[c]);
			}
			return o;
		});
	}

	// Perspective is imported here and nowhere else, so no other route downloads its JS or WASM.
	onMount(() => {
		let dead = false;
		(async () => {
			const [{ default: perspective }, { default: viewerLib }] = await Promise.all([
				import('@perspective-dev/client'),
				import('@perspective-dev/viewer')
			]);
			await import('@perspective-dev/viewer-datagrid');
			await import('@perspective-dev/viewer/themes');
			const [server, client] = await Promise.all([
				import('@perspective-dev/server/dist/wasm/perspective-server.wasm?url'),
				import('@perspective-dev/viewer/dist/wasm/perspective-viewer.wasm?url')
			]);
			await Promise.all([
				perspective.init_server(fetch(server.default)),
				viewerLib.init_client(fetch(client.default))
			]);
			const worker = await perspective.worker();
			if (dead) return;
			table = (await worker.table(SCHEMA as never)) as unknown as PTable;
			await (viewer as unknown as { load(t: unknown): Promise<void> }).load(table);
			ready = true;
		})().catch(setError);
		return () => (dead = true);
	});

	$effect(() => {
		const q = filterParams(parseFilter(page.url.searchParams));
		if (!ready || !table) return;
		let live = true;
		apiGet<Explore>('analytics/explore', q).then(
			async (r) => {
				if (!live) return;
				await table!.replace(toRows(r.rows));
				if (!live) return;
				clearError();
				truncated = r.truncated;
				count = r.rows.length;
			},
			(e) => {
				if (live) setError(e);
			}
		);
		return () => (live = false);
	});
</script>

<h1>Explore</h1>
{#if truncated && count !== null}
	<p class="cap" data-testid="explore-truncated">
		This slice is capped at {count} rows (newest first); older matching rows are not shown. Narrow the date window or the filters.
	</p>
{/if}
{#if count !== null}
	<p>Rows loaded: <span data-testid="explore-count">{count}</span></p>
{/if}
<perspective-viewer bind:this={viewer}></perspective-viewer>

<style>
	perspective-viewer {
		display: block;
		width: 100%;
		min-height: 36rem;
		height: 70vh;
	}
	.cap {
		padding: 0.5rem 0.75rem;
		background: #fff4d6;
		border: 1px solid #e0b84a;
	}
</style>
