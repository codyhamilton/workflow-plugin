<script lang="ts">
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import Pager from '$lib/components/Pager.svelte';
	import { filterParams, parseFilter } from '$lib/filters';
	import { label } from '$lib/format';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Executions, Shape } from '$lib/types';

	const SHAPES: Shape[] = ['complete', 'unreported', 'started'];

	let counts = $state<Executions['counts'] | null>(null);
	let rows = $state<Executions['rows']>([]);
	let next = $state<string | undefined>(undefined);

	// First-page query: the shared filter plus an optional `limit` passed through to the API.
	const params = $derived.by(() => {
		const q = filterParams(parseFilter(page.url.searchParams));
		const l = page.url.searchParams.get('limit');
		if (l) q.set('limit', l);
		return q;
	});

	$effect(() => {
		const q = params;
		let live = true;
		rows = [];
		next = undefined;
		apiGet<Executions>('analytics/executions', q).then(
			(r) => {
				if (!live) return;
				clearError();
				counts = r.counts;
				rows = r.rows;
				next = r.next;
			},
			(e) => {
				if (!live) return;
				counts = null;
				setError(e);
			}
		);
		return () => (live = false);
	});
</script>

<h1>Executions</h1>
{#if counts}
	<div class="tiles">
		{#each SHAPES as s (s)}
			<div class="tile">
				<span class="n" data-testid="exec-count-{s}">{counts[s]}</span>
				<span class="name">{s}</span>
			</div>
		{/each}
	</div>
	<table>
		<thead>
			<tr><th>repo</th><th>plan</th><th>conversation</th><th>brief</th><th>harness</th><th>shape</th><th>ts</th></tr>
		</thead>
		<tbody>
			{#each rows as r, i (i)}
				<tr data-testid="exec-row">
					<td>{label(r.repo_id)}</td>
					<td>{label(r.plan)}</td>
					<td>{label(r.conversation_id)}</td>
					<td>{label(r.brief_path)}</td>
					<td>{label(r.harness)}</td>
					<td>{r.shape}</td>
					<td><time>{r.ts}</time></td>
				</tr>
			{/each}
		</tbody>
	</table>
	<Pager
		path="analytics/executions"
		{params}
		{next}
		onpage={(more, n) => {
			rows = [...rows, ...more];
			next = n;
		}}
	/>
{/if}

<style>
	.tiles {
		display: flex;
		gap: 0.75rem;
	}
	.tile {
		min-width: 7rem;
		padding: 0.5rem 0.75rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
	}
	.n {
		font-size: 1.6rem;
		font-variant-numeric: tabular-nums;
	}
	.name {
		font-size: 0.8rem;
		color: #555;
	}
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid #eee;
	}
</style>
