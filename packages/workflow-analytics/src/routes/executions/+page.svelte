<script lang="ts">
	import { page } from '$app/state';
	import Pager from '$lib/components/Pager.svelte';
	import { label } from '$lib/format';
	import { getJSON } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Executions, Shape } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const SHAPES: Shape[] = ['complete', 'unreported', 'started'];

	let counts = $state<Executions['counts'] | null>(null);
	let rows = $state<Executions['rows']>([]);
	let next = $state<string | undefined>(undefined);

	// First-page query: the shared view params plus an optional `limit` passed through to the API.
	// `paramsFor` returns null while facets are pending or when an exclude matches nothing.
	const params = $derived.by(() => {
		const limit = page.url.searchParams.get('limit');
		return view.paramsFor('rest', limit ? { limit } : undefined);
	});

	$effect(() => {
		const q = params;
		if (!q) return;
		let live = true;
		rows = [];
		next = undefined;
		getJSON<Executions>('executions', 'analytics/executions', q).then(
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
{#if counts && params}
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
					<td>
						<button
							type="button"
							data-testid="exec-repo"
							onclick={(ev) => view.drill('repo_id', r.repo_id, { shift: ev.shiftKey })}
						>
							{label(r.repo_id)}
						</button>
					</td>
					<td>
						<button
							type="button"
							data-testid="exec-plan"
							onclick={(ev) => view.drill('plan', r.plan, { shift: ev.shiftKey })}
						>
							{label(r.plan)}
						</button>
					</td>
					<td>
						<a data-testid="exec-conversation" href={`/conversation?id=${encodeURIComponent(r.conversation_id)}`}>
							{label(r.conversation_id)}
						</a>
					</td>
					<td>{label(r.brief_path)}</td>
					<td>
						<button
							type="button"
							data-testid="exec-harness"
							onclick={(ev) => view.drill('harness', r.harness, { shift: ev.shiftKey })}
						>
							{label(r.harness)}
						</button>
					</td>
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
	td button {
		border: none;
		background: none;
		padding: 0;
		font: inherit;
		color: var(--accent);
		cursor: pointer;
		text-decoration: underline;
	}
</style>
